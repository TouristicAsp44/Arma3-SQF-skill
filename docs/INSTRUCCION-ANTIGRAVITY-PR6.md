================================================================================
INSTRUCCIÓN PARA ANTIGRAVITY — PR-6: Track B opcional — Servidor MCP local
                          (stdio, solo biblioteca estándar)
================================================================================
Copia este bloque completo en el chat de Antigravity, con la working directory
en la copia de trabajo:

    C:\Users\Touri\Documents\EDEN EDITOR\Skills Antigravity\arma3-sqf-skill

--------------------------------------------------------------------------------
CONTEXTO: DECISION DE PRODUCTO TOMADA Y POR QUÉ
--------------------------------------------------------------------------------
El usuario ha elegido el track **PR-6 (Track B: servidor MCP)**. Este hito es
**opcional y NO bloquea el producto**: si falla, la skill sigue siendo usable por
prompt + ficheros + scripts (Regla 2.3 del plan).

DECISIÓN DE DISEÑO (tomada por Mavis, no la reabras sin motivo):

  **Transporte: MCP sobre `stdio`, implementado SOLO con biblioteca estándar.**
  NO se construye un servidor HTTP/FastAPI público.

  Motivos (plan §6.3 y §6.4 + reglas del proyecto):
    - Un servidor HTTP público es un riesgo de seguridad y una fuga de código SQF
      de	addons/misiones a un servicio externo. Evitar la superficie HTTP elimina
      el riesgo de raíz, no lo mitiga.
    - El core tiene `dependencies = []` y una regla dura de "sin dependencias
      nuevas". Un MCP por stdio se puede escribir con la biblioteca estándar
      (JSON-RPC 2.0 sobre stdin/stdout), así que **la skill sigue siendo
      instalable sin pip install**.
    - MCP por stdio es lo que Claude Desktop consume de forma nativa vía
      `mcpServers` → `{command, args, env}`: no hay que publicar un servicio,
      ni API key, ni rate limit, ni hosting, ni tunnel, ni cuenta en ninguna
      plataforma.
    - El modelo no puede ver nada fuera de la máquina: el código SQF del usuario
      nunca sale del proceso local.

  Si en algún momento quieres la variante HTTP, es un **extra opt-in aparte**
  (ver Parte D), nunca el camino principal.

--------------------------------------------------------------------------------
ESTADO REAL VERIFICADO HOY (y dos defectos que ESTE hito debe cerrar)
--------------------------------------------------------------------------------
Gate actual: `python scripts/check.py --fase PR-5` → exit 0, **105/105 tests
verdes**; ruff limpio; inline `--check` OK; harness `--check` OK; tokens
intactos (Capa 0 1.186/1.200).

DEFECTO 1 — PROMESA ROTA EN UN ARTEFACTO YA PUBLICADO (gravedad: alta)
  `integrations/claude/claude_desktop_config_snippet.json` declara:
      "args": ["skills/arma3-sqf-skill/scripts/sqf_orchestrator.py", "--serve-mcp"]
  Pero **`sqf_orchestrator.py` NO tiene ninguna opción `--serve-mcp`** (sus
  `add_argument` son: --continuar, --state-file, --notes-file, --archived-notes-dir,
  --linter, --work-dir, --max-iterations, --input, --root, --dry-run, --mode-query,
  --lint, --mode, --file, --wiki, --wiki-path, --update-wiki, files).
  Es decir: el snippet que se entregó en PR-4 promete un arranque que **falla**.
  Un host que lo use hoy obtiene un error de argumentos. Esto es exactamente lo
  que la Regla R3 prohíbe (un artefacto que apunta a algo que no funciona).

DEFECTO 2 — RUTAS ABSOLUTAS EN UN ARTEFACTO DISTRIBUIBLE (gravedad: media)
  El mismo snippet incluye rutas absolutas de la máquina del autor:
      "cwd": "C:/Users/Touri/Documents/EDEN EDITOR/Skills Antigravity/arma3-sqf-skill"
      "SQF_WIKI_DB_PATH": "C:/Users/Touri/.a3ref/arma3_wiki.db"
      "cwd": "/var/arma3/arma3-sqf-skill"   (variante posix)
  El test `tests/test_no_absolute_paths.py` solo escanea el **código de runtime**
  (`skills/.../scripts`, `skills/.../references`, `scripts/`), por lo que NO
  detecta estas rutas. Para un artefacto que se copia a otros equipos, son rutas
  rotas por definición.

