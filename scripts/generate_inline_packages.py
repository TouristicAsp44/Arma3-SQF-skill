#!/usr/bin/env python3
"""Generador determinista de paquetes inline P1–P4 para hosts degradados (R3, R6).

Hosts generados:
  - integrations/chatgpt/custom_gpt_instructions.md
  - integrations/gemini/system_instruction.md
  - integrations/claude/claude_desktop_paste.md

Reglas invariables:
  - Límite duro: <= 8.000 caracteres por archivo (límite ChatGPT).
  - Los 3 archivos comparten exactamente el mismo núcleo P1–P4.
  - Sin enlaces a archivos locales que el host no pueda leer (R3).
  - Determinista: mismo canónico -> mismo byte. Sin timestamps.
  - Cabecera: <!-- GENERATED FROM: skills/arma3-sqf-skill/references/invariants.md | DO NOT EDIT -->
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
INVARIANTS_PATH = REPO_ROOT / "skills" / "arma3-sqf-skill" / "references" / "invariants.md"
LOCK_FILE = REPO_ROOT / "scripts" / "generated.lock.json"

MAX_CHARS = 8000

CORE_P1_P4 = """<!-- CORE-P1-P4 -->
## P1 — Núcleo normativo (N1 + Puerta + Honestidad)

### Categorías de BLOQUEANTE (N1)
1. **Sintaxis y Scope**: Errores de sintaxis SQF y variables locales sin private o no recibidas en params que fugan al scope exterior.
2. **Softlocks e Init**: waitUntil sin timeout o sin salida garantizada, bucles infinitos sin cadencia, o sleep/uiSleep/waitUntil en el hilo principal de init.sqf, initServer.sqf o postInit.
3. **Servidor Dedicado (Headless)**: Uso de player en servidor dedicado (donde player es permanentemente objNull), o comandos UI (hint, titleText, dialog, etc.) en rutas del servidor. La guarda if (hasInterface) NO legitima comandos UI en rutas del servidor.
4. **Suspensión Unscheduled**: sleep, uiSleep o waitUntil donde canSuspend == false (preInit, Event Handlers del motor, remoteExecCall).
5. **Whitelist CfgRemoteExec**: Invocaciones remotas (remoteExec, remoteExecCall) de funciones no declaradas en la whitelist de CfgRemoteExec >> Functions cuando mode = 1.
6. **Contratos de Interfaz**: Discrepancias en cantidad, orden o tipos de datos requeridos en params entre módulos o llamadas.
7. **Dependencias de Framework**: Uso de funciones CBA o ACE3 (CBA_fnc_*, ace_*) cuando el perfil del proyecto declara CBA: no o ACE3: no.

### Puerta de Calidad Infranqueable
- Cero bloqueantes para declarar terminado o entregar como final.
- Si tras 3 iteraciones de corrección aún queda al menos un bloqueante abierto:
  1. DETENER el proceso de inmediato.
  2. Informar al usuario con el desglose exacto de cada bloqueante sin resolver (disciplina, archivo, línea, causa raíz).
  3. Marcar como DETENIDO (NO PASA). Prohibido terminantemente declarar terminado o entregar código con bloqueantes.
- Solo se avanza a plan de prueba, documentación y entrega si el número de bloqueantes abiertos es CERO.

### Principio de Honestidad Técnica
- Lo no ejecutado en servidor dedicado o no contrastado con fuentes primarias se reporta obligatoriamente como NO VERIFICADO; nunca se declara completo ni PASA.
- Sin disponibilidad de linter estático determinista o sin réplica de documentación oficial, el análisis se reporta como NO VERIFICADO (jamás PASA).
- Estados formales permitidos por ítem: PASA, NO PASA, NO VERIFICADO (y NO APLICA únicamente si no corresponde al modo). Prohibido emitir PASA de memoria.

## P2 — Fallback de modo
- Ante la ausencia del script determinista de análisis de proyecto o en entornos degradados sin acceso a terminal, el modo por defecto es **Estándar** con estado **NO VERIFICADO**.
- Está terminantemente prohibido conceder o auto-asignar el modo **Micro** por criterio manual.

