from dataclasses import is_dataclass
from pathlib import Path

import pytest
from sqf_models import (
    ScopeStatus,
    SQFFinding,
    check_escalation_needed,
    check_escalation_needed_for_files,
    evaluate_token_scope,
)


def test_escalates_on_setvariable_broadcast():
    """Demuestra que setVariable con flag broadcast escala a Estándar."""
    code = 'player setVariable ["TAG_var", true, true];'
    result = check_escalation_needed(code, current_mode="Micro")
    assert result == "Estándar"

    # También la variante sin espacios
    code_compact = 'setVariable ["x", true]'
    assert check_escalation_needed(code_compact, current_mode="Micro") == "Estándar"


def test_escalates_on_scheduler_signals():
    """Demuestra que señales de scheduler (while, allUnits, EachFrame) escalan a Estándar."""
    code_while = 'while {true} do { sleep 1; };'
    assert check_escalation_needed(code_while, current_mode="Micro") == "Estándar"

    code_allunits = 'allUnits apply { _x setDamage 0; };'
    assert check_escalation_needed(code_allunits, current_mode="Micro") == "Estándar"

    code_eachframe = 'addMissionEventHandler ["EachFrame", { params ["_diag"]; }];'
    assert check_escalation_needed(code_eachframe, current_mode="Micro") == "Estándar"


def test_no_escalation_for_micro_file(tmp_path: Path):
    """Demuestra que un archivo limpio sin primitivas de red ni scheduler se queda en Micro."""
    clean_code = (
        '/*\n'
        ' * Función: TAG_fnc_sumar\n'
        ' */\n'
        'params [["_a", 0, [0]], ["_b", 0, [0]]];\n'
        'private _resultado = _a + _b;\n'
        '_resultado\n'
    )
    result = check_escalation_needed(clean_code, current_mode="Micro")
    assert result == "Micro"

    # Verificación por archivo físico
    clean_file = tmp_path / "fn_sumar.sqf"
    clean_file.write_text(clean_code, encoding="utf-8")
    result_files = check_escalation_needed_for_files([clean_file], current_mode="Micro")
    assert result_files == "Micro"


def test_escalation_never_returns_micro_for_empty_inventory():
    """Demuestra que check_escalation_needed_for_files lanza ValueError ante inventario vacío."""
    with pytest.raises(ValueError, match="Inventario vacio"):
        check_escalation_needed_for_files({}, current_mode="Micro")

    with pytest.raises(ValueError, match="Inventario vacio"):
        check_escalation_needed_for_files([], current_mode="Micro")


def test_sqffinding_is_dataclass_and_serializable():
    """Demuestra que SQFFinding es un dataclass puro, soporta model_dump y ScopeStatus opera según diseño."""
    finding = SQFFinding(
        severity="BLOQUEANTE",
        file="test.sqf",
        line=10,
        description="Error de prueba",
        evidence="bad code",
        discipline="Scope",
    )
    assert is_dataclass(finding)
    dumped = finding.model_dump()
    assert isinstance(dumped, dict)
    assert dumped["severity"] == "BLOQUEANTE"
    assert dumped["file"] == "test.sqf"
    assert dumped["line"] == 10
    assert dumped["discipline"] == "Scope"

    # Verificación de ScopeStatus y evaluate_token_scope
    assert ScopeStatus.MIXED.value == "MIXED"
    assert evaluate_token_scope("cmd", "") == ScopeStatus.INDETERMINATE
    assert evaluate_token_scope("cmd", "cmd [0,0,0];") == ScopeStatus.NOT_LOCAL
    assert evaluate_token_scope("_loc", "private _loc = 1; _x = _loc;") == ScopeStatus.LOCAL
    assert evaluate_token_scope("cmd", "private cmd = 1; cmd [0,0,0];") == ScopeStatus.MIXED


