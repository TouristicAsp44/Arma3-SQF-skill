"""Tests para el cálculo riguroso de métricas del harness (PR-5-bis, Tarea A.5)."""

from __future__ import annotations

import json
from pathlib import Path

from evals.harness import evaluate_external_host, normalized_file_sha256

REPO_ROOT = Path(__file__).resolve().parent.parent
HARNESS_FILE = REPO_ROOT / "evals" / "harness.py"

SKILL_PATH = "skills/arma3-sqf-skill/SKILL.md"
INLINE_PATH = "integrations/chatgpt/custom_gpt_instructions.md"


def real_context(*paths: str) -> list[dict]:
    """Contexto_cargado con el sha256 REAL de los ficheros indicados.

    El harness verifica el hash contra los ficheros actuales del repo (R3), así
    que un test debe usar el hash verdadero o su traza sería descartada.
    """
    return [
        {"archivo": p, "sha256": normalized_file_sha256(REPO_ROOT / p)}
        for p in paths
    ]


def test_harness_code_contains_no_hardcoded_metric_literals() -> None:
    """Verifica que harness.py no contiene literales fijos de métricas como '6/6 (0 FALSO_PASA)'."""
    text = HARNESS_FILE.read_text(encoding="utf-8")
    assert '"6/6 (0 FALSO_PASA)"' not in text, "harness.py contiene el literal fijo '6/6 (0 FALSO_PASA)'"
    assert '"100 %"' not in text and '"100.0 %"' not in text, (
        "harness.py contiene literales de porcentaje fijos en la lógica de cálculo de modelos"
    )


def test_omitted_finding_does_not_reduce_denominator(tmp_path: Path) -> None:
    """A.3: Una traza que omite un hallazgo esperado NO reduce el denominador (sale de expected.json)."""
    runs_dir = tmp_path / "runs"
    host_dir = runs_dir / "2026-11-18" / "test-host"
    host_dir.mkdir(parents=True)

    # Traza que NO reporta ningún hallazgo para g03 (donde se espera Cat. 3)
    trace = {
        "golden_id": "g03_dedicated_player",
        "host": "test-host",
        "modelo": "TestModel",
        "version": "1.0",
        "modo_evaluacion": "archivo",
        "contexto_cargado": real_context(SKILL_PATH),
        "respuesta_cruda": "REPORT_SCHEMA_VERSION: 1\nRESUMEN: bloqueantes=0; sugerencias=0; no_verificado=0",
    }
    (host_dir / "g03_dedicated_player.json").write_text(json.dumps(trace), encoding="utf-8")

    result = evaluate_external_host("test-host", "archivo", runs_dir=runs_dir)
    # Debe ser evaluado pero con M2 = 0.0 % porque omitió el hallazgo esperado de Cat. 3
    assert result["status"].startswith("EVALUADO")
    assert "0.0 %" in result["m2"], f"M2 debió ser 0.0 % ante omisión, obtenido: {result['m2']}"
    assert result["omisiones"] > 0 or result["falsos_pasa"] > 0


def test_m3_reflects_actual_number_not_fixed_literal(tmp_path: Path) -> None:
    """A.1: Un M3 con 1 hallazgo omitido o falso pasa refleja el cómputo real y no 6/6."""
    runs_dir = tmp_path / "runs"
    host_dir = runs_dir / "2026-11-18" / "test-host"
    host_dir.mkdir(parents=True)

    # Traza en modo pegado para g01 donde el modelo detecta el error
    trace1 = {
        "golden_id": "g01_syntax_scope",
        "host": "test-host",
        "modelo": "TestModel",
        "version": "1.0",
        "modo_evaluacion": "pegado",
        "contexto_cargado": real_context(INLINE_PATH),
        "respuesta_cruda": "REPORT_SCHEMA_VERSION: 1\n[BLOQUEANTE] code.sqf:4 (Scope): _leaked sin private\nRESUMEN: bloqueantes=1; sugerencias=0; no_verificado=0",
    }
    # Traza para g02 donde el modelo omite el softlock
    trace2 = {
        "golden_id": "g02_softlock_waituntil",
        "host": "test-host",
        "modelo": "TestModel",
        "version": "1.0",
        "modo_evaluacion": "pegado",
        "contexto_cargado": real_context(INLINE_PATH),
        "respuesta_cruda": "REPORT_SCHEMA_VERSION: 1\nRESUMEN: bloqueantes=0; sugerencias=0; no_verificado=0",
    }
    (host_dir / "g01.json").write_text(json.dumps(trace1), encoding="utf-8")
    (host_dir / "g02.json").write_text(json.dumps(trace2), encoding="utf-8")

    result = evaluate_external_host("test-host", "pegado", runs_dir=runs_dir)
    assert result["status"].startswith("EVALUADO")
    # M3 no debe ser 6/6
    assert "6/6" not in result["m3"], f"M3 no debió ser 6/6: {result['m3']}"
    assert result["falsos_pasa"] > 0 or result["omisiones"] > 0


