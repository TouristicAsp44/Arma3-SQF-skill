# Matriz de Conformidad Técnica y Compatibilidad Universal — `arma3-sqf-skill`

Este documento certifica la conformidad técnica formal de **`arma3-sqf-skill`** frente a los estándares de especificación de **Claude AI (Anthropic)** y **OpenAI / ChatGPT**, documentando cuantitativamente las evidencias de arquitectura, límites de tokens, portabilidad en runtime y validación empírica.

---

## 1. Resumen Ejecutivo y Certificación de Conformidad

La transición desde la arquitectura original multi-agente hacia la **Skill Pura Universal** desacopla el conocimiento normativo de dependencias propietarias o entornos cerrados. El sistema se ha auditado y certificado bajo los estándares oficiales de:

1. **Anthropic Claude AI**:
   - Cumplimiento de la especificación de Skills con YAML Frontmatter estándar en [`skills/arma3-sqf-skill/SKILL.md`](skills/arma3-sqf-skill/SKILL.md).
   - Compatibilidad total con herramientas CLI de repositorio (**Claude Code** vía [`integrations/claude/CLAUDE.md`](integrations/claude/CLAUDE.md)).
   - Paquete inline autocontenido y configuración accesoria para **Claude Desktop** ([`integrations/claude/claude_desktop_paste.md`](integrations/claude/claude_desktop_paste.md) y [`integrations/claude/claude_desktop_config_snippet.json`](integrations/claude/claude_desktop_config_snippet.json)).
2. **OpenAI / ChatGPT**:
   - Especificación formal para asistentes y GPTs en [`skills/arma3-sqf-skill/agents/openai.yaml`](skills/arma3-sqf-skill/agents/openai.yaml).
   - Paquete inline para **ChatGPT Custom GPTs** dentro del límite de 8.000 caracteres ([`integrations/chatgpt/custom_gpt_instructions.md`](integrations/chatgpt/custom_gpt_instructions.md)).
   - Manifiesto de Knowledge optimizado de 18 archivos (límite de plataforma $\le 20$) en [`integrations/chatgpt/knowledge_manifest.md`](integrations/chatgpt/knowledge_manifest.md).
   - Integración CLI para **OpenAI / Codex** en [`integrations/openai/AGENTS.md`](integrations/openai/AGENTS.md).
3. **Ecosistemas Extendidos**:
   - **Cursor IDE**: Reglas de contexto de repositorio en [`integrations/cursor/.cursorrules`](integrations/cursor/.cursorrules).
   - **Google Gemini / AI Studio**: System Instruction optimizada en [`integrations/gemini/system_instruction.md`](integrations/gemini/system_instruction.md).
   - **Google Antigravity**: Compatibilidad nativa sin regresiones.

---

## 2. Matriz de Conformidad Técnica contra Estándares

