"""Orquestador de ejecución SQF para Arma 3.

Etapa 3 (R2): Bucle de validación interactiva, linter como subprocess, y
archivo de notas. Todo anclado al directorio de trabajo experimental.
"""

import argparse
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
from collections.abc import Callable

from sqf_models import (
    SQFFinding,
    check_escalation_needed_for_files,
    determine_escalation_reason,
    format_findings_report,
    parse_sqflint_output,
    summarize_escalation,
)
from sqf_wiki_reader import (
    get_command,
    get_data_git_sha,
    get_function,
    lookup_syntax_symbol,
    resolve_wiki_root,
    update_wiki,
)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Ruta relativa al propio script. Una ruta absoluta a una maquina concreta hacia que
# el plugin no arranque en ningun otro equipo, y hacia que el linter se reporte
# como "no disponible" aunque este perfectamente instalado.
DEFAULT_LINTER = os.path.normpath(
    os.path.join(SCRIPT_DIR, "..", "references", "run_sqflint.py")
)


def default_mock_agent(prompt: str) -> str:
    """Mock agent. SOLO para dry-run: NUNCA debe usarse como agente real.

    Devuelve codigo deliberadamente trivial para que el dry-run ejercite el linter
    y la maquina de estados. El dry-run SIEMPRE termina en NO VERIFICADO.
    """
    return "private _resultado = 42;\n"


def read_sqf_file_robust(path: str) -> tuple[str, str | None]:
    """Lee un archivo SQF con detección de codificación y BOM.

    Soporta UTF-8 (con y sin BOM), UTF-16 LE/BE (con BOM) y Windows-1252.
    Retorna (contenido_texto, mensaje_error). Si la codificación no es soportada,
    retorna ("", mensaje_error).
    """
    try:
        with open(path, "rb") as f:
            raw = f.read()
    except OSError as e:
        return "", f"Error de E/S al leer archivo: {e}"

    if raw.startswith(b"\xef\xbb\xbf"):
        try:
            return raw.decode("utf-8-sig"), None
        except UnicodeDecodeError as e:
            return "", f"BOM UTF-8 presente pero fallo de decodificación: {e}"
    elif raw.startswith(b"\xff\xfe"):
        try:
            return raw.decode("utf-16-le"), None
        except UnicodeDecodeError as e:
            return "", f"BOM UTF-16 LE presente pero fallo de decodificación: {e}"
    elif raw.startswith(b"\xfe\xff"):
        try:
            return raw.decode("utf-16-be"), None
        except UnicodeDecodeError as e:
            return "", f"BOM UTF-16 BE presente pero fallo de decodificación: {e}"

    # Sin BOM: probar UTF-8 estricto
    try:
        return raw.decode("utf-8"), None
    except UnicodeDecodeError:
        pass

    # Fallback a Windows-1252 / ANSI común en Arma 3
    try:
        return raw.decode("windows-1252"), None
    except UnicodeDecodeError as e:
        return "", f"Codificación no soportada: {e}"


