"""Test de estructura de la skill portable (Fase 2).

Verifica que el `SKILL.md` nuevo expone las cuatro intenciones del plugin
original (auditar, diseñar, implementar, documentar/planificar) con su ruta
de artefacto, y que la Capa 0 no arrastra las definiciones normativas
completas (N3), que viven solo en el canónico.

En PR-1 el `SKILL.md` sigue siendo el original: el test no es exigible hasta
que PR-2 lo reescriba, y por eso se marca como aplicable desde PR-2.
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_FILE = REPO_ROOT / "skills" / "arma3-sqf-skill" / "SKILL.md"

INTENTS = {
    "AUDITAR": "references/lens-",
    "DISEÑAR": "references/workflows/modes.md",
    "IMPLEMENTAR": "references/workflows/implementation.md",
    "DOCUMENTAR": "references/workflows/documentation.md",
}


def _skill_text() -> str:
    return SKILL_FILE.read_text(encoding="utf-8")


def _is_layered_skill() -> bool:
    """El SKILL.md reescrito en capas (PR-2) es el que declara las intenciones."""
    return "AUDITAR" in _skill_text()


requires_layered_skill = pytest.mark.skipif(
    not SKILL_FILE.is_file() or not _is_layered_skill(),
    reason="El SKILL.md en capas se escribe en PR-2; verificable desde --fase PR-2.",
)


@requires_layered_skill
def test_skill_has_four_intents() -> None:
    """Las 4 intenciones del plugin original son alcanzables desde el prompt."""
    text = _skill_text()
    missing = [name for name in INTENTS if name not in text]
    assert not missing, f"Intenciones ausentes en SKILL.md: {missing}"


@requires_layered_skill
def test_skill_points_to_each_intent_artifact() -> None:
    text = _skill_text()
    missing = [path for path in set(INTENTS.values()) if path not in text]
    assert not missing, f"Rutas de artefacto ausentes en SKILL.md: {missing}"


@requires_layered_skill
def test_skill_references_canonical_and_report_format() -> None:
    text = _skill_text()
    assert "references/invariants.md" in text, "El prompt no apunta al canónico"
    assert "references/report_format.md" in text, "El prompt no apunta al contrato del informe"


@requires_layered_skill
def test_skill_does_not_duplicate_n3_definitions() -> None:
    """La Capa 0 no puede contener definiciones normativas completas."""
    text = _skill_text()
    n3_markers = [
        "variables locales fugadas al scope exterior",
        "condición alcanzable garantizada ni timeout de seguridad",
        "una guarda `if (hasInterface)` NO lo legitima",
    ]
    offenders = [m for m in n3_markers if m in text]
    assert not offenders, (
        "SKILL.md contiene definiciones N3 que pertenecen al canónico: " + "; ".join(offenders)
    )


@requires_layered_skill
def test_skill_tokens_within_budget() -> None:
    """El presupuesto de tokens (frontmatter, Capa 0, turno máx) se respeta."""
    from scripts.measure_tokens import main as measure_main

    assert measure_main() == 0, "Presupuesto de tokens superado"


@requires_layered_skill
def test_skill_references_flat_lenses_and_openai() -> None:
    """Valida que la skill apunta a los lentes planos lens-*.md y openai.yaml."""
    text = _skill_text()
    assert "references/lens-" in text or "lens-*.md" in text
    assert "openai.yaml" in text

    references_dir = REPO_ROOT / "skills" / "arma3-sqf-skill" / "references"
    for lens_name in (
        "lens-architect.md",
        "lens-best-practices.md",
        "lens-claims.md",
        "lens-config.md",
        "lens-locality.md",
        "lens-performance.md",
    ):
        assert (references_dir / lens_name).is_file(), f"Falta el lente plano {lens_name}"
    assert not (references_dir / "lenses").exists(), "references/lenses/ no debe existir"

    scripts_dir = REPO_ROOT / "skills" / "arma3-sqf-skill" / "scripts"
    assert (scripts_dir / "run_sqflint.py").is_file(), "run_sqflint.py debe ubicarse en scripts/"
    assert not (references_dir / "run_sqflint.py").exists(), "run_sqflint.py no debe estar en references/"
    assert (REPO_ROOT / "skills" / "arma3-sqf-skill" / "agents" / "openai.yaml").is_file()

