# Instalación y Configuración para Claude (Claude Code y Claude Desktop)

Esta guía detalla el procedimiento de instalación, configuración y verificación de `arma3-sqf-skill` para el ecosistema Anthropic Claude.

---

## 1. Claude Code (CLI / Terminal)

Claude Code es el host recomendado principal: cuenta con acceso nativo al sistema de archivos del repositorio y ejecución de herramientas de terminal.

### Procedimiento
1. Abre tu terminal en la raíz del repositorio clonado:
   ```bash
   cd RUTA_A_TU_PROYECTO
   ```
2. Asegúrate de contar con Python 3.11 o superior instalado (el núcleo utiliza exclusivamente la biblioteca estándar, sin paquetes externos requeridos).
3. Inicia Claude Code en el repositorio:
   ```bash
   claude
   ```
4. El archivo `integrations/claude/CLAUDE.md` es detectado e indexado automáticamente por Claude Code al iniciar.

### Verificación
Para validar que el entorno y las reglas de Claude Code están operativos:
```bash
python scripts/check.py --fase PR-5
```
Salida esperada: `TODO EN VERDE para la fase solicitada.`

---

## 2. Claude Desktop

Claude Desktop soporta dos modalidades de integración:

### Opción A: Modo Pegado (Host Degradado, sin servidor MCP)
Ideal para consultas rápidas sin configuración de procesos locales.
1. Abre el archivo generado `integrations/claude/claude_desktop_paste.md`.
2. Copia todo su contenido y pégalo como mensaje inicial en tu chat de Claude Desktop.
3. El modelo adoptará el protocolo de revisión estandarizado P1–P4.
4. Si el servidor MCP presenta incidencias o no está disponible en tu entorno, esta modalidad actúa como fallback inmediato y seguro.

### Opción B: Integración MCP Local por stdio (Track B / PR-6)
Para usuarios que configuran Claude Desktop con herramientas locales vía Model Context Protocol sobre transporte stdio:

1. Localiza tu archivo de configuración de Claude Desktop:
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Linux: `~/.config/Claude/claude_desktop_config.json`
2. Copia la entrada correspondiente (Windows o POSIX) desde `integrations/claude/claude_desktop_config_snippet.json` a la sección `mcpServers` de tu configuración.
3. En la entrada copiada, sustituye `"cwd": "RUTA_A_TU_PROYECTO"` por la ruta absoluta a tu copia local del repositorio.
4. Las variables de entorno `SQF_WIKI_DATA_PATH` y `SQF_WIKI_DB_PATH` apuntan por defecto a `~/.a3ref/data` y `~/.a3ref/arma3_wiki.db`. Si no dispones de la réplica local de la wiki de Bohemia, no es necesario configurarlas; el servidor degradará ordenadamente a estado `NO VERIFICADO`.
5. Verifica manualmente el arranque del servidor MCP ejecutando desde terminal:
   ```bash
   python skills/arma3-sqf-skill/scripts/sqf_orchestrator.py --serve-mcp
   ```
   Envía un handshake JSON-RPC de inicialización:
   ```json
   {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test", "version": "1.0"}}}
   ```
   El servidor responderá con las capacidades de herramientas (`capabilities.tools`) en stdout y registrará diagnósticos únicamente en stderr.
6. Reinicia Claude Desktop. Las 3 herramientas expuestas (`sqf_analyze`, `sqf_wiki_query`, `sqf_mode`) quedarán disponibles en el chat.
