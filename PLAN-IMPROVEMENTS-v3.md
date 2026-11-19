================================================================================
INSTRUCCIONES PARA MEJORAR, ACTUALIZAR Y OPTIMIZAR LA PLANEACIÓN (v2.1 → v2.2)
================================================================================

CONTEXTO: el Plan v2.1 ya cerró prácticamente todo lo abierto en las revisiones
previas (R1–R5, fuente canónica, mapeo de los 11 agentes, tabla de degradación
por host, smoke tests alineados a las 7 categorías, scripts/check.py, goldens
con N=3 y negativos, tool compuesta sqf_review, contrato de seguridad del
endpoint, CI workflow, DoD en 13 filas, riesgos reencuadrados).
NO se repiten esas correcciones.

Lo que sigue son los 19 puntos que QUEDAN abiertos en v2.1. Tres de ellos
(1, 6 y 7) son bloqueantes en sentido literal: con el plan tal como está,
el CI fallaría, o se perdería contenido normativo, o se rompería una
funcionalidad que hoy funciona en tu máquina.

Hallazgos verificados leyendo el repositorio (no inferidos):
  - `pyproject.toml` declara `requires-python = ">=3.11"` y `target-version = "py311"`.
  - `sqf_wiki_reader.py` resuelve hoy el dataset por 5 rutas candidatas
    (`plugin_root.parent/"Wiki"/"data"`, `plugin_root.parent/"wiki"/"data"`,
    `plugin_root/"data"`, `Path.home()/".a3ref"/"data"`, `Path.home()/".gemini"/"wiki"/"data"`)
    y expone `--wiki-path` por CLI.
  - `skills/arma3-sqf-review/references/` contiene `sqf-standards.md`,
    `wiki-cache.md`, `diferencial-misiones-addons.md` y `checklist-entrega.md`.
  - Las 7 categorías de BLOQUEANTE y la Puerta de Calidad viven hoy en el
    `SKILL.md` actual (Paso 7), NO en `rules/AGENTS.md` ni en `sqf-standards.md`.

================================================================================
PARTE A — CONTRADICCIONES Y HUECOS BLOQUEANTES
================================================================================

A.1 EL PLAN FALLA SU PROPIO CI: 2.b EXIGE LO QUE 2.k PROHÍBE (gravedad: BLOQUEANTE)
--------------------------------------------------------------------------------
2.b exige que la Capa 0 contenga el "índice de las 7 categorías de BLOQUEANTE
(una línea cada una, ~150 tokens)".
2.k y DoD #6 exigen que las 7 categorías "aparezcan SOLO en `invariants.md` y
no en `SKILL.md`, `checklist_static.md` ni en ninguna lente".
Ambos requisitos son incompatibles: la Capa 0 está dentro de `SKILL.md`.
Tal como está escrito, `scripts/check.py` fallaría en PR-2 aunque el trabajo
sea correcto.
CORRECCIÓN: el test de unicidad debe distinguir DOS niveles:
  - DEFINICIÓN NORMATIVA (categoría + descripción completa + condiciones +
    excepciones): PROHIBIDA fuera de `references/invariants.md`.
  - ÍNDICE (una línea por categoría, ≤ 25 tokens cada una): PERMITIDO y
    OBLIGATORIO en Capa 0, y también permitido en las copias inline de los
    hosts degradados (R3).
El test se implementa así:
  - Fase 1: ancla `<!-- CANON:BLOQUEANTES -->` … `<!-- /CANON:BLOQUEANTES -->`
    en `invariants.md`. Ningún otro archivo puede contener el ancla.
  - Fase 2: en los demás archivos, se comprueba que no aparecen las
    definiciones normativas (patrones de las 7 categorías con su detalle),
    y que el número de menciones de índice en Capa 0 es exactamente 7 y cada
    una ≤ 25 tokens.
Aplica lo mismo a la Puerta de Calidad y al principio de honestidad.

