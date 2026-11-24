# Guía de Instalación y Uso Universal — Arma 3 SQF Skill (`arma3-sqf-skill`)

Manual integral de instalación, configuración y operación para la **Skill Pura Universal de SQF para Arma 3**.

La skill está construida bajo una arquitectura modular, agnóstica de transporte (100% desacoplada de servidores MCP y transportes propietarios) y con cero dependencias externas en su motor de ejecución en Python (`Python 3.11+ stdlib pura`). Puede importarse tanto en plataformas conversacionales y asistentes web de IA (Claude AI, ChatGPT Custom GPTs) como en editores y entornos locales de ingeniería (Cursor, Claude Desktop, Google Antigravity, y ejecución directa por línea de comandos CLI/CI).

---

## 1. Arquitectura de Distribución («Skill Pura»)

El paquete distribuible canónico (`arma3-sqf-skill.zip`) organiza los artefactos en una jerarquía plana, modular y determinista:

```text
arma3-sqf-skill/
├── SKILL.md                  # Capa 0: Frontmatter YAML canónico + directrices de activación y triage
├── agents/
│   └── openai.yaml           # Descriptor de configuración para OpenAI / Custom GPTs
├── references/               # Base de conocimiento modular a 1 nivel de profundidad
│   ├── lens-architect.md     # Lente: Arquitectura, modularidad y CfgRemoteExec
│   ├── lens-best-practices.md# Lente: Buenas prácticas, params/private y micro-optimizaciones
│   ├── lens-claims.md        # Lente: Verificación rigurosa de APIs contra BIKI
│   ├── lens-config.md        # Lente: Misiones (description.ext) vs Addons (config.cpp)
│   ├── lens-locality.md      # Lente: Semántica AL/AG/EL/EG, Dedicated Server, HC y JIP
│   ├── lens-performance.md   # Lente: Carga de scheduler, cadencias por frame y bucles
│   ├── invariants.md         # Definición canónica de los 7 Bloqueantes P0 y reglas de oro
│   ├── rubrica.md            # Rúbrica formal de severidad (BLOQUEANTE, SUGERENCIA, NO_VERIFICADO)
│   ├── report_format.md      # Contrato de salida unificado (REPORT_SCHEMA_VERSION: 1)
│   ├── checklist-entrega.md  # Checklist de salida A–I para certificación de código
│   ├── diferencial-misiones-addons.md # Diferencias normativas según DESTINO
│   ├── sqf-standards.md      # Estándares de estilo, nomenclatura y estructuración SQF
│   ├── wiki-cache.md         # Caché compacta BIKI de alta velocidad
│   └── workflows/            # Flujos generativos (auditoría, desarrollo, documentación, tests)
├── scripts/                  # Motor determinista en Python stdlib pura (3.11+)
│   ├── sqf_orchestrator.py   # Orquestador central de análisis estático, triage y linters
│   ├── sqf_models.py         # Modelos de datos del contrato v1 y validadores de esquema
│   ├── sqf_wiki_reader.py    # Lector determinista de BIKI (soporte JSON y SQLite FTS5)
│   ├── wiki_db_builder.py    # Generador de base SQLite optimizada para búsquedas <0,5 ms
│   ├── run_sqflint.py        # Envoltorio multiplataforma con fallback a código de salida 3
│   └── bootstrap.sh          # Script de aprovisionamiento de caché offline para entornos efímeros
└── assets/
    └── logo.png              # Identidad visual de la skill (< 50 KB)
```

---

## 2. Importación y Uso en Anthropic Claude AI

Claude AI (en la web o en proyectos de Claude Pro/Team/Enterprise) admite importar skills empaquetadas directamente como archivo ZIP.

