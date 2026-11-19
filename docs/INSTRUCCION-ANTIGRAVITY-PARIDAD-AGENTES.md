================================================================================
INSTRUCCIÓN PARA ANTIGRAVITY — TRACK B: Verificación de la paridad de los 11
                            agentes + alcance documentado de `agents/`
================================================================================
Copia este bloque completo en el chat de Antigravity, con la working directory
en la copia de trabajo:

    C:\Users\Touri\Documents\EDEN EDITOR\Skills Antigravity\arma3-sqf-skill

Este track va PARALELO al Track A (medición, `docs/INSTRUCCION-ANTIGRAVITY-PR6PREP.md`).
Si tu cuota permite, empieza por el Track A (Partes A y B), que es el que
desbloquea la publicación; después haz el Track B.

--------------------------------------------------------------------------------
CONTEXTO: LO QUE YA ESTÁ HECHO (verificado por Mavis hoy)
--------------------------------------------------------------------------------
**Los 11 agentes del plugin original YA están portados a forma portable.** No hay
que portarlos: hay que VERIFICAR que el port es completo. El mapeo está
declarado, pero nunca se contrastó con el contenido de los agentes originales.

Mapeo declarado (Capa 0 §5 de `SKILL.md` y sección A de `docs/PARIDAD.md`):

  | # | Agente original (Antigravity) | Artefacto portable equivalente | Tipo |
  | :- | :--- | :--- | :--- |
  | 1 | `sqf-locality-auditor` | `references/lenses/locality.md` | Lente |
  | 2 | `sqf-performance-auditor` | `references/lenses/performance.md` | Lente |
  | 3 | `sqf-architect` | `references/lenses/architect.md` | Lente |
  | 4 | `sqf-mission-config-auditor` | `references/lenses/config.md` | Lente |
  | 5 | `sqf-best-practices-reviewer` | `references/lenses/best_practices.md` | Lente |
  | 6 | `sqf-claim-verifier` | `references/lenses/claims.md` + `wiki_db_builder.py` / DB FTS5 | Lente + herramienta |
  | 7 | `sqf-static-analyzer` | `sqf_orchestrator.py --lint` | Herramienta determinista |
  | 8 | `sqf-test-plan-generator` | `references/workflows/test_plan.md` | Workflow |
  | 9 | `sqf-doc-writer` | `references/workflows/documentation.md` | Workflow |
  | 10 | `sqf-developer` | `references/workflows/implementation.md` | Workflow |
  | 11 | `sqf-innovator` | `references/workflows/innovation.md` | Workflow |