def test_item_9_does_not_count_local_variables_as_absent():
    """Demuestra que el Ítem 9 no contabiliza variables locales como ausentes (D1)."""
    from sqf_orchestrator import compute_item_9_report

    source_code = (
        "private _resultado = 42;\n"
        "_pos = getPos player;\n"
        'playSoundUI "test";\n'
        'simboloInexistente123 "arg";\n'
    )
    stdout = (
        'test.sqf:3: error: can\'t interpret statement (missing ;?): <Variable(playSoundUI)> <String("test")>\n'
        'test.sqf:4: error: can\'t interpret statement (missing ;?): <Variable(simboloInexistente123)> <String("arg")>\n'
    )
    f1 = SQFFinding(
        severity="SUGERENCIA",
        file="test.sqf",
        line=3,
        description="Comando oficial válido según Biki: playSoundUI",
        evidence='<Variable(playSoundUI)> <String("test")>',
        discipline="Biki",
    )
    f2 = SQFFinding(
        severity="BLOQUEANTE",
        file="test.sqf",
        line=4,
        description="error: can't interpret statement (missing ;?): <Variable(simboloInexistente123)>",
        evidence='<Variable(simboloInexistente123)> <String("arg")>',
        discipline="Sintaxis",
    )
    report = compute_item_9_report(findings=[f1, f2], rc=1, stdout=stdout, source_code=source_code)

    assert "_resultado" not in report
    assert "_pos" not in report
    assert "1 ausentes (simboloInexistente123)" in report
    assert "1 bloqueantes asociados" in report


def test_item_9_clean_file_reaches_pasa():
    """Demuestra que un archivo SQF limpio alcanza el estado PASA en el Ítem 9 (Once.3)."""
    from sqf_orchestrator import compute_item_9_report

    source_code = (
        'private _resultado = 42;\n'
        'hint "Operación completada";\n'
        'sleep 5;\n'
    )
    stdout = "test.sqf:0: info: SIN ERRORES"
    report = compute_item_9_report(findings=[], rc=0, stdout=stdout, source_code=source_code)

    assert "PASA" in report
    assert "0 ausentes" in report
    assert "0 bloqueantes asociados" in report


def test_blocker_association_short_token_no_contamination():
    """Demuestra que la asociación de bloqueantes por token corto no contamina identificadores mayores (D7)."""
    from sqf_orchestrator import compute_item_9_report

    stdout = 'test.sqf:1: error: can\'t interpret statement: <Variable(pos)> <Number(10)>\n'
    f_pos = SQFFinding(
        severity="BLOQUEANTE",
        file="test.sqf",
        line=1,
        description="error de sintaxis en comando setPos con argumento erróneo",
        evidence="player setPos [0,0,0];",
        discipline="Sintaxis",
    )
    report = compute_item_9_report(findings=[f_pos], rc=1, stdout=stdout, source_code="")

    assert "1 ausentes (pos)" in report
    assert "0 bloqueantes asociados" in report


def test_sibling_module_import_from_plugin_root():
    """Demuestra que la importación de módulos hermanos funciona con sys.path configurado (D10)."""
    import sys
    plugin_root = Path(__file__).resolve().parent.parent
    scripts_dir = plugin_root / "skills" / "arma3-sqf-skill" / "scripts"
    assert str(scripts_dir) in sys.path or any(str(scripts_dir) in p for p in sys.path)
    import sqf_models
    import sqf_wiki_reader
    assert hasattr(sqf_wiki_reader, "lookup_syntax_symbol")
    assert hasattr(sqf_models, "parse_sqflint_output")


def test_item_9_folder_mode_with_unknown_identifier(tmp_path: Path):
    """Demuestra que el modo carpeta extrae candidatos reales y reporta ausentes/bloqueantes asociados (Once.1)."""
    from sqf_orchestrator import compute_item_9_report, read_sqf_file_robust

    f1 = tmp_path / "valid.sqf"
    f1.write_text('hint "hola";\nsleep 5;\n', encoding="utf-8")

    f2 = tmp_path / "with_unknown.sqf"
    f2.write_text('simboloInexistente123;\nplayer setPos [0,0,0];\n', encoding="utf-8")

    file_sources = {}
    for f in [f1, f2]:
        c, err = read_sqf_file_robust(str(f))
        assert err is None
        file_sources[str(f)] = c

    f_unknown = SQFFinding(
        severity="BLOQUEANTE",
        file=str(f2),
        line=1,
        description="error de sintaxis: <Variable(simboloInexistente123)> no interpretable",
        evidence="simboloInexistente123;",
        discipline="Sintaxis",
    )
    stdout = f"{f2}:1: error: can't interpret statement: <Variable(simboloInexistente123)>\n"

    report = compute_item_9_report(
        findings=[f_unknown],
        rc=1,
        stdout=stdout,
        target=str(tmp_path),
        file_sources=file_sources,
    )

    assert "0 de 0" not in report
    assert "1 ausentes (simboloInexistente123)" in report
    assert "1 bloqueantes asociados" in report
    assert "NO VERIFICADO" in report


