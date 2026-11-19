"""Test de referencias obsoletas en el material distribuible (R3).

Los ficheros que se publican (skill, integraciones, agentes, reglas y
documentacion de usuario) no pueden apuntar al nombre o a las rutas del
plugin original `arma3-sqf-review`, ya renombrado a `arma3-sqf-skill`:
serian enlaces a ficheros inexistentes o affordances con nombre caducado.

La documentacion historica (instrucciones de trabajo, estado del port,
planificacion) puede mencionarlo porque describe la historia del port.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Ficheros que describen la HISTORIA del port y pueden citar el nombre antiguo.
HISTORY_ALLOWED = (
    "docs/INSTRUCCION-ANTIGRAVITY-",
    "docs/ESTADO-PR.md",
    "docs/PARIDAD.md",
    "PLAN-IMPROVEMENTS",
)

# Material que se distribuye al usuario final.
DISTRIBUTED = (
    "skills",
    "integrations",
    "agents",
    "rules",
    "README.md",
    "INSTALL.md",
    "CONTRIBUTING.md",
)

LEGACY_NAME = "arma3-sqf-review"
LEGACY_SKILL_PATH = "skills/arma3-sqf-review"


def _is_history(path: Path) -> bool:
    rel = path.relative_to(REPO_ROOT).as_posix()
    return any(rel.startswith(prefix) or prefix in rel for prefix in HISTORY_ALLOWED)


def _distributed_files() -> list[Path]:
    found: list[Path] = []
    for entry in DISTRIBUTED:
        target = REPO_ROOT / entry
        if target.is_file():
            found.append(target)
        elif target.is_dir():
            found.extend(p for p in target.rglob("*") if p.is_file() and p.suffix in (".md", ".py", ".json", ".txt"))
    return found


def test_no_legacy_plugin_name_in_code_or_config() -> None:
    """En codigo y configuracion distribuidos no puede quedar el nombre del plugin original.

    En prosa Markdown el nombre antiguo si puede aparecer (por ejemplo, al
    explicar que la skill procede del plugin original); lo que no puede
    reaparecer es una ruta o una orden que apunte al nombre caducado.
    """
    offenders: list[str] = []
    for path in _distributed_files():
        if _is_history(path) or path.suffix == ".md":
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if LEGACY_NAME in text:
            offenders.append(path.relative_to(REPO_ROOT).as_posix())
    assert not offenders, (
        "Nombre del plugin original en codigo/configuracion distribuida: "
        + ", ".join(sorted(offenders))
    )


def test_no_stale_command_with_legacy_name_in_markdown() -> None:
    """Los comandos de la documentacion no pueden pedir clonar/ir al nombre antiguo."""
    offenders: list[str] = []
    for path in _distributed_files():
        if _is_history(path) or path.suffix != ".md":
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for marker in (f"cd {LEGACY_NAME}", f"/{LEGACY_NAME}.git"):
            if marker in text:
                offenders.append(f"{path.relative_to(REPO_ROOT).as_posix()} -> '{marker}'")
    assert not offenders, "Comandos obsoletos en la documentacion: " + "; ".join(offenders)


def test_no_legacy_skill_path_in_distributed_files() -> None:
    """Ninguna ruta `skills/arma3-sqf-review/...` puede quedar viva (enlaces rotos)."""
    offenders: list[str] = []
    for path in _distributed_files():
        if _is_history(path):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if LEGACY_SKILL_PATH in text:
            rel = path.relative_to(REPO_ROOT).as_posix()
            offenders.append(rel)
    assert not offenders, (
        "Rutas al directorio renombrado en material distribuible (enlaces rotos): "
        + ", ".join(sorted(offenders))
    )


def test_legacy_skill_path_does_not_exist_in_repo() -> None:
    """El directorio renombrado no debe existir: si vuelve a aparecer, el port esta mezclado."""
    assert not (REPO_ROOT / "skills" / "arma3-sqf-review").exists()
