================================================================================
INSTRUCCIÓN PARA ANTIGRAVITY — PR-5-ter: Cerrar PR-5-bis (documentación real)
                          + completar cobertura M3 + trazabilidad de contexto
================================================================================
Copia este bloque completo en el chat de Antigravity, con la working directory
en la copia de trabajo:

    C:\Users\Touri\Documents\EDEN EDITOR\Skills Antigravity\arma3-sqf-skill

--------------------------------------------------------------------------------
CONTEXTO: QUÉ SE LOGRÓ (auditado hoy por Mavis sobre el estado real del repo)
--------------------------------------------------------------------------------
PR-5-bis está **EJECUTADO Y CORRECTO en su Parte A**. Verificado:

  - `evals/harness.py` ya NO tiene M3 hardcodeado. Se calcula en runtime:
    `m3_str = f"{total_success}/{total_expected_findings} ({falsos_pasa} FALSO_PASA)"`
  - El parámetro `mode` SÍ se usa: filtra trazas por `modo_evaluacion` y cambia
    el cálculo (M2 vs M3) y los literales "N/A (modo ...)".
  - El denominador sale de `expected.json` (`total_expected_findings`), no de la
    traza. Los hallazgos esperados se recorren todos, se detecte o no.
  - `n` se reporta como repeticiones POR GOLDEN (`n_reps`), con modelo/version por
    mayoría y marca "Mixto (...)" si hay más de uno. Ya no sale `traces[0]`.
  - Se añadió el host `antigravity` al harness y a `docs/COMPATIBILIDAD.md`.
  - `tests/test_harness_metrics.py` existe y cubre las 6 situaciones de A.5.
  - Trazas reales en `evals/runs/2026-11-18/antigravity/`:
      * modo ARCHIVO: 14 goldens × 3 repeticiones = 42 trazas (completo)
      * modo PEGADO:  7 goldens × 1 repetición  =  7 trazas (INCOMPLETO)
  - `docs/QUALITY.md` regenerado por el harness (GENERATED, con SOURCE-HASH).
  - `python -m pytest tests/ -q` → **100 passed** (antes 93).
  - `python scripts/check.py --fase PR-5` → exit 0, todas las verificaciones OK
    (el único fallo que había, `test_quality_doc_in_sync_with_harness`, era
    porque se generaron trazas nuevas después del `--write`; regenerado y verde).
  - Modelo real registrado en las trazas: `gemini-3.8-flash-high`, v1.0, temp 0.2.

Lo que NO se ha hecho (es lo que pide este hito):

  A) La documentación de PR-5-bis NO se cerró. `docs/ESTADO-PR.md` sigue
     diciendo "M2: NO VERIFICADO / M3: NO VERIFICADO" y "93 tests", lo cual
     CONTRADICE el estado real medido. Es una regresión de honestidad: el repo
     publica una afirmación obsoleta sobre sus propias métricas.
  B) La cobertura de M3 (modo pegado) es parcial: 7 de 14 goldens, y solo 1
     repetición. `docs/QUALITY.md` publica esa fila como "EVALUADO" sin.warning
     de cobertura parcial → un lector podría creer que M3 cubre los 14 goldens.
     Eso incumple R4 (MÉTRICA + MÉTODO + ESTADO completo).
  C) M2 = 88,9 % queda POR DEBAJO del objetivo documentado (≥ 90 %) y la
     tabla no lo dice. Debe quedar explícito que la métrica NO PASA el objetivo,
     con el detalle de los 2 misses.
  D) `docs/PARIDAD.md` (ítems 11, 12 y 16) y `README.md` (insignia/frase de
     calidad) no reflejan lo medido.
  E) El harness valida que `contexto_cargado` exista y no esté vacío, pero NO
     verifica que el `sha256` declarado coincida con el fichero real. La
     trazabilidad R3 (el contexto fue el que se dice) es declarativa, no verificada.