DEFECTO 3 — EL SNIPPET APUNTA LA WIKI A UN FICHERO QUE NO ES EL DIRECTORIO DE
DATOS (gravedad: media)
  El snippet declara:
      "SQF_WIKI_DATA_PATH": "skills/arma3-sqf-skill/references/wiki-cache.md"
  Pero `sqf_wiki_reader.py` espera un **directorio** de datos que contenga
  `commands.json`, `topics.json`, `syntax.json`, etc. (`resolve_wiki_root()`
  resuelve `root / "commands.json"`; `_discover_default_wiki_path()` exige
  `candidate.is_dir() and (candidate / "syntax.json").exists()`).
  `wiki-cache.md` es un markdown, no el directorio de datos: con ese env todas
  las consultas wiki fallan en silencio y el host degrada a "sin wiki" sin que
  nadie lo note. Ademas, cuando el env viene de una variable, `resolve_wiki_root`
  **no comprueba** que sea un directorio valido.

Ademas, la medicion sigue incompleta (recordatorio, no parte de este hito):
M2 = 88,9 % (NO PASA OBJETIVO >= 90 %), M3 = 7/7 con cobertura 7/14 goldens.
Esa medicion la cierra `docs/INSTRUCCION-ANTIGRAVITY-PR6PREP.md` (Parte A/B).
Este hito **no debe tocar la medición**.

--------------------------------------------------------------------------------
PARTE A — IMPLEMENTAR EL SERVIDOR MCP (stdio, stdlib)  [P0]
--------------------------------------------------------------------------------
A.1 Crea `skills/arma3-sqf-skill/scripts/mcp_server.py`:
    - SOLO biblioteca estándar. Sin `import mcp`, sin `fastapi`, sin `requests`.
    - Transporte: JSON-RPC 2.0 sobre **stdin/stdout**, un mensaje JSON por
      línea (newline-delimited). **Los logs NUNCA a stdout** (van a stderr): un
      log en stdout corrompe el protocolo.
    - Methods minimas: `initialize`, `notifications/initialized`, `tools/list`,
      `tools/call`, `ping`. Respuestas con `jsonrpc`, `id`, `result`/`error`.
    - `initialize` debe devolver el `protocolVersion` que declares y `capabilities.tools`.
    - unknown method -> error JSON-RPC valido (nunca una excepcion sin capturar).
    - Un mensaje malformado -> error JSON-RPC, el servidor **sigue vivo**.
    - Entrada: `arguments` de `tools/call` -> objeto `input` validado con tipos
      claros y errores de validacion explicitos.

A.2 Herramientas expuestas (prioridad segun plan §6.2):
    1. `sqf_analyze` — **LA ATOMICA Y LA IMPORTANTE**. Recibe codigo SQF y,
       opcionalmente, `description.ext` y el perfil de proyecto; ejecuta el
       motor EXISTENTE y devuelve el informe v1 **literal**, en un solo paso:
          REPORT_SCHEMA_VERSION: 1
          [BLOQUEANTE|SUGERENCIA|NO_VERIFICADO] archivo:linea (disciplina): descripcion
          RESUMEN: bloqueantes=N; sugerencias=N; no_verificado=N
       Reutiliza `sqf_models.format_findings_report()` y
       `sqf_models.summarize_escalation()`. **Cero formato duplicado**: si el
       informe del MCP no coincide byte a byte con el del motor, es un bug.
       Si el codigo exige modo superior, devuelve el informe de modo
       (`MODO:`/`MOTIVO:`/`RESUMEN: modo=...; escalado=si|no`) con el mismo
       contrato.
    2. `sqf_wiki_query` — consulta de solo lectura sobre la replica local
       (`sqf_wiki_reader`), por titulo/alias. **No escribe nada.**
    3. `sqf_mode` — triaje determinista de modo (`mode_query`).
    - Justificacion del diseño (plan §6.2): exponer el analisis como una sola
      llamada atomica evita obligar al modelo a encadenar llamadas y a
      reconciliar severidades, que es el fallo que el propio SKILL.md prohibe.

A.3 Conecta el flag prometido:
    - Añade `--serve-mcp` a `sqf_orchestrator.py` (junto al resto de
      `add_argument`), de modo que el snippet existente
      (`sqf_orchestrator.py --serve-mcp`) **funcione tal cual** sin editar el
      artefacto publicado. La implementacion vive en `mcp_server.py`; el
      orquestador solo delega.
    - `--serve-mcp` no debe argparsear ni escribir estado en disco: solo servir
      por stdio hasta EOF.

