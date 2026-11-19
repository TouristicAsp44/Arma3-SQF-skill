import subprocess
import sys
from pathlib import Path

import pytest
from run_sqflint import main as run_sqflint_main
from run_sqflint import parse_error_line


def test_empty_dir_exits_3(tmp_path: Path):
    """Demuestra que un directorio sin archivos .sqf produce código de salida 3."""
    empty_dir = tmp_path / "empty_folder"
    empty_dir.mkdir()

    # Ejecución vía función main (captura SystemExit 3)
    with pytest.raises(SystemExit) as excinfo:
        run_sqflint_main([str(empty_dir)])
    assert excinfo.value.code == 3

    # Ejecución vía subprocess
    run_sqflint_script = Path(__file__).resolve().parent.parent / "skills" / "arma3-sqf-skill" / "references" / "run_sqflint.py"
    proc = subprocess.run(
        [sys.executable, str(run_sqflint_script), str(empty_dir)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 3
    assert "NO SE ENCONTRARON ARCHIVOS" in proc.stdout or "Directorio vacío" in proc.stdout


def test_warning_line_is_normalized():
    """Demuestra que la advertencia se normaliza al formato archivo:línea: warning: mensaje."""
    sample_raw_warning = '[42, 1]:warning:Local variable "_temp" is not private'
    normalized = parse_error_line("scripts/test.sqf", sample_raw_warning)
    assert normalized == 'scripts/test.sqf:42: warning: Local variable "_temp" is not private'