### Paso 1: Subida de la Skill en Ajustes
1. Inicia sesión en [Claude.ai](https://claude.ai).
2. Dirígete a la configuración de tu cuenta o proyecto:
   - En proyectos: Abre el proyecto -> **Project Knowledge** o panel de **Skills**.
   - En ajustes globales de la cuenta: **Settings** -> **Capabilities** / **Skills**.
3. Pulsa sobre **Upload Skill** (o **Add Content**) y sube el archivo empaquetado `arma3-sqf-skill.zip`.
4. Claude AI descomprimirá la estructura con la carpeta raíz `arma3-sqf-skill/` e indexará inmediatamente el archivo `SKILL.md` como la Capa 0 del sistema.

### Paso 2: Activación Automática por Contexto
No requieres comandos previos ni configuraciones complejas. Claude activará automáticamente la skill en cuanto detecte en la conversación:
- Archivos `.sqf`, estructuras de misión (`description.ext`, `mission.sqm`) o addons (`config.cpp`).
- Funciones y comandos de red multijugador: `remoteExec`, `remoteExecCall`, `CfgRemoteExec`, `publicVariable`, `setVariable [..., true]`.
- Conceptos de localidad y arquitectura de red: AL/AG (*Arguments Local/Global*), EL/EG (*Effects Local/Global*), servidor dedicado (`isDedicated`, `Arma3Server.exe`), Headless Client (`!hasInterface && !isServer`), eventos de unión tardía JIP (`didJIP`).
- Scheduler y concurrencia: `spawn`, `execVM`, `sleep`, `uiSleep`, `waitUntil`, `canSuspend`.

### Paso 3: Aprovisionamiento Opcional de Caché BIKI Offline (`bootstrap.sh`)
En entornos de Claude que cuenten con acceso a terminal o sandbox de ejecución Bash efímero (por ejemplo, sesiones interactivas con herramientas de consola o Claude Code):

1. Ejecuta el script de arranque incluido:
   ```bash
   bash scripts/bootstrap.sh
   ```
2. **Operaciones ejecutadas por `bootstrap.sh`**:
   - Clona superficialmente (`git clone --depth 1`) el repositorio canónico `https://github.com/a3ref/a3ref.git` en `$HOME/a3ref_cache/a3ref`.
   - Compila la base de datos SQLite optimizada (`arma3_wiki.db`) en `$HOME/a3ref_cache/arma3_wiki.db` usando `wiki_db_builder.py`.
   - Exporta automáticamente las variables de entorno necesarias:
     ```bash
     export SQF_WIKI_DB_PATH="$HOME/a3ref_cache/arma3_wiki.db"
     export PYTHONDONTWRITEBYTECODE=1
     ```
3. **Comportamiento si no se ejecuta `bootstrap.sh`**:
   Si tu entorno no permite ejecutar comandos Bash (chat conversacional puro), la skill funciona sin impedimentos: recurre a la base interna `references/wiki-cache.md` o aplica honestidad técnica reportando `[NO_VERIFICADO]` para cualquier comando cuya sintaxis o localidad no pueda confirmarse de manera fehaciente.

---

## 3. Configuración en OpenAI ChatGPT / Custom GPTs

Para utilizar la skill como un **Custom GPT** en la plataforma OpenAI ChatGPT (disponible para cuentas Plus, Team y Enterprise mediante GPT Builder).

### Paso 1: Crear el Custom GPT
1. Inicia sesión en ChatGPT y navega a **Explore GPTs** -> **+ Create**.
2. Selecciona la pestaña **Configure** para acceder a la parametrización técnica avanzada.

### Paso 2: Configurar Identidad e Instrucciones
Configura la ficha técnica del asistente a partir de los metadatos canónicos declarados en `skills/arma3-sqf-skill/agents/openai.yaml`:
- **Name**: `Arma 3 SQF Specialist`
- **Description**: `Asistencia técnica especializada y auditoría de scripts SQF para Arma 3 en servidor dedicado y multijugador.`
- **Instructions**: Abre el archivo `integrations/chatgpt/custom_gpt_instructions.md`, copia todo su contenido y pégalo en el campo **Instructions**.
  > **Nota de Diseño**: El texto provisto en `integrations/chatgpt/custom_gpt_instructions.md` está estrictamente optimizado para ocupar menos de 8.000 caracteres, respetando el límite rígido de GPT Builder sin perder ninguna directriz de los 7 Bloqueantes P0.

### Paso 3: Subir Archivos a Knowledge (Base de Conocimiento)
1. En la sección **Knowledge**, pulsa sobre **Upload files**.
2. Sube el archivo `arma3-sqf-skill.zip` o los documentos Markdown esenciales detallados en `integrations/chatgpt/knowledge_manifest.md`:
   - `SKILL.md`
   - Los 6 lentes modulares: `references/lens-architect.md`, `references/lens-best-practices.md`, `references/lens-claims.md`, `references/lens-config.md`, `references/lens-locality.md`, `references/lens-performance.md`.
   - Archivos canónicos normativos: `references/invariants.md`, `references/rubrica.md`, `references/report_format.md`, `references/checklist-entrega.md`, `references/diferencial-misiones-addons.md`, `references/sqf-standards.md`.
   - Flujos de trabajo: `references/workflows/*.md`.
  > **Advertencia**: No subas scripts ejecutables `.py` ni cachés binarias al panel Knowledge, ya que el motor de búsqueda vectorial de OpenAI solo indexa documentos de texto y Markdown.

### Paso 4: Configurar Capacidades (Capabilities)
- **Code Interpreter**: **Habilitado** (recomendado para que ChatGPT pueda recibir, leer y procesar archivos de script `.sqf`, `.ext` o `.hpp` adjuntos por el usuario en el chat).
- **Web Browsing**: **Habilitado** (útil como mecanismo de respaldo para consultar la wiki oficial de Bohemia Interactive si el usuario introduce un comando muy reciente no indexado).
- **DALL·E Image Generation**: **Deshabilitado** (inaplicable a la auditoría y desarrollo de scripts).

---

## 4. Instalación Local en Cursor, Claude Desktop y Google Antigravity

Para desarrolladores que trabajan en entornos locales con acceso directo al sistema de archivos del proyecto.

### 4.1 Cursor
1. Copia el archivo de reglas preconfigurado a la raíz de tu proyecto o repositorio:
   ```bash
   cp integrations/cursor/.cursorrules .cursorrules
   ```
2. Asegúrate de incluir la carpeta de la skill (`skills/arma3-sqf-skill/`) dentro del espacio de trabajo.
3. Cursor indexará las directrices y lentes automáticamente. El modelo aplicará de forma estricta los 7 Bloqueantes P0 y el formato de reporte v1 durante cualquier refactorización o edición de archivos `.sqf`.

### 4.2 Claude Desktop
Claude Desktop admite dos modalidades de integración:
- **Modalidad A (Modo Pegado / Conversación)**:
  Copia el contenido del archivo `integrations/claude/claude_desktop_paste.md` y pégalo al inicio de tu sesión en Claude Desktop. El modelo adoptará el protocolo estandarizado de auditoría y los 7 Bloqueantes P0.
- **Modalidad B (Uso con Terminal / Herramientas Locales)**:
  Ejecuta directamente el orquestador determinista desde una consola local integrada para validar archivos:
  ```bash
  python skills/arma3-sqf-skill/scripts/sqf_orchestrator.py --lint ruta/a/archivo.sqf
  ```

### 4.3 Google Antigravity
La skill cumple nativamente el estándar formal de Google Antigravity:
1. Copia la carpeta `arma3-sqf-skill` a cualquiera de las rutas estándar de descubrimiento de Antigravity:
   - **Global**: `~/.gemini/antigravity/skills/arma3-sqf-skill/`
   - **Workspace**: `.agents/skills/arma3-sqf-skill/` o `skills/arma3-sqf-skill/`
2. Antigravity detecta automáticamente el frontmatter YAML de `SKILL.md` (107 tokens) y carga bajo demanda las referencias de `references/lens-*.md` sin sobrecargar el contexto inicial.

---

## 5. Uso Local en Línea de Comandos (CLI / CI/CD)

El motor determinista de la skill está implementado en **Python 3.11+ utilizando exclusivamente la biblioteca estándar** (`stdlib pura`). No requiere instalar librerías externas mediante `pip`.

### 5.1 Triage y Auditoría con `sqf_orchestrator.py`

#### A. Consulta de Modo de Auditoría (`--mode-query`)
Determina de forma determinista el modo requerido (Micro, Estándar o Completo) a partir del análisis del inventario de archivos:
```bash
python skills/arma3-sqf-skill/scripts/sqf_orchestrator.py --mode-query --root /ruta/a/mi_mision
```
- **Micro**: <= 50 líneas, archivo único, sin init, sin primitivas de red ni scheduler.
- **Estándar**: 2–3 archivos, > 50 líneas, presencia de init o primitivas de red/scheduler.
- **Completo**: >= 4 archivos o >= 3 módulos, presencia de JIP, HC o persistencia.

#### B. Auditoría Estática de Archivos SQF (`--lint`)
Ejecuta la auditoría estática completa generando el informe estructurado bajo el contrato `REPORT_SCHEMA_VERSION: 1`:
```bash
python skills/arma3-sqf-skill/scripts/sqf_orchestrator.py --lint /ruta/a/mi_mision/fn_initServer.sqf
```

### 5.2 Consulta a la Wiki de Bohemia (BIKI) con `sqf_wiki_reader.py`

Permite inspeccionar sintaxis, tipos de argumentos, localidad y targets de comandos de Arma 3 de forma instantánea:

```bash
# Consulta directa de un comando (ej. remoteExec)
python skills/arma3-sqf-skill/scripts/sqf_wiki_reader.py --command remoteExec

# Búsqueda sintáctica en dos pasos
python skills/arma3-sqf-skill/scripts/sqf_wiki_reader.py --lookup "createVehicle"

# Volcado completo en formato JSON estructurado
python skills/arma3-sqf-skill/scripts/sqf_wiki_reader.py --command setVariable --full
```

### 5.3 Envoltorio Determinista de `sqflint` (`run_sqflint.py`)

Si cuentas con el linter nativo `sqflint` (`cargo install sqflint`), el script `run_sqflint.py` proporciona una interfaz multiplataforma unificada:

```bash
python skills/arma3-sqf-skill/scripts/run_sqflint.py /ruta/a/archivo.sqf
```

#### Códigos de Salida Estandarizados:
- `0`: **SIN ERRORES**. Análisis completado exitosamente sin fallos de sintaxis.
- `1`: **ERRORES**. Se detectaron fallos sintácticos o violaciones de estructura.
- `2`: **ERROR DE ARGUMENTOS**. Ruta no encontrada o argumentos inválidos.
- `3`: **SQFLINT_NO_DISPONIBLE**. El binario `sqflint` no está presente en el sistema. Emite un informe estructurado con estado `[NO_VERIFICADO]`.

### 5.4 Base de Datos SQLite FTS5 de Alto Rendimiento (`wiki_db_builder.py`)

Para habilitar consultas ultrarrápidas (<0,5 ms por comando, hasta 520x más rápido):
1. Clona el dataset oficial de `a3ref`:
   ```bash
   git clone --depth 1 https://github.com/a3ref/a3ref.git ~/.a3ref
   ```
2. Compila la base de datos SQLite con FTS5:
   ```bash
   python skills/arma3-sqf-skill/scripts/wiki_db_builder.py build --data ~/.a3ref/data --out ~/.a3ref/arma3_wiki.db
   ```
3. Configura la variable de entorno:
   - **Linux / macOS**:
     ```bash
     export SQF_WIKI_DB_PATH="$HOME/.a3ref/arma3_wiki.db"
     ```
   - **Windows (PowerShell)**:
     ```powershell
     $env:SQF_WIKI_DB_PATH = "$HOME\.a3ref\arma3_wiki.db"
     ```

---

## 6. Operación en Modo Sin Herramientas y Honestidad Técnica

### 6.1 Modo Sin Herramientas (Conversación Pura / Fallback)
En plataformas donde el modelo de lenguaje no cuenta con acceso de ejecución a terminal, sistema de archivos local ni binario de `sqflint` (tales como la interfaz web estándar de ChatGPT, Claude en modo pegado o Google Gemini):

1. **Regla R1 — Prohibición de Micro Manual**:
   Ante código pegado en el prompt, si no se puede inspeccionar el árbol de archivos completo del proyecto, está estrictamente prohibido asumir un modo `Micro`. El análisis se escala automáticamente a modo **`Estándar`** con indicación explícita de `NO VERIFICADO` en aspectos que requieran contexto global.
2. **Regla R2 — Los 7 Bloqueantes P0 Son Infranqueables**:
   El modelo evalúa visual y lógicamente el código contra los 7 bloqueantes canónicos de `references/invariants.md`:
   - *Bloqueante 1*: Sintaxis rota y variables sin ámbito explícito (`private` / `params`).
   - *Bloqueante 2*: Bucles infinitos, esperas sin timeout (`waitUntil`) y softlocks en `init`.
   - *Bloqueante 3*: Violaciones de entorno en servidor dedicado (`player`, comandos de interfaz `hint`/`cutRsc` en `isDedicated`).
   - *Bloqueante 4*: Suspensión ilegal en entorno no programado (`sleep`/`uiSleep` en bloques unscheduled con `!canSuspend`).
   - *Bloqueante 5*: Violación de listas blancas en `CfgRemoteExec >> Functions` (`mode = 1` vs `mode = 2`).
   - *Bloqueante 6*: Incompatibilidad de firmas o tipos en contratos `params`.
   - *Bloqueante 7*: Uso de dependencias no declaradas o incompatibles (`CBA_A3`, `ACE3`).
3. **Regla R3 — Cero Enlaces Rotos**:
   En entornos sin sistema de archivos, el modelo tiene prohibido generar enlaces a rutas de disco locales (`file://` o rutas relativas inaccesibles).
4. **Regla R4 — Formato Estandarizado de Informe**:
   Toda respuesta de auditoría debe cumplir el esquema formal unificado:
   ```text
   REPORT_SCHEMA_VERSION: 1
   [BLOQUEANTE|SUGERENCIA|NO_VERIFICADO] archivo:linea (disciplina): descripcion
   RESUMEN: bloqueantes=N; sugerencias=N; no_verificado=N
   ```

### 6.2 El Principio de Honestidad Técnica (`CANON:HONESTIDAD`)
El principio cardinal de la skill es: **Cero Falsos `PASA`**.

- **Sin herramientas no hay certeza absoluta**: Si no se dispone de `sqflint` o del validador de sintaxis en el entorno, el estado sintáctico debe reportarse obligatoriamente como **`NO VERIFICADO`**, nunca como `PASA`.
- **Sin réplica local BIKI**: Si la réplica de `a3ref` no está presente (`SIN_REPLICA`), la conformidad de comandos no triviales se clasifica como `NO VERIFICADO`.
- **Sin ejecución en servidor real**: Un análisis estático jamás debe certificar que un script "funciona garantizado en multijugador". Se certifica que *cumple las reglas estáticas de localidad y red*, señalando que la prueba dinámica en `Arma3Server.exe` requiere validación en hardware real.
