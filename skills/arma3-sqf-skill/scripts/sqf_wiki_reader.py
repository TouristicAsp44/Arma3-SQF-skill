"""Conector autónomo de consulta offline a la base de conocimiento BIKI (a3ref).

Proporciona resolución determinista en dos pasos para comandos y funciones SQF,
caché en proceso de alta velocidad para linters y subagentes, y utilidades CLI.
"""

from __future__ import annotations

import argparse
import copy
import gc
import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Any

# ==============================================================================
# RESOLUCIÓN DE RUTA E IMPORTACIÓN DE MÓDULOS (D10):
# Este módulo reside en 'skills/arma3-sqf-skill/scripts/'. Cuando es ejecutado
# como script o importado desde la raíz del plugin, subdirectorios o arnés de
# pruebas, asegura la inclusión de su directorio contenedor en 'sys.path' para
# permitir la resolución directa de sus módulos hermanos.
# ==============================================================================
_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))


def _discover_default_wiki_path() -> Path:
    """Descubre dinámicamente la ubicación de los datos de la wiki por proximidad o estándar de usuario.

    Orden de precedencia (sin eliminar ningún candidato histórico):
      1) ``--wiki-path`` (argumento CLI, se aplica en :func:`resolve_wiki_root`).
      2) Variable de entorno ``SQF_WIKI_DATA_PATH``.
      3) Candidatos por proximidad y estándar de usuario (lista histórica).
      4) Fallback empaquetado junto al paquete de la skill.

    Ninguna ruta es absoluta en código: todas se derivan de ``Path(__file__)``,
    de una variable de entorno declarada o del home del usuario mediante la
    lista blanca ``~`` (``.a3ref``, ``.gemini``).
    """
    plugin_root = _SCRIPT_DIR.parents[2]
    env_path = os.environ.get("SQF_WIKI_DATA_PATH")
    if env_path:
        p_env = Path(env_path).expanduser()
        if p_env.is_dir() and ((p_env / "syntax.json").exists() or (p_env / "commands.json").exists()):
            return p_env
    candidates = [
        plugin_root.parent / "Wiki" / "data",
        plugin_root.parent / "wiki" / "data",
        plugin_root / "data",
        Path.home() / ".a3ref" / "data",
        Path.home() / ".gemini" / "wiki" / "data",
    ]
    for candidate in candidates:
        if candidate.is_dir() and (candidate / "syntax.json").exists():
            return candidate
    return plugin_root / "data"


DEFAULT_WIKI_PATH = _discover_default_wiki_path()

# Cachés indexadas por ruta canónica resuelta (D3)
_syntax_caches: dict[str, dict[str, Any]] = {}
_index_caches: dict[str, dict[str, Any]] = {}
_index_by_lower_caches: dict[str, dict[str, list[dict[str, Any]]]] = {}
_commands_caches: dict[str, dict[str, dict[str, Any]]] = {}
_functions_caches: dict[str, dict[str, dict[str, Any]]] = {}
_db_connections: dict[str, sqlite3.Connection] = {}


def clear_caches() -> None:
    """Limpia todas las cachés en memoria del conector y cierra conexiones SQLite."""
    _syntax_caches.clear()
    _index_caches.clear()
    _index_by_lower_caches.clear()
    _commands_caches.clear()
    _functions_caches.clear()
    for conn in _db_connections.values():
        try:
            conn.close()
        except Exception:
            pass
    _db_connections.clear()


