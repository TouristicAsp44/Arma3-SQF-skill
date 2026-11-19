# Servidor Local MCP (Model Context Protocol) — `arma3-sqf-skill`

Este documento describe la arquitectura, instalación, herramientas y protocolos del servidor local MCP (Track B) integrado en `arma3-sqf-skill`.

---

## 1. Arquitectura y Transporte (stdio, stdlib pura)

El servidor MCP de `arma3-sqf-skill` está implementado sobre el estándar **JSON-RPC 2.0** utilizando transporte **stdio** (`sys.stdin` / `sys.stdout`) y exclusivamente la **biblioteca estándar de Python** (>= 3.11).

### Características Principales
- **Zero Dependencies**: No requiere `fastapi`, `uvicorn`, `requests` ni paquetes de terceros (`dependencies = []` en `pyproject.toml`). Funciona directamente en cualquier entorno con Python 3.11+.
- **Privacidad por Construcción**: Todo el procesamiento se realiza en la máquina local. No abre sockets de red, no expone puertos HTTP y no envía código ni telemetría fuera del equipo.
- **Sin Persistencia en Disco**: El análisis de código se realiza en memoria mediante directorios temporales efímeros que se destruyen inmediatamente tras la ejecución.
- **Canal de Diagnóstico Limpio**: La salida estándar (`stdout`) se reserva exclusivamente para tramas JSON-RPC estructuradas delimitadas por salto de línea. Todos los mensajes de log, aviso o diagnóstico se dirigen estrictamente a `stderr`.
- **UTF-8 Obligatorio en el Transporte**: MCP exige UTF-8. El servidor **fuerza UTF-8** en `stdin`/`stdout`/`stderr` al arrancar (`force_utf8_stdio()`), de modo que funciona igual en un Windows con locale `cp1252` (instalación estándar) que en un sistema con UTF-8 activo. Sin esa garantía, el servidor emitiría bytes no UTF-8 válidos y el cliente no podría decodificar la respuesta: el protocolo se corrompería en silencio.

---

## 2. Arranque y Verificación

El servidor MCP está integrado en el ejecutable orquestador principal:

```bash
python skills/arma3-sqf-skill/scripts/sqf_orchestrator.py --serve-mcp
```

### Protocolo de Handshake (Inicialización)
Al arrancar, el cliente MCP (como Claude Desktop) envía un mensaje de inicialización:
```json
{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "claude-desktop", "version": "1.0"}}}
```

