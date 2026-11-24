#!/usr/bin/env python3
"""Empaquetador oficial del artefacto distribuible `arma3-sqf-skill.zip`.

Construye un ZIP con estructura canónica estricta:
  - Directorio raíz único: `arma3-sqf-skill/`
  - Archivos:
      * SKILL.md
      * agents/openai.yaml
      * assets/logo.png
      * references/*.md (incluyendo referencias de workflows)
      * scripts/*.py y scripts/bootstrap.sh
  - Exclusiones estrictas: tests/, evals/, docs/, cachés, .pyc, etc.
  - Normalización de terminaciones de línea a LF.
  - Verificación de peso total < 150 KB.
"""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = REPO_ROOT / "skills" / "arma3-sqf-skill"
ASSETS_DIR = REPO_ROOT / "assets"
OUTPUT_ZIP = REPO_ROOT / "arma3-sqf-skill.zip"

FORBIDDEN_PATTERNS = [
    "tests",
    "evals",
    "docs",
    "legacy",
    "dist",
    ".git",
    ".github",
    ".coverage",
    "__pycache__",
    ".pyc",
]


def build_package(dest_path: Path = OUTPUT_ZIP) -> tuple[int, list[str]]:
    """Construye y valida el archivo ZIP distribuible."""
    files_to_pack: list[tuple[Path, str]] = []

    # 1. SKILL.md
    skill_md = SKILL_DIR / "SKILL.md"
    if not skill_md.is_file():
        raise FileNotFoundError(f"Falta SKILL.md en {skill_md}")
    files_to_pack.append((skill_md, "arma3-sqf-skill/SKILL.md"))

    # 2. agents/openai.yaml
    openai_yaml = SKILL_DIR / "agents" / "openai.yaml"
    if not openai_yaml.is_file():
        raise FileNotFoundError(f"Falta openai.yaml en {openai_yaml}")
    files_to_pack.append((openai_yaml, "arma3-sqf-skill/agents/openai.yaml"))

    # 3. assets/logo.png
    logo_png = ASSETS_DIR / "logo.png"
    if not logo_png.is_file():
        raise FileNotFoundError(f"Falta logo.png en {logo_png}")
    files_to_pack.append((logo_png, "arma3-sqf-skill/assets/logo.png"))

    # 4. references/ (*.md)
    ref_dir = SKILL_DIR / "references"
    for p in sorted(ref_dir.rglob("*.md")):
        rel = p.relative_to(SKILL_DIR).as_posix()
        files_to_pack.append((p, f"arma3-sqf-skill/{rel}"))

    # 5. scripts/ (*.py y bootstrap.sh)
    scripts_dir = SKILL_DIR / "scripts"
    for p in sorted(scripts_dir.glob("*.py")):
        rel = p.relative_to(SKILL_DIR).as_posix()
        files_to_pack.append((p, f"arma3-sqf-skill/{rel}"))

    bootstrap_sh = scripts_dir / "bootstrap.sh"
    if not bootstrap_sh.is_file():
        raise FileNotFoundError(f"Falta bootstrap.sh en {bootstrap_sh}")
    files_to_pack.append((bootstrap_sh, "arma3-sqf-skill/scripts/bootstrap.sh"))

    # Ordenamiento alfabético determinista
    files_to_pack.sort(key=lambda x: x[1])

    dest_path.parent.mkdir(parents=True, exist_ok=True)
    if dest_path.exists():
        dest_path.unlink()

    with zipfile.ZipFile(dest_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for src, arc in files_to_pack:
            data = src.read_bytes()
            if not arc.endswith(".png"):
                # Normalización estricta a LF
                text = data.decode("utf-8")
                text = text.replace("\r\n", "\n").replace("\r", "\n")
                data = text.encode("utf-8")
            zinfo = zipfile.ZipInfo(arc, date_time=(2026, 11, 23, 14, 0, 0))
            zinfo.compress_type = zipfile.ZIP_DEFLATED
            if arc.endswith(".sh"):
                zinfo.external_attr = 0o755 << 16
            else:
                zinfo.external_attr = 0o644 << 16
            zf.writestr(zinfo, data)

    # Verificación
    packed_names: list[str] = []
    with zipfile.ZipFile(dest_path, "r") as zf:
        corrupted = zf.testzip()
        if corrupted is not None:
            raise RuntimeError(f"Archivo corrupto en ZIP: {corrupted}")

        for info in zf.infolist():
            name = info.filename
            packed_names.append(name)
            if not name.startswith("arma3-sqf-skill/"):
                raise ValueError(f"Directorio raíz inválido: {name}")

            for forb in FORBIDDEN_PATTERNS:
                if forb in name:
                    raise ValueError(f"Patrón prohibido '{forb}' detectado en: {name}")

            if not name.endswith(".png"):
                raw = zf.read(name)
                if b"\r" in raw:
                    raise ValueError(f"CR o CRLF detectado en archivo interno: {name}")

    size_bytes = dest_path.stat().st_size
    max_bytes = 150 * 1024
    if size_bytes >= max_bytes:
        raise ValueError(f"El ZIP excede 150 KB ({size_bytes} >= {max_bytes} bytes)")

    return size_bytes, packed_names


def main() -> int:
    try:
        size_bytes, names = build_package()
        print(f"Paquete creado exitosamente: {OUTPUT_ZIP}")
        print(f"Archivos empaquetados: {len(names)}")
        print(f"Peso total: {size_bytes} bytes ({size_bytes / 1024:.2f} KB) - estricto < 150 KB [OK]")
        return 0
    except Exception as exc:
        print(f"Error empaquetando skill: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