A.2 LAS 7 CATEGORÍAS DESAPARECEN ENTRE PR-1 Y PR-2 (gravedad: BLOQUEANTE)
--------------------------------------------------------------------------------
Hecho verificado: las 7 categorías de Bloqueante y la Puerta de Calidad están
en el `SKILL.md` ACTUAL (Paso 7). `rules/AGENTS.md` solo tiene invariantes
generales; `sqf-standards.md` tiene estándar de código.
El plan: 1.f convierte AGENTS.md → `invariants.md`; 1.g absorbe
`sqf-standards.md`; 2.c "redactar `references/invariants.md`"; 2.a/2.b
REESCRIBEN el `SKILL.md`.
Consecuencia: en PR-1 el canónico no contiene las 7 categorías (nadie las
migra); en PR-2 el `SKILL.md` viejo se sobrescribe (y con él, las 7
categorías). Hay un instante en que la fuente canónica de la norma más
importante del plugin NO EXISTE en el repo, y el test de unicidad de PR-1
no tiene contra qué compararse.
CORRECCIÓN: añadir en PR-1 la tarea **1.g-bis** (nueva):
  "Migrar literalmente del `SKILL.md` actual a `references/invariants.md`:
   las 7 categorías normativas de BLOQUEANTE, la Puerta de Calidad
   Infranqueable, el principio de honestidad técnica, la rúbrica de severidad
   y la matriz de participación por modo. Sin este bloque, PR-2 sobrescribe el
   `SKILL.md` y la norma desaparece."
Y ajustar PR-2 2.c a "COMPLETAR/INDEXAR `invariants.md` (ya migrado en 1.g-bis),
  no redactar desde cero".
Corolario: DoD #6 pasa a "ancla CANON:BLOQUEANTES única en invariants.md".

A.3 LA TAREA 1.c ROMPE UNA FUNCIONALIDAD QUE HOY FUNCIONA (gravedad: BLOQUEANTE)
--------------------------------------------------------------------------------
1.c propone sustituir la resolución de rutas por:
  `SQF_WIKI_DATA_PATH` con fallback a `Path(__file__).parent.parent / "data"`.
Pero el código actual (verificado) ya resuelve por 5 rutas candidatas, entre
las que `Path.home()/".a3ref"/"data"` y `Path.home()/".gemini"/"wiki"/"data"`
— rutas que SÍ funcionan hoy en tu máquina y en la de otros usuarios con a3ref
instalado. Sustituir la lista por un único fallback ROMPE la detección de la
réplica a3ref para cualquiera que no la tenga dentro del paquete.
CORRECCIÓN (1.c reescrito): ORDEN DE PRECEDENCIA, sin eliminar nada:
  1) `--wiki-path` (CLI, ya existe)
  2) `SQF_WIKI_DATA_PATH` (env var)
  3) la lista actual de 5 candidatas, INCLUYENDO `Path.home()/".a3ref"/"data"`
  4) `Path(__file__).parent.parent/"data"` (fallback empaquetado)