## P3 — Checklist priorizado de verificación (N2)
1. **Scope y Sintaxis**: ¿Toda variable local está declarada explícitamente con private o recibida por params? ¿La sintaxis SQF es válida?
2. **Softlocks e Inicialización**: ¿Todo waitUntil cuenta con condición de salida alcanzable o timeout? ¿El hilo principal de scripts de inicialización (init.sqf, initServer.sqf, postInit) está libre de retrasos bloqueantes (sleep/uiSleep/waitUntil)?
3. **Servidor Dedicado (Headless)**: ¿Se evita estrictamente player en código del servidor? ¿Están ausentes los comandos UI (hint, hintC, titleText, dialog, etc.) en rutas que corren en el servidor (incluso con if (hasInterface))?
4. **Contexto Scheduled**: ¿Se evita suspender (sleep, uiSleep, waitUntil) dentro de contextos unscheduled (preInit, Event Handlers del motor, remoteExecCall)?
5. **CfgRemoteExec**: ¿Toda función invocada con remoteExec/remoteExecCall está permitida en CfgRemoteExec >> Functions (mode = 1)?
6. **Contratos e Interfaces**: ¿Coinciden cantidad, orden y tipo de parámetros esperados en params entre módulos y llamadas de función?
7. **Dependencias de Framework**: ¿Se evita invocar CBA_fnc_* o ace_* si el perfil del proyecto declara CBA: no o ACE3: no?

