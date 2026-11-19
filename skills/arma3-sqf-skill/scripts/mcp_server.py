#!/usr/bin/env python3
"""Servidor MCP (Model Context Protocol) local sobre transporte stdio para arma3-sqf-skill.

Implementación pura con biblioteca estándar (JSON-RPC 2.0 sobre stdin/stdout).
Privacidad por construcción: sin apertura de sockets de red, sin persistencia
de código del usuario en disco y sin telemetría externa.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, TextIO

# Inclusión del directorio contenedor para resolver módulos hermanos
_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from sqf_models import (
    check_escalation_needed,
    determine_escalation_reason,
    format_findings_report,
    parse_sqflint_output,
    summarize_escalation,
)
from sqf_orchestrator import DEFAULT_LINTER, compute_item_9_report
from sqf_wiki_reader import (
    get_command,
    get_data_git_sha,
    get_function,
    resolve_wiki_root,
)

PROTOCOL_VERSION = "2024-11-05"
SERVER_NAME = "arma3-sqf-skill-mcp"
SERVER_VERSION = "1.0.0"

# Códigos de error JSON-RPC 2.0
PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603

# Definición de herramientas MCP
TOOLS_DEFINITIONS: list[dict[str, Any]] = [
    {
        "name": "sqf_analyze",
        "description": (
            "Analiza código SQF de Arma 3 de forma atómica y determinista ejecutando el motor local. "
            "Devuelve un informe estructurado conforme al contrato v1 (REPORT_SCHEMA_VERSION: 1). "
            "Si el código exige un modo de análisis superior, devuelve el informe de triage correspondiente."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Contenido del archivo o fragmento SQF a auditar.",
                },
                "description_ext": {
                    "type": "string",
                    "description": "Contenido opcional de description.ext o CfgRemoteExec para auditoría de red.",
                },
                "project_profile": {
                    "type": "object",
                    "description": "Perfil opcional del proyecto (ARMA_VERSION, DESTINO, CBA, ACE3).",
                },
                "file_path": {
                    "type": "string",
                    "description": "Ruta o nombre virtual de archivo para reportar hallazgos (por defecto 'code.sqf').",
                },
                "mode": {
                    "type": "string",
                    "enum": ["Micro", "Estándar", "Completo"],
                    "description": "Modo explícito de ejecución. Si se omite, se ejecuta triaje automático.",
                },
            },
            "required": ["code"],
        },
    },
    {
        "name": "sqf_wiki_query",
        "description": (
            "Consulta técnica de solo lectura sobre comandos y funciones de Arma 3 contra la réplica local a3ref. "
            "Devuelve la ficha oficial del comando o responde NO VERIFICADO si no está documentado."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Nombre del comando o función SQF a consultar (ej. 'hint', 'remoteExec', 'BIS_fnc_MP').",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "sqf_mode",
        "description": (
            "Realiza el triaje determinista del modo de análisis recomendado (Micro, Estándar, Completo) "
            "según las señales de red, scheduler y ciclo de vida del código SQF."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Código SQF a evaluar.",
                },
                "file_path": {
                    "type": "string",
                    "description": "Ruta o nombre virtual de archivo opcional.",
                },
            },
            "required": ["code"],
        },
    },
]


def log_debug(message: str) -> None:
    """Emite mensajes de diagnóstico exclusivamente a stderr para no contaminar el canal stdio JSON-RPC."""
    print(f"[{SERVER_NAME}] {message}", file=sys.stderr, flush=True)


def force_utf8_stdio() -> None:
    """Fuerza UTF-8 en los streams de stdio (MCP exige UTF-8 en el transporte).

    Sin esto, en un Windows con locale distinto de UTF-8 (cp1252 es el valor
    por defecto de una instalación estándar) el servidor emitiría bytes que no
    son UTF-8 válido y el cliente MCP no podría decodificar la respuesta: el
    protocolo se corrompe en silencio. El error `replace` evita que un byte
    suelto tumbe el servidor.
    """
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, OSError):  # pragma: no cover - streams no reconfigurables
            pass


def handle_sqf_analyze(arguments: dict[str, Any]) -> str:
    """Ejecuta el análisis SQF sobre código en memoria sin persistencia en disco y produce el informe v1."""
    if not isinstance(arguments, dict) or "code" not in arguments:
        raise ValueError("El parámetro 'code' es obligatorio y debe ser una cadena de texto.")

    code = arguments["code"]
    if not isinstance(code, str):
        raise ValueError("El parámetro 'code' debe ser una cadena de texto.")

    description_ext = arguments.get("description_ext")
    file_path = arguments.get("file_path") or "code.sqf"
    requested_mode = arguments.get("mode")

    # 1. Triaje de modo si no se fijó un modo explícito que no sea Micro
    if requested_mode is None or requested_mode == "Micro":
        escalated_mode = check_escalation_needed(code, "Micro")
        if escalated_mode != "Micro":
            reason = determine_escalation_reason([code], escalated_mode)
            return summarize_escalation(escalated_mode, reason)

    # 2. Análisis del código con el motor determinista
    # Se utiliza un directorio temporal que se elimina automáticamente al finalizar (cero persistencia).
    with tempfile.TemporaryDirectory() as td:
        tmp_dir = Path(td)
        target_name = Path(file_path).name or "code.sqf"
        target_file = tmp_dir / target_name
        target_file.write_text(code, encoding="utf-8")

        if description_ext and isinstance(description_ext, str):
            (tmp_dir / "description.ext").write_text(description_ext, encoding="utf-8")

        resolved_linter = (
            os.path.abspath(DEFAULT_LINTER)
            if os.path.exists(DEFAULT_LINTER)
            else DEFAULT_LINTER
        )

        rc = 0
        stdout = ""
        if os.path.exists(resolved_linter):
            env = os.environ.copy()
            env["PYTHONDONTWRITEBYTECODE"] = "1"
            cmd = [sys.executable, "-B", resolved_linter, str(target_file)]
            try:
                proc = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    env=env,
                    timeout=30,
                    check=False,
                )
                rc = proc.returncode
                stdout = proc.stdout
            except subprocess.TimeoutExpired:
                rc = 3
                stdout = "TIMEOUT EXPIRED: El linter superó el tiempo límite."
            except (subprocess.SubprocessError, OSError) as e:
                rc = 3
                stdout = f"SQFLINT_NO_DISPONIBLE: error al invocar linter ({e})"
        else:
            rc = 3
            stdout = "SQFLINT_NO_DISPONIBLE: linter no encontrado"

        findings = parse_sqflint_output(rc, stdout, source_code=code)
        # Normalizar el nombre de archivo en los hallazgos al virtual solicitado
        for f in findings:
            f.file = file_path

        item_9 = compute_item_9_report(
            findings,
            rc,
            stdout,
            source_code=code,
            target=str(target_file),
            file_sources={str(target_file): code},
        )
        item_9_status = "NO_VERIFICADO" if ("| NO VERIFICADO |" in item_9) else "PASA"
        return format_findings_report(findings, item_9_status=item_9_status)


def handle_sqf_wiki_query(arguments: dict[str, Any]) -> str:
    """Consulta técnica contra la réplica de la wiki con degradación honesta si no está disponible."""
    if not isinstance(arguments, dict) or "query" not in arguments:
        raise ValueError("El parámetro 'query' es obligatorio.")

    query = str(arguments["query"]).strip()
    if not query:
        raise ValueError("El parámetro 'query' no puede estar vacío.")

    wiki_root = resolve_wiki_root()
    sha = get_data_git_sha(wiki_root)

    info = get_command(query, wiki_root) or get_function(query, wiki_root)
    if not info:
        res = {
            "status": "NO_VERIFICADO",
            "motivo": f"Símbolo '{query}' no encontrado en réplica a3ref o réplica wiki offline no disponible.",
            "wiki_sha": sha,
        }
    else:
        res = {
            "status": "VERIFICADO",
            "canonical_name": info.get("canonical_name", query),
            "type": info.get("type", "command"),
            "status_entry": info.get("status", "ok"),
            "version": info.get("version"),
            "url": info.get("url"),
            "locality": info.get("locality"),
            "groups": info.get("groups", []),
            "wiki_sha": sha,
            "description": info.get("description", ""),
        }

    return json.dumps(res, indent=2, ensure_ascii=False)


def handle_sqf_mode(arguments: dict[str, Any]) -> str:
    """Triaje determinista del modo de análisis sobre código SQF."""
    if not isinstance(arguments, dict) or "code" not in arguments:
        raise ValueError("El parámetro 'code' es obligatorio.")

    code = str(arguments["code"])
    mode = check_escalation_needed(code, "Micro")
    reason = determine_escalation_reason([code], mode)
    report = summarize_escalation(mode, reason)

    res = {
        "mode": mode,
        "reason": reason,
        "escalated": (mode != "Micro"),
        "report": report,
    }
    return json.dumps(res, indent=2, ensure_ascii=False)


def process_jsonrpc_request(request: dict[str, Any]) -> dict[str, Any] | None:
    """Procesa un mensaje JSON-RPC 2.0 y retorna la respuesta (o None si es notificación)."""
    if not isinstance(request, dict) or request.get("jsonrpc") != "2.0":
        return {
            "jsonrpc": "2.0",
            "id": request.get("id") if isinstance(request, dict) else None,
            "error": {"code": INVALID_REQUEST, "message": "Petición JSON-RPC 2.0 inválida."},
        }

    method = request.get("method")
    req_id = request.get("id")

    # Notificaciones (sin id)
    if req_id is None:
        if method == "notifications/initialized":
            log_debug("Cliente inicializado.")
        return None

    if method == "initialize":
        params = request.get("params") or {}
        client_version = params.get("protocolVersion", PROTOCOL_VERSION)
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": client_version,
                "capabilities": {
                    "tools": {},
                },
                "serverInfo": {
                    "name": SERVER_NAME,
                    "version": SERVER_VERSION,
                },
            },
        }

    if method == "ping":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {},
        }

    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": TOOLS_DEFINITIONS,
            },
        }

    if method == "tools/call":
        params = request.get("params") or {}
        tool_name = params.get("name")
        args = params.get("arguments") or {}

        try:
            if tool_name == "sqf_analyze":
                output_text = handle_sqf_analyze(args)
            elif tool_name == "sqf_wiki_query":
                output_text = handle_sqf_wiki_query(args)
            elif tool_name == "sqf_mode":
                output_text = handle_sqf_mode(args)
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {
                        "code": INVALID_PARAMS,
                        "message": f"Herramienta desconocida: {tool_name}",
                    },
                }

            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [
                        {"type": "text", "text": output_text},
                    ],
                    "report": output_text,
                    "isError": False,
                },
            }
        except ValueError as err:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": INVALID_PARAMS,
                    "message": f"Parámetros inválidos para {tool_name}: {err}",
                },
            }
        except Exception as exc:
            log_debug(f"Error interno en herramienta {tool_name}: {exc}")
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": INTERNAL_ERROR,
                    "message": f"Error interno en ejecución de {tool_name}: {exc}",
                },
            }

    # Método no soportado
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {
            "code": METHOD_NOT_FOUND,
            "message": f"Método no encontrado: {method}",
        },
    }


def run_mcp_server_stdio(
    input_stream: TextIO | None = None,
    output_stream: TextIO | None = None,
) -> int:
    """Bucle principal del servidor MCP sobre stdio procesando mensajes línea a línea."""
    in_s = input_stream or sys.stdin
    out_s = output_stream or sys.stdout

    # El transporte MCP es UTF-8 obligatorio: se fuerza antes de leer o escribir.
    if input_stream is None or output_stream is None:
        force_utf8_stdio()

    log_debug(f"Arrancando {SERVER_NAME} v{SERVER_VERSION} sobre stdio...")

    for line in in_s:
        raw_line = line.strip()
        if not raw_line:
            continue

        try:
            req_data = json.loads(raw_line)
        except Exception as parse_exc:
            log_debug(f"Error de parseo JSON: {parse_exc}")
            err_resp = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": PARSE_ERROR, "message": f"Error de parseo JSON: {parse_exc}"},
            }
            out_s.write(json.dumps(err_resp, ensure_ascii=False) + "\n")
            out_s.flush()
            continue

        resp = process_jsonrpc_request(req_data)
        if resp is not None:
            out_s.write(json.dumps(resp, ensure_ascii=False) + "\n")
            out_s.flush()

    log_debug("Finalizando servidor MCP (EOF en stdin).")
    return 0


if __name__ == "__main__":
    sys.exit(run_mcp_server_stdio())