--------------------------------------------------------------------------------
PARTE A — DOCUMENTACIÓN QUE MENTIRA HOY (BLOQUEANTE, P0)
--------------------------------------------------------------------------------
A.1 `docs/ESTADO-PR.md` — añade la sección "PR-5-bis" (y marca PR-5-bis como
    HECHO-PARCIAL donde corresponda) con el estado REAL:
      - M1: 100,0 % (2/2) — medido.
      - M2 (Antigravity, modo archivo, gemini-3.8-flash-high v1.0):
        88,9 % (mín 83,3 %) sobre 14 goldens × 3 repeticiones = 42 trazas.
        **NO ALCANZA el objetivo ≥ 90 %** → estado "MEDIDO / NO PASA OBJETIVO".
      - M3 (Antigravity, modo pegado): 7/7 (0 FALSO_PASA) pero SOLO sobre
        7 de 14 goldens y N=1 repetición → estado "MEDIDO / COBERTURA PARCIAL".
      - Omisiones: 2. Falsos PASA: 0. Falsos positivos: 0.
      - Suite completa: 100 tests verdes, 0 omitidos.
      - Cita el fichero de trazas: `evals/runs/2026-11-18/antigravity/`
        (ignorado por git por diseño; lo público es `docs/QUALITY.md`).
    Corrige el número de tests (93 → 100) y el bloque "Métricas medidas PR-5"
    que aún dice NO VERIFICADO para M2/M3. ACTUALIZA el bloque "Comandos de
    referencia" (93 → 100).

A.2 `docs/QUALITY.md` — lo regenera el harness, así que el cambio debe hacerse
    EN `evals/harness.py` (la tabla), nunca a mano:
      - Añade a la tabla por host una columna **"Goldens evaluados"** (y, si
        puedes, "Cobertura") que muestre explícitamente 14/14 para modo archivo y
        7/14 para modo pegado.
      - Cuando `goldens_evaluados < total goldens`, el campo `status` DEBE
        incluir el sufijo " (COBERTURA PARCIAL: k/14 goldens)" y el `motivo`
        debe decirlo. Nunca "EVALUADO" a secas sobre cobertura parcial.
      - Cuando la métrica no alcanza su objetivo, el `status` debe decirlo
        (p. ej. "EVALUADO / NO PASA OBJETIVO (88,9 % < 90 %)").
      - `docs/QUALITY.md` regenera con `python evals/harness.py --write` y debe
        seguir pasando `--check`.

A.3 `docs/PARIDAD.md` — actualiza los ítems 11, 12 y 16 al estado que la
    evidencia sostiene. Si la evidencia es "medido en 1 host, cobertura parcial
    en modo pegado", el texto debe decirlo, no "paridad total".

A.4 `README.md` — la insignia y la frase de calidad deben reflejar lo medido:
    - NO afirmes "misma calidad que el plugin original" (R5: solo con tabla por
      host respaldada por trazas, y solo para los hosts medidos).
    - Formulación admitida: "Validado en 1 host (Antigravity / gemini-3.8-flash-high):
      M1 100 % · M2 88,9 % (objetivo ≥ 90 %, no alcanzado) · M3 7/7 con cobertura
      7/14 goldens". Los hosts restantes siguen "NO VERIFICADO" por R1.

A.5 `docs/COMPATIBILIDAD.md` — la fila Antigravity ya existe; revisa que su
    columna de evidencia refleje el estado medido, no "completo" sin más.

--------------------------------------------------------------------------------
PARTE B — COMPLETAR LA COBERTURA DE M3 (P1, requiere que tengas tokens)
--------------------------------------------------------------------------------
La última ejecución de modo pegado murió a mitad (7/14 goldens, error de cuota
"Individual quota reached"). No es un fallo del harness: es la ejecución.