def compute_item_9_report(
    findings: list[SQFFinding],
    rc: int,
    stdout: str,
    source_code: str = "",
    wiki_path: str | None = None,
    target: str | None = None,
    file_sources: dict[str, str] | None = None,
) -> str:
    """Calcula y formatea la fila del Ítem 9 del Checklist con cobertura de tokens y procedencia dinámica (D1, D7).

    Soporta análisis de archivo individual o directorio completo, calculando candidatos
    y restringiendo la asociación de bloqueantes por archivo.
    """
    wiki_root = resolve_wiki_root(wiki_path)
    data_sha = get_data_git_sha(wiki_root)
    if rc == 3 or "SQFLINT_NO_DISPONIBLE" in stdout or any(f.severity == "NO_VERIFICADO" and "SQFLINT" in f.description for f in findings):
        return f"| 9. Verificación de Comandos en Wiki / Biki | NO VERIFICADO | sqflint no disponible en el host (SQFLINT_NO_DISPONIBLE); análisis estático omitido (commit: {data_sha}). |"

    # Preparar mapa de archivos a fuentes
    sources: dict[str, str] = {}
    if file_sources:
        sources = dict(file_sources)
    elif target and os.path.isfile(target):
        sources = {os.path.abspath(target): source_code}
    elif source_code:
        sources = {"": source_code}

    if not sources:
        sources[""] = ""

    per_file_candidates: dict[str, set[str]] = {}
    per_file_contrastados: dict[str, set[str]] = {}
    per_file_ausentes: dict[str, set[str]] = {}
    per_file_bloqueantes: dict[str, set[str]] = {}

    for fpath, fcode in sorted(sources.items()):
        norm_fpath = os.path.normcase(os.path.normpath(fpath)) if fpath else ""
        file_findings = [
            f for f in findings
            if (not norm_fpath)
            or os.path.normcase(os.path.normpath(f.file)) == norm_fpath
            or os.path.basename(f.file) == os.path.basename(fpath)
            or (not f.file)
        ]

        # Fuente 1 (Obligatoria): Identificadores que el analizador efectivamente reportó
        file_linter_tokens: set[str] = set()
        for f in file_findings:
            for m in re.finditer(r"<Variable\(([a-zA-Z0-9_]+)\)>", f.description + " " + f.evidence):
                file_linter_tokens.add(m.group(1))

        if fpath:
            base = os.path.basename(fpath)
            for line in stdout.splitlines():
                if base in line and "<Variable(" in line:
                    for m in re.finditer(r"<Variable\(([a-zA-Z0-9_]+)\)>", line):
                        file_linter_tokens.add(m.group(1))
        elif not file_linter_tokens:
            for m in re.finditer(r"<Variable\(([a-zA-Z0-9_]+)\)>", stdout):
                file_linter_tokens.add(m.group(1))

        candidates = set(file_linter_tokens)

        # Fuente 2 (Opcional, D1): Identificadores que inician sentencia en el código fuente,
        # PERO únicamente si existen en el catálogo con grafía canónica exacta.
        if fcode:
            clean = re.sub(r'/\*[\s\S]*?\*/|//.*|"(?:[^"]|"")*"|\'(?:[^\']|\'\')*\'', ' ', fcode)
            for tok in re.findall(r'(?:^|[;{}])\s*([a-zA-Z0-9_]+)\b(?!=)', clean, re.MULTILINE):
                info = lookup_syntax_symbol(tok, wiki_root)
                if info and tok == info.get("canonical_name"):
                    candidates.add(tok)

        contrastados: set[str] = set()
        ausentes: set[str] = set()
        for tok in candidates:
            info = lookup_syntax_symbol(tok, wiki_root)
            if info and tok == info.get("canonical_name"):
                contrastados.add(tok)
            else:
                ausentes.add(tok)

        # Regla de origen corregida con límites de palabra para evitar subcadenas (D7),
        # circunscrita estrictamente a los hallazgos del mismo archivo (Requerimiento 6):
        bloqueantes: set[str] = set()
        for tok in ausentes:
            pat = re.compile(r"\b" + re.escape(tok) + r"\b|<Variable\(" + re.escape(tok) + r"\)>", re.IGNORECASE)
            is_associated = any(
                f.severity == "BLOQUEANTE"
                and (pat.search(f.description) is not None or pat.search(f.evidence) is not None)
                for f in file_findings
            )
            if is_associated:
                bloqueantes.add(tok)

        per_file_candidates[fpath] = candidates
        per_file_contrastados[fpath] = contrastados
        per_file_ausentes[fpath] = ausentes
        per_file_bloqueantes[fpath] = bloqueantes

    all_candidates = set.union(*per_file_candidates.values()) if per_file_candidates else set()
    all_contrastados = set.union(*per_file_contrastados.values()) if per_file_contrastados else set()
    all_ausentes = set.union(*per_file_ausentes.values()) if per_file_ausentes else set()
    all_bloqueantes = set.union(*per_file_bloqueantes.values()) if per_file_bloqueantes else set()

    total = len(all_candidates)
    contrastados_count = len(all_contrastados)
    ausentes_count = len(all_ausentes)
    bloqueantes_count = len(all_bloqueantes)

    if total > 0 and contrastados_count == total and bloqueantes_count == 0:
        estado = "PASA"
        desc = (
            f"100% de tokens candidatos del código ({total}/{total}) contrastados contra "
            f"réplica offline a3ref (commit: {data_sha}; 0 ausentes; 0 bloqueantes asociados)."
        )
    else:
        estado = "NO VERIFICADO"
        aus_str = f" ({', '.join(sorted(all_ausentes))})" if all_ausentes else ""
        if total == 0:
            desc = (
                f"0 de 0 tokens candidatos del código (causa: no se detectaron sentencias SQF analizables en los archivos examinados; "
                f"commit: {data_sha}; 0 ausentes; 0 bloqueantes asociados)."
            )
        else:
            desc = (
                f"{contrastados_count} de {total} tokens candidatos contrastados contra "
                f"réplica offline a3ref (commit: {data_sha}; {ausentes_count} ausentes{aus_str}; "
                f"{bloqueantes_count} bloqueantes asociados)."
            )

    return f"| 9. Verificación de Comandos en Wiki / Biki | {estado} | Regla de Cobertura Documental:\n- {desc} |"


