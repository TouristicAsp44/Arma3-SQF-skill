"""Test de rutas absolutas en el código de runtime (R2 / tarea 1.d).

Ninguna ruta del código puede apuntar a una ubicación absoluta del sistema de
files del desarrollador. Solo se admiten:
  - rutas derivadas de `Path(__file__)`,
  - variables de entorno declaradas,
  - argumentos de CLI,
  - la lista blanca `~` de candidatos estándar de usuario (`.a3ref`, `.gemini`).
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
THIS_FILE = Path(__file__).resolve()

# El escáner solo aplica al CÓDIGO DE RUNTIME. Los tests pueden usar rutas
# sintéticas (p. ej. "C:/nonexistent_wiki_dir_xyz_123") para comprobar
# fallbacks, y este propio fichero contiene los patrones prohibidos.
RUNTIME_DIRS = [
    REPO_ROOT / "skills" / "arma3-sqf-skill" / "scripts",
    REPO_ROOT / "skills" / "arma3-sqf-skill" / "references",
    REPO_ROOT / "scripts",
]

ARTIFACT_DIRS = [
    REPO_ROOT / "integrations",
]

EXCLUDED_DIRS = {"legacy", ".git", "build", "dist", "__pycache__", ".pytest_cache"}

# Rutas absolutas prohibidas (literales deFS absolutas del autor).
FORBIDDEN_LITERALS = [
    "EDEN EDITOR",
    "C:\\Users",
    "C:/Users",
    "/home/",
]

FORBIDDEN_ARTIFACT_LITERALS = [
    "EDEN EDITOR",
    "C:\\Users",
    "C:/Users",
    "/home/",
    "/var/arma3",
]

# Patrones de rutas absolutas embebidas.
ABSOLUTE_PATH_RE = re.compile(r"[\"'](?:[A-Za-z]:\\\\|[A-Za-z]:/|/(?:home|Users|mnt|opt|var|tmp)/)")

# Rutas `~` permitidas (lista blanca explícita).
ALLOWED_HOME_RE = re.compile(r"Path\.home\(\)\s*/\s*\"(?P<dir>\.[A-Za-z0-9_.-]+)\"")

ALLOWED_HOME_DIRS = {".a3ref", ".gemini"}

# Patrones permitidos porque derivan de __file__, env var o argumento CLI.
ALLOWED_PATTERNS = [
    re.compile(r"Path\(__file__\)"),
    re.compile(r"os\.environ(?:\.get)?\("),
    re.compile(r"os\.getenv\("),
    re.compile(r"resolve_wiki_root\("),
    re.compile(r"--wiki-path"),
]


def _iter_source_files() -> list[Path]:
    files: list[Path] = []
    for base in RUNTIME_DIRS:
        if not base.is_dir():
            continue
        for pattern in ("*.py", "*.md", "**/*.py", "**/*.md"):
            files.extend(base.glob(pattern))
    return sorted(
        {
            f
            for f in files
            if f.resolve() != THIS_FILE
            and not any(part in EXCLUDED_DIRS for part in f.relative_to(REPO_ROOT).parts)
        }
    )


def test_no_absolute_paths_in_sources() -> None:
    offenders: list[str] = []

    for path in _iter_source_files():
        text = path.read_text(encoding="utf-8", errors="replace")
        rel = path.relative_to(REPO_ROOT)

        for literal in FORBIDDEN_LITERALS:
            if literal in text:
                offenders.append(f"{rel}: literal prohibido {literal!r}")

        for match in ABSOLUTE_PATH_RE.finditer(text):
            snippet = match.group(0)
            line_no = text[: match.start()].count("\n") + 1
            line = text.splitlines()[line_no - 1] if line_no <= len(text.splitlines()) else ""
            if any(pat.search(line) for pat in ALLOWED_PATTERNS):
                continue
            offenders.append(f"{rel}:{line_no}: ruta absoluta {snippet!r}")

        for match in ALLOWED_HOME_RE.finditer(text):
            if match.group("dir") not in ALLOWED_HOME_DIRS:
                offenders.append(
                    f"{rel}: Path.home() sobre un directorio no whitelistado: {match.group('dir')!r}"
                )

    assert not offenders, "Rutas absolutas no permitidas:\n" + "\n".join(offenders)


def test_no_absolute_paths_in_integrations_artifacts() -> None:
    """B.3: Los artefactos distribuibles en integrations/ no contienen rutas absolutas."""
    offenders: list[str] = []
    allowed_artifact_patterns = [
        re.compile(r"~/\.a3ref"),
        re.compile(r"~/\.gemini"),
    ]

    for base in ARTIFACT_DIRS:
        if not base.is_dir():
            continue
        for path in base.glob("**/*"):
            if not path.is_file() or any(part in EXCLUDED_DIRS for part in path.parts):
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            rel = path.relative_to(REPO_ROOT)

            for literal in FORBIDDEN_ARTIFACT_LITERALS:
                if literal in text:
                    offenders.append(f"{rel}: literal prohibido {literal!r}")

            for match in ABSOLUTE_PATH_RE.finditer(text):
                snippet = match.group(0)
                line_no = text[: match.start()].count("\n") + 1
                line = text.splitlines()[line_no - 1] if line_no <= len(text.splitlines()) else ""
                if any(pat.search(line) for pat in allowed_artifact_patterns):
                    continue
                offenders.append(f"{rel}:{line_no}: ruta absoluta {snippet!r}")

    assert not offenders, "Rutas absolutas no permitidas en integrations/:\n" + "\n".join(offenders)

