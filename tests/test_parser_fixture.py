from sqf_models import parse_sqflint_output


def test_scope_warning_is_bloqueante():
    """Demuestra que una advertencia de scope se clasifica como BLOQUEANTE con disciplina Scope."""
    stdout = 'scripts/fn_test.sqf:12: warning: Local variable "_x" is not from this scope (not private)'
    findings = parse_sqflint_output(rc=0, stdout=stdout, source_code='private _y = _x;')

    assert len(findings) == 1
    f = findings[0]
    assert f.severity == "BLOQUEANTE"
    assert f.line == 12
    assert f.discipline == "Scope"
    assert "not from this scope" in f.description or "not private" in f.description


def test_rc0_keeps_warnings():
    """Demuestra que con rc == 0 las advertencias no se descartan y se asigna disciplina."""
    stdout = 'scripts/fn_test.sqf:25: warning: Tab character used instead of spaces'
    findings = parse_sqflint_output(rc=0, stdout=stdout, source_code="")

    assert len(findings) == 1
    f = findings[0]
    assert f.severity == "SUGERENCIA"
    assert f.line == 25
    assert f.discipline == "Sintaxis"
    assert "Tab character" in f.description


def test_scope_precedence_over_variable_mark():
    """Demuestra que la guarda de ámbito tiene precedencia estricta sobre el tratamiento de comando (D2)."""
    stdout = 'scripts/fn_test.sqf:10: warning: Local variable "_z" is not from this scope (not private): <Variable(setPos)>'

    # Caso A: Con código fuente disponible
    findings_code = parse_sqflint_output(rc=0, stdout=stdout, source_code="_z = 10; setPos player;")
    assert len(findings_code) == 1
    assert findings_code[0].severity == "BLOQUEANTE"
    assert findings_code[0].discipline == "Scope"

    # Caso B: Con código fuente ausente
    findings_no_code = parse_sqflint_output(rc=0, stdout=stdout, source_code="")
    assert len(findings_no_code) == 1
    assert findings_no_code[0].severity == "BLOQUEANTE"
    assert findings_no_code[0].discipline == "Scope"