def _build_notes_content(findings: list[SQFFinding], iteration: int) -> str:
    timestamp = datetime.datetime.now().isoformat()
    lines = [
        f"=== NOTAS DE REVISIÓN SQF - Iteración {iteration} ===",
        f"Generado: {timestamp}",
        f"Total hallazgos: {len(findings)}",
        "",
        "Hallazgos detallados:",
    ]
    for idx, f in enumerate(findings, start=1):
        lines.append(f"{idx}. [{f.severity}] {f.file}:{f.line} - {f.description}")
        if f.evidence:
            lines.append(f"   Evidencia: {f.evidence}")
    lines.append("")
    lines.append("Acciones requeridas:")
    lines.append("- Corregir los errores de sintaxis indicados arriba.")
    lines.append("- Re-ejecutar el orquestador con --continuar.")
    lines.append("==========================================")
    return "\n".join(lines)


def _archive_previous_notes(resolved_notes_file: str, resolved_archived_notes_dir: str):
    if not os.path.exists(resolved_notes_file):
        return
    os.makedirs(resolved_archived_notes_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    archived_path = os.path.join(resolved_archived_notes_dir, f"notas_revision_{timestamp}.txt")
    shutil.move(resolved_notes_file, archived_path)
    print(f"Notas archivadas en {archived_path}.")


def _run_linter_on_code(
    code: str,
    resolved_linter: str,
    resolved_work_dir: str,
    iteration: int,
    timeout: int,
) -> tuple[int, str]:
    temp_filename = f"_temp_orchestrator_{os.getpid()}_{iteration}.sqf"
    temp_sqf_path = os.path.abspath(os.path.join(resolved_work_dir, temp_filename))

    try:
        with open(temp_sqf_path, "w", encoding="utf-8") as tf:
            tf.write(code)

        env = os.environ.copy()
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        cmd = [sys.executable, "-B", resolved_linter, temp_sqf_path]
        try:
            proc = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=env,
                timeout=timeout,
                check=False,
            )
            return proc.returncode, proc.stdout
        except subprocess.TimeoutExpired:
            return 3, "TIMEOUT EXPIRED: El linter superó el tiempo límite."
    finally:
        if os.path.exists(temp_sqf_path):
            try:
                os.remove(temp_sqf_path)
            except OSError:
                pass


