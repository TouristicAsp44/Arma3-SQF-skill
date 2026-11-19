"""Tests de validación estructural del dataset de Goldens (PR-5, Tarea 5.b)."""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GOLDENS_DIR = REPO_ROOT / "evals" / "goldens"

VALID_SEVERITIES = {"BLOQUEANTE", "SUGERENCIA"}
VALID_VERIFIABLE_TARGETS = {"archivo", "pegado"}


def _load_goldens() -> list[tuple[Path, dict]]:
    assert GOLDENS_DIR.is_dir(), f"No existe el directorio de goldens: {GOLDENS_DIR}"
    goldens = []
    for d in sorted(GOLDENS_DIR.iterdir()):
        if not d.is_dir():
            continue
        expected_file = d / "expected.json"
        code_file = d / "code.sqf"
        assert expected_file.is_file(), f"Golden {d.name} carece de expected.json"
        assert code_file.is_file(), f"Golden {d.name} carece de code.sqf"
        data = json.loads(expected_file.read_text(encoding="utf-8"))
        goldens.append((d, data))
    return goldens


def test_goldens_dataset_size_and_diversity() -> None:
    """Verifica que el dataset contiene >= 10 snippets, >= 3 limpios y >= 2 solo sugerencias."""
    goldens = _load_goldens()
    assert len(goldens) >= 10, f"Se requieren al menos 10 goldens, encontrados: {len(goldens)}"

    clean_count = 0
    suggestions_only_count = 0
    categories_covered: set[int] = set()

    for path, data in goldens:
        bloqueantes = data.get("bloqueantes_esperados", 0)
        sugerencias = data.get("sugerencias_esperadas", 0)
        hallazgos = data.get("hallazgos", [])

        if bloqueantes == 0 and sugerencias == 0:
            clean_count += 1
            assert len(hallazgos) == 0, f"Golden limpio {path.name} declara hallazgos"
        elif bloqueantes == 0 and sugerencias > 0:
            suggestions_only_count += 1
            assert len(hallazgos) > 0, f"Golden de sugerencias {path.name} no declara hallazgos"
            for h in hallazgos:
                assert h["severidad"] == "SUGERENCIA", f"{path.name} tiene severidad no sugerencia en solo-sugerencias"

        for h in hallazgos:
            cat = h.get("categoria")
            if cat is not None and 1 <= cat <= 7:
                categories_covered.add(cat)

    assert clean_count >= 3, f"Se requieren >= 3 snippets limpios, encontrados: {clean_count}"
    assert suggestions_only_count >= 2, f"Se requieren >= 2 snippets con solo sugerencias, encontrados: {suggestions_only_count}"

    for expected_cat in range(1, 8):
        assert expected_cat in categories_covered, f"La categoría normativa {expected_cat} no está cubierta en el dataset de goldens"


def test_goldens_schema_and_verifiable_en() -> None:
    """Cada hallazgo esperado declara severidad válida y verificable_en con valores permitidos."""
    goldens = _load_goldens()

    for path, data in goldens:
        assert "golden_id" in data, f"{path.name} no declara golden_id"
        assert "descripcion" in data, f"{path.name} no declara descripcion"
        assert "categoria_principal" in data, f"{path.name} no declara categoria_principal"
        assert "bloqueantes_esperados" in data, f"{path.name} no declara bloqueantes_esperados"
        assert "sugerencias_esperadas" in data, f"{path.name} no declara sugerencias_esperadas"

        hallazgos = data.get("hallazgos", [])
        for idx, h in enumerate(hallazgos):
            assert "categoria" in h, f"{path.name} hallazgo #{idx} sin categoria"
            assert 1 <= h["categoria"] <= 7, f"{path.name} hallazgo #{idx} con categoria fuera de rango 1..7"
            assert "archivo" in h, f"{path.name} hallazgo #{idx} sin archivo"
            assert "linea" in h and isinstance(h["linea"], int), f"{path.name} hallazgo #{idx} sin linea entera"
            assert h.get("severidad") in VALID_SEVERITIES, f"{path.name} hallazgo #{idx} severidad inválida"
            assert "verificable_en" in h and isinstance(h["verificable_en"], list), (
                f"{path.name} hallazgo #{idx} sin verificable_en como lista"
            )
            assert len(h["verificable_en"]) > 0, f"{path.name} hallazgo #{idx} verificable_en vacío"
            for target in h["verificable_en"]:
                assert target in VALID_VERIFIABLE_TARGETS, (
                    f"{path.name} hallazgo #{idx} tiene destino inválido en verificable_en: {target}"
                )


REVEALING_ROOTS = [
    "waituntil",
    "private",
    "scope",
    "whitelist",
    "player",
    "sleep",
    "uisleep",
    "unscheduled",
    "remoteexec",
    "contrato",
    "inyeccion",
    "inyección",
    "bloqueante",
    "defecto",
]


def test_unsignaled_goldens_contain_no_revealing_comments() -> None:
    """A.2: Los goldens no señalizados (b*) no deben contener comentarios que revelen el defecto."""
    b_goldens = [d for d in sorted(GOLDENS_DIR.iterdir()) if d.is_dir() and d.name.startswith("b")]
    assert len(b_goldens) == 6, f"Se esperaban 6 goldens b*, encontrados: {len(b_goldens)}"

    for b_dir in b_goldens:
        code_text = (b_dir / "code.sqf").read_text(encoding="utf-8")
        clean_code = re.sub(r"/\*.*?[Pp]erfil.*?\*/", "", code_text, flags=re.DOTALL)
        comments = re.findall(r"//.*?$|/\*.*?\*/", clean_code, flags=re.MULTILINE | re.DOTALL)

        for c in comments:
            c_lower = c.lower()
            for root in REVEALING_ROOTS:
                assert root not in c_lower, (
                    f"Golden no señalizado {b_dir.name} contiene comentario con raíz reveladora '{root}': {c.strip()}"
                )

