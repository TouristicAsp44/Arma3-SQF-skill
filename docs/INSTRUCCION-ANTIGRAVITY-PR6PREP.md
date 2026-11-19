================================================================================
INSTRUCCIÓN PARA ANTIGRAVITY — PR-6-PREP: Cerrar la medición (M3 completo)
                         + preparar el Release Gate PR-7 (SIN publicar)
================================================================================
Copia este bloque completo en el chat de Antigravity, con la working directory
en la copia de trabajo:

    C:\Users\Touri\Documents\EDEN EDITOR\Skills Antigravity\arma3-sqf-skill

--------------------------------------------------------------------------------
CONTEXTO: QUÉ SE HA CERRADO HOY (auditado y verificado por Mavis)
--------------------------------------------------------------------------------
La documentación que mentía ya no miente, y el harness ahora verifica la
reproducibilidad del contexto. Estado real y verificado:

  - `python scripts/check.py --fase PR-5` → exit 0, **105/105 tests verdes**.
  - `python -m ruff check .` → All checks passed.
  - `python scripts/generate_inline_packages.py --check` → OK.
  - `python evals/harness.py --check` → OK (docs/QUALITY.md sincronizado).
  - `python scripts/measure_tokens.py` → frontmatter 184/250 · Capa 0 1.186/1.200 ·
    lente más larga 480 · turno máx 1.666/2.500. **Presupuesto intacto.**
  - `docs/QUALITY.md` REGENERADO por el harness. Ahora publica:
      * columna **Cobertura** (goldens evaluados / 14);
      * `EVALUADO / NO PASA OBJETIVO (88.9 % < 90.0 %)` para M2;
      * `EVALUADO / COBERTURA PARCIAL (7/14 goldens)` para M3;
      * sección 4 "Cobertura, Límites y Trazabilidad (R3, R4)".
  - **Trazabilidad R3 implementada:** el harness recalcula el sha256 de cada
    fichero declarado en `contexto_cargado` (normalizando CRLF→LF, porque el
    checkout en Windows usa CRLF y el hash se calculó sobre el contenido
    lógico) y **descarta la traza si el hash no coincide**.
    Resultado sobre las 49 trazas actuales: **0 descartadas** → todas son
    reproducibles contra el repo actual.
  - `docs/ESTADO-PR.md`, `docs/PARIDAD.md` (ítems 11, 12, 16 + sección E-bis),
    `docs/COMPATIBILIDAD.md` (sección 3 nueva: estado de evidencia por host) y
    `README.md` (insignia + nota de evidencia) actualizados a lo que la
    evidencia sostiene. **Ya no se afirma "misma calidad"** en ningún sitio.

Métricas publicadas ahora mismo:

  | Métrica | Modo | Resultado | Objetivo | Estado |
  | :--- | :--- | :--- | :--- | :--- |
  | M1 | Script determinista | 100,0 % (2/2) | 100 % | PASA |
  | M2 | Archivo (14/14 goldens, N=3, 42 trazas) | 88,9 % (mín 83,3 %) | ≥ 90 % | NO PASA OBJETIVO |
  | M3 | Pegado (7/14 goldens, N=1, 7 trazas) | 7/7, 0 FALSO_PASA | 100 % | COBERTURA PARCIAL |

Host único ejecutado: **Antigravity**, modelo real **`gemini-3.8-flash-high`** v1.0,
temperatura 0,2. Los otros seis hosts siguen en `NO VERIFICADO` (R1).

Este hito tiene TRES partes, en este orden:

--------------------------------------------------------------------------------
PARTE A — COMPLETAR LA MEDICIÓN DE M3 (P0, es lo único que exige modelo)
--------------------------------------------------------------------------------
La última ejecución de modo pegado murió por cuota tras 7 de 14 goldens. Hay que
terminarla. Nada de esto lo puede hacer Mavis: requiere ejecutar el modelo.