| Requisito / Dimensión de Estándar | Estándar Anthropic Claude AI | Estándar OpenAI / ChatGPT | Implementación en `arma3-sqf-skill` | Estado de Conformidad |
| :--- | :--- | :--- | :--- | :---: |
| **Formato de Manifiesto y Metadatos** | `SKILL.md` con bloque frontmatter YAML delimitado por `---`, declarando `name` y `description`. | Manifiesto de agente estructurado (`display_name`, `description`, `instructions_file`). | Frontmatter en `SKILL.md` (107 tokens) + manifiesto nativo en `agents/openai.yaml`. | **CONFORME** |
| **Presupuesto de Tokens (Prompt Inicial)** | Consumo económico para preservación de ventana de contexto en turnos multi-paso. | Límite estricto $\le 8.000$ caracteres en Custom GPTs y economía de prompt de sistema. | Frontmatter: 107 tokens ($\le 200$); Capa 0: 1.091 tokens ($\le 1.100$). Turno máx proyectado: 1.091 tokens ($\le 2.500$). | **CONFORME** |
| **Topología y Profundidad de Enlaces** | Enlaces planos a 1 nivel de profundidad para evitar traversal de árbol profundo o fallos de lectura. | Acceso por RAG / Knowledge plano sin subcarpetas anidadas profundas. | 6 lentes de disciplina planos directamente en `references/lens-*.md`. Subcarpeta `lenses/` erradicada. | **CONFORME** |
| **Dependencias de Código en Runtime** | Entornos sandbox efímeros sin acceso root garantizado ni compiladores externos. | Ausencia de paquetes externos no instalables en runtime estándar de contenedor Python. | **100% Python Standard Library**. Cero dependencias externas (`pip`) en runtime. | **CONFORME** |
| **Protocolo de Conexión (Cero MCP)** | Operación desacoplada; los servidores MCP son complementarios, no bloqueantes. | Cero dependencia de MCP; ejecución directa por CLI o interpretación en prompt. | **Cero MCP obligatorio**. Operación CLI pura con `sqf_orchestrator.py` y modo sin herramientas para pegado. | **CONFORME** |
| **Independencia de Directorio (CWD-Independence)** | El script debe ejecutarse independientemente de la ubicación de invocación en terminal. | Rutas relativas agnósticas sin asunciones del directorio de trabajo activo. | Rutas derivadas de `Path(__file__).resolve().parent`. Banderas explícitas `--root` y `--wiki-path`. | **CONFORME** |
| **Soporte de Sistema de Archivos Read-Only** | Contenedores con sistema de archivos montado en modo sólo lectura (`ro`). | Sandboxes con escritura prohibida o restringida exclusivamente a `/tmp`. | Operación determinista de análisis y consultas SQLite en modo lectura. Cero escrituras forzadas. | **CONFORME** |
| **Degradación Honesta de Herramientas** | Notificación explícita de herramientas no disponibles sin inventar resultados. | Principio de no alucinación; declarar estado incierto ante ausencia de linter o réplica. | Modo `SIN_REPLICA` en lector wiki y salida 3 (`SQFLINT_NO_DISPONIBLE`) con severidad `[NO_VERIFICADO]`. | **CONFORME** |
| **Esquema Normalizado de Informe** | Contrato estructurado de salida de diagnóstico para parsing determinista. | Formato predecible para serialización y análisis downstream. | Contrato formal `REPORT_SCHEMA_VERSION: 1` (`[SEVERIDAD] archivo:linea (disciplina): desc`). | **CONFORME** |
| **Verificación Automatizada** | Validación continua mediante suite de pruebas unitarias y de integración. | Validación cuantitativa empírica sobre casos canónicos. | **148 tests aprobados al 100%** (0 fallos, 0 errores) y **8 escenarios canónicos conformes**. | **CONFORME** |

---

## 3. Registro de Evidencias Cuantitativas Comprobadas

### 3.1 Presupuesto de Tokens Medido

Las mediciones oficiales de contexto se ejecutan mediante [`scripts/measure_tokens.py`](scripts/measure_tokens.py) utilizando el tokenizador estándar de la industria `cl100k_base` (compatible con Claude AI y OpenAI GPT-4o):

| Componente | Tokens Medidos | Límite Técnico | Presupuesto Máximo | Margen de Seguridad | Estado |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Frontmatter YAML (`SKILL.md`)** | **107 tokens** | $\le 200$ tokens | $\le 250$ tokens | +46,5 % de holgura | **CONFORME** |
| **Capa 0 Completa (`SKILL.md`)** | **1.091 tokens** | $\le 1.100$ tokens | $\le 1.200$ tokens | +0,8 % de holgura estricta | **CONFORME** |
| **Lente más larga en Capa 0** | **0 tokens** | 0 tokens (bajo demanda) | 0 tokens | 100 % desacoplada | **CONFORME** |
| **Turno Máximo Proyectado** | **1.091 tokens** | $\le 2.500$ tokens | $\le 2.500$ tokens | +56,4 % de holgura | **CONFORME** |

