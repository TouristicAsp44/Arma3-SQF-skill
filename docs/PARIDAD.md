# Paridad: `arma3-sqf-review` → `arma3-sqf-skill`

Estado de la migración. Cada ítem del plugin original debe estar clasificado
como `PORTADO`, `PORTADO-REDUCIDO` o `NO APLICABLE` (con motivo). Un ítem en
`NO VERIFICADO` bloquea el Release Gate.

Leyenda de estado:
- `PORTADO` — equivalente funcional completo en la skill portable.
- `PORTADO-REDUCIDO` — portado con pérdida consciente; el motivo queda escrito.
- `NO APLICABLE` — la capacidad no tiene sentido sin multi-agente; motivo obligatorio.
- `NO VERIFICADO` — aún no evaluado.

## A. Agentes (11)

| # | Agente original | Artefacto en la skill | Tipo | Estado | Nota |
| :- | :--- | :--- | :--- | :--- | :--- |
| 1 | `sqf-locality-auditor` | `references/lens-locality.md` | Lente (AUTHORED + CANON-EXTRACT) | `PORTADO Y VERIFICADO` | 7 responsabilidades verificadas: máquina de ejecución AL/AG y EL/EG contra matriz a3ref, remoteExec/targets, publicVariable/broadcast, EHs y localidad, JIP y orden de init, dedicado/HC, softlocks y scheduler. Todas cubiertas en lens + canónico. |
| 2 | `sqf-performance-auditor` | `references/lens-performance.md` | Lente (AUTHORED + CANON-EXTRACT) | `PORTADO Y VERIFICADO` | 6 responsabilidades verificadas: carga de scheduler y cadencia sleep/uiSleep, handlers por frame, escaneos globales costosos, estructuras de datos y trabajo repetido, fugas de memoria/entidades, reparto servidor/HC. Todas cubiertas. |
| 3 | `sqf-architect` | `references/lens-architect.md` | Lente (AUTHORED + CANON-EXTRACT) | `PORTADO Y VERIFICADO` | 4 responsabilidades verificadas: fronteras modulares, contrato de interfaces tipado con params, definición de CfgRemoteExec y aislamiento de estado compartido. Todas cubiertas. |
| 4 | `sqf-mission-config-auditor` | `references/lens-config.md` | Lente (AUTHORED + CANON-EXTRACT) | `PORTADO Y VERIFICADO` | 5 responsabilidades verificadas: diferencial misión description.ext vs addon config.cpp, whitelist CfgRemoteExec mode=1, jerarquía CfgFunctions preInit/postInit, CfgPatches en addons, variables broadcast. Todas cubiertas. |
| 5 | `sqf-best-practices-reviewer` | `references/lens-best-practices.md` | Lente (AUTHORED + CANON-EXTRACT) | `PORTADO Y VERIFICADO` | 6 responsabilidades verificadas: declaración explícita params/private, evaluación perezosa contextual, nomenclatura y tags, compileFinal en globales, micro-optimizaciones sintácticas, call vs spawn. Todas cubiertas. |
| 6 | `sqf-claim-verifier` | `references/lens-claims.md` + `scripts/sqf_wiki_reader.py` / `arma3_wiki.db` | Lente + DB SQLite FTS5 | `PORTADO Y VERIFICADO` | 5 responsabilidades verificadas: procedencia dinámica con commit SHA, revid y URL canónica, prevalencia de la réplica local a3ref sobre web, consulta rápida FTS5 SQLite, reporte honesto NO VERIFICADO sin réplica, clasificación de certeza. Todas cubiertas. |
| 7 | `sqf-static-analyzer` | `scripts/sqf_orchestrator.py` | Herramienta determinista | `PORTADO Y VERIFICADO` | Herramienta determinista con contrato v1 (REPORT_SCHEMA_VERSION=1), linter sqflint determinista, integración de procedencia documental en Item 9, fallback honesto rc=10 / NO VERIFICADO si el linter no está instalado. |
| 8 | `sqf-test-plan-generator` | `references/workflows/test_plan.md` | Workflow generativo | `PORTADO Y VERIFICADO` | 4 responsabilidades verificadas: escenarios numerados en servidor dedicado, pruebas de unión tardía JIP, pruebas de ownership/locality, medición de scheduler. Todas cubiertas. |
| 9 | `sqf-doc-writer` | `references/workflows/documentation.md` | Workflow generativo | `PORTADO Y VERIFICADO` | 5 responsabilidades verificadas: principio de honestidad documental (solo lo implementado), diferencial de instalación misión vs addon, API pública con firmas y tipos, comportamiento MP/JIP, solución de problemas y diag_log. Todas cubiertas. |
| 10 | `sqf-developer` | `references/workflows/implementation.md` | Workflow generativo | `PORTADO Y VERIFICADO` | 5 responsabilidades verificadas: implementación fiel del contrato de interfaces, invariantes de servidor dedicado sin player, control estricto de scope params/private, control de canSuspend y desacople de esperas, respeto de perfiles CBA/vanilla. Todas cubiertas. |
| 11 | `sqf-innovator` | `references/workflows/innovation.md` | Workflow generativo | `PORTADO Y VERIFICADO` | 4 filtros obligatorios de viabilidad técnica (red/ancho de banda, scheduler/coste por frame, persistencia/JIP, invariantes de dedicado) y separación estricta concepto vs implementación verificada en wiki. Todas cubiertas. |