def _process_iteration_results(
    findings_objs: list,
    state: dict,
    iteration: int,
    max_iterations: int,
    resolved_state_file: str,
    resolved_failed_file: str,
    resolved_notes_file: str,
    dry_run: bool,
    mode: str,
) -> int:
    bloqueantes = [f for f in findings_objs if f.severity == "BLOQUEANTE"]
    print(f"Iteración {iteration}: {len(findings_objs)} hallazgos ({len(bloqueantes)} bloqueantes).")

    notes_content = _build_notes_content(findings_objs, iteration)
    with open(resolved_notes_file, "w", encoding="utf-8") as nf:
        nf.write(notes_content)
    print(f"Notas de revisión actualizadas en {resolved_notes_file}.")

    if not bloqueantes and not dry_run:
        print("Iteración sin bloqueantes. Validación exitosa.")
        state["status"] = "EXITOSO"
        state["findings"] = [f.model_dump() for f in findings_objs]
        with open(resolved_state_file, "w", encoding="utf-8") as sf:
            json.dump(state, sf, indent=2)
        return 0

    if dry_run and not bloqueantes:
        print("Dry-run sin bloqueantes: el mock agent no valida código real.")
        print("Estado: NO VERIFICADO (simulacion con mock agent)")
        state["status"] = "NO_VERIFICADO"
        state["findings"] = [f.model_dump() for f in findings_objs]
        with open(resolved_state_file, "w", encoding="utf-8") as sf:
            json.dump(state, sf, indent=2)
        return 10

    if iteration >= max_iterations:
        print(f"Se alcanzó el límite máximo de {max_iterations} iteraciones con bloqueantes abiertos.")
        print("PUERTA DE CALIDAD INFRANQUEABLE (T09): DETENIDO (NO PASA).")
        state["status"] = "FALLIDO"
        state["iteration"] = iteration
        state["findings"] = [f.model_dump() for f in findings_objs]
        state["bloqueantes_abiertos"] = len(bloqueantes)

        with open(resolved_failed_file, "w", encoding="utf-8") as ff:
            json.dump(state, ff, indent=2)
        print(f"Estado fallido guardado en {resolved_failed_file}.")

        if os.path.exists(resolved_state_file):
            try:
                os.remove(resolved_state_file)
            except OSError:
                pass
        return 1

    print(f"Bloqueantes pendientes. Guarda estado para iteración {iteration + 1}.")
    state["iteration"] = iteration + 1
    state["status"] = "EN_PROGRESO"
    state["findings"] = [f.model_dump() for f in findings_objs]
    with open(resolved_state_file, "w", encoding="utf-8") as sf:
        json.dump(state, sf, indent=2)
    return 0


def _build_agent_prompt(
    iteration: int,
    state: dict,
    resolved_notes_file: str,
    input_code: str | None,
    mode: str,
) -> str:
    prompt_parts = [
        f"Iteración {iteration} de desarrollo/revisión SQF (Modo: {mode}).",
        f"Código previo:\n{state.get('last_code', '') or (input_code or '')}",
    ]
    if os.path.exists(resolved_notes_file):
        try:
            with open(resolved_notes_file, "r", encoding="utf-8") as nf:
                prompt_parts.append(f"Notas de la iteración previa:\n{nf.read()}")
        except OSError:
            pass
    prompt_parts.append("Genera el código SQF corregido resolviendo todos los bloqueantes.")
    return "\n\n".join(prompt_parts)


def run_orchestrator(
    state_file: str | None = None,
    notes_file: str | None = None,
    archived_notes_dir: str | None = None,
    linter_executable: str | None = None,
    work_dir: str | None = None,
    continuar: bool = False,
    max_iterations: int = 3,
    agent_func: Callable[[str], str] | None = None,
    input_code: str | None = None,
    input_file: str | None = None,
    input_root: str | None = None,
    dry_run: bool = False,
    mode: str | None = None,
    timeout: int = 30,
) -> int:
    resolved_work_dir = os.path.abspath(work_dir) if work_dir else os.getcwd()
    os.makedirs(resolved_work_dir, exist_ok=True)

    resolved_state_file = (
        os.path.abspath(state_file)
        if state_file
        else os.path.join(resolved_work_dir, "orchestrator_state.json")
    )
    resolved_failed_file = os.path.join(
        os.path.dirname(resolved_state_file),
        "orchestrator_state.fallido.json",
    )
    resolved_notes_file = (
        os.path.abspath(notes_file)
        if notes_file
        else os.path.join(resolved_work_dir, "notas_revision.txt")
    )
    resolved_archived_notes_dir = (
        os.path.abspath(archived_notes_dir)
        if archived_notes_dir
        else os.path.join(resolved_work_dir, "archived_notes")
    )
    resolved_linter = (
        os.path.abspath(linter_executable)
        if linter_executable
        else DEFAULT_LINTER
    )

    if not dry_run and agent_func is None:
        raise ValueError(
            "run_orchestrator exige agent_func en modo real. Si deseas ejecutar una "
            "simulación con el mock agent, pasa dry_run=True explícitamente."
        )

    effective_agent = agent_func if agent_func is not None else default_mock_agent

    effective_input_code = input_code
    if effective_input_code is None and input_file is not None:
        input_file_path = os.path.abspath(input_file)
        if not os.path.exists(input_file_path):
            raise FileNotFoundError(f"No se encontró el archivo de entrada: {input_file_path}")
        with open(input_file_path, "r", encoding="utf-8") as f:
            effective_input_code = f.read()

    resolved_mode = mode or "Micro"

    if continuar:
        if not os.path.exists(resolved_state_file):
            print(f"Error: no existe archivo de estado previo en {resolved_state_file}.", file=sys.stderr)
            return 1
        with open(resolved_state_file, "r", encoding="utf-8") as sf:
            state = json.load(sf)
        iteration = state.get("iteration", 1)
        _archive_previous_notes(resolved_notes_file, resolved_archived_notes_dir)
    else:
        iteration = 1
        state = {
            "iteration": 1,
            "status": "INICIADO",
            "findings": [],
            "last_code": effective_input_code or "",
            "mode": resolved_mode,
        }

    agent_prompt = _build_agent_prompt(
        iteration,
        state,
        resolved_notes_file,
        effective_input_code,
        resolved_mode,
    )

    new_code = effective_agent(agent_prompt)
    state["last_code"] = new_code

    rc, stdout = _run_linter_on_code(
        new_code,
        resolved_linter,
        resolved_work_dir,
        iteration,
        timeout,
    )

    try:
        findings_objs = parse_sqflint_output(rc, stdout, source_code=new_code)
    except ValueError as e:
        print(f"ERROR FATAL DEL LINTER: {e}", file=sys.stderr)
        return 2

    return _process_iteration_results(
        findings_objs,
        state,
        iteration,
        max_iterations,
        resolved_state_file,
        resolved_failed_file,
        resolved_notes_file,
        dry_run,
        resolved_mode,
    )