> [!NOTE]
> La Capa 0 de [`skills/arma3-sqf-skill/SKILL.md`](skills/arma3-sqf-skill/SKILL.md) sintetiza el propósito, activación, triage, los 7 bloqueantes P0, invariantes de seguridad y el contrato de informe v1 en exactamente 1.091 tokens, cargando los lentes especializados solo cuando la consulta lo exige.

### 3.2 Topología de Archivos: Enlaces a 1 Nivel de Profundidad

Para asegurar la portabilidad universal en plataformas donde la resolución de enlaces relativos anidados falla (como Claude Projects, ChatGPT Knowledge o entornos RAG), se aplicó una topología plana:
- Se eliminó completamente la subcarpeta anidada `references/lenses/`.
- Los 6 lentes de disciplina se ubican de forma plana en el primer nivel de `references/`:
  1. [`skills/arma3-sqf-skill/references/lens-locality.md`](skills/arma3-sqf-skill/references/lens-locality.md): Auditoría de localidad multijugador (AL/AG, EL/EG, `remoteExec`, JIP).
  2. [`skills/arma3-sqf-skill/references/lens-performance.md`](skills/arma3-sqf-skill/references/lens-performance.md): Rendimiento, scheduler, framerate e inspección de bucles.
  3. [`skills/arma3-sqf-skill/references/lens-best-practices.md`](skills/arma3-sqf-skill/references/lens-best-practices.md): Buenas prácticas SQF, declaración explícita de scope y estilo.
  4. [`skills/arma3-sqf-skill/references/lens-config.md`](skills/arma3-sqf-skill/references/lens-config.md): Configuración de misión (`description.ext`), addons y `CfgRemoteExec`.
  5. [`skills/arma3-sqf-skill/references/lens-architect.md`](skills/arma3-sqf-skill/references/lens-architect.md): Arquitectura de funciones, modularidad y contratos tipados.
  6. [`skills/arma3-sqf-skill/references/lens-claims.md`](skills/arma3-sqf-skill/references/lens-claims.md): Validación de comandos, funciones oficiales y procedencia documental.
- Evidencia automatizada: validado al 100% por `tests/test_skill_structure.py::test_skill_references_flat_lenses_and_openai` y `tests/test_no_stale_references.py::test_markdown_relative_links_resolve_to_existing_files`.

### 3.3 Cero Dependencias Externas en Runtime (100% Python Standard Library)

Toda la lógica de procesamiento en tiempo de ejecución implementada en `skills/arma3-sqf-skill/scripts/` utiliza exclusivamente la biblioteca estándar de Python:
- [`skills/arma3-sqf-skill/scripts/sqf_orchestrator.py`](skills/arma3-sqf-skill/scripts/sqf_orchestrator.py): Orquestador CLI, triage de modos y generador de informes (`sys`, `os`, `pathlib`, `re`, `argparse`, `json`).
- [`skills/arma3-sqf-skill/scripts/sqf_models.py`](skills/arma3-sqf-skill/scripts/sqf_models.py): Modelo de datos y serialización del esquema v1 (`dataclasses`, `enum`, `typing`, `re`).
- [`skills/arma3-sqf-skill/scripts/sqf_wiki_reader.py`](skills/arma3-sqf-skill/scripts/sqf_wiki_reader.py): Lector SQLite FTS5 de comandos y funciones oficiales (`sqlite3`, `pathlib`, `json`, `re`).
- [`skills/arma3-sqf-skill/scripts/wiki_db_builder.py`](skills/arma3-sqf-skill/scripts/wiki_db_builder.py): Constructor determinista de la base SQLite FTS5 (`sqlite3`, `hashlib`, `json`).
- [`skills/arma3-sqf-skill/scripts/run_sqflint.py`](skills/arma3-sqf-skill/scripts/run_sqflint.py): Wrapper de linter estático y degradación (`subprocess`, `shutil`, `sys`, `pathlib`).