A.1 Ejecuta los 14 goldens en MODO PEGADO con N=3 repeticiones.
    Procedimiento (protocolo en `evals/GOLDENS-PROTOCOL.md`):
      - Inyecta el paquete inline del host degradado:
        `integrations/gemini/system_instruction.md` (el que se usó la última vez)
        o `integrations/chatgpt/custom_gpt_instructions.md`.
      - Pega SOLO el `code.sqf` (sin `description.ext`): es lo que haría un
        usuario real, y por eso Cat. 5 y Cat. 7 deben salir `NO VERIFICADO` y
        NO como bloqueantes inventados.
      - Temperatura efectiva 0,1–0,3. N=3 por golden.
      - NO reveles `expected.json` al modelo que evalúa.
      - Si vuelves a quedarte sin cuota a mitad, **no inventes** las trazas que
        faltan: deja la cobertura parcial tal cual y sigue con la Parte B.

A.2 Formato de traza (lo lee `evals/harness.py`):
      `evals/runs/<YYYY-MM-DD>/antigravity/<golden_id>_pegado_rep<N>.json`
    con: golden_id, host, modelo, version, temperatura, fecha,
    modo_evaluacion ("pegado"), prompt_enviado, respuesta_cruda,
    contexto_cargado: [{archivo, sha256}], repeticion,
    veredicto_por_hallazgo: [{categoria, esperado_linea, detectado_linea,
                              veredicto, justificacion}]
      - `modelo` = el MODELO REAL. Si no lo sabes con certeza:
        "N/A (modelo no identificado)". **NUNCA inventes nombre ni versión.**
      - **El `sha256` de `contexto_cargado` debe ser el del fichero tal y como
        lo lee Python con `read_text(encoding="utf-8")`** (saltos de línea
        normalizados a LF). Si lo calculas con otra herramienta sobre los bytes
        crudos en Windows, te dará CRLF y el harness descartará la traza.
        La forma correcta:
            python -c "import hashlib,pathlib;print(hashlib.sha256(pathlib.Path('integrations/gemini/system_instruction.md').read_text(encoding='utf-8').encode('utf-8')).hexdigest())"

A.3 Reingerir y regenerar:
        python evals/harness.py --write
        python evals/harness.py --check
    La fila de M3 debe pasar a cobertura 14/14. Si el harness no consume
    alguna traza, **corrige el harness** (no renombres trazas a mano) y añade el
    test que lo bloquee.

A.4 Documenta el resultado en `docs/ESTADO-PR.md` (sección PR-5-bis), incluido
    el caso de que M3 no llegue al 100 %: publícalo tal cual.

--------------------------------------------------------------------------------
PARTE B — CERRAR LA BRECHA DE M2 (P1, opcional, requiere más cuota)
--------------------------------------------------------------------------------
M2 = 88,9 % con 2 omisiones, por debajo del objetivo ≥ 90 %. Comprueba primero
si las 2 omisiones son **errores reales del modelo** o **ambigüedades del
ground truth**:

B.1 Localiza los 2 misses concretos (los goldens y hallazgos omitidos) y
    clasifícalos en una de estas dos categorías:
      - **Fallo real del modelo:** el modelo no detectó un bloqueante que el
        canónico sí define. → Es un dato de calidad: se documenta, no se toca
        el canónico.
      - **Ambigüedad del contrato:** el `expected.json` exige un bloqueante que
        el enunciado del golden no permite inferir (p. ej. depende de
        `description.ext` ausente o de un perfil de proyecto no declarado).
        → **NO cambies `expected.json` para maquillar la métrica.** Lo correcto
        es (a) dejarlo como está, (b) documentar el caso en
        `docs/ESTADO-PR.md` como "limitación del dataset", y (c) si el
        canónico realmente dice algo distinto de lo que el golden codifica,
        **eso es un bug del dataset**: propón el cambio en `expected.json` con
        su justificación explícita, esperando aprobación. Cambiar un esperado
        cambia el contrato → revisar el canónico y regenerar hashes.

B.2 Si hay margen de cuota, repite el modo archivo con N=3 sobre los goldens
    afectados para ver si el fallo es estable o fluctuante. Documenta la
    dispersión.

