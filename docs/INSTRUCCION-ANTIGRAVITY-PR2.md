================================================================================
INSTRUCCIÓN PARA ANTIGRAVITY — Continuar el port `arma3-sqf-skill` (PR-2)
================================================================================
Copia este bloque completo en el chat de Antigravity, con la working directory
en la copia de trabajo:

    C:\Users\Touri\Documents\EDEN EDITOR\Skills Antigravity\arma3-sqf-skill

--------------------------------------------------------------------------------
CONTEXTO
--------------------------------------------------------------------------------
Estamos portando el plugin Antigravity `arma3-sqf-review` a una SKILL PORTABLE
que funcione en Claude Code, Claude Desktop, Cursor, Codex, ChatGPT Custom GPTs
y Gemini, sin depender del runtime multi-agente de Antigravity.

- Directorio ORIGINAL (SOLO LECTURA, NO TOCAR NUNCA):
  `C:\Users\Touri\Documents\EDEN EDITOR\Skills Antigravity\arma3-sqf-review\`
- Directorio de TRABAJO (todo se hace aquí):
  `C:\Users\Touri\Documents\EDEN EDITOR\Skills Antigravity\arma3-sqf-skill\`
- Plan de referencia: **Plan v2.4** + correcciones de la revisión v2.5.
- Estado operativo y trazabilidad: `docs/ESTADO-PR.md` y `docs/PARIDAD.md`.

ESTADO VERIFICADO AL INICIO DE ESTA SESIÓN (no lo reestimes, está comprobado):
  PR-1 = CERRADO Y EN VERDE. `python scripts/check.py --fase PR-1` → exit 0.
  Suite: 58 tests en verde, 5 omitidos (los 5 son exigibles desde PR-2).
  `ruff check .` → All checks passed.
  La tarea bloqueante 1.g-bis YA ESTÁ HECHA: las 7 categorías de BLOQUEANTE,
  la Puerta de Calidad, el principio de honestidad técnica, la precedencia de
  conflictos y la propiedad de reglas están migrados literalmente a
  `skills/arma3-sqf-skill/references/invariants.md`.

--------------------------------------------------------------------------------
TU OBJETIVO EN ESTA SESIÓN: COMPLETAR PR-2
--------------------------------------------------------------------------------
"Núcleo Portable — SKILL.md en capas + references".

CRITERIO DE ENTRADA: `python scripts/check.py --fase PR-1` en verde.
CRITERIO DE SALIDA: `python scripts/check.py --fase PR-2` en verde (exit 0).

Hay una regla de oro: **NO sobrescribas `SKILL.md` antes de leer
`references/invariants.md`**. El prompt nuevo debe ACTIVAR Y ENRUTAR, nunca
redefinir la norma. La fuente canónica ya existe y está congelada por tests.

--------------------------------------------------------------------------------
REGLAS INVARIABLES (NO NEGOCIABLES)
--------------------------------------------------------------------------------
R1. El Release Gate solo depende de validación LOCAL. Los hosts externos
    pueden quedar `NO VERIFICADO` sin bloquear.
R2. Una única fuente canónica por regla. Las definiciones N3 (texto normativo
    completo) SOLO pueden vivir en:
      - `references/invariants.md`   → anclas CANON:BLOQUEANTES, CANON:PUERTA,
        CANON:HONESTIDAD, CANON:MODOS, CANON:PRECEDENCIA, CANON:PROPIEDAD
      - `references/rubrica.md`      → CANON:RUBRICA, CANON:PARTICIPACION
      - `references/sqf-standards.md`→ CANON:ESTANDAR
    La propiedad entre los tres es DISJUNTA: ninguna regla se define en dos.
R3. Ningún artefacto puede enlazar a un fichero que su host no pueda leer.
    Si no puede leerlo, va INLINE y recortado (paquete P1–P4).
R4. Todo criterio tiene MÉTRICA + MÉTODO + ESTADO.
R5. "Igual calidad" solo es publicable con tabla por host (modelo, versión, N=3).
R6. El texto normativo que viva fuera del canónico es GENERADO y verificado
    por hash por regiones: bloque `<!-- AUTHORED -->…<!-- /AUTHORED -->` (escrito
    a mano, con hash en `scripts/generated.lock.json`) + región
    `<!-- CANON-EXTRACT:X -->…<!-- /CANON-EXTRACT:X -->` (inyectada del canónico,
    verificada por hash).

REGLAS DE TRABAJO (respetar siempre):
  - NO toques `arma3-sqf-review\` (original, solo lectura).
  - NO hagas push a GitHub hasta el Release Gate con aprobación del usuario.
  - CI local obligatorio antes de cerrar: `python scripts/check.py --fase PR-2`.
  - Un test SKIPPED en una fase que ya lo exige = FALLO, no verde.

--------------------------------------------------------------------------------
TAREAS DE PR-2 (en este orden)
--------------------------------------------------------------------------------
2.a  Reescribe el frontmatter de `skills/arma3-sqf-skill/SKILL.md` BILINGÜE
     (ES + EN) en la `description`. ≤ 250 tokens (frontmatter). Es lo que el
     host lee para ACTIVAR la skill: incluye disparadores concretos
     (remoteExec, publicVariable, JIP, Headless Client, init.sqf,
     CfgRemoteExec, bucles sobre allUnits, variables sin private, comandos de
     interfaz en servidor) y qué NO activar (preguntas conceptuales, typos,
     código no SQF).

2.b  Reescribe el CUERPO de `SKILL.md` como CAPA 0 — cuerpo ≤ 1.200 tokens.
     Debe contener exactamente:
       - Índice N1 de las 7 categorías de BLOQUEANTE: UNA LÍNEA por categoría,
         ≤ 25 tokens cada una (NO las definiciones: esas están en el canónico).
       - La regla de la puerta: "si hay ≥ 1 bloqueante → NO entregar, informar
         y detener".
       - La regla de honestidad: "sin linter o sin wiki → `NO VERIFICADO`,
         nunca `PASA`".
       - Tabla compacta de criterios de modo (Micro / Estándar / Completo) +
         la regla de fallback ("Estándar + NO VERIFICADO") +
         "nunca Micro por criterio manual".
       - Las 4 INTENCIONES con su ruta exacta:
           AUDITAR     → references/lenses/
           DISEÑAR     → references/workflows/modes.md + references/lenses/architect.md
           IMPLEMENTAR → references/workflows/implementation.md + references/lenses/best_practices.md
           DOCUMENTAR/PLANIFICAR → references/workflows/documentation.md | test_plan.md
       - Mecanismo de lentes: nombre EXACTO del fichero + patrón disparador.
           Ejemplo: `remoteExec | publicVariable → lee references/lenses/locality.md`
       - Ruta exacta a `references/invariants.md` y a `references/report_format.md`.
       - Los 7 parámetros del Perfil de Proyecto se declaran UNA vez al inicio
         de sesión; los turnos siguientes dicen "perfil declarado" (no los
         repitas en el prompt).
     NO incluyas aquí ninguna definición N3 ni texto largo de los agentes.

2.b-bis Define en `references/invariants.md` los tres niveles de contenido
     normativo (N1 índice / N2 resumen ≤60 tokens por ítem / N3 definición
     completa), indicando dónde se permite cada uno y cómo se verifica.

2.c  Completa `references/invariants.md` (ya migrado en 1.g-bis): añade
     `REPORT_SCHEMA_VERSION = 1` y el bloque del Paquete Inline P1–P4
     (índice 7 + puerta + honestidad / fallback de modo / checklist priorizado /
     formato del informe). No reescribas las definiciones ya migradas.

2.d-bis Crea las 6 LENTES en `references/lenses/` con el modelo de regiones:
       locality.md, performance.md, architect.md, config.md,
       best_practices.md, claims.md
     Cada una: bloque `<!-- AUTHORED -->` con las señales, heurísticas y
     ejemplos de la disciplina, + región `<!-- CANON-EXTRACT:BLOQUEANTES -->`
     con el extracto N1/N2 de las categorías que le aplican.
     Crea además `scripts/generated.lock.json` con el hash sha256 de cada
     región AUTHORED (clave con la forma `<ruta>#AUTHORED:<índice>`).