El test de rutas absolutas (1.d) debe EXCLUIR `Path.home()` cuando aparece
como parte de una lista de candidatos declarados, o definir una lista blanca
explícita de rutas `~` permitidas (`.a3ref`, `.gemini`). Sin esa excepción, el
test que exige "0 paths que no provengan de Path(__file__)/env var/arg CLI"
(DoD #1) invalida la propia lista blanca que 1.c debe conservar.

A.4 EL DATASET a3ref NO LLEGA AL USUARIO: FALTA LA DISTRIBUCIÓN (gravedad: alta)
--------------------------------------------------------------------------------
La réplica BIKI (a3ref) NO está en el repo: es un clon externo que el usuario
debe tener. El plan solo dice "wiki-cache.md se trocea por comando" (2.f) y
nunca dice CÓMO obtiene un tercero los datos. Resultado: en una instalación
nueva, `sqf_wiki_lookup` no encuentra nada, la lente `claims.md` no puede
verificar comandos y todo lo que dependa de la BIKI cae a `NO VERIFICADO`
sin explicación.
CORRECCIÓN: nueva tarea **2.g-bis**:
  - Documentar en `INSTALL.md` cómo obtener el dataset: clonar a3ref en una
    ruta conocida + `python sqf_wiki_reader.py --update` (el flag ya existe).
  - Definir el estado explícito `SIN_REPLICA` en la respuesta del lookup cuando
    no hay dataset, y mapearlo a `NO VERIFICADO` en el informe.
  - Añadir el dataset a la sección de "Lo que NO incluye esta skill" del README.
  - Aclarar en la tabla de degradación: "sin dataset a3ref, la verificación BIKI
    no es posible en ningún host; el resto de la auditoría sí".
  - Considerar un paquete de datos opcional en PyPI (PR-7) o, si no, documentar
    el clonado como prerrequisito de una de las dos capas de verificación.

A.5 DEPENDENCIA CIRCULAR PR-3 ↔ PR-4 (gravedad: alta)
--------------------------------------------------------------------------------
PR-3 (3.i) exige ejecutar los 3 smoke tests "en al menos Claude Code y modo
pegado" y su criterio de salida dice "Al menos Claude Code y modo pegado con
los 3 smoke tests verdes".
El MODO PEGADO se construye en PR-4 (4.a genera `checklist_static.md`, 4.c lo
añade a Capa 0). En PR-3 el modo pegado aún no existe como artefacto.
CORRECCIÓN: dos opciones, elige una y declárala:
  (a) PR-3 exit = solo Claude Code (modo pegado se valida en PR-4, que ya tiene
      su propio criterio de salida con los 3 smoke tests); o
  (b) mover la generación del checklist a PR-2 (como parte de `invariants.md`)
      y dejar PR-4 solo para pulir el modo degradado.
Recomiendo (a): PR-3 valida el adapter, PR-4 valida el modo degradado.

A.6 LA Capa 0 SOLO ACTIVA AUDITORÍA: SE PIERDEN LOS WORKFLOWS GENERATIVOS
    (gravedad: alta — regresión funcional)
--------------------------------------------------------------------------------
El plugin original es un EQUIPO DE DESARROLLO, no un linter: `sqf-architect`
(diseño), `sqf-developer` (implementación), `sqf-innovator` (mecánicas nuevas),
`sqf-test-plan-generator`, `sqf-doc-writer`. El v2.1 crea 4 workflows
(`references/workflows/*.md`), pero la Capa 0 de 2.b SOLO dice cómo activar
lentes de AUDITORÍA (remoteExec, publicVariable, allUnits…). Un usuario que
pide "diseña un sistema JIP con CBA" no dispararía nada: el prompt solo ofrece
lentes de auditoría. Es una degradación funcional silenciosa (DoD #10 la
detectaría tarde, en PR-5).
CORRECCIÓN: 2.b debe incluir una sección de INTENCIONES (4 líneas, ~100 tokens):
  - AUDITAR  → modo de revisión (lentes + blockers + informe de estados)
  - DISEÑAR  → `references/workflows/modes.md` + `lenses/architect.md`
  - IMPLEMENTAR → `references/workflows/implementation.md` + `lenses/best_practices.md`
  - DOCUMENTAR/PLANIFICAR → `references/workflows/documentation.md` / `test_plan.md`
Y un test que verifique que Capa 0 menciona las 4 intenciones y las 4 rutas.
Añadir al DoD: "Las 4 intenciones del plugin original son alcanzables desde Capa 0".

A.7 INVENTARIO DE `references/` INCOMPLETO (gravedad: media-alta)
--------------------------------------------------------------------------------
2.f define el inventario solo a nivel de regla de tamaño. Faltan dos ficheros
que existen HOY en el repo y son parte del entregable del plugin original
(verificado en `skills/arma3-sqf-review/references/`):
  - `checklist-entrega.md` (bloques A–I): es lo que produce el Informe Desglosado
    de Estados por ítem (`PASA/NO PASA/NO VERIFICADO/NO APLICA`) — el entregable
    central de la skill. Sin él, el "informe de estados" del objetivo no tiene
    fuente.
  - `diferencial-misiones-addons.md`: criterios de entrega por DESTINO
    (misión vs addon). El Perfil de Proyecto declara DESTINO, pero ningún
    artefacto del port lo usa.
CORRECCIÓN: 2.f pasa a ser el INVENTARIO NOMINAL con una fila por fichero:
  `invariants.md` (canónico), `checklist-entrega.md` (plantilla de entrega),
  `diferencial-mision-addon.md` (criterios por destino),
  `lenses/*.md` (6), `workflows/*.md` (4), `wiki-cache/` (troceado),
  `report_format.md` (ver A.9).
Y una tarea 2.f-bis: "incorporar `checklist-entrega.md` al canónico o como
  referencia sister; decidir si vive en `invariants.md` (canónico) o aparte".
DoD nuevo: "El informe de estados por ítem (A–I) está disponible en modo
  archivo y en modo pegado".

A.8 R2 vs R3: LAS COPIAS INLINE SON DUPLICADOS POR DEFINICIÓN (gravedad: media-alta)
--------------------------------------------------------------------------------
R2 exige una única fuente canónica. R3 exige que los hosts degradados
(ChatGPT, Gemini) lleven el checklist INLINE. Una copia inline de las reglas
ES un duplicado → divergencia garantizada con el paso del tiempo. El plan
resuelve checklist_static.md con "generado o derivado" (4.a), pero no aplica
el mismo mecanismo a los artefactos de host.
CORRECCIÓN: TODOS los artefactos que contengan texto normativo deben ser
GENERADOS, nunca escritos a mano:
  - `references/checklist_static.md`  ← generador desde `invariants.md`
  - `integrations/chatgpt/custom_gpt_instructions.md` ← generador (recorte)
  - `integrations/gemini/system_instruction.md` ← generador (recorte)
  - versión EN de `SKILL.md` e `invariants.md` ← TRADUCCIÓN ASISTIDA + revisión
    (no generable automáticamente: mantenlo como fichero versionado, pero con
    un test que verifique que contiene las mismas 7 categorías y la puerta).
Mecanismo: cada fichero generado lleva una cabecera
  `<!-- GENERATED FROM: references/invariants.md | DO NOT EDIT -->`
y `scripts/check.py` regenera y compara (hash). Si el canónico cambió y el
generado no, CI falla. Esto convierte R2 y R3 en compatibles y verificables.

A.9 EL FORMATO DEL INFORME ES UN CONTRATO SIN VERSIÓN (gravedad: media)
--------------------------------------------------------------------------------
El formato `archivo:linea (disciplina): descripcion` + `RESUMEN:` es hoy el
contrato entre el script, el prompt, los evals y cualquier consumidor externo
(el skill loDocumenta como "el subagente lee el informe estructurado sin parsear
stdout a mano"). Ese contrato no está versionado ni declarado en el prompt.
CORRECCIÓN: `REPORT_SCHEMA_VERSION = 1` declarado en `invariants.md` y en el
código; `references/report_format.md` con la especificación; Capa 0 dice en una
línea "responde SIEMPRE con el formato v1 (ver references/report_format.md)";
el golden test (6.g) verifica versión + estructura, no solo la presencia de
`RESUMEN:`. Añadir DoD: "El informe emitido lleva versión de esquema y el
  consumidor (SKILL.md, evals, MCP) la declara".

A.10 QUÉ CUENTA COMO "DETECCIÓN" EN LOS EVALS NO ESTÁ DEFINIDO (gravedad: media)
--------------------------------------------------------------------------------
5.c define la métrica agregada y N=3, pero no el criterio de acierto: ¿qué
cuenta como bloqueante "detectado"? ¿Coincidencia de la categoría? ¿Basta con
que el modelo diga BLOQUEANTE en el fichero correcto? ¿Quién juzga: un LLM judge
o un matcher determinista sobre el informe? Sin eso, la métrica no es
reproducible entre hosts y R5 no se sostiene.
CORRECCIÓN (5.c y 5.b): especificar
  - formato del hallazgo esperado: `{categoria: 1..7, archivo, linea, severidad}`;
  - coincidencia: misma categoría + severidad BLOQUEANTE + archivo/linea dentro
    de ±2 líneas (tolerancia declarada);
  - juez: matcher determinista sobre el informe estructurado (NO LLM judge)
    para evitar variabilidad en el juez; si se usa LLM judge, su prompt se
    versiona en `evals/judge_prompt.md` y su salida se audita manualmente en
    una muestra;
  - qué se evalúa por separado: bloqueantes (métrica estricta) y sugerencias
    (métrica informativa, no puerta).

A.11 LA VERSIÓN EN SE CUELA EN EL ÚLTIMO PR Y ROMPE EL PRESUPUESTO (gravedad: media)
--------------------------------------------------------------------------------
7.c genera la versión EN en PR-7 (publicación), pero el frontmatter bilingüe
(2.a, español) es lo que el host lee para ACTIVAR la skill: un frontmatter solo
en español penaliza la activación en modelos por defecto, y sin embargo el
criterio de PR-3 (smoke tests) se ejecuta con la versión ES.
Además, si EN vive como sección dentro del mismo `SKILL.md`, el cuerpo se
duplica y el presupuesto de 1.200 tokens se rompe por construcción.
CORRECCIÓN: decidir la estructura:
  - Opción recomendada: DOS skills instalables, `skills/arma3-sqf-skill/` (ES) y
    `skills/arma3-sqf-skill-en/` (EN), con `name:` distinto en el frontmatter,
    referencias compartidas (`references/` comunes) y el MISMO presupuesto
    ≤ 1.200 tokens medido para ambas. El usuario instala la que su host prefiera.
  - Medir siempre AMBAS versiones en `measure_tokens.py`.
  - Adelantar a PR-2 el frontmatter bilingüe (o el EN del `description`), porque
    es parte del mecanismo de activación y no de la documentación.

A.12 `measure_tokens.py` NO DEFINE QUÉ CUENTA (gravedad: media)
--------------------------------------------------------------------------------
DoD #4 y #5 miden "Capa 0" y "Capa 0 + Capa 1", pero no se define el alcance
exacto del conteo: ¿incluye el frontmatter? ¿incluye la tabla de lentes? ¿el
cálculo de "Capa 1" es "la lente más larga" o "la suma de todas las lentes
detectadas"? Sin alcance fijo, el test es interpretable y el CI no es una puerta.
CORRECCIÓN: definir en el propio script y en el DoD:
  - `tokens_frontmatter` (description) ≤ 250, cuenta aparte, porque lo carga
    el host siempre y en todos los turnos.
  - `tokens_capa0` = cuerpo del SKILL.md sin frontmatter ≤ 1.200.
  - `tokens_turno_max` = capa0 + lente_más_larga (peor caso realisticamente
    alcanzable) ≤ 2.500; y documentar el peor caso absoluto (capa0 + 6 lentes)
    como métrica informativa.
  - Margen del 15 % por diferencia de tokenizer (tiktoken ≠ tokenizer del host);
    el presupuesto es una APROXIMACIÓN y debe decirlo el propio README.

A.13 REQUIRES-PYTHON DEL REPO CONTRADICE LA MATRIZ DE CI (gravedad: media, verificada)
--------------------------------------------------------------------------------
`pyproject.toml` declara hoy `requires-python = ">=3.11"`, `target-version = "py311"`
y `python_version = "3.11"`. DoD #11 y 5.g exigen CI en 3.10/3.11/3.12/3.13.
CORRECCIÓN: alinear en PR-1: o se sube la matriz a ≥ 3.11 (recomendado: 3.11,
3.12, 3.13), o se baja `requires-python` a ">=3.10" y se ajusta ruff/pyright.
Añadir en PR-1 la tarea 1.m: "alinear `requires-python`, `target-version`,
`python_version` y la matriz de CI; declarar la matriz de SO en README".

A.14 `legacy/` Y EL PAQUETE: EXCLUIRLO ES DECLARLO, NO ESTÁ HECHO (gravedad: baja-media)
--------------------------------------------------------------------------------
La tabla dice "excluido de paridad y empaquetado", pero ninguna tarea lo
implementa: `legacy/agents/` would entrar en el wheel/sdist (MANIFEST.in) y en
el escaneo de rutas (1.d) y en el test de unicidad (2.k) — precisamente los
tres que el plan dice que debe excluir.
CORRECCIÓN: 1.n (nueva): "Excluir `legacy/` de `MANIFEST.in`/packaging, del
escaneo de rutas y del test de unicidad; añadir `.gitattributes` o equivalente
para marcarlo como no distribuible". Verificado: hoy `.gitattributes` ya existe
en el repo, es el sitio natural para `legacy/** -export-ignore`.

A.15 EL DoD NO DISTINGUE EL RESULTADO DEL MODO PEGADO NI LA LATENCIA (gravedad: media)
--------------------------------------------------------------------------------
R1 permite que los hosts externos queden NO VERIFICADO, pero el DoD solo
exige los smoke tests "en Claude Code" (#9): no hay fila para el MODO PEGADO,
que es la única validación que corre en CUALQUIER host y la que sostiene la
promesa "diversos modelos de IA".
CORRECCIÓN: añadir filas al DoD:
  #9b Modo pegado: S1–S3 correctos en ≥ 2 hosts/modelos (tabla con modelo/versión).
  #9c El informe en modo pegado marca `NO VERIFICADO` (no `PASA`) en todo ítem
      que requeriría linter o BIKI.
  #9d Latencia del modo pegado: respuesta completa en < 60 s (límite de UX).
Y una fila para el informe de estados A–I (ver A.7).

A.16 EL SMOKE TEST S2 DECLARA "× 2" PERO EL CRITERIO ES "3/3" (gravedad: media)
--------------------------------------------------------------------------------
La matriz de smoke tests define S1/S2/S3 con "BLOQUEANTE × 2" cada uno (dos
hallazgos por test), pero DoD #9 mide "3/3 veredictos correctos" (por test).
La ambigüedad afecta a la métrica: ¿3/3 significa 3 tests o 6 hallazgos?
CORRECCIÓN: unificar en hallazgos: "S1–S3 ⇒ 6/6 hallazgos bloqueantes
  detectados (2 por test, categoría correcta)". Y registrar en la tabla de
  resultados una columna "categoria detectada" por hallazgo, no solo el
  veredicto global.

A.17 LA DEPENDENCIA `sqf.analyzer` NO ESTÁ AUDITADA PARA DISTRIBUCIÓN (gravedad: media)
--------------------------------------------------------------------------------
El plan da por hecho "motor in-process (`import sqf.analyzer`)" como riesgo
resuelto. No se ha decided: ¿de dónde viene ese paquete, con qué licencia, se
puede distribuir en el wheel, funciona en Windows/Linux con las versiones
fijadas, y qué pasa si el usuario no lo tiene instalado?
CORRECCIÓN: en PR-1 1.i (consolidación de requirements) especificar por
dependencia: nombre en PyPI, versión fijada, licencia, si es dependencia
obligatoria u opcional, y el comportamiento si falta (el motor ya define
`SQFLINT_NO_DISPONIBLE` → `NO VERIFICADO`; documentarlo como comportamiento
soportado, no como bug).

A.18 MIGRACIÓN DE USUARIOS DE LA SKILL VIEJA (gravedad: baja-media)
--------------------------------------------------------------------------------
El nombre cambia de `arma3-sqf-review` a `arma3-sqf-skill`. Un usuario que ya
tiene instalada la skill antigua en su host seguirá viendo las dos (o solo la
antigua) y su `SKILL.md` quedará obsoleto. No hay tarea de migración.
CORRECCIÓN: 7.b (INSTALL.md) incluye una sección "Si vienes de
`arma3-sqf-review`": desinstalar la skill anterior y sus subagentes antes de
instalar esta; y en el changelog de la release, una línea de migración.

A.19 EL PLAN NO DICE QUÉ PASA CON `plugin.json` Y EL PLUGIN ORIGINAL (gravedad: baja)
--------------------------------------------------------------------------------
El repo conserva `plugin.json` (Antigravity). Tras el port, `plugin.json` sigue
declarando un plugin que ya no es el producto principal. Falta la decisión:
¿se mantiene como "plugin legacy compatible", se renombra, o se marca como
deprecated con aviso en el README?
CORRECCIÓN: añadir una tarea en PR-7: "Decidir el estado de `plugin.json` y del
  `agents/` original: mantener como compatibilidad Antigravity (con nota) o
  marcar deprecated; documentarlo en README y en el changelog."

================================================================================
PARTE B — SECUENCIA PROPUESTA (reordena lo mínimo imprescindible)
================================================================================
El backbone del v2.1 es correcto y NO se toca. Los ajustes son de alcance y de
orden, y solo dos tareas exigen cambio de PR:

  PR-1 + 1.g-bis  migrar las 7 categorías, la Puerta de Calidad y la rúbrica
                 desde el SKILL.md actual a references/invariants.md  (A.2)
        + 1.c-bis  reescritura de 1.c como precedencia (CLI > env > candidatos
                   actuales > fallback empaquetado) + lista blanca `~` en el
                   test de rutas  (A.3)
        + 1.m      alinear requires-python / target-version / matriz CI  (A.13)
        + 1.n      excluir legacy/ de packaging, escaneo y unicidad  (A.14)
        + 1.o      checklist de dependencias con licencia y versionado  (A.17)

  PR-2 + Capa 0 con las 4 INTENCIONES (auditar/diseñar/implementar/documentar)
                 + rutas a los 4 workflows                                        (A.6)
        + índice de 7 categorías con la nueva regla de niveles (índice vs
          definición) y el test 2.k reescrito en dos fases                       (A.1)
        + 2.g-bis  distribución del dataset a3ref + estado SIN_REPLICA          (A.4)
        + 2.f-bis  inventario nominal de references/ (+ checklist-entrega.md,
                    diferencial-mision-addon.md, report_format.md)               (A.7, A.9)
        + 2.g-ter  cabeceras GENERATED + verificación por hash en check.py        (A.8)
        + frontmatter bilingüe desde ya, no en PR-7                               (A.11)
        + 2.f-ter  alcance exacto del conteo de measure_tokens + margen 15 %     (A.12)

  PR-3  criterio de salida: solo Claude Code (desacoplar del modo pegado)     (A.5)
        + A.15 fila de DoD para modo pegado
  PR-4  + validación del modo pegado con los 3 smoke tests
  PR-5  + criterio de acierto, matcher determinista, sin LLM judge no auditado   (A.10)
        + harness FUERA de CI (script manual con claves), CI solo con partes
          deterministas                                                            (A.10)
  PR-6  + REPORT_SCHEMA_VERSION en la respuesta de sqf_review                    (A.9)
  PR-7  + skill EN como segunda skill instalable (no sección duplicada)          (A.11)
        + sección de migración desde arma3-sqf-review                            (A.18)
        + decisión sobre plugin.json/agents legacy                               (A.19)

Regla transversal añadida:
  R6  Todo texto normativo que viva fuera del canónico es GENERADO y verificado
      por hash en CI; la traducción EN es la única excepción (archivo
      versionado y auditado por test de cobertura de las 7 categorías).

================================================================================
PARTE C — VERIFICACIÓN DE ESTADO
================================================================================
- Cerrado en v2.1 y NO se repite: R1–R5, canonicidad, mapeo de 11 agentes,
  tabla de degradación por host, smoke tests reescritos, check.py, N=3,
  negativos limpios, tool compuesta, contrato de seguridad del endpoint,
  criterio de abandono del Track B, CI workflow, DoD de 13 filas, riesgos
  reencuadrados, HF Spaces eliminado, tunnel con hostname estable.
- Abierto: 19 puntos (A.1–A.19), de los cuales 3 son bloqueantes (A.1, A.2,
  A.3), 5 de gravedad alta (A.4, A.5, A.6, A.7, A.8) y 11 de gravedad media
  o baja.
- No he ejecutado el plan ni modificado el plugin: el análisis es documental
  sobre el v2.1 y el estado real del repo (pyproject.toml, sqf_wiki_reader.py,
  skills/arma3-sqf-review/references/, SKILL.md actual, .gitattributes).

================================================================================
FIN DE LAS INSTRUCCIONES v2.1 → v2.2
================================================================================
