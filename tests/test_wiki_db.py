"""Pruebas unitarias y de integración para la base de conocimiento SQLite (a3ref).

Verifica la construcción determinista, paridad campo a campo contra JSON,
búsqueda FTS5 y degradación a LIKE, metadatos de procedencia y funcionamiento
con y sin base de datos sobre el fixture ligero 'wiki_mini'.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from sqf_wiki_reader import (
    clear_caches,
    get_command,
    get_dataset_sha,
    get_dataset_updated_timestamp,
    get_function,
    get_topic,
    lookup_syntax_symbol,
)
from wiki_db_builder import (
    SCHEMA_VERSION,
    build_db,
    compute_db_content_digest,
    get_db_stats,
    query_db,
    verify_db_parity,
)

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "wiki_mini"


@pytest.fixture(autouse=True)
def _clean_cache():
    clear_caches()
    yield
    clear_caches()


@pytest.fixture
def mini_db(tmp_path: Path) -> Path:
    """Construye una base de datos SQLite temporal a partir del fixture wiki_mini."""
    db_file = tmp_path / "wiki_mini.db"
    build_db(FIXTURES_DIR, db_file, enable_fts=True)
    return db_file


@pytest.fixture
def mini_db_no_fts(tmp_path: Path) -> Path:
    """Construye una base de datos SQLite temporal sin FTS a partir del fixture wiki_mini."""
    db_file = tmp_path / "wiki_mini_no_fts.db"
    build_db(FIXTURES_DIR, db_file, enable_fts=False)
    return db_file


def test_build_produces_tables_and_expected_counts(mini_db: Path) -> None:
    """Build produce una base de datos con las 6 tablas y los conteos exactos del fixture."""
    stats = get_db_stats(mini_db)
    counts = stats["actual_counts"]

    assert counts["commands"] == 3
    assert counts["functions"] == 2
    assert counts["topics"] == 1
    assert counts["symbols"] == 5
    assert counts["index_items"] == 5
    assert stats["fts_count"] == 6  # 3 commands + 2 functions + 1 topic


def test_meta_table_contents(mini_db: Path) -> None:
    """La tabla meta almacena schema_version, dataset_sha, dataset_updated y fts_enabled."""
    stats = get_db_stats(mini_db)
    meta = stats["meta"]

    assert meta["schema_version"] == SCHEMA_VERSION
    assert meta["fts_enabled"] == "1"
    assert len(meta["dataset_sha"]) == 64
    assert meta["dataset_updated"] != "NO_VERIFICADO"
    assert int(meta["counts_commands"]) == 3
    assert int(meta["counts_functions"]) == 2
    assert int(meta["counts_topics"]) == 1


def test_parity_db_vs_json_all_items(mini_db: Path) -> None:
    """Verificación formal de paridad campo a campo DB <-> JSON con verify_db_parity."""
    ok, errors = verify_db_parity(mini_db, FIXTURES_DIR)
    assert ok is True, f"Paridad falló con errores: {errors}"


def test_lookup_symbol_parity_db_and_json(mini_db: Path) -> None:
    """lookup_syntax_symbol devuelve exactamente las mismas claves y valores con DB y con JSON."""
    tokens_to_test = [
        "remoteExec",
        "remoteexec",
        "isDedicated",
        "addPublicVariableEventHandler",
        "BIS_fnc_guiMessage",
        "bis_fnc_mp",
    ]

    for tok in tokens_to_test:
        res_json = lookup_syntax_symbol(tok, data_dir=FIXTURES_DIR)
        res_db = lookup_syntax_symbol(tok, db_path=mini_db)

        assert res_json is not None, f"JSON no encontró {tok}"
        assert res_db is not None, f"DB no encontró {tok}"

        # Paridad campo a campo
        assert res_db["canonical_name"] == res_json["canonical_name"]
        assert res_db["status"] == res_json["status"]
        assert res_db["version"] == res_json["version"]
        assert res_db["replaced_by"] == res_json["replaced_by"]
        assert res_db["url"] == res_json["url"]
        assert res_db["type"] == res_json["type"]


def test_get_command_parity_db_and_json(mini_db: Path) -> None:
    """get_command devuelve enriquecimiento idéntico entre JSON y DB."""
    for cmd in ["remoteExec", "isDedicated", "addPublicVariableEventHandler"]:
        res_json = get_command(cmd, data_dir=FIXTURES_DIR)
        res_db = get_command(cmd, db_path=mini_db)

        assert res_json is not None
        assert res_db is not None
        assert res_db["canonical_name"] == res_json["canonical_name"]
        assert res_db["status"] == res_json["status"]
        assert res_db["version"] == res_json["version"]
        assert res_db["url"] == res_json["url"]
        assert res_db["description"] == res_json["description"]


def test_get_function_parity_db_and_json(mini_db: Path) -> None:
    """get_function devuelve enriquecimiento idéntico entre JSON y DB."""
    for fn in ["BIS_fnc_guiMessage", "BIS_fnc_MP"]:
        res_json = get_function(fn, data_dir=FIXTURES_DIR)
        res_db = get_function(fn, db_path=mini_db)

        assert res_json is not None
        assert res_db is not None
        assert res_db["canonical_name"] == res_json["canonical_name"]
        assert res_db["status"] == res_json["status"]
        assert res_db["version"] == res_json["version"]
        assert res_db["url"] == res_json["url"]


def test_get_topic_parity_db_and_json(mini_db: Path) -> None:
    """get_topic retorna el artículo completo con markdown idéntico entre JSON y DB."""
    topic_title = "Arma 3: Dedicated Server"
    res_json = get_topic(topic_title, data_dir=FIXTURES_DIR)
    res_db = get_topic(topic_title, db_path=mini_db)

    assert res_json is not None
    assert res_db is not None
    assert res_db["title"] == res_json["title"]
    assert res_db["markdown"] == res_json["markdown"]
    assert res_db["url"] == res_json["url"]
    assert res_db["revid"] == res_json["revid"]


def test_fts_search_and_like_fallback(mini_db: Path, mini_db_no_fts: Path) -> None:
    """FTS5 localiza hits por texto y el modo --no-fts degrada de forma transparente a LIKE."""
    # Búsqueda con FTS activo
    hits_fts = query_db(mini_db, search="dedicated")
    assert isinstance(hits_fts, list)
    assert len(hits_fts) > 0
    hit_names = [h["name"] for h in hits_fts]
    assert "isDedicated" in hit_names or "Arma 3: Dedicated Server" in hit_names

    # Búsqueda con FTS inactivo (degradación a LIKE)
    hits_like = query_db(mini_db_no_fts, search="dedicated")
    assert isinstance(hits_like, list)
    assert len(hits_like) > 0
    names_like = [h["name"] for h in hits_like]
    assert "isDedicated" in names_like


def test_determinism_two_builds_same_digest(tmp_path: Path) -> None:
    """Dos compilaciones consecutivas del mismo dataset generan el MISMO content digest."""
    db1 = tmp_path / "build1.db"
    db2 = tmp_path / "build2.db"

    build_db(FIXTURES_DIR, db1, enable_fts=True)
    build_db(FIXTURES_DIR, db2, enable_fts=True)

    digest1 = compute_db_content_digest(db1)
    digest2 = compute_db_content_digest(db2)

    assert digest1 == digest2
    assert len(digest1) == 64


def test_fallback_without_db_json_reader_works() -> None:
    """Si no se proporciona DB y solo existe data_dir JSON, el lector funciona normalmente."""
    sym = lookup_syntax_symbol("remoteExec", data_dir=FIXTURES_DIR)
    assert sym is not None
    assert sym["canonical_name"] == "remoteExec"
    assert sym["status"] == "ok"


def test_provenance_metadata_preserved_in_db(mini_db: Path) -> None:
    """La DB expone correctamente url, revid, updated, version y dataset_sha."""
    cmd = get_command("remoteExec", db_path=mini_db)
    assert cmd is not None
    assert "url" in cmd and cmd["url"].startswith("https://")
    assert "revid" in cmd and isinstance(cmd["revid"], int)
    assert "updated" in cmd
    assert cmd["version"] == "1.50"

    d_sha = get_dataset_sha(db_path=mini_db)
    assert len(d_sha) == 64
    d_updated = get_dataset_updated_timestamp(db_path=mini_db)
    assert d_updated != "NO_VERIFICADO"
