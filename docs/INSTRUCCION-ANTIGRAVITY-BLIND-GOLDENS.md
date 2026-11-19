================================================================================
INSTRUCCIÓN PARA ANTIGRAVITY — TRACK C: Goldens NO señalizados (medición real)
                       + regla estricta de modo pegado + fidelidad del linter
================================================================================
Copia este bloque completo en el chat de Antigravity, con la working directory
en la copia de trabajo:

    C:\Users\Touri\Documents\EDEN EDITOR\Skills Antigravity\arma3-sqf-skill

Este track es el que **cierra la última limitación metodológica** del producto.
Va después del Track A (medición, ya hecho) y es la condición para que la
afirmación de calidad publicable sea defendible.

--------------------------------------------------------------------------------
CONTEXTO: QUÉ SE MIDIÓ Y QUÉ SIGNIFICA (auditoría de Mavis, 2026-11-19)
--------------------------------------------------------------------------------
Estado actual tras la corrección del arnés:

  | Métrica | Modo | Cobertura | Resultado | Objetivo | Estado |
  | :--- | :--- | :--- | :--- | :--- | :--- |
  | M1 | Script determinista | 2/2 | 100 % | 100 % | PASA |
  | M2 | Archivo | 14/14 goldens, N=3 (42 trazas) | **100,0 %** | ≥ 90 % | PASA |
  | M3 | Pegado | 14/14 goldens, N=3 (42 trazas) | **33/33**, 0 FALSO_PASA | 100 % | PASA |

  84 trazas reproducibles en `evals/runs/2026-11-18/antigravity/` (0 descartadas por hash).

**Corrección aplicada a M2.** El 88,9 % publicado anteriormente era un artefacto del
instrumento: el clasificador de categorías buscaba por subcadena, y `"ace"` coincide dentro de
"interf**ace**s" (→ Cat. 7) mientras `"ui"` coincide dentro de "arq**ui**tectura" (→ Cat. 3). El
modelo detectaba el bloqueante de `g07` en las 3 repeticiones; el arnés lo contaba como omisión.
Corregido a raíces por token (`classify_discipline()`) + test de 8 casos. **M2 = 100 %** sobre las
mismas trazas, sin tocar `expected.json` ni ningún golden.

**LIMITACIÓN METODOLÓGICA (esto es lo que cierra este track).**
  13 de los 14 goldens son **señalizados**: su `code.sqf` incluye un comentario que describe el
  defecto, por ejemplo:
      g02:  // waitUntil sin timeout ni garantía de salida
      g05:  // Los Event Handlers del motor corren en contexto unscheduled (canSuspend == false)
      g06:  // fnc_unauthorizedRemote no está en la whitelist de CfgRemoteExec (mode = 1)
      g08:  // Inyección de función CBA_fnc_* en proyecto configurado como CBA: no
  Es decir: **el propio enunciado le dice al modelo cuál es el defecto**. Lo que M2 y M3 miden
  hoy es, por tanto:
      - la CONFORMIDAD del informe (categoría, severidad, formato v1, disciplina), y
      - la AUSENCIA DE falsos positivos (acreditada por los goldens limpios g09–g11: 0).
  Y **NO** miden la detección a ciega de defectos sutiles. Afirmar con estas cifras que "la skill
  encuentra cualquier defecto de SQF" sería una afirmación **no respaldada por la evidencia**,
  justo lo que R5 prohíbe.
  Consecuencia colateral grave: los goldens g06 (CfgRemoteExec) y g08 (CBA) declaran en su
  `expected.json` `verificable_en: ["archivo"]` —porque en un caso real de modo pegado NO hay
  `description.ext` ni perfil de proyecto— pero su propio comentario **sí** aporta ese contexto.
  Por eso el modelo puede (y debe) responder BLOQUEANTE sin inventar nada, y el 33/33 no es
  una trampa, pero **tampoco mide el comportamiento honesto** que se quiere medir: "sin contexto
  de proyecto, ¿reportas NO VERIFICADO en lugar de afirmar un bloqueante?".