2.e-bis Crea los 4 WORKFLOWS en `references/workflows/` (versionados, excepción
     explícita a R6): modes.md, test_plan.md, documentation.md,
     implementation.md, innovation.md.
     `modes.md` debe contener la matriz de participación por modo (puedes
     citarla desde rubrica.md CANON:PARTICIPACION) y el escalado.

2.f  Crea `references/report_format.md` COPIANDO la salida real del motor.
     NO lo escribas de memoria. Ejecuta:
       python3 skills/arma3-sqf-skill/scripts/sqf_orchestrator.py --lint fixtures/test_scope.sqf
     y documenta literalmente:
       REPORT_SCHEMA_VERSION: 1
       [BLOQUEANTE|SUGERENCIA|NO_VERIFICADO] archivo:linea (disciplina): descripcion
       RESUMEN: bloqueantes=N; sugerencias=N; no_verificado=N
     Documenta TAMBIÉN que el informe de MODO es otro documento:
       MODO: <modo> / MOTIVO: <motivo> / RESUMEN: modo=<modo>; escalado=<si|no>
     Regla del matcher: el informe de hallazgos se identifica por que su
     RESUMEN contiene `bloqueantes=`.

2.f-bis Inventario nominal de `references/` con el tamaño estimado de cada
       fichero (todos < 20 KB). `wiki-cache.md` NO se trocea todavía aquí: la
       regla de troceado por comando y el manifiesto de Knowledge son de PR-3.

