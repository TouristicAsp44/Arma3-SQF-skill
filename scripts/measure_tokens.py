#!/usr/bin/env python3
"""Medición de presupuesto de tokens para arma3-sqf-skill.

Presupuesto normativo (DoD v2.4):
    - tokens_frontmatter <= 250   (frontmatter description de SKILL.md)
    - tokens_capa0      <= 1.200 (cuerpo de SKILL.md sin frontmatter)
    - tokens_turno_max  <= 2.500 (capa0 + lente más larga)

Margen de tolerancia: 15% por discrepancias entre tokenizers (tiktoken cl100k_base
vs tokenizers propios de Claude, Gemini u OpenAI).
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = REPO_ROOT / "skills" / "arma3-sqf-skill"
SKILL_FILE = SKILL_DIR / "SKILL.md"
SKILL_EN_FILE = REPO_ROOT / "skills" / "arma3-sqf-skill-en" / "SKILL.md"
LENSES_DIR = SKILL_DIR / "references" / "lenses"

BUDGET_FRONTMATTER = 250
BUDGET_CAPA0 = 1200
BUDGET_TURNO_MAX = 2500
MARGIN_RATIO = 1.15


def measure_skill_file(skill_path: Path, enc) -> tuple[int, int, bool]:
    text = skill_path.read_text(encoding="utf-8")
    parts = text.split("---", 2)
    frontmatter = parts[1] if len(parts) > 2 else ""
    body = parts[2] if len(parts) > 2 else text

    fm_tokens = len(enc.encode(frontmatter))
    body_tokens = len(enc.encode(body))
    return fm_tokens, body_tokens, True


def measure_lenses(lenses_dir: Path, enc) -> dict[str, int]:
    lens_tokens: dict[str, int] = {}
    if lenses_dir.is_dir():
        for path in sorted(lenses_dir.glob("*.md")):
            lens_tokens[path.name] = len(enc.encode(path.read_text(encoding="utf-8")))
    return lens_tokens


def main() -> int:
    try:
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
    except ImportError:
        print("WARN: tiktoken no disponible; instalando estimación heurística (1 token ~ 4 caracteres).")
        class HeuristicEncoder:
            def encode(self, text: str) -> list[int]:
                return [0] * max(1, len(text) // 4)
        enc = HeuristicEncoder()

    if not SKILL_FILE.is_file():
        print(f"ERROR: {SKILL_FILE} no existe.")
        return 1

    fm_tokens, body_tokens, _ = measure_skill_file(SKILL_FILE, enc)
    lenses = measure_lenses(LENSES_DIR, enc)
    max_lens_tokens = max(lenses.values()) if lenses else 0
    max_lens_name = max(lenses, key=lenses.get) if lenses else "ninguna"
    turno_max = body_tokens + max_lens_tokens

    print("== Medición de tokens (tiktoken cl100k_base) ==")
    print(f"  Frontmatter (ES): {fm_tokens} tokens (presupuesto <= {BUDGET_FRONTMATTER})")
    print(f"  Capa 0 (ES):      {body_tokens} tokens (presupuesto <= {BUDGET_CAPA0})")
    print(f"  Lente más larga:  {max_lens_tokens} tokens ({max_lens_name})")
    print(f"  Turno máx (ES):   {turno_max} tokens (presupuesto <= {BUDGET_TURNO_MAX})")

    limit_fm = int(BUDGET_FRONTMATTER * MARGIN_RATIO)
    limit_capa0 = int(BUDGET_CAPA0 * MARGIN_RATIO)
    limit_turno = int(BUDGET_TURNO_MAX * MARGIN_RATIO)

    failed = False
    if fm_tokens > limit_fm:
        print(f"FALLO: frontmatter supera {BUDGET_FRONTMATTER} tokens (+15% margen = {limit_fm})")
        failed = True
    if body_tokens > limit_capa0:
        print(f"FALLO: Capa 0 supera {BUDGET_CAPA0} tokens (+15% margen = {limit_capa0})")
        failed = True
    if turno_max > limit_turno:
        print(f"FALLO: Turno máximo supera {BUDGET_TURNO_MAX} tokens (+15% margen = {limit_turno})")
        failed = True

    if SKILL_EN_FILE.is_file():
        fm_en, body_en, _ = measure_skill_file(SKILL_EN_FILE, enc)
        turno_en = body_en + max_lens_tokens
        print(f"  Frontmatter (EN): {fm_en} tokens (presupuesto <= {BUDGET_FRONTMATTER})")
        print(f"  Capa 0 (EN):      {body_en} tokens (presupuesto <= {BUDGET_CAPA0})")
        print(f"  Turno máx (EN):   {turno_en} tokens (presupuesto <= {BUDGET_TURNO_MAX})")
        if fm_en > limit_fm or body_en > limit_capa0 or turno_en > limit_turno:
            print("FALLO: versión EN supera presupuesto de tokens.")
            failed = True

    if failed:
        return 1

    print("\nPresupuesto de tokens respetado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
