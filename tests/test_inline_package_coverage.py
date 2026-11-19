"""Tests de cobertura estática del paquete inline P1–P4 (R2, R3)."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TARGETS = [
    REPO_ROOT / "integrations" / "chatgpt" / "custom_gpt_instructions.md",
    REPO_ROOT / "integrations" / "gemini" / "system_instruction.md",
    REPO_ROOT / "integrations" / "claude" / "claude_desktop_paste.md",
]


def test_inline_packages_have_full_normative_coverage() -> None:
    """Verifica que el paquete inline contiene las 7 categorías, puerta, honestidad y fallback."""
    for path in TARGETS:
        assert path.is_file(), f"Falta el artefacto inline: {path}"
        text = path.read_text(encoding="utf-8")

        # 1. Las 7 categorías normativas
        assert "1. **Sintaxis y Scope**" in text or "Sintaxis" in text
        assert "2. **Softlocks" in text or "Softlock" in text
        assert "3. **Servidor Dedicado" in text or "Dedicado" in text
        assert "4. **Suspensión Unscheduled**" in text or "Unscheduled" in text
        assert "5. **Whitelist CfgRemoteExec**" in text or "CfgRemoteExec" in text
        assert "6. **Contratos de Interfaz**" in text or "Contratos" in text
        assert "7. **Dependencias de Framework**" in text or "Framework" in text

        # 2. Puerta de Calidad Infranqueable
        assert "Puerta de Calidad" in text
        assert "Cero bloqueantes" in text or "cero bloqueantes" in text
        assert "3 iteraciones" in text

        # 3. Principio de Honestidad Técnica
        assert "Honestidad Técnica" in text
        assert "NO VERIFICADO" in text

        # 4. Fallback de modo y prohibición de Micro manual
        assert "Fallback de modo" in text
        assert "Estándar" in text
        assert "Micro" in text and "prohibid" in text.lower()

        # 5. Formato de informe
        assert "REPORT_SCHEMA_VERSION = 1" in text
        assert "RESUMEN: bloqueantes=" in text