2.f-ter Crea `scripts/measure_tokens.py` con `tiktoken` y el alcance EXACTO:
         tokens_frontmatter ≤ 250      (frontmatter del SKILL.md)
         tokens_capa0      ≤ 1.200    (cuerpo del SKILL.md, sin frontmatter)
         tokens_turno_max  ≤ 2.500    (capa0 + lente más larga)
       Margen del 15 % por diferencia de tokenizer (tiktoken ≠ tokenizer del
       host). Debe medir TAMBIÉN la versión EN cuando exista (PR-7).

2.g-ter Extiende `scripts/check.py` con la verificación por hash de regiones
       (CANON-EXTRACT vs canónico, AUTHORED vs `generated.lock.json`) y añade
       el check de `measure_tokens.py` a la fase PR-2.

2.g-bis Distribución del dataset a3ref: documenta en `INSTALL.md` cómo obtener
       el dataset (clonar a3ref + `python sqf_wiki_reader.py --update`), el
       estado `SIN_REPLICA` → `NO VERIFICADO`, y la sección "Lo que NO incluye
       esta skill" en el README.

2.h  Test de unicidad Fase 2 activo: 0 definiciones N3 fuera de su canónico,
       extractos CANON-EXTRACT validados por hash, 7 menciones N1 en Capa 0.
       El test `tests/test_canonical_uniqueness.py::test_n3_definitions_not_duplicated_outside_canonical`
       debe dejar de estar omitido (ahora se cumple porque el SKILL.md nuevo
       ya no lleva las definiciones).

2.i  Bloque de Perfil de Proyecto (7 parámetros) como entrada única.
2.j  Actualiza `docs/PARIDAD.md` con el estado real de los ítems afectados
       (los 5 que hoy están `NO VERIFICADO` de PR-2 pasan a `PORTADO`).
2.k  Verifica que `tests/test_skill_structure.py` deja de estar omitido y pasa.

--------------------------------------------------------------------------------
VERIFICACIÓN ANTES DE CERRAR (obligatoria)
--------------------------------------------------------------------------------
    python3 -m pytest tests/ -q
    python3 scripts/check.py --fase PR-2
    python3 -m ruff check .

Los tres deben salir en verde. `check.py --fase PR-2` DEBE devolver exit 0:
ahora falla en "estructura de la skill" porque el SKILL.md aún no está en
capas; al terminar PR-2 tiene que pasar. Si algún test queda OMITIDO en una
fase ya exigida, es un fallo, no un verde.

--------------------------------------------------------------------------------
LO QUE NO DEBES HACER
--------------------------------------------------------------------------------
- No toques `arma3-sqf-review\` (original, solo lectura).
- No hagas push a GitHub ni publiques nada.
- No redefinas en `SKILL.md` las 7 categorías, la puerta, la honestidad, los
  modos, la precedencia ni la propiedad: se CITAN, no se reescriben.
- No crees las lentes como ficheros planos sin regiones AUTHORED/CANON-EXTRACT:
  el test de hash los rechazará.
- No inventes el formato del informe: cópialo de la salida real del motor.
- No borres `agents\` ni `legacy\agents\`: la decisión de qué hacer con el
  plugin legacy está abierta (tarea 1.o, se cierra en PR-7) y no hay git que
  proteja el borrado.
- No añadas dependencias al motor: `skills/arma3-sqf-skill/scripts/` usa solo
  la biblioteca estándar de Python (>=3.11).

--------------------------------------------------------------------------------
CRITERIOS DE ACEPTACIÓN DE ESTA SESIÓN
--------------------------------------------------------------------------------
 1. `check.py --fase PR-2` en verde (exit 0).
 2. `SKILL.md` con frontmatter bilingüe ≤ 250 tokens y cuerpo ≤ 1.200 tokens.
 3. 4 intenciones presentes con su ruta exacta y sus 4 workflows.
 4. 6 lentes con regiones AUTHORED + CANON-EXTRACT y `generated.lock.json`
    coherente.
 5. `report_format.md` idéntico a la salida real del motor.
 6. Los 5 tests omitidos pasan a ejecutarse y quedan en verde.
 7. `docs/PARIDAD.md` y `docs/ESTADO-PR.md` actualizados.

Al terminar, informa: qué cambiaste, el resultado literal de los tres comandos
de verificación, el recuento de tokens medido (frontmatter / capa0 / turno_max)
y cualquier desviación respecto al plan.

================================================================================
FIN DE LA INSTRUCCIÓN
================================================================================