def resolve_wiki_db(
    db_path: str | Path | None = None,
    data_dir: Path | None = None,
) -> Path | None:
    """Resuelve la ruta a la base de datos SQLite por orden estricto de precedencia:

    1. db_path explícito (CLI --db-path o argumento directo).
    2. Si data_dir es un fichero .db o contiene arma3_wiki.db.
    3. Si data_dir es un Path explícito (no None), se respeta y NO se cae a la DB por defecto.
    4. Variable de entorno SQF_WIKI_DB_PATH (solo si data_dir is None).
    5. Path.home() / ".a3ref" / "arma3_wiki.db" (instalación por defecto, solo si data_dir is None).
    6. None si no existe DB.
    """
    if db_path:
        p = Path(db_path).expanduser()
        if p.is_file():
            return p
    if data_dir is not None:
        p_data = Path(data_dir)
        if p_data.is_file() and p_data.suffix.lower() == ".db":
            return p_data
        if (p_data / "arma3_wiki.db").is_file():
            return p_data / "arma3_wiki.db"
        # Si data_dir se especificó explícitamente pero no contiene DB,
        # el llamador solicitó evaluar esa ruta concreta; no caer a la DB global.
        return None

    env_path = os.environ.get("SQF_WIKI_DB_PATH")
    if env_path:
        # expanduser(): un valor como "~/.a3ref/arma3_wiki.db" debe resolverse
        # al home del usuario; sin esto la variable se ignora en silencio.
        p = Path(env_path).expanduser()
        if p.is_file():
            return p

    default_db = Path.home() / ".a3ref" / "arma3_wiki.db"
    if default_db.is_file():
        return default_db

    return None


def _get_db_connection(db_file: Path) -> sqlite3.Connection:
    key = str(db_file.resolve())
    conn = _db_connections.get(key)
    if conn is None:
        conn = sqlite3.connect(str(db_file))
        conn.row_factory = sqlite3.Row
        _db_connections[key] = conn
    return conn


def resolve_wiki_root(override_path: str | Path | None = None) -> Path:
    """Resuelve la ruta a los datos de la wiki por jerarquía estricta (D6):

    1. override_path explícito si se provee.
    2. Variable de entorno SQF_WIKI_DATA_PATH o A3REF_WIKI_PATH si está definida y es
       un directorio de datos válido (contiene syntax.json o commands.json). Si no es
       un directorio válido, se descarta para evitar romper el wiki en silencio y se
       continúa con la precedencia normal (candidatos -> fallback).
    3. Ruta local por defecto (DEFAULT_WIKI_PATH descubierta dinámicamente).
    """
    if override_path:
        return Path(override_path).expanduser()
    for env_var in ("SQF_WIKI_DATA_PATH", "A3REF_WIKI_PATH"):
        env_val = os.environ.get(env_var)
        if env_val:
            p_env = Path(env_val).expanduser()
            if p_env.is_dir() and ((p_env / "syntax.json").exists() or (p_env / "commands.json").exists()):
                return p_env
    return _discover_default_wiki_path()