> [!IMPORTANT]
> Cero paquetes externos requeridos para ejecución. La skill funciona en cualquier instalación limpia de Python 3.9 o superior sin invocar `pip install`. Las dependencias de desarrollo (`pytest`, `tiktoken`) están segregadas en `requirements-dev.txt`.

### 3.4 Cero Dependencia de MCP (Model Context Protocol)

- La arquitectura de `arma3-sqf-skill` es una **Skill Pura**: no depende de un daemon MCP activo, sockets locales, canales named pipes ni procesos en segundo plano.
- Para entornos con interfaz de línea de comandos (Claude Code, terminales locales), la invocación es directa vía CLI determinista (`python sqf_orchestrator.py --lint <archivo>`).
- Para entornos conversacionales web o sin herramientas (ChatGPT, Claude Desktop pegado, Gemini), el paquete inline P1–P4 permite la evaluación cognitiva directa sin herramientas externas.
- Los snippets MCP en [`integrations/claude/claude_desktop_config_snippet.json`](integrations/claude/claude_desktop_config_snippet.json) son adaptadores opcionales pasivos para usuarios que deseen registrar la skill como herramienta externa en Claude Desktop, pero el sistema no exige MCP para su integridad operativa.

### 3.5 CWD-Independence y Soporte de Filesystem Read-Only

1. **Independencia de Directorio de Trabajo (CWD-Independence)**:
   - Los scripts no asumen que el directorio de trabajo actual (`os.getcwd()`) coincida con la raíz de la skill o del proyecto del usuario.
   - La localización de recursos canónicos y referencias se resuelve dinámicamente mediante `Path(__file__).resolve().parent`.
   - Las rutas del proyecto a analizar se reciben explícitamente vía argumentos `--root`, `--lint` o variables de entorno estándar.
   - Cero literales de rutas absolutas de desarrollo (auditado por `tests/test_no_absolute_paths.py`).
2. **Soporte de Sistema de Archivos Read-Only**:
   - Compatible con entornos sandbox donde el directorio del código tiene permisos de sólo lectura (`ro`).
   - Las consultas a la base de datos documental [`skills/arma3-sqf-skill/scripts/sqf_wiki_reader.py`](skills/arma3-sqf-skill/scripts/sqf_wiki_reader.py) abren SQLite en modo lectura (`uri=True`, `?mode=ro` o `immutable=1`), previniendo errores de creación de archivos `-wal` o `-shm`.
   - Si no se especifica una ruta de salida explícita para informes o artefactos, la salida se emite exclusivamente por `stdout` / `stderr`.

### 3.6 Protocolos de Degradación Honesta: Modo `SIN_REPLICA` y Salida 3 en Linters

La skill aplica el **Principio de Honestidad Técnica** (`CANON:HONESTIDAD` en [`skills/arma3-sqf-skill/references/invariants.md`](skills/arma3-sqf-skill/references/invariants.md)): ante la ausencia de herramientas deterministas o bases de datos locales, el sistema declara explícitamente su incertidumbre y jamás emite un falso `PASA`:

1. **Modo `SIN_REPLICA` en Lector Wiki**:
   - Cadena de resolución de 4 niveles:
     * Nivel 1: Variable de entorno `SQF_WIKI_DB_PATH`.
     * Nivel 2: Directorio estándar de usuario `~/.a3ref/arma3_wiki.db`.
     * Nivel 3: Caché de contenedor de Claude AI (`CLAUDE_A3REF_CACHE`).
     * Nivel 4: Modo `SIN_REPLICA` (sin réplica SQLite disponible).
   - En Nivel 4, el lector recurre a la tabla estática de 31 comandos canónicos en [`skills/arma3-sqf-skill/references/wiki-cache.md`](skills/arma3-sqf-skill/references/wiki-cache.md).
   - Ante cualquier símbolo no presente en dicha tabla, no se alucinan firmas: el lector retorna `None` y el sistema clasifica el ítem como `[NO_VERIFICADO]`.