def test_mode_filtering_isolates_modes_in_same_host(tmp_path: Path) -> None:
    """A.2: Trazas de ambos modos en el mismo host no se contaminan entre sí."""
    runs_dir = tmp_path / "runs"
    host_dir = runs_dir / "2026-11-18" / "dual-host"
    host_dir.mkdir(parents=True)

    # Traza solo en modo archivo
    trace_file = {
        "golden_id": "g03_dedicated_player",
        "host": "dual-host",
        "modelo": "FileModel",
        "version": "1.0",
        "modo_evaluacion": "archivo",
        "contexto_cargado": real_context(SKILL_PATH),
        "respuesta_cruda": (
            "REPORT_SCHEMA_VERSION: 1\n"
            "[BLOQUEANTE] code.sqf:2 (Dedicado): player en server\n"
            "[BLOQUEANTE] code.sqf:4 (Dedicado): player en ruta de servidor\n"
            "RESUMEN: bloqueantes=2; sugerencias=0; no_verificado=0"
        ),
    }
    (host_dir / "file_run.json").write_text(json.dumps(trace_file), encoding="utf-8")

    # Evaluación para modo pegado debe ser NO_VERIFICADO porque no hay trazas de pegado
    pegado_eval = evaluate_external_host("dual-host", "pegado", runs_dir=runs_dir)
    assert pegado_eval["status"] == "NO_VERIFICADO"

    # Evaluación para modo archivo debe ser EVALUADO
    file_eval = evaluate_external_host("dual-host", "archivo", runs_dir=runs_dir)
    assert file_eval["status"].startswith("EVALUADO")
    assert "100.0 %" in file_eval["m2"]


def test_mixed_models_reported_correctly(tmp_path: Path) -> None:
    """A.4: Trazas con más de un modelo se reportan como Mixto."""
    runs_dir = tmp_path / "runs"
    host_dir = runs_dir / "2026-11-18" / "mix-host"
    host_dir.mkdir(parents=True)

    t1 = {
        "golden_id": "g01_syntax_scope",
        "host": "mix-host",
        "modelo": "ModelA",
        "version": "1.0",
        "modo_evaluacion": "archivo",
        "contexto_cargado": [{"archivo": "SKILL.md", "sha256": "abc"}],
        "respuesta_cruda": "REPORT_SCHEMA_VERSION: 1\nRESUMEN: bloqueantes=0; sugerencias=0; no_verificado=0",
    }
    t2 = {
        "golden_id": "g02_softlock_waituntil",
        "host": "mix-host",
        "modelo": "ModelB",
        "version": "2.0",
        "modo_evaluacion": "archivo",
        "contexto_cargado": [{"archivo": "SKILL.md", "sha256": "def"}],
        "respuesta_cruda": "REPORT_SCHEMA_VERSION: 1\nRESUMEN: bloqueantes=0; sugerencias=0; no_verificado=0",
    }
    (host_dir / "t1.json").write_text(json.dumps(t1), encoding="utf-8")
    (host_dir / "t2.json").write_text(json.dumps(t2), encoding="utf-8")

    res = evaluate_external_host("mix-host", "archivo", runs_dir=runs_dir)
    assert "Mixto" in res["modelo"]
    assert "ModelA" in res["modelo"] and "ModelB" in res["modelo"]


def test_unexpected_finding_counts_as_false_positive(tmp_path: Path) -> None:
    """A.3: Una traza que inventa un bloqueante no esperado se cuenta como falso positivo."""
    runs_dir = tmp_path / "runs"
    host_dir = runs_dir / "2026-11-18" / "fp-host"
    host_dir.mkdir(parents=True)

    # g09 es un snippet LIMPIO (0 bloqueantes esperados)
    trace = {
        "golden_id": "g09_clean_basic",
        "host": "fp-host",
        "modelo": "HallucinatingModel",
        "version": "1.0",
        "modo_evaluacion": "archivo",
        "contexto_cargado": [{"archivo": "SKILL.md", "sha256": "abc"}],
        "respuesta_cruda": "REPORT_SCHEMA_VERSION: 1\n[BLOQUEANTE] code.sqf:10 (Scope): Bloqueante inventado\nRESUMEN: bloqueantes=1; sugerencias=0; no_verificado=0",
    }
    (host_dir / "clean_hallucinated.json").write_text(json.dumps(trace), encoding="utf-8")

    res = evaluate_external_host("fp-host", "archivo", runs_dir=runs_dir)
    assert res["falsos_positivos"] > 0, "No se contabilizó el falso positivo"