def test_item_9_file_mode_parity(tmp_path: Path):
    """Demuestra que el modo archivo individual mantiene paridad con modo carpeta (Once.2)."""
    from sqf_orchestrator import compute_item_9_report, read_sqf_file_robust

    f2 = tmp_path / "single_unknown.sqf"
    code = 'simboloInexistente123;\nplayer setPos [0,0,0];\n'
    f2.write_text(code, encoding="utf-8")

    c, err = read_sqf_file_robust(str(f2))
    assert err is None

    f_unknown = SQFFinding(
        severity="BLOQUEANTE",
        file=str(f2),
        line=1,
        description="error de sintaxis: <Variable(simboloInexistente123)>",
        evidence="simboloInexistente123;",
        discipline="Sintaxis",
    )
    stdout = f"{f2}:1: error: can't interpret statement: <Variable(simboloInexistente123)>\n"

    report = compute_item_9_report(
        findings=[f_unknown],
        rc=1,
        stdout=stdout,
        source_code=c,
        target=str(f2),
    )

    assert "0 de 0" not in report
    assert "1 ausentes (simboloInexistente123)" in report
    assert "1 bloqueantes asociados" in report
    assert "NO VERIFICADO" in report


def test_utf16_bom_encoding_detection(tmp_path: Path):
    """Demuestra que un archivo SQF en UTF-16 LE con BOM se decodifica y analiza sin descartarse en silencio (Once.3)."""
    from sqf_orchestrator import compute_item_9_report, read_sqf_file_robust

    f_utf16 = tmp_path / "sample_utf16.sqf"
    text_content = 'hint "Mensaje en UTF-16";\nsleep 10;\n'
    # Escribir con BOM explícito UTF-16 LE
    f_utf16.write_bytes(b"\xff\xfe" + text_content.encode("utf-16-le"))

    decoded_text, err = read_sqf_file_robust(str(f_utf16))
    assert err is None
    assert "hint" in decoded_text
    assert "sleep" in decoded_text

    stdout = f"{f_utf16}:0: info: OK\n"
    report = compute_item_9_report(
        findings=[],
        rc=0,
        stdout=stdout,
        source_code=decoded_text,
        target=str(f_utf16),
    )

    assert "0 de 0" not in report
    assert "PASA" in report
    assert "0 ausentes" in report
    assert "0 bloqueantes asociados" in report


def test_summary_incorporates_item_9_unverified_on_missing_linter():
    """Demuestra que el resumen incorpora NO VERIFICADO cuando el Ítem 9 está en NO VERIFICADO (Once.4)."""
    from sqf_models import format_findings_report
    from sqf_orchestrator import compute_item_9_report

    # Caso A: Analizador estático no disponible
    finding_unv = SQFFinding(
        severity="NO_VERIFICADO",
        file="test.sqf",
        line=0,
        description="Linter no disponible (SQFLINT_NO_DISPONIBLE)",
        evidence="",
        discipline="Sintaxis",
    )
    item_9_a = compute_item_9_report([finding_unv], rc=3, stdout="SQFLINT_NO_DISPONIBLE")
    assert "NO VERIFICADO" in item_9_a
    report_a = format_findings_report([finding_unv], item_9_status="NO_VERIFICADO")
    assert "RESUMEN: bloqueantes=0; sugerencias=0; no_verificado=1" in report_a
    assert "no_verificado=0" not in report_a

    # Caso B: Sin hallazgos NO_VERIFICADO en findings, pero Ítem 9 en NO VERIFICADO por símbolo ausente
    f_bloq = SQFFinding(
        severity="BLOQUEANTE",
        file="test.sqf",
        line=1,
        description="error can't interpret <Variable(simboloAusente999)>",
        evidence="simboloAusente999;",
        discipline="Sintaxis",
    )
    item_9_b = compute_item_9_report(
        [f_bloq],
        rc=1,
        stdout="test.sqf:1: error: <Variable(simboloAusente999)>",
        source_code="",
    )
    assert "NO VERIFICADO" in item_9_b
    report_b = format_findings_report([f_bloq], item_9_status="NO_VERIFICADO")
    # El resumen debe reportar no_verificado=1 reflejando el Ítem 9 sin contradecirse
    assert "RESUMEN: bloqueantes=1; sugerencias=0; no_verificado=1" in report_b
    assert "no_verificado=0" not in report_b

