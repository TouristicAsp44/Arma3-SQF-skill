"""Tests de la clasificación de categorías del arnés (harness).

El clasificador traduce la etiqueta libre de disciplina del informe v1 a una de
las 7 categorías normativas. Antes se hacía por subcadena, lo que producía
falsas omisiones: "interfaces" contiene "ace" (interfACEs) y "arquitectura"
contiene "ui" (arqUIitectura). Un bloqueante de contratos de interfaz se
clasificaba como dependencia ACE3 (Cat. 7) o servidor dedicado (Cat. 3), y el
arnés contaba una omisión que nunca existio: el modelo si habia detectado el
defecto, la etiqueta lexica lo descolocaba.
"""

from __future__ import annotations

import json
from pathlib import Path

from evals.harness import classify_discipline, disciplines_compatible


def test_interfaces_is_category_6_not_ace3() -> None:
    """"interfaces" contiene "ace" como subcadena, pero es un contrato de interfaz (Cat. 6)."""
    assert classify_discipline("Interfaces") == 6
    assert classify_discipline("Interfaces") != 7


def test_arquitectura_interfaces_is_category_6_not_dedicated() -> None:
    """"arquitectura" contiene "ui" como subcadena, pero es Cat. 6, no servidor dedicado."""
    assert classify_discipline("Arquitectura / Interfaces") == 6
    assert classify_discipline("Arquitectura / Interfaces") != 3


def test_ui_alone_is_still_dedicated() -> None:
    """El token suelto "ui" si sigue siendo servidor dedicado (Cat. 3)."""
    assert classify_discipline("UI") == 3
    assert classify_discipline("Player en servidor") == 3


def test_uisleep_is_not_confused_with_ui() -> None:
    """"uiSleep" es contexto unscheduled (Cat. 4), no UI de servidor."""
    assert classify_discipline("uiSleep") == 4
    assert classify_discipline("sleep") == 4


def test_cba_and_ace3_still_category_7() -> None:
    assert classify_discipline("CBA_fnc_hashCreate") == 7
    assert classify_discipline("Dependencias de Framework") == 7
    assert classify_discipline("ACE3") == 7


def test_plurals_and_accents() -> None:
    assert classify_discipline("contratos") == 6
    assert classify_discipline("Parámetros") == 6
    assert classify_discipline("Configuración / CfgRemoteExec") == 5
    assert classify_discipline("Contrato de Interfaz") == 6


def test_unclassifiable_discipline_returns_none() -> None:
    """Una etiqueta que no encaja en ninguna categoría devuelve None (no inventa)."""
    assert classify_discipline("Best-practices") is None
    assert classify_discipline("Calidad") is None
    assert classify_discipline("Documentación") is None


def test_disciplines_compatible_uses_expected_label_as_evidence() -> None:
    """Las etiquetas del modelo y del ground truth se comparan como evidencia."""
    assert disciplines_compatible("Interfaces", "Arquitectura / Interfaces")
    assert not disciplines_compatible("Framework", "Configuración / Red")


def test_blocker_out_of_mode_scope_is_not_a_false_positive(tmp_path: Path) -> None:
    """Un bloqueante de una categoria que el modo NO evalua no es un falso positivo.

    En modo archivo, M2 solo puntua las categorias 3-7. `g01_syntax_scope`
    declara un hallazgo de Cat. 1 (scope) que queda fuera del alcance de M2. Si
    el modelo lo detecta correctamente, ese bloqueante es una deteccion
    acertada: contarlo como falso positivo penalizaria una deteccion correcta.
    """
    from evals.harness import evaluate_external_host

    runs_dir = tmp_path / "runs"
    host_dir = runs_dir / "2026-11-19" / "fp-scope-host"
    host_dir.mkdir(parents=True)

    trace = {
        "golden_id": "g01_syntax_scope",
        "host": "fp-scope-host",
        "modelo": "TestModel",
        "version": "1.0",
        "modo_evaluacion": "archivo",
        "contexto_cargado": [{"archivo": "SKILL.md", "sha256": "abc"}],
        # Bloqueante de Cat. 1 (scope) en la linea 4: fuera del alcance de M2
        # pero declarado en el ground truth -> deteccion correcta, no FP.
        "respuesta_cruda": (
            "REPORT_SCHEMA_VERSION: 1\n"
            "[BLOQUEANTE] code.sqf:4 (Scope): variable global usada sin private\n"
            "RESUMEN: bloqueantes=1; sugerencias=0; no_verificado=0"
        ),
    }
    (host_dir / "g01.json").write_text(json.dumps(trace), encoding="utf-8")

    res = evaluate_external_host("fp-scope-host", "archivo", runs_dir=runs_dir)
    assert res["falsos_positivos"] == 0, (
        "Un bloqueante de categoria fuera del alcance del modo no debe contar como falso positivo"
    )
    assert res["hallazgos_no_declarados"] == []
