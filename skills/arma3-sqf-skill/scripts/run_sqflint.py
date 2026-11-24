#!/usr/bin/env python3
"""
Envoltorio multiplataforma determinista para sqflint (Windows y Linux).
Uso: python run_sqflint.py <archivo.sqf | directorio>

Códigos de salida:
  0: SIN ERRORES (análisis completado sin errores de sintaxis)
  1: ERRORES (se detectaron errores de sintaxis en uno o más archivos)
  2: Error de argumentos o ruta no encontrada
  3: SQFLINT_NO_DISPONIBLE (el linter no está instalado, accesible o target vacío)
"""
from __future__ import annotations

import glob
import importlib.util
import os
import re
import shutil
import site
import subprocess
import sys

try:
    import sqf.analyzer as sqf_analyzer
    from sqf.exceptions import SQFParserError, SQFWarning
    from sqf.parser import parse as sqf_parse
    HAS_SQF_ENGINE = True
except ImportError:
    HAS_SQF_ENGINE = False
    sqf_analyzer = None
    SQFParserError = None
    SQFWarning = None
    sqf_parse = None


def locate_sqflint() -> list[str] | None:
    """
    Localiza el ejecutable o comando de sqflint en el sistema siguiendo una cascada multiplataforma:
    1. Búsqueda directa en $PATH (shutil.which).
    2. Invocación como módulo Python (sys.executable -m sqflint) si sqflint o sqf están disponibles.
    3. Rutas estándar de usuario (Scripts / bin en APPDATA, LOCALAPPDATA, site.getuserbase(), sys.prefix, ~/.local/bin, etc.).
    Retorna una lista con el comando base o None si no está disponible.
    """
    # 1. Búsqueda directa en PATH
    exe = shutil.which("sqflint")
    if exe:
        return [exe]
    if sys.platform == "win32":
        exe = shutil.which("sqflint.exe")
        if exe:
            return [exe]

    # 2. Invocación como módulo Python en el intérprete activo
    if HAS_SQF_ENGINE or (importlib.util.find_spec("sqflint") is not None) or (importlib.util.find_spec("sqf") is not None):
        return [sys.executable, "-m", "sqflint"]

    # 3. Búsqueda en rutas estándar de usuario y prefijos del sistema
    candidates: list[str] = []
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA", "")
        if appdata:
            candidates.extend(glob.glob(os.path.join(appdata, "Python", "Python*", "Scripts", "sqflint.exe")))
            candidates.extend(glob.glob(os.path.join(appdata, "Python", "Python*", "Scripts", "sqflint.EXE")))
        localappdata = os.environ.get("LOCALAPPDATA", "")
        if localappdata:
            candidates.extend(glob.glob(os.path.join(localappdata, "Programs", "Python", "Python*", "Scripts", "sqflint.exe")))
            candidates.extend(glob.glob(os.path.join(localappdata, "Programs", "Python", "Python*", "Scripts", "sqflint.EXE")))
        try:
            user_base = site.getuserbase()
            if user_base:
                candidates.append(os.path.join(user_base, "Scripts", "sqflint.exe"))
                candidates.append(os.path.join(user_base, "Scripts", "sqflint.EXE"))
        except (AttributeError, OSError):
            pass
        candidates.append(os.path.join(sys.prefix, "Scripts", "sqflint.exe"))
        candidates.append(os.path.join(sys.prefix, "Scripts", "sqflint.EXE"))
        candidates.append(os.path.expanduser("~/.local/bin/sqflint.exe"))
    else:
        try:
            user_base = site.getuserbase()
            if user_base:
                candidates.append(os.path.join(user_base, "bin", "sqflint"))
        except (AttributeError, OSError):
            pass
        candidates.append(os.path.expanduser("~/.local/bin/sqflint"))
        candidates.append(os.path.join(sys.prefix, "bin", "sqflint"))
        candidates.append("/usr/local/bin/sqflint")
        candidates.append("/usr/bin/sqflint")

    for path in candidates:
        if os.path.isfile(path):
            is_executable = (sys.platform == "win32") or os.access(path, os.X_OK)
            if is_executable:
                return [path]

    return None


def parse_error_line(file_path: str, line: str) -> str:
    """
    Parsea una línea de salida de sqflint con formato [line,col]:error:msg o [line,col]:warning:msg
    y la formatea como archivo:línea: nivel: mensaje.
    """
    m = re.match(r"^\[(\d+),\s*(\d+)\]:(?:(error|warning):)?(.*)$", line, re.IGNORECASE)
    if m:
        line_num = m.group(1)
        level = (m.group(3) or "error").lower()
        msg = m.group(4).strip()
        return f"{file_path}:{line_num}: {level}: {msg}"
    if re.match(r"^(.*?):(\d+):\s*(error|warning):\s*(.*)$", line, re.IGNORECASE):
        return line
    return f"{file_path}:1: error: {line}"


def _collect_target_files(target: str) -> list[str]:
    files: list[str] = []
    if os.path.isdir(target):
        for root, _, filenames in os.walk(target):
            for f in sorted(filenames):
                if f.lower().endswith(".sqf"):
                    files.append(os.path.join(root, f))
        files.sort()
    else:
        files.append(target)
    return files