A.4 Degradacion honesta (Principio de Honestidad Tecnica):
    - Sin replica `a3ref` ni DB: `sqf_wiki_query` responde `NO VERIFICADO` con
      motivo, nunca inventa documentacion. Respeta la precedencia existente
      (CLI > env `SQF_WIKI_DATA_PATH` > candidatos > fallback).
    - Sin linter disponible: lo que no se puede verificar se reporta
      `NO VERIFICADO` (no `PASA`).
    - El MCP no debe persistir el codigo del usuario en disco ni enviarlo a
      ningun sitio. En memoria y nada mas.

A.5 Privacidad por construccion (no por politica):
    - No abras sockets. No hay `http.server`, no hay `asyncio` de red, no hay
      descargas, no hay telemetria. Todo es local.
    - Documentalo como postura en `docs/PRIVACIDAD.md`.

--------------------------------------------------------------------------------
PARTE B — ARREGLAR LOS ARTEFACTOS PUBLICADOS  [P0]
--------------------------------------------------------------------------------
B.1 Corrige `integrations/claude/claude_desktop_config_snippet.json`:
    - **CERO rutas absolutas.** Usa placeholders legibles y explica como
      sustituirlos, p. ej.:
          "cwd": "RUTA_A_TU_PROYECTO"
      con una nota en el `install.md` de que hay que reemplazarlo, mas una
      variante equivalente con `~` o variable de entorno donde el host lo admita.
      La variante posix `/var/arma3/...` tambien es una ruta absoluta: idem.
    - `SQF_WIKI_DB_PATH` -> usa `~/.a3ref/arma3_wiki.db` o la variable de
      entorno ya soportada por el reader, nunca una ruta de la maquina del autor.
    - `SQF_WIKI_DATA_PATH` -> debe apuntar al **directorio de datos** de la
      replica `a3ref` (el que contiene `commands.json`, `topics.json`,
      `syntax.json`), **no** a `references/wiki-cache.md`. Documenta el valor
      esperado (p. ej. `~/.a3ref/data`) y deja el env sin fijar si la replica
      no esta montada (el reader ya degrada a `NO VERIFICADO`).
    - Como red de seguridad en el codigo (no solo en el snippet): que
      `resolve_wiki_root()` **valide** que la ruta del env sea un directorio
      con `syntax.json` y, si no lo es, la descarte y siga la precedencia
      normal (candidatos -> fallback). Hoy una variable mal puesta rompe el
      wiki en silencio.
    - El JSON debe seguir siendo **JSON valido** (no admite comentarios).

B.2 Añade `integrations/claude/install.md` (si no existe) o actualizalo con:
    - Donde pegar el snippet en `claude_desktop_config.json` del usuario.
    - Como arrancar/verificar: `python skills/arma3-sqf-skill/scripts/sqf_orchestrator.py --serve-mcp`
      y como comprobar que responde (un `initialize` a mano o el comando de
      prueba que crees en la Parte C).
    - Como volver al modo pegado si el MCP no arranca (`claude_desktop_paste.md`).

B.3 Extiende la cobertura de rutas absolutas a los artefactos distribuibles:
    - Anade `integrations/` al escaner de `tests/test_no_absolute_paths.py`
      (crea `RUNTIME_DIRS`/`ARTIFACT_DIRS` separados) y **haz que falle** si
      aparece `C:/Users`, `C:\Users`, `/home/`, `/var/arma3`, `EDEN EDITOR` o
      cualquier ruta absoluta de FS en `integrations/`.
    - Si el test encuentra rutas legitimas que debe permitir (p. ej. `~/.a3ref`),
      declaralas en la lista blanca explicita, como ya se hace con `~`.

B.4 Contrato entre el snippet y el CLI (esto mata el Defecto 1 para siempre):
    - Test que lee `integrations/claude/claude_desktop_config_snippet.json` y
      **verifica que cada flag de `args` existe realmente** en el argparse del
      script apuntado. Si alguien borra `--serve-mcp`, el test falla.
    - Test que verifica que el `command` del snippet es resoluble (o que la
      variante posix esta documentada como alternativa).
    - Test que verifica que la ruta de `SQF_WIKI_DATA_PATH` del snippet (o su
      ausencia) es coherente con lo que el reader espera (directorio de datos),
      para que el Defecto 3 no vuelva.