## A-bis. Alcance y No Portabilidad de `agents/`

1. **Definiciones Exclusivas de Antigravity**: Los archivos en `agents/` son subagentes que utilizan frontmatter exclusivo del entorno Google Antigravity (`subagent: true`, `mainAgent: false`, `model`, `commandExecutionPolicy: sandbox`, `tools`). No son portables ni se cargan en hosts como Claude Code, Cursor, Codex, ChatGPT o Gemini.
2. **Equivalencia Funcional Completa**: Ningún host externo pierde capacidades al no cargar `agents/`, ya que toda la inteligencia técnica, reglas, heurísticas y rúbricas fueron trasladadas a las lentes planas bajo demanda (`references/lens-*.md`), flujos de trabajo (`references/workflows/`) y scripts deterministas (`scripts/sqf_orchestrator.py`).
3. **Precedencia Normativa**: Si un subagente de `agents/` y los documentos canónicos discrepan, **prevalece estrictamente el canónico** (`references/invariants.md`, `references/sqf-standards.md`, `references/rubrica.md`).
4. **Histórico y Depuración**: Los snapshots históricos de agentes heredados del plugin original fueron purgados en la versión 2.0.0 para maximizar la ventana de contexto y portabilidad, conservándose `agents/` exclusivamente para Antigravity.

## B. Comportamientos normativos (18)

