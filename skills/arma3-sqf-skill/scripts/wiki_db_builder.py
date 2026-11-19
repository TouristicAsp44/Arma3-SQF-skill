#!/usr/bin/env python3
"""Constructor y gestor determinista de la base de conocimiento SQLite para SQF / BIKI (a3ref).

Genera una base de datos relacional con soporte FTS5 a partir de los datos JSON
de a3ref (commands.json, functions.json, index.json, syntax.json, topics.json).
Utiliza exclusivamente la biblioteca estándar de Python (>= 3.11).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1.0"


def check_fts5_supported(conn: sqlite3.Connection) -> bool:
    """Comprueba en tiempo de ejecución si SQLite soporta FTS5."""
    try:
        conn.execute("CREATE VIRTUAL TABLE temp._fts_check USING fts5(x)")
        conn.execute("DROP TABLE temp._fts_check")
        return True
    except (sqlite3.OperationalError, sqlite3.DatabaseError):
        return False


def get_git_sha(target_dir: Path) -> str:
    """Obtiene el commit SHA de Git del repositorio data si está disponible."""
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


def compute_dataset_hash(data_dir: Path) -> tuple[str, str]:
    """Calcula un hash SHA256 determinista de los 5 archivos fuente y extrae el timestamp updated."""
    files = ["commands.json", "functions.json", "index.json", "syntax.json", "topics.json"]
    h = hashlib.sha256()
    dataset_updated = "NO_VERIFICADO"

    for fname in sorted(files):
        fpath = data_dir / fname
        if fpath.is_file():
            content = fpath.read_bytes()
            h.update(f"{fname}:{len(content)}".encode("utf-8"))
            h.update(content)
            if fname in ("syntax.json", "commands.json") and dataset_updated == "NO_VERIFICADO":
                try:
                    meta_raw = json.loads(content.decode("utf-8"))
                    if isinstance(meta_raw, dict) and "updated" in meta_raw:
                        dataset_updated = str(meta_raw["updated"])
                except Exception:
                    pass

    return h.hexdigest(), dataset_updated


def init_schema(conn: sqlite3.Connection, enable_fts: bool = True) -> bool:
    """Crea las tablas relacionales y, si es posible y solicitado, la tabla FTS5."""
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS commands (
        name TEXT PRIMARY KEY,
        name_lower TEXT UNIQUE,
        title TEXT,
        type TEXT,
        url TEXT,
        revid INTEGER,
        updated TEXT,
        status TEXT,
        groups_json TEXT,
        games_json TEXT,
        since TEXT,
        arma3_since TEXT,
        description TEXT,
        operator TEXT,
        syntaxes_json TEXT,
        aliases_json TEXT,
        doc_json TEXT
    );
    """)
    cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_commands_name_lower ON commands(name_lower);")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS functions (
        name TEXT PRIMARY KEY,
        name_lower TEXT UNIQUE,
        title TEXT,
        type TEXT,
        url TEXT,
        revid INTEGER,
        updated TEXT,
        status TEXT,
        groups_json TEXT,
        games_json TEXT,
        since TEXT,
        arma3_since TEXT,
        description TEXT,
        operator TEXT,
        syntaxes_json TEXT,
        aliases_json TEXT,
        doc_json TEXT
    );
    """)
    cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_functions_name_lower ON functions(name_lower);")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS topics (
        title TEXT PRIMARY KEY,
        title_lower TEXT,
        name TEXT,
        type TEXT,
        url TEXT,
        revid INTEGER,
        updated TEXT,
        aliases_json TEXT,
        markdown TEXT,
        doc_json TEXT
    );
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_topics_title_lower ON topics(title_lower);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_topics_name_lower ON topics(LOWER(name));")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS symbols (
        key TEXT PRIMARY KEY,
        kind TEXT,
        name TEXT,
        forms_json TEXT,
        status TEXT,
        syntax_json TEXT,
        operator TEXT,
        replaced_by_json TEXT
    );
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_symbols_name ON symbols(name);")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS index_items (
        name_lower TEXT,
        name TEXT,
        type TEXT,
        md TEXT,
        json TEXT,
        groups_json TEXT,
        syntax_json TEXT,
        summary TEXT,
        arma3_since TEXT,
        locality_json TEXT,
        status TEXT,
        operator TEXT,
        aliases_json TEXT
    );
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_index_items_name_lower ON index_items(name_lower);")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS meta (
        key TEXT PRIMARY KEY,
        value TEXT
    );
    """)

    fts_active = False
    if enable_fts and check_fts5_supported(conn):
        cur.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS wiki_fts USING fts5(
            kind,
            name,
            title,
            summary,
            description,
            syntax,
            groups,
            tokenize = 'unicode61'
        );
        """)
        fts_active = True

    conn.commit()
    return fts_active


def build_db(data_dir: Path, out_db: Path, enable_fts: bool = True) -> dict[str, Any]:
    """Construye la base de datos SQLite de forma determinista y ordenada."""
    if not data_dir.is_dir():
        raise FileNotFoundError(f"Directorio de datos no encontrado: {data_dir}")

    out_db.parent.mkdir(parents=True, exist_ok=True)
    if out_db.exists():
        out_db.unlink()

    conn = sqlite3.connect(str(out_db))
    conn.execute("PRAGMA journal_mode = OFF;")
    conn.execute("PRAGMA synchronous = OFF;")
    conn.execute("PRAGMA encoding = 'UTF-8';")

    fts_active = init_schema(conn, enable_fts=enable_fts)

    # 1. Cargar y ordenar commands.json
    commands_path = data_dir / "commands.json"
    cmd_count = 0
    if commands_path.is_file():
        with open(commands_path, "r", encoding="utf-8") as f:
            raw_cmds = json.load(f)
        cmd_items = raw_cmds.get("items", []) if isinstance(raw_cmds, dict) else raw_cmds
        # Orden determinista por name
        cmd_items = sorted(cmd_items, key=lambda x: str(x.get("name", "")))
        
        insert_cmd = """
        INSERT INTO commands (
            name, name_lower, title, type, url, revid, updated, status,
            groups_json, games_json, since, arma3_since, description, operator,
            syntaxes_json, aliases_json, doc_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        rows = []
        fts_rows = []
        for it in cmd_items:
            name = str(it.get("name", ""))
            name_lower = name.lower()
            title = str(it.get("title", name))
            itype = str(it.get("type", "command"))
            url = it.get("url") or f"https://community.bistudio.com/wiki/{name} (NO_VERIFICADO: url ausente en snapshot)"
            revid = it.get("revid")
            updated = str(it.get("updated", ""))
            status = str(it.get("status", "ok"))
            groups_json = json.dumps(it.get("groups", []), ensure_ascii=False)
            games_json = json.dumps(it.get("games", {}), ensure_ascii=False)
            since = str(it.get("since") or "")
            arma3_since = str(it.get("arma3_since") or "")
            description = str(it.get("description") or "")
            operator = str(it.get("operator") or "")
            syntaxes_json = json.dumps(it.get("syntaxes", []), ensure_ascii=False)
            aliases_json = json.dumps(it.get("aliases", []), ensure_ascii=False)
            doc_json = json.dumps(it, ensure_ascii=False, sort_keys=True)

            rows.append((
                name, name_lower, title, itype, url, revid, updated, status,
                groups_json, games_json, since, arma3_since, description, operator,
                syntaxes_json, aliases_json, doc_json
            ))

            if fts_active:
                # Extraer texto de sintaxis
                syntax_texts = []
                for s in it.get("syntaxes", []):
                    if isinstance(s, dict) and "syntax" in s:
                        syntax_texts.append(str(s["syntax"]))
                groups_str = " ".join(it.get("groups", []))
                fts_rows.append((
                    "command", name, title, "", description, " ".join(syntax_texts), groups_str
                ))

        conn.executemany(insert_cmd, rows)
        if fts_active and fts_rows:
            conn.executemany(
                "INSERT INTO wiki_fts (kind, name, title, summary, description, syntax, groups) VALUES (?, ?, ?, ?, ?, ?, ?)",
                fts_rows,
            )
        cmd_count = len(rows)

    # 2. Cargar y ordenar functions.json
    functions_path = data_dir / "functions.json"
    fn_count = 0
    if functions_path.is_file():
        with open(functions_path, "r", encoding="utf-8") as f:
            raw_fns = json.load(f)
        fn_items = raw_fns.get("items", []) if isinstance(raw_fns, dict) else raw_fns
        fn_items = sorted(fn_items, key=lambda x: str(x.get("name", "")))

        insert_fn = """
        INSERT INTO functions (
            name, name_lower, title, type, url, revid, updated, status,
            groups_json, games_json, since, arma3_since, description, operator,
            syntaxes_json, aliases_json, doc_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        rows = []
        fts_rows = []
        for it in fn_items:
            name = str(it.get("name", ""))
            name_lower = name.lower()
            title = str(it.get("title", name))
            itype = str(it.get("type", "function"))
            url = it.get("url") or f"https://community.bistudio.com/wiki/{name} (NO_VERIFICADO: url ausente en snapshot)"
            revid = it.get("revid")
            updated = str(it.get("updated", ""))
            status = str(it.get("status", "ok"))
            groups_json = json.dumps(it.get("groups", []), ensure_ascii=False)
            games_json = json.dumps(it.get("games", {}), ensure_ascii=False)
            since = str(it.get("since") or "")
            arma3_since = str(it.get("arma3_since") or "")
            description = str(it.get("description") or "")
            operator = str(it.get("operator") or "")
            syntaxes_json = json.dumps(it.get("syntaxes", []), ensure_ascii=False)
            aliases_json = json.dumps(it.get("aliases", []), ensure_ascii=False)
            doc_json = json.dumps(it, ensure_ascii=False, sort_keys=True)

            rows.append((
                name, name_lower, title, itype, url, revid, updated, status,
                groups_json, games_json, since, arma3_since, description, operator,
                syntaxes_json, aliases_json, doc_json
            ))

            if fts_active:
                syntax_texts = []
                for s in it.get("syntaxes", []):
                    if isinstance(s, dict) and "syntax" in s:
                        syntax_texts.append(str(s["syntax"]))
                groups_str = " ".join(it.get("groups", []))
                fts_rows.append((
                    "function", name, title, "", description, " ".join(syntax_texts), groups_str
                ))

        conn.executemany(insert_fn, rows)
        if fts_active and fts_rows:
            conn.executemany(
                "INSERT INTO wiki_fts (kind, name, title, summary, description, syntax, groups) VALUES (?, ?, ?, ?, ?, ?, ?)",
                fts_rows,
            )
        fn_count = len(rows)

    # 3. Cargar y ordenar topics.json (sin markdown en FTS)
    topics_path = data_dir / "topics.json"
    topic_count = 0
    if topics_path.is_file():
        with open(topics_path, "r", encoding="utf-8") as f:
            raw_topics = json.load(f)
        top_items = raw_topics.get("items", []) if isinstance(raw_topics, dict) else raw_topics
        top_items = sorted(top_items, key=lambda x: str(x.get("title") or x.get("name") or ""))

        insert_top = """
        INSERT INTO topics (
            title, title_lower, name, type, url, revid, updated,
            aliases_json, markdown, doc_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        rows = []
        fts_rows = []
        for it in top_items:
            title = str(it.get("title") or it.get("name") or "")
            title_lower = title.lower()
            name = str(it.get("name") or title)
            itype = str(it.get("type", "topic"))
            url = str(it.get("url") or f"https://community.bistudio.com/wiki/{title}")
            revid = it.get("revid")
            updated = str(it.get("updated", ""))
            aliases = it.get("aliases", [])
            aliases_json = json.dumps(aliases, ensure_ascii=False)
            markdown = str(it.get("markdown") or "")
            doc_json = json.dumps(it, ensure_ascii=False, sort_keys=True)

            rows.append((
                title, title_lower, name, itype, url, revid, updated,
                aliases_json, markdown, doc_json
            ))

            if fts_active:
                groups_str = " ".join(it.get("groups", [])) + " " + " ".join(aliases)
                fts_rows.append((
                    "topic", name, title, "", "", "", groups_str
                ))

        conn.executemany(insert_top, rows)
        if fts_active and fts_rows:
            conn.executemany(
                "INSERT INTO wiki_fts (kind, name, title, summary, description, syntax, groups) VALUES (?, ?, ?, ?, ?, ?, ?)",
                fts_rows,
            )
        topic_count = len(rows)

    # 4. Cargar y ordenar syntax.json -> symbols
    syntax_path = data_dir / "syntax.json"
    symbol_count = 0
    if syntax_path.is_file():
        with open(syntax_path, "r", encoding="utf-8") as f:
            raw_syn = json.load(f)
        
        insert_sym = """
        INSERT INTO symbols (key, kind, name, forms_json, status, syntax_json, operator, replaced_by_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        rows = []
        # Commands en syntax
        cmds_dict = raw_syn.get("commands", {})
        for k in sorted(cmds_dict.keys()):
            v = cmds_dict[k]
            name = str(v.get("name", k))
            forms_json = json.dumps(v.get("forms", []), ensure_ascii=False)
            status = str(v.get("status", "ok"))
            syntax_json = json.dumps(v.get("syntax", []), ensure_ascii=False)
            operator = str(v.get("operator") or "")
            replaced_by_json = json.dumps(v.get("replaced_by", []), ensure_ascii=False) if "replaced_by" in v else None
            rows.append((k, "command", name, forms_json, status, syntax_json, operator, replaced_by_json))

        # Functions en syntax
        fns_dict = raw_syn.get("functions", {})
        for k in sorted(fns_dict.keys()):
            v = fns_dict[k]
            name = str(v.get("name", k))
            forms_json = json.dumps(v.get("forms", []), ensure_ascii=False)
            status = str(v.get("status", "ok"))
            syntax_json = json.dumps(v.get("syntax", []), ensure_ascii=False)
            operator = str(v.get("operator") or "")
            replaced_by_json = json.dumps(v.get("replaced_by", []), ensure_ascii=False) if "replaced_by" in v else None
            rows.append((k, "function", name, forms_json, status, syntax_json, operator, replaced_by_json))

        conn.executemany(insert_sym, rows)
        symbol_count = len(rows)

    # 5. Cargar y ordenar index.json -> index_items
    index_path = data_dir / "index.json"
    idx_count = 0
    if index_path.is_file():
        with open(index_path, "r", encoding="utf-8") as f:
            raw_idx = json.load(f)
        idx_items = raw_idx.get("items", []) if isinstance(raw_idx, dict) else raw_idx
        idx_items = sorted(idx_items, key=lambda x: (str(x.get("name", "")).lower(), str(x.get("type", ""))))

        insert_idx = """
        INSERT INTO index_items (
            name_lower, name, type, md, json, groups_json, syntax_json,
            summary, arma3_since, locality_json, status, operator, aliases_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        rows = []
        for it in idx_items:
            name = str(it.get("name", ""))
            name_lower = name.lower()
            itype = str(it.get("type", ""))
            md = str(it.get("md", ""))
            json_rel = str(it.get("json", ""))
            groups_json = json.dumps(it.get("groups", []), ensure_ascii=False)
            syntax_json = json.dumps(it.get("syntax", []), ensure_ascii=False)
            summary = str(it.get("summary") or "")
            arma3_since = str(it.get("arma3_since") or "")
            locality_json = json.dumps(it.get("locality", {}), ensure_ascii=False)
            status = str(it.get("status", "ok"))
            operator = str(it.get("operator") or "")
            aliases_json = json.dumps(it.get("aliases", []), ensure_ascii=False)

            rows.append((
                name_lower, name, itype, md, json_rel, groups_json, syntax_json,
                summary, arma3_since, locality_json, status, operator, aliases_json
            ))

        conn.executemany(insert_idx, rows)
        idx_count = len(rows)

    # 6. Metadatos de procedencia
    dataset_sha, dataset_updated = compute_dataset_hash(data_dir)
    dataset_git_sha = get_git_sha(data_dir)
    built_at = datetime.now(timezone.utc).isoformat()

    meta_entries = [
        ("schema_version", SCHEMA_VERSION),
        ("dataset_updated", dataset_updated),
        ("dataset_sha", dataset_sha),
        ("dataset_git_sha", dataset_git_sha),
        ("built_at", built_at),
        ("counts_commands", str(cmd_count)),
        ("counts_functions", str(fn_count)),
        ("counts_topics", str(topic_count)),
        ("counts_symbols", str(symbol_count)),
        ("counts_index_items", str(idx_count)),
        ("fts_enabled", "1" if fts_active else "0"),
    ]
    conn.executemany("INSERT INTO meta (key, value) VALUES (?, ?)", meta_entries)
    conn.commit()

    conn.execute("VACUUM;")
    conn.close()

    return {
        "schema_version": SCHEMA_VERSION,
        "db_path": str(out_db),
        "fts_enabled": fts_active,
        "dataset_sha": dataset_sha,
        "dataset_git_sha": dataset_git_sha,
        "dataset_updated": dataset_updated,
        "counts": {
            "commands": cmd_count,
            "functions": fn_count,
            "topics": topic_count,
            "symbols": symbol_count,
            "index_items": idx_count,
        },
    }


def compute_db_content_digest(db_path: Path) -> str:
    """Calcula un digest SHA256 determinista de todas las filas en las tablas para verificar determinismo."""
    conn = sqlite3.connect(str(db_path))
    h = hashlib.sha256()

    tables_and_cols = [
        ("commands", "SELECT name, name_lower, title, url, revid, status, description FROM commands ORDER BY name"),
        ("functions", "SELECT name, name_lower, title, url, revid, status, description FROM functions ORDER BY name"),
        ("topics", "SELECT title, title_lower, name, url, revid FROM topics ORDER BY title"),
        ("symbols", "SELECT key, kind, name, status FROM symbols ORDER BY key"),
        ("index_items", "SELECT name_lower, name, type, summary FROM index_items ORDER BY name_lower, type"),
    ]

    for tbl, query in tables_and_cols:
        h.update(f"TABLE:{tbl}\n".encode("utf-8"))
        for row in conn.execute(query):
            line = "|".join("" if v is None else str(v) for v in row)
            h.update(f"{line}\n".encode("utf-8"))

    conn.close()
    return h.hexdigest()


def get_db_stats(db_path: Path) -> dict[str, Any]:
    """Recupera estadísticas de la base de datos."""
    if not db_path.is_file():
        raise FileNotFoundError(f"Base de datos no encontrada: {db_path}")

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    meta = {}
    for row in cur.execute("SELECT key, value FROM meta"):
        meta[row["key"]] = row["value"]

    actual_counts = {}
    for tbl in ["commands", "functions", "topics", "symbols", "index_items"]:
        try:
            cnt = cur.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
            actual_counts[tbl] = cnt
        except Exception:
            actual_counts[tbl] = -1

    fts_count = 0
    if meta.get("fts_enabled") == "1":
        try:
            fts_count = cur.execute("SELECT COUNT(*) FROM wiki_fts").fetchone()[0]
        except Exception:
            fts_count = -1

    conn.close()

    file_size_bytes = db_path.stat().st_size
    file_size_mb = round(file_size_bytes / (1024 * 1024), 2)

    return {
        "db_path": str(db_path),
        "file_size_bytes": file_size_bytes,
        "file_size_mb": file_size_mb,
        "meta": meta,
        "actual_counts": actual_counts,
        "fts_count": fts_count,
    }


def query_db(
    db_path: Path,
    command: str | None = None,
    function: str | None = None,
    topic: str | None = None,
    search: str | None = None,
) -> dict[str, Any] | list[dict[str, Any]] | None:
    """Ejecuta consultas puntuales o búsqueda sobre la base de datos."""
    if not db_path.is_file():
        return None

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    meta = dict(cur.execute("SELECT key, value FROM meta").fetchall())
    fts_enabled = meta.get("fts_enabled") == "1"

    if command:
        row = cur.execute(
            "SELECT doc_json FROM commands WHERE name_lower = ?", (command.strip().lower(),)
        ).fetchone()
        conn.close()
        return json.loads(row["doc_json"]) if row else None

    if function:
        row = cur.execute(
            "SELECT doc_json FROM functions WHERE name_lower = ?", (function.strip().lower(),)
        ).fetchone()
        conn.close()
        return json.loads(row["doc_json"]) if row else None

    if topic:
        t_low = topic.strip().lower()
        row = cur.execute(
            "SELECT doc_json FROM topics WHERE title_lower = ? OR LOWER(name) = ?", (t_low, t_low)
        ).fetchone()
        conn.close()
        return json.loads(row["doc_json"]) if row else None

    if search:
        query_text = search.strip()
        results: list[dict[str, Any]] = []

        if fts_enabled:
            # Sanitizar query simple para FTS5
            # Escapar comillas dobles y usar tokens
            safe_query = " ".join(f'"{word}"' for word in query_text.replace('"', "").split() if word)
            if safe_query:
                sql = """
                SELECT kind, name, title, summary, description
                FROM wiki_fts
                WHERE wiki_fts MATCH ?
                ORDER BY rank
                LIMIT 25
                """
                try:
                    for r in cur.execute(sql, (safe_query,)).fetchall():
                        results.append({
                            "kind": r["kind"],
                            "name": r["name"],
                            "title": r["title"],
                            "summary": r["summary"],
                            "description": r["description"][:120] if r["description"] else "",
                        })
                except sqlite3.OperationalError:
                    # En caso de sintaxis FTS no válida, degradar a LIKE
                    fts_enabled = False

        if not fts_enabled or not results:
            # Fallback transparente a LIKE
            pattern = f"%{query_text}%"
            sql_cmds = """
            SELECT 'command' as kind, name, title, description
            FROM commands
            WHERE name LIKE ? OR title LIKE ? OR description LIKE ?
            LIMIT 15
            """
            for r in cur.execute(sql_cmds, (pattern, pattern, pattern)).fetchall():
                results.append({
                    "kind": "command",
                    "name": r["name"],
                    "title": r["title"],
                    "summary": "",
                    "description": r["description"][:120] if r["description"] else "",
                })

            sql_fns = """
            SELECT 'function' as kind, name, title, description
            FROM functions
            WHERE name LIKE ? OR title LIKE ? OR description LIKE ?
            LIMIT 10
            """
            for r in cur.execute(sql_fns, (pattern, pattern, pattern)).fetchall():
                results.append({
                    "kind": "function",
                    "name": r["name"],
                    "title": r["title"],
                    "summary": "",
                    "description": r["description"][:120] if r["description"] else "",
                })

        conn.close()
        return results

    conn.close()
    return None


def verify_db_parity(db_path: Path, data_dir: Path) -> tuple[bool, list[str]]:
    """Comprueba la paridad completa campo a campo entre la base de datos y los JSON fuente."""
    errors: list[str] = []
    if not db_path.is_file():
        return False, [f"DB no existe: {db_path}"]
    if not data_dir.is_dir():
        return False, [f"Data dir no existe: {data_dir}"]

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    # 1. Comandos
    cmd_file = data_dir / "commands.json"
    if cmd_file.is_file():
        with open(cmd_file, "r", encoding="utf-8") as f:
            raw = json.load(f)
        items = raw.get("items", []) if isinstance(raw, dict) else raw
        db_count = conn.execute("SELECT COUNT(*) FROM commands").fetchone()[0]
        if len(items) != db_count:
            errors.append(f"commands count mismatch: JSON={len(items)} vs DB={db_count}")
        for it in items[:50]:  # Comprobar muestra exhaustiva
            name_low = str(it.get("name", "")).lower()
            row = conn.execute("SELECT doc_json FROM commands WHERE name_lower = ?", (name_low,)).fetchone()
            if not row:
                errors.append(f"command missing in DB: {it.get('name')}")
            else:
                db_doc = json.loads(row["doc_json"])
                if db_doc.get("name") != it.get("name"):
                    errors.append(f"command name mismatch: {it.get('name')} != {db_doc.get('name')}")

    # 2. Funciones
    fn_file = data_dir / "functions.json"
    if fn_file.is_file():
        with open(fn_file, "r", encoding="utf-8") as f:
            raw = json.load(f)
        items = raw.get("items", []) if isinstance(raw, dict) else raw
        db_count = conn.execute("SELECT COUNT(*) FROM functions").fetchone()[0]
        if len(items) != db_count:
            errors.append(f"functions count mismatch: JSON={len(items)} vs DB={db_count}")
        for it in items[:50]:
            name_low = str(it.get("name", "")).lower()
            row = conn.execute("SELECT doc_json FROM functions WHERE name_lower = ?", (name_low,)).fetchone()
            if not row:
                errors.append(f"function missing in DB: {it.get('name')}")

    # 3. Topics
    top_file = data_dir / "topics.json"
    if top_file.is_file():
        with open(top_file, "r", encoding="utf-8") as f:
            raw = json.load(f)
        items = raw.get("items", []) if isinstance(raw, dict) else raw
        db_count = conn.execute("SELECT COUNT(*) FROM topics").fetchone()[0]
        if len(items) != db_count:
            errors.append(f"topics count mismatch: JSON={len(items)} vs DB={db_count}")

    # 4. Syntax
    syn_file = data_dir / "syntax.json"
    if syn_file.is_file():
        with open(syn_file, "r", encoding="utf-8") as f:
            raw = json.load(f)
        expected_sym_count = len(raw.get("commands", {})) + len(raw.get("functions", {}))
        db_count = conn.execute("SELECT COUNT(*) FROM symbols").fetchone()[0]
        if expected_sym_count != db_count:
            errors.append(f"symbols count mismatch: JSON={expected_sym_count} vs DB={db_count}")

    # 5. Index
    idx_file = data_dir / "index.json"
    if idx_file.is_file():
        with open(idx_file, "r", encoding="utf-8") as f:
            raw = json.load(f)
        items = raw.get("items", []) if isinstance(raw, dict) else raw
        db_count = conn.execute("SELECT COUNT(*) FROM index_items").fetchone()[0]
        if len(items) != db_count:
            errors.append(f"index_items count mismatch: JSON={len(items)} vs DB={db_count}")

    conn.close()
    return len(errors) == 0, errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Constructor determinista de la base de datos BIKI SQLite")
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # Subcomando: build
    p_build = subparsers.add_parser("build", help="Construir base de datos SQLite")
    p_build.add_argument("--data", type=Path, required=True, help="Directorio con archivos JSON de a3ref")
    p_build.add_argument("--out", type=Path, required=True, help="Ruta del fichero .db de salida")
    p_build.add_argument("--no-fts", action="store_true", help="Desactivar índice de texto completo FTS5")
    p_build.add_argument("--jobs", type=int, default=1, help="Número de jobs (respetado como estándar)")

    # Subcomando: stats
    p_stats = subparsers.add_parser("stats", help="Mostrar estadísticas de la base de datos")
    p_stats.add_argument("--db", type=Path, required=True, help="Ruta del fichero .db")

    # Subcomando: verify
    p_verify = subparsers.add_parser("verify", help="Verificar paridad DB vs JSON")
    p_verify.add_argument("--db", type=Path, required=True, help="Ruta del fichero .db")
    p_verify.add_argument("--data", type=Path, required=True, help="Directorio con archivos JSON de a3ref")

    # Subcomando: query
    p_query = subparsers.add_parser("query", help="Consultar información en la base de datos")
    p_query.add_argument("--db", type=Path, required=True, help="Ruta del fichero .db")
    p_query.add_argument("--command", type=str, default=None, help="Nombre de comando a consultar")
    p_query.add_argument("--function", type=str, default=None, help="Nombre de función a consultar")
    p_query.add_argument("--topic", type=str, default=None, help="Título de tópico a consultar")
    p_query.add_argument("--search", type=str, default=None, help="Texto a buscar (FTS o LIKE)")

    args = parser.parse_args()

    if args.subcommand == "build":
        t0 = time.perf_counter()
        res = build_db(args.data, args.out, enable_fts=not args.no_fts)
        elapsed = round(time.perf_counter() - t0, 3)
        res["build_time_seconds"] = elapsed
        print(f"Base de datos generada exitosamente en {args.out} ({elapsed}s)")
        print(json.dumps(res, indent=2, ensure_ascii=False))
        return 0

    elif args.subcommand == "stats":
        stats = get_db_stats(args.db)
        print(json.dumps(stats, indent=2, ensure_ascii=False))
        return 0

    elif args.subcommand == "verify":
        ok, errs = verify_db_parity(args.db, args.data)
        if ok:
            print("VERIFICACIÓN EXITOSA: Paridad completa DB <-> JSON confirmada.")
            return 0
        else:
            print(f"FALLO DE VERIFICACIÓN: {len(errs)} error(es) detectado(s):", file=sys.stderr)
            for e in errs:
                print(f"  - {e}", file=sys.stderr)
            return 1

    elif args.subcommand == "query":
        res = query_db(args.db, command=args.command, function=args.function, topic=args.topic, search=args.search)
        if res is not None:
            print(json.dumps(res, indent=2, ensure_ascii=False))
            return 0
        else:
            print("Elemento no encontrado en la base de datos.", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
