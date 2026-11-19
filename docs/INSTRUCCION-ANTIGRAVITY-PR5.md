================================================================================
INSTRUCCIÓN PARA ANTIGRAVITY — PR-5: Evals Formales, Goldens y docs/QUALITY.md
================================================================================
Copia este bloque completo en el chat de Antigravity, con la working directory
en la copia de trabajo:

    C:\Users\Touri\Documents\EDEN EDITOR\Skills Antigravity\arma3-sqf-skill

--------------------------------------------------------------------------------
CONTEXTO Y ESTADO (verificado hoy)
--------------------------------------------------------------------------------
Port del plugin Antigravity `arma3-sqf-review` a una skill portable.

- ORIGINAL (SOLO LECTURA, NO TOCAR NUNCA):
  `C:\Users\Touri\Documents\EDEN EDITOR\Skills Antigravity\arma3-sqf-review\`
- TRABAJO: `C:\Users\Touri\Documents\EDEN EDITOR\Skills Antigravity\arma3-sqf-skill\`
- PR-1..PR-4: CERRADOS Y EN VERDE. `python scripts/check.py --fase PR-4` → exit 0,
  86/86 tests verdes, `ruff check .` limpio, paquete inline P1–P4 verificado.
- Tokens: frontmatter 184/250 · Capa 0 1.186/1.200 · turno máx 1.666/2.500.
- DB de conocimiento: `~/.a3ref/arma3_wiki.db` (58,42 MB, fts_enabled=1).

RESTRICCIÓN DEL ENTORNO (verificada): en esta máquina NO hay ninguna CLI de
modelo (`claude`, `gemini`, `codex` no están en el PATH) ni variables de entorno
con claves de API. Por tanto la evaluación con modelo real NO puede ejecutarse
aquí: el harness debe quedar CONSTRUIDO y VALIDADO, y la medición real
ejecutarse donde sí haya modelo (Antigravity, Claude Code u otro host).
Esto NO es un bloqueo: es exactamente lo que R1 y CANON:HONESTIDAD exigen
declarar.

--------------------------------------------------------------------------------
5.a CORRECCIÓN BLOQUEANTE: EL RUNNER DE SMOKE FABRICA UNA FILA (HACER PRIMERO)
--------------------------------------------------------------------------------
VERIFICADO HOY en `evals/smoke/run_smoke.py` (líneas ~110-126): la fila
"ChatGPT Custom GPT" está **escrita a mano en el script**, con
`modelo_version = "GPT-4o / Web UI"` y veredicto `DETECTADO` para Cat. 1/2/3
calculado por reglas locally. **No se ejecutó ningún GPT-4o.** Eso es una
afirmación de procedencia falsa en la tabla que R5 declara como evidencia
publicable, y contradice `references/invariants.md` → `CANON:HONESTIDAD`
("lo no ejecutado se reporta NO VERIFICADO; nunca se declara completo").
Además, la tabla que aparece en el informe de PR-4 no coincide con la salida
real del script (el script imprime "N/A (CLI no disponible…)" para Claude Code,
no "Claude 3.7 Sonnet / CLI").

REGLAS A IMPLEMENTAR:
  1. ELIMINA la fila hardcodeada de "ChatGPT Custom GPT" del runner.
  2. REGLA DE ORO DE LA EVIDENCIA: una fila de host en cualquier tabla de
     evaluación SOLO puede existir si hay una traza real en
     `evals/runs/<fecha>/<host>/<caso>.json`. Sin traza → la fila NO se emite,
     o se emite como `NO VERIFICADO` con motivo explícito y
     `modelo_version = "N/A (sin ejecución)"`. NUNCA se escribe el nombre de un
     modelo que no se ha ejecutado.
  3. Lo que la fila de ChatGPT quería comprobar de verdad (que el PAQUETE INLINE
     P1–P4 contiene las reglas necesarias para detectar Cat. 1/2/3) es una
     comprobación ESTÁTICA DEL ARTEFACTO, no una evaluación de modelo:
     conviértela en un test propio ("cobertura del paquete inline") que verifique
     que `integrations/chatgpt/custom_gpt_instructions.md` contiene el índice de
     las 7 categorías, la puerta, la honestidad, el fallback de modo y el
     formato del informe. Sin fila en la tabla de smoke.
  4. El runner DEBE escribir su tabla en `docs/SMOKE-RESULTS.md` (generado,
     versionado, con la cabecera GENERATED). `docs/ESTADO-PR.md` y
     `docs/QUALITY.md` ENLAZAN a ese fichero; nadie reescribe la tabla a mano.
  5. Añade un test (`tests/test_smoke_evidence.py`) que falle si:
       - alguna fila con veredicto distinto de `NO_VERIFICADO` no tiene traza
         correspondiente en `evals/runs/`;
       - alguna fila nombra un modelo (`modelo_version`) sin traza que lo
         respalde;
       - `docs/SMOKE-RESULTS.md` está desactualizada respecto al runner
         (regenera y compara hash).

--------------------------------------------------------------------------------
REGLAS INVARIABLES (NO NEGOCIABLES)
--------------------------------------------------------------------------------
R1. El Release Gate depende solo de validación LOCAL; los hosts externos pueden
    quedar `NO VERIFICADO` sin bloquear la publicación.
R2. Una única fuente canónica por regla. Ninguna definición N3 fuera de
    `references/invariants.md`, `references/rubrica.md` y
    `references/sqf-standards.md`. Este PR NO escribe ninguna regla nueva.
R3. Ningún artefacto de host enlaza a un fichero que ese host no pueda leer.
R4. Todo criterio de aceptación tiene MÉTRICA + MÉTODO + ESTADO.
R5. "Igual calidad" solo es publicable con `docs/QUALITY.md` con tabla por host
    (modelo, versión, N=3, M1/M2/M3) **respaldada por trazas**.
R6. El texto normativo fuera del canónico es GENERADO y verificado por hash.

REGLAS DE TRABAJO:
  - NO toques `arma3-sqf-review\`. NO hagas push ni publiques nada.
  - Solo biblioteca estándar de Python (>=3.11). Ninguna dependencia nueva.
  - Cero rutas absolutas. Un test SKIPPED en fase ya exigida = FALLO.
  - NO modifiques la Capa 0 (1.186/1.200, 14 tokens de margen) ni los canónicos.

--------------------------------------------------------------------------------
TAREAS DE PR-5
--------------------------------------------------------------------------------
5.b  DATASET DE GOLDENS `evals/goldens/`
      - ≥ 10 snippets SQF, ≥ 1 por cada una de las 7 categorías normativas.
      - ≥ 3 snippets LIMPIOS (0 bloqueantes esperados) → test de falsos positivos.
      - ≥ 2 snippets con SOLO sugerencias (no deben escalar a bloqueante).
      - Cada hallazgo esperado: {categoria: 1..7, archivo, linea, severidad,
        verificable_en: [archivo|pegado]}.
      - Formato de cada golden: directorio con `code.sqf` (+ `description.ext`
        cuando la categoría lo exija) y `expected.json`.
      - Reutiliza `tests/fixtures/wiki_mini/` y `evals/smoke/` como material de
        partida; no dupliques casos.
      - `tests/test_goldens_dataset.py`: cada golden tiene esperados, las 7
        categorías cubiertas, negativos presentes y `verificable_en` declarado.

5.c  HARNESS `evals/harness.py`
      - Calcula M1, M2 y M3 con DENOMINADORES SEPARADOS:
          M1 (script): hallazgos Cat. 1–2 detectados por
              `sqf_orchestrator.py --lint` sobre los goldens deterministas → 100 %.
          M2 (modelo, modo archivo): hallazgos Cat. 3–7 detectados por el modelo
              con filesystem → ≥ 90 %, N=3, reportando media y mínimo.
          M3 (modelo, modo pegado): (DETECTADO + NO_VERIFICADO justificado) /
              esperables con `verificable_en: pegado` → 6/6, 0 falsos PASA.
      - Veredictos del matcher por hallazgo esperado: `DETECTADO`,
        `NO_VERIFICADO` (con justificación), `SILENCIO` (no cuenta; se reporta
        aparte como omisión) y `FALSO_PASA` (falta crítica).
      - Coincidencia: misma categoría + severidad BLOQUEANTE + archivo y línea
        dentro de ±2 líneas.
      - Matcher DETERMINISTA sobre el informe v1. No uses LLM-judge: si lo
        necesitas, su prompt va versionado en `evals/judge_prompt.md` y su
        salida se audita a mano en una muestra.
      - Separa detección por SCRIPT y por MODELO en los informes: nunca atribuyas
        al modelo lo que hizo el script.

5.d  EJECUTORES DE HOST PLUGGABLES
      El harness debe poder ejecutar los goldens en un host real, pero aquí no
      hay ninguna CLI de modelo. Implementa un ejecutor con adaptador:
        --runner local     → motor determinista (sin modelo; solo M1)
        --runner cli:<cmd> → ejecuta `<cmd>` con el prompt del golden y captura
                             stdout (p. ej. `claude -p`, `gemini -p`).
                             Si el comando no existe → la fila queda
                             `NO_VERIFICADO` con motivo, sin inventar nada.
        --runner manual    → el humano/agente pega la respuesta del host en un
                             fichero y el harness la registra como traza.
      Además, escribe `evals/GOLDENS-PROTOCOL.md`: el guion exacto para
      ejecutar los goldens en un host (qué pegar, qué enviar, cómo devolver la
      respuesta) para que Antigravity o Claude Code puedan ejecutarlos en esta
      misma máquina y volcar las respuestas en `evals/runs/<fecha>/<host>/`.
      Traza obligatoria por golden y host:
        `evals/runs/<fecha>/<host>/<golden>.json` con: prompt enviado,
        respuesta cruda, modelo, versión, temperatura, veredicto por hallazgo
        y `contexto_cargado` (ficheros leídos + hash).
      `evals/runs/` está en `.gitignore`: lo que se versiona es
      `docs/QUALITY.md` y `docs/SMOKE-RESULTS.md`.

5.e  `docs/QUALITY.md` (artefacto público, GENERADO por el harness)
      Tabla por host: Host | Modelo | Versión | Fecha | N | M1 | M2 | M3 |
      Falsos PASA | Omisiones | Conclusión.
      REGLAS:
        - Solo filas respaldadas por traza. Sin traza → `NO VERIFICADO`.
        - Si no hay ejecución de modelo en este entorno, la tabla lo dice
          explícitamente y `docs/QUALITY.md` NO afirma "misma calidad".
        - Enlaza a `docs/SMOKE-RESULTS.md` y al directorio de trazas.
        - El README lo enlaza (ya está previsto desde PR-4).

5.f  POLÍTICA DE ITERACIÓN DEL PORT (simétrica a la del plugin original)
      Si un gate de calidad falla (M2 < 90 %, M3 < 6/6, omisiones > 0):
        - itera sobre Capa 0 / lentes / prompt de evaluación, hasta 3 iteraciones;
        - si tras 3 iteraciones sigue fallando: NO se publica en verde. El
          criterio queda `NO VERIFICADO` con motivo en `docs/QUALITY.md`, se
          publica con la limitación explícita y se anota como known-issue;
        - PROHIBIDO ajustar un golden para que pase (cambiar un esperado =
          cambiar el contrato → exige revisar el canónico y regenerar hashes).

5.g  GATE
      Añade a `scripts/check.py` los checks dirigidos, con `skip_is_failure=True`
      y fase de exigencia **PR-5**:
        - "goldens"          → tests/test_goldens_dataset.py
        - "evidencia smoke"  → tests/test_smoke_evidence.py
        - "cobertura paquete inline" → el test estático de 5.a-3
      `python scripts/check.py --fase PR-5` → exit 0.

5.h  DOCUMENTACIÓN
      `docs/ESTADO-PR.md`: sección PR-5 con estado por tarea, métricas medidas
      y la lista explícita de lo que queda `NO VERIFICADO` y por qué.
      `docs/PARIDAD.md`: actualiza los ítems 11, 12 y 16 (checklist de
      entrega, criterios por destino, regla de verificación wiki) según lo que
      PR-5 haya podido verificar.
      `README.md`: enlaza `docs/QUALITY.md` y matiza la afirmación de calidad
      según el estado real de la tabla (no "misma calidad" si hay filas
      `NO VERIFICADO`).

--------------------------------------------------------------------------------
VERIFICACIÓN ANTES DE CERRAR (obligatoria)
--------------------------------------------------------------------------------
    python3 -m pytest tests/ -q
    python3 scripts/check.py --fase PR-5
    python3 -m ruff check .
    python3 scripts/generate_inline_packages.py --check
    python3 evals/harness.py --help

Los cinco en verde. `check.py --fase PR-5` DEBE devolver exit 0.

--------------------------------------------------------------------------------
LO QUE NO DEBES HACER
--------------------------------------------------------------------------------
- No toques `arma3-sqf-review\`. No hagas push ni publiques nada.
- No escribas NINGÚN nombre de modelo ni veredicto que no venga de una traza
  real. Si no se ejecutó, `NO VERIFICADO` con motivo.
- No inventes M1/M2/M3: si no hay ejecución de modelo, M2 y M3 se reportan
  como no medidos, no como 0 ni como 100 %.
- No modifiques la Capa 0 ni los canónicos.
- No borres `agents\` ni `legacy\agents\` (decisión abierta, tarea 1.o; sin git).
- No añadas dependencias ni rutas absolutas.

--------------------------------------------------------------------------------
CRITERIOS DE ACEPTACIÓN
--------------------------------------------------------------------------------
 1. La fila fabricada de "ChatGPT Custom GPT / GPT-4o" ya no existe en ningún
    runner, tabla ni documento, y su comprobación de valor pasó a ser un test
    estático del paquete inline.
 2. `test_smoke_evidence.py` verde: ninguna fila sin traza, ningún modelo sin
    traza, `docs/SMOKE-RESULTS.md` sincronizada.
 3. `evals/goldens/` con ≥ 10 snippets, 7 categorías cubiertas, ≥ 3 limpios,
    ≥ 2 solo-sugerencias, con `verificable_en` declarado.
 4. Harness con M1/M2/M3 de denominadores separados y veredictos DETECTADO /
    NO_VERIFICADO / SILENCIO / FALSO_PASA; M1 = 100 % en los goldens
    deterministas.
 5. `docs/QUALITY.md` generado, con tabla por host y sin afirmaciones sin
    respaldo.
 6. `evals/GOLDENS-PROTOCOL.md` con el guion de ejecución para un host real.
 7. `check.py --fase PR-5` en verde (exit 0), 0 tests omitidos.
 8. `docs/ESTADO-PR.md`, `docs/PARIDAD.md` y `README.md` actualizados.

Al terminar, informa: qué cambiaste, la salida literal de los cinco comandos,
M1 medido, el estado real de M2/M3 (medidos o `NO VERIFICADO` con motivo), y
la tabla de `docs/QUALITY.md`. Si no pudiste ejecutar con modelo, dilo sin
maquillar: el objetivo de este PR es precisamente que la evidencia diga la
verdad.

================================================================================
FIN DE LA INSTRUCCIÓN
================================================================================
