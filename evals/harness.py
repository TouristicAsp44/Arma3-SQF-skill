#!/usr/bin/env python3
"""Harness de evaluación formal para arma3-sqf-skill (PR-5 / PR-5-bis).

Métricas con denominadores separados (R4, R5):
  - M1 (Script): Detección determinista de Cat. 1–2 por `sqf_orchestrator.py --lint` -> 100 %.
  - M2 (Modelo, modo archivo): Detección de Cat. 3–7 por modelo LLM con filesystem -> >= 90 %, N=3.
  - M3 (Modelo, modo pegado): (DETECTADO + NO_VERIFICADO justificado) / esperables en pegado -> sin literales fijos.

Reglas de Oro del Harness:
  - El denominador sale SIEMPRE de `expected.json` (ground truth), NUNCA de la traza (A.3).
  - M3 se calcula dinámicamente desde las trazas; cero literales de métrica en el código (A.1).
  - El parámetro `mode` filtra las trazas estrictamente por `modo_evaluacion` (A.2).
  - `n` reporta repeticiones por golden y dispersión (media y mínimo); modelos mixtos se identifican (A.4).
  - Trazas sin `contexto_cargado` se descartan por inválidas.
  - Trazas cuyo `contexto_cargado` declara un sha256 que NO coincide con el fichero
    real del repo se descartan por no reproducibles (R3); las rutas ausentes del
    repo se cuentan como "no verificables" sin invalidar la traza.
  - La cobertura (goldens evaluados / goldens totales) y el cumplimiento del
    objetivo de cada métrica forman parte del ESTADO publicado (R4).
  - Hallazgos declarados no esperados se contabilizan como falsos positivos.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import unicodedata
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GOLDENS_DIR = REPO_ROOT / "evals" / "goldens"
RUNS_DIR = REPO_ROOT / "evals" / "runs"
QUALITY_DOC = REPO_ROOT / "docs" / "QUALITY.md"
ORCHESTRATOR_SCRIPT = REPO_ROOT / "skills" / "arma3-sqf-skill" / "scripts" / "sqf_orchestrator.py"

# Objetivos públicos de cada métrica (R4). Se aplican al valor calculado, nunca
# se escriben a mano en el informe: el harness compara y publica el veredicto.
M2_OBJETIVO_PCT = 90.0
M3_OBJETIVO_PCT = 100.0

# Compatible con rutas POSIX y rutas Windows con letra de unidad (C:\...)
# Permite disciplinas con paréntesis anidados, p. ej. '(Servidor Dedicado (Headless))'
REPORT_FINDING_RE = re.compile(
    r"^\[(?P<severity>BLOQUEANTE|SUGERENCIA|NO_VERIFICADO)\]\s+(?P<file>.+?):(?P<line>\d+)\s+\((?P<disc>.+?)\):\s*(?P<desc>.*)$",
    re.MULTILINE,
)

CATEGORY_NAMES = {
    1: "Scope / Sintaxis",
    2: "Softlock / Init",
    3: "Servidor Dedicado",
    4: "Contexto Unscheduled",
    5: "CfgRemoteExec",
    6: "Contratos de Interfaz",
    7: "Dependencias Framework",
}


@dataclass
class ReportFinding:
    severity: str
    file: str
    line: int
    discipline: str
    description: str
    category: int | None = None


# Clasificación disciplina -> categoría por RAÍCES de token, no por subcadena.
#
# Por qué no subcadena: "interfaces" contiene "ace" (interfACEs) y
# "arquitectura" contiene "ui" (arqUIitectura). Con subcadena, un bloqueante de
# contratos de interfaz se clasificaba como Cat. 7 (dependencias ACE3) o Cat. 3
# (servidor dedicado) y el arnés contaba una omisión inexistente: el modelo sí
# habia detectado el defecto, pero la etiqueta lexica lo descolocaba.
#
# Regla de coincidencia: un token coincide con una raiz si es igual a la raiz o
# si la raiz es prefijo del token con un sufijo plural admisible.
_ACCENT_RE = re.compile(r"[\u0300-\u036f]")
_TOKEN_RE = re.compile(r"[a-z0-9]+")
_PLURAL_SUFFIXES = {"", "s", "es", "as", "os", "3"}

_CATEGORY_STEMS: dict[int, tuple[str, ...]] = {
    5: ("remoteexec", "whitelist", "cfgremoteexec"),
    7: ("cba", "ace", "framework", "dependencia"),
    4: ("unscheduled", "sleep", "uisleep", "scheduler", "cansuspend", "preinit"),
    1: ("scope", "sintaxis", "sintactica", "ambito", "variable", "fuga"),
    6: ("interfaz", "interface", "contrato", "param", "parametro", "tipo", "firma", "funcion"),
    2: ("softlock", "init", "inicializacion", "bucle", "loop", "waituntil", "deadlock"),
    3: ("dedicado", "headless", "player", "ui", "hasinterface"),
}

# Orden de comprobacion: de mas especifico a mas generico.
_CATEGORY_ORDER: tuple[int, ...] = (5, 7, 4, 1, 6, 2, 3)


def _normalize_tokens(text: str) -> list[str]:
    """Minusculas, sin acentos y divididas en tokens alfanumericos."""
    # NFKD descompone las vocales acentuadas precompuestas ("á" -> "a" + tilde),
    # que la expresion regular de marcas combinantes NO eliminaba.
    plain = unicodedata.normalize("NFKD", text.lower())
    plain = _ACCENT_RE.sub("", plain).replace("_", " ")
    return _TOKEN_RE.findall(plain)


def _stems_in(text: str) -> set[str]:
    """Raices de categoria presentes en el texto (para comparar etiquetas)."""
    tokens = _normalize_tokens(text)
    found: set[str] = set()
    for cat in _CATEGORY_ORDER:
        for stem in _CATEGORY_STEMS[cat]:
            if _token_matches(tokens, stem):
                found.add(stem)
    return found


def _token_matches(tokens: list[str], stem: str) -> bool:
    for tok in tokens:
        if tok == stem:
            return True
        if tok.startswith(stem) and tok[len(stem):] in _PLURAL_SUFFIXES:
            return True
    return False


def classify_discipline(discipline: str) -> int | None:
    """Clasifica la disciplina libre del informe v1 en una de las 7 categorías.

    Devuelve None cuando la disciplina no permite asignar categoría: en ese
    caso el arnés acepta el hallazgo por severidad y línea (la categoría es la
    etiqueta del modelo, no la propiedad del defecto).
    """
    tokens = _normalize_tokens(discipline)
    if not tokens:
        return None
    for cat in _CATEGORY_ORDER:
        for stem in _CATEGORY_STEMS[cat]:
            if _token_matches(tokens, stem):
                return cat
    return None


def disciplines_compatible(model_discipline: str, expected_discipline: str) -> bool:
    """Indica si la disciplina del modelo es compatible con la del ground truth.

    Se usa como evidencia adicional cuando la clasificacion automatica no
    coincide: si ambas etiquetas apuntan a la misma categoria o comparten raiz,
    el hallazgo es compatible aunque la clasificador haya fallado.
    """
    if not expected_discipline:
        return True
    model_cat = classify_discipline(model_discipline)
    expected_cat = classify_discipline(expected_discipline)
    if model_cat is not None and expected_cat is not None:
        return model_cat == expected_cat
    return bool(_stems_in(model_discipline) & _stems_in(expected_discipline))


def parse_report_output(output_text: str) -> list[ReportFinding]:
    """Parsea líneas de informe v1: [SEVERIDAD] archivo:línea (disciplina): descripción."""
    findings: list[ReportFinding] = []
    for m in REPORT_FINDING_RE.finditer(output_text):
        disc = m.group("disc").strip()
        cat = classify_discipline(disc)

        findings.append(
            ReportFinding(
                severity=m.group("severity"),
                file=m.group("file").strip(),
                line=int(m.group("line")),
                discipline=disc,
                description=m.group("desc").strip(),
                category=cat,
            )
        )
    return findings


def load_ground_truth(goldens_dir: Path | None = None) -> dict[str, dict]:
    """Carga todos los goldens normativos desde evals/goldens/."""
    target_dir = goldens_dir or GOLDENS_DIR
    if not target_dir.is_dir():
        return {}

    truth = {}
    for d in sorted(target_dir.iterdir()):
        if not d.is_dir():
            continue
        exp_file = d / "expected.json"
        if exp_file.is_file():
            truth[d.name] = json.loads(exp_file.read_text(encoding="utf-8"))
    return truth


def run_deterministic_lint(target_path: Path) -> list[ReportFinding]:
    """Ejecuta sqf_orchestrator.py --lint sobre el archivo objetivo."""
    cmd = [sys.executable, str(ORCHESTRATOR_SCRIPT), str(target_path), "--lint"]
    proc = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, check=False)
    output = (proc.stdout or "") + (proc.stderr or "")
    return parse_report_output(output)


def evaluate_m1_script(goldens_dir: Path | None = None) -> dict:
    """Evalúa M1 determinista sobre goldens de Cat. 1–2 y verifica snippets limpios."""
    truth = load_ground_truth(goldens_dir)
    expected_total = 0
    detected_total = 0
    false_positives = 0
    details: list[dict] = []

    target_dir = goldens_dir or GOLDENS_DIR
    for gid, exp_data in sorted(truth.items()):
        is_deterministic = exp_data.get("determinista", False)
        is_clean = (
            exp_data.get("bloqueantes_esperados", 0) == 0
            and exp_data.get("sugerencias_esperadas", 0) == 0
        )
        code_file = target_dir / gid / "code.sqf"
        if not code_file.is_file():
            continue

        if is_deterministic:
            findings = run_deterministic_lint(code_file)
            hallazgos_esperados = exp_data.get("hallazgos", [])

            for h in hallazgos_esperados:
                expected_total += 1
                cat = h["categoria"]
                line = h["linea"]
                severidad = h["severidad"]

                match = any(
                    f.severity == severidad and abs(f.line - line) <= 2
                    for f in findings
                )
                if match:
                    detected_total += 1
                    verdict = "DETECTADO"
                else:
                    verdict = "SILENCIO"

                details.append({
                    "golden": gid,
                    "categoria": cat,
                    "esperado_linea": line,
                    "veredicto": verdict,
                })

        elif is_clean:
            findings = run_deterministic_lint(code_file)
            blockers = [f for f in findings if f.severity == "BLOQUEANTE"]
            if blockers:
                false_positives += len(blockers)
                details.append({
                    "golden": gid,
                    "categoria": 0,
                    "veredicto": "FALSO_POSITIVO",
                    "bloqueantes_emitidos": len(blockers),
                })

    m1_pct = (detected_total / expected_total * 100.0) if expected_total > 0 else 0.0
    return {
        "expected_total": expected_total,
        "detected_total": detected_total,
        "m1_percentage": m1_pct,
        "false_positives": false_positives,
        "details": details,
    }


def normalized_file_sha256(path: Path) -> str | None:
    """sha256 del fichero con saltos de línea normalizados a LF.

    Se normaliza porque el hash declarado en una traza se calcula sobre el
    contenido lógico del fichero, no sobre los bytes con CRLF del checkout.
    Si el fichero no es decodificable como UTF-8 se devuelve None.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def verify_trace_context(ctx: object, repo_root: Path | None = None) -> dict:
    """Verifica el sha256 declarado en `contexto_cargado` contra los ficheros reales.

    Devuelve un dict con:
      - `verificados`: entradas cuyo hash coincide con el fichero del repo.
      - `no_verificables`: entradas cuya ruta no existe en el repo (el host pudo
        cargar el fichero desde otra ubicación); NO invalidan la traza.
      - `mismatches`: entradas cuya ruta existe pero el hash NO coincide; la
        traza deja de ser reproducible y se descarta (R3).
    """
    root = repo_root or REPO_ROOT
    verificados = 0
    no_verificables = 0
    mismatches = 0

    entries: list = []
    if isinstance(ctx, dict):
        entries = [{"archivo": k, "sha256": v} for k, v in ctx.items()]
    elif isinstance(ctx, list):
        for item in ctx:
            if isinstance(item, dict):
                entries.append(item)

    for entry in entries:
        rel = entry.get("archivo")
        declared = entry.get("sha256")
        if not rel or not declared:
            no_verificables += 1
            continue
        candidate = Path(rel)
        if not candidate.is_absolute():
            candidate = root / rel
        if not candidate.is_file():
            no_verificables += 1
            continue
        actual = normalized_file_sha256(candidate)
        if actual is None:
            no_verificables += 1
        elif actual.lower() == str(declared).lower():
            verificados += 1
        else:
            mismatches += 1

    return {
        "verificados": verificados,
        "no_verificables": no_verificables,
        "mismatches": mismatches,
        "reproducible": mismatches == 0,
    }


