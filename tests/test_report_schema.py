"""Test de contrato del informe estructurado (esquema v1).

Este test NO lee el markdown: ejecuta el motor real (`run_lint`) y valida la
SALIDA. Es el contrato compartido entre el script, el prompt de la skill, los
evals y cualquier consumidor externo (MCP).

Esquema v1 — INFORME DE HALLAZGOS:
    REPORT_SCHEMA_VERSION: 1
    [BLOQUEANTE|SUGERENCIA|NO_VERIFICADO] archivo:linea (disciplina): descripcion
    RESUMEN: bloqueantes=N; sugerencias=N; no_verificado=N

Esquema v1 — INFORME DE MODO (documento DISTINTO):
    REPORT_SCHEMA_VERSION: 1
    MODO: <modo>
    MOTIVO: <motivo>
    RESUMEN: modo=<modo>; escalado=<si|no>
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from sqf_models import REPORT_SCHEMA_VERSION, format_findings_report, summarize_escalation
from sqf_orchestrator import run_lint

FINDING_LINE_RE = re.compile(
    r"^\[(?P<sev>BLOQUEANTE|SUGERENCIA|NO_VERIFICADO)\] (?P<file>.+):(?P<line>\d+) \((?P<disc>[^)]+)\): (?P<desc>.+)$"
)
FINDINGS_RESUMEN_RE = re.compile(r"^RESUMEN: bloqueantes=\d+; sugerencias=\d+; no_verificado=\d+$")
MODE_RESUMEN_RE = re.compile(r"^RESUMEN: modo=\S+; escalado=(si|no)$")


def test_report_schema_version_is_declared() -> None:
    assert REPORT_SCHEMA_VERSION == 1


def test_findings_report_matches_schema_v1() -> None:
    report = format_findings_report([])
    lines = report.splitlines()
    assert lines[0] == "REPORT_SCHEMA_VERSION: 1"
    assert FINDINGS_RESUMEN_RE.match(lines[-1]), f"RESUMEN con formato inesperado: {lines[-1]!r}"


def test_mode_report_matches_schema_v1() -> None:
    report = summarize_escalation("Estándar", "motivo de prueba")
    lines = report.splitlines()
    assert lines[0] == "REPORT_SCHEMA_VERSION: 1"
    assert "MODO: Estándar" in lines
    assert MODE_RESUMEN_RE.match(lines[-1]), f"RESUMEN de modo con formato inesperado: {lines[-1]!r}"


def test_script_output_matches_report_schema_v1(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """La SALIDA REAL del script cumple el esquema v1 declarado."""
    leak_file = tmp_path / "scope_leak.sqf"
    leak_file.write_text("private _y = _z;", encoding="utf-8")

    rc = run_lint(target=str(leak_file))
    captured = capsys.readouterr().out
    lines = [ln for ln in captured.splitlines() if ln.strip()]

    assert rc in (0, 10), f"Código de salida inesperado: {rc}"
    assert lines, "El script no produjo salida"

    # 1) Primera línea: versión de esquema.
    assert lines[0] == "REPORT_SCHEMA_VERSION: 1", f"Primera línea inesperada: {lines[0]!r}"

    # 2) Toda línea de hallazgo (las que empiezan por "[") cumple el formato.
    #    El informe puede incluir además el bloque del ítem 9 (tabla de
    #    estados), que es otro documento apendado, no una línea de hallazgo.
    findings = [ln for ln in lines[1:] if ln.startswith("[")]
    assert findings, "El informe no contiene ninguna línea de hallazgo"
    for line in findings:
        assert FINDING_LINE_RE.match(line), f"Línea de hallazgo con formato inesperado: {line!r}"

    # 3) La sección RESUMEN de hallazgos está presente y con el formato declarado.
    resumen_lines = [ln for ln in lines if ln.startswith("RESUMEN:")]
    assert resumen_lines, "No hay línea RESUMEN en la salida"
    assert any(FINDINGS_RESUMEN_RE.match(ln) for ln in resumen_lines), (
        f"RESUMEN con formato inesperado: {resumen_lines[-1]!r}"
    )

    # 4) El informe de hallazgos NO debe contener el RESUMEN de modo.
    assert not any(MODE_RESUMEN_RE.match(ln) for ln in lines), (
        "El informe de hallazgos contiene un RESUMEN de modo"
    )


def test_findings_report_and_mode_report_are_distinct_documents() -> None:
    """Los dos RESUMEN del motor tienen formatos distintos y no se confunden."""
    hallazgos = format_findings_report([]).splitlines()
    modo = summarize_escalation("Micro").splitlines()

    assert any(FINDINGS_RESUMEN_RE.match(ln) for ln in hallazgos)
    assert any(MODE_RESUMEN_RE.match(ln) for ln in modo)
    assert not any(MODE_RESUMEN_RE.match(ln) for ln in hallazgos)
    assert not any(FINDINGS_RESUMEN_RE.match(ln) for ln in modo)
