#!/usr/bin/env python3
"""Punto de entrada único de validación local de `arma3-sqf-skill`.

Uso:
    python scripts/check.py --fase PR-1
    python scripts/check.py --fase PR-2
    python scripts/check.py --fase todos

Códigos de salida:
    0 -> todo lo aplicable a la fase pasó
    1 -> al menos una verificación falló (o una esperada en la fase quedó SKIPPED)

Reglas de fase (R4):
    - Cada verificación declara la fase en la que empieza a ser exigible.
    - Un test marcado como SKIPPED cuando la fase ya lo exige es un FALLO:
      "todavía no aplica" y "se ha olvidado crearlo" no son lo mismo.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TESTS_DIR = REPO_ROOT / "tests"

PHASES = ["PR-1", "PR-2", "PR-3", "PR-4", "PR-5", "PR-6", "PR-7"]

# (etiqueta, node_ids de pytest, fase de exigencia, skip_es_fallo)
# En la suite completa un skip puede ser legítimo (test de una fase posterior);
# en los checks dirigidos, un skip en fase ya exigida es un fallo.
CHECKS: list[tuple[str, list[str], str, bool]] = [
    ("pytest (suite completa)", ["tests/"], "PR-1", False),
    ("rutas absolutas", ["tests/test_no_absolute_paths.py"], "PR-1", True),
    (
        "anclas CANON únicas",
        ["tests/test_canonical_uniqueness.py::test_canonical_anchors_exist_once"],
        "PR-1",
        True,
    ),
    ("esquema de informe v1", ["tests/test_report_schema.py"], "PR-2", True),
    ("estructura de la skill", ["tests/test_skill_structure.py"], "PR-2", True),
    ("hashes de regiones y extractos", ["tests/test_generated_files_hash.py"], "PR-2", True),
    (
        "unicidad de definiciones N3",
        ["tests/test_canonical_uniqueness.py::test_n3_definitions_not_duplicated_outside_canonical"],
        "PR-2",
        True,
    ),
    ("base de conocimiento SQLite", ["tests/test_wiki_db.py"], "PR-3", True),
    ("paquetes inline", ["tests/test_inline_packages.py"], "PR-4", True),
    ("adaptadores host", ["tests/test_host_adapters.py"], "PR-4", True),
    ("goldens", ["tests/test_goldens_dataset.py"], "PR-5", True),
    ("evidencia smoke", ["tests/test_smoke_evidence.py"], "PR-5", True),
    ("cobertura paquete inline", ["tests/test_inline_package_coverage.py"], "PR-5", True),
    ("mcp handshake", ["tests/test_mcp_server.py::test_mcp_handshake_and_tools_list"], "PR-6", True),
    (
        "mcp contrato de informe v1",
        [
            "tests/test_mcp_server.py::test_sqf_analyze_returns_valid_v1_report",
            "tests/test_mcp_server.py::test_sqf_analyze_byte_for_byte_parity_with_engine",
        ],
        "PR-6",
        True,
    ),
    (
        "integraciones sin rutas absolutas",
        ["tests/test_no_absolute_paths.py::test_no_absolute_paths_in_integrations_artifacts"],
        "PR-6",
        True,
    ),
    (
        "snippet MCP coherente con el CLI",
        ["tests/test_host_adapters.py::test_claude_desktop_snippet_contract_with_cli"],
        "PR-6",
        True,
    ),
    ("docs MCP", ["tests/test_mcp_server.py::test_mcp_and_privacy_docs_exist_and_complete"], "PR-6", True),
    ("paridad de agentes verificable", ["tests/test_agent_port_parity.py"], "PR-7", True),
]

_SUMMARY_RE = re.compile(r"(?P<count>\d+)\s+(?P<kind>passed|failed|skipped|error|errors|xfailed|xfailed)\b")


def _phase_index(phase: str) -> int:
    return PHASES.index(phase)


def _run_pytest(node_ids: list[str]) -> tuple[int, int, int, str]:
    """Ejecuta pytest y devuelve (fallos, omitidos, total_ok, salida)."""
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", *node_ids, "-q", "--no-header", "-p", "no:cacheprovider", "-rs"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    output = (proc.stdout or "") + (proc.stderr or "")
    counts = {"passed": 0, "failed": 0, "skipped": 0, "error": 0}
    for match in _SUMMARY_RE.finditer(output):
        kind = match.group("kind")
        if kind.startswith("xfail"):
            continue
        if kind.startswith("error"):
            kind = "error"
        elif kind == "failed":
            kind = "failed"
        elif kind == "skipped":
            kind = "skipped"
        elif kind == "passed":
            kind = "passed"
        counts[kind] = counts.get(kind, 0) + int(match.group("count"))

    failures = counts["failed"] + counts["error"]
    skipped = counts["skipped"]
    passed = counts["passed"]
    return failures, skipped, passed, output


def _check(label: str, node_ids: list[str], skip_is_failure: bool) -> tuple[bool, str]:
    failures, skipped, passed, output = _run_pytest(node_ids)
    if failures:
        detail = "\n".join(output.strip().splitlines()[-12:])
        return False, f"{failures} fallo(s)\n{detail}"
    if skipped and skip_is_failure:
        detail = "\n".join(
            ln for ln in output.splitlines() if ln.startswith("SKIPPED")
        ) or "sin detalle"
        return False, f"{skipped} test(s) omitido(s) en una fase que ya los exige:\n{detail}"
    return True, f"{passed} test(s) en verde"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validación local de arma3-sqf-skill")
    parser.add_argument(
        "--fase",
        default="todos",
        help="Fase a validar (PR-1..PR-7) o 'todos'.",
    )
    args = parser.parse_args(argv)

    if args.fase != "todos" and args.fase not in PHASES:
        print(f"ERROR: fase desconocida {args.fase!r}. Validas: {', '.join(PHASES)} o 'todos'.")
        return 1

    limit = len(PHASES) if args.fase == "todos" else _phase_index(args.fase) + 1
    failures: list[str] = []

    print(f"== Validación local: fase {args.fase} ==")
    for label, node_ids, required_phase, skip_is_failure in CHECKS:
        if _phase_index(required_phase) >= limit:
            print(f"  [N/A  ] {label} (exigible desde {required_phase})")
            continue
        ok, detail = _check(label, node_ids, skip_is_failure)
        if ok:
            print(f"  [ OK  ] {label} — {detail}")
        else:
            first = detail.strip().splitlines()[0] if detail.strip() else ""
            print(f"  [FALLA] {label}: {first}")
            failures.append(label)

    if failures:
        print(f"\nFALLO: {len(failures)} verificación(es) en rojo -> {', '.join(failures)}")
        return 1

    print("\nTODO EN VERDE para la fase solicitada.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