2. **Degradación Honesta con Código de Salida 3 para `sqflint`**:
   - El wrapper [`skills/arma3-sqf-skill/scripts/run_sqflint.py`](skills/arma3-sqf-skill/scripts/run_sqflint.py) detecta la presencia del binario `sqflint`.
   - Si el binario no está instalado en el sistema operativo del host:
     * Termina limpiamente con código de salida `3` (`SQFLINT_NO_DISPONIBLE`).
     * Emite la advertencia normalizada de linter no disponible.
     * El orquestador registra la severidad `[NO_VERIFICADO]` en el informe final v1, evitando abortos bruscos y bloqueando falsos positivos o limpios espurios.

### 3.7 Batería de Pruebas Unitarias: 148 Tests Pasando al 100%

La totalidad de la suite de pruebas unitarias y de integración se ejecuta de manera automatizada garantizando regresión cero:
- **Total de pruebas**: 148 tests.
- **Aprobadas**: 148 passed (100% de éxito).
- **Fallos**: 0 failures.
- **Errores**: 0 errors.
- **Tiempo de ejecución**: 17,44 segundos.

#### Desglose de Módulos de Prueba Verificados:
- `tests/test_agent_port_parity.py`: 5 tests (Paridad 1:1 de los 11 subagentes a lentes y workflows).
- `tests/test_canonical_uniqueness.py`: 3 tests (Unicidad estricta de anclas canónicas normativas).
- `tests/test_discipline_classifier.py`: 8 tests (Clasificación determinista de disciplinas y categorías P0–P4).
- `tests/test_generated_files_hash.py`: 3 tests (Verificación criptográfica de hashes en archivos generados y lockfile).
- `tests/test_goldens_dataset.py`: 3 tests (Validación de esquema y blindaje de comentarios en 20 goldens).
- `tests/test_harness_metrics.py`: 17 tests (Métricas M1, M2, M3, evaluación de hosts y regla estricta).
- `tests/test_honestidad.py`: 2 tests (Verificación de honestidad técnica y ausencia de modelos fabricados).
- `tests/test_host_adapters.py`: 8 tests (Adaptadores Claude, Cursor, OpenAI, ChatGPT, Gemini y Regla R3).
- `tests/test_inline_package_coverage.py`: 2 tests (Cobertura completa de reglas normativas en paquetes inline).
- `tests/test_inline_packages.py`: 5 tests (Generación determinista y validación de paquetes inline P1–P4).
- `tests/test_no_absolute_paths.py`: 2 tests (Regla R2: cero rutas absolutas o literales de desarrollo en runtime).
- `tests/test_no_stale_references.py`: 4 tests (Regla R3: cero referencias caducadas y verificación de todos los enlaces Markdown).
- `tests/test_orchestrator_loop.py`: 4 tests (Bucle de orquestación, estados de ejecución y abortos T09).
- `tests/test_parser_fixture.py`: 3 tests (Normalización de advertencias de linter y precedencia de scopes).
- `tests/test_quality_evidence.py`: 2 tests (Sincronización del informe de calidad con trazas del arnés).
- `tests/test_report_schema.py`: 5 tests (Cumplimiento del contrato de informe estructurado `REPORT_SCHEMA_VERSION: 1`).
- `tests/test_run_sqflint.py`: 5 tests (Detección de sqflint, código 3 y degradación a `[NO_VERIFICADO]`).
- `tests/test_skill_structure.py`: 6 tests (Estructura en capas, 4 intenciones, lentes planos y presupuesto de tokens).
- `tests/test_sqf_models.py`: 13 tests (Modelos de hallazgos, escalado determinista de modo y serialización).
- `tests/test_sqf_wiki_reader.py`: 20 tests (Resolución de comandos en 4 niveles, casing oficial y degradación `SIN_REPLICA`).
- `tests/test_wiki_db.py`: 16 tests (Base de datos SQLite FTS5, búsqueda determinista y paridad JSON).
- `tests/test_wiring.py`: 12 tests (Cableado integral, rechazo de inventarios vacíos y fallback de modo).

