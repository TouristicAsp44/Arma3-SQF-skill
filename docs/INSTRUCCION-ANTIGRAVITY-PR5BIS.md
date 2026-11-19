================================================================================
INSTRUCCIÓN PARA ANTIGRAVITY — PR-5-bis: Corrección del harness + Medición real
================================================================================
Copia este bloque completo en el chat de Antigravity, con la working directory
en la copia de trabajo:

    C:\Users\Touri\Documents\EDEN EDITOR\Skills Antigravity\arma3-sqf-skill

--------------------------------------------------------------------------------
CONTEXTO Y ESTADO (verificado hoy)
--------------------------------------------------------------------------------
PR-1..PR-5 cerrados y en verde. `python scripts/check.py --fase PR-5` → exit 0,
93/93 tests verdes, `ruff check .` limpio.
Tokens: frontmatter 184/250 · Capa 0 1.186/1.200 · turno máx 1.666/2.500.
DB: `~/.a3ref/arma3_wiki.db` (58,42 MB, fts_enabled=1).
La fila fabricada de "GPT-4o" ya no existe: el runner de smoke ahora dice
"N/A (sin ejecución)" y `tests/test_smoke_evidence.py` +
`tests/test_quality_evidence.py` bloquean esa clase de fallo. BIEN HECHO.

Este hito tiene dos mitades:
  A) Corregir TRES defectos del harness que solo se manifestan cuando existen
     trazas reales. Son bloqueantes: si no se corrigen ahora, la PRIMERA
     medición real publicará cifras falsas.
  B) Ejecutar la medición real de los goldens en el host donde estés
     (Antigravity) y volcar las trazas, para que M2 y M3 pasen de
     "NO VERIFICADO" a "MEDIDO".

--------------------------------------------------------------------------------
PARTE A — CORRECCIONES BLOQUEANTES DEL HARNESS (PRIORIDAD ABSOLUTA)
--------------------------------------------------------------------------------
VERIFICADO HOY en `evals/harness.py`. Estos defectos están latentes porque
ahora no hay trazas: en cuanto haya una ejecución real, publicarán números que
no se corresponden con lo medido.

A.1 M3 ESTÁ HARDCODEADO  →  `harness.py:196`
      "m3": "6/6 (0 FALSO_PASA)",
    Es una cadena literal. Con trazas reales, M3 se publicaría SIEMPRE como
    "6/6 (0 FALSO_PASA)", sea cual sea el resultado real. Es la misma clase de
    defecto que la fila de GPT-4o, pero en la métrica principal.
    CORRECCIÓN: M3 se CALCULA desde las trazas, con la misma fórmula que
    M2, y con denominador propio:
      M3 = (DETECTADO + NO_VERIFICADO justificado) / esperables del modo
      pegado, y se reportan por separado `falsos_pasa` y `omisiones`.
    Si el resultado real no es 6/6, se publica 6/6 solo si lo es. Prohibido
    cualquier literal de métrica en el código.

A.2 EL ARGUMENTO `mode` SE IGNORA  →  `harness.py:153`
      def evaluate_external_host(host_id: str, mode: str) -> dict:
    `mode` se recibe y no se usa. Consecuencia: un host con trazas de ambos
    modos se mediría con la misma métrica, y M2 (modo archivo) se contaminaría
    con trazas de modo pegado.
    CORRECCIÓN: filtra las trazas por `modo_evaluacion` ("archivo" / "pegado")
    y usa `mode` en el cálculo. Un host sin trazas de ese modo → NO VERIFICADO
    para ese modo (no "N/A").

A.3 EL DENOMINADOR DE M2 VIENE DE LA TRAZA, NO DE LA VERDAD  →  `harness.py:175`
      for v in tr.get("veredicto_por_hallazgo", []):
    El denominador se construye con los hallazgos que la PROPIA traza declara.
    Si una traza omite un hallazgo esperado, ese hallazgo desaparece del
    denominador → la métrica se infla sin que nadie lo note.
    CORRECCIÓN: el denominador sale SIEMPRE de `evals/goldens/<id>/expected.json`
    (la verdad declarada), nunca de la traza. Por cada hallazgo esperado:
      - si la traza lo marca DETECTADO → suma al numerador;
      - si la traza lo marca NO_VERIFICADO con justificación → cuenta como
        acierto solo si `verificable_en` incluye el modo evaluado; si no, cuenta
        como omisión;
      - si la traza lo marca SILENCIO → omisión;
      - si la traza lo marca FALSO_PASA → falta crítica.
    Además, comprueba que la traza NO declare hallazgos que no están en
    `expected.json`: si los declara, es un falso positivo y cuenta como tal.