B.1 Completa el modo PEGADO con N=3 repeticiones para los 14 goldens:
      - Inyecta el paquete inline que corresponda al host degradado:
        `integrations/claude/claude_desktop_paste.md` (o el de tu host).
      - Pega SOLO el `code.sqf` (sin `description.ext`): así es como un usuario
        real pegaría el código, y por eso Cat. 5 y Cat. 7 deben salir
        NO_VERIFICADO y NO como bloqueantes inventados.
      - Temperatura efectiva 0,1–0,3. N=3 por golden.
      - Formato de traza EXACTO (lo lee `evals/harness.py`):
        `evals/runs/<YYYY-MM-DD>/antigravity/<golden_id>_pegado_rep<N>.json`
        con: golden_id, host, modelo, version, temperatura, fecha,
        modo_evaluacion ("pegado"), prompt_enviado, respuesta_cruda,
        contexto_cargado: [{archivo, sha256}], repeticion,
        veredicto_por_hallazgo: [{categoria, esperado_linea, detectado_linea,
                                  veredicto, justificacion}]
      - `modelo` = el modelo REAL. Si no lo sabes con certeza: "N/A (modelo no
        identificado)". NUNCA inventes nombre ni versión.
      - NO reveles `expected.json` al modelo que evalúa.

B.2 IMPORTANTE SOBRE EL NOMBRE DE FICHERO: los traces de archivo usan
    `<golden_id>_rep<N>.json` y los de pegado `<golden_id>_pegado_rep<N>.json`.
    Verifica con el harness (no a ojo) que ambas convenciones se leen. Si el
    harness se está comiendo alguna traza pegado por no coincidir con su
    patrón, CORRIGE el harness (no renombres a mano las trazas para taparlo) y
    añade un test que lo bloquee.

B.3 Reingerir y regenerar:
        python evals/harness.py --write
        python evals/harness.py --check

B.4 Documenta en `docs/ESTADO-PR.md` la cobertura final de M3 y el resultado.
    Si M3 no llega al 100 %, publícalo tal cual.

--------------------------------------------------------------------------------
PARTE C — TRAZABILIDAD DEL CONTEXTO (P2, mejora de R3)
--------------------------------------------------------------------------------
C.1 El harness acepta trazas cuyo `contexto_cargado` declare hashes que no
    corresponden a ningún fichero real. Añade verificación:
      - Por cada entrada `{archivo, sha256}`: si la ruta existe en el repo,
        calcular su sha256 y compararlo. Si NO coincide → traza INVÁLIDA (se
        descarta y se cuenta como descartada, con motivo visible en QUALITY.md).
      - Si la ruta no existe, marcarla como "no verificable" (no descartes por
        eso: el host puede haber cargado ficheros de otra ubicación) pero
        contarla en un contador visible.
      - Añade el recuento de trazas "descartadas por contexto no verificable" a
        la tabla o a la sección de honestidad de QUALITY.md.
      - NO invalides todas las trazas actuales si sus rutas no resuelven: usa
        rutas relativas al repo y, si las trazas actuales guardan rutas
        absolutas o externas, migra el formato de las trazas a rutas RELATIVAS
        al repo en la siguiente regeneración (R3 + cero rutas absolutas).
C.2 Añade el test correspondiente en `tests/test_harness_metrics.py`: traza con
    sha256 incorrecto → descartada; traza con sha256 correcto → aceptada.

--------------------------------------------------------------------------------
PARTE D — PENDIENTES DE PRODUCTO QUE SIGUEN ABIERTOS (NO los cierres tú)
--------------------------------------------------------------------------------
Estos dos NO son código y requieren una decisión del usuario. NO los toques, NO
borres nada y NO decidas por tu cuenta. Solo deja constancia en
`docs/ESTADO-PR.md` de que siguen pendientes:

  - Tarea 1.o: qué hacer con `plugin.json` y con los 11 agentes duplicados en
    `agents/` y `legacy/agents/`. Sin repositorio git, borrar es IRREVERSIBLE.
    Es una decisión de producto para PR-7.
  - PR-6 (servidor MCP/FastAPI, Track B) y PR-7 (Release Gate + publicación):
    requieren aprobación explícita del usuario. Nada de push, nada de publicar.