Respuesta del servidor:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "2024-11-05",
    "capabilities": {
      "tools": {}
    },
    "serverInfo": {
      "name": "arma3-sqf-skill-mcp",
      "version": "1.0.0"
    }
  }
}
```

Posteriormente, el cliente envía la notificación de inicialización completada:
```json
{"jsonrpc": "2.0", "method": "notifications/initialized"}
```

---

## 3. Catálogo de Herramientas Expuestas

El servidor expone tres herramientas atómicas mediante el método `tools/list`:

### 3.1 `sqf_analyze` (Herramienta Principal de Auditoría)
Ejecuta el motor local determinista sobre el código SQF proporcionado y emite un informe estructurado conforme al contrato v1 (`REPORT_SCHEMA_VERSION: 1`), con paridad byte a byte respecto a la CLI.

#### `inputSchema`:
```json
{
  "type": "object",
  "properties": {
    "code": {
      "type": "string",
      "description": "Contenido del archivo o fragmento SQF a auditar."
    },
    "description_ext": {
      "type": "string",
      "description": "Contenido opcional de description.ext o CfgRemoteExec para auditoría de red."
    },
    "project_profile": {
      "type": "object",
      "description": "Perfil opcional del proyecto (ARMA_VERSION, DESTINO, CBA, ACE3)."
    },
    "file_path": {
      "type": "string",
      "description": "Ruta o nombre virtual de archivo para reportar hallazgos (por defecto 'code.sqf')."
    },
    "mode": {
      "type": "string",
      "enum": ["Micro", "Estándar", "Completo"],
      "description": "Modo explícito de ejecución. Si se omite, se ejecuta triaje automático."
    }
  },
  "required": ["code"]
}
```

#### Ejemplo de Petición (`tools/call`):
```json
{
  "jsonrpc": "2.0",
  "id": 10,
  "method": "tools/call",
  "params": {
    "name": "sqf_analyze",
    "arguments": {
      "code": "private _x = 10;\n_leaked = 20;",
      "file_path": "initServer.sqf"
    }
  }
}
```

#### Ejemplo de Respuesta:
```json
{
  "jsonrpc": "2.0",
  "id": 10,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "REPORT_SCHEMA_VERSION: 1\n[BLOQUEANTE] initServer.sqf:2 (Scope): Local variable \"_leaked\" assigned to an outer scope (not private)\n[SUGERENCIA] initServer.sqf:1 (Sintaxis): Variable \"_x\" not used\nRESUMEN: bloqueantes=1; sugerencias=1; no_verificado=0"
      }
    ],
    "report": "REPORT_SCHEMA_VERSION: 1\n[BLOQUEANTE] initServer.sqf:2 (Scope): Local variable \"_leaked\" assigned to an outer scope (not private)\n[SUGERENCIA] initServer.sqf:1 (Sintaxis): Variable \"_x\" not used\nRESUMEN: bloqueantes=1; sugerencias=1; no_verificado=0",
    "isError": false
  }
}
```

---

### 3.2 `sqf_wiki_query` (Consulta Documental Oficial)
Realiza consultas de solo lectura contra la réplica offline local de la wiki de Bohemia Interactive (`a3ref` / `arma3_wiki.db`).

#### `inputSchema`:
```json
{
  "type": "object",
  "properties": {
    "query": {
      "type": "string",
      "description": "Nombre del comando o función SQF a consultar (ej. 'hint', 'remoteExec', 'BIS_fnc_MP')."
    }
  },
  "required": ["query"]
}
```

#### Comportamiento ante Ausencia de Documentación:
Si la réplica local o base de datos SQLite no está disponible en la máquina, o si el símbolo no existe, responde estrictamente con estado `NO VERIFICADO` y motivo explícito (Principio de Honestidad Técnica).

---

### 3.3 `sqf_mode` (Triaje Determinista de Modo)
Determina si un fragmento o archivo califica para el modo **Micro** o si debe escalar a **Estándar** por la presencia de llamadas de red (`remoteExec`, `publicVariable`), scheduler (`waitUntil`, `sleep`, bucles pesados) o ciclo de vida (`initServer.sqf`, `description.ext`).

#### `inputSchema`:
```json
{
  "type": "object",
  "properties": {
    "code": {
      "type": "string",
      "description": "Código SQF a evaluar."
    },
    "file_path": {
      "type": "string",
      "description": "Ruta o nombre virtual de archivo opcional."
    }
  },
  "required": ["code"]
}
```

---

## 4. Configuración en Claude Desktop

Para habilitar las herramientas MCP en Claude Desktop:

1. Edita el archivo de configuración de Claude Desktop:
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Linux**: `~/.config/Claude/claude_desktop_config.json`
2. Incorpora la sección correspondiente de `integrations/claude/claude_desktop_config_snippet.json`:
   ```json
   {
     "mcpServers": {
       "arma3-sqf": {
         "command": "python",
         "args": [
           "skills/arma3-sqf-skill/scripts/sqf_orchestrator.py",
           "--serve-mcp"
         ],
         "cwd": "RUTA_A_TU_PROYECTO",
         "env": {
           "SQF_WIKI_DATA_PATH": "~/.a3ref/data",
           "SQF_WIKI_DB_PATH": "~/.a3ref/arma3_wiki.db"
         }
       }
     }
   }
   ```
3. Sustituye `"RUTA_A_TU_PROYECTO"` por la ruta absoluta a tu copia de trabajo local.
4. Reinicia Claude Desktop. Las 3 herramientas aparecerán identificadas por el icono de herramientas en la interfaz de chat.

---

## 5. Matriz de Degradación: Qué se Pierde sin Servidor MCP

Cuando Claude Desktop se utiliza en **Modo Pegado** (sin servidor MCP activo), aplican los protocolos de degradación estricta:

| Capacidad | Con Servidor MCP (Track B) | Sin Servidor MCP (Modo Pegado P1–P4) |
| :--- | :--- | :--- |
| **Análisis Determinista de Sintaxis / Scope (Cat. 1)** | Ejecutado por `sqf_analyze` con motor `sqflint` local. | Inspección manual/heurística del LLM bajo paquete inline. |
| **Triaje de Modo de Análisis** | Determinista (`sqf_mode`). | Forzado a `Estándar + NO VERIFICADO` (prohibido Micro manual). |
| **Verificación de Red / Whitelist (Cat. 5)** | Contrastable si se pasa `description_ext`. | Obligatorio `NO VERIFICADO` (sin acceso a `description.ext`). |
| **Verificación de Frameworks (Cat. 7)** | Contrastable si se pasa `project_profile`. | Obligatorio `NO VERIFICADO` (sin acceso a perfil de proyecto). |
| **Consulta Documental Biki** | Contrastada en DB local con commit SHA dinámico. | `NO VERIFICADO` si el modelo carece de contexto offline. |
| **Persistencia / Fuga de Código** | Cero fuga (proceso local por stdio). | El código del usuario se envía a la API del proveedor LLM. |