A.4 `N` SE REPORTA COMO TOTAL DE TRAZAS, NO COMO REPETICIONES POR GOLDEN
      "n": len(traces),
    Con 14 goldens × 3 repeticiones = 42 trazas, la tabla publicaría N=42,
    mientras que el protocolo define N=3 repeticiones por golden. Además
    `modelo` y `version` se toman de `traces[0]` (la primera), ocultando si las
    repeticiones usaron modelos distintos.
    CORRECCIÓN:
      - `n` = número de REPETICIONES por golden (min y máx sobre los goldens
        evaluados); reporta también el número de goldens evaluados.
      - `modelo`/`version` = el de la MAYORÍA de las trazas; si hay más de uno,
        publícalo como "mixto: a, b, c" con el detalle por golden.
      - Reporta también la dispersión (mínimo y media) como exige R5.

A.5 TESTS QUE BLOQUEAN LA REGRESIÓN (añádelos, no son opcionales)
      `tests/test_harness_metrics.py` con trazas SINTÉTICAS en un directorio
      temporal (monkeypatch de `RUNS_DIR`), cubriendo:
      - una traza que OMITE un hallazgo esperado → el denominador NO baja (A.3)
      - una traza con M3 real distinto de 6/6 → el M3 reportado lo refleja (A.1)
      - trazas de ambos modos en el mismo host → cada modo mide lo suyo (A.2)
      - trazas con 2 modelos distintos → la tabla lo refleja (A.4)
      - una traza que declara un hallazgo no esperado → se cuenta como falso
        positivo
      - una traza sin `contexto_cargado` → se rechaza o se marca inválida
      Además, un test que falle si el código del harness contiene literales de
      métrica fijos (p. ej. "6/6 (0 FALSO_PASA)").

--------------------------------------------------------------------------------
PARTE B — MEDICIÓN REAL (ejecutar los goldens en este host)
--------------------------------------------------------------------------------
B.1  EJECUTA LOS 14 GOLDENS EN MODO ARCHIVO, N=3 REPETICIONES
      Procedimiento (ya documentado en `evals/GOLDENS-PROTOCOL.md`):
      - Para cada golden `evals/goldens/<id>/`: carga `code.sqf` y, si existe,
        `description.ext`.
      - Contexto: `skills/arma3-sqf-skill/SKILL.md` + las lentes que el propio
        SKILL.md diga abrir (no las fuerces todas).
      - Temperatura efectiva 0.1–0.3. N=3 por golden.
      - El informe que pides al modelo debe respetar el esquema v1 literal:
          REPORT_SCHEMA_VERSION: 1
          [BLOQUEANTE|SUGERENCIA|NO_VERIFICADO] archivo:linea (disciplina): descripcion
          RESUMEN: bloqueantes=N; sugerencias=N; no_verificado=N
      - No le digas qué bloqueantes hay: eso es lo que se mide. NO reveles
        `expected.json` al modelo en ningún momento.

B.2  EJECUTA LOS 14 GOLDENS EN MODO PEGADO (paquete inline), N=3
      - Injecta el paquete inline que corresponda al host degradado:
        `integrations/claude/claude_desktop_paste.md` o
        `integrations/chatgpt/custom_gpt_instructions.md`.
      - Pega SOLO el `code.sqf` en el chat (sin `description.ext`): así es como
        un usuario real pegaría el código, y por eso Cat. 5 y Cat. 7 deben
        salir `NO VERIFICADO` y NO como bloqueantes inventados.

B.3  TRAZAS (formato EXACTO, el harness las lee así)
      `evals/runs/<YYYY-MM-DD>/<host_id>/<golden_id>.json` con estos campos:
        golden_id, host, modelo, version, temperatura, fecha,
        modo_evaluacion ("archivo" | "pegado"),
        prompt_enviado, respuesta_cruda,
        contexto_cargado: [{archivo, sha256}],
        repeticion: 1|2|3,
        veredicto_por_hallazgo: [{categoria, esperado_linea, detectado_linea,
                                  veredicto, justificacion}]
      `host_id` DEBE coincidir con los que el harness consulta:
        "claude-code", "claude-desktop", "cursor", "openai-codex", "chatgpt",
        "gemini". Para este hito usa el id que corresponda al host donde
        ejecutes (ej. "antigravity" NO existe en esa lista: si ejecutas en
        Antigravity, registra las trazas bajo el id del host equivalente que
        describas, o añade "antigravity" al harness como host nuevo y a la
        matriz de docs/COMPATIBILIDAD.md).
      `modelo` debe ser el MODELO REAL que produjo la respuesta (nombre y
      versión exactos). Si no lo conoces con certeza, deja "N/A (modelo no
      identificado)" y el host quedará NO VERIFICADO. NUNCA inventes un nombre
      de modelo.
      `veredicto_por_hallazgo` lo calcula el harness, no tú: guarda en la traza
      los HALLAZGOS EMITIDOS por el modelo (categoría inferida, archivo, línea,
      severidad) y deja el veredicto para el harness. Si el harness no puede
      calcularlo, entonces sí inclúyelo, pero incluyendo toda la lista de
      esperados con su veredicto.

