================================================================================
INSTRUCCIÓN PARA ANTIGRAVITY — PR-3: Base de Conocimiento (Wiki SQLite / FTS)
================================================================================
Copia este bloque completo en el chat de Antigravity, con la working directory
en la copia de trabajo:

    C:\Users\Touri\Documents\EDEN EDITOR\Skills Antigravity\arma3-sqf-skill

--------------------------------------------------------------------------------
CONTEXTO Y ESTADO (verificado, no lo reestimes)
--------------------------------------------------------------------------------
Seguimos el port del plugin Antigravity `arma3-sqf-review` a una skill
portable (Claude Code / Cursor / Codex / ChatGPT / Gemini).

- ORIGINAL (SOLO LECTURA, NO TOCAR NUNCA):
  `C:\Users\Touri\Documents\EDEN EDITOR\Skills Antigravity\arma3-sqf-review\`
- TRABAJO: `C:\Users\Touri\Documents\EDEN EDITOR\Skills Antigravity\arma3-sqf-skill\`
- PR-1 y PR-2: CERRADOS Y EN VERDE.
  `python scripts/check.py --fase PR-2` → exit 0, 64/64 tests en verde,
  0 omitidos. `ruff check .` limpio.
- Tokens medidos: frontmatter 184/250 · Capa 0 **1.186/1.200** · turno máx
  1.666/2.500 · lente más larga 480 (performance.md).

ESTADO REAL DE LA RÉPLICA a3ref EN ESTA MÁQUINA (verificado):
  `C:\Users\Touri\.a3ref\data\`  →  commands.json 4,5 MB · functions.json 2,4 MB ·
  index.json 2,2 MB · syntax.json 543 KB · **topics.json 27,5 MB** · schema.json 22 KB
  dataset updated = 2026-11-04T21:31:31Z · commands count=2657 · functions count=2062
  index count=5394 · topics count=675

PROBLEMA QUE RESUELVE ESTE PR:
  Hoy `sqf_wiki_reader.py` carga commands+functions+index+ syntax en memoria
  (~10 MB parseados) y para cada consulta de topic **reparsea topics.json
  entero (27,5 MB) y llama a `gc.collect()`**. Eso hace que la verificación
  BIKI — que es la fuente primaria obligatoria según
  `references/invariants.md` — sea lenta y frágil en cualquier host que no
  tenga la réplica clonada.

OBJETIVO DEL PR-3:
  Construir una base de conocimiento SQLite con FTS5 sobre la réplica a3ref,
  de modo que la verificación BIKI sea (a) una consulta de milisegundos,
  (b) un único fichero distribuible, y (c) reproducible con la misma
  procedencia (URL + revid + SHA del dataset) que exige el canónico.

--------------------------------------------------------------------------------
REGLAS INVARIABLES (NO NEGOCIABLES)
--------------------------------------------------------------------------------
R1. El Release Gate solo depende de validación LOCAL.
R2. Una única fuente canónica por regla. Las definiciones N3 solo viven en
    `references/invariants.md`, `references/rubrica.md` y
    `references/sqf-standards.md`. Este PR NO redefine ninguna regla.
R3. Ningún artefacto puede enlazar a un fichero que su host no pueda leer.
R4. Todo criterio de aceptación tiene MÉTRICA + MÉTODO + ESTADO.
R5. "Igual calidad" solo es publicable con tabla por host (modelo, versión, N=3).
R6. El texto normativo fuera del canónico es GENERADO y verificado por hash.

REGLAS DE TRABAJO:
  - NO toques `arma3-sqf-review\`.
  - NO hagas push a GitHub ni publiques nada.
  - `skills/arma3-sqf-skill/scripts/` usa SOLO biblioteca estándar de Python
    (>=3.11). `sqlite3` es de la estándar: vale. Ninguna dependencia nueva.
  - Ninguna ruta absoluta: solo `Path(__file__)`, variables de entorno
    declaradas o argumentos de CLI (lo verifica `tests/test_no_absolute_paths.py`,
    que escanea el runtime).
  - Un test SKIPPED en una fase ya exigida = FALLO, no verde.

--------------------------------------------------------------------------------
MARGEN CRÍTICO DE TOKENS
--------------------------------------------------------------------------------
La Capa 0 está en **1.186 de 1.200 tokens**: solo quedan 14 de margen. NO
añadas nada a `SKILL.md` Capa 0 en este PR salvo que elimines el equivalente.
La documentación del DB va en `references/lenses/claims.md` (se carga bajo
demanda, no cuenta para Capa 0) y en `INSTALL.md` / `README.md`.

--------------------------------------------------------------------------------
TAREAS DE PR-3
--------------------------------------------------------------------------------
3.a  CONTRATO DE DATOS (no lo inventes: está en el JSON real)
     Fuente: `~/.a3ref/data/*.json`, formato v2 documentado en `schema.json`.
     - `commands.json` / `functions.json`: {updated, source, count, items[]}
       con items tipo {name, title, type, url, revid, updated, groups[],
       status, games{}, since, arma3_since, description, operator,
       syntaxes[{syntax, params[], returns}], aliases[]}
       (commands count=2657, functions count=2062)
     - `index.json`: {updated, count, items[]} con {name, type, md, json,
       groups[], syntax[], summary, arma3_since, locality{argument, effect,
       server_exec}, status, operator, aliases[]} (count=5394)
     - `syntax.json`: {updated, commands{}, functions{}} con
       {name, forms[], status, syntax[], operator}
     - `topics.json`: {updated, source, count, items[]} con {name, title, type,
       url, revid, updated, aliases[], markdown} (count=675, 27,5 MB: el peso
       está en `markdown`)
     Escribe este contrato en `docs/WIKI-DB.md` (esquema de tablas + campos de
     procedencia) antes de escribir código.

3.b  CONSTRUCTOR: `skills/arma3-sqf-skill/scripts/wiki_db_builder.py`
     Solo biblioteca estándar. Subcomandos:
       build   --data <dir> --out <fichero.db> [--no-fts] [--jobs N]
       stats   --db <fichero.db>
       verify  --db <fichero.db> --data <dir>     (paridad DB vs JSON)
       query   --db <fichero.db> --command <nombre> | --function <nombre>
              | --topic <título> | --search <texto>
     Esquema SQLite mínimo y suficiente:
       commands(name PK, name_lower UNIQUE, title, type, url, revid, updated,
                status, groups_json, games_json, since, arma3_since,
                description, operator, syntaxes_json, aliases_json, doc_json)
       functions(ídem)
       topics(title PK, title_lower, name, type, url, revid, updated,
              aliases_json, markdown, doc_json)
       symbols(key PK, kind, name, forms_json, status, syntax_json, operator)
       index_items(name_lower, name, type, md, json, groups_json, syntax_json,
                   summary, arma3_since, locality_json, status, operator,
                   aliases_json)
       meta(key PK, value)   → schema_version, dataset_updated, dataset_sha,
                              dataset_git_sha, built_at, counts_*, fts_enabled
     FTS5: tabla virtual `wiki_fts` sobre (kind, name, title, summary,
     description, syntax, groups). NO indexes el `markdown` completo de topics
     (es el 27,5 MB): el topic se busca por título/alias y, si hace falta,
     por LIKE sobre markdown. Justifica el tamaño y la latencia en
     `docs/WIKI-DB.md`.
     DETERMINISMO:Inserción ordenada (name/title asc), `PRAGMA` fijo y `VACUUM` al
     final. Dos builds sobre el mismo dataset deben dar el MISMO digest de
     contenido (calcula un digest de filas, no del fichero: SQLite puede
     variar en bytes). Test de esto.

3.c  DEGRADACIÓN HONESTA SI NO HAY FTS5
     Detecta FTS5 en runtime:
       sqlite3.connect(":memory:").execute("CREATE VIRTUAL TABLE t USING fts5(x)")
     Si no está disponible: construye SIN FTS, deja `meta.fts_enabled=0` y el
     `search` cae a LIKE. La búsqueda degrada, el resto de la DB funciona.
     Esto NO es un bug: documéntalo. Añade `--no-fts` para poder probar la
     ruta sin FTS de forma determinista.

3.d  INTEGRACIÓN CON `sqf_wiki_reader.py` (sin romper CI)
     Precedencia de resolución de la DB:
       1) `--db-path` (CLI)
       2) `SQF_WIKI_DB_PATH` (env var)
       3) `Path.home()/".a3ref"/"arma3_wiki.db"` (instalación por defecto)
       4) SIN DB → la ruta JSON actual (comportamiento de hoy, CI incluido)
     Si la DB existe y es válida, `get_command`, `get_function`, `get_topic`,
     `lookup_syntax_symbol`, `get_data_git_sha` y
     `get_dataset_updated_timestamp` responden DESDE LA DB y devuelven
     EXACTAMENTE las mismas claves y valores que hoy (canonical_name, status,
     version, replaced_by, url, type). Cero cambios aguas abajo.
     La CI actual clona `a3ref/data` como JSON y NO tiene DB: ese camino debe
     seguir funcionando intacto. La DB es una ACELERACIÓN y una forma de
     distribución, no un reemplazo obligatorio.

3.e  PROCEDENCIA (obligatoria por `references/invariants.md`)
     La DB debe poder devolver, por entrada: url oficial, revid, versión
     (arma3_since/since) y estado (ok / deprecated / broken / replaced_by),
     más el SHA del dataset y su timestamp `updated`. El lector debe exponerlos
     con la DB activa igual que con JSON. Un item sin url en el snapshot sigue
     siendo `NO_VERIFICADO: url ausente en snapshot` — no inventes URLs.

3.f  DISTRIBUCIÓN
     El `.db` NO se versiona ni se empaqueta: añádelo a `.gitignore` y a
     `MANIFEST.in` (prune). Tamaño esperado:decenas de MB; si el fichero supera un
     umbral razonable (p. ej. 60 MB), reduce el alcance (por ejemplo, topics
     sin FTS sobre markdown) y documenta la decisión.
     `INSTALL.md`: sección "Base de conocimiento SQLite (opcional)" con el
     comando de build, la env var y el hecho de que es opcional.
     `README.md`: "Lo que NO incluye esta skill" → matizar que la DB es
     opcional y construible localmente.

3.g  TESTS: `tests/test_wiki_db.py` (CI-friendly, SIN la réplica de 30 MB)
     Crea un dataset sintético mínimo en `tests/fixtures/wiki_mini/` con
     3 comandos, 2 functions, 1 topic, `syntax.json` e `index.json`.
     Tests:
       - build produce DB con las tablas y los conteos esperados
       - lookup por DB == lookup por JSON para TODOS los items del mini dataset
         (paridad campo a campo)
       - búsqueda FTS devuelve los hits esperados (y la ruta LIKE cuando
         `--no-fts`)
       - determinismo: dos builds → mismo digest de contenido
       - fallback: sin DB, el lector JSON sigue funcionando
       - `meta` contiene dataset_sha / dataset_updated / fts_enabled
       - el lector con DB devuelve la MISMA procedencia (url, revid, versión)

3.h  MEDICIÓN (métrica y método, R4)
     Mide y documenta en `docs/WIKI-DB.md`:
       - latencia mediana de `lookup_syntax_symbol` y `get_topic`: JSON vs DB
         (medir sobre la réplica real de esta máquina, N=50)
       - tamaño en disco de la DB frente al tamaño total de los JSON
       - tiempo de construcción de la DB
     NO prometas "más pequeño" sin medirlo: el objetivo declarado es
     LATENCIA y DISTRIBUICIÓN, no tamaño.

3.i  GATE
     Añade a `scripts/check.py` un check dirigido "base de conocimiento SQLite"
     → `tests/test_wiki_db.py`, con fase de exigencia **PR-3** y
     `skip_is_failure=True`.
     `python scripts/check.py --fase PR-3` debe salir en verde (exit 0).

3.j  DOCUMENTACIÓN
     `docs/ESTADO-PR.md`: sección PR-3 con el estado por tarea y las métricas
     medidas. `docs/PARIDAD.md`: actualiza el ítem 16 (regla de verificación
     wiki) y añade el artefacto de DB en la columna correspondiente.
     `references/lenses/claims.md`: en su bloque AUTHORED, documenta el camino
     rápido por DB (una frase, sin tocar el presupuesto de Capa 0). Si lo
     editas, regenera `scripts/generated.lock.json` con el hash AUTHORED
     actualizado (el test de regiones lo exige).

--------------------------------------------------------------------------------
VERIFICACIÓN ANTES DE CERRAR (obligatoria)
--------------------------------------------------------------------------------
    python3 -m pytest tests/ -q
    python3 scripts/check.py --fase PR-3
    python3 -m ruff check .
    python3 skills/arma3-sqf-skill/scripts/wiki_db_builder.py stats --db "<tu .db>"

Los cuatro en verde. `check.py --fase PR-3` DEBE devolver exit 0.

--------------------------------------------------------------------------------
LO QUE NO DEBES HACER
--------------------------------------------------------------------------------
- No toques `arma3-sqf-review\`.
- No hagas push a GitHub ni publiques nada (ni el .db).
- No versionees el fichero .db ni los datos de la réplica.
- No añadas dependencias al motor: solo biblioteca estándar.
- No reescribas la Capa 0 sin margen: solo queda 14 tokens de holgura.
- No rompas la ruta JSON del lector: la CI actual no tiene DB y debe seguir
  verde.
- No inventes URLs ni procedencias que no estén en el snapshot: si un campo
  falta, `NO VERIFICADO`.
- No borres `agents\` ni `legacy\agents\` (decisión abierta, tarea 1.o; sin git).

--------------------------------------------------------------------------------
CRITERIOS DE ACEPTACIÓN
--------------------------------------------------------------------------------
 1. `check.py --fase PR-3` en verde (exit 0), 0 tests omitidos.
 2. DB construida desde la réplica real con las 5 tablas + `meta` + FTS.
 3. Paridad campo a campo DB↔JSON verificada en test con dataset sintético.
 4. El lector usa la DB si existe y el JSON si no, con respuestas idénticas.
 5. Procedencia (url, revid, versión, status, replaced_by) conservada.
 6. Latencia medida y documentada (JSON vs DB) sobre la réplica real.
 7. El `.db` fuera de Git y del paquete; `INSTALL.md` y `README.md` actualizados.
 8. `docs/ESTADO-PR.md` y `docs/PARIDAD.md` actualizados.

Al terminar, informa: qué cambiaste, la salida literal de los cuatro comandos,
las métricas medidas (latencia JSON vs DB, tamaño DB vs JSON, tiempo de build),
el tamaño y contenido de la tabla `meta`, y cualquier desviación respecto al
plan.

================================================================================
FIN DE LA INSTRUCCIÓN
================================================================================