def read_input_code(input_path: str | None) -> str | None:
    if not input_path:
        return None
    resolved = os.path.abspath(input_path)
    if not os.path.exists(resolved):
        raise FileNotFoundError(f"No se encontró el archivo de entrada: {resolved}")
    with open(resolved, "r", encoding="utf-8") as f:
        return f.read()


def mode_query(root: str | None = None) -> int:
    resolved_root = os.path.abspath(root) if root else os.getcwd()
    if not os.path.exists(resolved_root):
        print(f"ERROR: La ruta '{resolved_root}' no existe.", file=sys.stderr)
        return 1

    sqf_files: dict[str, str] = {}
    if os.path.isdir(resolved_root):
        for r_dir, _, f_names in os.walk(resolved_root):
            for f_name in sorted(f_names):
                if f_name.lower().endswith(".sqf"):
                    full_p = os.path.join(r_dir, f_name)
                    try:
                        with open(full_p, "r", encoding="utf-8", errors="replace") as sqf_f:
                            sqf_files[full_p] = sqf_f.read()
                    except OSError:
                        pass
    elif resolved_root.lower().endswith(".sqf"):
        try:
            with open(resolved_root, "r", encoding="utf-8", errors="replace") as sqf_f:
                sqf_files[resolved_root] = sqf_f.read()
        except OSError:
            pass

    try:
        mode = check_escalation_needed_for_files(sqf_files, "Micro")
    except ValueError as exc:
        print("ESTADO: NO VERIFICADO")
        print(str(exc))
        print("No se decide ningun modo. Revisa la ruta de --root: el modo mas permisivo")
        print("no se concede por defecto ante un inventario vacio.")
        return 10

    reason = determine_escalation_reason(sqf_files, mode)
    print(summarize_escalation(mode, reason))
    return 0


