#!/usr/bin/env python3
"""fake_linter.py - Simulador determinista de run_sqflint.py para el arnés de pruebas (D8).

Reproduce con fidelidad los formatos reales de sqflint:
1. Error de sentencia no interpretable con marca de variable y argumento:
   archivo:línea: error: can't interpret statement (missing ;?): <Variable(cmd)> <String("...")>
2. Aviso de ámbito con literal de variable:
   archivo:línea: warning: Local variable "_x" is not from this scope (not private)
3. Caso combinado (para pruebas de precedencia):
   archivo:línea: warning: Local variable "_x" is not from this scope (not private): <Variable(cmd)>
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def simulate_linter(target: Path, forced_rc: int | None = None) -> tuple[int, str]:
    if forced_rc is not None:
        if forced_rc == 0:
            return 0, f"{target}:1: info: SIN ERRORES"
        if forced_rc == 1:
            return 1, f'{target}:1: error: can\'t interpret statement (missing ;?): <Variable(testErr)> <String("arg")>'
        if forced_rc == 2:
            return 2, "Error de uso: argumentos inválidos"
        if forced_rc == 3:
            return 3, f"{target}:1: error: Directorio vacío o sin archivos .sqf"
        return forced_rc, f"{target}:1: error: rc {forced_rc}"

    if not target.exists():
        # Para pruebas CLI con targets simulados no existentes en disco
        return 1, f'{target}:1: error: can\'t interpret statement (missing ;?): <Variable(playSoundUI)> <String("test")>'

    if target.is_dir():
        sqf_files = list(target.rglob("*.sqf"))
        if not sqf_files:
            return 3, f"{target}:1: error: Directorio vacío o sin archivos .sqf"
        target = sqf_files[0]

    content = target.read_text(encoding="utf-8", errors="ignore")

    lines: list[str] = []
    has_error = False

    if "SYNTAX_ERROR" in content:
        lines.append(f'{target}:10: error: can\'t interpret statement (missing ;?): <Variable(syntaxErrCmd)> <String("arg")>')
        has_error = True

    if "SIMULTANEOUS_SCOPE" in content:
        lines.append(f'{target}:5: warning: Local variable "_z" is not from this scope (not private): <Variable(setPos)>')

    elif "SCOPE_WARNING" in content or "_z" in content:
        lines.append(f'{target}:5: warning: Local variable "_z" is not from this scope (not private)')

    if "GENERIC_WARNING" in content:
        lines.append(f"{target}:15: warning: Advertencia general de linter")

    # Detectar tokens de variables o comandos en el contenido para emitir marcas <Variable(...)> con formato real
    tokens = re.findall(r"\b([a-zA-Z_]\w*)\b", content)
    for tok in tokens:
        if tok in ("playSoundUI", "comandoInventado123", "setpos", "setPos", "testVar"):
            lines.append(f'{target}:1: error: can\'t interpret statement (missing ;?): <Variable({tok})> <String("param")>')
            has_error = True
            break

    if has_error:
        return 1, "\n".join(lines)

    if lines:
        lines.append(f"{target}:0: info: SIN ERRORES")
        return 0, "\n".join(lines)

    return 0, f"{target}:0: info: SIN ERRORES"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Simulador determinista de sqflint")
    parser.add_argument("target", nargs="?", help="Archivo .sqf o directorio a analizar")
    parser.add_argument("--rc", type=int, default=None, help="Forzar código de salida")

    args = parser.parse_args(argv)

    if not args.target and args.rc is None:
        parser.print_usage(sys.stderr)
        return 2

    target_path = Path(args.target) if args.target else Path(".")
    rc, output = simulate_linter(target_path, forced_rc=args.rc)

    if output:
        print(output)
    return rc


if __name__ == "__main__":
    sys.exit(main())