B.4  INGESTA Y PUBLICACIÓN
      python3 evals/harness.py --write     # recalcula M1/M2/M3 y regenera QUALITY.md
      python3 evals/harness.py --check     # debe pasar
      Si el harness no sabe calcular un veredicto, MEJÓRALO (Parte A) en lugar de
      rellenar el número a mano.

B.5  DOCUMENTA LOS RESULTADOS CON SUS LÍMITES
      - `docs/QUALITY.md`: lo regenera el harness. No lo edites a mano.
      - `docs/ESTADO-PR.md`: sección "PR-5-bis" con el estado real: M1 medido,
        M2 medido (o NO VERIFICADO con motivo), M3 medido, N real, modelo real,
        dispersión, y la lista de goldens con omisiones o falsos PASA.
      - `docs/PARIDAD.md`: ítems 11, 12 y 16 con el estado que la evidencia
        sustains.
      - `README.md`: la insignia y la frase de calidad deben reflejar lo
        medido. Si M2/M3 no se pudieron medir, NO digas "misma calidad".

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
  - NO toques `arma3-sqf-review\`. NO hagas push ni publiques nada.
  - Solo biblioteca estándar de Python (>=3.11). Ninguna dependencia nueva.
  - Cero rutas absolutas. Un test SKIPPED en fase ya exigida = FALLO.
  - NO modifiques la Capa 0 (1.186/1.200, 14 tokens de margen) ni los canónicos.
  - `evals/runs/` sigue en `.gitignore`: lo público es `docs/QUALITY.md`.

--------------------------------------------------------------------------------
VERIFICACIÓN ANTES DE CERRAR (obligatoria)
--------------------------------------------------------------------------------
    python3 -m pytest tests/ -q
    python3 scripts/check.py --fase PR-5
    python3 -m ruff check .
    python3 evals/harness.py --check
    python3 scripts/generate_inline_packages.py --check

Los cinco en verde. Y ADEMÁS: `docs/QUALITY.md` debe contener filas con M2/M3
MEDIDOS para el host realmente ejecutado, o `NO VERIFICADO` con motivo real.

--------------------------------------------------------------------------------
LO QUE NO DEBES HACER
--------------------------------------------------------------------------------
- No reveles `expected.json` al modelo que evalúa: destruye la medición.
- No escribas ninguna métrica a mano: ni en el harness, ni en QUALITY.md,
  ni en ESTADO-PR.md. Si el harness no la calcula, hay que programarla.
- No inventes nombres de modelo ni de versión. Si no lo sabes: "N/A".
- No marques verde un host sin trazas.
- No ajustes `expected.json` para que la métrica pase (cambiar un esperado =
  cambiar el contrato → revisar el canónico y regenerar hashes).
- No toques la Capa 0 ni los canónicos. No borres `agents\` ni `legacy\agents\`.

--------------------------------------------------------------------------------
CRITERIOS DE ACEPTACIÓN
--------------------------------------------------------------------------------
 1. `harness.py` NO contiene ninguna métrica literal: M3 se calcula; `mode` se
    aplica; el denominador sale de `expected.json`; `n` son repeticiones por
    golden; modelo/version se reportan con honestidad.
 2. `tests/test_harness_metrics.py` verde con las 6 situaciones de A.5.
 3. Trazas reales en `evals/runs/<fecha>/<host_id>/` para los goldens
    ejecutados, N=3, con `contexto_cargado` y `modelo` real.
 4. `docs/QUALITY.md` regenerado con M2/M3 MEDIDOS para el host ejecutado (o
    NO VERIFICADO con motivo real si no fue posible).
 5. `docs/ESTADO-PR.md` con la sección PR-5-bis y los límites explícitos.
 6. `check.py --fase PR-5` en verde (exit 0), 0 tests omitidos.
 7. `ruff check .` limpio y el resto de comandos en verde.

Al terminar, informa: qué corregiste, la salida literal de los cinco comandos,
la tabla de `docs/QUALITY.md`, el número de goldens y repeticiones realmente
ejecutados, el modelo real usado y las omisiones/falsos PASA observados. Si
alguna métrica no se pudo medir, dilo sin maquillarla: ese es el objetivo del
hito.

================================================================================
FIN DE LA INSTRUCCIÓN
================================================================================