--------------------------------------------------------------------------------
PARTE C — TESTS Y GATE  [P0]
--------------------------------------------------------------------------------
C.1 `tests/test_mcp_server.py` (nuevo), con trazas sinteticas en `tmp_path`:
    - Handshake: `initialize` -> `notifications/initialized` -> `tools/list`
      devuelve las 3 herramientas con su `inputSchema`.
    - `tools/call` de `sqf_analyze` devuelve un informe que cumple el contrato
      v1: empieza por `REPORT_SCHEMA_VERSION: 1`, cada hallazgo en el formato
      `[SEVERIDAD] archivo:linea (disciplina): descripcion`, y termina con
      `RESUMEN: bloqueantes=N; sugerencias=N; no_verificado=N`.
    - El informe del MCP **coincide con el del motor** para el mismo input
      (misma funcion, mismo texto): test de paridad, no de forma.
    - Mensaje JSON malformado -> error JSON-RPC valido y el servidor sigue
      vivo (test que envia otra peticion despues).
    - Metodo desconocido -> error JSON-RPC valido.
    - Ningun log a stdout: el test captura stdout durante una llamada y
      comprueba que **solo** hay JSON-RPC.
    - Sin wiki: `sqf_wiki_query` responde `NO VERIFICADO` con motivo.
    - Test de no-persistencia: tras `sqf_analyze` no aparece ningun fichero
      nuevo con el codigo de prueba en el arbol del repo ni en `tmp_path`.
    - Test de no-red: el modulo importado no usa sockets (assert sobre el
      codigo fuente: sin `socket`, `http.server`, `urllib.request`).
    - El test usa `subprocess` con el script real (no solo imports), para
      comprobar el arranque por stdio de verdad.

C.2 `tests/test_host_adapters.py` o el fichero que corresponda: el check de
    contrato del snippet (B.4) y el de rutas en `integrations/` (B.3).

C.3 `scripts/check.py --fase PR-6` con checks dirigidos:
    - "mcp handshake"
    - "mcp contrato de informe v1"
    - "integraciones sin rutas absolutas"
    - "snippet MCP coherente con el CLI"
    - "docs MCP"
    Con `skip_is_failure=True` (un SKIPPED en fase ya exigida = FALLO).
    Y `--fase PR-6` debe dejar el gate **completo** en verde (suite entera).

C.4 El gate `--fase PR-5` **debe seguir en verde** (no lo rompas: PR-6 es
    aditivo). Si necesitas tocar algo de PR-5, justifica por que y actualiza
    el generador correspondiente (`generated.lock.json` y friends).

--------------------------------------------------------------------------------
PARTE D — VARIANTE HTTP (extra opt-in, NO en este hito)  [P2, solo decisión]
--------------------------------------------------------------------------------
D.1 NO implementes FastAPI ni HTTP en este hito. Si en el futuro se quiere:
    - Va como extra: `[project.optional-dependencies] http = ["fastapi", "uvicorn"]`
      y **el core sigue funcionando sin el extra**.
    - Exige una decision explicita del usuario (publicar un servicio = exponer
      codigo SQF de terceros).
    - Postura de privacidad obligatoria en `docs/PRIVACIDAD.md`: opt-in, sin
      datos persistentes, limite de tasa, clave de API, aviso explicito de que
      el codigo SQF sale de la maquina del usuario.
D.2 Deja en `docs/ESTADO-PR.md` una nota de "Track B HTTP: no implementado,
    decision pendiente del usuario" con los criterios que harian falta.

--------------------------------------------------------------------------------
PARTE E — DOCUMENTACION  [P0]
--------------------------------------------------------------------------------
E.1 `docs/MCP.md` (nuevo): que es, como se arranca, configuracion por host
    (Claude Desktop), lista de herramientas con su `inputSchema`, ejemplos de
    llamada, y la tabla de que se pierde sin MCP (todo lo que el modo pegado
    degrade a `NO VERIFICADO`).
E.2 `docs/PRIVACIDAD.md` (nuevo): postura de privacidad **por construccion**:
    todo local, sin red, sin persistencia del codigo del usuario, sin
    telemetria, sin claves de API. Y la nota de que la variante HTTP (si algún
    dia existe) tendria otra postura y requiere opt-in.
E.3 `docs/COMPATIBILIDAD.md`: la fila de Claude Desktop pasa a indicar el modo
    MCP por stdio disponible. Ojo: la columna de **estado de evidencia** sigue
    en `NO VERIFICADO` hasta que haya trazas reales en ese host (R5). No
    confundas "soporte tecnico disponible" con "calidad medida".
E.4 `README.md` + `INSTALL.md`: seccion corta de MCP (que es, cuando lo
    necesitas, cuando NO lo necesitas). Sin cambiar la insignia de calidad ni
    las cifras de la Parte E de PR-5-bis.