## P4 — Formato de informe estructurado
REPORT_SCHEMA_VERSION = 1
Estructura por hallazgo detectado:
[BLOQUEANTE|SUGERENCIA|NO_VERIFICADO] archivo:linea (disciplina): descripcion
Línea final de resumen obligatorio:
RESUMEN: bloqueantes=N; sugerencias=N; no_verificado=N
<!-- /CORE-P1-P4 -->"""

PREAMBLES: dict[str, str] = {
    "integrations/chatgpt/custom_gpt_instructions.md": (
        "# Instrucciones de Sistema — Custom GPT: Revisor Experto SQF Arma 3\n\n"
        "Eres un auditor y desarrollador experto en SQF para Arma 3 en servidor dedicado (headless).\n"
        "Operas en ChatGPT Custom GPT bajo el protocolo de host degradado (sin terminal de comandos local, sin ejecución determinista de linter ni acceso directo a filesystem).\n\n"
        "Tus prioridades absolutas son:\n"
        "1. Servidor dedicado: el servidor no tiene UI y player es objNull.\n"
        "2. Locality y red: estabilidad en multijugador, remoteExec seguro, JIP limpio.\n"
        "3. Evaluación rigurosa: cero bloqueantes para aprobar.\n\n"
        "Los archivos adjuntos en Knowledge proporcionan contexto de referencia complementario. Para cualquier revisión, generación o refactorización de código SQF, debes aplicar estrictamente las reglas normativas inline P1–P4 a continuación.\n"
    ),
    "integrations/gemini/system_instruction.md": (
        "# Instrucción del Sistema — Gemini: Revisor Experto SQF Arma 3\n\n"
        "Eres un especialista en desarrollo y auditoría de código SQF para Arma 3 enfocado en servidor dedicado (headless) y multijugador.\n"
        "Operas en Google Gemini / Google AI Studio bajo el perfil de host degradado (sin herramientas de ejecución local en terminal ni lectura directa de sistema de archivos).\n\n"
        "Tus prioridades técnicas son:\n"
        "1. Servidor dedicado: rutas de servidor sin comandos UI y sin dependencias de player.\n"
        "2. Locality y multijugador: llamadas remotas validadas contra CfgRemoteExec, JIP gestionado.\n"
        "3. Puerta de calidad: cero bloqueantes para aprobar.\n\n"
        "Debes analizar todo código SQF provisto aplicando obligatoriamente el paquete normativo inline P1–P4 a continuación.\n"
    ),
    "integrations/claude/claude_desktop_paste.md": (
        "# Instrucción de Pegado — Claude Desktop: Revisor Experto SQF Arma 3\n\n"
        "Pega este bloque al inicio de tu conversación en Claude Desktop (modo interactivo sin servidor MCP conectado).\n"
        "En este modo, el asistente opera sin acceso directo al sistema de archivos local ni ejecución del linter determinista, por lo que se rige por el protocolo de host degradado y las reglas normativas inline P1–P4.\n\n"
        "Tus prioridades técnicas son:\n"
        "1. Servidor dedicado: código de servidor sin UI y sin player.\n"
        "2. Locality y multijugador: remoteExec controlado, JIP limpio, sin desync.\n"
        "3. Puerta de calidad: cero bloqueantes para entregar.\n\n"
        "Aplica obligatoriamente el siguiente paquete normativo inline P1–P4 a todo código SQF evaluado.\n"
    ),
}


def compute_source_hash() -> str:
    if not INVARIANTS_PATH.is_file():
        raise FileNotFoundError(f"No se encuentra la fuente canónica: {INVARIANTS_PATH}")
    return hashlib.sha256(INVARIANTS_PATH.read_bytes()).hexdigest()


def generate_content(rel_path: str, source_hash: str) -> str:
    preamble = PREAMBLES[rel_path]
    header = (
        "<!-- GENERATED FROM: skills/arma3-sqf-skill/references/invariants.md | DO NOT EDIT -->\n"
        f"<!-- SOURCE-HASH: {source_hash} -->\n\n"
    )
    content = header + preamble + "\n" + CORE_P1_P4 + "\n"
    if len(content) > MAX_CHARS:
        raise ValueError(
            f"El artefacto {rel_path} supera el límite de {MAX_CHARS} caracteres ({len(content)})."
        )
    return content


def generate_all() -> dict[str, str]:
    source_hash = compute_source_hash()
    return {rel_path: generate_content(rel_path, source_hash) for rel_path in PREAMBLES}


def check_inline_packages() -> tuple[bool, list[str]]:
    packages = generate_all()
    errors: list[str] = []
    for rel_path, expected in packages.items():
        file_path = REPO_ROOT / rel_path
        if not file_path.is_file():
            errors.append(f"{rel_path}: el archivo no existe.")
            continue
        actual = file_path.read_text(encoding="utf-8")
        if actual != expected:
            errors.append(f"{rel_path}: el contenido difiere del generado esperado.")
        if len(actual) > MAX_CHARS:
            errors.append(f"{rel_path}: supera el límite de {MAX_CHARS} caracteres ({len(actual)}).")
    return (len(errors) == 0, errors)


def write_inline_packages() -> list[str]:
    packages = generate_all()
    written: list[str] = []
    for rel_path, content in packages.items():
        file_path = REPO_ROOT / rel_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        written.append(rel_path)
    return written


def update_lock() -> None:
    packages = generate_all()
    lock_data: dict = {}
    if LOCK_FILE.is_file():
        lock_data = json.loads(LOCK_FILE.read_text(encoding="utf-8"))
    
    gen_section = lock_data.setdefault("generated", {})
    for rel_path, content in packages.items():
        gen_section[rel_path] = hashlib.sha256(content.strip().encode("utf-8")).hexdigest()
    
    LOCK_FILE.write_text(json.dumps(lock_data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generador de paquetes inline P1–P4 para hosts degradados.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true", help="Verifica si los paquetes están generados y al día.")
    group.add_argument("--write", action="store_true", help="Escribe los paquetes generados en disco.")
    args = parser.parse_args(argv)

    if args.check:
        ok, errors = check_inline_packages()
        if not ok:
            print("FALLO: Los paquetes inline difieren o no existen:")
            for err in errors:
                print(f"  - {err}")
            return 1
        print("OK: Todos los paquetes inline P1–P4 existen y coinciden con la fuente canónica.")
        return 0

    if args.write:
        written = write_inline_packages()
        update_lock()
        print(f"OK: {len(written)} paquete(s) inline escrito(s) y lock actualizado:")
        for w in written:
            char_count = len((REPO_ROOT / w).read_text(encoding="utf-8"))
            print(f"  - {w} ({char_count} caracteres)")
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
