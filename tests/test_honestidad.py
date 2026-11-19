"""Tests de honestidad de evidencia y ausencia de afirmaciones no verificadas (R1, R4, R5, CANON:HONESTIDAD).

Garantiza que ninguna documentación, tabla o informe declare modelos reales,
métricas o veredictos para hosts externos sin trazas reproducibles en evals/runs/.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
QUALITY_DOC = REPO_ROOT / "docs" / "QUALITY.md"
COMPATIBILIDAD_DOC = REPO_ROOT / "docs" / "COMPATIBILIDAD.md"
RUNS_DIR = REPO_ROOT / "evals" / "runs"


def _parse_compatibilidad_evidence_table() -> list[dict[str, str]]:
    assert COMPATIBILIDAD_DOC.is_file(), f"Falta {COMPATIBILIDAD_DOC}"
    text = COMPATIBILIDAD_DOC.read_text(encoding="utf-8")

    section_match = re.search(r"## 3\. Estado de Evidencia por Host.*?\n(\|.*?)(?=\n## |\Z)", text, re.S)
    assert section_match, "No se encontró la sección '## 3. Estado de Evidencia por Host' en docs/COMPATIBILIDAD.md"

    rows: list[dict[str, str]] = []
    lines = [line.strip() for line in section_match.group(1).splitlines() if line.strip().startswith("|")]
    for line in lines[2:]:  # saltar cabecera y separador
        parts = [p.strip().replace("**", "").replace("`", "") for p in line.split("|")[1:-1]]
        if len(parts) >= 5:
            rows.append({
                "host": parts[0],
                "modo": parts[1],
                "cobertura": parts[2],
                "metricas": parts[3],
                "estado": parts[4],
            })
    return rows


def test_no_fabricated_models_or_unverified_claims() -> None:
    """Ningún host externo declara cobertura ni estado exitoso sin traza real en evals/runs/."""
    rows = _parse_compatibilidad_evidence_table()
    assert len(rows) >= 6, "La tabla de evidencia por host está vacía o incompleta"

    has_external_traces = RUNS_DIR.is_dir() and any(
        p for p in RUNS_DIR.glob("*/*/*.json") if "antigravity" not in p.parts
    )

    for r in rows:
        host = r["host"]
        estado = r["estado"]
        cobertura = r["cobertura"]

        # Antigravity cuenta con 120 trazas medidas
        if host == "Antigravity":
            assert "PASA" in estado or "NO PASA OBJETIVO" in estado
            continue

        # Hosts externos sin traza: obligatoriamente NO VERIFICADO y 0/20
        if not has_external_traces:
            assert "NO VERIFICADO" in estado, (
                f"Host externo {host} tiene estado {estado} sin trazas reales en evals/runs/"
            )
            assert cobertura.startswith("0/"), (
                f"Host externo {host} declara cobertura {cobertura} sin trazas reales"
            )


def test_quality_doc_honestidad_unverified_hosts() -> None:
    """docs/QUALITY.md declara estrictamente NO VERIFICADO para los 6 hosts no medidos."""
    assert QUALITY_DOC.is_file(), f"Falta {QUALITY_DOC}"
    text = QUALITY_DOC.read_text(encoding="utf-8")

    unverified_hosts = [
        "Claude Code",
        "Claude Desktop",
        "Cursor",
        "OpenAI / Codex",
        "ChatGPT Custom GPT",
        "Google Gemini",
    ]

    has_external_traces = RUNS_DIR.is_dir() and any(
        p for p in RUNS_DIR.glob("*/*/*.json") if "antigravity" not in p.parts
    )

    if not has_external_traces:
        for host in unverified_hosts:
            assert host in text, f"Falta mención al host {host} en docs/QUALITY.md"
            # Verificar que en la tabla de hosts figura como NO VERIFICADO
            host_pattern = re.compile(rf"\|\s*\*\*{re.escape(host)}\*\*\s*\|.*?\|\s*`?(NO VERIFICADO|NO_VERIFICADO)`?\s*\|")
            assert host_pattern.search(text), f"Host {host} no está declarado como NO VERIFICADO en docs/QUALITY.md"