B.2-bis **FIDELIDAD DE LA EVIDENCIA: 8 DE LAS 49 TRAZAS EXISTENES CITAN UNA RUTA
DE LINTER QUE NO EXISTE (auditoría de Mavis, 2026-11-19).**
    8 trazas de `evals/runs/2026-11-18/antigravity/` declara en su informe:
        "SQFLINT: skills/arma3-sqf-review/references/run_sqflint.py (disponible, rc=0)"
    Esa ruta **no existe** en el repo portado (la ruta real es
    `skills/arma3-sqf-skill/references/run_sqflint.py`). Es decir: esos informes
    declaran haber ejecutado un linter en una ruta inexistente y aun así
    reportan "rc=0" y "Item 1 PASA". Esa evidencia **no es reproducible** y
    debilita la trazabilidad de M2 (el harness verifica el `contexto_cargado`
    declarado, pero no las rutas que el modelo afirma en su informe).

    Al repetir la medición:
      - Asegúrate de que el informe cite SIEMPRE la ruta real
        `skills/arma3-sqf-skill/references/run_sqflint.py` (o la que resuelva
        `--mode-query`), nunca una ruta heredada del plugin original.
      - Si el linter no está disponible, el informe debe decirlo y marcar ese
        ítem como `NO VERIFICADO` (Principio de Honestidad Técnica), nunca
        "disponible, rc=0".
      - Opcionalmente, amplía el harness con un check que detecte en las
        respuestas del modelo rutas del plugin original (`arma3-sqf-review`) y
        las compte como evidencia no reproducible, para que la calidad se mida
        sobre lo que realmente se ejecutó.
      - Documenta en `docs/ESTADO-PR.md` cuántas trazas de la medición nueva
        tienen evidencia de linter verificable, junto a las 8 antiguas que no
        la tienen.

B.3 En ningún caso ajustes el objetivo (90 %), el harness ni el dataset para
    que la métrica pase. La política de iteración del port (máx. 3 iteraciones)
    se respeta: si tras esto el gate sigue en rojo, se documenta
    `NO VERIFICADO`/`NO PASA OBJETIVO` con su límite y se publica con esa
    limitación explícita.

--------------------------------------------------------------------------------
PARTE C — PREPARAR EL RELEASE GATE PR-7 (P1, SIN publicar NADA)
--------------------------------------------------------------------------------
El objetivo es dejar el paquete listo para publicar, con la evidencia real y
las limitaciones declaradas. **Nada de push, nada de release, nada de publicar
en marketplaces.** La publicación requiere la aprobación explícita del usuario
en una fase posterior.

C.1 Checklist de entrega (`references/checklist-entrega.md`): repásalo y deja
    constancia de los ítems A–I con su estado real.

C.2 Paquete distribuible: verifica que el contenido publicable es coherente y
    no arrastra artefactos de trabajo:
      - `skills/arma3-sqf-skill/` (SKILL.md + references/ + scripts/)
      - `integrations/` (14 artefactos)
      - `docs/` (COMPATIBILIDAD, ESTADO-PR, PARIDAD, QUALITY, SMOKE-RESULTS,
        WIKI-DB)
      - `evals/goldens/` + `evals/harness.py` + `evals/GOLDENS-PROTOCOL.md`
      - `README.md`, `INSTALL.md`, `CONTRIBUTING.md`, `LICENSE`, `MANIFEST.in`
      - `evals/runs/` **NO** se publica (está en `.gitignore`): lo público es
        `docs/QUALITY.md`. Comprueba que el `.gitignore` y `MANIFEST.in` lo
        excluyen de verdad.
      - `skills/arma3-sqf-skill/references/wiki-cache.md` y cualquier cache
        local: NO debe distribuirse.

C.3 Tarea 1.o — **NO LA EJECUTES, SOLO PREPARA LA DECISIÓN.** Hay 11 agentes
    duplicados en `agents/` y en `legacy/agents/`, más un `plugin.json` de
    estilo plugin que ya no describe este producto (ahora es una skill
    universal). Sin repositorio git, borrar es IRREVERSIBLE.
      - Redacta en `docs/ESTADO-PR.md` una sección "Decisión pendiente 1.o" con
        las opciones y sus consecuencias:
          A) Mantener `agents/` como fuente y borrar `legacy/agents/`.
          B) Mantener `legacy/agents/` como histórico y borrar `agents/`.
          C) Mantener ambos y documentar la duplicación.
          D) Fusión: elegir la versión canónica de cada agente.
        + Qué hacer con `plugin.json` (mantenerlo, moverlo a `legacy/`, o
          retirarlo) y qué implica para cada host.
      - **NO borres, NO muevas y NO edites** `agents/`, `legacy/agents/` ni
        `plugin.json`. La decisión es del usuario.

C.4 Decide y documenta la **versión de la skill** y la **fecha de release** en
    `docs/ESTADO-PR.md` como propuesta (no aplicada).

