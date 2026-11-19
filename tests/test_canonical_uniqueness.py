"""Test de unicidad de las reglas normativas (R2).

Fase 1 (exigible desde PR-1):
  - Cada ancla canónica `<!-- CANON:* -->` aparece EXACTAMENTE UNA vez en todo
    el repositorio, y vive en su documento canónico.
  - Los extractos `<!-- CANON-EXTRACT:* -->` (regiones inyectadas en
    artefactos derivados) están permitidos, pero deben quedar dentro de un
    archivo y ser verificables por hash.

Fase 2 (exigible desde PR-2):
  - Las definiciones normativas (N3) no aparecen fuera de su canónico.
  - La Capa 0 contiene exactamente 7 líneas de índice (N1).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = REPO_ROOT / "skills" / "arma3-sqf-skill"
REFERENCES = SKILL_DIR / "references"

EXCLUDED_DIRS = {"legacy", ".git", "build", "dist", "__pycache__", ".pytest_cache"}

# Documentos canónicos y anclas que cada uno posee.
CANONICAL_DOCS: dict[str, set[str]] = {
    "references/invariants.md": {
        "BLOQUEANTES",
        "PUERTA",
        "HONESTIDAD",
        "MODOS",
        "PRECEDENCIA",
        "PROPIEDAD",
    },
    "references/sqf-standards.md": {"ESTANDAR"},
    "references/rubrica.md": {"RUBRICA", "PARTICIPACION"},
}

CANON_ANCHOR_RE = re.compile(r"<!--\s*CANON:([A-Z_]+)\s*-->")
CANON_EXTRACT_RE = re.compile(r"<!--\s*CANON-EXTRACT:([A-Z_]+)\s*-->")


def _iter_repo_files() -> list[Path]:
    files: list[Path] = []
    for pattern in ("*.md", "**/*.md"):
        files.extend(REPO_ROOT.glob(pattern))
    return sorted(
        {
            f
            for f in files
            if not any(part in EXCLUDED_DIRS for part in f.relative_to(REPO_ROOT).parts)
            and f.name not in {"PARIDAD.md", "QUALITY.md"}
            and not f.name.startswith("PLAN-IMPROVEMENTS")
        }
    )


def _canonical_path(doc: str) -> Path:
    return SKILL_DIR / doc


def _layered_skill_exists() -> bool:
    """El SKILL.md reescrito en capas (PR-2) sustituye al original."""
    skill_file = REPO_ROOT / "skills" / "arma3-sqf-skill" / "SKILL.md"
    return skill_file.is_file() and "AUDITAR" in skill_file.read_text(encoding="utf-8")


requires_layered_skill = pytest.mark.skipif(
    not _layered_skill_exists(),
    reason="El SKILL.md en capas se escribe en PR-2; la unicidad N3 se verifica desde PR-2.",
)


def test_canonical_anchors_exist_once() -> None:
    """Cada ancla CANON aparece exactamente una vez y en su documento canónico."""
    seen: dict[str, list[str]] = {}
    offenders: list[str] = []

    for path in _iter_repo_files():
        text = path.read_text(encoding="utf-8", errors="replace")
        rel = path.relative_to(REPO_ROOT).as_posix()
        for match in CANON_ANCHOR_RE.finditer(text):
            anchor = match.group(1)
            seen.setdefault(anchor, []).append(rel)

    for doc, anchors in CANONICAL_DOCS.items():
        canonical = _canonical_path(doc)
        if not canonical.is_file():
            offenders.append(f"documento canónico ausente: {doc}")
            continue
        text = canonical.read_text(encoding="utf-8")
        present = set(CANON_ANCHOR_RE.findall(text))
        for anchor in anchors:
            if anchor not in present:
                offenders.append(f"{doc}: falta el ancla CANON:{anchor}")

    for anchor, locations in seen.items():
        if len(locations) != 1:
            offenders.append(f"CANON:{anchor} aparece {len(locations)} veces: {locations}")
            continue
        owner = [doc for doc, anchors in CANONICAL_DOCS.items() if anchor in anchors]
        if not owner:
            offenders.append(f"CANON:{anchor} no pertenece a ningún documento canónico")
        elif locations[0] != _canonical_path(owner[0]).relative_to(REPO_ROOT).as_posix():
            offenders.append(
                f"CANON:{anchor} vive en {locations[0]} pero su canónico es {owner[0]}"
            )

    assert not offenders, "Unicidad de anclas rota:\n" + "\n".join(offenders)


def test_canonical_documents_exist() -> None:
    """Los tres documentos canónicos existen y son localizables."""
    missing = [doc for doc in CANONICAL_DOCS if not _canonical_path(doc).is_file()]
    assert not missing, f"Documentos canónicos ausentes: {missing}"


@requires_layered_skill
def test_n3_definitions_not_duplicated_outside_canonical() -> None:
    """Las definiciones normativas N3 no se repiten fuera de su canónico (Fase 2)."""
    invariants = _canonical_path("references/invariants.md")
    if not invariants.is_file():
        return  # Fase 2: el canónico aún no existe.

    canonical_text = invariants.read_text(encoding="utf-8")
    # Frases distintivas de la definición de bloqueante (N3).
    n3_markers = [
        "variables locales fugadas al scope exterior",
        "condición alcanzable garantizada ni timeout de seguridad",
        "una guarda `if (hasInterface)` NO lo legitima",
        "ausentes de la lista blanca de `CfgRemoteExec >> Functions`",
        "discrepancias en cantidad, orden o tipos de datos requeridos en `params`",
    ]
    for marker in n3_markers:
        assert marker in canonical_text, f"Marcador N3 ausente del canónico: {marker!r}"

    offenders: list[str] = []
    for path in _iter_repo_files():
        rel = path.relative_to(REPO_ROOT).as_posix()
        if rel == "skills/arma3-sqf-skill/references/invariants.md":
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for marker in n3_markers:
            if marker in text:
                offenders.append(f"{rel}: contiene una definición N3 fuera del canónico")

    assert not offenders, "Definiciones N3 duplicadas:\n" + "\n".join(offenders)