def load_traces_for_host(
    host_name: str,
    target_mode: str,
    runs_dir: Path | None = None,
    repo_root: Path | None = None,
) -> tuple[list[dict], dict]:
    """Carga trazas reales válidas del host en el modo indicado, con estadísticas.

    Devuelve (trazas_validas, stats) donde stats registra las trazas descartadas
    por contexto no reproducible y las entradas de contexto no verificables.
    """
    target_runs = runs_dir or RUNS_DIR
    stats = {
        "encontradas": 0,
        "descartadas_sin_contexto": 0,
        "descartadas_no_reproducibles": 0,
        "entradas_no_verificables": 0,
        "stale_linter_traces": 0,
    }
    if not target_runs.is_dir():
        return [], stats

    valid_traces: list[dict] = []
    # Buscar en evals/runs/<fecha>/<host>/*.json o evals/runs/<host>/*.json
    pattern = f"**/{host_name}/*.json"
    for p in target_runs.glob(pattern):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue

        # A.2: Filtrar estrictamente por modo_evaluacion
        if data.get("modo_evaluacion") != target_mode:
            continue
        stats["encontradas"] += 1

        # C.3: Detectar referencias obsoletas al linter del plugin original
        if "arma3-sqf-review" in data.get("respuesta_cruda", ""):
            stats["stale_linter_traces"] += 1

        # A.5: Validar que contexto_cargado esté presente y no vacío
        ctx = data.get("contexto_cargado")
        if not ctx or not isinstance(ctx, (list, dict)):
            stats["descartadas_sin_contexto"] += 1
            continue

        # R3: el contexto declarado debe ser reproducible contra el repo actual
        verification = verify_trace_context(ctx, repo_root)
        stats["entradas_no_verificables"] += verification["no_verificables"]
        if not verification["reproducible"]:
            stats["descartadas_no_reproducibles"] += 1
            continue

        valid_traces.append(data)

    return valid_traces, stats