def get_data_git_sha(data_dir: Path | None = None, db_path: Path | None = None) -> str:
    """Obtiene en tiempo de ejecución el commit SHA de la réplica offline data o de la DB."""
    db = resolve_wiki_db(db_path, data_dir)
    if db:
        try:
            conn = _get_db_connection(db)
            row = conn.execute("SELECT value FROM meta WHERE key = 'dataset_git_sha'").fetchone()
            if row and row["value"]:
                return str(row["value"])
        except Exception:
            pass

    target_dir = resolve_wiki_root(data_dir)
    if not target_dir.exists():
        return f"NO_VERIFICADO (directorio no existe: {target_dir})"
    try:
        res = subprocess.run(
            ["git", "-C", str(target_dir), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.strip()
    except (subprocess.SubprocessError, OSError):
        pass
    return "NO_VERIFICADO"


def get_dataset_updated_timestamp(data_dir: Path | None = None, db_path: Path | None = None) -> str:
    """Obtiene el valor de la clave 'updated' de syntax.json o de la DB."""
    db = resolve_wiki_db(db_path, data_dir)
    if db:
        try:
            conn = _get_db_connection(db)
            row = conn.execute("SELECT value FROM meta WHERE key = 'dataset_updated'").fetchone()
            if row and row["value"]:
                return str(row["value"])
        except Exception:
            pass

    syn = load_syntax(data_dir)
    if syn and "updated" in syn:
        return str(syn["updated"])
    return "NO_VERIFICADO"


def get_dataset_sha(data_dir: Path | None = None, db_path: Path | None = None) -> str:
    """Obtiene el hash SHA256 del dataset desde meta en la DB o NO_VERIFICADO."""
    db = resolve_wiki_db(db_path, data_dir)
    if db:
        try:
            conn = _get_db_connection(db)
            row = conn.execute("SELECT value FROM meta WHERE key = 'dataset_sha'").fetchone()
            if row and row["value"]:
                return str(row["value"])
        except Exception:
            pass
    return "NO_VERIFICADO"


def _cache_key(root: Path) -> str:
    return str(root)


def load_syntax(data_dir: Path | None = None) -> dict[str, Any]:
    """Carga syntax.json con caché en memoria indexada por ruta resuelta (D3)."""
    root = resolve_wiki_root(data_dir)
    key = _cache_key(root)
    if key in _syntax_caches:
        return _syntax_caches[key]

    target = root / "syntax.json"
    if not target.exists():
        _syntax_caches[key] = {}
        return {}
    with open(target, "r", encoding="utf-8") as f:
        data = json.load(f)
    _syntax_caches[key] = data
    return data


def load_index(data_dir: Path | None = None) -> dict[str, Any]:
    """Carga index.json en memoria y construye el índice por nombre en minúsculas (D3)."""
    root = resolve_wiki_root(data_dir)
    key = _cache_key(root)
    if key in _index_caches:
        return _index_caches[key]

    target = root / "index.json"
    if not target.exists():
        _index_caches[key] = {}
        _index_by_lower_caches[key] = {}
        return {}
    with open(target, "r", encoding="utf-8") as f:
        data = json.load(f)
    by_lower: dict[str, list[dict[str, Any]]] = {}
    items = data.get("items", []) if isinstance(data, dict) else data
    for item in items:
        name_lower = str(item.get("name", "")).lower()
        by_lower.setdefault(name_lower, []).append(item)
    _index_caches[key] = data
    _index_by_lower_caches[key] = by_lower
    return data


def _ensure_commands_loaded(data_dir: Path | None = None) -> dict[str, dict[str, Any]]:
    """Carga commands.json en caché por nombre en minúsculas (D3, D5)."""
    root = resolve_wiki_root(data_dir)
    key = _cache_key(root)
    if key in _commands_caches:
        return _commands_caches[key]

    target = root / "commands.json"
    cmd_map: dict[str, dict[str, Any]] = {}
    if not target.exists():
        _commands_caches[key] = cmd_map
        return cmd_map
    with open(target, "r", encoding="utf-8") as f:
        raw = json.load(f)
    items = raw.get("items", []) if isinstance(raw, dict) else raw
    for it in items:
        name = it.get("name", "")
        name_lower = name.lower()
        status = it.get("status", "ok")
        version = it.get("arma3_since") or it.get("since") or "versión no disponible en el snapshot"
        url = it.get("url") or f"https://community.bistudio.com/wiki/{name} (NO_VERIFICADO: url ausente en snapshot)"
        locality = it.get("locality", {})
        enriched = dict(it)
        enriched["canonical_name"] = name
        enriched["status"] = status
        enriched["version"] = version
        enriched["url"] = url
        enriched["locality"] = locality
        cmd_map[name_lower] = enriched
    _commands_caches[key] = cmd_map
    return cmd_map


def _ensure_functions_loaded(data_dir: Path | None = None) -> dict[str, dict[str, Any]]:
    """Carga functions.json en caché por nombre en minúsculas (D3, D5)."""
    root = resolve_wiki_root(data_dir)
    key = _cache_key(root)
    if key in _functions_caches:
        return _functions_caches[key]

    target = root / "functions.json"
    fn_map: dict[str, dict[str, Any]] = {}
    if not target.exists():
        _functions_caches[key] = fn_map
        return fn_map
    with open(target, "r", encoding="utf-8") as f:
        raw = json.load(f)
    items = raw.get("items", []) if isinstance(raw, dict) else raw
    for it in items:
        name = it.get("name", "")
        name_lower = name.lower()
        status = it.get("status", "ok")
        version = it.get("arma3_since") or it.get("since") or "versión no disponible en el snapshot"
        url = it.get("url") or f"https://community.bistudio.com/wiki/{name} (NO_VERIFICADO: url ausente en snapshot)"
        enriched = dict(it)
        enriched["canonical_name"] = name
        enriched["status"] = status
        enriched["version"] = version
        enriched["url"] = url
        fn_map[name_lower] = enriched
    _functions_caches[key] = fn_map
    return fn_map


def _db_lookup_syntax_symbol(db_path: Path, token: str) -> dict[str, Any] | None:
    """Resolución en dos pasos desde la base de datos SQLite."""
    if not token or not token.strip():
        return None
    t_lower = token.strip().lower()
    conn = _get_db_connection(db_path)
    cur = conn.cursor()

    sym_row = cur.execute(
        "SELECT key, kind, name, forms_json, status, syntax_json, operator, replaced_by_json FROM symbols WHERE key = ?",
        (t_lower,),
    ).fetchone()
    if not sym_row:
        return None

    syn_kind = sym_row["kind"]
    syn_name = sym_row["name"]
    syn_status = sym_row["status"]
    syn_replaced_by = json.loads(sym_row["replaced_by_json"]) if sym_row["replaced_by_json"] else None

    idx_rows = cur.execute(
        "SELECT name, type, summary, arma3_since, locality_json, status, aliases_json FROM index_items WHERE name_lower = ?",
        (t_lower,),
    ).fetchall()

    chosen = None
    if syn_kind == "command":
        for r in idx_rows:
            if r["type"] == "command":
                chosen = r
                break
    if not chosen and syn_kind == "function":
        for r in idx_rows:
            if r["type"] == "function":
                chosen = r
                break
    if not chosen:
        for r in idx_rows:
            if r["type"] in ("command", "function"):
                chosen = r
                break

    canonical_name = chosen["name"] if chosen else syn_name
    status = syn_status or (chosen["status"] if chosen else "ok")
    version = chosen["arma3_since"] if (chosen and chosen["arma3_since"]) else None
    version_str = version if version else "versión no disponible en el snapshot"
    item_type = chosen["type"] if chosen else syn_kind
    replaced_by = syn_replaced_by

    url = None
    if syn_kind == "command" or item_type == "command":
        c_row = cur.execute("SELECT url, doc_json FROM commands WHERE name_lower = ?", (canonical_name.lower(),)).fetchone()
        if c_row:
            if c_row["url"]:
                url = c_row["url"]
            if not replaced_by and c_row["doc_json"]:
                doc = json.loads(c_row["doc_json"])
                replaced_by = doc.get("replaced_by")
    if not url and (syn_kind == "function" or item_type == "function"):
        f_row = cur.execute("SELECT url, doc_json FROM functions WHERE name_lower = ?", (canonical_name.lower(),)).fetchone()
        if f_row:
            if f_row["url"]:
                url = f_row["url"]
            if not replaced_by and f_row["doc_json"]:
                doc = json.loads(f_row["doc_json"])
                replaced_by = doc.get("replaced_by")

    if not url:
        url = f"https://community.bistudio.com/wiki/{canonical_name} (NO_VERIFICADO: url ausente en snapshot)"

    return {
        "canonical_name": canonical_name,
        "status": status,
        "version": version_str,
        "replaced_by": replaced_by,
        "url": url,
        "type": item_type,
    }


def lookup_syntax_symbol(
    token: str,
    data_dir: Path | None = None,
    db_path: Path | None = None,
) -> dict[str, Any] | None:
    """Resolución en dos pasos con desempate por tipo (command > topic, function > topic) y URL oficial (D5).

    Retorna un diccionario con canonical_name, status, version, replaced_by, url y type,
    o None si el símbolo no existe como comando o función oficial.
    """
    if not token or not token.strip():
        return None

    db = resolve_wiki_db(db_path, data_dir)
    if db:
        try:
            res = _db_lookup_syntax_symbol(db, token)
            if res is not None:
                return res
        except Exception:
            pass

    t_lower = token.strip().lower()

    # Paso 1: Comprobar presencia en syntax.json
    syn = load_syntax(data_dir)
    if not syn:
        return None
    syn_cmd = syn.get("commands", {}).get(t_lower)
    syn_fn = syn.get("functions", {}).get(t_lower)
    if not syn_cmd and not syn_fn:
        return None

    syn_data = syn_cmd or syn_fn

    # Paso 2: Desempate y grafía canónica desde index.json
    root = resolve_wiki_root(data_dir)
    key = _cache_key(root)
    idx = load_index(data_dir)
    if not idx:
        return None
    candidates = _index_by_lower_caches.get(key, {}).get(t_lower, [])
    if not candidates:
        items = idx.get("items", []) if isinstance(idx, dict) else idx
        for it in items:
            if str(it.get("name", "")).lower() == t_lower:
                candidates.append(it)

    # Desempate priorizando type matching
    chosen = None
    if syn_cmd:
        for c in candidates:
            if c.get("type") == "command":
                chosen = c
                break
    if not chosen and syn_fn:
        for c in candidates:
            if c.get("type") == "function":
                chosen = c
                break
    if not chosen:
        for c in candidates:
            if c.get("type") in ("command", "function"):
                chosen = c
                break

    canonical_name = chosen.get("name") if chosen else syn_data.get("name", token.strip())
    status = syn_data.get("status") or (chosen.get("status") if chosen else "ok")
    replaced_by = syn_data.get("replaced_by") or (chosen.get("replaced_by") if chosen else None)
    version = (chosen.get("arma3_since") or chosen.get("since")) if chosen else None
    version_str = version if version else "versión no disponible en el snapshot"
    item_type = chosen.get("type") if chosen else ("command" if syn_cmd else "function")

    # Tomar la URL oficial del registro oficial de commands o functions (D5)
    rec = get_command(canonical_name, data_dir) if syn_cmd else get_function(canonical_name, data_dir)
    if not rec:
        rec = get_command(canonical_name, data_dir) or get_function(canonical_name, data_dir)

    if rec and rec.get("url"):
        url = rec["url"]
    elif chosen and chosen.get("url"):
        url = chosen["url"]
    elif syn_data and syn_data.get("url"):
        url = syn_data["url"]
    else:
        url = f"https://community.bistudio.com/wiki/{canonical_name} (NO_VERIFICADO: url ausente en snapshot)"

    return {
        "canonical_name": canonical_name,
        "status": status,
        "version": version_str,
        "replaced_by": replaced_by,
        "url": url,
        "type": item_type,
    }


def get_command(
    name: str,
    data_dir: Path | None = None,
    db_path: Path | None = None,
) -> dict[str, Any] | None:
    """Consulta detallada en commands.json o base de datos SQLite."""
    if not name or not name.strip():
        return None

    db = resolve_wiki_db(db_path, data_dir)
    if db:
        try:
            conn = _get_db_connection(db)
            row = conn.execute(
                "SELECT doc_json FROM commands WHERE name_lower = ?",
                (name.strip().lower(),),
            ).fetchone()
            if row and row["doc_json"]:
                it = json.loads(row["doc_json"])
                cname = it.get("name", "")
                status = it.get("status", "ok")
                version = it.get("arma3_since") or it.get("since") or "versión no disponible en el snapshot"
                url = it.get("url") or f"https://community.bistudio.com/wiki/{cname} (NO_VERIFICADO: url ausente en snapshot)"
                locality = it.get("locality", {})
                enriched = dict(it)
                enriched["canonical_name"] = cname
                enriched["status"] = status
                enriched["version"] = version
                enriched["url"] = url
                enriched["locality"] = locality
                return enriched
            return None
        except Exception:
            pass

    cache = _ensure_commands_loaded(data_dir)
    return cache.get(name.strip().lower())


def get_function(
    name: str,
    data_dir: Path | None = None,
    db_path: Path | None = None,
) -> dict[str, Any] | None:
    """Consulta detallada en functions.json o base de datos SQLite."""
    if not name or not name.strip():
        return None

    db = resolve_wiki_db(db_path, data_dir)
    if db:
        try:
            conn = _get_db_connection(db)
            row = conn.execute(
                "SELECT doc_json FROM functions WHERE name_lower = ?",
                (name.strip().lower(),),
            ).fetchone()
            if row and row["doc_json"]:
                it = json.loads(row["doc_json"])
                cname = it.get("name", "")
                status = it.get("status", "ok")
                version = it.get("arma3_since") or it.get("since") or "versión no disponible en el snapshot"
                url = it.get("url") or f"https://community.bistudio.com/wiki/{cname} (NO_VERIFICADO: url ausente en snapshot)"
                enriched = dict(it)
                enriched["canonical_name"] = cname
                enriched["status"] = status
                enriched["version"] = version
                enriched["url"] = url
                return enriched
            return None
        except Exception:
            pass

    cache = _ensure_functions_loaded(data_dir)
    return cache.get(name.strip().lower())


def get_topic(
    title: str,
    data_dir: Path | None = None,
    db_path: Path | None = None,
) -> dict[str, Any] | None:
    """Lectura puntual bajo demanda de topics.json o base de datos SQLite."""
    if not title or not title.strip():
        return None

    db = resolve_wiki_db(db_path, data_dir)
    if db:
        try:
            conn = _get_db_connection(db)
            t_low = title.strip().lower()
            row = conn.execute(
                "SELECT doc_json FROM topics WHERE title_lower = ? OR LOWER(name) = ?",
                (t_low, t_low),
            ).fetchone()
            if row and row["doc_json"]:
                return json.loads(row["doc_json"])
            return None
        except Exception:
            pass

    root = resolve_wiki_root(data_dir)
    target = root / "topics.json"
    if not target.exists():
        return None
    target_low = title.strip().lower()
    with open(target, "r", encoding="utf-8") as f:
        raw = json.load(f)
    items = raw.get("items", []) if isinstance(raw, dict) else raw
    match = None
    for it in items:
        t_name = str(it.get("title") or it.get("name") or "").lower()
        if t_name == target_low:
            match = copy.deepcopy(it)
            break
    del raw, items
    gc.collect()
    return match


def update_wiki(data_dir: Path | None = None) -> tuple[bool, str]:
    """Sincronización git pull secuencial con timeout de 30s, verificación de repositorio limpio

    y captura explícita de excepciones (D4). Orden estricto: primero data_dir y luego raíz.
    """
    root = resolve_wiki_root(data_dir)
    if not root.exists():
        return False, f"NO_VERIFICADO: Directorio de datos no existe: {root}"

    repos_to_sync = [root, root.parent]
    messages = []
    for r in repos_to_sync:
        git_dir = r / ".git"
        if not git_dir.exists() and not (r.parent / ".git").exists():
            return False, f"Directorio {r.name} no contiene repositorio git (.git ausente)."

        try:
            res_stat = subprocess.run(
                ["git", "-C", str(r), "status", "--porcelain"],
                capture_output=True,
                text=True,
                check=False,
                timeout=30,
            )
            if res_stat.returncode != 0:
                return False, f"Error al verificar estado de git en {r.name}: {res_stat.stderr.strip()}"
            if res_stat.stdout.strip():
                return False, f"Repositorio sucio en {r.name}; contiene cambios no confirmados."

            res_pull = subprocess.run(
                ["git", "-C", str(r), "pull", "--ff-only"],
                capture_output=True,
                text=True,
                check=False,
                timeout=30,
            )
            if res_pull.returncode != 0:
                return False, f"Error en git pull en {r.name}: {res_pull.stderr.strip()}"
            messages.append(f"{r.name}: {res_pull.stdout.strip()}")
        except FileNotFoundError:
            return False, "Comando 'git' no encontrado en el sistema; control de versiones no disponible."
        except subprocess.TimeoutExpired:
            return False, f"Tiempo de espera agotado (30s) al sincronizar repositorio {r.name}."
        except (subprocess.SubprocessError, OSError) as e:
            return False, f"Excepción al ejecutar git en {r.name}: {e}"

    return True, " | ".join(messages)


def main():
    parser = argparse.ArgumentParser(description="Lector autónomo de la base de conocimiento BIKI (a3ref)")
    parser.add_argument("--command", type=str, default=None, help="Consultar información completa de un comando")
    parser.add_argument("--function", type=str, default=None, help="Consultar información completa de una función")
    parser.add_argument("--topic", type=str, default=None, help="Consultar un tópico de la wiki")
    parser.add_argument("--lookup", type=str, default=None, help="Búsqueda sintáctica en 2 pasos de un símbolo")
    parser.add_argument("--wiki-path", type=str, default=None, help="Ruta personalizada a la carpeta data")
    parser.add_argument("--db-path", type=str, default=None, help="Ruta a la base de datos SQLite arma3_wiki.db")
    parser.add_argument("--update-wiki", "--update", action="store_true", help="Actualizar repositorios git")
    parser.add_argument("--sha", action="store_true", help="Mostrar commit SHA de la réplica data")
    parser.add_argument("--dataset-sha", action="store_true", help="Mostrar hash SHA256 del dataset")

    args = parser.parse_args()
    data_path = resolve_wiki_root(args.wiki_path) if args.wiki_path else None
    db_path = Path(args.db_path) if args.db_path else None

    if args.sha:
        print(get_data_git_sha(data_path, db_path=db_path))
        sys.exit(0)

    if args.dataset_sha:
        print(get_dataset_sha(data_path, db_path=db_path))
        sys.exit(0)

    if args.update_wiki:
        ok, msg = update_wiki(data_path)
        if ok:
            print(msg)
            sys.exit(0)
        else:
            print(f"Error al sincronizar wiki: {msg}", file=sys.stderr)
            sys.exit(1)

    if args.command:
        info = get_command(args.command, data_path, db_path=db_path)
        if info:
            print(json.dumps(info, indent=2, ensure_ascii=False))
            sys.exit(0)
        else:
            print(f"Comando no encontrado: {args.command}", file=sys.stderr)
            sys.exit(1)

    if args.function:
        info = get_function(args.function, data_path, db_path=db_path)
        if info:
            print(json.dumps(info, indent=2, ensure_ascii=False))
            sys.exit(0)
        else:
            print(f"Función no encontrada: {args.function}", file=sys.stderr)
            sys.exit(1)

    if args.topic:
        info = get_topic(args.topic, data_path, db_path=db_path)
        if info:
            print(json.dumps(info, indent=2, ensure_ascii=False))
            sys.exit(0)
        else:
            print(f"Tópico no encontrado: {args.topic}", file=sys.stderr)
            sys.exit(1)

    if args.lookup:
        info = lookup_syntax_symbol(args.lookup, data_path, db_path=db_path)
        if info:
            print(json.dumps(info, indent=2, ensure_ascii=False))
            sys.exit(0)
        else:
            print(f"Símbolo no identificado: {args.lookup}", file=sys.stderr)
            sys.exit(1)

    parser.print_help()


if __name__ == "__main__":
    main()
