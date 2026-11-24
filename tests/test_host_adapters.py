"""Tests para adaptadores de host y matriz de compatibilidad (PR-4, R3, R4)."""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
INTEGRATIONS_DIR = REPO_ROOT / "integrations"
COMPATIBILITY_DOC = REPO_ROOT / "docs" / "COMPATIBILIDAD.md"

HOSTS = ["claude", "cursor", "openai", "chatgpt", "gemini"]

# Enlaces markdown del tipo [texto](destino)
MD_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def test_each_host_has_artifacts_and_install_guide() -> None:
    """Cada host soportado cuenta con sus artefactos requeridos y su install.md."""
    # Claude
    assert (INTEGRATIONS_DIR / "claude" / "CLAUDE.md").is_file()
    assert (INTEGRATIONS_DIR / "claude" / "claude_desktop_config_snippet.json").is_file()
    assert (INTEGRATIONS_DIR / "claude" / "claude_desktop_paste.md").is_file()
    assert (INTEGRATIONS_DIR / "claude" / "install.md").is_file()

    # Cursor
    assert (INTEGRATIONS_DIR / "cursor" / ".cursorrules").is_file()
    assert (INTEGRATIONS_DIR / "cursor" / "install.md").is_file()

    # OpenAI / Codex
    assert (INTEGRATIONS_DIR / "openai" / "AGENTS.md").is_file()
    assert (INTEGRATIONS_DIR / "openai" / "install.md").is_file()

    # ChatGPT
    assert (INTEGRATIONS_DIR / "chatgpt" / "custom_gpt_instructions.md").is_file()
    assert (INTEGRATIONS_DIR / "chatgpt" / "knowledge_manifest.md").is_file()
    assert (INTEGRATIONS_DIR / "chatgpt" / "install.md").is_file()

    # Gemini
    assert (INTEGRATIONS_DIR / "gemini" / "system_instruction.md").is_file()
    assert (INTEGRATIONS_DIR / "gemini" / "install.md").is_file()

    # Common
    assert (INTEGRATIONS_DIR / "common" / "skill-layout.md").is_file()


def test_rule_r3_degraded_hosts_have_no_broken_local_file_links() -> None:
    """Regla R3: Los artefactos de hosts degradados no enlazan a ficheros locales inaccesibles."""
    degraded_artifacts = [
        INTEGRATIONS_DIR / "chatgpt" / "custom_gpt_instructions.md",
        INTEGRATIONS_DIR / "gemini" / "system_instruction.md",
        INTEGRATIONS_DIR / "claude" / "claude_desktop_paste.md",
    ]

    for artifact in degraded_artifacts:
        assert artifact.is_file(), f"Falta el artefacto degradado: {artifact}"
        text = artifact.read_text(encoding="utf-8")

        # Prohibido usar enlaces file://
        assert "file://" not in text, f"{artifact.name} contiene enlaces file://"

        # Ningún enlace markdown relativo a rutas del repositorio
        for label, target in MD_LINK_RE.findall(text):
            target_clean = target.strip().split("#")[0]
            if target_clean.startswith(("http://", "https://", "mailto:")):
                continue
            # Si apunta a un fichero relativo en el repo, el host degradado no lo puede leer
            raise AssertionError(
                f"{artifact.name} viola la Regla R3: contiene enlace markdown a fichero local inaccesible: [{label}]({target})"
            )


def test_claude_desktop_config_snippet() -> None:
    """El snippet de Claude Desktop es JSON válido, con campos command, args, cwd y env, sin pseudocódigo."""
    snippet_path = INTEGRATIONS_DIR / "claude" / "claude_desktop_config_snippet.json"
    assert snippet_path.is_file(), "Falta claude_desktop_config_snippet.json"

    raw_text = snippet_path.read_text(encoding="utf-8")
    assert "/ruta/a/" not in raw_text, "El snippet contiene pseudocódigo '/ruta/a/'"
    assert "<tu_" not in raw_text and "<ruta" not in raw_text, "El snippet contiene marcadores '<...>' de pseudocódigo"

    data = json.loads(raw_text)
    servers = data.get("mcpServers", {})
    assert servers, "No se encontraron servidores en 'mcpServers'"

    for name, srv in servers.items():
        assert "command" in srv, f"Servidor {name} no contiene 'command'"
        assert "args" in srv and isinstance(srv["args"], list), f"Servidor {name} no contiene 'args' como lista"
        assert "cwd" in srv, f"Servidor {name} no contiene 'cwd'"
        assert "env" in srv and isinstance(srv["env"], dict), f"Servidor {name} no contiene 'env' como dict"
        assert "SQF_WIKI_DATA_PATH" in srv["env"], f"Servidor {name} no define SQF_WIKI_DATA_PATH"
        assert "SQF_WIKI_DB_PATH" in srv["env"], f"Servidor {name} no define SQF_WIKI_DB_PATH"


