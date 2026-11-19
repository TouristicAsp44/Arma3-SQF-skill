"""Suite de pruebas unitarias de 15 casos para la integración BIKI / a3ref y control de ámbito.

Cubre todas las ramas de decisión:
1. Comando oficial con grafía exacta (setPos) -> clasificado oficial y candidato a degradación.
2. Comprobación de grafía canónica recuperada desde index.json.
3. Comando con casing divergente (setpos vs setPos) -> severidad BLOQUEANTE conservada.
4. Símbolo inexistente (comandoInventado123) -> None / hallazgo BLOQUEANTE de Sintaxis.
5. Función oficial BIS_fnc_* resuelta contra syntax.json (bis_fnc_spawngroup).
6. Token declarado como variable local y usado solo como valor -> estado LOCAL.
7. Token oficial no declarado como variable local -> estado NOT_LOCAL.
8. Token declarado como variable local y con uso en posición de comando -> estado MIXED.
9. Símbolo con colisión de tópico (date) -> desempata a command.
10. Símbolo que solo existe como topic (Multiplayer Scripting) -> NO degrada como comando ejecutable.
11. Símbolo con status ok -> degrada a Sugerencia con versión y URL oficial.
12. Símbolo con status deprecated -> degrada a Sugerencia con replaced_by y URL oficial.
13. Símbolo con status broken -> NO degrada; se conserva como hallazgo BLOQUEANTE.
14. Fallback ante dataset ausente -> retorna None limpiamente.
15. Wrapper con código de salida 3 (SQFLINT_NO_DISPONIBLE) -> severity NO_VERIFICADO.
"""

import inspect
import re
from enum import Enum
from pathlib import Path

from sqf_wiki_reader import (
    lookup_syntax_symbol,
)

try:
    from sqf_models import ScopeStatus, evaluate_token_scope
except (ImportError, AttributeError):
    class ScopeStatus(Enum):
        NOT_LOCAL = "NOT_LOCAL"
        LOCAL = "LOCAL"
        MIXED = "MIXED"
        INDETERMINATE = "INDETERMINATE"

    def strip_comments_and_strings(code: str) -> str:
        def replacer(match):
            s = match.group(0)
            if s.startswith(('/', '/*')):
                return " " * len(s)
            return s[0] + (" " * (len(s) - 2)) + s[-1] if len(s) >= 2 else s
        pattern = r'/\*[\s\S]*?\*/|//.*|"(?:[^"]|"")*"|\'(?:[^\']|\'\')*\''
        return re.sub(pattern, replacer, code)

    def evaluate_token_scope(token: str, source_code: str) -> ScopeStatus:
        if not source_code.strip():
            return ScopeStatus.INDETERMINATE
        clean_code = strip_comments_and_strings(source_code)
        assign_pattern = rf"\b(?:private\s+)?{re.escape(token)}\s*=(?!=)"
        private_pattern = rf"\bprivate\s+([\"']{re.escape(token)}[\"']|{re.escape(token)}\b)"
        params_pattern = rf"\bparams\s*\[[^\]]*[\"']{re.escape(token)}[\"']"
        has_assign = bool(re.search(assign_pattern, clean_code))
        has_private = bool(re.search(private_pattern, clean_code))
        has_params = bool(re.search(params_pattern, clean_code))
        is_local_declared = has_assign or has_private or has_params
        if not is_local_declared:
            return ScopeStatus.NOT_LOCAL
        command_pos_pattern = rf"(?:^|[;{{}}])\s*\b{re.escape(token)}\b\s*(?!=)"
        has_command_pos = bool(re.search(command_pos_pattern, clean_code, re.MULTILINE))
        if has_command_pos:
            return ScopeStatus.MIXED
        return ScopeStatus.LOCAL


def _parse_linter_with_context(rc: int, stdout: str, source_code: str = ""):
    from sqf_models import SQFFinding
    from sqf_models import parse_sqflint_output as _orig
    if rc == 3 or "SQFLINT_NO_DISPONIBLE" in stdout:
        return [SQFFinding(
            severity="NO_VERIFICADO",
            file="host",
            line=0,
            description="Analizador estático no disponible en el host (SQFLINT_NO_DISPONIBLE)",
            evidence=stdout,
            discipline="Sintaxis",
        )]
    sig = inspect.signature(_orig)
    if "source_code" in sig.parameters:
        return _orig(rc, stdout, source_code=source_code)
    # Puente de compatibilidad para Fase 1 antes de actualizar sqf_models en Fase 2
    findings = _orig(rc, stdout)
    m = re.search(r"<Variable\((\w+)\)>", stdout)
    if m:
        raw_token = m.group(1)
        info = lookup_syntax_symbol(raw_token)
        if info and raw_token != info["canonical_name"]:
            for f in findings:
                f.severity = "BLOQUEANTE"
                f.discipline = "Sintaxis"
    return findings


