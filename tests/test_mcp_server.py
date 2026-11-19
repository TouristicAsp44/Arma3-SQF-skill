"""Pruebas exhaustivas para el servidor MCP local sobre transporte stdio (PR-6, C.1).

Cubre:
1. Handshake completo (initialize -> notifications/initialized -> tools/list con 3 herramientas).
2. tools/call con sqf_analyze y conformidad estricta con el esquema v1.
3. Paridad byte a byte entre el informe emitido por MCP y el motor determinista.
4. Resiliencia ante mensaje JSON malformado (error -32700) sin caída del servidor.
5. Error ante método desconocido (-32601).
6. Ausencia total de logs en stdout (todo stdout es JSON-RPC válido).
7. Degradación honesta de sqf_wiki_query ante ausencia de wiki o símbolo inexistente (NO VERIFICADO).
8. Cero persistencia del código del usuario tras la ejecución de sqf_analyze.
9. Ausencia de sockets y llamadas de red en el módulo mcp_server.py.
10. Ejecución real por subproceso stdio a través del flag --serve-mcp de sqf_orchestrator.py.
"""

from __future__ import annotations

import io
import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_DIR = REPO_ROOT / "skills" / "arma3-sqf-skill" / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from mcp_server import (
    METHOD_NOT_FOUND,
    PARSE_ERROR,
    process_jsonrpc_request,
    run_mcp_server_stdio,
)
from sqf_orchestrator import run_lint

MCP_SERVER_PATH = SCRIPT_DIR / "mcp_server.py"
ORCHESTRATOR_PATH = SCRIPT_DIR / "sqf_orchestrator.py"


def test_no_network_libraries_in_mcp_server() -> None:
    """Verifica que mcp_server.py no importa módulos de red ni abre sockets (Privacidad por Construcción)."""
    code = MCP_SERVER_PATH.read_text(encoding="utf-8")
    forbidden = ["socket", "http.server", "urllib.request", "requests", "fastapi", "uvicorn", "aiohttp"]
    for mod in forbidden:
        assert f"import {mod}" not in code, f"mcp_server.py no debe importar '{mod}'"
        assert f"from {mod}" not in code, f"mcp_server.py no debe importar desde '{mod}'"


def test_mcp_handshake_and_tools_list() -> None:
    """Handshake MCP: initialize -> notifications/initialized -> tools/list devolviendo 3 herramientas."""
    # 1. initialize
    init_req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0"},
        },
    }
    init_res = process_jsonrpc_request(init_req)
    assert init_res is not None
    assert init_res["jsonrpc"] == "2.0"
    assert init_res["id"] == 1
    assert "protocolVersion" in init_res["result"]
    assert "tools" in init_res["result"]["capabilities"]
    assert init_res["result"]["serverInfo"]["name"] == "arma3-sqf-skill-mcp"

    # 2. notification/initialized (no debe producir respuesta)
    notif_req = {
        "jsonrpc": "2.0",
        "method": "notifications/initialized",
    }
    notif_res = process_jsonrpc_request(notif_req)
    assert notif_res is None

    # 3. tools/list
    list_req = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
    }
    list_res = process_jsonrpc_request(list_req)
    assert list_res is not None
    assert list_res["id"] == 2
    tools = list_res["result"]["tools"]
    tool_names = [t["name"] for t in tools]
    assert "sqf_analyze" in tool_names
    assert "sqf_wiki_query" in tool_names
    assert "sqf_mode" in tool_names

    # Cada herramienta debe declarar su inputSchema
    for t in tools:
        assert "inputSchema" in t
        assert t["inputSchema"]["type"] == "object"
        assert "properties" in t["inputSchema"]


def test_sqf_analyze_returns_valid_v1_report() -> None:
    """sqf_analyze devuelve un informe conforme al contrato v1 estricto."""
    sample_code = "private _x = 10;\n_leaked = 20;\n"
    call_req = {
        "jsonrpc": "2.0",
        "id": 10,
        "method": "tools/call",
        "params": {
            "name": "sqf_analyze",
            "arguments": {
                "code": sample_code,
                "file_path": "code.sqf",
            },
        },
    }
    res = process_jsonrpc_request(call_req)
    assert res is not None
    assert res["id"] == 10
    assert not res["result"]["isError"]

    report = res["result"]["report"]
    lines = report.strip().splitlines()
    assert lines[0] == "REPORT_SCHEMA_VERSION: 1"
    assert lines[-1].startswith("RESUMEN: bloqueantes=")
    assert "[BLOQUEANTE]" in report
    assert "code.sqf:2 (Scope)" in report