def test_trace_without_loaded_context_is_rejected(tmp_path: Path) -> None:
    """A.5: Una traza sin contexto_cargado se rechaza como inválida."""
    runs_dir = tmp_path / "runs"
    host_dir = runs_dir / "2026-11-18" / "nocontext-host"
    host_dir.mkdir(parents=True)

    trace = {
        "golden_id": "g01_syntax_scope",
        "host": "nocontext-host",
        "modelo": "NoCtxModel",
        "version": "1.0",
        "modo_evaluacion": "archivo",
        # contexto_cargado ausente o vacío
        "contexto_cargado": [],
        "respuesta_cruda": "REPORT_SCHEMA_VERSION: 1\nRESUMEN: bloqueantes=0; sugerencias=0; no_verificado=0",
    }
    (host_dir / "bad_trace.json").write_text(json.dumps(trace), encoding="utf-8")

    res = evaluate_external_host("nocontext-host", "archivo", runs_dir=runs_dir)
    # Al ser inválida, no hay trazas válidas -> NO_VERIFICADO
    assert res["status"] == "NO_VERIFICADO"


def test_trace_with_wrong_context_hash_is_discarded(tmp_path: Path) -> None:
    """R3: una traza cuyo sha256 de contexto NO coincide con el fichero real se descarta."""
    runs_dir = tmp_path / "runs"
    host_dir = runs_dir / "2026-11-18" / "badhash-host"
    host_dir.mkdir(parents=True)

    trace = {
        "golden_id": "g01_syntax_scope",
        "host": "badhash-host",
        "modelo": "TestModel",
        "version": "1.0",
        "modo_evaluacion": "archivo",
        "contexto_cargado": [{"archivo": SKILL_PATH, "sha256": "0" * 64}],
        "respuesta_cruda": "REPORT_SCHEMA_VERSION: 1\n[BLOQUEANTE] code.sqf:4 (Scope): fuga\nRESUMEN: bloqueantes=1; sugerencias=0; no_verificado=0",
    }
    (host_dir / "bad_hash.json").write_text(json.dumps(trace), encoding="utf-8")

    res = evaluate_external_host("badhash-host", "archivo", runs_dir=runs_dir)
    assert res["status"] == "NO_VERIFICADO", "La traza no reproducible debió descartarse"
    assert res["traces_descartadas"] == 1


def test_trace_with_correct_context_hash_is_accepted(tmp_path: Path) -> None:
    """R3: una traza con el sha256 real del contexto se acepta y se mide."""
    runs_dir = tmp_path / "runs"
    host_dir = runs_dir / "2026-11-18" / "goodhash-host"
    host_dir.mkdir(parents=True)

    trace = {
        "golden_id": "g01_syntax_scope",
        "host": "goodhash-host",
        "modelo": "TestModel",
        "version": "1.0",
        "modo_evaluacion": "archivo",
        "contexto_cargado": real_context(SKILL_PATH),
        "respuesta_cruda": "REPORT_SCHEMA_VERSION: 1\n[BLOQUEANTE] code.sqf:4 (Scope): fuga\nRESUMEN: bloqueantes=1; sugerencias=0; no_verificado=0",
    }
    (host_dir / "good_hash.json").write_text(json.dumps(trace), encoding="utf-8")

    res = evaluate_external_host("goodhash-host", "archivo", runs_dir=runs_dir)
    assert res["status"].startswith("EVALUADO")
    assert res["traces_descartadas"] == 0


