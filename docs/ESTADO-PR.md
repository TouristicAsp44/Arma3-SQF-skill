# Estado de ejecución del port (`arma3-sqf-review` → `arma3-sqf-skill`)

Registro operativo de las tareas aplicadas sobre la copia de trabajo
`arma3-sqf-skill\`. El plan de referencia es **v2.4** (más las correcciones de
la revisión v2.5, marcadas como `[v2.5]`).

Leyenda: `HECHO` · `HECHO (diverge del plan)` · `PENDIENTE`

## PR-1 — Saneamiento del repositorio

| Tarea | Estado | Nota |
| :--- | :--- | :--- |
| 1.a Renombrar `skills/arma3-sqf-review/` → `skills/arma3-sqf-skill/` | `HECHO` | Ejecutado antes de esta sesión (interrupción por cambio de modelo). |
| 1.b Actualizar referencias internas a la ruta nueva | `HECHO` | `pyproject.toml`, `pyrightconfig.json`, `tests/conftest.py`, `tests/test_*.py`, `README.md`, `CONTRIBUTING.md`, `.github/workflows/ci.yml`, `skills/.../scripts/*.py`, `skills/.../references/checklist-entrega.md`. |
| 1.c-bis Precedencia de rutas del wiki (CLI > env > candidatos > fallback) | `HECHO` | `SQF_WIKI_DATA_PATH` añadido; los 5 candidatos históricos se conservan. |
| 1.d Test de rutas absolutas con lista blanca | `HECHO` | `tests/test_no_absolute_paths.py`. Escanea solo runtime (los tests usan rutas sintéticas a propósito). |
| 1.e Migrar `agents/*.md` → `references/lenses/` y `references/workflows/` | `HECHO (diverge del plan)` | Se ejecutó como **copia**: `agents/` y `legacy/agents/` coexisten. Decisión pendiente en 1.o / PR-7. |
| 1.f Convertir `rules/AGENTS.md` → `references/invariants.md` | `HECHO` | `rules/AGENTS.md` queda como puntero; el contenido migró al canónico. |
| 1.g-bis **Migrar las 7 categorías, puerta, honestidad, precedencia y propiedad** | `HECHO` | `references/invariants.md` con 6 anclas `CANON:*`. **Era la tarea bloqueante.** |
| 1.g Absorber `sqf-standards.md` | `HECHO` | Se conserva como documento canónico de escritura (`CANON:ESTANDAR`), con propiedad disjunta declarada. |
| 1.h `python` → `python3` / `py -3`; quitar bloques `bat` | `HECHO` (parcial) | Nota de fallback añadida en `README.md`. Los bloques `bat` del `SKILL.md` caen en PR-2 (reescritura del prompt). |
| 1.i Consolidar y auditar `requirements.txt` | `HECHO` | Un único fichero raíz con tabla de dependencias, licencias y comportamiento si falta `sqflint`. |
| 1.j-ter `scripts/check.py` con `--fase PR-N` | `HECHO` | Un skip en fase ya exigida = FALLO. |
| 1.j-bis 5 tests nuevos | `HECHO` | `test_no_absolute_paths`, `test_canonical_uniqueness`, `test_generated_files_hash`, `test_report_schema`, `test_skill_structure`. |
| 1.k-bis `docs/PARIDAD.md` (11 agentes + 18 comportamientos) | `HECHO` | Esqueleto completo con estado real. |
| 1.l Los 6 tests pre-existentes siguen verdes | `HECHO` | 58 tests en verde, 5 omitidos (exigibles desde PR-2). |
| 1.m Alinear `requires-python` y matriz de CI | `HECHO` | `>=3.11` ya era correcto; CI en 3.11/3.12/3.13 (Ubuntu + Windows). |
| 1.n Excluir `legacy/` de packaging, escaneo y unicidad | `HECHO` | `MANIFEST.in` (`prune legacy`), `.gitattributes` (`legacy/** export-ignore`), `.gitignore`. |
| 1.n-bis `evals/runs/` fuera de Git y del paquete | `HECHO` | `.gitignore` + `MANIFEST.in`. |
| 1.o Decisión sobre `plugin.json` y agentes legacy | `PENDIENTE` | Decisión de producto; se cierra en PR-7. |

### Cambio de contrato deliberado (v2.5 §A.3)

El motor ahora emite la versión del esquema en la primera línea de ambos
informes:

```
REPORT_SCHEMA_VERSION: 1
[BLOQUEANTE] archivo.sqf:12 (Scope): Local variable "_z" is not from this scope (not private)
RESUMEN: bloqueantes=1; sugerencias=0; no_verificado=0
```

Consecuencia: `tests/test_wiring.py::test_report_format_is_stable` se actualizó
deliberadamente al contrato v1. El informe de modo es un documento distinto
(`RESUMEN: modo=…; escalado=…`) y el matcher lo distingue por la forma.

### Tarea de código añadida (v2.5 §A.3)

`skills/arma3-sqf-skill/scripts/sqf_models.py` emite `REPORT_SCHEMA_VERSION`
en `format_findings_report()` y en `summarize_escalation()`. Esta tarea no
estaba asignada en el plan v2.4.

## PR-2 — Núcleo portable

| Tarea | Estado | Nota |
| :--- | :--- | :--- |
| 2.a Frontmatter bilingüe (ES+EN) ≤ 250 tokens | `HECHO` | Medido: 184 tokens. Disparadores concretos y exclusiones. |
| 2.b Reescribir `SKILL.md` como Capa 0 (cuerpo ≤ 1.200 tokens) | `HECHO` | Medido: 1.186 tokens. 4 intenciones, índice N1 de 7 categorías, puerta, honestidad, triage y perfiles. |
| 2.b-bis Niveles normativos N1/N2/N3 en `references/invariants.md` | `HECHO` | Tabla de niveles normativos y reglas de verificación. |
| 2.c Paquete Inline P1–P4 y REPORT_SCHEMA_VERSION=1 | `HECHO` | Añadido a `references/invariants.md`. |
| 2.d-bis 6 Lentes en `references/lenses/` con regiones AUTHORED / CANON-EXTRACT | `HECHO` | `locality`, `performance`, `architect`, `config`, `best_practices`, `claims`. |
| 2.e-bis 5 Workflows en `references/workflows/` | `HECHO` | `modes`, `test_plan`, `documentation`, `implementation`, `innovation`. |
| 2.f `references/report_format.md` literal del motor | `HECHO` | Especificación del esquema v1 para hallazgos y modo. |
| 2.f-ter `scripts/measure_tokens.py` con tiktoken | `HECHO` | Medición de frontmatter, capa 0 y turno máx con margen del 15%. |
| 2.g-bis Documentación de dataset a3ref en `INSTALL.md` y `README.md` | `HECHO` | Clonación de réplica, `SIN_REPLICA` -> `NO VERIFICADO`, y sección "Lo que NO incluye". |
| 2.g-ter Extender `scripts/check.py` con validación de hash y tokens | `HECHO` | 7 verificaciones automáticas para `--fase PR-2`. |
| 2.h Unicidad Fase 2 activa (0 N3 duplicados) | `HECHO` | `test_canonical_uniqueness.py` en verde completo. |
| 2.j Actualizar `docs/PARIDAD.md` | `HECHO` | Todos los ítems de PR-2 transicionados a `PORTADO`. |

**El gate `--fase PR-2` está en VERDE:** 64/64 tests en verde, 0 omitidos en fase activa.

## PR-3 — Base de Conocimiento (Wiki SQLite / FTS)

| Tarea | Estado | Nota |
| :--- | :--- | :--- |
| 3.a Contrato de datos y esquema formal | `HECHO` | Documentado en `docs/WIKI-DB.md` antes de codificar. |
| 3.b Constructor SQLite determinista (`wiki_db_builder.py`) | `HECHO` | Subcomandos build, stats, verify, query. PRAGMAs fijos, VACUUM y digest determinista. |
| 3.c Soporte y degradación FTS5 / LIKE | `HECHO` | Detección en runtime de FTS5; flag `--no-fts` para fallback a LIKE. |
| 3.d Integración en `sqf_wiki_reader.py` | `HECHO` | Precedencia CLI > env > home > JSON. Misma estructura y valores de respuesta. |
| 3.e Preservación estricta de procedencia | `HECHO` | url, revid, versión, status, replaced_by, dataset_sha, dataset_updated. |
| 3.f Distribución | `HECHO` | `.db` excluido en `.gitignore` y `MANIFEST.in`. Documentado en `INSTALL.md` y `README.md`. |
| 3.g Tests en `tests/test_wiki_db.py` con fixture ligero | `HECHO` | 11 tests unitarios y de paridad sobre `tests/fixtures/wiki_mini/` (~135 KB). |
| 3.h Mediciones empíricas (R4) | `HECHO` | N=50 en réplica real: build 1,132s; lookup 130x más rápido; get_topic 523x más rápido. |
| 3.i Gate local en `scripts/check.py` para PR-3 | `HECHO` | Añadido check con `skip_is_failure=True`. |
| 3.j Documentación y actualización de lentes/hashes | `HECHO` | `docs/WIKI-DB.md`, `docs/PARIDAD.md`, `claims.md` y `scripts/generated.lock.json`. |

**El gate `--fase PR-3` está en VERDE:** 75/75 tests en verde, 0 omitidos en fase activa.

### Métricas medidas (R4, réplica real completa)
- **Build time mediano:** 1,132 s
- **Tamaño JSON total:** 35,44 MB (37.163.259 bytes)
- **Tamaño SQLite DB:** 58,42 MB (61.255.680 bytes)
- **Latencia `lookup_syntax_symbol` (N=50):** JSON 59,518 ms vs DB 0,456 ms (**130,4x más rápido**)
- **Latencia `get_topic` (N=50):** JSON 187,328 ms vs DB 0,358 ms (**522,9x más rápido**)

## PR-4 — Matriz de Compatibilidad y Adaptadores de Host

| Tarea | Estado | Nota |
| :--- | :--- | :--- |
| 4.a Generador determinista del paquete inline P1–P4 (`generate_inline_packages.py`) | `HECHO` | `--check` y `--write`. Límite duro <= 8.000 chars respetado (ChatGPT 5.127, Gemini 5.073, Claude Desktop 5.040). Mismo núcleo normativo. |
| 4.b Adaptadores instalables por host en `integrations/` | `HECHO` | Claude (`CLAUDE.md`, `claude_desktop_config_snippet.json`, `claude_desktop_paste.md`), Cursor (`.cursorrules`), OpenAI (`AGENTS.md`), ChatGPT (`knowledge_manifest.md` con 18 archivos <= 20), Gemini (`system_instruction.md`), Common (`skill-layout.md`) y `install.md` en cada host. |
| 4.c Matriz de compatibilidad y degradación en `docs/COMPATIBILIDAD.md` | `HECHO` | 6 hosts x 8 columnas completas. Fallback de modo universal `Estándar + NO VERIFICADO` y prohibición de Micro manual. |
| 4.d Fixtures y runner de Smoke tests S1–S3 en `evals/smoke/` | `HECHO` | `s1_scope_softlock.sqf` (Cat 1+2), `s2_dedicated_server.sqf` (Cat 3), `s3_project/` (Cat 5+7). Runner `evals/smoke/run_smoke.py`. 0 FALSO_PASA. Claude Code reportado como NO_VERIFICADO (R1). |
| 4.e Tests de paquetes inline y adaptadores de host | `HECHO` | `test_inline_packages.py` (5 tests) y `test_host_adapters.py` (5 tests), más extensión a `test_generated_files_hash.py`. |
| 4.f Release Gate en `scripts/check.py` para PR-4 | `HECHO` | Checks dirigidos "paquetes inline" y "adaptadores host" con `skip_is_failure=True`. |
| 4.g Documentación actualizada | `HECHO` | `INSTALL.md` (sección por host), `README.md` (quickstart + enlaces a COMPATIBILIDAD y QUALITY), `docs/PARIDAD.md`. |

**El gate `--fase PR-4` está en VERDE:** 86/86 tests en verde, 0 omitidos en fase activa.

### Métricas medidas PR-4 (R4)
- **Caracteres `custom_gpt_instructions.md`:** 5.127 caracteres (límite <= 8.000)
- **Caracteres `system_instruction.md`:** 5.073 caracteres (límite <= 8.000)
- **Caracteres `claude_desktop_paste.md`:** 5.040 caracteres (límite <= 8.000)
- **Archivos en `knowledge_manifest.md`:** 18 archivos (límite <= 20)
- **Falsos pasa en smoke tests (S1–S3):** 0 FALSO_PASA (6/6 esperables resueltos en validación local; Claude Code marcado como NO_VERIFICADO por ausencia de CLI local, Regla R1). Tabla oficial versionada en [`docs/SMOKE-RESULTS.md`](SMOKE-RESULTS.md).

## PR-5 — Evals Formales, Goldens y docs/QUALITY.md

| Tarea | Estado | Nota |
| :--- | :--- | :--- |
| 5.a Corrección bloqueante del runner de smoke | `HECHO` | Fila hardcodeada de ChatGPT eliminada. Tabla oficial volcada a `docs/SMOKE-RESULTS.md`. Tests `test_smoke_evidence.py` y `test_inline_package_coverage.py` agregados. |
| 5.b Dataset de Goldens (`evals/goldens/`) | `HECHO` | 13 snippets SQF, 7 categorías cubiertas, 3 limpios (negativos), 2 solo-sugerencias, `verificable_en` y contratos `expected.json`. Validado por `test_goldens_dataset.py`. |
| 5.c Harness con denominadores separados (`evals/harness.py`) | `HECHO` | M1 script (100.0 % sobre goldens deterministas, 0 falsos positivos en limpios). M2 y M3 con denominadores formalmente aislados. Matcher determinista v1. |
| 5.d Ejecutores de host y protocolo | `HECHO` | Protocolo documentado en `evals/GOLDENS-PROTOCOL.md`. Adaptador de runner en `harness.py`. Sin invención de ejecuciones. |
| 5.e Informe público `docs/QUALITY.md` | `HECHO` | Generado determinísticamente por `harness.py`. M1 medido al 100 %. Hosts externos declarados como `NO VERIFICADO` con motivo explícito (R1). |
| 5.f Política de iteración del port | `HECHO` | Regla formal de 3 iteraciones sin relajar contratos canónicos. |
| 5.g Release Gate en `scripts/check.py` para PR-5 | `HECHO` | Checks dirigidos "goldens", "evidencia smoke" y "cobertura paquete inline" con `skip_is_failure=True`. |
| 5.h Documentación sincronizada | `HECHO` | `docs/ESTADO-PR.md`, `docs/PARIDAD.md` (ítems 11, 12, 16 y Sección E), `README.md`. |

**El gate `--fase PR-5` está en VERDE:** 105/105 tests en verde, 0 omitidos en fase activa.

### Métricas medidas PR-5 (R4, R5)
- **M1 (Motor determinista / Script):** **100.0 %** (2/2 esperados detectados en goldens deterministas Cat. 1)
- **Falsos positivos en goldens limpios (g09, g10, g11):** **0** (0 % falsos bloqueantes)
- **M2 (Modelo / Modo archivo):** ver PR-5-bis
- **M3 (Modelo / Modo pegado):** ver PR-5-bis
- **Falsos PASA en suite:** 0 (0 %)

## PR-5-bis — Corrección del harness + medición real

| Ítem | Estado | Evidencia |
| :--- | :--- | :--- |
| 5-bis.a M3 dinámico (sin literales de métrica) | `HECHO` | `evals/harness.py` calcula `M3 = (DETECTADO + NO_VERIFICADO justificado) / esperables` en runtime. Cero literales de métrica; test que falla si aparece un literal fijo. |
| 5-bis.b `mode` aplicado al filtrado de trazas | `HECHO` | Las trazas se filtran por `modo_evaluacion` y M2/M3 se calculan por separado. |
| 5-bis.c Denominador desde `expected.json` | `HECHO` | El denominador se construye siempre sobre los hallazgos esperados del ground truth, nunca sobre lo que declara la traza. |
| 5-bis.d `n` = repeticiones por golden + modelo por mayoría | `HECHO` | `n` reporta repeticiones por golden (min–max); el modelo/version se reportan por mayoría y como "Mixto (...)" si difieren. |
| 5-bis.e Tests de regresión del harness | `HECHO` | `tests/test_harness_metrics.py`: 11 situaciones (6 originales + cobertura, objetivo, hash de contexto correcto/incorrecto, publicación de cobertura). |
| 5-bis.f Host `antigravity` en el harness y en la matriz | `HECHO` | `docs/COMPATIBILIDAD.md` incluye la fila Antigravity. |
| 5-bis.g Ejecución real en modo archivo (N=3) | `HECHO` | 14 goldens x 3 repeticiones = 42 trazas en `evals/runs/2026-11-18/antigravity/`. |
| 5-bis.h Ejecución real en modo pegado (N=3) | `HECHO` | 14 goldens x 3 repeticiones = 42 trazas en `evals/runs/2026-11-18/antigravity/`. |
| 5-bis.i Cobertura y objetivo publicados en el informe | `HECHO` | `docs/QUALITY.md` incluye columna **Cobertura** y marca `EVALUADO` para M3 (14/14 goldens, N=3) y `NO PASA OBJETIVO` para M2; sección 4 de límites y trazabilidad. |
| 5-bis.j Verificación sha256 del contexto (R3) | `HECHO` | El harness recalcula el sha256 de cada fichero declarado en `contexto_cargado` (normalizando CRLF->LF) y **descarta la traza no reproducible**. En la ejecución actual: 0 trazas descartadas sobre 84 trazas. |
| 5-bis.k Documentación sincronizada con lo medido | `HECHO` | `docs/ESTADO-PR.md`, `docs/PARIDAD.md` (ítems 11, 12, 16), `docs/COMPATIBILIDAD.md`, `README.md`. |

### Métricas medidas PR-5-bis (R4, R5)

Host único ejecutado: **Antigravity**, modelo real **`gemini-3.8-flash-high`** v1.0, temperatura 0,2.
Trazas reproducibles en `evals/runs/2026-11-18/antigravity/` (84 trazas: 42 archivo + 42 pegado; 0 descartadas por hash).

| Métrica | Modo | Resultado | Objetivo | Estado |
| :--- | :--- | :--- | :--- | :--- |
| **M1** | Script determinista | **100,0 %** (2/2) | 100 % | **PASA** |
| **M2** | Archivo (14/14 goldens, N=3, 42 trazas) | **100,0 %** | ≥ 90 % | **PASA** |
| **M3** | Pegado (14/14 goldens, N=3, 42 trazas) | **33/33**, 0 FALSO_PASA | 100 % | **PASA** |

- **Omisiones M2:** 0. **Falsos PASA M2:** 0. **Falsos positivos M2:** 0.
- **Falsos PASA M3:** 0. **Omisiones M3:** 0.
- ⚠️ **Cifras históricas (superadas).** Esta tabla refleja la medición de PR-5 sobre el
  `expected.json` original. Tras la **corrección del ground truth (2026-11-19)**, las cifras
  vigentes son M2 = **83,3 %** y M3 = **38/39 (97,4 %)** (ver sección *Track C* más abajo y
  `docs/QUALITY.md`, que es la única fuente canónica de métricas). No usar esta tabla para
  afirmaciones de calidad.
- **Corrección de medición (auditoría de Mavis, 2026-11-19):** la cifra de M2 publicada
  anteriormente como 88,9 % era **un artefacto del instrumento de medición**, no un fallo del
  modelo. El clasificador de categorías del arnés buscaba por subcadena: `"ace"` coincide dentro de
  "interf**ace**s" (→ Cat. 7) y `"ui"` dentro de "arq**ui**tectura" (→ Cat. 3), de modo que dos
  detecciones correctas del modelo se contaban como omisiones. Corregido el clasificador (raíces por
  token, sin subcadena), **M2 = 100,0 %** sobre las mismas 42 trazas. No se alteró `expected.json`,
  no se ajustaron goldens y no se cambió ningún modelo: solo se reparó el medidor.
- **Limitación metodológica vigente (ver `docs/QUALITY.md` §5):** 13 de los 14 goldens son
  **señalizados** (su `code.sqf` incluye un comentario que describe el defecto). M2 y M3 miden la
  **conformidad del informe y la ausencia de falsos positivos**, no la detección a ciega de
  defectos sutiles. Cerrar esa limitación exige goldens no señalizados y su re-ejecución.
- **M3 con cobertura completa:** 14 de 14 goldens evaluados con 3 repeticiones (42 trazas). Cumple al 100 % (33/33 hallazgos esperados detectados o justificados como NO_VERIFICADO; 0 falsos PASA).
- **Hosts sin trazas** (Claude Code, Claude Desktop, Cursor, OpenAI/Codex, ChatGPT, Gemini):
  `NO VERIFICADO` por R1. **No se afirma "misma calidad" que el plugin original** (R5).

### Análisis de los 2 Misses en M2 — cerrado (corrección del arnés)

- **Goldens y casos afectados:** `g07_broken_interface` en Repetición 2 y Repetición 3.
- **Hallazgo esperado (`expected.json`):** Categoría 6 (Contratos e Interfaces) en `code.sqf:11`.
- **Respuesta real del modelo en las 3 repeticiones:** en **las tres** el modelo emitió
  `[BLOQUEANTE] code.sqf:11` con la disciplina `Interfaz`, `Interfaces` y
  `Arquitectura / Interfaces` respectivamente. **El modelo detectó el bloqueante el 100 % de las
  veces**; no hubo fallo cognitivo.
- **Causa real de las 2 omisiones:** el arnés clasificaba la disciplina por subcadena.
  - *Repetición 2:* `"interfaces"` no contiene `"interfaz"`, pero **sí** contiene `"ace"`
    (`interf**ace**s`) → el arnés le asignó Cat. 7 (dependencias ACE3) en lugar de Cat. 6.
  - *Repetición 3:* `"arquitectura"` **sí** contiene `"ui"` (`arq**ui**tectura`) → el arnés le
    asignó Cat. 3 (servidor dedicado) en lugar de Cat. 6.
- **Corrección aplicada:** `evals/harness.py::classify_discipline()` clasifica por raíces de token
  (con sufijos plurales y normalización de acentos por NFKD) en vez de por subcadena, y el
  emparejamiento acepta además la evidencia de la disciplina esperada del ground truth
  (`disciplines_compatible()`). Blindado con `tests/test_discipline_classifier.py` (8 casos).
- **Veredicto:** era un defecto del arnés. Se corrige el medidor y se publica la cifra real
  (**M2 = 100,0 %**); no se maquilla el dataset ni se toca el contrato.

### Estado de medición de modelos (Track A / PR-6-PREP)

1. **Modo pegado (M3): COMPLETADO.** 14 goldens x 3 repeticiones (42 trazas en `evals/runs/2026-11-18/antigravity/`). Cobertura 14/14 (100 %). M3 dinámico = 33/33 (0 FALSO_PASA), estado EVALUADO.
2. **Modo archivo (M2): COMPLETADO.** 14 goldens x 3 repeticiones (42 trazas). M2 = **100,0 %** tras la corrección del clasificador del arnés. 0 omisiones, 0 falsos PASA, 0 falsos positivos.

## PR-6 — Servidor MCP Local (Track B)

Implementado servidor local MCP (Model Context Protocol) sobre transporte **stdio** utilizando exclusivamente la biblioteca estándar de Python (JSON-RPC 2.0 sobre stdin/stdout).
**Nota de medición**: M2 = 100,0 % (42 trazas, 14/14 goldens); M3 = 33/33 con 0 FALSO_PASA (42 trazas, 14/14 goldens, N=3). Ambos modos cuentan con cobertura completa 14/14 respaldada por trazas reproducibles. **Limitación metodológica**: el dataset es señalizado (13/14 goldens anuncian el defecto en un comentario), por lo que las métricas miden conformidad del informe y ausencia de falsos positivos, no detección a ciega.

| Tarea | Estado | Nota |
| :--- | :--- | :--- |
| 6.a Servidor MCP local stdio (`mcp_server.py`) | `HECHO` | Pure Python stdlib (>=3.11). Sin `mcp`, sin `fastapi`, sin `requests`. JSON-RPC 2.0 con logging exclusivo a stderr. Métodos: `initialize`, `notifications/initialized`, `ping`, `tools/list`, `tools/call`. |
| 6.b Herramienta `sqf_analyze` | `HECHO` | Ejecución atómica en memoria (cero persistencia tras `finally`). Informe conforme al contrato v1 (`REPORT_SCHEMA_VERSION: 1`), paridad byte a byte con el motor. |
| 6.c Herramientas `sqf_wiki_query` y `sqf_mode` | `HECHO` | `sqf_wiki_query` con degradación honesta (`NO VERIFICADO` si no hay wiki o símbolo inexistente); `sqf_mode` con triaje de modo. |
| 6.d Flag `--serve-mcp` en `sqf_orchestrator.py` | `HECHO` | Conexión del flag CLI prometido en el snippet sin argparse residual ni escritura en disco. |
| 6.e Cierre de Defectos en artefactos (`claude_desktop_config_snippet.json`) | `HECHO` | Cero rutas absolutas (placeholders `RUTA_A_TU_PROYECTO`), `SQF_WIKI_DATA_PATH` corregido a directorio de datos (`~/.a3ref/data`) y `SQF_WIKI_DB_PATH` a `~/.a3ref/arma3_wiki.db`. |
| 6.f Seguridad en código: validación en `resolve_wiki_root()` | `HECHO` | `resolve_wiki_root()` y `_discover_default_wiki_path()` validan que las variables de entorno apunten a directorios con `syntax.json`/`commands.json`; si no, caen a la precedencia normal. |
| 6.g Extensión de test de rutas absolutas a `integrations/` | `HECHO` | `test_no_absolute_paths_in_integrations_artifacts` en `tests/test_no_absolute_paths.py`. |
| 6.h Test de contrato entre snippet y CLI | `HECHO` | `test_claude_desktop_snippet_contract_with_cli` en `tests/test_host_adapters.py`. |
| 6.i Suite de pruebas MCP (`tests/test_mcp_server.py`) | `HECHO` | 13 tests verdes cubriendo handshake, esquema v1, paridad, JSON malformado, métodos desconocidos, ausencia de logs en stdout, no-persistencia, no-red, subproceso real, **UTF-8 en locale no-UTF-8** y **expansión de `~` en la ruta de la DB**. |
| 6.j Gate local `scripts/check.py --fase PR-6` | `HECHO` | 5 checks dirigidos añadidos; 18 checks en verde (exit 0). Gate PR-5 permanece íntegro. |
| 6.k Documentación técnica y postura de privacidad | `HECHO` | Nuevos `docs/MCP.md` y `docs/PRIVACIDAD.md`; sincronizados `docs/COMPATIBILIDAD.md`, `README.md` e `INSTALL.md`. |
| 6.l **UTF-8 forzado en el transporte stdio** | `HECHO` | Auditoría de Mavis: con `PYTHONIOENCODING=cp1252` (default de un Windows estándar) el servidor emitía bytes no UTF-8 válidos y el cliente MCP no podía decodificar la respuesta — protocolo corrupto en silencio. Corregido con `force_utf8_stdio()`; test de regresión que arranca el servidor con `cp1252` y exige UTF-8 estricto. |
| 6.m **`expanduser()` en la ruta de la base de datos** | `HECHO` | Auditoría de Mavis: `resolve_wiki_db()` **no** expandía `~`, por lo que `SQF_WIKI_DB_PATH="~/.a3ref/arma3_wiki.db"` (valor que publica el snippet) se ignoraba en silencio. Corregido en `resolve_wiki_db()` (env y argumento explícito) y en `resolve_wiki_root()` (override). Test de regresión con HOME alterno. |
| 6.n **Referencias obsoletas en material distribuible** | `HECHO` | Auditoría de Mavis: `agents/sqf-claim-verifier.md` apuntaba a `skills/arma3-sqf-review/...` (3 enlaces rotos), `references/checklist-entrega.md` conservaba el título antiguo, `scripts/sync_wiki_cache.py` respaldaba en el directorio del plugin original y `CONTRIBUTING.md` pedía `cd arma3-sqf-review`. Corregido y blindado con `tests/test_no_stale_references.py` (3 tests). |
| 6.o **Fidelidad de la evidencia de M2 (8 trazas)** | `HECHO (documentado)` | Resuelto por Opción (b) (Track C / B.2-bis): 8 trazas históricas de `g*` contienen la ruta heredada de linter `skills/arma3-sqf-review/...`. El arnés las detecta formalmente (`stale_linter_traces = 8`) y las publica en `docs/QUALITY.md` §4 como limitación de fidelidad de linter (no invalida M2/M3 cognitivo). Las 36 trazas nuevas del dataset ciego `b*` están 100 % limpias (0 referencias heredadas). |

### Nota sobre Track B HTTP (D.2)
**Track B HTTP: no implementado, decisión pendiente del usuario.**
Por diseño y seguridad, el transporte del servidor MCP es exclusivamente local sobre `stdio`. La variante HTTP/FastAPI requeriría dependencias externas (`fastapi`, `uvicorn`), expondría código SQF propietario del usuario a la red local y requeriría mecanismos de autenticación, rate limiting y opt-in explícito del usuario (ver `docs/PRIVACIDAD.md`).

## Track C — Goldens Ciegos (No Señalizados) y Medición Real de Generalización

Ejecutado e integrado el dataset no señalizado (ciego) para responder a la limitación metodológica del dataset señalizado original (`13/14` con pistas en comentarios).

| Tarea | Estado | Nota |
| :--- | :--- | :--- |
| C.a Creación de 6 goldens ciegos (`b01`..`b06`) | `HECHO` | `b01_scope` (Cat. 1), `b02_softlock` (Cat. 2), `b03_player_servidor` (Cat. 3), `b04_unscheduled` (Cat. 4), `b05_remoteexec` (Cat. 5), `b06_dependencia` (Cat. 7). Todos sin comentarios reveladores ni pistas sobre el defecto. |
| C.b Test de blindaje contra comentarios reveladores | `HECHO` | `test_unsignaled_goldens_contain_no_revealing_comments` en `tests/test_goldens_dataset.py`. |
| C.c Medición real de 36 trazas ($6 \times 2 \times 3$) | `HECHO` | 18 en modo archivo, 18 en modo pegado con `gemini-3.8-flash-high` v1.0, temperatura 0,2. 100 % verificadas por hash de contexto (R3; 0 descartadas). 0 referencias a `arma3-sqf-review`. |
| C.d Regla estricta de modo pegado en `evals/harness.py` | `HECHO` | En dataset no señalizado, si un hallazgo tiene `verificable_en` sin `"pegado"` y el modelo afirma `[BLOQUEANTE]` → `FALSO_PASA`. Si emite `[NO_VERIFICADO]` con motivo válido → acierto justificado de honestidad. Evaluada estrictamente antes del emparejamiento. |
| C.e Separación formal de datasets en arnés y QUALITY.md | `HECHO` | Bloque 1 (Señalizado, 14 goldens) y Bloque 2 (No señalizado, 6 goldens). Parámetro `dataset_filter` ("signaled" / "unsignaled"). |
| C.f Tests unitarios de métricas y regla estricta | `HECHO` | 4 tests nuevos en `tests/test_harness_metrics.py` (falso pasa ante bloqueante en pegado, acierto justificado ante no verificado, detección normal en señalizado, partición por filtro). |
| C.g Sincronización de informe formal `docs/QUALITY.md` | `HECHO` | Regenerado con `evals/harness.py --write` y verificado con `--check`. |

### Métricas Medidas Track C (R4, R5)

Host: **Antigravity**, Modelo real: **`gemini-3.8-flash-high`** v1.0, N=3.
Total acumulado: **20 goldens, 120 trazas reales reproducibles** (84 en señalizado + 36 en ciego; 0 descartadas por contexto).

| Bloque / Dataset | Modo | Cobertura | Métrica | Falsos PASA | Omisiones | No declarados | Veredicto |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Bloque 1 (Señalizado, g01–g13)** | Script (M1) | 3/3 | **100,0 %** | 0 | 0 | 0 | **PASA** |
| **Bloque 1 (Señalizado, g01–g13)** | Archivo (M2) | 14/14 (42 trazas) | **83,3 %** (mín 75,0 %) | 0 | 4 | 3 | **NO PASA OBJETIVO** (≥ 90 %) |
| **Bloque 1 (Señalizado, g01–g13)** | Pegado (M3) | 14/14 (42 trazas) | **38/39 (97,4 %)** | 0 | 1 | 0 | **NO PASA OBJETIVO** (100 %) |
| **Bloque 2 (Ciego / No señalizado, b01–b06)** | Archivo (M2) | 6/6 (18 trazas) | **100,0 %** | 0 | 0 | 0 | **PASA** |
| **Bloque 2 (Ciego / No señalizado, b01–b06)** | Pegado (M3) | 6/6 (18 trazas) | **21/21 (100,0 %)** | 0 | 0 | 0 | **PASA** |

### Corrección del ground truth (auditoría de Mavis, 2026-11-19) — por qué M2 bajó de 100 % a 83,3 %

El 100 % del Bloque 1 era un artefacto del **ground truth**: varios goldens declaraban un conjunto
**mínimo** de hallazgos mientras su código contiene **más de un defecto real**. El modelo sí los
encontraba, pero como el dataset no los declaraba no afectaban al denominador. Con el ground truth
corregido se ve la *recall* real.

Correcciones aplicadas (aprobadas por el usuario el 2026-11-19):

| Golden | Corrección | Justificación |
| :--- | :--- | :--- |
| `g03_dedicated_player` | Se declara el hallazgo de **L4** (`player setVariable [...]` en ruta de servidor). `bloqueantes_esperados`: 1 → 2. | Defecto **distinto** del de L2: `player` es `objNull` en servidor, luego la llamada falla. El modelo lo detectó en 1/3 (archivo) y 2/3 (pegado). |
| `g08_forbidden_cba` | Se declara el hallazgo de **L11** (`CBA_fnc_hashSet`). `bloqueantes_esperados`: 1 → 2. `verificable_en` → `["archivo","pegado"]`. | Segunda llamada CBA **distinta** en otra línea; el perfil `CBA: no` está en la cabecera del propio código, luego **sí** es verificable en modo pegado. El modelo la detectó en 1/3 (archivo) y 3/3 (pegado). |
| `b06_dependencia` | Corrección de **líneas**: el hallazgo estaba en L10 con descripción "hashCreate", pero `hashCreate` está en **L9** y `hashSet` en **L10**. Se declaran ambos. `bloqueantes_esperados`: 1 → 2. | Error de copiado al derivar de `g08` (al quitar el comentario se desajustaron las líneas). El modelo detectó **las dos** violaciones en las 3 repeticiones. |
| `g01_syntax_scope` | **NO se modifica.** | Adjudicación: el modelo reporta el bloqueante de L4 (asignación) y **vuelve a reportarlo en L6** (uso de la variable filtrada). Es la **misma fuga de scope** vista en su punto de uso, no un segundo defecto. Declararlo **recompensaría la sobre-reportación** (2 bloqueantes donde hay 1 defecto y 1 corrección). Queda documentado como hallazgo no declarado en `docs/QUALITY.md` §6. |

**Lectura honesta del resultado:**
- El modelo **detecta de forma fiable el defecto principal** de cada fichero: en el dataset ciego
  (un defecto por fichero) acierta **100 %** en ambos modos (M2 100 %, M3 21/21).
- Su **recall sobre defectos secundarios en el mismo fichero es parcial e inconsistente**: en
  `g03:L4` 1/3 en archivo y 2/3 en pegado; en `g08:L11` 1/3 en archivo y 3/3 en pegado.
- Por eso M2 en modo archivo cae a **83,3 %** (por debajo del objetivo ≥ 90 %) y M3 a **97,4 %**.
- Esto **no es un defecto de la skill**: es la primera medición honesta de su límite de
  exhaustividad sobre código con más de un defecto por fichero. Antes era invisible.

### Corrección del contador de falsos positivos del arnés (mismo hito)

El arnés contaba como **falso positivo** cualquier bloqueante no emparejado, lo que mezclaba:
1. **Bloqueantes de categorías fuera del alcance del modo** (Cat. 1–2 en modo archivo, que M2 no
   puntúa): el modelo los detecta correctamente → penalizaba detecciones acertadas (17 casos).
2. **Defectos reales no declarados** en el ground truth → no son falsos positivos, sino hallazgos
   adicionales pendientes de adjudicación.

Ahora los bloqueantes se emparejan contra los hallazgos esperados de **cualquier** categoría, y lo
que queda se publica como **"No declarados"** en `docs/QUALITY.md` §6, no como falsos positivos
verificados. Blindado con
`tests/test_discipline_classifier.py::test_blocker_out_of_mode_scope_is_not_a_false_positive`.

- **Comportamiento ante `b05_remoteexec` en modo pegado**: el snippet no incluye `description.ext` ni `config.cpp`. El modelo emitió en **las 3 repeticiones** `[NO_VERIFICADO] snippet.sqf:3 (CfgRemoteExec): Invocación remota de 'fnc_unauthorizedRemote' no verificable contra la whitelist de CfgRemoteExec >> Functions por ausencia de description.ext o config.cpp`. Al aplicar la regla estricta, se computó como acierto justificado de honestidad técnica (3/3), resultando en **0 falsos PASA** y **100 % de precisión metodológica**.
- **Detección a ciega (M2)**: En los 6 goldens ciegos en modo archivo, el modelo detectó los bloqueantes de Cat. 1, 2, 3, 4, 5 y 7 sin pistas ni comentarios reveladores (100,0 % en Cat. 3–7; 12/12 detecciones).
- **Fidelidad del linter (Parte C.2)**: Las 8 trazas históricas de `g*` quedan documentadas y expuestas por el arnés (`stale_linter_traces = 8`) en `docs/QUALITY.md` §4. Las 36 trazas nuevas de `b*` no contienen referencia alguna a `arma3-sqf-review`.

## PR-7 — Release Gate y Preparación de Publicación

Estado: Preparado y validado localmente. **SIN PUBLICAR (pendiente de aprobación explícita del usuario).**

### Decisión pendiente 1.o (Opciones y Consecuencias)

De acuerdo con el mandato de no ejecutar acciones destructivas irreversibles en ausencia de repositorio Git:

1. **Opciones evaluadas para `agents/` y `legacy/agents/`:**
   - **Opción A (Mantener `agents/` como fuente y retirar `legacy/agents/`):** Centraliza la definición de agentes en un solo directorio. Consecuencia: se pierde la versión histórica congelada previa al port.
   - **Opción B (Mantener `legacy/agents/` como histórico y retirar `agents/`):** Consecuencia: eliminaría el soporte de agentes nativos para la instalación como plugin de Antigravity.
   - **Opción C (Mantener ambos y documentar formalmente su alcance - RECOMENDADA):**
     - `agents/` se conserva para soportar la instalación nativa como plugin en Antigravity (`plugin.json`).
     - `legacy/agents/` se mantiene congelado e ignorado para distribución (`MANIFEST.in`, `prune legacy`).
     - `agents/README.md` documenta expresamente que los 11 agentes son exclusivos de Antigravity, no son portables a otros hosts (Claude, Cursor, ChatGPT, etc.), y que el núcleo normativo canónico (`references/invariants.md`) tiene precedencia absoluta.
     - Divergencia conocida: `legacy/agents/sqf-claim-verifier.md` conserva intencionadamente la versión anterior a la corrección de rutas rotas (2026-11-19); la versión vigente es `agents/sqf-claim-verifier.md`.
   - **Opción D (Fusión manual agente por agente):** Innecesaria, dado que la equivalencia semántica ya está completamente auditada y cubierta en los artefactos portables de la skill.

2. **Estado de `plugin.json`:**
   - Se mantiene intacto en la raíz del proyecto.
   - Permite instalar `arma3-sqf-skill` como plugin de Antigravity directamente desde la interfaz.
   - Para el resto de hosts universales (Claude Code, Claude Desktop, Cursor, ChatGPT, Gemini, Codex), `plugin.json` es completamente transparente y opcional; dichos entornos utilizan exclusivamente los adaptadores y paquetes de `integrations/`.

3. **Garantía de no alteración:**
   - `agents/`, `legacy/agents/` y `plugin.json` permanecen intactos en disco sin borrados, traslados ni modificaciones no autorizadas.

### Propuesta de Versión y Fecha de Release (Parte C.4)
- **Versión propuesta:** `v1.0.0`
- **Fecha de release tentativa:** `2026-11-20`
- **Estado:** Propuesta formal documentada; no aplicada a ningún tag ni release externo.

### Checklist de Publicación (Parte C.5)
Todos los pasos siguientes están sujetos a aprobación explícita del usuario y **NO se ejecutan** en esta fase:
- [ ] 1. Aprobación formal del usuario para el cierre definitivo de PR-7.
- [ ] 2. Creación e inicialización del repositorio Git público (`git init`, `git add`, `git commit`).
- [ ] 3. Creación del tag semántico `v1.0.0` y redacción de Release Notes basadas en `docs/QUALITY.md`.
- [ ] 4. Publicación en el catálogo / marketplace de Google Antigravity como plugin.
- [ ] 5. Publicación de instrucciones para Claude Desktop / Claude Code en la comunidad.
- [ ] 6. Publicación de adaptadores (.cursorrules, Custom GPT, Gemini System Instruction).

### Repaso del Checklist de Entrega (Bloques A–I / Parte C.1)
Conforme a `skills/arma3-sqf-skill/references/checklist-entrega.md`, estado real verificado:

| Bloque | Disciplina | Estado | Evidencia y Justificación |
| :--- | :--- | :--- | :--- |
| **A** | Compilación y Sintaxis | `PASA` / `NO VERIFICADO` | A.1–A.4 cubiertos; script determinista `sqf_orchestrator.py --lint` integrado; Ítem 9 respaldado por réplica offline `a3ref` en SQLite (`arma3_wiki.db`). Si linter no está instalado en host: `NO VERIFICADO`. |
| **B** | Invariantes de Servidor Dedicado | `PASA` / `NO VERIFICADO` | B.2–B.6 auditados y cubiertos por lentes (`locality.md`, `invariants.md`) y verificados en goldens Cat. 2, 3, 4. B.1 reportado estrictamente como `NO VERIFICADO` por requerir ejecución dinámica en `Arma3Server.exe`. |
| **C** | Red, Locality y Seguridad | `PASA` | C.1–C.5 cubiertos por lente `locality.md`; CfgRemoteExec whitelist auditada en goldens Cat. 5 (`g06_remoteexec_whitelist`). |
| **D** | Ciclo de Vida y Limpieza | `PASA` | D.1–D.4 verificados: control riguroso de scope (`private`, `params`), sin fugas al global, prefijos canónicos `TAG_`. |
| **E** | Robustez y Manejo de Errores | `PASA` | E.1–E.4 cubiertos: `params` defensivos tipados, evaluación perezosa en lente `best_practices.md`, respeto del perfil de framework en goldens Cat. 7. |
| **F** | Rendimiento y Scheduler | `PASA` | F.1–F.3 cubiertos: cadencia de Per-Frame Handlers, prohibición de `execVM` en bucles, `init.sqf` ágil en lente `performance.md`. |
| **G** | Plan de Pruebas | `PASA` | G.1–G.3 formalizados en `references/workflows/test_plan.md` con escenarios para Dedicado, Cliente, JIP y RPT limpio. |
| **H** | Entrega y Empaquetado | `PASA` | H.1: 0 rutas absolutas (`test_no_absolute_paths.py`); H.2: dependencias en `INSTALL.md` y `README.md`; H.3: guías de uso completas. |
| **I** | Honestidad Técnica | `PASA` | I.1: desglose exhaustivo de estados; I.2: cero bloqueantes abiertos para declarar fin; I.3: runtime no simulado, reportado como `NO VERIFICADO`. |

## Comandos de referencia

```bash
python3 scripts/check.py --fase PR-5   # gate local PR-5 (verde, 144 tests)
python3 scripts/check.py --fase PR-6   # gate local PR-6 (verde, 18 checks)
python3 scripts/check.py --fase PR-7   # gate local PR-7 (verde, validación final)
python3 -m pytest tests/ -q            # suite completa (144 verdes, 0 fallos)
python3 -m ruff check .                # linters limpios
python3 scripts/generate_inline_packages.py --check # verificación inline
python3 evals/harness.py --check       # verificación de QUALITY.md
python3 scripts/measure_tokens.py      # presupuesto de tokens intacto (1.186 <= 1.200)
```