| # | Comportamiento | Dónde vive en la skill portable | Estado | Nota |
| :- | :--- | :--- | :--- | :--- |
| 1 | 7 categorías de BLOQUEANTE | `references/invariants.md` → `CANON:BLOQUEANTES` | `PORTADO` | Migrado literalmente en PR-1 (1.g-bis) |
| 2 | Puerta de Calidad Infranqueable | `references/invariants.md` → `CANON:PUERTA` | `PORTADO` | PR-1 (1.g-bis) |
| 3 | Principio de honestidad técnica | `references/invariants.md` → `CANON:HONESTIDAD` | `PORTADO` | PR-1 (1.g-bis) |
| 4 | Rúbrica de severidad (BLOQUEANTE vs Sugerencia) | `references/rubrica.md` → `CANON:RUBRICA` | `PORTADO` | PR-1 (desbordamiento por tamaño) |
| 5 | Precedencia de conflictos (locality > performance > estilo) | `references/invariants.md` → `CANON:PRECEDENCIA` | `PORTADO` | PR-1 (1.g-bis) |
| 6 | Propiedad de reglas / dueño único por tema | `references/invariants.md` → `CANON:PROPIEDAD` | `PORTADO` | PR-1 (1.g-bis) |
| 7 | Tabla de participación por modo | `references/rubrica.md` → `CANON:PARTICIPACION` | `PORTADO` | PR-1 (desbordamiento por tamaño) |
| 8 | Criterios de modo deterministas + fallback + prohibición Micro manual | `references/invariants.md` → `CANON:MODOS` | `PORTADO` | PR-1 (1.g-bis) |
| 9 | Perfil de Proyecto de 7 parámetros | `references/invariants.md` (bloque «Perfil del Proyecto») | `PORTADO` | PR-1 |
| 10 | Formato de paquete de contexto (handoff entre subagentes) | — | `NO APLICABLE` | Sin multi-agente no hay traspaso entre agentes; el contexto vive en el prompt y en las referencias |
| 11 | Checklist de salida A–I (Informe Desglosado de Estados) | `references/checklist-entrega.md` | `PORTADO` | PR-2: disponible en modo archivo y modo pegado; PR-5: verificado con goldens limpios y arnés determinista; PR-5-bis: el formato de informe v1 se validó en las 42 trazas reales de modo archivo (0 falsos PASA) |
| 12 | Criterios de entrega por DESTINO (misión vs addon) | `references/diferencial-misiones-addons.md` | `PORTADO` | PR-2: disponible en diferencial-misiones-addons.md; PR-5: verificado en goldens g06/g08 con description.ext y perfil de misión; PR-5-bis: g08 (dependencias de framework) evaluado en modo archivo con el modelo real |
| 13 | Flujo de 10 pasos y su orden | `references/workflows/modes.md` + Capa 0 | `PORTADO` | PR-2: 4 intenciones en Capa 0 y matriz de participación en modes.md |
| 14 | Regla de correcciones (máx. 3 iter., orden locality→performance→BP) | `references/invariants.md` → `CANON:PUERTA` + `CANON:PRECEDENCIA` | `PORTADO` | PR-1 (1.g-bis) |
| 15 | Formato del informe estructurado (REPORT_SCHEMA_VERSION=1) | `scripts/sqf_models.py` + `references/report_format.md` | `PORTADO` | PR-1 (2.f-cua): el motor emite la versión |
| 16 | Regla de verificación wiki (a3ref primaria, URL+revid+SHA, cache ≠ evidencia) | `references/invariants.md` + `scripts/wiki_db_builder.py` + `scripts/sqf_wiki_reader.py` | `PORTADO` | PR-3: Base SQLite FTS5 (arma3_wiki.db); PR-5: validado en Item 9 del linter en la suite de goldens; PR-5-bis: las trazas de evaluación no aportan evidencia del Item 9 en campo, que queda sin verificar en host |
| 17 | Escalado de modo y puerta `NO VERIFICADO` por ítem | `references/invariants.md` → `CANON:MODOS` + `CANON:HONESTIDAD` | `PORTADO` | PR-1 (1.g-bis) |
| 18 | Separación pregunta conceptual (sin flujo) vs revisión (dispara flujo) | `references/invariants.md` → `CANON:MODOS` + frontmatter de la skill | `PORTADO` | Criterio "Sin flujo" en CANON:MODOS; el frontmatter se reescribe en PR-2 |

## C. Notas de ejecución (PR-1)

- `skills/arma3-sqf-review/` → `skills/arma3-sqf-skill/` (1.a, ejecutado).
- Los 11 subagentes se copiaron a `legacy/agents/` (1.e) **como copia, no como
  movimiento**: `agents/` sigue existiendo en la raíz. Decisión pendiente
  (1.o / PR-7): borrar `agents/` o declararlo compatibilidad Antigravity.
  `legacy/` está excluido de packaging, del escaneo de rutas y del test de
  unicidad.