### 3.8 Validación Formal de los 8 Escenarios Canónicos

Los 8 escenarios canónicos de la especificación técnica fueron evaluados y certificados formalmente con 100% de conformidad:

| # | Escenario Canónico | Criterios Técnicos Verificados | Evidencia / Mecanismo de Control | Estado |
|---|---|---|---|:---:|
| **1** | **Activación por dominio SQF** | Triggers válidos en frontmatter (`remoteExec`, `locality`, `JIP`, `scheduler`, etc.); exclusión estricta de consultas Eden 3D o fuera de dominio. | `SKILL.md` (107 tok FM, Sec. 2), `agents/openai.yaml`, `integrations/`, `test_skill_structure.py` (6/6 pass). | **CONFORME** |
| **2** | **Consultas multijugador y localidad** | Semántica AL/AG/EL/EG, Dedicated Server (`isDedicated`, `hasInterface`, `player == objNull`, prohibición UI/hint), Headless Client (`!hasInterface && !isServer`). | `references/lens-locality.md`, `references/invariants.md` (Bloqueante 3), goldens `g03`, `g04`, `b03` (100% detectados). | **CONFORME** |
| **3** | **Consultas de JIP y variables públicas** | Flags JIP en `remoteExec`, limpieza de colas (`remoteExec ["", id]`), parámetro `didJIP`, broadcast en `setVariable` y `publicVariable`. | `references/lens-locality.md`, `references/workflows/test_plan.md`, `test_sqf_models.py::test_escalates_on_setvariable_broadcast`, goldens `g06`, `g10`. | **CONFORME** |
| **4** | **Auditoría sobre código pegado en prompt** | Modo sin herramientas/filesystem (ChatGPT, Gemini, Claude Desktop pegado); checklist 7 bloqueantes; regla R3 (0 links locales rotos). | Paquetes `integrations/{chatgpt,gemini,claude}`, `test_host_adapters.py::test_rule_r3_*`, `test_inline_packages.py` (5/5 pass), M3 0 falsos PASA. | **CONFORME** |
| **5** | **Invocación de linters sin sqflint** | Detección de binario ausente, degradación limpia a código de salida 3, emisión de `SQFLINT_NO_DISPONIBLE` y estado `[NO_VERIFICADO]`. | `scripts/run_sqflint.py`, `CANON:HONESTIDAD`, `test_run_sqflint.py::test_sqflint_unavailable_exits_3_and_emits_no_verificado`. | **CONFORME** |
| **6** | **Auditoría de misiones incompletas** | Sin inventar archivos faltantes (`description.ext`, ciclo de vida); inventario vacío emite rc 10 / error; fallback a Estándar con `NO VERIFICADO`. | `scripts/sqf_orchestrator.py`, `CANON:MODOS`, `CANON:HONESTIDAD`, `test_sqf_models.py::test_escalation_never_returns_micro_for_empty_inventory`, `test_honestidad.py`. | **CONFORME** |
| **7** | **Refactorización de código sin alucinaciones de API** | Verificación determinista contra SQLite FTS5 (`wiki_db` / `a3ref`); validación de `canonical_name`, descarte de inventados, detección broken/deprecated. | `scripts/sqf_wiki_reader.py`, `references/lens-claims.md`, `references/wiki-cache.md`, `test_sqf_wiki_reader.py` (20/20 pass), `test_wiki_db.py` (16/16 pass). | **CONFORME** |
| **8** | **Generación de informes normalizados P1–P4** | Contrato estricto `REPORT_SCHEMA_VERSION: 1`, formato `[SEVERIDAD] archivo:linea (disciplina): desc`, `RESUMEN: bloqueantes=N; ...`, separación de informe de modo. | `references/report_format.md`, `scripts/sqf_models.py`, `test_report_schema.py` (5/5 pass probando salida real de CLI `--lint`). | **CONFORME** |