def _lint_single_file(f: str, sqflint_cmd: list[str]) -> tuple[str, list[str], list[str], bool]:
    output = ""
    rc = 0
    if HAS_SQF_ENGINE and sqflint_cmd == [sys.executable, "-m", "sqflint"]:
        # Análisis directo en proceso: máxima portabilidad y velocidad multiplataforma
        try:
            with open(f, "r", encoding="utf-8", errors="replace") as sqf_file:
                code_text = sqf_file.read()
            lines: list[str] = []
            has_parser_error = False
            try:
                res = sqf_parse(code_text)
                for e in sqf_analyzer.analyze(res).exceptions:
                    pos_line = e.position[0]
                    pos_col = e.position[1] - 1
                    level = "warning" if (SQFWarning and isinstance(e, SQFWarning)) else "error"
                    lines.append(f"[{pos_line},{pos_col}]:{level}:{e.message}")
                    if SQFParserError and isinstance(e, SQFParserError):
                        has_parser_error = True
            except SQFParserError as e:
                pos_line = e.position[0]
                pos_col = e.position[1] - 1
                lines.append(f"[{pos_line},{pos_col}]:error:{e.message}")
                has_parser_error = True
            output = "\n".join(lines).strip()
            rc = 1 if has_parser_error else 0
        except Exception as ex:
            output = f"Excepción al ejecutar sqflint: {ex}"
            rc = 1
    else:
        cmd = sqflint_cmd + ["-e", "e", f]
        sub_env = os.environ.copy()
        sub_env["PYTHONUTF8"] = "1"
        try:
            res = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=sub_env,
                check=False,
                timeout=30,
            )
            output = res.stdout.strip()
            rc = res.returncode
        except (subprocess.SubprocessError, OSError) as ex:
            output = f"Excepción al ejecutar sqflint: {ex}"
            rc = 1

    file_lines: list[str] = []
    file_errors: list[str] = []
    if output:
        for line in output.splitlines():
            s_line = line.strip()
            if not s_line:
                continue
            normalized = parse_error_line(f, s_line)
            file_lines.append(normalized)
            if re.search(r":\s*error:", normalized, re.IGNORECASE) or re.search(r":\s*warning:", normalized, re.IGNORECASE):
                file_errors.append(normalized)

    has_error = (rc != 0) or any(re.search(r":\s*error:", line_item, re.IGNORECASE) for line_item in file_lines)
    if has_error:
        status_tag = f"ERRORES (exit {rc})"
        if not file_lines and rc != 0:
            file_errors.append(f"{f}:1: error: Error de sintaxis desconocido (exit {rc})")
            file_lines.append(file_errors[-1])
    else:
        status_tag = "OK"

    return status_tag, file_lines, file_errors, has_error


def _emit_linter_results(
    detailed_results: list[tuple[str, str, list[str]]],
    error_lines: list[str],
    total_files: int,
    total_with_errors: int,
) -> None:
    if total_with_errors == 0:
        print("ESTADO: SIN ERRORES")
        print(f"Total archivos analizados: {total_files}")
        for f, status_tag, lines in detailed_results:
            print(f"== {f} ({status_tag}) ==")
            for line_item in lines:
                print(f"  {line_item}")
        warnings_only = [e for e in error_lines if re.search(r":\s*warning:", e, re.IGNORECASE)]
        if warnings_only:
            print("\n--- ADVERTENCIAS (archivo:línea) ---")
            for w in warnings_only:
                print(f"  {w}")
        print(f"ARCHIVOS_CON_PROBLEMAS=0 DE {total_files} (advertencias: {len(warnings_only)})")
        sys.exit(0)
    else:
        print("ESTADO: ERRORES")
        print(f"ARCHIVOS_CON_PROBLEMAS={total_with_errors} DE {total_files}")
        print("\n--- DETALLE DE ERRORES (archivo:línea) ---")
        for err in error_lines:
            print(f"  {err}")
        print("\n--- DESGLOSE POR ARCHIVO ---")
        for f, status_tag, lines in detailed_results:
            print(f"== {f} ({status_tag}) ==")
            for line_item in lines:
                print(f"  {line_item}")
        sys.exit(1)


def main(argv: list[str] | None = None) -> int:
    if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except (AttributeError, OSError):
            pass

    args = sys.argv[1:] if argv is None else argv
    if len(args) < 1:
        print("Uso: python run_sqflint.py <archivo.sqf | directorio>")
        sys.exit(2)

    target = args[0]
    if not os.path.exists(target):
        print(f"ERROR: La ruta '{target}' no existe.")
        sys.exit(2)

    sqflint_cmd = locate_sqflint()
    if not sqflint_cmd:
        print("SQFLINT_NO_DISPONIBLE (instala con: pip install sqflint, o preinstálalo fuera del sandbox)")
        print(f"[NO_VERIFICADO] {target}:0 (Sintaxis): Analizador estático no disponible en el host (SQFLINT_NO_DISPONIBLE)")
        sys.exit(3)

    files = _collect_target_files(target)
    if not files:
        print(f"ESTADO: NO SE ENCONTRARON ARCHIVOS .sqf EN '{target}'")
        print(f"[NO_VERIFICADO] {target}:0 (Sintaxis): Directorio vacío o sin archivos .sqf. El análisis no se ejecutó.")
        print("El analisis no se ejecuto. Reportar como NO VERIFICADO, nunca como PASA.")
        sys.exit(3)

    total_with_errors = 0
    detailed_results: list[tuple[str, str, list[str]]] = []
    error_lines: list[str] = []

    for f in files:
        status_tag, file_lines, file_errors, has_error = _lint_single_file(f, sqflint_cmd)
        if has_error:
            total_with_errors += 1
        error_lines.extend(file_errors)
        detailed_results.append((f, status_tag, file_lines))

    _emit_linter_results(detailed_results, error_lines, len(files), total_with_errors)
    return 0


if __name__ == "__main__":
    main()
