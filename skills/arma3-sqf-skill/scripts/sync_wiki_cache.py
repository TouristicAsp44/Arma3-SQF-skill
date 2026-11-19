#!/usr/bin/env python3
"""sync_wiki_cache.py - Sincronización determinista, reversible e idempotente de wiki-cache.md.

Aplica la regla de solo celdas vacías, preservando notas humanas e invariantes
de servidor dedicado, actualizando procedencia con Git SHA dinámico.
"""

from __future__ import annotations

import argparse
import datetime
import os
import re
import shutil
import sys
from pathlib import Path

# Agregar carpeta scripts para importar sqf_wiki_reader
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from sqf_wiki_reader import (
    get_command,
    get_data_git_sha,
    get_function,
    resolve_wiki_root,
)

DEFAULT_CACHE_PATH = SCRIPT_DIR.parent / "references" / "wiki-cache.md"
BACKUP_DIR = Path(
    os.environ.get(
        "ARMA3_BACKUP_DIR",
        str(Path.home() / ".gemini" / "antigravity" / "backups" / "arma3-sqf-skill" / "references"),
    )
)


def sync_cache(
    cache_path: Path,
    dry_run: bool = False,
    wiki_path: str | None = None,
) -> tuple[bool, str]:
    if not cache_path.exists():
        return False, f"Error: no existe el archivo {cache_path}"

    data_dir = resolve_wiki_root(wiki_path)
    data_sha = get_data_git_sha(data_dir)
    today_str = datetime.date.today().isoformat()

    content = cache_path.read_text(encoding="utf-8")
    lines = content.splitlines()

    table_header_idx = -1
    for idx, line in enumerate(lines):
        if line.startswith("| Comando |"):
            table_header_idx = idx
            break

    if table_header_idx == -1:
        return False, "Error: no se encontró la cabecera de la tabla en wiki-cache.md"

    header_cells = [c.strip() for c in lines[table_header_idx].split("|")[1:-1]]
    try:
        header_cells.index("Comando")
        col_sintaxis = header_cells.index("Sintaxis")
        col_arg = header_cells.index("Arg")
        col_efe = header_cells.index("Efe")
        header_cells.index("Nota MP / Restricciones")
        col_url = header_cells.index("URL Biki")
        col_estado = header_cells.index("Estado")
        col_consultado = header_cells.index("Consultado")
        col_fuente = header_cells.index("Fuente")
    except ValueError as e:
        return False, f"Error en estructura de columnas de la tabla: {e}"

    filas_verificadas = 0
    filas_ausentes = 0
    filas_no_revisadas = 0

    new_lines = list(lines)
    row_count = 0

    for i in range(table_header_idx + 2, len(lines)):
        line = lines[i]
        if not line.startswith("|"):
            break
        m = re.match(r"^\|\s*`([a-zA-Z0-9_]+)`\s*\|", line)
        if not m:
            continue

        row_count += 1
        cmd_name = m.group(1)
        cells = [c.strip() for c in line.split("|")[1:-1]]
        if len(cells) != len(header_cells):
            return False, f"Desalineación de columnas en fila {row_count} ({cmd_name}): {len(cells)} != {len(header_cells)}"

        # Consultar catálogo a3ref
        info = get_command(cmd_name, data_dir) or get_function(cmd_name, data_dir)

        if info:
            filas_verificadas += 1

            # 1. Sintaxis (solo celda vacía o guión)
            if not cells[col_sintaxis] or cells[col_sintaxis] == "-":
                syntaxes = info.get("syntaxes", [])
                if syntaxes and isinstance(syntaxes, list):
                    first_syn = syntaxes[0].get("syntax", "")
                    if first_syn:
                        cells[col_sintaxis] = f"`{first_syn}`"
                if not cells[col_sintaxis] or cells[col_sintaxis] == "-":
                    cells[col_sintaxis] = f"`{info.get('canonical_name', cmd_name)}`"

            # 2. Localidad: Arg y Efe (solo celda vacía o guión)
            loc = info.get("locality", {})
            if isinstance(loc, dict):
                arg_val = loc.get("argument")
                if not cells[col_arg] or cells[col_arg] == "-":
                    if arg_val == "global":
                        cells[col_arg] = "AG"
                    elif arg_val == "local":
                        cells[col_arg] = "AL"

                efe_val = loc.get("effect")
                if not cells[col_efe] or cells[col_efe] == "-":
                    if efe_val == "global":
                        cells[col_efe] = "EG"
                    elif efe_val == "local":
                        cells[col_efe] = "EL"

            # 3. URL Biki (solo celda vacía o guión)
            if not cells[col_url] or cells[col_url] == "-" or not cells[col_url].startswith("https://community.bistudio.com/wiki/"):
                cells[col_url] = info.get("url") or f"https://community.bistudio.com/wiki/{info.get('canonical_name', cmd_name)}"

            # 4. Estado: actualizar a VERIFICADO
            cells[col_estado] = "VERIFICADO"

            # 5. Consultado (solo si vacía o guión)
            if not cells[col_consultado] or cells[col_consultado] == "-":
                cells[col_consultado] = today_str

            # 6. Fuente: inyectar SHA en runtime (si vacía o guión)
            if not cells[col_fuente] or cells[col_fuente] == "-":
                cells[col_fuente] = f"a3ref (commit: {data_sha})"
        else:
            filas_ausentes += 1
            cells[col_estado] = "NO VERIFICADO"

        new_lines[i] = "| " + " | ".join(cells) + " |"

    total_filas_tabla = row_count
    if filas_verificadas + filas_ausentes + filas_no_revisadas != total_filas_tabla or total_filas_tabla != 31:
        return False, (
            f"Violación de invariante de conservación de filas: "
            f"verificadas ({filas_verificadas}) + ausentes ({filas_ausentes}) + "
            f"no revisadas ({filas_no_revisadas}) != total ({total_filas_tabla}), esperado exactamente 31"
        )

    summary_msg = (
        f"Sincronización analizada: {total_filas_tabla} filas totales | "
        f"{filas_verificadas} verificadas | {filas_ausentes} ausentes | {filas_no_revisadas} no revisadas | "
        f"Git SHA: {data_sha}"
    )

    if dry_run:
        return True, f"[DRY-RUN] {summary_msg} (Sin escrituras en disco)."

    # Crear respaldo obligatorio antes de escribir
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    ts_bak = BACKUP_DIR / f"wiki-cache.md.{ts}.bak"
    latest_bak = BACKUP_DIR / "wiki-cache.md.bak.latest"
    shutil.copyfile(cache_path, ts_bak)
    shutil.copyfile(cache_path, latest_bak)

    if not ts_bak.exists() or ts_bak.stat().st_size != cache_path.stat().st_size:
        return False, f"Error: Falló la creación del respaldo externo en {ts_bak}"

    # Escritura atómica mediante archivo .tmp
    tmp_path = cache_path.with_suffix(".tmp")
    tmp_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    tmp_path.replace(cache_path)

    return True, f"[EXITO] {summary_msg} (Archivo wiki-cache.md actualizado y respaldado en {ts_bak.name})."


def main():
    parser = argparse.ArgumentParser(description="Sincronizador de wiki-cache.md con la réplica a3ref")
    parser.add_argument("--dry-run", action="store_true", help="Simulación sin modificar archivos en disco")
    parser.add_argument("--target", type=str, default=str(DEFAULT_CACHE_PATH), help="Ruta al archivo wiki-cache.md")
    parser.add_argument("--wiki-path", type=str, default=None, help="Ruta personalizada a la base de datos data")

    args = parser.parse_args()
    ok, msg = sync_cache(Path(args.target), dry_run=args.dry_run, wiki_path=args.wiki_path)
    print(msg)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
