================================================================================
INSTRUCCIONES PARA MEJORAR, ACTUALIZAR Y OPTIMIZAR LA PLANEACIÓN (v2.0 → v2.1)
================================================================================

CONTEXTO: esta revisión parte del Plan v2.0 ya saneado. Las recomendaciones
previas están adoptadas (objetivo medible + no-objetivo, dos tracks, PR-1..PR-7,
presupuesto por capas, matriz de portabilidad, measure_tokens.py, evals con
goldens, DoD como tabla métrica, riesgos revisados, tunnel con hostname estable,
postura de privacidad en Track B). NO se repiten.
Lo que sigue son los huecos y las contradicciones que QUEDAN ABIERTAS en v2.0,
ordenados por gravedad. Todos son corregibles sin reescribir el plan.

================================================================================
PARTE A — HUECOS FUNCIONALES (lo que degrada la calidad si no se cierra)
================================================================================

A.1 TRES FUENTES DE VERDAD PARA LOS INVARIANTES (gravedad: alta)
--------------------------------------------------------------------------------
En el repo existen hoy TRES sitios con las reglas de servidor dedicado:
  (a) `rules/AGENTS.md`                       → 1.f lo convierte en `references/invariants.md`
  (b) `skills/arma3-sqf-review/references/sqf-standards.md`  → NO aparece en ninguna tarea de PR-2
  (c) el propio `SKILL.md` actual (Paso 7, rúbrica de severidad, entrega) → 2.c dice "preservar"
DECISIÓN REQUERIDA: un único fichero canónico de reglas. Recomendado:
  `references/invariants.md` = canónico (absorbe lo de AGENTS.md y las 7 categorías
  de BloQUEANTE + Puerta de Calidad + honestidad técnica + criterios de modo).
  `sqf-standards.md` se RETIRA o se convierte en un puntero ("ver invariants.md").
  El `SKILL.md` nuevo NO reescribe reglas: solo activa y enruta.
Añade una tarea explícita en PR-2: "1.5 fusionar/absorber sqf-standards.md en
invariants.md y dejar una sola copia de cada regla". Sin esto, cada PR
reintroduce divergencias y el riesgo "dos fuentes de verdad" que tú mismo
declaraste se dispara dentro del propio repo nuevo.

A.2 LA PUERTA DE CALIDAD NO ES EJECUTABLE EN CAPA 0 (gravedad: alta)
--------------------------------------------------------------------------------
2.c ubica las 7 categorías de Bloqueante, la Puerta de Calidad y el principio de
honestidad técnica DENTRO de `references/invariants.md`. Pero 2.b define Capa 0
como "invariantes + criterios de activación + cómo abrir references" ≤ 1.200
tokens. Resultado: en Capa 0 el modelo NO conoce los criterios de bloqueo ni la
regla "cero bloqueantes ⇒ no entregar" → puede entregar como "PASA" sin haber
leído la referencia. Es exactamente el failure mode que el plan promete evitar.
DECISIÓN: Capa 0 debe incluir, de forma compacta:
  - los 7 criterios de BLOQUEANTE enunciados por TÍTULO (una línea cada uno, ~150–200 tokens),
  - la regla de la puerta ("si hay ≥1 bloqueante ⇒ NO entregar, informar y detener"),
  - la regla de honestidad ("sin linter/wiki ⇒ NO VERIFICADO, nunca PASA"),
  - y la RUTA exacta a `references/invariants.md` para el detalle.
Equivale a "índice + regla + puntero", no a "contenido completo".
Aplica el mismo criterio a la versión EN (7.c) y a las instructions de hosts sin
filesystem (A.4).

A.3 EL MODO PEGADO DUPLICA EL CHECKLIST (gravedad: media-alta)
--------------------------------------------------------------------------------
PR-4 crea `references/checklist_static.md` como checklist "exhaustivo" y 4.c
lo añade al Capa 0. Ese checklist volverá a contener reglas de invariantes y
criterios de bloqueante → tercer duplicado (junto a A.1 y A.2), con divergencia
garantizada. DECISIÓN: `checklist_static.md` no es un documento nuevo: es la
MISMA `references/invariants.md` reorganizada como "preguntas sí/no por ítem con
el ítem al que corresponde", o bien se GENERA desde invariants.md con un script
y un test que verifique que ambos derivan de la misma fuente.