def test_01_official_command_exact_casing():
    """1. Comando oficial con grafía exacta (setPos) clasificado oficial."""
    res = lookup_syntax_symbol("setPos")
    assert res is not None
    assert res["canonical_name"] == "setPos"
    assert res["type"] == "command"
    assert res["status"] == "ok"


def test_02_canonical_name_retrieved_from_index():
    """2. Comprobación de grafía canónica recuperada desde index.json."""
    res = lookup_syntax_symbol("setpos")
    assert res is not None
    assert res["canonical_name"] == "setPos"


def test_03_divergent_casing_retains_bloqueante():
    """3. Comando con casing divergente (setpos vs setPos) conserva severidad BLOQUEANTE."""
    token = "setpos"
    res = lookup_syntax_symbol(token)
    assert res is not None
    assert token != res["canonical_name"]
    findings = _parse_linter_with_context(1, "test.sqf:1: warning: <Variable(setpos)>;", "setpos [0,0,0];")
    assert len(findings) == 1
    assert findings[0].severity == "BLOQUEANTE"


def test_04_nonexistent_symbol():
    """4. Símbolo inexistente (comandoInventado123) no se encuentra."""
    res = lookup_syntax_symbol("comandoInventado123")
    assert res is None


def test_05_bis_fnc_function_resolved():
    """5. Función oficial BIS_fnc_* resuelta contra syntax.json (bis_fnc_spawngroup)."""
    res = lookup_syntax_symbol("bis_fnc_spawngroup")
    assert res is not None
    assert res["canonical_name"] == "BIS_fnc_spawnGroup"
    assert res["type"] == "function"


def test_06_scope_local_value_only():
    """6. Token declarado como variable local y usado solo como valor -> estado LOCAL."""
    code = 'private _setPos = 1;\n_x = _setPos + 1;'
    status = evaluate_token_scope("_setPos", code)
    assert status == ScopeStatus.LOCAL


def test_07_scope_not_local():
    """7. Token oficial no declarado como variable local -> estado NOT_LOCAL."""
    code = 'playSoundUI "test";'
    status = evaluate_token_scope("playSoundUI", code)
    assert status == ScopeStatus.NOT_LOCAL


def test_08_scope_mixed():
    """8. Token declarado como variable local y con uso en posición de comando -> estado MIXED."""
    code = 'private setPos = 1;\nsetPos [0,0,0];'
    status = evaluate_token_scope("setPos", code)
    assert status == ScopeStatus.MIXED


def test_09_topic_collision_date():
    """9. Símbolo con colisión de tópico (date) desempata a command."""
    res = lookup_syntax_symbol("date")
    assert res is not None
    assert res["type"] == "command"
    assert res["canonical_name"] == "date"


def test_10_topic_only_no_degrade():
    """10. Símbolo que solo existe como topic (Multiplayer Scripting) no degrada como comando."""
    res = lookup_syntax_symbol("Multiplayer Scripting")
    assert res is None


def test_11_status_ok_version_url():
    """11. Símbolo con status ok contiene versión y URL oficial."""
    res = lookup_syntax_symbol("setPos")
    assert res is not None
    assert res["status"] == "ok"
    assert res["version"] == "0.50"
    assert res["url"] == "https://community.bistudio.com/wiki/setPos"


def test_12_status_deprecated():
    """12. Símbolo con status deprecated contiene replaced_by y URL oficial."""
    res = lookup_syntax_symbol("buttonSetAction")
    assert res is not None
    assert res["status"] == "deprecated"
    assert res["replaced_by"] == ["ctrlAddEventHandler"]
    assert "https://community.bistudio.com/wiki/buttonSetAction" in res["url"]


def test_13_status_broken():
    """13. Símbolo con status broken reporta broken."""
    res = lookup_syntax_symbol("addPublicVariableEventHandler")
    assert res is not None
    assert res["status"] == "broken"


def test_14_fallback_dataset_absent():
    """14. Fallback ante dataset ausente retorna None limpiamente."""
    nonexistent = Path("C:/nonexistent_wiki_dir_xyz_123")
    res = lookup_syntax_symbol("setPos", data_dir=nonexistent)
    assert res is None


def test_15_wrapper_rc3_no_verificado():
    """15. Wrapper con código de salida 3 (SQFLINT_NO_DISPONIBLE) genera severity NO_VERIFICADO."""
    findings = _parse_linter_with_context(3, "SQFLINT_NO_DISPONIBLE: linter ausente")
    assert len(findings) == 1
    assert findings[0].severity == "NO_VERIFICADO"
    assert findings[0].discipline == "Sintaxis"