def test_sqf_analyze_byte_for_byte_parity_with_engine(tmp_path: Path) -> None:
    """Paridad byte a byte: el informe del MCP coincide exactamente con el de sqf_orchestrator."""
    code_text = "private _arr = [1, 2, 3];\n_leaked = 99;\n"
    test_sqf = tmp_path / "test_parity.sqf"
    test_sqf.write_text(code_text, encoding="utf-8")

    # Ejecutar orchestrator capturando stdout
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    try:
        run_lint(target=str(test_sqf))
        engine_output = sys.stdout.getvalue()
    finally:
        sys.stdout = old_stdout

    # El motor imprime el informe v1 seguido de la sección item 9. Extraer informe v1
    v1_engine_lines = []
    for line in engine_output.splitlines():
        v1_engine_lines.append(line)
        if line.startswith("RESUMEN: bloqueantes="):
            break
    expected_v1 = "\n".join(v1_engine_lines)

    # Llamada MCP con el mismo archivo y código
    call_req = {
        "jsonrpc": "2.0",
        "id": 20,
        "method": "tools/call",
        "params": {
            "name": "sqf_analyze",
            "arguments": {
                "code": code_text,
                "file_path": str(test_sqf),
            },
        },
    }
    mcp_res = process_jsonrpc_request(call_req)
    assert mcp_res is not None
    mcp_report = mcp_res["result"]["report"]

    assert mcp_report == expected_v1, (
        f"Divergencia entre informe MCP y motor:\nMCP:\n{mcp_report}\n\nMOTOR:\n{expected_v1}"
    )


def test_malformed_json_returns_error_and_server_stays_alive() -> None:
    """Mensaje JSON malformado genera error -32700 y el servidor sigue procesando peticiones posteriores."""
    in_buf = io.StringIO("{malformed json line\n" + json.dumps({"jsonrpc": "2.0", "id": 5, "method": "ping"}) + "\n")
    out_buf = io.StringIO()

    rc = run_mcp_server_stdio(input_stream=in_buf, output_stream=out_buf)
    assert rc == 0

    output_lines = [json.loads(line) for line in out_buf.getvalue().strip().splitlines() if line.strip()]
    assert len(output_lines) == 2

    # Primer mensaje: error de parseo
    assert output_lines[0]["jsonrpc"] == "2.0"
    assert output_lines[0]["id"] is None
    assert output_lines[0]["error"]["code"] == PARSE_ERROR

    # Segundo mensaje: procesado con éxito
    assert output_lines[1]["jsonrpc"] == "2.0"
    assert output_lines[1]["id"] == 5
    assert output_lines[1]["result"] == {}


def test_unknown_method_returns_proper_jsonrpc_error() -> None:
    """Un método desconocido devuelve error JSON-RPC -32601."""
    req = {
        "jsonrpc": "2.0",
        "id": 42,
        "method": "non_existent_method_xyz",
    }
    res = process_jsonrpc_request(req)
    assert res is not None
    assert res["id"] == 42
    assert res["error"]["code"] == METHOD_NOT_FOUND
    assert "Método no encontrado" in res["error"]["message"]


def test_no_logs_to_stdout_during_execution(monkeypatch) -> None:
    """Verifica que ningún log contamina stdout durante la ejecución de llamadas MCP."""
    in_buf = io.StringIO(
        json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": "sqf_mode", "arguments": {"code": "isServer;"}},
        })
        + "\n"
    )
    out_buf = io.StringIO()

    rc = run_mcp_server_stdio(input_stream=in_buf, output_stream=out_buf)
    assert rc == 0

    raw_output = out_buf.getvalue()
    # Cada línea en stdout debe ser un JSON-RPC válido sin texto suelto
    for line in raw_output.strip().splitlines():
        parsed = json.loads(line)
        assert parsed.get("jsonrpc") == "2.0"
        assert parsed.get("id") == 1


def test_sqf_wiki_query_without_wiki_returns_no_verificado(monkeypatch, tmp_path: Path) -> None:
    """Sin réplica wiki o ante símbolo inexistente, sqf_wiki_query responde NO VERIFICADO con motivo."""
    # Redirigir a una ruta de wiki vacía
    fake_empty_dir = tmp_path / "empty_wiki_data"
    fake_empty_dir.mkdir()
    monkeypatch.setenv("SQF_WIKI_DATA_PATH", str(fake_empty_dir))
    monkeypatch.setenv("SQF_WIKI_DB_PATH", str(fake_empty_dir / "nonexistent.db"))

    call_req = {
        "jsonrpc": "2.0",
        "id": 99,
        "method": "tools/call",
        "params": {
            "name": "sqf_wiki_query",
            "arguments": {"query": "nonexistent_symbol_12345"},
        },
    }
    res = process_jsonrpc_request(call_req)
    assert res is not None
    data = json.loads(res["result"]["content"][0]["text"])
    assert data["status"] == "NO_VERIFICADO"
    assert "no encontrado" in data["motivo"] or "no disponible" in data["motivo"]


def test_no_code_persistence_after_sqf_analyze(tmp_path: Path) -> None:
    """Verifica que tras sqf_analyze no queda ningún archivo residual con el código del usuario."""
    sentinel = "SENTINEL_UNIQUE_TOKEN_XYZ_987654"
    code = f"private _val = '{sentinel}';\n"

    call_req = {
        "jsonrpc": "2.0",
        "id": 100,
        "method": "tools/call",
        "params": {
            "name": "sqf_analyze",
            "arguments": {"code": code},
        },
    }
    res = process_jsonrpc_request(call_req)
    assert res is not None

    # Comprobar que ningún archivo en el repositorio contiene el centinela
    for p in REPO_ROOT.glob("**/*"):
        if p.is_file() and p.suffix in (".sqf", ".tmp", ".txt"):
            text = p.read_text(encoding="utf-8", errors="replace")
            assert sentinel not in text, f"El código del usuario persistió en {p}"