def run_lint(
    target: str | None = None,
    linter_executable: str | None = None,
    mode: str | None = None,
    timeout: int = 30,
    wiki_path: str | None = None,
) -> int:
    resolved_target = os.path.abspath(target) if target else os.getcwd()
    if not os.path.exists(resolved_target):
        print(f"ERROR: La ruta '{resolved_target}' no existe.", file=sys.stderr)
        return 1

    source_code = ""
    file_sources: dict[str, str] = {}
    encoding_findings: list[SQFFinding] = []

    if os.path.isfile(resolved_target):
        content, err = read_sqf_file_robust(resolved_target)
        if err:
            finding = SQFFinding(
                severity="NO_VERIFICADO",
                file=resolved_target,
                line=0,
                description=f"Codificación no soportada ({err})",
                evidence=err,
                discipline="Sistema",
            )
            item_9 = compute_item_9_report([finding], 0, "", source_code="", wiki_path=wiki_path, target=resolved_target)
            report = format_findings_report([finding], item_9_status="NO_VERIFICADO")
            print(report)
            print(f"\n{item_9}")
            print("Estado: NO VERIFICADO (codificación no soportada)")
            return 10
        source_code = content
        file_sources[resolved_target] = content

    if os.path.isdir(resolved_target):
        for root, _, filenames in os.walk(resolved_target):
            for f in sorted(filenames):
                if f.lower().endswith(".sqf"):
                    fpath = os.path.join(root, f)
                    content, err = read_sqf_file_robust(fpath)
                    if err:
                        encoding_findings.append(
                            SQFFinding(
                                severity="NO_VERIFICADO",
                                file=fpath,
                                line=0,
                                description=f"Codificación no soportada ({err})",
                                evidence=err,
                                discipline="Sistema",
                            )
                        )
                    else:
                        file_sources[fpath] = content

        if not file_sources and not encoding_findings:
            print("[NO_VERIFICADO] 0: (Sistema): no se encontraron archivos .sqf; el analisis no se ejecuto")
            print("RESUMEN: bloqueantes=0; sugerencias=0; no_verificado=1")
            print("ESTADO: NO VERIFICADO")
            return 10

    resolved_linter = (
        os.path.abspath(str(linter_executable))
        if linter_executable
        else DEFAULT_LINTER
    )
    if not os.path.exists(resolved_linter):
        finding = SQFFinding(
            severity="NO_VERIFICADO",
            file=resolved_target,
            line=0,
            description="Linter no disponible (SQFLINT_NO_DISPONIBLE)",
            evidence=f"No se encontró el ejecutable: {resolved_linter}",
            discipline="Sintaxis",
        )
        item_9 = compute_item_9_report(
            [finding], 3, "SQFLINT_NO_DISPONIBLE", source_code, wiki_path,
            target=resolved_target, file_sources=file_sources
        )
        report = format_findings_report([finding], item_9_status="NO_VERIFICADO")
        print(report)
        print(f"\n{item_9}")
        print("Estado: NO VERIFICADO (el linter no está disponible)")
        return 10

    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    cmd = [sys.executable, "-B", resolved_linter, resolved_target]
    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
            timeout=timeout,
            check=False,
        )
        rc = proc.returncode
        stdout = proc.stdout
    except subprocess.TimeoutExpired:
        rc = 3
        stdout = "TIMEOUT EXPIRED: El linter superó el tiempo límite."
    except (subprocess.SubprocessError, OSError) as e:
        rc = 3
        stdout = f"SQFLINT_NO_DISPONIBLE: error al invocar linter ({e})"

    findings = parse_sqflint_output(rc, stdout, source_code=source_code)
    if encoding_findings:
        findings.extend(encoding_findings)

    item_9 = compute_item_9_report(
        findings, rc, stdout, source_code=source_code, wiki_path=wiki_path,
        target=resolved_target, file_sources=file_sources
    )
    item_9_status = "NO_VERIFICADO" if ("| NO VERIFICADO |" in item_9) else "PASA"
    report = format_findings_report(findings, item_9_status=item_9_status)
    print(report)
    print(f"\n{item_9}")

    if any(f.severity == "NO_VERIFICADO" for f in findings) or rc == 3 or "SQFLINT_NO_DISPONIBLE" in stdout:
        print("Estado: NO VERIFICADO (el linter no está disponible)")
        return 10

    return 0