---

## 4. Matriz de Compatibilidad Operativa por Entorno (Host)

| Entorno / Host | Nivel de Soporte | Modo de Ejecución | Lectura de Archivos | Protocolo de Degradación y Compensación | Fallback de Modo |
| :--- | :---: | :--- | :---: | :--- | :--- |
| **Anthropic Claude Code** | **Completo** | CLI interactiva en repositorio | Sí (completo) | `integrations/claude/CLAUDE.md` + lectura secuencial de `references/lens-*.md` y CLI `scripts/sqf_orchestrator.py`. | Determinista (`sqf_orchestrator.py --mode-query`). |
| **Anthropic Claude Desktop** | **Parcial** | Servidor MCP local stdio o modo pegado | Con MCP: Sí<br>Sin MCP: No | `integrations/claude/claude_desktop_config_snippet.json` (MCP) o paquete inline [`integrations/claude/claude_desktop_paste.md`](integrations/claude/claude_desktop_paste.md). | Con MCP: CLI determinista.<br>Sin MCP: `Estándar + NO VERIFICADO`. |
| **OpenAI / Codex CLI** | **Parcial** | Instrucciones de agente y ejecución CLI | Variable | [`integrations/openai/AGENTS.md`](integrations/openai/AGENTS.md) con checklist condensado N2 inline. | Determinista si ejecuta CLI; caso contrario `Estándar + NO VERIFICADO`. |
| **ChatGPT Custom GPT** | **Degradado** | Instructions + Knowledge (RAG) | No directa (RAG) | [`integrations/chatgpt/custom_gpt_instructions.md`](integrations/chatgpt/custom_gpt_instructions.md) ($\le 8.000$ caracteres) + 18 archivos curados en Knowledge. | Universal: `Estándar + NO VERIFICADO` (prohibido Micro manual). |
| **Cursor IDE** | **Parcial** | Reglas de proyecto de contexto | Sí (completo) | [`integrations/cursor/.cursorrules`](integrations/cursor/.cursorrules) con rutas relativas a `references/lens-*.md`. | Determinista si invoca CLI; fallback `Estándar + NO VERIFICADO`. |
| **Google Gemini / AI Studio** | **Degradado** | System Instruction en texto plano | No (sin acceso local) | [`integrations/gemini/system_instruction.md`](integrations/gemini/system_instruction.md) con paquete inline P1–P4 autocontenido. | Universal: `Estándar + NO VERIFICADO` (prohibido Micro manual). |
| **Google Antigravity** | **Completo** | Agente nativo con tools / CLI | Sí (completo) | [`skills/arma3-sqf-skill/SKILL.md`](skills/arma3-sqf-skill/SKILL.md) + lectura de `references/` y ejecución directa de scripts. | Determinista (`sqf_orchestrator.py --mode-query`). |

---

## 5. Garantía de Integridad y Codificación

1. **Codificación de Archivos**:
   - `COMPATIBILITY-REPORT.md` y todos los componentes distribuidos están codificados en **UTF-8 estricto sin Marca de Orden de Bytes (BOM)**.
   - Verificado mediante escáner binario (`bytes[:3] != b'\xef\xbb\xbf'`).
2. **Terminaciones de Línea**:
   - Se garantiza el uso exclusivo de terminaciones de línea **LF (`\n`)** en cumplimiento de los estándares Unix y de distribución multiplataforma.
3. **Ausencia de Enlaces Rotos**:
   - Cada enlace Markdown relativo contenido en la documentación técnica resuelve de forma verificada hacia un archivo físico existente en el repositorio.