def test_claude_desktop_snippet_contract_with_cli() -> None:
    """B.4: El snippet de Claude Desktop respeta el contrato con el CLI real y el reader de wiki."""
    snippet_path = INTEGRATIONS_DIR / "claude" / "claude_desktop_config_snippet.json"
    data = json.loads(snippet_path.read_text(encoding="utf-8"))
    servers = data.get("mcpServers", {})

    orch_path = REPO_ROOT / "skills" / "arma3-sqf-skill" / "scripts" / "sqf_orchestrator.py"
    assert orch_path.is_file(), "No se encontró sqf_orchestrator.py"
    orch_code = orch_path.read_text(encoding="utf-8")

    for name, srv in servers.items():
        args = srv.get("args", [])
        assert args, f"Servidor {name} no contiene argumentos"

        # 1. El script invocado existe en el repositorio
        script_rel = args[0]
        script_file = REPO_ROOT / script_rel
        assert script_file.is_file(), f"El script {script_rel} apuntado por {name} no existe"

        # 2. Cada flag en args existe en el parser del orquestador (CLI pura con --mode-query o --lint)
        flags = [a for a in args[1:] if a.startswith("--")]
        assert any(f in ("--mode-query", "--lint") for f in flags), (
            f"Se esperaba flag CLI puro (--mode-query o --lint) en args de {name}"
        )
        for flag in flags:
            assert f'"{flag}"' in orch_code or f"'{flag}'" in orch_code, (
                f"El flag {flag} de {name} no existe en argparse de {script_rel}"
            )

        # 3. Command es python/python3 válido
        cmd = srv.get("command", "")
        assert cmd in ("python", "python3"), f"Comando inesperado en {name}: {cmd}"

        # 4. SQF_WIKI_DATA_PATH apunta a un directorio de datos y no a un fichero .md
        env = srv.get("env", {})
        data_path = env.get("SQF_WIKI_DATA_PATH", "")
        assert not data_path.endswith(".md"), (
            f"{name}: SQF_WIKI_DATA_PATH no debe apuntar a un archivo markdown ({data_path})"
        )
        assert "data" in data_path or data_path.startswith("~"), (
            f"{name}: SQF_WIKI_DATA_PATH debe apuntar a un directorio de datos ({data_path})"
        )



def test_chatgpt_knowledge_manifest() -> None:
    """knowledge_manifest.md declara <= 20 archivos, criterio explícito y excluye wiki-cache.md completo."""
    manifest_path = INTEGRATIONS_DIR / "chatgpt" / "knowledge_manifest.md"
    assert manifest_path.is_file(), "Falta knowledge_manifest.md"

    text = manifest_path.read_text(encoding="utf-8")
    assert "20" in text, "No menciona el límite de 20 archivos de ChatGPT"
    assert "criterio de selección" in text.lower(), "No incluye sección explícita de criterio de selección"
    assert "wiki-cache.md" in text, "No menciona la justificación sobre wiki-cache.md"
    assert "exclu" in text.lower(), "No contiene exclusiones justificadas"

    # Verificar que el número de archivos incluidos en la tabla es <= 20
    # Cada fila de inventario tiene formato `| N.º | `
    rows = [ln for ln in text.splitlines() if re.match(r"^\|\s*\d+\s*\|", ln)]
    assert 0 < len(rows) <= 20, f"El manifiesto declara {len(rows)} archivos (debe ser <= 20)"


def test_compatibility_matrix_covers_all_hosts_and_columns() -> None:
    """docs/COMPATIBILIDAD.md cubre los 6 hosts con todas las columnas y fallback de modo."""
    assert COMPATIBILITY_DOC.is_file(), "Falta docs/COMPATIBILIDAD.md"
    text = COMPATIBILITY_DOC.read_text(encoding="utf-8")

    # Columnas requeridas
    required_cols = [
        "Host",
        "Mecanismo",
        "Lectura de archivos",
        "Soporte",
        "Qué se pierde",
        "Límite",
        "Compensación",
        "Fallback de modo",
    ]
    for col in required_cols:
        assert col in text, f"Falta la columna {col} en COMPATIBILIDAD.md"

    # 6 hosts
    expected_hosts = [
        "Claude Code",
        "Claude Desktop",
        "Cursor",
        "OpenAI",
        "ChatGPT Custom GPT",
        "Gemini",
    ]
    for host in expected_hosts:
        assert host in text, f"Falta el host {host} en COMPATIBILIDAD.md"

    # Fallback de modo y prohibición de Micro manual
    assert "Estándar" in text and "NO VERIFICADO" in text, "No declara fallback 'Estándar + NO VERIFICADO'"
    assert "Micro" in text and "prohibid" in text.lower(), "No declara la prohibición de conceder Micro manualmente"