def main():
    parser = argparse.ArgumentParser(description="Orquestador SQF Antigravity")
    parser.add_argument("--continuar", action="store_true", help="Continuar sesión previa")
    parser.add_argument("--state-file", type=str, default=None, help="Ruta al archivo de estado")
    parser.add_argument("--notes-file", type=str, default=None, help="Ruta al archivo de notas de revisión")
    parser.add_argument("--archived-notes-dir", type=str, default=None, help="Directorio para notas archivadas")
    parser.add_argument("--linter", type=str, default=None, help="Ruta al ejecutable del linter")
    parser.add_argument("--work-dir", type=str, default=None, help="Directorio de trabajo")
    parser.add_argument("--max-iterations", type=int, default=3, help="Límite máximo de iteraciones")
    parser.add_argument("--input", dest="input_code", default=None,
                        help="Ruta a un .sqf a auditar. Si se omite, el orquestador no tiene codigo de partida.")
    parser.add_argument("--root", dest="input_root", default=None,
                        help="Carpeta del proyecto a auditar (inventario de archivos .sqf).")
    parser.add_argument("--dry-run", action="store_true",
                        help="Simulacion con el agente mock. SIEMPRE termina en NO VERIFICADO (exit 10).")
    parser.add_argument("--mode-query", action="store_true",
                        help="Consulta el modo correspondiente al proyecto según el inventario de archivos.")
    parser.add_argument("--lint", action="store_true",
                        help="Ejecuta análisis estático y produce el informe estructurado de hallazgos.")
    parser.add_argument("--mode", type=str, choices=["Micro", "Estándar", "Completo"], default=None,
                        help="Modo explícito de ejecución (evita re-escalado automático).")
    parser.add_argument("--file", dest="file_path", default=None,
                        help="Ruta a un archivo .sqf a auditar")
    parser.add_argument("--wiki", type=str, default=None,
                        help="Consultar información técnica de un comando en la wiki a3ref")
    parser.add_argument("--wiki-path", type=str, default=None,
                        help="Ruta personalizada a la base de datos de la wiki")
    parser.add_argument("--update-wiki", "--update", action="store_true",
                        help="Actualizar repositorios de la wiki")
    parser.add_argument("--serve-mcp", action="store_true",
                        help="Arranca el servidor MCP local sobre stdio (JSON-RPC 2.0).")
    parser.add_argument("files", nargs="*", help="Archivos o rutas adicionales.")

    args = parser.parse_args()

    if args.serve_mcp:
        from mcp_server import run_mcp_server_stdio
        sys.exit(run_mcp_server_stdio())

    if args.wiki:
        wiki_root = resolve_wiki_root(args.wiki_path)
        info = get_command(args.wiki, wiki_root) or get_function(args.wiki, wiki_root)
        sha = get_data_git_sha(wiki_root)
        if info:
            print(f"=== FICHA TÉCNICA BIKI: {info.get('canonical_name')} ===")
            print(f"Commit Git SHA: {sha}")
            print(f"Status: {info.get('status')}")
            print(f"Versión: {info.get('version')}")
            print(f"URL: {info.get('url')}")
            if "locality" in info:
                loc = info["locality"]
                print(f"Locality: Argumento={loc.get('argument')}, Efecto={loc.get('effect')}")
            print(json.dumps(info, indent=2, ensure_ascii=False))
            sys.exit(0)
        else:
            print(f"Símbolo no encontrado en a3ref: {args.wiki}", file=sys.stderr)
            sys.exit(1)

    if args.update_wiki:
        wiki_root = resolve_wiki_root(args.wiki_path)
        ok, msg = update_wiki(wiki_root)
        if ok:
            print(f"Actualización de Wiki: {msg}")
            sys.exit(0)
        else:
            print(f"Error al sincronizar wiki: {msg}", file=sys.stderr)
            sys.exit(1)

    if args.mode_query and args.lint:
        print("ERROR: --mode-query y --lint son mutuamente excluyentes.", file=sys.stderr)
        sys.exit(1)

    if args.mode_query:
        target_root = args.input_root or (args.files[0] if args.files else ".")
        sys.exit(mode_query(root=target_root))

    if args.file_path:
        sys.exit(run_lint(target=args.file_path, linter_executable=args.linter, mode=args.mode, wiki_path=args.wiki_path))

    if args.lint:
        target = args.input_root or args.input_code or (args.files[0] if args.files else ".")
        sys.exit(run_lint(target=target, linter_executable=args.linter, mode=args.mode, wiki_path=args.wiki_path))

    try:
        code = run_orchestrator(
            state_file=args.state_file,
            notes_file=args.notes_file,
            archived_notes_dir=args.archived_notes_dir,
            linter_executable=args.linter,
            work_dir=args.work_dir,
            continuar=args.continuar,
            max_iterations=args.max_iterations,
            input_code=read_input_code(args.input_code),
            input_root=args.input_root,
            dry_run=args.dry_run,
            mode=args.mode,
        )
        sys.exit(code)
    except (FileNotFoundError, ValueError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