--------------------------------------------------------------------------------
REGLAS INVIABLES
--------------------------------------------------------------------------------
R1. El Release Gate depende solo de validación LOCAL.
R2. Ninguna definición N3 fuera de `references/invariants.md`,
    `references/rubrica.md` y `references/sqf-standards.md`.
R3. Ningún artefacto de host enlaza a un fichero que ese host no pueda leer.
R4. Todo criterio tiene MÉTRICA + MÉTODO + ESTADO (incluido el estado de
    cobertura).
R5. "Igual calidad" solo es publicable con tabla por host respaldada por trazas.
R6. Lo normativo fuera del canónico es GENERATED y verificado por hash.

REGLAS DE TRABAJO:
  - NO toques `arma3-sqf-review\`. NO hagas push ni publiques nada.
  - Solo biblioteca estándar de Python (>=3.11). Ninguna dependencia nueva.
  - Cero rutas absolutas. Un test SKIPPED en fase ya exigida = FALLO.
  - NO modifiques la Capa 0 (1.186/1.200, 14 tokens de margen) ni los canónicos.
  - `evals/runs/` sigue en `.gitignore`: lo público es `docs/QUALITY.md`.
  - NO escribas ninguna métrica a mano: ni en el harness, ni en QUALITY.md, ni
    en ESTADO-PR.md. Si el harness no la calcula, hay que programarla.
  - NO inventes nombres de modelo ni de versión. Si no lo sabes: "N/A".
  - NO marques verde un host sin trazas.
  - NO ajustes `expected.json` para que la métrica pase (cambiar un esperado =
    cambiar el contrato → revisar el canónico y regenerar hashes).

--------------------------------------------------------------------------------
VERIFICACIÓN ANTENES DE CERRAR (obligatoria)
--------------------------------------------------------------------------------
    python -m pytest tests/ -q
    python scripts/check.py --fase PR-5
    python -m ruff check .
    python evals/harness.py --check
    python scripts/generate_inline_packages.py --check
    python scripts/measure_tokens.py

Los seis en verde. Además:
  - `docs/QUALITY.md` debe mostrar cobertura explícita (goldens evaluados) y el
    estado real de M2 (88,9 %, NO PASA OBJETIVO ≥ 90 %) y M3 (7/7 con cobertura
    7/14 si no completaste B.1).
  - `docs/ESTADO-PR.md` no debe contener ninguna afirmación "NO VERIFICADO"
    sobre M2/M3 que contradiga `docs/QUALITY.md`.
  - Ningún documento debe afirmar "misma calidad" sin la tabla por host.

--------------------------------------------------------------------------------
CRITERIOS DE ACEPTACIÓN
--------------------------------------------------------------------------------
 1. `docs/ESTADO-PR.md` refleja el estado real medido (M1 100 %, M2 88,9 %
    NO PASA OBJETIVO, M3 7/7 cobertura 7/14, 100 tests, modelo real).
 2. `docs/QUALITY.md` expone la cobertura por host y marca explícitamente
    cobertura parcial y objetivo no alcanzado. Regenerado por el harness.
 3. `docs/PARIDAD.md` (11, 12, 16) y `README.md` actualizados a lo que la
    evidencia sostiene, sin afirmaciones de paridad total.
 4. (Si hay tokens) Modo pegado completo: 14 goldens × 3 repeticiones, M3
    recalculado por el harness, cobertura 14/14.
 5. El harness verifica el sha256 de `contexto_cargado` y el test lo bloquea.
 6. `check.py --fase PR-5` en verde (exit 0), 0 tests omitidos, `ruff` limpio.

Al terminar, informa: qué documentaste, la salida literal de los seis comandos,
la tabla de `docs/QUALITY.md` completa, el número de goldens y repeticiones
realmente ejecutados por modo, el modelo real usado y las omisiones/falsos PASA
observados. Si algo no se pudo medir, dilo sin maquillarlo: ese es el objetivo.

================================================================================
FIN DE LA INSTRUCCIÓN
================================================================================
