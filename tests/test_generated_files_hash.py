"""Test de coherencia de los artefactos GENERADOS por región (R6).

Modelo de regiones:
  - Bloque `<!-- AUTHORED --> ... <!-- /AUTHORED -->`: contenido específico de
    la disciplina, escrito a mano. Se protege con un hash en
    `scripts/generated.lock.json`.
  - Región `<!-- CANON-EXTRACT:* --> ... <!-- /CANON-EXTRACT:* -->`: extracto
    normativo inyectado desde el canónico. Se verifica por hash contra el
    documento canónico.

Fase 2: los ficheros derivados (lentes, paquetes inline) aún no existen en
PR-1; el test se limita entonces a verificar la coherencia de las regiones
presentes.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = REPO_ROOT / "skills" / "arma3-sqf-skill"
REFERENCES = SKILL_DIR / "references"
LOCK_FILE = REPO_ROOT / "scripts" / "generated.lock.json"

EXCLUDED_DIRS = {"legacy", ".git", "build", "dist", "__pycache__", ".pytest_cache"}

AUTHORED_RE = re.compile(
    r"<!--\s*AUTHORED\s*-->(?P<body>.*?)<!--\s*/AUTHORED\s*-->", re.DOTALL
)
CANON_EXTRACT_RE = re.compile(
    r"<!--\s*CANON-EXTRACT:(?P<anchor>[A-Z_]+)\s*-->(?P<body>.*?)<!--\s*/CANON-EXTRACT:(?P=anchor)\s*-->",
    re.DOTALL,
)
CANON_BLOCK_RE = re.compile(
    r"<!--\s*CANON:(?P<anchor>[A-Z_]+)\s*-->(?P<body>.*?)<!--\s*/CANON:(?P=anchor)\s*-->",
    re.DOTALL,
)


def _sha256(text: str) -> str:
    return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()


def _iter_derived_files() -> list[Path]:
    files: list[Path] = []
    for base in (REFERENCES / "lenses", REFERENCES / "workflows", REPO_ROOT / "integrations"):
        if base.is_dir():
            files.extend(base.rglob("*.md"))
    return sorted(f for f in files if not any(p in EXCLUDED_DIRS for p in f.parts))


def _canonical_blocks() -> dict[str, str]:
    blocks: dict[str, str] = {}
    for path in REFERENCES.glob("*.md"):
        text = path.read_text(encoding="utf-8")
        for match in CANON_BLOCK_RE.finditer(text):
            blocks[match.group("anchor")] = match.group("body")
    return blocks


def test_canon_extracts_match_canonical() -> None:
    """Cada extracto inyectado coincide con el bloque canónico correspondiente."""
    if not _iter_derived_files():
        return  # Fase 2: aún no hay artefactos derivados.

    canonical = _canonical_blocks()
    assert canonical, "No se encontraron bloques CANON en references/"

    offenders: list[str] = []
    for path in _iter_derived_files():
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(REPO_ROOT).as_posix()
        for match in CANON_EXTRACT_RE.finditer(text):
            anchor = match.group("anchor")
            body = match.group("body")
            if anchor not in canonical:
                offenders.append(f"{rel}: extracto de un ancla inexistente CANON:{anchor}")
                continue
            expected = canonical[anchor]
            if body.strip() not in expected and expected.strip() not in body.strip():
                offenders.append(
                    f"{rel}: el extracto CANON-EXTRACT:{anchor} no coincide con el canónico (hash "
                    f"{_sha256(body)[:12]} != {_sha256(expected)[:12]})"
                )

    assert not offenders, "Extractos normativos divergentes:\n" + "\n".join(offenders)


def test_authored_regions_match_lock() -> None:
    """Las regiones AUTHORED no cambian sin actualizar el lock."""
    if not LOCK_FILE.is_file():
        return  # Fase 2: el lock se crea junto a las lentes.
    if not _iter_derived_files():
        return

    lock = json.loads(LOCK_FILE.read_text(encoding="utf-8"))
    offenders: list[str] = []
    for path in _iter_derived_files():
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(REPO_ROOT).as_posix()
        for index, match in enumerate(AUTHORED_RE.finditer(text)):
            digest = _sha256(match.group("body"))
            key = f"{rel}#AUTHORED:{index}"
            expected = lock.get("authored", {}).get(key)
            if expected is None:
                offenders.append(f"{key}: región AUTHORED sin entrada en generated.lock.json")
            elif expected != digest:
                offenders.append(f"{key}: hash {digest[:12]} != lock {expected[:12]}")

    assert not offenders, "Regiones AUTHORED divergentes del lock:\n" + "\n".join(offenders)


def test_generated_files_match_lock() -> None:
    """Los ficheros generados completos coinciden con el hash registrado en el lock."""
    if not LOCK_FILE.is_file():
        return
    lock = json.loads(LOCK_FILE.read_text(encoding="utf-8"))
    generated = lock.get("generated", {})
    if not generated:
        return

    offenders: list[str] = []
    for rel, expected in generated.items():
        file_path = REPO_ROOT / rel
        if not file_path.is_file():
            offenders.append(f"{rel}: fichero generado no existe")
            continue
        actual = _sha256(file_path.read_text(encoding="utf-8"))
        if actual != expected:
            offenders.append(f"{rel}: hash {actual[:12]} != lock {expected[:12]}")

    assert not offenders, "Ficheros generados divergentes del lock:\n" + "\n".join(offenders)

