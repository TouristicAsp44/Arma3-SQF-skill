# Guía de Instalación y Configuración — `arma3-sqf-skill`

Instrucciones completas para instalar la skill universal de SQF para Arma 3 en cada host soportado, configurar sus dependencias, adaptadores y conjuntos de datos.

---

## 1. Requisitos Previos Generales

- **Python**: 3.11 o superior (compatible con Python 3.11, 3.12, 3.13, 3.14).
- *(Opcional pero recomendado)* **`sqflint`**: Linter nativo de SQF (`cargo install sqflint` o binario oficial).
- *(Opcional)* **Base SQLite FTS5**: Permite consultas sub-milisegundo (<0,5 ms) de comandos BIKI. Es opcional; si no existe, se degrada limpiamente a JSON o `NO VERIFICADO`.
- **Paquete Inline P1–P4**: Para entornos sin lectura de sistema de archivos (ChatGPT Custom GPT, Google Gemini, Claude Desktop pegado), los paquetes inline generados (`integrations/*/`) son autónomos y no requieren dependencias de disco.

---

## 2. Instalación por Host

### 2.1 Claude Code (CLI / Terminal)
1. Clona o copia el repositorio y sitúate en su raíz:
   ```bash
   cd arma3-sqf-skill
   ```
2. Asegúrate de contar con Python 3.11+ (el núcleo utiliza exclusivamente la biblioteca estándar).
3. Inicia Claude Code en el directorio del proyecto:
   ```bash
   claude
   ```
   Claude Code detectará automáticamente el archivo `integrations/claude/CLAUDE.md`.
4. **Comando de verificación**:
   ```bash
   python scripts/check.py --fase PR-6
   ```

### 2.2 Claude Desktop
Claude Desktop admite dos modalidades de integración:
- **Opción A (Sin MCP — Modo Pegado)**:
  Copia el contenido del archivo generado `integrations/claude/claude_desktop_paste.md` y pégalo al inicio de la conversación. Es el fallback inmediato si no se desea configurar procesos locales.
- **Opción B (Con MCP Local — Track B / PR-6)**:
  Integra el servidor MCP local por stdio (`sqf_orchestrator.py --serve-mcp`) en `claude_desktop_config.json` usando el fragmento de `integrations/claude/claude_desktop_config_snippet.json`.
  - **¿Qué es?**: Servidor JSON-RPC 2.0 por stdio (stdlib pura) que expone `sqf_analyze`, `sqf_wiki_query` y `sqf_mode`.
  - **¿Cuándo lo necesitas?**: Para que Claude Desktop invoque el motor de análisis y la wiki automáticamente en local.
  - **¿Cuándo NO lo necesitas?**: En Claude Code, Cursor o Antigravity (que ya tienen acceso a archivos), o usando el modo pegado.
  - Consulta la guía detallada en [`docs/MCP.md`](docs/MCP.md) y [`integrations/claude/install.md`](integrations/claude/install.md).
- **Comando de verificación**:
  ```bash
  python -m pytest tests/test_mcp_server.py
  ```

### 2.3 Cursor
1. Copia el archivo de reglas a la raíz del espacio de trabajo:
   ```bash
   cp integrations/cursor/.cursorrules .cursorrules
   ```
2. Asegúrate de que la carpeta `skills/arma3-sqf-skill/` esté accesible en el workspace.
3. **Comando de verificación**:
   ```bash
   python -m pytest tests/test_host_adapters.py -k cursor
   ```

### 2.4 OpenAI Codex / CLI
1. Copia o referencia `integrations/openai/AGENTS.md` como archivo de instrucciones de agente en la raíz de trabajo:
   ```bash
   cp integrations/openai/AGENTS.md AGENTS.md
   ```
2. **Comando de verificación**:
   ```bash
   python -m pytest tests/test_host_adapters.py -k openai
   ```

### 2.5 ChatGPT Custom GPT
1. En GPT Builder (**Configure**), pega el contenido de `integrations/chatgpt/custom_gpt_instructions.md` en el campo **Instructions** (estrictamente <= 8.000 caracteres).
2. En la sección **Knowledge**, sube los **18 archivos** detallados en `integrations/chatgpt/knowledge_manifest.md`. *(No subir `wiki-cache.md` ni archivos `.py`)*.
3. **Comando de verificación (local)**:
   ```bash
   python -m pytest tests/test_inline_packages.py
   ```

### 2.6 Google Gemini / Google AI Studio
1. En Google AI Studio, crea un Chat Prompt y pega el contenido de `integrations/gemini/system_instruction.md` en el campo **System Instructions**.
2. Vía API de Python, inyecta `system_instruction.md` en `GenerateContentConfig(system_instruction=...)`.
3. **Comando de verificación (local)**:
   ```bash
   python scripts/generate_inline_packages.py --check
   ```

---

## 3. Dataset Offline BIKI (`a3ref`) y Caché de Comandos

La skill incluye soporte determinista para verificar la sintaxis, tipos y locality de comandos de Arma 3 contra la base de datos oficial de la Bohemia Interactive Community Wiki (BIKI).

### 3.1 Cómo obtener el dataset completo
1. **Clonar la réplica de `a3ref`**:
   ```bash
   git clone https://github.com/a3ref/a3ref.git ~/.a3ref
   ```
2. **Configurar la ruta mediante variable de entorno**:
   - Linux / macOS: `export SQF_WIKI_DATA_PATH="$HOME/.a3ref/data"`
   - Windows (PowerShell): `$env:SQF_WIKI_DATA_PATH = "$HOME\.a3ref\data"`
3. **Actualizar la caché procesada**:
   ```bash
   python skills/arma3-sqf-skill/scripts/sqf_wiki_reader.py --update
   ```

### 3.2 Estado sin réplica (`SIN_REPLICA`) y Degradación Limpia
Si la réplica de `a3ref` no está instalada:
- El estado pasa a `SIN_REPLICA`.
- Por el **Principio de Honestidad Técnica** (`references/invariants.md`), las comprobaciones dependientes de BIKI se marcarán obligatoriamente como **`NO VERIFICADO`**, nunca como `PASA`.

---

## 4. Base de Conocimiento SQLite (Opcional pero Recomendada)

Para acelerar las consultas BIKI a **sub-milisegundo (<0,5 ms)** (hasta 520x más rápido) y unificar la réplica en un archivo único:
1. **Construir la base de datos**:
   ```bash
   python skills/arma3-sqf-skill/scripts/wiki_db_builder.py build --data ~/.a3ref/data --out ~/.a3ref/arma3_wiki.db
   ```
2. **Carácter opcional**:
   Si no existe `arma3_wiki.db`, el motor recurre automáticamente a los ficheros JSON o reporta `NO VERIFICADO` con honestidad técnica.

---

## 5. Verificación Completa de la Instalación

Valida localmente todo el sistema con el release gate:

```bash
python scripts/check.py --fase PR-4
python -m pytest tests/ -q
python -m ruff check .
```
Salida esperada: `TODO EN VERDE para la fase solicitada.` y `All checks passed!`.