--------------------------------------------------------------------------------
PARTE A — GOLDENS NO SEÑALIZADOS (P0: el trabajo central)
--------------------------------------------------------------------------------
A.1 Crea **6 goldens nuevos** en `evals/goldens/` con identificadores `b01`..`b06`, sin
    comentarios que describan el defecto. Reglas:
      - El `code.sqf` NO puede contener ningún comentario que nombre la categoría ni el
        defecto (nada de "waitUntil sin timeout", "sin private", "no está en la whitelist").
      - SÍ puede contener comentarios inocuos y neutros (nombres de variables, contexto de la
        función, "// proyecto de misión"). Lo que no puede es dar la respuesta.
      - Extensión y complejidad **equivalentes** a los goldens existentes, para que el
        dataset sea comparable.
      - Cada golden debe tener su `expected.json` con `categoria`, `archivo`, `linea`,
        `severidad`, `disciplina`, `descripcion` y `verificable_en` **correctos**: si el
        defecto depende de `description.ext` o de un perfil de proyecto, `verificable_en` debe
        ser `["archivo"]` (no verificable en pegado).
      - Añade además `description.ext` en los goldens que lo necesiten (como g06), para que en
        modo archivo el defecto sea confirmable.

    Cobertura mínima de los 6 (1 por categoría crítica, sin señalizar):
      - **b01_scope**: variable global sin `private` ni `params` (Cat. 1).
      - **b02_softlock**: `waitUntil` sin condición de salida alcanzable (Cat. 2).
      - **b03_player_servidor**: `player` usado en ruta que corre en servidor dedicado, sin
        guarda (Cat. 3).
      - **b04_unscheduled**: `sleep`/`uiSleep` dentro de un handler de motor (Cat. 4).
      - **b05_remoteexec**: `remoteExec` a una función; el defecto **solo** es confirmable
        con el `description.ext` que define la whitelist (Cat. 5, `verificable_en: ["archivo"]`).
      - **b06_dependencia**: llamada a `CBA_fnc_*` con el perfil del proyecto **declarado
        dentro del propio `code.sqf`** (Cat. 7). Ojo: aquí el contexto SÍ está en el fragmento,
        así que el defecto **es** verificable en pegado: `verificable_en: ["archivo","pegado"]`.

A.2 **Verifica que los goldens nuevos no están señalizados.** El harness ya cuenta los
    goldens señalizados (`count_signaled_goldens()`), y `docs/QUALITY.md` §5 lo publica. Añade un
    test que falle si un golden **no señalizado** (los `b*`) contiene un comentario con una raíz
    de categoría (`waituntil`, `private`, `scope`, `whitelist`, `cba`, `player`, `sleep`,
    `unscheduled`, `remoteexec`, `contrato`...). Es el blindaje de que el dataset no se contamine.

A.3 Ejecuta los 6 goldens nuevos en **ambos modos**, N=3 repeticiones cada uno
    (6 × 3 × 2 = 36 trazas nuevas), con el mismo procedimiento y formato de traza de siempre.
      - `evals/runs/<YYYY-MM-DD>/antigravity/b01_scope_rep1.json` …
      - `evals/runs/<YYYY-MM-DD>/antigravity/b01_scope_pegado_rep1.json` …
    Modelo real: el mismo (`gemini-3.8-flash-high` v1.0, temperatura 0,2). Si el modelo cambia,
    **decláralo**: el harness reporta "Mixto" y eso es información, no un problema.

--------------------------------------------------------------------------------
PARTE B — REGLA ESTRICTA DE MODO PEGADO (P0, junto con A)
--------------------------------------------------------------------------------
B.1 Endurece el arnés para el dataset **no señalizado**:
      - En modo pegado, si un hallazgo esperado tiene `verificable_en` que **no** incluye
        "pegado" y el modelo afirma `[BLOQUEANTE]`, eso **NO es una detección**: es un
        **FALSO_PASA** (el modelo afirma como verificado algo que el fragmento no permite
        verificar). Suma a `falsos_pasa`, no al numerador.
      - Si el modelo responde `[NO_VERIFICADO]` con motivo → cuenta como acierto justificado
        (comportamiento correcto).
      - Si no dice nada → omisión.
    Hoy el orden del código hace que un BLOQUEANTE coincidente "gane" antes de aplicar esta
    regla; hay que **mirar la regla de verificabilidad ANTES de aceptar el emparejamiento**.

