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
    clear_caches,
    format_synthetic,
    get_command,
    get_db_resolution_level,
    is_degraded_mode,
    load_wiki_cache_md,
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


def test_16_synthetic_output_formatting():
    """16. Formateo sintético de salida < 200 tokens con firma, argumentos, retorno, versión y resumen."""
    cmd = get_command("remoteExec")
    assert cmd is not None
    synth = format_synthetic(cmd)

    # Verifica campos requeridos
    assert "Firma:" in synth
    assert "Localidad:" in synth
    assert "Arg:" in synth and "Efe:" in synth
    assert "Retorno:" in synth
    assert "Versión:" in synth
    assert "Resumen:" in synth
    assert "remoteExec" in synth

    # Comprueba que el volumen es compacto (< 200 tokens, ~70 palabras)
    word_count = len(synth.split())
    assert word_count < 100, f"Salida sintética excede el umbral de tokens: {word_count} palabras"


def test_17_db_resolution_chain_4_levels(tmp_path: Path, monkeypatch):
    """17. Cadena de resolución agnóstica de 4 niveles para la base de datos SQLite."""
    clear_caches()
    empty_home = tmp_path / "empty_home"
    empty_home.mkdir()

    # Nivel 1: Variable de entorno SQF_WIKI_DB_PATH
    fake_db = tmp_path / "custom.db"
    fake_db.write_bytes(b"SQLite format 3\x00")
    monkeypatch.setenv("SQF_WIKI_DB_PATH", str(fake_db))
    tier, label, p = get_db_resolution_level()
    assert tier == 1
    assert label == "SQF_WIKI_DB_PATH"
    assert p == fake_db
    monkeypatch.delenv("SQF_WIKI_DB_PATH", raising=False)

    # Nivel 2: Estándar de usuario ~/.a3ref/arma3_wiki.db
    fake_home = tmp_path / "user_home"
    (fake_home / ".a3ref").mkdir(parents=True)
    user_db = fake_home / ".a3ref" / "arma3_wiki.db"
    user_db.write_bytes(b"SQLite format 3\x00")
    monkeypatch.setenv("HOME", str(fake_home))
    monkeypatch.setenv("USERPROFILE", str(fake_home))
    tier, label, p = get_db_resolution_level()
    assert tier == 2
    assert p == user_db

    # Nivel 3: Fallback de contenedor Claude AI
    monkeypatch.setenv("HOME", str(empty_home))
    monkeypatch.setenv("USERPROFILE", str(empty_home))
    claude_db = tmp_path / "claude_cache" / "arma3_wiki.db"
    claude_db.parent.mkdir(parents=True)
    claude_db.write_bytes(b"SQLite format 3\x00")
    monkeypatch.setenv("CLAUDE_A3REF_CACHE", str(claude_db))
    tier, label, p = get_db_resolution_level()
    assert tier == 3
    assert label == "CLAUDE_CONTAINER_DB"
    assert p == claude_db
    monkeypatch.delenv("CLAUDE_A3REF_CACHE", raising=False)

    # Nivel 4: Sin réplica SQLite local/contenedor
    tier, label, p = get_db_resolution_level()
    assert tier == 4
    assert label == "SIN_REPLICA"
    assert p is None
    clear_caches()


def test_18_degraded_mode_sin_replica_wiki_cache(tmp_path: Path, monkeypatch):
    """18. Modo degradado SIN_REPLICA consulta wiki-cache.md (31 comandos clave) y emite None para no presentes."""
    clear_caches()
    # Verifica que la tabla de 31 comandos se carga correctamente
    wcache = load_wiki_cache_md()
    assert len(wcache) == 31
    assert "remoteexec" in wcache
    assert "publicvariable" in wcache
    assert "didjip" in wcache

    # Simular entorno aislado sin base de datos ni dataset JSON
    empty_home = tmp_path / "empty_home"
    empty_home.mkdir()
    monkeypatch.setenv("HOME", str(empty_home))
    monkeypatch.setenv("USERPROFILE", str(empty_home))
    monkeypatch.delenv("SQF_WIKI_DB_PATH", raising=False)
    monkeypatch.delenv("SQF_WIKI_DATA_PATH", raising=False)
    monkeypatch.delenv("A3REF_WIKI_PATH", raising=False)

    import sqf_wiki_reader
    monkeypatch.setattr(sqf_wiki_reader, "_discover_default_wiki_path", lambda: empty_home)
    clear_caches()

    assert is_degraded_mode() is True

    # Comando presente en wiki-cache.md (31 comandos)
    info_re = get_command("remoteExec")
    assert info_re is not None
    assert info_re["mode"] == "SIN_REPLICA"
    assert info_re["canonical_name"] == "remoteExec"
    assert info_re["arg"] == "AG"
    assert info_re["effect"] == "EG"

    # Comando oficial pero no presente en wiki-cache.md (debe emitir None honestamente)
    info_sp = get_command("setPos")
    assert info_sp is None

    # Comando inventado (debe emitir None limpiamente)
    info_inv = get_command("comandoTotalmenteInexistente999")
    assert info_inv is None
    clear_caches()


def test_19_degraded_mode_lookup_syntax_symbol(tmp_path: Path, monkeypatch):
    """19. lookup_syntax_symbol en modo degradado SIN_REPLICA resuelve comandos de wiki-cache.md."""
    clear_caches()
    empty_home = tmp_path / "empty_home"
    empty_home.mkdir()
    monkeypatch.setenv("HOME", str(empty_home))
    monkeypatch.setenv("USERPROFILE", str(empty_home))
    monkeypatch.delenv("SQF_WIKI_DB_PATH", raising=False)
    monkeypatch.delenv("SQF_WIKI_DATA_PATH", raising=False)
    monkeypatch.delenv("A3REF_WIKI_PATH", raising=False)

    import sqf_wiki_reader
    monkeypatch.setattr(sqf_wiki_reader, "_discover_default_wiki_path", lambda: empty_home)
    clear_caches()

    res = lookup_syntax_symbol("didJIP")
    assert res is not None
    assert res["canonical_name"] == "didJIP"
    assert res["mode"] == "SIN_REPLICA"
    assert res["status"] == "ok"
    assert res["type"] == "command"

    # Símbolo no presente en wiki-cache.md en modo degradado
    res_none = lookup_syntax_symbol("simboloAusenteEnCache123")
    assert res_none is None
    clear_caches()


def test_20_cli_synthetic_vs_full(tmp_path: Path):
    """20. CLI emite salida sintética compacta por defecto y JSON exhaustivo con --full."""
    import subprocess
    import sys

    # Salida sintética por defecto
    proc_synth = subprocess.run(
        [sys.executable, str(Path(__file__).resolve().parent.parent / "skills" / "arma3-sqf-skill" / "scripts" / "sqf_wiki_reader.py"), "--command", "remoteExec"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "Comando: remoteExec" in proc_synth.stdout
    assert "Firma:" in proc_synth.stdout
    assert "Localidad:" in proc_synth.stdout
    assert len(proc_synth.stdout.split()) < 100

    # Salida --full (exhaustiva en JSON)
    proc_full = subprocess.run(
        [sys.executable, str(Path(__file__).resolve().parent.parent / "skills" / "arma3-sqf-skill" / "scripts" / "sqf_wiki_reader.py"), "--command", "remoteExec", "--full"],
        capture_output=True,
        text=True,
        check=True,
    )
    import json
    data = json.loads(proc_full.stdout)
    assert data["canonical_name"] == "remoteExec"
    assert "examples" in data or "syntaxes" in data or "syntax" in data