def test_partial_coverage_is_published_in_status(tmp_path: Path) -> None:
    """R4: la cobertura incompleta se publica en el estado de la fila."""
    runs_dir = tmp_path / "runs"
    host_dir = runs_dir / "2026-11-18" / "partial-host"
    host_dir.mkdir(parents=True)

    trace = {
        "golden_id": "g01_syntax_scope",
        "host": "partial-host",
        "modelo": "TestModel",
        "version": "1.0",
        "modo_evaluacion": "archivo",
        "contexto_cargado": real_context(SKILL_PATH),
        "respuesta_cruda": "REPORT_SCHEMA_VERSION: 1\n[BLOQUEANTE] code.sqf:4 (Scope): fuga\nRESUMEN: bloqueantes=1; sugerencias=0; no_verificado=0",
    }
    (host_dir / "g01.json").write_text(json.dumps(trace), encoding="utf-8")

    res = evaluate_external_host("partial-host", "archivo", runs_dir=runs_dir)
    assert "COBERTURA PARCIAL" in res["status"]
    assert res["goldens_evaluados"] < res["goldens_totales"]
    assert res["cobertura"].startswith(f"{res['goldens_evaluados']}/")


def test_metric_below_objective_is_flagged_not_passing(tmp_path: Path) -> None:
    """R4: una métrica por debajo de su objetivo se marca como NO PASA OBJETIVO."""
    runs_dir = tmp_path / "runs"
    host_dir = runs_dir / "2026-11-18" / "below-host"
    host_dir.mkdir(parents=True)

    # g03 espera un bloqueante de Cat. 3; la traza no reporta nada -> M2 = 0 %
    trace = {
        "golden_id": "g03_dedicated_player",
        "host": "below-host",
        "modelo": "TestModel",
        "version": "1.0",
        "modo_evaluacion": "archivo",
        "contexto_cargado": real_context(SKILL_PATH),
        "respuesta_cruda": "REPORT_SCHEMA_VERSION: 1\nRESUMEN: bloqueantes=0; sugerencias=0; no_verificado=0",
    }
    (host_dir / "g03.json").write_text(json.dumps(trace), encoding="utf-8")

    res = evaluate_external_host("below-host", "archivo", runs_dir=runs_dir)
    assert "NO PASA OBJETIVO" in res["status"]
    assert res["metric_pct"] < res["objetivo_pct"]


def test_quality_doc_publishes_coverage_and_objective_columns() -> None:
    """R4: el informe publicado expone cobertura y veredicto de objetivo."""
    quality = (REPO_ROOT / "docs" / "QUALITY.md").read_text(encoding="utf-8")
    assert "| Cobertura |" in quality, "Falta la columna de cobertura en docs/QUALITY.md"
    assert "COBERTURA PARCIAL" in quality or "NO PASA OBJETIVO" in quality, (
        "El informe debe marcar explícitamente cobertura parcial u objetivo no alcanzado"
    )
    assert "## 4. Cobertura, Límites y Trazabilidad" in quality


def test_parse_report_output_supports_nested_parentheses_in_discipline() -> None:
    """A.3: parse_report_output debe procesar disciplinas con paréntesis anidados sin truncar."""
    from evals.harness import parse_report_output

    sample = (
        "REPORT_SCHEMA_VERSION: 1\n"
        "[BLOQUEANTE] snippet.sqf:4 (Servidor Dedicado (Headless)): Uso del comando UI 'hint' en ruta de servidor.\n"
        "[NO_VERIFICADO] snippet.sqf:1 (Suspensi\u00f3n Unscheduled): Contexto de ejecuci\u00f3n no determinable.\n"
        "RESUMEN: bloqueantes=1; sugerencias=0; no_verificado=1"
    )
    findings = parse_report_output(sample)
    assert len(findings) == 2, f"Se esperaban 2 hallazgos, obtenidos {len(findings)}"
    b = findings[0]
    assert b.severity == "BLOQUEANTE"
    assert b.file == "snippet.sqf"
    assert b.line == 4
    assert b.discipline == "Servidor Dedicado (Headless)"
    assert b.category == 3


def test_strict_rule_unsignaled_golden_blocker_in_pegado_is_false_pass(tmp_path: Path) -> None:
    """Parte B: En golden no señalizado, si verificable_en no tiene pegado y el modelo emite BLOQUEANTE -> FALSO_PASA."""
    runs_dir = tmp_path / "runs"
    host_dir = runs_dir / "2026-11-18" / "strict-fp-host"
    host_dir.mkdir(parents=True)

    trace = {
        "golden_id": "b05_remoteexec",
        "host": "strict-fp-host",
        "modelo": "HallucinatingModel",
        "version": "1.0",
        "modo_evaluacion": "pegado",
        "contexto_cargado": real_context(INLINE_PATH),
        "respuesta_cruda": (
            "REPORT_SCHEMA_VERSION: 1\n"
            "[BLOQUEANTE] snippet.sqf:3 (CfgRemoteExec): Invocación remota no permitida en whitelist\n"
            "RESUMEN: bloqueantes=1; sugerencias=0; no_verificado=0"
        ),
    }
    (host_dir / "b05.json").write_text(json.dumps(trace), encoding="utf-8")

    res = evaluate_external_host("strict-fp-host", "pegado", runs_dir=runs_dir, dataset_filter="unsignaled")
    assert res["status"].startswith("EVALUADO")
    assert res["falsos_pasa"] == 1, f"Debió contarse como 1 FALSO_PASA, obtenido: {res['falsos_pasa']}"


