"""Tests de paridad de port de agentes (Track B / PR-7).

Verifica de forma ejecutable que los 11 agentes del plugin original
tienen paridad completa y verificada con artefactos portables en la skill.
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
AGENTS_DIR = REPO_ROOT / "agents"
PARIDAD_MD = REPO_ROOT / "docs" / "PARIDAD.md"
SKILL_MD = REPO_ROOT / "skills" / "arma3-sqf-skill" / "SKILL.md"


def get_agent_names() -> list[str]:
    """Devuelve los nombres base de los 11 agentes en agents/."""
    assert AGENTS_DIR.is_dir(), f"No existe el directorio {AGENTS_DIR}"
    agent_files = sorted([p.stem for p in AGENTS_DIR.glob("*.md") if p.name != "README.md"])
    assert len(agent_files) == 11, f"Se esperaban 11 agentes en {AGENTS_DIR}, encontrados {len(agent_files)}"
    return agent_files


def parse_paridad_agents_table() -> dict[str, dict]:
    """Parsea la tabla de la sección A de docs/PARIDAD.md."""
    text = PARIDAD_MD.read_text(encoding="utf-8")
    section_match = re.search(r"## A\. Agentes.*?\n(\|.*?)(?=\n## |\Z)", text, re.S)
    assert section_match, "No se encontró la sección '## A. Agentes' en docs/PARIDAD.md"

    lines = [line.strip() for line in section_match.group(1).splitlines() if line.strip().startswith("|")]
    assert len(lines) >= 3, "Tabla de agentes vacía en docs/PARIDAD.md"

    table = {}
    for row_str in lines[2:]:  # saltar header y separador
        cols = [c.strip() for c in row_str.split("|")[1:-1]]
        if len(cols) < 5:
            continue
        agent_raw = cols[1].strip("` ")
        artifact_raw = cols[2].strip()
        kind_raw = cols[3].strip()
        status_raw = cols[4].strip("` ")
        note_raw = cols[5].strip() if len(cols) > 5 else ""

        table[agent_raw] = {
            "artifact": artifact_raw,
            "kind": kind_raw,
            "status": status_raw,
            "note": note_raw,
        }

    return table


def test_all_11_agents_present_in_paridad_table():
    """Cada agente en agents/ debe tener una fila en docs/PARIDAD.md."""
    agents = get_agent_names()
    table = parse_paridad_agents_table()

    for ag in agents:
        assert ag in table, f"El agente '{ag}' no figura en docs/PARIDAD.md sección A"


def test_each_agent_artifact_exists_on_disk():
    """Cada artefacto referenciado en la tabla de agentes debe existir en disco."""
    table = parse_paridad_agents_table()

    for ag, entry in table.items():
        art = entry["artifact"]
        assert art, f"El agente '{ag}' no declara artefacto equivalente"
        assert "NO CUBIERTA" not in entry["status"], f"El agente '{ag}' tiene estado NO CUBIERTA"

        # Extraer rutas relativas de código o markdown: p. ej. `references/lenses/locality.md`
        paths = re.findall(r"[\w/\.-]+\.(?:md|py)", art)
        assert paths, f"No se extrajo ninguna ruta de archivo para '{ag}': '{art}'"

        for p in paths:
            candidate = REPO_ROOT / p
            if not candidate.exists():
                candidate = REPO_ROOT / "skills" / "arma3-sqf-skill" / p
            assert candidate.is_file(), f"Para agente '{ag}', el archivo '{p}' no existe en disco ({candidate})"


def test_agents_parity_status_verified():
    """Ningún agente debe quedar en estado genérico no respaldado ni NO VERIFICADO."""
    table = parse_paridad_agents_table()

    for ag, entry in table.items():
        status = entry["status"]
        assert status in (
            "PORTADO Y VERIFICADO",
            "PORTADO PARCIAL",
        ), f"El agente '{ag}' tiene estado '{status}'. Debe ser 'PORTADO Y VERIFICADO' o 'PORTADO PARCIAL'"

        if status == "PORTADO PARCIAL":
            assert entry["note"], f"El agente '{ag}' es PORTADO PARCIAL pero no especifica la limitación en la nota"


def test_portable_lenses_and_workflows_referenced_in_skill_md():
    """Cada lente y workflow debe estar referenciado en SKILL.md para activación bajo demanda."""
    skill_text = SKILL_MD.read_text(encoding="utf-8")
    table = parse_paridad_agents_table()

    for ag, entry in table.items():
        paths = re.findall(r"references/(?:lens-[\w-]+|workflows/[\w-]+)\.md", entry["artifact"])
        for p in paths:
            basename = Path(p).name
            assert basename in skill_text, f"El artefacto portable '{p}' (agente '{ag}') no está referenciado en SKILL.md"


def test_agents_readme_exists_and_documents_scope():
    """agents/README.md debe existir y documentar que no es portable y el canónico manda."""
    readme = AGENTS_DIR / "README.md"
    assert readme.is_file(), "agents/README.md no existe para documentar el alcance de agents/"
    content = readme.read_text(encoding="utf-8")
    assert "NO son portables" in content or "no son portables" in content.lower(), "agents/README.md debe advertir sobre no portabilidad"
    assert "invariants.md" in content or "canónico" in content.lower(), "agents/README.md debe citar la precedencia del canónico"