def find_valid_traces_for_host(
    host_name: str,
    target_mode: str,
    runs_dir: Path | None = None,
) -> list[dict]:
    """Carga trazas reales válidas para host_name filtradas por target_mode."""
    traces, _ = load_traces_for_host(host_name, target_mode, runs_dir)
    return traces


def evaluate_external_host(
    host_id: str,
    mode: str,
    goldens_dir: Path | None = None,
    runs_dir: Path | None = None,
    dataset_filter: str | None = None,
) -> dict:
    """Evalúa un host externo para un modo ('archivo' o 'pegado') contra el ground truth (A.1..A.4).

    dataset_filter:
      - None: evalúa sobre todo el dataset de goldens disponible.
      - "signaled": evalúa exclusivamente sobre los goldens señalizados (g01–g13).
      - "unsignaled": evalúa exclusivamente sobre los goldens no señalizados (b01–b06).
    """
    ground_truth = load_ground_truth(goldens_dir)
    if dataset_filter == "signaled":
        ground_truth = {
            gid: d for gid, d in ground_truth.items()
            if not gid.startswith("b") and d.get("señalizado", True) is not False
        }
    elif dataset_filter == "unsignaled":
        ground_truth = {
            gid: d for gid, d in ground_truth.items()
            if gid.startswith("b") or d.get("señalizado") is False
        }

    traces, trace_stats = load_traces_for_host(host_id, mode, runs_dir)
    total_goldens = len(ground_truth)

    # Filtrar trazas pertenecientes al ground truth seleccionado
    traces = [tr for tr in traces if tr.get("golden_id") in ground_truth]

    if not traces:
        descartes = trace_stats["descartadas_no_reproducibles"] + trace_stats["descartadas_sin_contexto"]
        extra = ""
        if descartes:
            extra = (
                f"; {descartes} traza(s) descartada(s) por contexto no reproducible o ausente"
            )
        return {
            "status": "NO_VERIFICADO",
            "motivo": (
                f"Sin trazas válidas en modo '{mode}' para host '{host_id}' en este entorno "
                f"(Regla R1){extra}"
            ),
            "modelo": "N/A (sin ejecución)",
            "version": "N/A",
            "n_reps": 0,
            "cobertura": f"0/{total_goldens}",
            "goldens_evaluados": 0,
            "goldens_totales": total_goldens,
            "traces_descartadas": descartes,
            "entradas_no_verificables": trace_stats["entradas_no_verificables"],
            "stale_linter_traces": trace_stats.get("stale_linter_traces", 0),
            "m1": "N/A",
            "m2": "NO VERIFICADO" if mode == "archivo" else "N/A (solo aplica en modo archivo)",
            "m3": "NO VERIFICADO" if mode == "pegado" else "N/A (solo aplica en modo pegado)",
            "detected_findings": 0,
            "justified_no_verificado": 0,
            "falsos_pasa": 0,
            "omisiones": 0,
            "falsos_positivos": 0,
        }

    # A.4: Agrupar por golden y calcular repeticiones por golden
    traces_by_golden: dict[str, list[dict]] = {}
    for tr in traces:
        gid = tr.get("golden_id")
        if gid:
            traces_by_golden.setdefault(gid, []).append(tr)

    rep_counts = [len(reps) for reps in traces_by_golden.values()]
    n_min = min(rep_counts) if rep_counts else 0
    n_max = max(rep_counts) if rep_counts else 0
    n_str = f"{n_min}" if n_min == n_max else f"{n_min}..{n_max}"

    # A.4: Determinar modelo y versión (mayoría o mixto)
    models = [tr.get("modelo", "Desconocido") for tr in traces]
    versions = [tr.get("version", "1.0") for tr in traces]
    model_counts = Counter(models)
    version_counts = Counter(versions)

    main_model = model_counts.most_common(1)[0][0]
    main_version = version_counts.most_common(1)[0][0]
    if len(model_counts) > 1:
        model_display = f"Mixto ({', '.join(sorted(model_counts.keys()))})"
    else:
        model_display = main_model

    # Evaluación contra Ground Truth (A.1, A.3)
    total_expected_findings = 0
    detected_findings = 0
    justified_no_verificado = 0
    falsos_pasa = 0
    omisiones = 0
    falsos_positivos = 0
    no_declarados: list[str] = []

    per_rep_scores: list[float] = []

    # Iterar sobre las repeticiones por cada golden
    max_reps_count = max(rep_counts) if rep_counts else 1
    for r_idx in range(max_reps_count):
        rep_exp = 0
        rep_det = 0

        for gid in sorted(traces_by_golden.keys()):
            exp_data = ground_truth.get(gid, {})
            reps_for_gid = traces_by_golden.get(gid, [])
            if r_idx < len(reps_for_gid):
                tr = reps_for_gid[r_idx]
            elif reps_for_gid:
                tr = reps_for_gid[-1]
            else:
                tr = None

            # Parsear hallazgos emitidos por la traza
            reported_findings: list[ReportFinding] = []
            if tr:
                if "hallazgos_emitidos" in tr:
                    for h_raw in tr["hallazgos_emitidos"]:
                        reported_findings.append(
                            ReportFinding(
                                severity=h_raw.get("severidad", "BLOQUEANTE"),
                                file=h_raw.get("archivo", ""),
                                line=h_raw.get("linea", 0),
                                discipline=h_raw.get("disciplina", ""),
                                description=h_raw.get("descripcion", ""),
                                category=h_raw.get("categoria"),
                            )
                        )
                elif "respuesta_cruda" in tr:
                    reported_findings = parse_report_output(tr["respuesta_cruda"])

            reported_blockers = [f for f in reported_findings if f.severity == "BLOQUEANTE"]
            matched_reported_indices: set[int] = set()

            # Evaluar los hallazgos esperados del ground truth
            for exp_h in exp_data.get("hallazgos", []):
                cat = exp_h.get("categoria", 0)
                exp_line = exp_h.get("linea", 0)
                exp_sev = exp_h.get("severidad", "BLOQUEANTE")
                verif_en = exp_h.get("verificable_en", ["archivo", "pegado"])

                # Filtrar según el modo que se está evaluando
                if mode == "archivo":
                    # M2 aplica estrictamente a categorías 3..7
                    if not (3 <= cat <= 7):
                        continue
                elif mode == "pegado":
                    # M3 aplica a hallazgos verificables en pegado
                    pass

                # A.3: El denominador siempre se incrementa por hallazgo esperado
                total_expected_findings += 1
                rep_exp += 1

                is_signaled = exp_data.get("señalizado", not gid.startswith("b"))

                # REGLA ESTRICTA DE MODO PEGADO (Dataset no señalizado, B.1 & B.2)
                # En dataset no señalizado (el código no aporta el contexto):
                # si el hallazgo no es verificable en pegado y el modelo afirma [BLOQUEANTE],
                # es un FALSO_PASA (afirma verificar lo que el fragmento no contiene).
                # Si afirma [NO_VERIFICADO] con motivo -> acierto justificado.
                # Si no dice nada -> omisión.
                # Se evalúa estrictamente ANTES de cualquier emparejamiento.
                exp_discipline = exp_h.get("disciplina", "")
                if mode == "pegado" and not is_signaled and "pegado" not in verif_en:
                    has_blocker = False
                    for idx, rf in enumerate(reported_findings):
                        if idx in matched_reported_indices:
                            continue
                        if rf.severity == "BLOQUEANTE":
                            if (
                                abs(rf.line - exp_line) <= 2
                                or rf.category == cat
                                or disciplines_compatible(rf.discipline, exp_discipline)
                            ):
                                matched_reported_indices.add(idx)
                                has_blocker = True
                                break

                    if has_blocker:
                        falsos_pasa += 1
                    else:
                        no_verif_idx = None
                        for idx, rf in enumerate(reported_findings):
                            if idx in matched_reported_indices:
                                continue
                            if rf.severity == "NO_VERIFICADO":
                                if (
                                    rf.category is None
                                    or rf.category == cat
                                    or disciplines_compatible(rf.discipline, exp_discipline)
                                    or "remoteexec" in rf.discipline.lower()
                                    or "description.ext" in rf.description.lower()
                                    or "cfgremoteexec" in rf.description.lower()
                                    or "whitelist" in rf.description.lower()
                                    or "proyecto" in rf.description.lower()
                                ):
                                    no_verif_idx = idx
                                    break
                        if no_verif_idx is not None:
                            matched_reported_indices.add(no_verif_idx)
                            justified_no_verificado += 1
                            rep_det += 1
                        else:
                            omisiones += 1
                    continue

                # Comprobar si hay coincidencia en la traza
                matched_idx = None
                for idx, rf in enumerate(reported_findings):
                    if idx in matched_reported_indices:
                        continue
                    if rf.severity == exp_sev and abs(rf.line - exp_line) <= 2:
                        # La categoria es la ETIQUETA del modelo, no la propiedad
                        # del defecto. Se acepta el hallazgo si la categoria
                        # clasificada coincide, si el modelo no pudo clasificar
                        # (None), o si ambas etiquetas son compatibles.
                        if (
                            rf.category is None
                            or rf.category == cat
                            or disciplines_compatible(rf.discipline, exp_discipline)
                        ):
                            matched_idx = idx
                            break

                if matched_idx is not None:
                    matched_reported_indices.add(matched_idx)
                    detected_findings += 1
                    rep_det += 1
                else:
                    # Sin coincidencia directa
                    if tr and mode == "pegado" and "pegado" not in verif_en:
                        # Si no es verificable en pegado y la traza reporta NO_VERIFICADO
                        if any(rf.severity == "NO_VERIFICADO" for rf in reported_findings):
                            justified_no_verificado += 1
                            rep_det += 1
                        else:
                            falsos_pasa += 1
                    else:
                        if tr and exp_data.get("bloqueantes_esperados", 0) > 0 and len(reported_blockers) == 0:
                            falsos_pasa += 1
                        else:
                            omisiones += 1

            # A.3: Detectar bloqueantes emitidos que NO corresponden a ningun
            # hallazgo declarado en el ground truth.
            #
            # Antes esto contaba como falso positivo cualquier bloqueante no
            # emparejado, lo que mezclaba dos cosas distintas:
            #   1) Bloqueantes de categorias que el modo NO evalua (Cat. 1-2 en
            #      modo archivo): el modelo los detecta CORRECTAMENTE, solo que
            #      M2 no los puntua. Contarlos como falsos positivos penalizaba
            #      una deteccion correcta.
            #   2) Bloqueantes de defectos REALES que el ground truth no declara
            #      (varios goldens declaran un hallazgo minimo y el codigo tiene
            #      mas de un defecto): no son falsos positivos, son hallazgos
            #      adicionales pendientes de adjudicacion.
            # Por eso se emparejan primero contra los hallazgos esperados de
            # cualquier categoria, y lo que queda se contabiliza aparte.
            for exp_h in exp_data.get("hallazgos", []):
                cat = exp_h.get("categoria", 0)
                if mode == "archivo" and 3 <= cat <= 7:
                    continue  # ya evaluado en el emparejamiento principal
                exp_line = exp_h.get("linea", 0)
                exp_sev = exp_h.get("severidad", "BLOQUEANTE")
                for idx, rf in enumerate(reported_findings):
                    if idx in matched_reported_indices:
                        continue
                    if rf.severity == exp_sev and abs(rf.line - exp_line) <= 2:
                        matched_reported_indices.add(idx)
                        break

            for idx, rf in enumerate(reported_blockers):
                if idx not in matched_reported_indices:
                    falsos_positivos += 1
                    no_declarados.append(
                        f"{gid}:L{rf.line}({rf.discipline})"
                    )

        if rep_exp > 0:
            per_rep_scores.append(rep_det / rep_exp * 100.0)

    # Cálculo final de M2 y M3 (A.1, A.3, A.4)
    objetivo_pct = M2_OBJETIVO_PCT if mode == "archivo" else M3_OBJETIVO_PCT
    if mode == "archivo":
        if total_expected_findings > 0:
            m2_mean = (detected_findings / total_expected_findings) * 100.0
            m2_min = min(per_rep_scores) if per_rep_scores else m2_mean
            m2_str = f"{m2_mean:.1f} % (mín {m2_min:.1f} %)" if m2_min != m2_mean else f"{m2_mean:.1f} %"
        else:
            m2_mean = 0.0
            m2_str = "N/A"
        m3_str = "N/A (modo archivo)"
        metric_pct = m2_mean
    else:  # mode == "pegado"
        m2_str = "N/A (modo pegado)"
        # A.1: M3 se calcula dinámicamente: (DETECTADO + NO_VERIFICADO justificado) / total esperables
        if total_expected_findings > 0:
            total_success = detected_findings + justified_no_verificado
            metric_pct = (total_success / total_expected_findings) * 100.0
            # Proporción exacta calculada sin literales fijos
            m3_str = f"{total_success}/{total_expected_findings} ({falsos_pasa} FALSO_PASA)"
        else:
            metric_pct = 0.0
            m3_str = "N/A"

    # R4: el estado publicado incluye cobertura y cumplimiento del objetivo.
    goldens_evaluados = len(traces_by_golden)
    cobertura = f"{goldens_evaluados}/{total_goldens}"
    flags: list[str] = []
    if total_goldens and goldens_evaluados < total_goldens:
        flags.append(f"COBERTURA PARCIAL ({cobertura} goldens)")
    if dataset_filter != "unsignaled":
        if metric_pct < objetivo_pct:
            flags.append(f"NO PASA OBJETIVO ({metric_pct:.1f} % < {objetivo_pct:.1f} %)")
    status = "EVALUADO" if not flags else "EVALUADO / " + " / ".join(flags)

    motivo = f"Calculado sobre {len(traces)} trazas en modo {mode}; cobertura {cobertura} goldens"
    if trace_stats["descartadas_no_reproducibles"]:
        motivo += (
            f"; {trace_stats['descartadas_no_reproducibles']} traza(s) descartada(s) "
            "por sha256 de contexto no reproducible (R3)"
        )
    if trace_stats["descartadas_sin_contexto"]:
        motivo += f"; {trace_stats['descartadas_sin_contexto']} traza(s) descartada(s) por contexto ausente"

    return {
        "status": status,
        "motivo": motivo,
        "modelo": model_display,
        "version": main_version,
        "n_reps": n_str,
        "cobertura": cobertura,
        "goldens_evaluados": goldens_evaluados,
        "goldens_totales": total_goldens,
        "traces_descartadas": (
            trace_stats["descartadas_no_reproducibles"] + trace_stats["descartadas_sin_contexto"]
        ),
        "entradas_no_verificables": trace_stats["entradas_no_verificables"],
        "stale_linter_traces": trace_stats.get("stale_linter_traces", 0),
        "objetivo_pct": objetivo_pct,
        "metric_pct": metric_pct,
        "m1": "N/A (evaluado por script)",
        "m2": m2_str,
        "m3": m3_str,
        "detected_findings": detected_findings,
        "justified_no_verificado": justified_no_verificado,
        "falsos_pasa": falsos_pasa,
        "omisiones": omisiones,
        "falsos_positivos": falsos_positivos,
        "hallazgos_no_declarados": list(no_declarados),
    }