- `rules/AGENTS.md` se convierte en `references/invariants.md` (1.f).
  Su contenido se ha absorbido en el canónico; el fichero original permanece
  hasta que PR-2 lo retire.
- El formato del informe cambió a esquema v1 con `REPORT_SCHEMA_VERSION`. El
  test `tests/test_wiring.py::test_report_format_is_stable` se actualizó
  deliberadamente a ese contrato nuevo.

## D. Adaptadores por Host y Compatibilidad (PR-4)

| # | Capacidad / Host | Artefacto en la skill | Tipo | Estado | Nota |
| :- | :--- | :--- | :--- | :--- | :--- |
| 1 | Claude Code | `integrations/claude/CLAUDE.md` | Adaptador Host | `PORTADO` | Región CANON-EXTRACT + AUTHORED verificado por hash |
| 2 | Claude Desktop | `integrations/claude/claude_desktop_paste.md` + `claude_desktop_config_snippet.json` | Adaptador Host (Degradado / MCP) | `PORTADO` | Paquete inline P1–P4 y configuración MCP válida sin pseudocódigo |
| 3 | Cursor | `integrations/cursor/.cursorrules` | Adaptador Host | `PORTADO` | Reglas de proyecto con rutas relativas a `skills/arma3-sqf-skill/` |
| 4 | OpenAI Codex / CLI | `integrations/openai/AGENTS.md` | Adaptador Host | `PORTADO` | Instrucciones con checklist condensado N2 inline |
| 5 | ChatGPT Custom GPT | `integrations/chatgpt/custom_gpt_instructions.md` + `knowledge_manifest.md` | Adaptador Host (Degradado RAG) | `PORTADO` | Paquete inline <= 8.000 chars + 18 archivos <= 20 de Knowledge |
| 6 | Google Gemini | `integrations/gemini/system_instruction.md` | Adaptador Host (Degradado) | `PORTADO` | System instruction en texto plano con paquete P1–P4 |
| 7 | Paquete inline P1–P4 | `scripts/generate_inline_packages.py` | Generador determinista | `PORTADO` | Generación determinista con verificación CLI `--check` y lock file |
| 8 | Matriz de compatibilidad | `docs/COMPATIBILIDAD.md` | Documentación normativa | `PORTADO` | 6 hosts x 8 columnas completas con fallback universal |
| 9 | Smoke tests S1–S3 | `evals/smoke/` + `run_smoke.py` | Fixtures y Runner | `RETIRADO` | Subsistema preliminar retirado y consolidado en el arnés formal de 20 goldens (PR-8). |

## E. Evals Formales, Goldens y Calidad (PR-5)

| # | Capacidad / Entregable | Artefacto en la skill | Tipo | Estado | Nota |
| :- | :--- | :--- | :--- | :--- | :--- |
| 1 | Dataset de Goldens | `evals/goldens/` (20 casos) | Dataset normativo | `PORTADO` | 20 goldens en 2 bloques (14 señalizados `g01`–`g13`, 6 ciegos no señalizados `b01`–`b06`); 7 categorías cubiertas, negativos y regla estricta |
| 2 | Harness de Evaluación | `evals/harness.py` | Arnés de medición | `PORTADO` | M1 script (100 %); M2/M3 con denominadores separados; soporte de dos bloques independientes (`signaled` / `unsignaled`); verificación sha256 del contexto (R3) |
| 3 | Protocolo de Ejecución | `evals/GOLDENS-PROTOCOL.md` | Guía de reproducción | `PORTADO` | Guion para ejecutar en host externo con traza reproducible |
| 4 | Informe de Calidad | `docs/QUALITY.md` | Documentación generada | `PORTADO` | Generado por harness en 2 bloques: Bloque 1 (Señalizado, 14 goldens) y Bloque 2 (Ciego, 6 goldens). M1 100 %; Bloque 1: M2 83,3 % y M3 38/39 (97,4 %) — ambos NO PASA OBJETIVO; Bloque 2: M2 100 %, M3 21/21 (100 %, 0 falsos PASA). Cobertura completa en Antigravity; resto de hosts NO VERIFICADO (R1) |
| 5 | Resultados Smoke auditados | `docs/SMOKE-RESULTS.md` | Documentación generada | `RETIRADO` | Subsistema preliminar retirado y consolidado en el arnés formal de 20 goldens (PR-8). |
| 6 | Medición real en host (PR-5-bis / Track C) | `evals/runs/2026-11-18/antigravity/` + `docs/QUALITY.md` | Evidencia de ejecución | `PORTADO Y VERIFICADO` | 120 trazas reales: 84 en señalizado (14x2x3) + 36 en ciego (6x2x3). Cobertura completa en ambos bloques y modos (100 % reproducibles R3) |