B.2 Esta regla **debe cambiar el resultado de `b05_remoteexec` en modo pegado** y ese es el
    objetivo: se mide si el modelo, sin `description.ext`, reporta `NO VERIFICADO` en vez de
    inventar un bloqueante. **Si el modelo lo hace bien, b05 aporta su acierto honesto. Si lo
    hace mal, el FALSO_PASA queda registrado y publicado** — que es exactamente lo que hay que
    saber y no hay que maquillar.

B.3 No apliques la regla estricta al dataset señalizado existente (g01–g13): sus comentarios
    aportan el contexto de proyecto, así que un BLOQUEANTE ahí sí es una detección legítima.
    Implementa la distinción de forma explícita y documentada en el código (por ejemplo,
    evaluando si el golden aporta el contexto), **no** por caso especial.

B.4 Para que el informe sea legible, **separa los dos datasets**:
      - Dataset señalizado (g01–g13): mide conformidad del informe y ausencia de falsos
        positivos. Es lo que ya está medido (M2 100 %, M3 33/33).
      - Dataset no señalizado (b01–b06): mide detección a ciega y honestidad del reporte
        `NO VERIFICADO` en modo pegado. Es la cifra que falta.
    El informe `docs/QUALITY.md` debe publicar **ambos bloques por separado**, con su cobertura
    y su estado. El objetivo del dataset no señalizado no se fija por adelantado: se mide y se
    publica lo que salga.

--------------------------------------------------------------------------------
PARTE C — FIDELIDAD DEL EVIDENCIA DEL LINTER (P1)
--------------------------------------------------------------------------------
C.1 8 de las 49 trazas originales (de 49; hoy 84 en total) declaran en su informe:
      "SQFLINT: skills/arma3-sqf-review/references/run_sqflint.py (disponible, rc=0)"
    Esa ruta **no existe** en el repo portado (la real es
    `skills/arma3-sqf-skill/references/run_sqflint.py`): su evidencia de linter no es
    reproducible aunque el hash del contexto sí lo sea.

C.2 Opciones (elige una y documéntala):
      - (a) **Re-ejecutar** las trazas afectadas y volver a generarlas con la ruta real.
      - (b) **Documentar** la limitación: en esas 8 trazas, el ítem 1 del checklist de entrega
        ("análisis estático con linter") no es evidencia verificable, aunque la métrica M2/M3
        no dependa de ello (M2/M3 miden hallazgos del modelo, no la salida del linter).
      En ambos casos, deja constancia en `docs/ESTADO-PR.md`.

C.3 Opcional pero recomendable: un check en el harness que detecte en `respuesta_cruda` rutas
    del plugin original (`arma3-sqf-review`) y las cuente como "evidencia no reproducible",
    publicándolas en `docs/QUALITY.md`. Así el próximo caso se ve solo.

--------------------------------------------------------------------------------
PARTE D — INFORME Y DOCUMENTACIÓN (P0)
--------------------------------------------------------------------------------
D.1 `docs/QUALITY.md` (generado por el harness, **no lo edites a mano**):
      - Bloque 1: dataset señalizado (g01–g13) — cobertura, M2, M3, estado.
      - Bloque 2: dataset no señalizado (b01–b06) — cobertura, M2, M3, falsos PASA, estado.
      - §5 debe actualizarse con los dos conteos de goldens señalizados (13 de 19 y 0 de 6).
      - La sección de honestidad debe decir explícitamente qué mide cada bloque.

D.2 `docs/ESTADO-PR.md`: sección "Track C — Medición no señalizada" con los resultados reales
    de los dos bloques, los falsos PASA (si los hay) y la resolución del punto C.2.

