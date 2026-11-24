import subprocess
import sys
from pathlib import Path

import pytest
from run_sqflint import locate_sqflint, main as run_sqflint_main, parse_error_line


def test_empty_dir_exits_3(tmp_path: Path):
    """Demuestra que un directorio sin archivos .sqf produce código de salida 3."""
    empty_dir = tmp_path / "empty_folder"
    empty_dir.mkdir()

    # Ejecución vía función main (captura SystemExit 3)
    with pytest.raises(SystemExit) as excinfo:
        run_sqflint_main([str(empty_dir)])
    assert excinfo.value.code == 3

    # Ejecución vía subprocess
    run_sqflint_script = Path(__file__).resolve().parent.parent / "skills" / "arma3-sqf-skill" / "scripts" / "run_sqflint.py"
    if not run_sqflint_script.exists():
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


def test_sqflint_unavailable_exits_3_and_emits_no_verificado(tmp_path: Path, monkeypatch, capsys: pytest.CaptureFixture[str]):
    """Cuando sqflint no está disponible, sale con código 3 y emite [NO_VERIFICADO]."""
    test_sqf = tmp_path / "test.sqf"
    test_sqf.write_text("hint 'test';", encoding="utf-8")

    import run_sqflint
    monkeypatch.setattr(run_sqflint, "locate_sqflint", lambda: None)

    with pytest.raises(SystemExit) as excinfo:
        run_sqflint_main([str(test_sqf)])
    assert excinfo.value.code == 3

    captured = capsys.readouterr().out
    assert "SQFLINT_NO_DISPONIBLE" in captured
    assert "[NO_VERIFICADO]" in captured


def test_locate_sqflint_detects_command():
    """Verifica que locate_sqflint localiza sqflint en el entorno."""
    cmd = locate_sqflint()
    assert cmd is not None
    assert isinstance(cmd, list)
    assert len(cmd) >= 1


def test_clean_file_exits_0(tmp_path: Path):
    """Un archivo sin errores sintácticos sale con código 0."""
    clean_sqf = tmp_path / "clean.sqf"
    clean_sqf.write_text("params ['_unit']; _unit setDamage 0;", encoding="utf-8")

    with pytest.raises(SystemExit) as excinfo:
        run_sqflint_main([str(clean_sqf)])
    assert excinfo.value.code == 0


def test_syntax_error_file_exits_1(tmp_path: Path):
    """Un archivo con errores sintácticos sale con código 1."""
    broken_sqf = tmp_path / "broken.sqf"
    broken_sqf.write_text("hint 'unclosed string;", encoding="utf-8")

    with pytest.raises(SystemExit) as excinfo:
        run_sqflint_main([str(broken_sqf)])
    assert excinfo.value.code == 1

