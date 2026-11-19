import json
from pathlib import Path

import pytest
from sqf_orchestrator import run_orchestrator


def test_mock_agent_never_returns_clean_pass(tmp_path: Path):
    """Demuestra que el modo dry-run devuelve código 10 (NO VERIFICADO), nunca 0."""
    rc = run_orchestrator(
        work_dir=str(tmp_path),
        dry_run=True,
    )
    assert rc == 10


def test_missing_agent_raises(tmp_path: Path):
    """Demuestra que sin agent_func y sin dry-run se lanza ValueError."""
    with pytest.raises(ValueError, match="run_orchestrator exige agent_func"):
        run_orchestrator(
            work_dir=str(tmp_path),
            agent_func=None,
            dry_run=False,
        )


def test_input_file_populates_state(tmp_path: Path):
    """Demuestra que el parámetro input_file carga el código real y se lo entrega al agente en el prompt."""
    input_sqf = tmp_path / "custom_sample.sqf"
    secret_code = "private _token_identificador_12345 = 999;"
    input_sqf.write_text(secret_code, encoding="utf-8")

    captured_prompts = []

    def capturing_agent(prompt: str) -> str:
        captured_prompts.append(prompt)
        return "private _ok = true;"

    rc = run_orchestrator(
        work_dir=str(tmp_path),
        input_file=str(input_sqf),
        agent_func=capturing_agent,
        dry_run=False,
    )
    assert rc in (0, 10)
    assert len(captured_prompts) == 1
    assert secret_code in captured_prompts[0]


def test_t09_abort_writes_failed_state(tmp_path: Path):
    """Demuestra que 3 iteraciones consecutivas con bloqueante escriben estado fallido y retornan código 1."""
    plugin_root = Path(__file__).resolve().parent.parent
    fake_linter = plugin_root / "tests" / "fixtures" / "fake_linter.py"

    def agent_always_errors(prompt: str) -> str:
        # Devuelve código que el fake_linter detecta como SYNTAX_ERROR
        return "SYNTAX_ERROR // invalid sqf code"

    # Iteración 1: falla y guarda estado para iteración 2
    rc1 = run_orchestrator(
        work_dir=str(tmp_path),
        linter_executable=str(fake_linter),
        agent_func=agent_always_errors,
        dry_run=False,
        max_iterations=3,
    )
    assert rc1 == 0

    # Iteración 2: continúa, falla y guarda estado para iteración 3
    rc2 = run_orchestrator(
        work_dir=str(tmp_path),
        linter_executable=str(fake_linter),
        agent_func=agent_always_errors,
        dry_run=False,
        continuar=True,
        max_iterations=3,
    )
    assert rc2 == 0

    # Iteración 3: alcanza límite máximo de 3 iteraciones, escribe estado fallido y retorna código 1
    rc3 = run_orchestrator(
        work_dir=str(tmp_path),
        linter_executable=str(fake_linter),
        agent_func=agent_always_errors,
        dry_run=False,
        continuar=True,
        max_iterations=3,
    )

    assert rc3 == 1
    failed_state_file = tmp_path / "orchestrator_state.fallido.json"
    assert failed_state_file.exists()
    state_data = json.loads(failed_state_file.read_text(encoding="utf-8"))
    assert state_data.get("status") == "FALLIDO"
    assert state_data.get("iteration") == 3
