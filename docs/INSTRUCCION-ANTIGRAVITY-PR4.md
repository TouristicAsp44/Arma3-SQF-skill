================================================================================
INSTRUCCIÓN PARA ANTIGRAVITY — PR-4: Matriz de Compatibilidad y Adaptadores de Host
================================================================================
Copia este bloque completo en el chat de Antigravity, con la working directory
en la copia de trabajo:

    C:\Users\Touri\Documents\EDEN EDITOR\Skills Antigravity\arma3-sqf-skill

--------------------------------------------------------------------------------
CONTEXTO Y ESTADO (verificado hoy, no lo reestimes)
--------------------------------------------------------------------------------
Port del plugin Antigravity `arma3-sqf-review` a una skill portable
(Claude Code / Claude Desktop / Cursor / Codex / ChatGPT Custom GPT / Gemini).

- ORIGINAL (SOLO LECTURA, NO TOCAR NUNCA):
  `C:\Users\Touri\Documents\EDEN EDITOR\Skills Antigravity\arma3-sqf-review\`
- TRABAJO: `C:\Users\Touri\Documents\EDEN EDITOR\Skills Antigravity\arma3-sqf-skill\`
- PR-1, PR-2 y PR-3: CERRADOS Y EN VERDE.
  `python scripts/check.py --fase PR-3` → exit 0 · 75/75 tests verdes ·
  `ruff check .` limpio · DB `~/.a3ref/arma3_wiki.db` (58,42 MB, fts_enabled=1,
  dataset_sha 537907f6…, git_sha 2c396002…).
- Tokens: frontmatter 184/250 · **Capa 0 1.186/1.200** · turno máx 1.666/2.500.

LO QUE YA EXISTE Y DEBES REUTILIZAR (no lo reescribas):
- Núcleo: `skills/arma3-sqf-skill/SKILL.md` (Capa 0, 4 intenciones, índice N1
  de las 7 categorías, puerta, honestidad, triage de modo, activación de
  lentes/flujos, formato del informe, perfil de 7 parámetros).
- Canónicos: `references/invariants.md` (CANON:BLOQUEANTES, PUERTA, HONESTIDAD,
  MODOS, PRECEDENCIA, PROPIEDAD + **bloque "Paquete Inline P1–P4"**),
  `references/rubrica.md`, `references/sqf-standards.md`.
- 6 lentes en `references/lenses/`, 5 workflows en `references/workflows/`,
  `references/report_format.md`, `references/checklist-entrega.md`,
  `references/diferencial-misiones-addons.md`, `references/wiki-cache.md`.
- Motor: `skills/arma3-sqf-skill/scripts/` (sqf_orchestrator.py, sqf_models.py,
  sqf_wiki_reader.py, wiki_db_builder.py, fake_linter.py, sync_wiki_cache.py).
- Tooling: `scripts/check.py` (gate por fases), `scripts/measure_tokens.py`,
  `scripts/generated.lock.json`.
- NO existen todavía: `integrations/` ni `evals/`. Este PR los crea.

OBJETIVO DEL PR-4:
  Que la skill sea instalable y utilizable TAL CUAL en cada host soportado,
  con un artefacto por host, la matriz de degradación por host y los smoke
  tests ejecutados con evidencia (trazas) reproducibles.

--------------------------------------------------------------------------------
REGLAS INVARIABLES (NO NEGOCIABLES)
--------------------------------------------------------------------------------
R1. El Release Gate depende solo de validación LOCAL; los hosts externos pueden
    quedar `NO VERIFICADO` sin bloquear la publicación.
R2. Una única fuente canónica por regla. Ninguna definición N3 fuera de
    `references/invariants.md`, `references/rubrica.md` y
    `references/sqf-standards.md`. Este PR NO escribe ninguna regla nueva.
R3. NINGÚN artefacto de host puede enlazar a un fichero que ese host no pueda
    leer. Si no puede leerlo, va INLINE (paquete P1–P4). Esto es verificable y
    va con test.
R4. Todo criterio de aceptación tiene MÉTRICA + MÉTODO + ESTADO.
R5. "Igual calidad" solo es publicable con tabla por host (modelo, versión, N).
R6. El texto normativo fuera del canónico es GENERADO y verificado por hash por
    regiones: bloque `<!-- AUTHORED -->` + región `<!-- CANON-EXTRACT:X -->`.
    Todo artefacto GENERATED lleva cabecera
    `<!-- GENERATED FROM: … | DO NOT EDIT -->` y su hash vive en un lock file.

REGLAS DE TRABAJO:
  - NO toques `arma3-sqf-review\`.
  - NO hagas push a GitHub ni publiques nada.
  - Solo biblioteca estándar de Python (>=3.11). Ninguna dependencia nueva.
  - Cero rutas absolutas: solo `Path(__file__)`, env vars declaradas o CLI.
  - Un test SKIPPED en fase ya exigida = FALLO.
  - NO modifiques la Capa 0 sin margen: solo queda 14 tokens de holgura.

--------------------------------------------------------------------------------
CONVENCIÓN DE RUTAS (debe quedar explícita en los artefactos)
--------------------------------------------------------------------------------
Todas las rutas dentro de la skill son RELATIVAS A LA RAÍZ DE LA SKILL, es
decir `skills/arma3-sqf-skill/`. Ejemplos válidos dentro de un artefacto:
  `references/lenses/locality.md`
  `scripts/sqf_orchestrator.py --lint <archivo>`
  `references/invariants.md`
Esto vale para Claude Code (que instala la carpeta de la skill), Cursor
(reglas con rutas al repo), Codex/AGENTS.md y los artefactos pegados.

--------------------------------------------------------------------------------
TAREAS DE PR-4
--------------------------------------------------------------------------------
4.a  GENERADOR DEL PAQUETE INLINE P1–P4  (pieza nueva y crítica)
     `scripts/generate_inline_packages.py` — solo biblioteca estándar.
     Lee `skills/arma3-sqf-skill/references/invariants.md` (bloque P1–P4) y
     genera los tres artefactos degradados:
       integrations/chatgpt/custom_gpt_instructions.md
       integrations/gemini/system_instruction.md
       integrations/claude/claude_desktop_paste.md
     REQUISITOS:
       - Los tres comparten EXACTAMENTE el mismo núcleo P1–P4 (mismo contenido
         normativo); solo cambia la cabecera/preámbulo específico del host.
       - Límite duro: ≤ 8.000 CHARACTERES por artefacto (el límite real de
         ChatGPT es de caracteres, no de tokens). Si el paquete no cabe:
         recorta P3 (checklist) NUNCA P1, P2 ni P4. El generador DEBE FALLAR
         con exit code 1 si aun así se supera el límite.
       - P1 incluye obligatoriamente: índice N1 de las 7 categorías + regla de
         puerta + principio de honestidad. P2: fallback de modo
         (`Estándar + NO VERIFICADO`, prohibido Micro manual). P3: checklist
         priorizado por ítem (N2). P4: formato del informe v1 en una línea.
       - Determinista: mismo canónico → mismo byte. Sin timestamps.
       - Cabecera `<!-- GENERATED FROM: skills/arma3-sqf-skill/references/invariants.md | DO NOT EDIT -->`
         + hash del contenido fuente, y verificación por hash en el lock file
         `scripts/generated.lock.json` (misma sección `generated`/mismo
         mecanismo por regiones que las lentes; si el lock actual no lo
         soporta, añade la clave que corresponda y actualiza
         `tests/test_generated_files_hash.py` en consecuencia).
       - CLI: `--check` (verifica sin escribir, exit 1 si hay divergencia) y
         `--write` (regenera). El gate debe usar `--check`.

4.b  ADAPTADORES POR HOST (artefactos reales, instalables)
     integrations/claude/
       - CLAUDE.md                     → GENERATED: región CANON-EXTRACT +
                                         bloque AUTHORED "cómo usar en Claude Code"
       - claude_desktop_config_snippet.json → instalable REAL, con campo
                                         `command`, `args`, `cwd` y `env`
                                         (`SQF_WIKI_DATA_PATH`, `SQF_WIKI_DB_PATH`),
                                         con variantes Windows (ruta real) y POSIX.
                                         NUNCA pseudocódigo tipo "/ruta/a/tu/…".
       - claude_desktop_paste.md       → GENERATED (paquete inline P1–P4)
       - install.md                    → procedimiento + comando de verificación
     integrations/cursor/
       - .cursorrules (o rules/)       → reglas con rutas al repo y disparadores
       - install.md
     integrations/openai/
       - AGENTS.md                     → instrucciones Codex / OpenAI CLI
       - install.md
     integrations/chatgpt/
       - custom_gpt_instructions.md    → GENERATED (4.a)
       - knowledge_manifest.md         → qué ficheros subir, con CRITERIO DE
                                         SELECCIÓN explícito y **≤ 20 ficheros**
                                         (límite de ficheros por GPT: VERIFICA el
                                         valor vigente antes de fijarlo).
                                         `wiki-cache.md` NO se sube completo: solo
                                         un subconjunto curado. Declara el conteo
                                         y el motivo de cada exclusión.
       - install.md
     integrations/gemini/
       - system_instruction.md         → GENERATED (4.a)
       - install.md
     integrations/common/
       - skill-layout.md               → estructura final esperada de la skill
                                         por host + convención de rutas + qué
                                         fichero se copia a qué destino.

4.c  MATRIZ DE COMPATIBILIDAD Y DEGRADACIÓN (documento nuevo)
     `docs/COMPATIBILIDAD.md` con una fila por host y estas columnas:
       Host | Mecanismo | Lectura de archivos | Soporte | Qué se pierde |
       Límite | Compensación (fichero + mecanismo) | Fallback de modo
     Reglas que DEBEN quedar reflejadas:
       - Claude Code: completo; lee `references/` bajo demanda.
       - Claude Desktop: parcial; sin MCP (Track B) usa el artefacto pegado;
         con MCP usaría el servidor de PR-6.
       - Cursor: parcial; sin subagentes multi-paso; las lentes se cargan como
         reglas adicionales.
       - Codex/OpenAI CLI: parcial; `AGENTS.md` con checklist condensado inline.
       - ChatGPT Custom GPT: degradado; Knowledge = RAG (inyección NO
         determinista); pierde modo archivo y Cat. 4/5/7 → `NO VERIFICADO`.
       - Gemini/AI Studio: degradado; system instruction en texto plano.
       - En TODOS los hosts degradados: fallback de modo = `Estándar +
         NO VERIFICADO`; prohibido conceder `Micro` por criterio manual.
     Enlaza esta matriz desde el README. NO la dupliques dentro de la Capa 0.

4.d  SMOKE TESTS S1–S3 CON EVIDENCIA (Claude Code, modo archivo)
     Material de prueba en `evals/smoke/`:
       - S1: variable sin `private` + `waitUntil` sin salida garantizada
              → Cat. 1 + Cat. 2 = 2 BLOQUEANTE
       - S2: `player` en `init.sqf` + `hint` en ruta de servidor (con y sin
              guarda `hasInterface`; la guarda NO legitima)
              → Cat. 3 + Cat. 4 = 2 BLOQUEANTE
       - S3: `remoteExec` a función ausente del whitelist `CfgRemoteExec`
              (mode = 1) + uso de `CBA_fnc_*` con perfil declarado `CBA: no`
              → Cat. 5 + Cat. 7 = 2 BLOQUEANTE
     S3 necesita material de apoyo: un proyecto fixture con `description.ext`
     (CfgRemoteExec) y un perfil declarado, porque Cat. 5 y Cat. 7 NO son
     verificables sin ese contexto.
     Ejecución y trazas:
       - Ejecuta los 3 casos en Claude Code (modo archivo).
       - Guarda la traza en `evals/runs/<fecha>/claude-code/<caso>.json` con:
         prompt enviado, respuesta cruda, modelo, versión, temperatura,
         veredicto por hallazgo y `contexto_cargado` (ficheros leídos + hash).
       - `evals/runs/` está en `.gitignore`: lo que se versiona es la tabla
         resumida, no las trazas.
     Métrica (fíjala así, es la que ya está en el plan):
       - "esperables resueltos" = DETECTADO + NO_VERIFICADO justificado.
       - Veredictos del matcher: `DETECTADO`, `NO_VERIFICADO`, `SILENCIO`
         (no cuenta) y `FALSO_PASA` (falta crítica).
       - Objetivo en modo archivo: 6/6 esperables resueltos, 0 `FALSO_PASA`.
       - Tabla de resultados: host × caso × categoría, con modelo y versión.
       - Si no puedes ejecutar Claude Code en este entorno, la fila queda
         `NO VERIFICADO` con motivo (R1) — NO lo marques verde.

4.e  TESTS
     `tests/test_inline_packages.py`:
       - los 3 artefactos inline existen y contienen P1, P2, P3 y P4
       - los 3 miden ≤ 8.000 caracteres
       - su núcleo normativo es idéntico entre los 3 (hash de la sección P1–P4)
       - `--check` del generador pasa (no hay divergencia)
       - regenerar dos veces produce el mismo hash (determinismo)
     `tests/test_host_adapters.py`:
       - cada host tiene su artefacto y su `install.md`
       - NINGÚN artefacto de host enlaza a un fichero que ese host no pueda
         leer (comprueba la regla R3 host por host)
       - el snippet de Claude Desktop es JSON válido con `command`, `args`,
         `cwd` y `env`; y no contiene pseudocódigo ("/ruta/a/…", "<…>")
       - `knowledge_manifest.md` declara ≤ 20 ficheros y un criterio de
         selección; no incluye el `wiki-cache.md` completo
       - la matriz de `docs/COMPATIBILIDAD.md` cubre los 6 hosts con todas las
         columnas y el fallback de modo
     Mantén `tests/test_generated_files_hash.py` coherente con el nuevo lock.

4.f  GATE
     Añade a `scripts/check.py` dos checks dirigidos, ambos con
     `skip_is_failure=True` y fase de exigencia **PR-4**:
       - "paquetes inline"  → tests/test_inline_packages.py
       - "adaptadores host"  → tests/test_host_adapters.py
     `python scripts/check.py --fase PR-4` → exit 0.

4.g  DOCUMENTACIÓN
     `INSTALL.md`: una sección por host (Claude Code, Claude Desktop, Cursor,
     Codex, ChatGPT Custom GPT, Gemini) con el procedimiento de instalación y
     el comando de verificación. Añade la nota de que la base de conocimiento
     SQLite es opcional y de que el paquete inline P1–P4 es lo que permite
     trabajar en hosts sin lectura de archivos.
     `README.md`: quickstart por host + enlace a `docs/COMPATIBILIDAD.md` y a
     `docs/QUALITY.md` (este último se crea en PR-5; enlázalo como previsto).
     `docs/ESTADO-PR.md`: sección PR-3 completada (métricas medidas: latencia
     JSON 59,5 ms vs DB 0,456 ms en lookup_syntax_symbol; 187,3 ms vs 0,358 ms
     en get_topic; DB 58,42 MB vs 35,44 MB de JSON; build 1,132 s) y sección
     PR-4 en curso.
     `docs/PARIDAD.md`: actualiza los ítems afectados por los adaptadores.

--------------------------------------------------------------------------------
VERIFICACIÓN ANTES DE CERRAR (obligatoria)
--------------------------------------------------------------------------------
    python3 -m pytest tests/ -q
    python3 scripts/check.py --fase PR-4
    python3 -m ruff check .
    python3 scripts/generate_inline_packages.py --check
    python3 scripts/measure_tokens.py

Los cinco en verde. `check.py --fase PR-4` DEBE devolver exit 0.

--------------------------------------------------------------------------------
LO QUE NO DEBES HACER
--------------------------------------------------------------------------------
- No toques `arma3-sqf-review\`.
- No hagas push a GitHub ni publiques nada.
- No modifiques la Capa 0 (1.186/1.200, 14 tokens de margen) ni los canónicos.
- No escribas a mano el contenido de los artefactos GENERATED: se generan.
- No superes 8.000 caracteres en un artefacto inline ni subas `wiki-cache.md`
  completo al Knowledge de ChatGPT.
- No enlaces desde un artefacto de host a ficheros que ese host no pueda leer.
- No inventes URLs, procedencias ni resultados de smoke test: si no se pudo
  ejecutar, `NO VERIFICADO` con motivo.
- No borres `agents\` ni `legacy\agents\` (decisión abierta, tarea 1.o; sin git).
- No añadas dependencias ni rutas absolutas.

--------------------------------------------------------------------------------
CRITERIOS DE ACEPTACIÓN
--------------------------------------------------------------------------------
 1. `check.py --fase PR-4` en verde (exit 0), 0 tests omitidos.
 2. 3 artefactos inline GENERADOS, ≤ 8.000 caracteres, con P1–P4 completos y
    núcleo idéntico entre ellos.
 3. 6 artefactos de host + `install.md` por host + `knowledge_manifest.md` con
    ≤ 20 ficheros y criterio de selección.
 4. `docs/COMPATIBILIDAD.md` con los 6 hosts, todas las columnas y el fallback
    de modo.
 5. Smoke tests S1–S3 ejecutados en Claude Code con trazas y tabla de
    veredictos por categoría (o `NO VERIFICADO` con motivo si no fue posible).
 6. Tests de paquetes inline y de adaptadores en verde.
 7. `INSTALL.md` y `README.md` con sección por host.
 8. `docs/ESTADO-PR.md` y `docs/PARIDAD.md` actualizados.

Al terminar, informa: qué cambiaste, la salida literal de los cinco comandos,
los caracteres medidos de cada artefacto inline, la tabla de smoke tests
(host × caso × categoría con modelo y versión), y cualquier desviación.

================================================================================
FIN DE LA INSTRUCCIÓN
================================================================================