D.3 `README.md`: la insignia y la nota de evidencia deben reflejar los **dos** bloques y decir
    cuál es la afirmación publicable. Si el dataset no señalizado da un porcentaje bajo, se
    publica tal cual: es la medición honesta de la detección a ciega.

D.4 `docs/PARIDAD.md` (sección E-bis) y `docs/COMPATIBILIDAD.md`: sincronizar con los dos
    bloques y con la limitación metodológica.

--------------------------------------------------------------------------------
REGLAS INVIABLES
--------------------------------------------------------------------------------
R1. El Release Gate depende solo de validación LOCAL.
R2. Ninguna definición N3 fuera de `references/invariants.md`,
    `references/rubrica.md` y `references/sqf-standards.md`.
R3. Ningún artefacto de host enlaza a un fichero que ese host no pueda leer.
R4. Todo criterio tiene MÉTRICA + MÉTODO + ESTADO.
R5. "Igual calidad" solo es publicable con tabla por host respaldada por trazas.
R6. Lo normativo fuera del canónico es GENERADO y verificado por hash.

REGLAS DE TRABAJO:
  - NO toques `arma3-sqf-review\`. **NO hagas push. NO publiques nada.**
  - Solo biblioteca estándar de Python (>=3.11). Ninguna dependencia nueva.
  - Cero rutas absolutas. Un test SKIPPED en fase ya exigida = FALLO.
  - **NO modifiques la Capa 0** (1.186/1.200) ni los canónicos.
  - **NO cambies `expected.json` de los goldens existentes** (g01–g13) para alterar métricas.
    Si detectas que su `verificable_en` es incoherente con el contenido del golden (caso g06 y
    g08), **propón el cambio con su justificación** y espera aprobación explícita: cambiar un
    esperado cambia el contrato. No lo apliques por tu cuenta.
  - NO inventes nombres de modelo ni de versión. NO escribas métricas a mano.
  - La medición existente (M1/M2/M3 del dataset señalizado) **no se toca** salvo que el arnés
    lo recalcule por sí mismo.

--------------------------------------------------------------------------------
VERIFICACIÓN ANTES DE CERRAR (obligatoria)
--------------------------------------------------------------------------------
    python -m pytest tests/ -q
    python scripts/check.py --fase PR-5
    python scripts/check.py --fase PR-6
    python scripts/check.py --fase PR-7
    python -m ruff check .
    python evals/harness.py --check
    python scripts/generate_inline_packages.py --check
    python scripts/measure_tokens.py

Los ocho en verde. Además:
  - `docs/QUALITY.md` con los dos bloques de dataset y sin ambigüedad sobre qué mide cada uno.
  - `evals/runs/` con las 36 trazas nuevas de los 6 goldens no señalizados.

--------------------------------------------------------------------------------
CRITERIOS DE ACEPTACIÓN
--------------------------------------------------------------------------------
 1. 6 goldens no señalizados (`b01`–`b06`) creados, con `expected.json` correcto, y con test
    que falle si un `b*` contiene un comentario revelador.
 2. 36 trazas nuevas (6 goldens × 2 modos × 3 repeticiones), reproducibles y con modelo real.
 3. Regla estricta de modo pegado implementada y aplicada **antes** del emparejamiento, con
    test que lo demuestre (un BLOQUEANTE sobre un hallazgo no verificable en pegado = FALSO_PASA).
 4. `docs/QUALITY.md` con dos bloques separados (señalizado / no señalizado), cada uno con
    cobertura, métrica y estado; nada escrito a mano.
 5. Punto C.2 resuelto (re-ejecución o documentación) y registrado.
 6. Los ocho comandos en verde; Capa 0 sin tocar.

Al terminar, informa: los dos bloques de resultados con sus cifras, cuántos falsos PASA
aparecieron en el dataset no señalizado (y si el modelo》报道 `NO_VERIFICADO` donde debía),
la salida literal de los ocho comandos y qué afirmación de calidad queda publicable con esa
evidencia. Si el resultado es malo, publícalo tal cual: esa es la razón de medirlo.

================================================================================
FIN DE LA INSTRUCCIÓN
================================================================================
