"""Tests de verificación de evidencia en docs/QUALITY.md y harness (R1, R4, R5)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
QUALITY_DOC = REPO_ROOT / "docs" / "QUALITY.md"
RUNS_DIR = REPO_ROOT / "evals" / "runs"


def test_quality_doc_in_sync_with_harness() -> None:
    """docs/QUALITY.md está generado y sincronizado con evals/harness.py --check."""
    proc = subprocess.run(
        [sys.executable, "evals/harness.py", "--check"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, f"harness.py --check falló:\n{proc.stdout}\n{proc.stderr}"


def test_quality_doc_has_no_fabricated_models() -> None:
    """docs/QUALITY.md no declara modelos ni métricas sin trazas en evals/runs/."""
    assert QUALITY_DOC.is_file(), "Falta docs/QUALITY.md"
    text = QUALITY_DOC.read_text(encoding="utf-8")

    # M1 debe estar verificado al 100 %
    assert "100.0 %" in text, "M1 no está al 100.0 %"

    # Si no hay trazas reales en runs/, los hosts externos deben figurar como NO_VERIFICADO
    has_traces = RUNS_DIR.is_dir() and any(RUNS_DIR.glob("*/*/*.json"))
    if not has_traces:
        assert "NO VERIFICADO" in text
        assert "sin ejecución" in text
        # Ningún nombre de modelo específico atribuido a hosts externos
        for forbidden in ["Claude 3.7", "GPT-4o", "gemini-2.0"]:
            assert forbidden not in text, f"Modelo no ejecutado {forbidden} encontrado en docs/QUALITY.md"
