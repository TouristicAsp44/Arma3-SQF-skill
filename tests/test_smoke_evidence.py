"""Tests de honestidad de evidencia en Smoke Tests (R1, R5, CANON:HONESTIDAD)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SMOKE_RESULTS_MD = REPO_ROOT / "docs" / "SMOKE-RESULTS.md"
RUNS_DIR = REPO_ROOT / "evals" / "runs"


def _parse_smoke_table() -> list[dict[str, str]]:
    assert SMOKE_RESULTS_MD.is_file(), f"Falta {SMOKE_RESULTS_MD}"
    text = SMOKE_RESULTS_MD.read_text(encoding="utf-8")

    rows: list[dict[str, str]] = []
    # Líneas de tabla Markdown: | **Host** | Caso | Categoría | Modelo | **Veredicto** | Motivo |
    for line in text.splitlines():
        if not line.startswith("|") or "---" in line or "Host | Caso" in line:
            continue
        parts = [p.strip().replace("**", "") for p in line.split("|")[1:-1]]
        if len(parts) >= 6:
            rows.append({
                "host": parts[0],
                "caso": parts[1],
                "categoria": parts[2],
                "modelo_version": parts[3],
                "veredicto": parts[4],
                "motivo": parts[5],
            })
    return rows


def test_smoke_results_in_sync_with_runner() -> None:
    """docs/SMOKE-RESULTS.md está sincronizado con la salida del runner."""
    proc = subprocess.run(
        [sys.executable, "evals/smoke/run_smoke.py", "--check"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, f"run_smoke.py --check falló:\n{proc.stdout}\n{proc.stderr}"


def test_no_fabricated_models_or_unverified_claims() -> None:
    """Ninguna fila nombra un modelo real ni emite veredicto sin traza en evals/runs/."""
    rows = _parse_smoke_table()
    assert len(rows) >= 6, "La tabla de smoke está vacía o incompleta"

    for r in rows:
        host = r["host"]
        modelo = r["modelo_version"]
        veredicto = r["veredicto"]

        # Local Engine se valida localmente
        if host == "Local (Engine)":
            assert modelo == "Deterministic Python Engine"
            assert veredicto in ("DETECTADO", "SILENCIO")
            continue

        # Hosts externos sin traza: obligatoriamente NO_VERIFICADO y N/A
        if not (RUNS_DIR.is_dir() and any(RUNS_DIR.glob("*/*/*.json"))):
            assert veredicto == "NO_VERIFICADO", (
                f"Fila {host} / {r['caso']} tiene veredicto {veredicto} sin trazas reales en evals/runs/"
            )
            assert "N/A" in modelo or "sin ejecución" in modelo or "local" in modelo.lower(), (
                f"Fila {host} / {r['caso']} nombra un modelo ({modelo}) sin traza real"
            )