def test_strict_rule_unsignaled_golden_no_verificado_in_pegado_is_justified(tmp_path: Path) -> None:
    """Parte B: En golden no señalizado, si el modelo emite NO_VERIFICADO -> acierto justificado de honestidad."""
    runs_dir = tmp_path / "runs"
    host_dir = runs_dir / "2026-11-18" / "honest-host"
    host_dir.mkdir(parents=True)

    trace = {
        "golden_id": "b05_remoteexec",
        "host": "honest-host",
        "modelo": "HonestModel",
        "version": "1.0",
        "modo_evaluacion": "pegado",
        "contexto_cargado": real_context(INLINE_PATH),
        "respuesta_cruda": (
            "REPORT_SCHEMA_VERSION: 1\n"
            "[NO_VERIFICADO] snippet.sqf:3 (CfgRemoteExec): Whitelist de CfgRemoteExec no verificable sin description.ext\n"
            "RESUMEN: bloqueantes=0; sugerencias=0; no_verificado=1"
        ),
    }
    (host_dir / "b05.json").write_text(json.dumps(trace), encoding="utf-8")

    res = evaluate_external_host("honest-host", "pegado", runs_dir=runs_dir, dataset_filter="unsignaled")
    assert res["status"].startswith("EVALUADO")
    assert res["falsos_pasa"] == 0, f"No debió haber falsos pasa, obtenido: {res['falsos_pasa']}"
    assert res["justified_no_verificado"] == 1, (
        f"Debió contarse como 1 justified_no_verificado, obtenido: {res['justified_no_verificado']}"
    )


def test_strict_rule_signaled_golden_blocker_in_pegado_is_normal_detection(tmp_path: Path) -> None:
    """Parte B: En golden señalizado (g06), un BLOQUEANTE cuenta como detección normal (mantiene paridad con g06)."""
    runs_dir = tmp_path / "runs"
    host_dir = runs_dir / "2026-11-18" / "signaled-host"
    host_dir.mkdir(parents=True)

    trace = {
        "golden_id": "g06_remoteexec_whitelist",
        "host": "signaled-host",
        "modelo": "SignaledModel",
        "version": "1.0",
        "modo_evaluacion": "pegado",
        "contexto_cargado": real_context(INLINE_PATH),
        "respuesta_cruda": (
            "REPORT_SCHEMA_VERSION: 1\n"
            "[BLOQUEANTE] snippet.sqf:4 (CfgRemoteExec): Función fnc_unauthorizedRemote no autorizada en CfgRemoteExec\n"
            "RESUMEN: bloqueantes=1; sugerencias=0; no_verificado=0"
        ),
    }
    (host_dir / "g06.json").write_text(json.dumps(trace), encoding="utf-8")

    res = evaluate_external_host("signaled-host", "pegado", runs_dir=runs_dir, dataset_filter="signaled")
    assert res["status"].startswith("EVALUADO")
    assert res["falsos_pasa"] == 0
    assert res["detected_findings"] == 1


def test_evaluate_external_host_dataset_filter() -> None:
    """Parte B: dataset_filter particiona correctamente entre 'signaled' y 'unsignaled'."""
    res_signaled = evaluate_external_host("antigravity", "archivo", dataset_filter="signaled")
    assert res_signaled["goldens_totales"] == 14, f"Señalizados deben ser 14, obtenido: {res_signaled['goldens_totales']}"

    res_unsignaled = evaluate_external_host("antigravity", "archivo", dataset_filter="unsignaled")
    assert res_unsignaled["goldens_totales"] == 6, f"No señalizados deben ser 6, obtenido: {res_unsignaled['goldens_totales']}"

    res_all = evaluate_external_host("antigravity", "archivo")
    assert res_all["goldens_totales"] == 20, f"Totales deben ser 20, obtenido: {res_all['goldens_totales']}"