def test_subprocess_stdio_via_serve_mcp_flag() -> None:
    """Comprueba el funcionamiento real de sqf_orchestrator.py --serve-mcp por subproceso stdio."""
    cmd = [sys.executable, str(ORCHESTRATOR_PATH), "--serve-mcp"]
    proc = subprocess.Popen(
        cmd,
        cwd=str(REPO_ROOT),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    requests = [
        json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05"}}),
        json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}),
        json.dumps({"jsonrpc": "2.0", "id": 2, "method": "ping"}),
        json.dumps({"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "sqf_mode", "arguments": {"code": "private _x = 1;"}}}),
    ]

    input_payload = "\n".join(requests) + "\n"
    stdout, stderr = proc.communicate(input_payload, timeout=15)
    assert proc.returncode == 0

    lines = [json.loads(line) for line in stdout.strip().splitlines() if line.strip()]
    assert len(lines) == 3  # 1 (init), 2 (ping), 3 (tools/call); notification no genera respuesta

    assert lines[0]["id"] == 1
    assert "capabilities" in lines[0]["result"]

    assert lines[1]["id"] == 2
    assert lines[1]["result"] == {}

    assert lines[2]["id"] == 3
    mode_res = json.loads(lines[2]["result"]["content"][0]["text"])
    assert mode_res["mode"] == "Micro"
    assert mode_res["escalated"] is False


def test_mcp_and_privacy_docs_exist_and_complete() -> None:
    """Verifica que docs/MCP.md y docs/PRIVACIDAD.md existen y contienen las secciones requeridas."""
    mcp_doc = REPO_ROOT / "docs" / "MCP.md"
    priv_doc = REPO_ROOT / "docs" / "PRIVACIDAD.md"

    assert mcp_doc.is_file(), "Falta docs/MCP.md"
    assert priv_doc.is_file(), "Falta docs/PRIVACIDAD.md"

    mcp_text = mcp_doc.read_text(encoding="utf-8")
    assert "--serve-mcp" in mcp_text
    assert "sqf_analyze" in mcp_text
    assert "sqf_wiki_query" in mcp_text
    assert "sqf_mode" in mcp_text
    assert "inputSchema" in mcp_text
    assert "claude_desktop_config.json" in mcp_text

    priv_text = priv_doc.read_text(encoding="utf-8")
    assert "Privacidad por Construcción" in priv_text
    assert "stdio" in priv_text
    assert "persistencia" in priv_text.lower()
    assert "HTTP" in priv_text


def test_stdio_transport_emits_valid_utf8_regardless_of_locale() -> None:
    """El transporte MCP debe emitir UTF-8 válido aunque el locale del sistema sea cp1252.

    MCP exige UTF-8. Sin forzar la codificacion, un Windows estandar (cp1252)
    emite bytes que el cliente MCP no puede decodificar y el protocolo se
    corrompe en silencio. Este test fija esa garantia.
    """
    req = {
        "jsonrpc": "2.0",
        "id": 77,
        "method": "tools/call",
        "params": {"name": "sqf_mode", "arguments": {"code": "player side;"}},
    }
    payload = (json.dumps(req, ensure_ascii=False) + "\n").encode("utf-8")

    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "cp1252"
    proc = subprocess.run(
        [sys.executable, str(ORCHESTRATOR_PATH), "--serve-mcp"],
        cwd=str(REPO_ROOT),
        input=payload,
        capture_output=True,
        env=env,
        timeout=30,
    )
    assert proc.returncode == 0
    assert proc.stdout, "El servidor no emitio ninguna respuesta"

    # Debe decodificar como UTF-8 estricto: si no, el cliente MCP falla.
    decoded = proc.stdout.decode("utf-8")
    first = json.loads(decoded.strip().splitlines()[0])
    text = first["result"]["content"][0]["text"]
    reason = json.loads(text)["reason"]
    assert "señales" in reason, f"Texto no decodificado correctamente en UTF-8: {reason!r}"


def test_wiki_db_path_env_expands_user_home(monkeypatch, tmp_path: Path) -> None:
    """SQF_WIKI_DB_PATH con '~' debe expandirse; si no, la variable se ignora en silencio."""
    from sqf_wiki_reader import resolve_wiki_db

    fake_home = tmp_path / "home"
    (fake_home / ".a3ref").mkdir(parents=True)
    db_file = fake_home / ".a3ref" / "arma3_wiki.db"
    db_file.write_bytes(b"SQLite format 3\x00")

    monkeypatch.setenv("HOME", str(fake_home))
    monkeypatch.setenv("USERPROFILE", str(fake_home))
    monkeypatch.setenv("SQF_WIKI_DB_PATH", "~/.a3ref/arma3_wiki.db")

    resolved = resolve_wiki_db()
    assert resolved is not None, "La variable SQF_WIKI_DB_PATH con '~' fue ignorada en silencio"
    assert resolved == db_file