## E-bis. Límites de la evidencia medida (PR-5-bis / Track C)

- **Alcance:** la calidad se ha medido en **un único host** (Antigravity) con el modelo real
  `gemini-3.8-flash-high` v1.0. No hay ejecución en Claude Code, Claude Desktop, Cursor, Codex,
  ChatGPT ni Gemini: esos hosts siguen en `NO VERIFICADO` (R1).
- **Distinción metodológica en 2 bloques independientes:**
  - **Bloque 1 (Dataset señalizado, 14 goldens × 3 reps = 84 trazas):** 13 de los 14 goldens anuncian el
    defecto en un comentario. Mide **conformidad del informe y ausencia de falsos positivos** (M1 = 100 %,
    M2 = 83,3 % (mín 75,0 %, **NO PASA OBJETIVO** ≥ 90 %, 4 omisiones), M3 = 38/39 = 97,4 % (**NO PASA OBJETIVO** 100 %, 1 omisión), 0 FALSO_PASA).
  - **Bloque 2 (Dataset ciego / no señalizado, 6 goldens × 3 reps = 36 trazas):** código limpio sin
    comentarios reveladores. Mide **generalización cognitiva real a ciega**:
    - **M2 (modo archivo):** 100,0 % (12/12 esperados en Cat. 3–7 detectados en las 3 repeticiones; 0 omisiones, 0 falsos PASA).
    - **M3 (modo pegado):** 21/21 (100,0 %, 0 falsos PASA). Ante `b05_remoteexec` (whitelist no disponible sin `description.ext`), el modelo emitió `[NO_VERIFICADO]` de forma consistente en las 3 repeticiones, demostrando honestidad técnica y 0 bloqueantes inventados.
- **Corrección del ground truth (2026-11-19):** el 100 % previo del Bloque 1 era un artefacto del
  `expected.json` (no declaraba los defectos secundarios de `g03`, `g08` y `b06`). Con el ground truth
  corregido, M2 = 83,3 % y M3 = 97,4 %. El modelo detecta fiablemente el defecto **principal** de cada
  fichero (100 % en el bloque ciego) pero su *recall* sobre defectos **secundarios** en el mismo fichero
  es parcial e inconsistente (`g03:L4` 1/3 archivo y 2/3 pegado; `g08:L11` 1/3 archivo y 3/3 pegado).
  El límite es de exhaustividad del modelo, no de la skill.
- **Fidelidad de evidencia del linter (Track C / C.2):** 8 trazas históricas de `g*` referencian la ruta heredada `skills/arma3-sqf-review/...`. El arnés las expone formalmente en `docs/QUALITY.md` §4 (`stale_linter_traces = 8`). Las 36 trazas nuevas de `b*` están 100 % libres de rutas heredadas.
- **No se afirma "misma calidad" que el plugin original** (R5): la afirmación de equivalencia
  requiere tabla por host respaldada por trazas, y hoy solo hay un host con cobertura completa
  en modo archivo y en modo pegado.
- **Trazabilidad (R3):** las 120 trazas verifican el sha256 de su `contexto_cargado` contra los
  ficheros actuales del repo; 0 descartadas por contexto no reproducible.