Lo que falta, y es el encargo real de este track:

  1. **Ninguno de esos 11 mapeos está verificado contra el contenido del agente
     original.** `docs/PARIDAD.md` dice `PORTADO` para los 11, pero eso es una
     **afirmación**, no una evidencia: nadie contrastó responsabilidades,
     entradas, salidas ni prohibiciones de `agents/<nombre>.md` con lo que
     realmente hace el artefacto portable. Bajo el Principio de Honestidad
     Técnica, una afirmación sin evidencia no puede sostenerse.
  2. **`agents/` no tiene alcance documentado.** Sus 11 ficheros llevan
     frontmatter **exclusivo de Antigravity**: `subagent: true`, `mainAgent`,
     `model: pro`, `commandExecutionPolicy: sandbox`, `tools: [view_file,
     grep_search]`. Son el mismo tipo de mecanismo no portable que ya se
     abolió en `rules/AGENTS.md` (su `trigger: always_on` se sustituyó por un
     puntero al canónico, porque "es un mecanismo exclusivo de Antigravity y no
     es portable"). La misma lógica debe aplicarse a `agents/`.
  3. **Divergencia conocida entre `agents/` y `legacy/agents/`.** 10 de los 11
     ficheros son idénticos; `sqf-claim-verifier.md` difiere porque Mavis corrigió
     hoy en `agents/` tres rutas rotas (`skills/arma3-sqf-review/...`) que en
     `legacy/agents/` siguen como estaban.

Decisión ya tomada por el usuario (no la reabras, aplícala):
  **Los 11 agentes se PORTAN a forma portable (ya mayoritariamente hecho) y se
  VERIFICAN. `agents/` se conserva y se documenta su alcance. NO se borra nada.**

--------------------------------------------------------------------------------
PARTE A — AUDITORÍA DE COBERTURA, AGENTE POR AGENTE (P0)
--------------------------------------------------------------------------------
A.1 Para cada uno de los 11 agentes, haz esto (no te saltes ninguno):
      1. Lee el System Prompt original en `agents/<nombre>.md` completo.
      2. Extrae su lista de **responsabilidades** (qué debe hacer), **entradas**
         (qué contexto necesita), **salida** (qué debe emitir) y
         **prohibiciones** (qué no puede hacer).
      3. Lee el artefacto portable equivalente completo.
      4. Contrasta responsabilidad por responsabilidad y clasifica cada una:
         `CUBIERTA` | `PARCIAL` | `NO CUBIERTA`.
      5. Si algo queda `PARCIAL` o `NO CUBIERTA`: **añádelo al artefacto
         portable**, respetando las reglas:
           - **NO toques la Capa 0** de `SKILL.md` (1.186/1.200 tokens, 14 de
             margen). Los workflows y lentes se cargan bajo demanda: caben sin
             tocar la Capa 0.
           - **Ninguna definición N3 fuera de los canónicos** (`invariants.md`,
             `rubrica.md`, `sqf-standards.md`). Si el hueco necesita una regla
             normativa, se escribe en el canónico y se referencia con su ancla
             `CANON:*`; si es un extracto, con `CANON-EXTRACT:*` y su hash.
           - Los artefactos con regiones AUTHORED/EXTRACT conservan su
             delimitación y su entrada en `scripts/generated.lock.json`
             (R6). Si tocas una región extractada, regenera el lock.
      6. Registra el resultado en `docs/PARIDAD.md` (sección A) con la columna
         de nota sustituida por evidencia concreta: qué responsabilidades se
         verificaron y cuáles estaba pendientes.

A.2 Criterio de cierre del hueco: un agente está `PORTADO Y VERIFICADO` cuando
    **todas** sus responsabilidades son `CUBIERTA` y hay una referencia
    verificable (fichero + sección) en la tabla de paridad. Si queda alguna
    `PARCIAL` sin resolver, el estado es `PORTADO PARCIAL` y se documenta la
    limitación — **no se maquilla**.

A.3 Atención especial a estos puntos, que son donde los agentes originales
    tienen más contenido que la forma portable:
      - `sqf-claim-verifier`: el original exige **procedencia dinámica** (commit
        SHA en tiempo de ejecución, `revid`, URL canónica de BIKI) y el
        **Principio de Prevalencia de la Fuente Primaria** (la réplica local
        `a3ref` prevalece sobre la web). Comprueba que `references/lenses/claims.md`
        los recoge.
      - `sqf-mission-config-auditor`: el original cubre `CfgRemoteExec`,
        `CfgFunctions`, perfiles de misión y `description.ext`. Comprueba que
        `references/lenses/config.md` cubre las cuatro.
      - `sqf-static-analyzer`: su equivalente es una **herramienta**, no un
        documento. Verifica que `sqf_orchestrator.py --lint` cubre lo que el
        agente prometía (contrato v1, `REPORT_SCHEMA_VERSION`, item 9/wiki) y
        que la Capa 0 lo invoca igual que al original.
      - `sqf-architect` y `sqf-developer`: el original distingue diseño
        (sin escribir código) de implementación. Comprueba que la frontera
        sigue siendo inequívoca en los workflows.

--------------------------------------------------------------------------------
PARTE B — `agents/README.md` Y ALCANCE DOCUMENTADO (P0)
--------------------------------------------------------------------------------
B.1 Crea `agents/README.md` (Breve, en español) con:
      - **Qué son**: definiciones de subagente del plugin Antigravity original,
        conservadas para quien trabaje en Antigravity.
      - **Que NO son portables**: su frontmatter (`subagent`, `mainAgent`,
        `model: pro`, `commandExecutionPolicy: sandbox`,
        `tools: [view_file, grep_search]`) es específico de Antigravity. En
        Claude Code, Cursor, Codex, ChatGPT o Gemini **no se cargan**: un host
        que no los soporte no pierde nada porque sus equivalentes portables
        son las lentes, los workflows y los scripts.
      - **Tabla de equivalencia** agente → artefacto portable (la de la Parte A),
        para que quien lea `agents/` sepa a qué artefacto portable corresponde.
      - **Advertencia de estado**: el equivalente portable es la fuente de verdad
        normativa; si un agente y su equivalente discrepan, **manda el canónico**
        (`references/invariants.md`).
      - Nota de que `legacy/agents/` es el histórico congelado: no se distribuye
        ni se empaqueta (ver `MANIFEST.in`).

B.2 Referencia `agents/README.md` desde `README.md` (sección de arquitectura o
    de "Lo que NO incluye esta skill") y desde `docs/COMPATIBILIDAD.md`, en la
    misma línea donde se explains que `agents/` es exclusivo de Antigravity.
    **Cuidado con el presupuesto de tokens de `SKILL.md`: no lo toques.**

B.3 `legacy/agents/` es material histórico CONGELADO (`MANIFEST.in` dice
    "Material histórico congelado: no se distribuye ni se empaqueta"). **NO lo
    modifiques**, ni siquiera para sincronizar la corrección de
    `sqf-claim-verifier.md`. Deja constancia de la divergencia en
    `docs/ESTADO-PR.md`:
      "`legacy/agents/sqf-claim-verifier.md` conserva intencionadamente la
       versión anterior a la corrección de rutas (pre-2026-11-19). La versión
       vigente es `agents/sqf-claim-verifier.md`."

B.4 **NO muevas, NO borres y NO renombres `agents/`.** La decisión de producto
    ya está tomada: se conservan con su alcance documentado.

--------------------------------------------------------------------------------
PARTE C — PARIDAD EJECUTABLE (P1: convierte la afirmación en evidencia)
--------------------------------------------------------------------------------
C.1 Crea `tests/test_agent_port_parity.py` que verifique, de forma ejecutable:
      - Cada fichero `agents/<nombre>.md` (los 11) tiene una fila en la tabla de
        paridad de `docs/PARIDAD.md` con un artefacto portable asociado.
      - Cada artefacto portable referenciado **existe en disco**.
      - Ningún agente queda con equivalente ausente o con estado `NO CUBIERTA`.
      - La fila declara el estado de verificación (`PORTADO Y VERIFICADO` /
        `PORTADO PARCIAL`) y, si es parcial, la limitación concreta.
      - Cada artefacto portable de tipo lente/workflow es referenciado desde
        `SKILL.md` (para que la activación bajo demanda siga funcionando).
    Este test es el que convierte "PORTADO" en algo que no se puede afirmar sin
    trabajar.

C.2 Añade el check dirigido al gate: `scripts/check.py --fase PR-7` (o el
    identificador de fase que corresponda) con un check nuevo
    "paridad de agentes verificable", con `skip_is_failure=True`.
    Si `--fase PR-7` no existe todavia, créalo con los checks que ya aplican
    (los de PR-5 y PR-6 deben seguir en verde) y **sin publicar nada**.

C.3 Si al auditar los 11 agentes encuentras que un workflow portable necesita
    un extracto normativo nuevo, Remember: el extracto va al canónico, se
    inyecta con su ancla y se regenera `scripts/generated.lock.json`. Ningún
    texto normativo nuevo fuera de los 3 canónicos.

--------------------------------------------------------------------------------
PARTE D — DOCUMENTACIÓN (P1)
--------------------------------------------------------------------------------
D.1 `docs/PARIDAD.md`:
      - Sección A: sustituir la nota genérica ("PR-2: Lente bajo demanda
        implementada...") por la **evidencia de la auditoría**: qué
        responsabilidades se verificaron, cuántas y su resultado.
      - Añadir la tabla de equivalencia completa (11 filas).
      - Nueva sección "A-bis. Alcance de `agents/`" con lo decidido en la
        Parte B.
D.2 `docs/ESTADO-PR.md`: nueva sección "TRACK B — Paridad de agentes" con:
      - El resultado de la auditoría (11 agentes: cuántos verificados, cuántos
        parciales y por qué).
      - Los huecos encontrados y cómo se cerraron (o su limitación).
      - La decisión de producto registrada: `agents/` se conserva con alcance
        documentado; `legacy/agents/` congelado; `plugin.json` se mantiene
        como vía de instalación del skill como plugin de Antigravity, y **no**
        es un requisito para los demás hosts.
      - La nota de divergencia de `legacy/agents/sqf-claim-verifier.md`.
D.3 `README.md`: si en algún punto se insinúa paridad con el plugin original,
      que sea con la evidencia de esta auditoría, no con una afirmación.

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
  - **NO modifiques la Capa 0** (1.186/1.200, 14 tokens de margen) ni los
    canónicos (salvo extractos con ancla y hash, regenerando el lock).
  - **NO borres ni muevas** `agents/`, `legacy/agents/` ni `plugin.json`.
  - NO escribas ninguna métrica a mano. NO inventes nombres de modelo.
  - La medición (M2 88,9 %, M3 7/14) **no se toca** en este track.

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
  - `docs/PARIDAD.md` con la tabla de equivalencia y el resultado real de la
    auditoría (sin `PORTADO` genérico sin evidencia).
  - `agents/README.md` existente y referenciado.
  - `agents/` y `legacy/agents/` intactos en contenido y ubicación.

--------------------------------------------------------------------------------
CRITERIOS DE ACEPTACIÓN
--------------------------------------------------------------------------------
 1. Los 11 agentes auditados uno a uno, con resultado `CUBIERTA/PARCIAL/NO
    CUBIERTA` por responsabilidad y la evidencia escrita en `docs/PARIDAD.md`.
 2. Todo hueco `PARCIAL`/`NO CUBIERTA` cerrado en el artefacto portable, o
    documentado como limitación explícita (nunca maquillado).
 3. `tests/test_agent_port_parity.py` en verde: la paridad deja de ser una
    afirmación y pasa a ser un test.
 4. `agents/README.md` con alcance, tabla de equivalencia y advertencia de
    precedencia del canónico; referenciado desde README/COMPATIBILIDAD.
 5. Check nuevo en el gate y `--fase PR-7` en verde.
 6. Capa 0 sin tocar (1.186/1.200) y canónicos con hashes regenerados si
   Procede.
 7. `agents/`, `legacy/agents/` y `plugin.json` intactos.
 8. Los ocho comandos de verificación en verde.

Al terminar, informa: la tabla de los 11 agentes con su estado verificado, los
huecos que encontraste y cómo los cerraste, la salida literal de los ocho
comandos, y confirma que `agents/`, `legacy/agents/` y `plugin.json` no se
movieron ni se borraron.

================================================================================
FIN DE LA INSTRUCCIÓN
================================================================================