E.5 `docs/ESTADO-PR.md`: nueva seccion "PR-6 — Track B MCP" con el estado real
    de cada item (A, B, C, E) y que **la medicion no ha cambiado**.

--------------------------------------------------------------------------------
REGLAS INVIABLES
--------------------------------------------------------------------------------
R1. El Release Gate depende solo de validacion LOCAL.
R2. Ninguna definicion N3 fuera de `references/invariants.md`,
    `references/rubrica.md` y `references/sqf-standards.md`.
R3. Ningun artefacto de host enlaza a un fichero que ese host no pueda leer
    (ni a una opcion de CLI que no exista).
R4. Todo criterio tiene METRICA + METODO + ESTADO.
R5. "Igual calidad" solo es publicable con tabla por host respaldada por trazas.
R6. Lo normativo fuera del canonico es GENERADO y verificado por hash.

REGLAS DE TRABAJO:
  - NO toques `arma3-sqf-review\`. **NO hagas push. NO publiques nada.**
  - Solo biblioteca estandar de Python (>=3.11). **Ninguna dependencia nueva**
    en el camino principal (el MCP por stdio debe funcionar sin pip install).
  - Cero rutas absolutas en codigo **y en artefactos distribuibles**.
  - Un test SKIPPED en fase ya exigida = FALLO.
  - NO modifiques la Capa 0 (1.186/1.200, 14 tokens de margen) ni los canonicos.
  - NO toques `docs/QUALITY.md`, `evals/goldens/` ni las trazas: la medicion es
    de PR-5-bis y no se modifica en este hito.
  - NO escribas ninguna metrica a mano en ningun sitio.
  - NO inventes nombres de modelo ni de version.
  - NO borres `agents/`, `legacy/agents/` ni `plugin.json` (decision 1.o abierta).

--------------------------------------------------------------------------------
VERIFICACION ANTES DE CERRAR (obligatoria)
--------------------------------------------------------------------------------
    python -m pytest tests/ -q
    python scripts/check.py --fase PR-5     # no debe romperse
    python scripts/check.py --fase PR-6     # nuevo gate, en verde
    python -m ruff check .
    python evals/harness.py --check
    python scripts/generate_inline_packages.py --check
    python scripts/measure_tokens.py

Los siete en verde. Ademas:
  - `python skills/arma3-sqf-skill/scripts/sqf_orchestrator.py --serve-mcp`
    arranca y responde a un `initialize` por stdin.
  - `integrations/` sin ninguna ruta absoluta (el test lo bloquea).
  - `docs/QUALITY.md` y las cifras de `docs/ESTADO-PR.md` **sin cambios**.

--------------------------------------------------------------------------------
CRITERIOS DE ACEPTACION
--------------------------------------------------------------------------------
 1. `mcp_server.py` en stdlib puro, JSON-RPC 2.0 por stdio, con las 3
    herramientas y sin ningun log a stdout.
 2. `sqf_orchestrator.py --serve-mcp` existe y arranca: el snippet publicado
    deja de ser una promesa rota.
 3. `sqf_analyze` devuelve el informe v1 **byte a byte igual** al del motor.
 4. `integrations/claude/claude_desktop_config_snippet.json` sin rutas
    absolutas, JSON valido, con `SQF_WIKI_DATA_PATH` apuntando a un directorio
    de datos valido, y con test de contrato contra el CLI real.
 5. `resolve_wiki_root()` valida la ruta del env y cae a la precedencia normal
    si no es un directorio de datos valido (Defecto 3 cerrado en codigo, no
    solo en el snippet).
 6. `tests/test_mcp_server.py` con los 8 casos de C.1 en verde.
 7. `scripts/check.py --fase PR-6` en verde con 5 checks dirigidos.
 8. `docs/MCP.md`, `docs/PRIVACIDAD.md`, y sincronizados COMPATIBILIDAD /
    README / INSTALL / ESTADO-PR.
 9. Cero dependencias nuevas obligatorias; `dependencies = []` intacto.
 10. `--fase PR-5` sigue en verde y la medicion no ha cambiado.

Al terminar, informa: que herramientas expone y con que `inputSchema`, la
salida literal de los siete comandos, un ejemplo real de llamada MCP con su
respuesta, la lista de ficheros nuevos/tocados, y confirma que la medicion
(88,9 % / 7-14) sigue intacta. Si algo no se pudo hacer, dilo sin maquillarlo.

================================================================================
FIN DE LA INSTRUCCIÓN
================================================================================