A.4 LA PROGRESSIVE DISCLOSURE NO FUNCIONA EN HOSTS SIN LECTURA DE ARCHIVOS
    (gravedad: alta)
--------------------------------------------------------------------------------
El mecanismo central del plan ("el modelo abre references/lenses/*.md cuando
detecta la señal") solo es posible en hosts que leen archivos bajo demanda
(Claude Code, Cursor). En ChatGPT Custom GPT el Knowledge es RAG (búsqueda
semántica, no inyección determinista) y en Gemini la system instruction es texto
plano. Por tanto:
  - La etiqueta "Degradado" de la matriz debe explicar QUÉ se degrada.
  - Para ChatGPT/Gemini hay que definir un artefacto SELF-CONTAINED: un fichero
    de instructions que embeba el checklist completo inline (no enlaces).
  - Límite duro: 8.000 caracteres en Custom GPT instructions. El checklist
    inline completo no cabe ⇒ hay que decidir qué se prioriza (criterios +
    puerta + honestidad) y qué se delega a Knowledge.
TAREA NUEVA (PR-3): "3.x Tabla de degradación por host: qué artefacto se entrega,
qué mecanismo usa (lectura de archivo / RAG / inline), qué se pierde, qué
límite de tamaño se respeta y cómo se compensa."

A.5 EL TRIAGE DE MODO DESAPARECE DEL NÚCLEO (gravedad: alta — regresión funcional)
--------------------------------------------------------------------------------
El plugin original tiene un comportamiento normativo que el v2.0 ya no
garantiza: el modo determinista Micro/Estándar/Completo calculado por
`sqf_orchestrator.py --mode-query`, con fallback "Estándar + NO VERIFICADO" y la
prohibición de clasificar Micro por criterio manual. En v2.0 el triage solo
aparece como endpoint `POST /api/mode` en Track B (PR-6) → el Track A (camino
crítico) se queda SIN triage de modo, y con él se pierden:
  - la matriz de participación por modo (quién revisa qué según el modo),
  - el escalado automático (Micro → Estándar → Completo),
  - la regla de fallback y la prohibición de Micro manual.
TAREA NUEVA (PR-2): "2.x Incorporar en Capa 0 la TABLA DE CRITERIOS DE MODO
(determinista, corta) + la regla de fallback + 'nunca Micro por criterio manual'
+ el mecanismo para consultar el script cuando existe (modo archivo)".
DECISIÓN: la tabla de criterios de modo cabe en ~120–150 tokens y es obligatoria.
También define el destino de la matriz de participación por modo: documento de
workflow `references/workflows/modes.md` (no es una lente).

A.6 LOS 11 SUBAGENTES NO ESTÁN CUBIERTOS POR LAS 5 LENTES (gravedad: media)
--------------------------------------------------------------------------------
PR-2 2.d define 5 lentes (locality, performance, architect, config, best_practices)
pero 1.e migra 11 agentes. El mapeo no está declarado y los roles generativos
(`sqf-developer`, `sqf-innovator`) no son lentes de auditoría: son workflow.
TAREA NUEVA (PR-1/2): tabla de mapeo agente → artefacto:
  sqf-locality-auditor      → lenses/locality.md
  sqf-performance-auditor   → lenses/performance.md
  sqf-architect             → lenses/architect.md
  sqf-mission-config-auditor→ lenses/config.md
  sqf-best-practices-reviewer→ lenses/best_practices.md
  sqf-static-analyzer       → modo archivo: script (no lente)
  sqf-claim-verifier        → lenses/claims.md  (verificación BIKI con URL+fecha)
  sqf-test-plan-generator   → workflows/test_plan.md
  sqf-doc-writer            → workflows/documentation.md
  sqf-developer             → workflows/implementation.md
  sqf-innovator             → workflows/innovation.md
Cada artefacto no creado en el port debe declararse en PARIDAD.md como
PORTADO-REDUCIDO o NO APLICABLE con motivo. Sin este mapeo, `docs/PARIDAD.md`
(5.e) queda sin fuente de verdad.

A.7 FALTA EL INVENTARIO DE REFERENCIAS (gravedad: media)
--------------------------------------------------------------------------------
PR-3 3.e exige "references/ autocontenido y archivos < 20 KB", pero PR-2 no
define el inventario final de `references/`. Faltan decisiones sobre
`wiki-cache.md` (probablemente > 20 KB: trocear por comando, generar un índice,
o no subirlo a Knowledge) y sobre el tamaño del checklist estático.
TAREA NUEVA (PR-2): "2.x Definir el inventario final de references/ con tamaño
estimado de cada uno y la regla de troceado; `wiki-cache.md` se trocea por
comando y NO se sube completo a Knowledge de Custom GPT".

A.8 DOCUMENTOS DUPLICADOS: PORTING.md vs PARIDAD.md (gravedad: baja)
--------------------------------------------------------------------------------
2.i crea `docs/PORTING.md` (tabla de paridad) y 5.e crea `docs/PARIDAD.md`
(la misma tabla). Mantén UNO: `docs/PARIDAD.md`, creado en PR-2 como esqueleto
y completado en PR-5. Elimina PORTING.md o conviértelo en la guía de proceso del
port (qué hacer en cada PR) sin duplicar la tabla de paridad.

A.9 EL RIESGO DE DERIVA ESTÁ DEFINIDO CONTRA EL PROYECTO EQUIVOCADO (gravedad: media)
--------------------------------------------------------------------------------
La tabla de riesgos habla de "deriva entre arma3-sqf-skill y arma3-sqf-review
(dos fuentes de verdad)" → mitigación: "docs/PARIDAD.md actualizado en cada PR".
Eso es sintoma, no causa. La deriva real está DENTRO del repo nuevo (invariants
vs standards vs checklist vs SKILL.md, ver A.1–A.3) y ENTRE los artefactos
legacy/agents y references/lenses (ver A.10). Corrige el riesgo para que nombre
esas dos derivas concretas y su mitigación (fuente canónica + test de duplicado).

A.10 `legacy/agents/` ES RUIDO QUE INVITA A LA DERIVA (gravedad: baja)
--------------------------------------------------------------------------------
Mover 11 agentes a `legacy/agents/` tras migrarlos a `references/lenses/` crea
DOS Representations del mismo conocimiento en el mismo repo, y nada impide que
alguien edite la copia legacy. RECOMENDACIÓN: no conservar `legacy/` en el árbol
(la historia de git ya es el archivo); si se conserva, marcarlo "frozen,
no editar" y excluirlo del test de paridad y del empaquetado.

================================================================================
PARTE B — MÉTRICAS Y CRITERIOS (lo que hace que la evidencia sea falsable)
================================================================================

B.1 MÉTRICA DE GOLDENS INCONSISTENTE (gravedad: media)
--------------------------------------------------------------------------------
DoD #7 dice "detección ≥ 90 % de bloqueantes esperados" con la métrica "≥ 9/10
casos". Son cosas distintas: 9/10 casos correctos ≠ 90 % de los bloqueantes
detectados (un caso puede tener 3 bloqueantes). Corrige:
  - Métrica: (bloqueantes esperados detectados) / (bloqueantes esperados totales)
    ≥ 0,90, agregado sobre el conjunto de goldens, con desglose por categoría
    de bloqueante (las 7).
  - El numerador y el denominador deben aparecer en el informe del harness.

B.2 LOS GOLDENS NO EXIGEN NEGATIVOS LIMPIOS (gravedad: media)
--------------------------------------------------------------------------------
DoD #8 exige "0 falsos positivos bloqueantes" pero 5.a no exige snippets sin
defectos. Sin negativos, ese criterio no se puede evaluar. AÑADE a 5.a: "≥ 3
snippets LIMPIOS (sin bloqueantes) que deben producir 0 hallazgos bloqueantes,
y ≥ 2 snippets con SOLO suggerencias (que no deben escalar a bloqueante)".
Esto es además el test de la regresión más común: el modelo marca todo como
bloqueante.

B.3 LOS 3 SMOKE TESTS NO MAPEAN A LAS 7 CATEGORÍAS NORMATIVAS (gravedad: alta)
--------------------------------------------------------------------------------
Los casos propuestos en PR-3 miden lo que el linter ya sabe (caso A) y dos
patrones cuya gravedad de veredicto es discutible:
  - Caso B: "hint sin guarda hasInterface ⇒ BLOQUEANTE". Según la regla 3 de
    `rules/AGENTS.md`, la UI en ruta de servidor es bloqueante INCLUSO con
    guarda `hasInterface` (la guarda solo evita el error, no el trabajo inútil).
    El enunciado del smoke test induce a la Interpretación incorrecta.
  - Caso C: "remoteExec sin verificación de isServer ⇒ BLOQUEANTE". remoteExec
    servidor→cliente es legal; lo bloqueante es (a) invocar remoteExec desde
    el cliente, (b) función remota ausente de la whitelist `CfgRemoteExec`
    con mode = 1, o (c) esperar indefinidamente una variable nunca emitida.
CORRECCIÓN: reescribe los 3 smoke tests para que cada uno apunte a una
categoría normativa inequívoca, y añade casos para las categorías que hoy
quedan sin cobertura humana (dedicado/`player`, `init.sqf` bloqueante,
contrato de interfaces roto, dependencia CBA/ACE3 no autorizada, sleep en
contexto unscheduled). Propuesta mínima de 3 smoke tests alineados:
  S1 → Regla 1/2 (scope y softlock): variable sin private + waitUntil sin salida.
  S2 → Regla 3/4 (dedicado y unscheduled): `player` en init.sqf + `hint` en
       ruta de servidor (con y sin guarda).
  S3 → Regla 5/7 (whitelist y framework): remoteExec a función no whitelistada
       + uso de CBA_fnc_* con perfil CBA: no.
Cada smoke test debe declarar su regla de origen en la tabla de resultados.

B.4 EL RENDIMIENTO ES "MANUAL" Y LOS HOSTS EXTERNOS SON UNA DEPENDENCIA DE TRACK A
    (gravedad: media)
--------------------------------------------------------------------------------
DoD #9 y PR-3 exigen probar en Claude Code, Claude Desktop, Cursor y Codex:
requiere cuentas externas, y en Codex/Cursor el smoke test depende del modelo
y de la versión. Y PR-4 4.d exige ChatGPT web (crear un Custom GPT = acción
externamente visible). TRACK A, que se define como "camino crítico", depende así de
hosts externos, contradiciendo "si falla el Track B, la skill sigue usable".
DECISIÓN:
  - Separa "validación local obligatoria" (Claude Code local + modo pegado en
    cualquier host + harness de goldens local) de "validación por host"
    (opcional, se marca NO VERIFICADO si no hay cuenta).
  - Solo la validación local es condición de salida del Release Gate.
  - Añade al PR-3 un registro de MODELO y VERSIÓN usados en cada smoke test:
    sin eso, los resultados no son comparables ni reproducibles.
  - 4.d: el smoke test de ChatGPT web debe usar el harness de goldens pegando
    el código, sin crear un GPT público (o con aprobación explícita).

B.5 "DETECCIÓN ≥ 90 %" MIDIDO POR UN LLM NO ES DETERMINISTA (gravedad: media)
--------------------------------------------------------------------------------
El harness PR-5 medirá a un modelo, con variabilidad por sampling y por host.
Sin control, el DoD es inestable y no se puede usar como puerta. AÑADE:
  - Cada golden se evalúa N=3 repeticiones y se reporta la tasa de detección
    (media y mínima), no una corrida única.
  - Se fija la temperatura/modelo por host en la tabla de resultados.
  - El umbral se aplica al AGREGADO y se documenta el margen de error.
  - Distingue "detección por el LLM" de "detección por el script determinista":
    el linter (`sqf_orchestrator.py --lint`) debe dar el 100 % en los goldens
    deterministas; el LLM es la capa semántica. Medir los dos por separado evita
    atribuir al modelo lo que hace el script.

B.6 EL DODE FALTA LAS MÉTRICAS DE NO-FUNCIONALIDAD (gravedad: media)
--------------------------------------------------------------------------------
Añade filas al DoD para: (a) Python mínimo soportado y matriz de SO declarada
en README; (b) versión del SDK MCP y nota de compatibilidad; (c) `references/`
completo por debajo del tamaño acordado; (d) tiempo de respuesta del checklist
en modo pegado (límite de latencia para que el usuario no abandone);
(e) cero rutas absolutas YA cubierto en #1 pero que también aplique a
documentación e `integrations/`, no solo a `.py`.

B.7 "MÉTRICA = 0 MATCHES" ES FRÁGIL (gravedad: baja)
--------------------------------------------------------------------------------
DoD #1 busca literales (`"EDEN EDITOR"`, `C:\Users`, `Path.home()`, `/home/`).
Unas rutas absolutas equivalentes (por ejemplo `D:\Proyectos\...` o
`os.environ["HOME"] + "/..."`) no se detectan. Mejora el test: además de
literales, valida que TODO path en runtime provenga de `Path(__file__)`,
de una variable de entorno declarada, o de un argumento CLI; y añade un
archivo `references/` y `integrations/` al alcance del escaneo.

================================================================================
PARTE C — COHERENCIA OPERATIVA DEL PLAN (proceso y contratos)
================================================================================

C.1 NO EXISTE TAREA PARA ACTUALIZAR EL WORKFLOW DE CI (gravedad: media-alta)
--------------------------------------------------------------------------------
1.d añade un test de rutas y 5.c integra `measure_tokens.py` en "CI local", pero
ninguna tarea modifica `.github/workflows/ci.yml` ni define qué es "CI local".
DECISIÓN: añadir en PR-1 la tarea "1.j Crear `scripts/check.py` (o Makefile)
que ejecute: pytest + test de rutas + measure_tokens + test de paridad, con
exit code no-cero ante cualquier fallo" y en PR-5 "5.x Actualizar
`.github/workflows/ci.yml` para ejecutar el mismo script en Ubuntu + Windows
(Python 3.10/3.11/3.12/3.13)". Sin un comando único, "CI local obligatorio en
cada PR" es una frase sin mecanismo.

C.2 CONTRADICCIÓN RESUELTA DE MANERA FLOJA EN EL TRACK B (gravedad: media)
--------------------------------------------------------------------------------
6.a propone 3 endpoints atómicos y 6.b expone 3 tools MCP. Eso devuelve el
problema que el SKILL.md prohíbe: el modelo encadena llamadas y reconcilia
severidades a mano, con una segunda fuente de verdad. Además, "3 endpoints
atómicos" choca con la Atomicidad MCP real: cada tool debe ser autocontenida.
DECISIÓN:
  - Tool principal COMPUESTA: `sqf_review(code, root?, profile?)` → devuelve el
    informe completo (modo + lint + bloqueantes + estados + hechos wiki). Un
    solo turno, una sola fuente de verdad.
  - Tools granulares OPCIONALES solo para seguimiento: `sqf_wiki_lookup(command)`,
    `sqf_triage(root)`.
  - Test de contrato MCP (6.f) que verifique que `sqf_review` devuelve el
    informe completo con `RESUMEN:`.

C.3 EL CONTRATO DEL ENDPOINT NO ESTÁ DEFINIDO (gravedad: media)
--------------------------------------------------------------------------------
6.a no dice de dónde sale el código SQF: ¿del body HTTP, de un path en disco
leído por el servidor, de ambos? Si el servidor lee paths del cliente, hay
riesgo de path traversal y de exponer el sistema de ficheros del host. AÑADE
al plan: contrato explícito (body `code` como vía principal; `root` solo si
está dentro de una raíz permitida y whitelistada), Auth (clave de API en
header), límites (tamaño máximo de payload), timeouts y CORS deshabilitado por
defecto. Y que la postura de privacidad de 6.d incluya esto, no solo "no
persistimos".

C.4 EL TRACK B NO TIENE MIGRACIÓN NI ROLLBACK (gravedad: media)
--------------------------------------------------------------------------------
6.c fija `mcp[cli]>=1.0,<2.0` "con nota de compatibilidad", pero no hay plan de
upgrade ni criterio de abandono. Añade en 6.c/6.d: (a) nota de compatibilidad
con la versión exacta probada; (b) criterio de abandono explícito ("si el SDK
MCP rompe el contrato o el mantenimiento supera X horas/mes, PR-7 publica sin
Track B"); (c) el Track B debe poder desactivarse sin tocar el núcleo.

C.5 LOS ARTEFACTOS POR HOST NO CUBREN TODA LA MATRIZ (gravedad: media)
--------------------------------------------------------------------------------
La matriz declara 6 hosts; PR-3 produce 3.a Claude, 3.c Cursor, 3.d OpenAI/Codex.
Faltan los artefactos de los dos hosts marcados como Degradado (ChatGPT Custom
GPT y Gemini), precisamente los que hoy no tienen NADA entregado:
  - `integrations/chatgpt/custom_gpt_instructions.md` (≤ 8.000 caracteres, con el
    checklist inline según A.4) + `integrations/chatgpt/knowledge_manifest.md`
    (qué ficheros subir y cuáles trocear).
  - `integrations/gemini/system_instruction.md` (texto plano, sin enlaces) +
    nota de Function Calling si se activa Track B.
AÑADE 3.f, 3.g, 3.h. Sin ellos, dos filas de la matriz son promises, no
producto.

C.6 FALTA EL CONTRATO DE INSTALACIÓN POR HOST (gravedad: baja-media)
--------------------------------------------------------------------------------
Cada host instala de forma distinta (symlink a la carpeta de skills, copia,
ruta en `~/.claude/skills`, `.cursor/rules`, `AGENTS.md` en el repo del
usuario). PR-7 lo cubre en INSTALL.md, pero PR-3 necesita los artefactos
instalados para ejecutar los smoke tests. AÑADE en PR-3: `integrations/<host>/install.md`
con el procedimiento y el comando de verificación, y un artefacto común
`integrations/common/skill-layout.md` que documente la estructura final esperada.

C.7 FALTA EL TRATAMIENTO DEL "MODO MICRO / ESCALADO" EN LOS HOSTS DEGRADADOS
    (gravedad: media)
--------------------------------------------------------------------------------
El modo pegado no puede ejecutar `sqf_orchestrator.py --mode-query`, luego el
criterio determinista de modo no es calculable: hay que DECIDIR el fallback en
ese host. La regla original ("fallback = Estándar + NO VERIFICADO, nunca Micro
por criterio manual") es coherente y debe quedar explícita en el artefacto de
cada host degradado. AÑADE a A.5 y a C.5.

================================================================================
PARTE D — SECUENCIA FINAL PROPUESTA (reemplaza el orden de PRs del v2.0)
================================================================================
El orden del v2.0 es correcto en su backbone (saneamiento → núcleo → adapters →
degradado → evals → Track B → release). Ajustes puntuales de orden y alcance:

  PR-1  + 1.j scripts/check.py (comando único de validación local)
        + 1.k tabla de mapeo de los 11 agentes (A.6)
        + 1.l decisión de fuente canónica y fusión de sqf-standards (A.1)
  PR-2  + Capa 0 con índice de las 7 reglas, puerta de calidad y honestidad
        (A.2) + tabla de criterios de modo (A.5) + inventario de references (A.7)
        + un único docs/PARIDAD.md (A.8)
  PR-3  + artefactos ChatGPT y Gemini (C.5) + tabla de degradación por host
        (A.4) + install.md por host (C.6) + smoke tests alineados con las 7
        categorías (B.3) + registro de modelo/versión (B.4)
  PR-4  + checklist derivado de la fuente canónica, no documento paralelo (A.3)
        + fallback de modo en hosts degradados (C.7)
  PR-5  + métrica de goldens por bloqueante (B.1) + negativos limpios (B.2)
        + N=3 repeticiones y separación linter/LLM (B.5) + workflow CI remoto (C.1)
  PR-6  + tool compuesta sqf_review (C.2) + contrato de seguridad del endpoint
        (C.3) + criterio de abandono (C.4)
  PR-7  + README/INSTALL + versión EN + publicación, todo tras Release Gate

Reglas transversales que conviene declarar en el propio plan:
  R1  El Release Gate solo depende de la validación LOCAL. Los hosts externos
      pueden quedar NO VERIFICADO y no bloquean la publicación.
  R2  Toda regla tiene una única fuente canónica; los duplicados se prohíben
      con un test de estructura.
  R3  Ningún artefacto de host puede enlazar a un fichero que ese host no pueda
      leer; si no puede leerlo, va inline y recortado.
  R4  Todo criterio de aceptación tiene MÉTRICA + MÉTODO + ESTADO. Un criterio
      sin método verificable se elimina del DoD.
  R5  "Igual calidad que el plugin original" solo es una afirmación publicable
      si PR-5 produce tabla por host con modelo, versión y N repeticiones.

================================================================================
FIN DE LAS INSTRUCCIONES v2.0 → v2.1
================================================================================
