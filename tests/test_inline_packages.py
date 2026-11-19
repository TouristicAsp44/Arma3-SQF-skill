"""Tests para los paquetes inline P1–P4 de hosts degradados (R3, R6)."""

from __future__ import annotations

import hashlib
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
INLINE_PATHS = [
    REPO_ROOT / "integrations" / "chatgpt" / "custom_gpt_instructions.md",
    REPO_ROOT / "integrations" / "gemini" / "system_instruction.md",
    REPO_ROOT / "integrations" / "claude" / "claude_desktop_paste.md",
]

CORE_RE = re.compile(
    r"<!--\s*CORE-P1-P4\s*-->(?P<core>.*?)<!--\s*/CORE-P1-P4\s*-->", re.DOTALL
)


def _sha256(text: str) -> str:
    return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()


def test_inline_packages_exist_and_contain_sections() -> None:
    """Los 3 artefactos inline existen y contienen P1, P2, P3 y P4."""
    for path in INLINE_PATHS:
        assert path.is_file(), f"Falta el artefacto inline: {path}"
        text = path.read_text(encoding="utf-8")
        assert "P1" in text, f"{path.name} no contiene sección P1"
        assert "P2" in text, f"{path.name} no contiene sección P2"
        assert "P3" in text, f"{path.name} no contiene sección P3"
        assert "P4" in text, f"{path.name} no contiene sección P4"
        assert "REPORT_SCHEMA_VERSION" in text, f"{path.name} no define REPORT_SCHEMA_VERSION"


def test_inline_packages_char_budget() -> None:
    """Los 3 artefactos miden <= 8.000 caracteres (límite estricto ChatGPT)."""
    for path in INLINE_PATHS:
        text = path.read_text(encoding="utf-8")
        length = len(text)
        assert length <= 8000, f"{path.name} supera 8.000 caracteres ({length})"
        assert length > 500, f"{path.name} es sospechosamente corto ({length})"


def test_inline_packages_normative_core_identical() -> None:
    """El núcleo normativo P1–P4 es idéntico entre los 3 artefactos."""
    cores: list[str] = []
    for path in INLINE_PATHS:
        text = path.read_text(encoding="utf-8")
        match = CORE_RE.search(text)
        assert match is not None, f"{path.name} no contiene el delimitador <!-- CORE-P1-P4 -->"
        cores.append(match.group("core").strip())

    core_hashes = [_sha256(c) for c in cores]
    assert len(set(core_hashes)) == 1, (
        f"El núcleo normativo difiere entre artefactos: {core_hashes}"
    )


def test_generator_check_passes() -> None:
    """El comando `scripts/generate_inline_packages.py --check` devuelve exit code 0."""
    proc = subprocess.run(
        [sys.executable, "scripts/generate_inline_packages.py", "--check"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, f"generate_inline_packages.py --check falló:\n{proc.stdout}\n{proc.stderr}"


def test_generator_determinism() -> None:
    """Regenerar dos veces produce exactamente los mismos bytes (sin timestamps)."""
    from scripts.generate_inline_packages import generate_all

    run1 = generate_all()
    run2 = generate_all()
    assert run1 == run2, "El generador no es determinista entre dos llamadas"
    for rel_path, content in run1.items():
        assert _sha256(content) == _sha256(run2[rel_path])