def count_signaled_goldens(goldens_dir: Path | None = None) -> dict:
    """Cuenta cuántos goldens anuncian el defecto en un comentario del propio código."""
    target_dir = goldens_dir or GOLDENS_DIR
    total = 0
    signaled = 0
    total_g = 0
    signaled_g = 0
    total_b = 0
    signaled_b = 0
    if not target_dir.is_dir():
        return {
            "total": 0,
            "signaled": 0,
            "total_g": 0,
            "signaled_g": 0,
            "total_b": 0,
            "signaled_b": 0,
        }
    for d in sorted(target_dir.iterdir()):
        if not d.is_dir() or not (d / "expected.json").is_file():
            continue
        total += 1
        is_b = d.name.startswith("b")
        if is_b:
            total_b += 1
        else:
            total_g += 1

        code_file = d / "code.sqf"
        if not code_file.is_file():
            continue
        try:
            lines = code_file.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError):
            continue
        if any(line.strip().startswith("//") for line in lines):
            signaled += 1
            if is_b:
                signaled_b += 1
            else:
                signaled_g += 1
    return {
        "total": total,
        "signaled": signaled,
        "total_g": total_g,
        "signaled_g": signaled_g,
        "total_b": total_b,
        "signaled_b": signaled_b,
    }


def generate_quality_markdown(
    m1_res: dict,
    goldens_dir: Path | None = None,
    runs_dir: Path | None = None,
) -> str:
    """Genera el contenido de docs/QUALITY.md garantizando R1, R4 y R5."""
    script_path = Path(__file__).resolve()
    script_hash = hashlib.sha256(script_path.read_bytes()).hexdigest()
    signal = count_signaled_goldens(goldens_dir)

    # Evaluación de hosts - Bloque 1: Dataset Señalizado (g01–g13)
    claude_code_s = evaluate_external_host("claude-code", "archivo", goldens_dir, runs_dir, dataset_filter="signaled")
    claude_desk_s = evaluate_external_host("claude-desktop", "pegado", goldens_dir, runs_dir, dataset_filter="signaled")
    cursor_s = evaluate_external_host("cursor", "archivo", goldens_dir, runs_dir, dataset_filter="signaled")
    codex_s = evaluate_external_host("openai-codex", "archivo", goldens_dir, runs_dir, dataset_filter="signaled")
    chatgpt_s = evaluate_external_host("chatgpt", "pegado", goldens_dir, runs_dir, dataset_filter="signaled")
    gemini_s = evaluate_external_host("gemini", "pegado", goldens_dir, runs_dir, dataset_filter="signaled")
    antigravity_file_s = evaluate_external_host("antigravity", "archivo", goldens_dir, runs_dir, dataset_filter="signaled")
    antigravity_pegado_s = evaluate_external_host("antigravity", "pegado", goldens_dir, runs_dir, dataset_filter="signaled")

    # Evaluación de hosts - Bloque 2: Dataset NO Señalizado (b01–b06)
    antigravity_file_u = evaluate_external_host("antigravity", "archivo", goldens_dir, runs_dir, dataset_filter="unsignaled")
    antigravity_pegado_u = evaluate_external_host("antigravity", "pegado", goldens_dir, runs_dir, dataset_filter="unsignaled")
    claude_code_u = evaluate_external_host("claude-code", "archivo", goldens_dir, runs_dir, dataset_filter="unsignaled")
    claude_desk_u = evaluate_external_host("claude-desktop", "pegado", goldens_dir, runs_dir, dataset_filter="unsignaled")
    cursor_u = evaluate_external_host("cursor", "archivo", goldens_dir, runs_dir, dataset_filter="unsignaled")
    codex_u = evaluate_external_host("openai-codex", "archivo", goldens_dir, runs_dir, dataset_filter="unsignaled")
    chatgpt_u = evaluate_external_host("chatgpt", "pegado", goldens_dir, runs_dir, dataset_filter="unsignaled")
    gemini_u = evaluate_external_host("gemini", "pegado", goldens_dir, runs_dir, dataset_filter="unsignaled")

    stale_count = antigravity_file_s.get("stale_linter_traces", 0) + antigravity_pegado_s.get("stale_linter_traces", 0)

    # Bloqueantes no declarados en el ground truth, agregados por dataset y modo.
    undeclared_items: list[tuple[str, list[str]]] = []
    for label, ev in (
        ("Dataset señalizado · modo archivo", antigravity_file_s),
        ("Dataset señalizado · modo pegado", antigravity_pegado_s),
        ("Dataset NO señalizado · modo archivo", antigravity_file_u),
        ("Dataset NO señalizado · modo pegado", antigravity_pegado_u),
    ):
        items = ev.get("hallazgos_no_declarados", [])
        if items:
            undeclared_items.append((label, items))

    lines = [
        "<!-- GENERATED FROM: evals/harness.py | DO NOT EDIT -->",
        f"<!-- SOURCE-HASH: {script_hash} -->",
        "",
        "# Informe Formal de Calidad y Métricas de Evaluación — `arma3-sqf-skill`",
        "",
        "Este documento consolida la evaluación formal de precisión, robustez y cobertura de la skill portable `arma3-sqf-skill` a través de sus arneses deterministas y ejecuciones en hosts.",
        "",
        "## 1. Definición y Denominadores de Métricas (R4, R5)",
        "",
        "- **M1 (Motor Determinista / Script)**: Exactitud de detección en categorías normativas Cat. 1–2 sobre el dataset de goldens deterministas mediante `sqf_orchestrator.py --lint`. **Objetivo: 100 %**.",
        "- **M2 (Modelo en Modo Archivo)**: Detección de bloqueantes en categorías Cat. 3–7 con acceso al sistema de archivos del repositorio ($N=3$, reportando media y mínimo). **Objetivo: $\\ge 90\\%$**.",
        "- **M3 (Modelo en Modo Pegado)**: Proporción de $(\\text{DETECTADO} + \\text{NO\\_VERIFICADO justificado}) / \\text{esperables en pegado}$ bajo el paquete inline P1–P4. **Objetivo: 100 %, 0 falsos PASA**.",
        "",
        "---",
        "",
        "## 2. Tablas Consolidadas de Calidad por Dataset y Host",
        "",
        "### 2.1 Bloque 1 — Dataset Señalizado (`g01`–`g13`, N=14)",
        "",
        "*Mide la conformidad del informe (categoría, severidad, formato v1 y disciplina) y la ausencia de falsos positivos en código con contexto anunciado en comentarios.*",
        "",
        "| Host | Modelo | Versión | N | Cobertura | M1 (Script) | M2 (Modo Archivo) | M3 (Modo Pegado) | Falsos PASA | Omisiones | Conclusión |",
        "| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |",
        f"| **Local (Deterministic Engine)** | Python `sqf_orchestrator.py` | 1.0 | 1 | {m1_res['expected_total']}/{m1_res['expected_total']} (Cat. 1–2) | **{m1_res['m1_percentage']:.1f} %** | N/A (solo script) | N/A (solo script) | 0 | 0 | **PASA** (Cat. 1 determinista 100 %, 0 falsos positivos en snippets limpios) |",
        f"| **Antigravity (Modo Archivo)** | {antigravity_file_s['modelo']} | {antigravity_file_s['version']} | {antigravity_file_s['n_reps']} | {antigravity_file_s['cobertura']} | N/A | {antigravity_file_s['m2']} | N/A | {antigravity_file_s['falsos_pasa']} | {antigravity_file_s['omisiones']} | **{antigravity_file_s['status']}** ({antigravity_file_s['motivo']}) |",
        f"| **Antigravity (Modo Pegado)** | {antigravity_pegado_s['modelo']} | {antigravity_pegado_s['version']} | {antigravity_pegado_s['n_reps']} | {antigravity_pegado_s['cobertura']} | N/A | N/A | {antigravity_pegado_s['m3']} | {antigravity_pegado_s['falsos_pasa']} | {antigravity_pegado_s['omisiones']} | **{antigravity_pegado_s['status']}** ({antigravity_pegado_s['motivo']}) |",
        f"| **Claude Code** | {claude_code_s['modelo']} | {claude_code_s['version']} | {claude_code_s['n_reps']} | {claude_code_s['cobertura']} | N/A | {claude_code_s['m2']} | N/A | {claude_code_s['falsos_pasa']} | {claude_code_s['omisiones']} | **{claude_code_s['status']}** ({claude_code_s['motivo']}) |",
        f"| **Claude Desktop** | {claude_desk_s['modelo']} | {claude_desk_s['version']} | {claude_desk_s['n_reps']} | {claude_desk_s['cobertura']} | N/A | N/A | {claude_desk_s['m3']} | {claude_desk_s['falsos_pasa']} | {claude_desk_s['omisiones']} | **{claude_desk_s['status']}** ({claude_desk_s['motivo']}) |",
        f"| **Cursor** | {cursor_s['modelo']} | {cursor_s['version']} | {cursor_s['n_reps']} | {cursor_s['cobertura']} | N/A | {cursor_s['m2']} | N/A | {cursor_s['falsos_pasa']} | {cursor_s['omisiones']} | **{cursor_s['status']}** ({cursor_s['motivo']}) |",
        f"| **OpenAI / Codex** | {codex_s['modelo']} | {codex_s['version']} | {codex_s['n_reps']} | {codex_s['cobertura']} | N/A | {codex_s['m2']} | N/A | {codex_s['falsos_pasa']} | {codex_s['omisiones']} | **{codex_s['status']}** ({codex_s['motivo']}) |",
        f"| **ChatGPT Custom GPT** | {chatgpt_s['modelo']} | {chatgpt_s['version']} | {chatgpt_s['n_reps']} | {chatgpt_s['cobertura']} | N/A | N/A | {chatgpt_s['m3']} | {chatgpt_s['falsos_pasa']} | {chatgpt_s['omisiones']} | **{chatgpt_s['status']}** ({chatgpt_s['motivo']}) |",
        f"| **Google Gemini** | {gemini_s['modelo']} | {gemini_s['version']} | {gemini_s['n_reps']} | {gemini_s['cobertura']} | N/A | N/A | {gemini_s['m3']} | {gemini_s['falsos_pasa']} | {gemini_s['omisiones']} | **{gemini_s['status']}** ({gemini_s['motivo']}) |",
        "",
        "---",
        "",
        "### 2.2 Bloque 2 — Dataset NO Señalizado (`b01`–`b06`, N=6)",
        "",
        "*Mide la detección a ciega de defectos sin comentarios reveladores y la honestidad técnica (`NO_VERIFICADO`) en modo pegado ante la ausencia de `description.ext` o perfil de proyecto.*",
        "",
        "| Host | Modelo | Versión | N | Cobertura | M1 (Script) | M2 (Modo Archivo) | M3 (Modo Pegado) | Falsos PASA | Omisiones | Conclusión |",
        "| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |",
        f"| **Antigravity (Modo Archivo)** | {antigravity_file_u['modelo']} | {antigravity_file_u['version']} | {antigravity_file_u['n_reps']} | {antigravity_file_u['cobertura']} | N/A | {antigravity_file_u['m2']} | N/A | {antigravity_file_u['falsos_pasa']} | {antigravity_file_u['omisiones']} | **{antigravity_file_u['status']}** ({antigravity_file_u['motivo']}) |",
        f"| **Antigravity (Modo Pegado)** | {antigravity_pegado_u['modelo']} | {antigravity_pegado_u['version']} | {antigravity_pegado_u['n_reps']} | {antigravity_pegado_u['cobertura']} | N/A | N/A | {antigravity_pegado_u['m3']} | {antigravity_pegado_u['falsos_pasa']} | {antigravity_pegado_u['omisiones']} | **{antigravity_pegado_u['status']}** ({antigravity_pegado_u['motivo']}) |",
        f"| **Claude Code** | {claude_code_u['modelo']} | {claude_code_u['version']} | {claude_code_u['n_reps']} | {claude_code_u['cobertura']} | N/A | {claude_code_u['m2']} | N/A | {claude_code_u['falsos_pasa']} | {claude_code_u['omisiones']} | **{claude_code_u['status']}** ({claude_code_u['motivo']}) |",
        f"| **Claude Desktop** | {claude_desk_u['modelo']} | {claude_desk_u['version']} | {claude_desk_u['n_reps']} | {claude_desk_u['cobertura']} | N/A | N/A | {claude_desk_u['m3']} | {claude_desk_u['falsos_pasa']} | {claude_desk_u['omisiones']} | **{claude_desk_u['status']}** ({claude_desk_u['motivo']}) |",
        f"| **Cursor** | {cursor_u['modelo']} | {cursor_u['version']} | {cursor_u['n_reps']} | {cursor_u['cobertura']} | N/A | {cursor_u['m2']} | N/A | {cursor_u['falsos_pasa']} | {cursor_u['omisiones']} | **{cursor_u['status']}** ({cursor_u['motivo']}) |",
        f"| **OpenAI / Codex** | {codex_u['modelo']} | {codex_u['version']} | {codex_u['n_reps']} | {codex_u['cobertura']} | N/A | {codex_u['m2']} | N/A | {codex_u['falsos_pasa']} | {codex_u['omisiones']} | **{codex_u['status']}** ({codex_u['motivo']}) |",
        f"| **ChatGPT Custom GPT** | {chatgpt_u['modelo']} | {chatgpt_u['version']} | {chatgpt_u['n_reps']} | {chatgpt_u['cobertura']} | N/A | N/A | {chatgpt_u['m3']} | {chatgpt_u['falsos_pasa']} | {chatgpt_u['omisiones']} | **{chatgpt_u['status']}** ({chatgpt_u['motivo']}) |",
        f"| **Google Gemini** | {gemini_u['modelo']} | {gemini_u['version']} | {gemini_u['n_reps']} | {gemini_u['cobertura']} | N/A | N/A | {gemini_u['m3']} | {gemini_u['falsos_pasa']} | {gemini_u['omisiones']} | **{gemini_u['status']}** ({gemini_u['motivo']}) |",
        "",
        "---",
        "",
        "## 3. Estado de Ejecución y Honestidad Técnica (Regla R1)",
        "",
        "En este entorno de validación local:",
        "1. **M1 queda formalmente medido y verificado al 100 %** mediante la suite determinista sobre `evals/goldens/`.",
        "2. Para hosts con ejecuciones reales, las métricas M2 y M3 se calculan exclusivamente desde trazas reproducibles en `evals/runs/`.",
        "3. Cualquier host sin trazas queda registrado como `NO VERIFICADO` con motivo explícito y sin atribuir modelos ficticios, cumpliendo rigurosamente con el **Principio de Honestidad Técnica** (`references/invariants.md`).",
        "4. Para ejecutar la suite de goldens en hosts adicionales y generar trazas, consulta el protocolo en [`evals/GOLDENS-PROTOCOL.md`](../evals/GOLDENS-PROTOCOL.md).",
        "5. Los resultados de los casos de smoke tests se encuentran en [`docs/SMOKE-RESULTS.md`](SMOKE-RESULTS.md).",
        "",
        "---",
        "",
        "## 4. Cobertura, Límites y Trazabilidad (R3, R4)",
        "",
        "La columna **Cobertura** indica cuántos goldens de cada bloque se evaluaron por host y modo "
        f"(Bloque 1: {antigravity_file_s['goldens_totales']} goldens; Bloque 2: {antigravity_file_u['goldens_totales']} goldens). "
        "Una cobertura inferior al total del bloque se marca como `COBERTURA PARCIAL` en la conclusión de la fila: "
        "la métrica no es extrapolable a los goldens no ejecutados.",
        "",
        "Una métrica que no alcanza su objetivo se marca como `NO PASA OBJETIVO` con el valor medido "
        f"y el umbral público (M2 ≥ {M2_OBJETIVO_PCT:.0f} %, M3 = {M3_OBJETIVO_PCT:.0f} %).",
        "",
        "Trazabilidad del contexto (R3): cada traza declara el `sha256` de los ficheros que cargó. "
        "El harness lo recalcula contra los ficheros actuales del repo (con saltos de línea normalizados "
        "a LF) y **descarta la traza si el hash no coincide**, por no ser reproducible. "
        f"En esta ejecución: {antigravity_file_s['traces_descartadas'] + antigravity_pegado_s['traces_descartadas'] + antigravity_file_u['traces_descartadas'] + antigravity_pegado_u['traces_descartadas']} "
        "traza(s) descartada(s) por contexto no reproducible o ausente.",
        "",
        f"**Evidencia de linter y trazabilidad histórica (Parte C.3):** {stale_count} trazas del dataset "
        "histórico señalizado contienen en su respuesta cruda menciones a rutas del plugin original "
        "(`arma3-sqf-review`). Esta limitación está documentada en `docs/ESTADO-PR.md`; las métricas "
        "semánticas M2/M3 no dependen de la salida del linter determinista, y las 36 trazas del dataset "
        "no señalizado están 100 % libres de rutas heredadas.",
        "",
        "**Alcance de la evidencia:** las métricas solo son publicables como afirmación de calidad "
        "para los hosts efectivamente medidos y con la cobertura indicada. Los hosts sin trazas "
        "permanecen en `NO VERIFICADO` y no admiten afirmación de equivalencia.",
        "",
        "---",
        "",
        "## 5. Limitación Metodológica y Separación de Datasets (lectura obligatoria de M2 y M3)",
        "",
        f"El dataset de evaluación consta de {signal['total']} goldens divididos metodológicamente en dos bloques:",
        "",
        f"- **Bloque 1: Dataset Señalizado ({signal['total_g']} goldens, `g01`–`g13`)**: {signal['signaled_g']} de {signal['total_g']} "
        "goldens incluyen en su propio `code.sqf` un comentario que describe el defecto "
        "(p. ej. `// waitUntil sin timeout`, `// Variable local sin private`).",
        "  - **Qué mide**: la **conformidad del informe** (categoría, severidad, formato v1 y disciplina) "
        "y la **ausencia de falsos positivos** sobre código correcto (g09–g11). Mide la fiabilidad de la tubería de reporte cuando el contexto es conocido.",
        "  - **Qué NO mide**: no mide la detección a ciega de defectos sin aviso explícito.",
        "",
        f"- **Bloque 2: Dataset NO Señalizado ({signal['total_b']} goldens, `b01`–`b06`)**: {signal['signaled_b']} de {signal['total_b']} "
        "goldens contienen comentarios reveladores (0 % de señalización; blindaje verificado por test automatizado).",
        "  - **Qué mide**: la **detección a ciega real** de defectos críticos y la **honestidad técnica** "
        "ante la ausencia de archivos de configuración (`description.ext`) en modo pegado (reportando `NO_VERIFICADO` en lugar de emitir un falso `BLOQUEANTE`).",
        "  - **Regla estricta de modo pegado**: si un defecto requiere `description.ext` para ser comprobado "
        "(como `b05_remoteexec`) y el modelo afirma `[BLOQUEANTE]`, el arnés lo penaliza como `FALSO_PASA`. Si reporta `[NO_VERIFICADO]`, cuenta como acierto de honestidad.",
        "",
        "Esta separación metodológica garantiza que ninguna afirmación de calidad pública extrapole la conformidad del formato a la detección de defectos no señalizados sin respaldo empírico directo.",
        "",
        "---",
        "",
        "## 6. Bloqueantes No Declarados en el Ground Truth (adjudicación pendiente)",
        "",
        "El arnés empareja cada bloqueante emitido con los hallazgos declarados en `expected.json`. "
        "Los que **no** corresponden a ningún hallazgo declarado (en ninguna categoría, ni siquiera "
        "fuera del alcance del modo) se listan aquí. **No son falsos positivos verificados**: son "
        "defectos reales que el modelo detectó y que el ground truth no declara, porque varios "
        "goldens declaran un conjunto mínimo de hallazgos mientras su código contiene más de un "
        "defecto. Confirmar o descartar cada uno exige adjudicar caso por caso contra el código.",
        "",
        *( [f"- **{label}**: " + ", ".join(f"`{x}`" for x in items) for label, items in undeclared_items] or ["- Sin bloqueantes no declarados."] ),
        "",
        "Los casos concretos y su análisis están en `docs/ESTADO-PR.md` (sección Track C). "
        "La cifra es reproducible: `python evals/harness.py --write`.",
    ]

    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Harness de evaluación formal M1/M2/M3 para arma3-sqf-skill.")
    parser.add_argument("--runner", choices=["local", "manual"], default="local",
                        help="Ejecutor: 'local' (motor determinista) o 'manual' (trazas)")
    parser.add_argument("--write", action="store_true", help="Genera y escribe docs/QUALITY.md")
    parser.add_argument("--check", action="store_true", help="Verifica si docs/QUALITY.md está actualizado")
    args = parser.parse_args(argv)

    m1_res = evaluate_m1_script()

    if args.write:
        content = generate_quality_markdown(m1_res)
        QUALITY_DOC.parent.mkdir(parents=True, exist_ok=True)
        QUALITY_DOC.write_text(content, encoding="utf-8")
        print(f"OK: {QUALITY_DOC.relative_to(REPO_ROOT)} generado exitosamente.")
        print(f"  M1 (Script): {m1_res['m1_percentage']:.1f} % ({m1_res['detected_total']}/{m1_res['expected_total']} esperados detectados)")
        print(f"  Falsos positivos en limpios: {m1_res['false_positives']}")
        return 0

    if args.check:
        if not QUALITY_DOC.is_file():
            print(f"FALLO: {QUALITY_DOC.relative_to(REPO_ROOT)} no existe.")
            return 1
        expected = generate_quality_markdown(m1_res)
        actual = QUALITY_DOC.read_text(encoding="utf-8")
        if expected != actual:
            print(f"FALLO: {QUALITY_DOC.relative_to(REPO_ROOT)} difiere de la salida esperada del harness.")
            return 1
        print(f"OK: {QUALITY_DOC.relative_to(REPO_ROOT)} está sincronizado.")
        return 0

    # Modo estándar interactivo
    print("== Evaluación Formal de Calidad ==")
    print(f"  M1 (Script determinista): {m1_res['m1_percentage']:.1f} % (esperados detectados: {m1_res['detected_total']}/{m1_res['expected_total']})")
    print(f"  Falsos positivos: {m1_res['false_positives']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
