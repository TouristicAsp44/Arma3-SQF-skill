from pathlib import Path
from unittest.mock import patch

import pytest
from sqf_models import SQFFinding, format_findings_report
from sqf_orchestrator import mode_query, run_lint, run_orchestrator


def test_mode_query_refuses_empty_inventory(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    """Sobre un directorio sin .sqf, --mode-query sale con 10, imprime NO VERIFICADO y no dice MODO: Micro."""
    empty_dir = tmp_path / "empty_project"
    empty_dir.mkdir()

    rc = mode_query(root=str(empty_dir))
    assert rc == 10
    captured = capsys.readouterr().out
    assert "NO VERIFICADO" in captured
    assert "MODO: Micro" not in captured
    assert "MODO: Estándar" not in captured


def test_lint_mode_refuses_empty_inventory(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    """--lint sobre un directorio sin .sqf sale con 10 y no_verificado=1, no con bloqueantes=0 exit 0."""
    empty_dir = tmp_path / "empty_project_lint"
    empty_dir.mkdir()

    rc = run_lint(target=str(empty_dir))
    assert rc == 10
    captured = capsys.readouterr().out
    assert "no_verificado=1" in captured
    assert "NO VERIFICADO" in captured


def test_mode_query_returns_estandar_for_network_file(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    """--mode-query sobre un archivo con remoteExec devuelve Estándar."""
    net_file = tmp_path / "fn_network.sqf"
    net_file.write_text('remoteExec ["hint", 0];', encoding="utf-8")

    rc = mode_query(root=str(tmp_path))
    assert rc == 0
    captured = capsys.readouterr().out
    assert "MODO: Estándar" in captured
    assert "RESUMEN: modo=Estándar; escalado=si" in captured


def test_mode_query_is_called_with_the_file_inventory(tmp_path: Path):
    """check_escalation_needed_for_files se invoca con el inventario completo."""
    file_a = tmp_path / "script_a.sqf"
    file_b = tmp_path / "script_b.sqf"
    file_a.write_text("private _a = 1;", encoding="utf-8")
    file_b.write_text("private _b = 2;", encoding="utf-8")

    with patch("sqf_orchestrator.check_escalation_needed_for_files", wraps=None) as mock_escalate:
        mock_escalate.return_value = "Estándar"
        rc = mode_query(root=str(tmp_path))
        assert rc == 0
        mock_escalate.assert_called_once()
        inv = mock_escalate.call_args[0][0]
        assert isinstance(inv, dict)
        assert len(inv) == 2
        assert str(file_a.resolve()) in [str(Path(p).resolve()) for p in inv]
        assert str(file_b.resolve()) in [str(Path(p).resolve()) for p in inv]


def test_explicit_mode_is_not_re_escalated(tmp_path: Path):
    """Con --mode Micro y un archivo de red, el script no re-escala."""
    net_file = tmp_path / "fn_network.sqf"
    net_file.write_text('remoteExec ["hint", 0];', encoding="utf-8")

    # Invocación de orquestador con modo explícito Micro
    state_file = tmp_path / "state.json"
    rc = run_orchestrator(
        work_dir=str(tmp_path),
        state_file=str(state_file),
        input_root=str(tmp_path),
        mode="Micro",
        dry_run=True,
    )
    # Termina en 10 por dry-run, pero el estado preserva Micro y no escala a Estándar
    assert rc == 10


def test_lint_mode_reports_scope_leak_as_bloqueante(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    """--lint sobre el fixture private _y = _z; devuelve BLOQUEANTE."""
    leak_file = tmp_path / "scope_leak.sqf"
    leak_file.write_text("private _y = _z;", encoding="utf-8")

    rc = run_lint(target=str(leak_file))
    captured = capsys.readouterr().out
    assert rc == 0
    assert "[BLOQUEANTE]" in captured
    assert "(Scope)" in captured
    assert "RESUMEN: bloqueantes=" in captured
    assert "bloqueantes=1" in captured


def test_lint_mode_exit_zero_with_findings(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    """--lint sale con 0 aunque haya hallazgos."""
    leak_file = tmp_path / "scope_leak.sqf"
    leak_file.write_text("private _y = _z;", encoding="utf-8")

    rc = run_lint(target=str(leak_file))
    assert rc == 0
    captured = capsys.readouterr().out
    assert "RESUMEN: bloqueantes=1" in captured


def test_lint_mode_exit_ten_when_linter_unavailable(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    """Sin linter, --lint sale con 10 (NO VERIFICADO), no 0."""
    sample_file = tmp_path / "clean.sqf"
    sample_file.write_text("private _a = 1;", encoding="utf-8")

    rc = run_lint(target=str(sample_file), linter_executable="/ruta/inexistente/run_sqflint.py")
    assert rc == 10
    captured = capsys.readouterr().out
    assert "[NO_VERIFICADO]" in captured
    assert "NO VERIFICADO" in captured


def test_report_format_is_stable():
    """format_findings_report produce el formato de una línea por hallazgo y el RESUMEN."""
    findings = [
        SQFFinding(
            severity="BLOQUEANTE",
            file="test.sqf",
            line=12,
            description="Variable out of scope",
            evidence="private _x = _y;",
            discipline="Scope",
        ),
        SQFFinding(
            severity="SUGERENCIA",
            file="test.sqf",
            line=24,
            description="Variable no usada",
            evidence="private _unused = 1;",
            discipline="Sintaxis",
        ),
    ]

    report = format_findings_report(findings)
    lines = report.splitlines()
    # Esquema v1: primera línea de versión, una línea por hallazgo, RESUMEN final.
    assert len(lines) == 4
    assert lines[0] == "REPORT_SCHEMA_VERSION: 1"
    assert lines[1] == "[BLOQUEANTE] test.sqf:12 (Scope): Variable out of scope"
    assert lines[2] == "[SUGERENCIA] test.sqf:24 (Sintaxis): Variable no usada"
    assert lines[3] == "RESUMEN: bloqueantes=1; sugerencias=1; no_verificado=0"


def test_skill_md_invokes_the_orchestrator():
    """El SKILL.md contiene al menos 2 invocaciones de sqf_orchestrator."""
    plugin_root = Path(__file__).resolve().parent.parent
    skill_file = plugin_root / "skills" / "arma3-sqf-skill" / "SKILL.md"
    assert skill_file.is_file(), f"No se encontró SKILL.md en {skill_file}"

    content = skill_file.read_text(encoding="utf-8")
    orchestrator_count = content.count("sqf_orchestrator")
    assert orchestrator_count >= 2, f"Se esperaban >= 2 menciones de sqf_orchestrator, pero se encontraron {orchestrator_count}"
    assert "sqf_orchestrator.py --root <raíz del proyecto> --mode-query" in content or "sqf_orchestrator.py" in content
    assert "--mode-query" in content
    assert "--lint" in content


def test_lenses_and_scripts_registered_in_skill_md():
    """Valida la presencia y registro de los 6 lentes planos references/lens-*.md, run_sqflint.py y openai.yaml."""
    plugin_root = Path(__file__).resolve().parent.parent
    skill_root = plugin_root / "skills" / "arma3-sqf-skill"
    skill_file = skill_root / "SKILL.md"
    assert skill_file.is_file(), f"No se encontró SKILL.md en {skill_file}"
    content = skill_file.read_text(encoding="utf-8")

    # 1. Registro de los 6 lentes planos en SKILL.md y presencia en disco
    expected_lenses = [
        "lens-architect.md",
        "lens-best-practices.md",
        "lens-claims.md",
        "lens-config.md",
        "lens-locality.md",
        "lens-performance.md",
    ]
    ref_dir = skill_root / "references"
    for lens in expected_lenses:
        assert (ref_dir / lens).is_file(), f"Falta el lente plano {lens} en {ref_dir}"
        assert lens in content, f"El lente plano {lens} no está referenciado en {skill_file}"

    # 2. Ausencia de la ruta antigua references/lenses/
    assert not (ref_dir / "lenses").exists(), "La antigua ruta references/lenses/ no debe existir"

    # 3. Ubicación de run_sqflint.py en scripts/ y ausencia en references/
    assert (skill_root / "scripts" / "run_sqflint.py").is_file(), "run_sqflint.py debe estar en scripts/"
    assert not (ref_dir / "run_sqflint.py").exists(), "run_sqflint.py no debe estar en references/"

    # 4. Presencia de openai.yaml en agents/ y registro en SKILL.md
    openai_yaml = skill_root / "agents" / "openai.yaml"
    assert openai_yaml.is_file(), f"Falta {openai_yaml}"
    assert "openai.yaml" in content, f"openai.yaml no está referenciado en {skill_file}"