C.5 Checklist de publicación: una sección nueva en `docs/ESTADO-PR.md` que
    liste, en orden, los pasos que faltan para publicar (crear repo git,
    tag, publicar en los marketplaces de cada host) y que marque cada uno como
    "pendiente de aprobación del usuario". Ningún paso se ejecuta.

C.6 Revisa que `README.md`, `INSTALL.md` y `docs/COMPATIBILIDAD.md` no
    afirmen nada que la evidencia no sostenga. En particular: nada de "misma
    calidad", nada de "soportado en 6 hosts" sin el matiz `NO VERIFICADO`.

--------------------------------------------------------------------------------
REGLAS INVIABLES
--------------------------------------------------------------------------------
R1. El Release Gate depende solo de validación LOCAL.
R2. Ninguna definición N3 fuera de `references/invariants.md`,
    `references/rubrica.md` y `references/sqf-standards.md`.
R3. Ningún artefacto de host enlaza a un fichero que ese host no pueda leer.
R4. Todo criterio tiene MÉTRICA + MÉTODO + ESTADO (incluido el de cobertura).
R5. "Igual calidad" solo es publicable con tabla por host respaldada por trazas.
R6. Lo normativo fuera del canónico es GENERATED y verificado por hash.

REGLAS DE TRABAJO:
  - NO toques `arma3-sqf-review\`. **NO hagas push. NO publiques nada.**
  - Solo biblioteca estándar de Python (>=3.11). Ninguna dependencia nueva.
  - Cero rutas absolutas. Un test SKIPPED en fase ya exigida = FALLO.
  - NO modifiques la Capa 0 (1.186/1.200, 14 tokens de margen) ni los canónicos.
  - NO escribas ninguna métrica a mano: ni en el harness, ni en QUALITY.md, ni
    en ESTADO-PR.md. Si el harness no la calcula, hay que programarla.
  - NO inventes nombres de modelo ni de versión. Si no lo sabes: "N/A".
  - NO marques verde un host sin trazas.

--------------------------------------------------------------------------------
VERIFICACIÓN ANTES DE CERRAR (obligatoria)
--------------------------------------------------------------------------------
    python -m pytest tests/ -q
    python scripts/check.py --fase PR-5
    python -m ruff check .
    python evals/harness.py --check
    python scripts/generate_inline_packages.py --check
    python scripts/measure_tokens.py

Los seis en verde. Además:
  - `docs/QUALITY.md` con la cobertura real de M3 (14/14 si completaste A.1) y
    M2 con su veredicto de objetivo.
  - `docs/ESTADO-PR.md` sin afirmaciones que contradigan `docs/QUALITY.md`.
  - `docs/ESTADO-PR.md` con la sección "Decisión pendiente 1.o" y el checklist de
    publicación, ambos sin nada ejecutado.

--------------------------------------------------------------------------------
CRITERIOS DE ACEPTACIÓN
--------------------------------------------------------------------------------
 1. M3 medido sobre 14 goldens x 3 repeticiones (o, si la cuota volvió a
    cortarse, cobertura parcial explícita y sin trazas inventadas).
 2. Las 2 omisiones de M2 clasificadas: fallo real del modelo vs ambigüedad del
    dataset, con la decisión razonada y sin maquillar la métrica.
 3. `docs/QUALITY.md` regenerado por el harness y en `--check` verde.
 4. Checklist de entrega A–I repasado con estado real.
 5. Paquete distribuible verificado: sin caches, sin `evals/runs/`, con los
    artefactos correctos en su sitio.
 6. Decisión 1.o **documentada, no aplicada** (agents/, legacy/agents/,
    plugin.json intactos).
 7. Checklist de publicación redactado, **sin ejecutar nada**.
 8. `check.py --fase PR-5` en verde (exit 0), 0 tests omitidos, `ruff` limpio.

Al terminar, informa: qué mediste (números reales por modo), la salida literal
de los seis comandos, la tabla completa de `docs/QUALITY.md`, el modelo real
usado, la clasificación de los 2 misses de M2, y qué queda pendiente de
decisión del usuario. Si algo no se pudo medir, dilo sin maquillarlo: ese es el
objetivo del hito.

================================================================================
FIN DE LA INSTRUCCIÓN
================================================================================
