# Changelog — `arma3-sqf-skill`

Todas las novedades relevantes de esta skill se documentan aquí.
El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y el versionado
semántico ([SemVer](https://semver.org/lang/es/)).

## [1.0.0] — 2026-11-19

Primera versión estable de la **skill universal** derivada del plugin `arma3-sqf-review`
de Antigravity. Publicable en Claude Code/Desktop, Cursor, OpenAI Codex, ChatGPT Custom GPTs,
Gemini y Antigravity, con `dependencies = []` (solo biblioteca estándar de Python >= 3.11).

### Añadido

- **Núcleo portable** (`skills/arma3-sqf-skill/`): `SKILL.md` con 4 capas de presupuesto de
  tokens (frontmatter 184/250, Capa 0 1186/1200), motor determinista `sqf_orchestrator.py`
  (Cat. 1–2) y referencias canónicas en `references/` (`invariants.md`, `rubrica.md`,
  `sqf-standards.md`).
- **Servidor MCP por stdio** (`scripts/mcp_server.py`, JSON-RPC 2.0, stdlib puro): herramientas
  `sqf_analyze`, `sqf_wiki_query` y `sqf_mode`. Flag `--serve-mcp` en el CLI.
- **Índice SQLite de la wiki SQF** (`scripts/build_wiki_db.py`): aceleración opcional sobre la
  ruta JSON original, que permanece intacta; FTS5 degrada a `LIKE` si no está disponible.
- **Paquetes inline P1–P4** (`scripts/generate_inline_packages.py`): copias generadas de la
  fuente canónica para hosts sin acceso a ficheros (ChatGPT, Gemini), protegidas por
  `scripts/generated.lock.json`.
- **Integraciones por host**: `integrations/{claude,cursor,openai,chatgpt,gemini}/` + Claude Code
  y Claude Desktop.
- **Harnes de evaluación** (`evals/harness.py`) con dos bloques metodológicamente independientes:
  dataset **señalizado** (`g01`–`g13`, 14 goldens) y dataset **ciego / no señalizado**
  (`b01`–`b06`, 6 goldens), verificación `sha256` del contexto cargado (Regla R3),
  denominadores separados y sección de *bloqueantes no declarados*.
- **Métricas R4 (MÉTRICA + MÉTODO + ESTADO)**: M1 (script, 100 %), M2 (modelo en modo archivo,
  objetivo >= 90 %), M3 (modelo en modo pegado, objetivo 100 % y 0 falsos PASA).
- **Documentación**: `docs/QUALITY.md` (generado), `docs/PARIDAD.md`,
  `docs/COMPATIBILIDAD.md`, `docs/MCP.md`, `docs/PRIVACIDAD.md`, `docs/SMOKE-RESULTS.md`.
- **Suite de 144 tests** y gate por fases `scripts/check.py --fase PR-5 | PR-6 | PR-7`.

### Corregido

- **Ground truth corregido** (`g03`, `g08`, `b06`): se declararon los defectos secundarios que el
  `expected.json` original omitía. `g01` se dejó intacto por adjudicación (declarar un duplicado
  del mismo defecto habría recompensado la sobre-reportación).
- **Clasificador léxico del arnés**: `"ace"` dentro de "interf**ace**s" y `"ui"` dentro de
  "arq**ui**tectura" producían categorías erróneas (M2 de 88,9 % a 100 % en el momento de la
  corrección). Sustituido por `classify_discipline()` y `disciplines_compatible()`.
- **Contador de falsos positivos**: ya no penaliza bloqueantes de categorías fuera del alcance
  del modo; lo no declarado se publica aparte como *adjudicación pendiente*.
- **Servidor MCP**: UTF-8 forzado en `stdio` (`force_utf8_stdio()`) y `expanduser()` en
  `resolve_wiki_db()` / `resolve_wiki_root()` (antes `~/.a3ref/...` se ignoraba en silencio).
- **Referencias obsoletas** en material distribuible: `agents/sqf-claim-verifier.md`,
  `references/checklist-entrega.md`, `scripts/sync_wiki_cache.py`, `CONTRIBUTING.md`. Blindado con
  `tests/test_no_stale_references.py`.

### Estado de la evidencia (publicado, no maquillado)

- Bloque 1 (señalizado): M1 100 % · **M2 83,3 % (mín 75,0 %) — NO PASA OBJETIVO (>= 90 %), 4
  omisiones** · **M3 38/39 (97,4 %) — NO PASA OBJETIVO, 1 omisión**.
- Bloque 2 (ciego): **M2 100 %** · **M3 21/21 (100 %), 0 falsos PASA**.
- 120 trazas reproducibles, 0 descartadas por hash de contexto (R3).
- 6 hosts sin ejecución real permanecen en `NO VERIFICADO`: sin trazas no se afirma "misma
  calidad" que el plugin original (Regla R5).
- **Ground truth honesto**: se declararon defectos secundarios reales en `g03` (L4) y `g08` (L11),
  y se ajustaron líneas en `b06`. Esto evidenció que el modelo detecta el 100 % del defecto principal
  en código ciego, pero su exhaustividad en defectos secundarios es parcial (caída de M2 a 83,3 %).
- **Arnés de evaluación**: clasificación de disciplinas por raíces de token NFKD y regla estricta de
  modo pegado para configuraciones ausentes (honestidad técnica ante `b05_remoteexec`).

### Trazabilidad y resultados por fase (histórico migrado de `ESTADO-PR.md`)

- **PR-1 (Saneamiento del repositorio):** Renombrado canónico a `arma3-sqf-skill`, anclas `CANON:*` en `references/invariants.md`, esquema de informe v1, test de rutas absolutas y CI en Python 3.11/3.12/3.13.
- **PR-2 (Núcleo portable):** Frontmatter bilingüe (184/250 tokens), Capa 0 de `SKILL.md` (1.186/1.200 tokens), 6 lentes con delimitadores `AUTHORED`/`CANON-EXTRACT`, 5 workflows y unicidad N3 (`test_canonical_uniqueness.py`). Gate PR-2 en verde.
- **PR-3 (Base de conocimiento SQLite):** Constructor determinista `wiki_db_builder.py` con FTS5 y degradación a `LIKE`. Lookup 130x más rápido y `get_topic` 523x más rápido sobre réplica completa de 35,4 MB. Preservación estricta de procedencia (`revid`, `dataset_sha`). Gate PR-3 en verde.
- **PR-4 (Matriz de compatibilidad y adaptadores):** Adaptadores para Claude, Cursor, OpenAI/Codex, ChatGPT y Gemini. Paquetes inline P1–P4 deterministas (<= 8.000 chars). Smoke tests S1–S3 con 0 falsos PASA. Gate PR-4 en verde.
- **PR-5 y PR-5-bis (Evals formales y arnés de evaluación):** 14 goldens señalizados (`g01`–`g13`), 84 trazas reproducibles (14 x 2 x 3) con hash de contexto SHA-256 (0 descartadas). Corrección de falsos fallos del arnés por subcadena en clasificación de disciplinas. Gate PR-5 en verde.
- **Track C (Goldens ciegos y corrección de ground truth):** Creación de 6 goldens no señalizados (`b01`–`b06`) y 36 trazas (6 x 2 x 3). Corrección honesta del ground truth (`g03`, `g08`, `b06`) para penalizar omisiones de defectos secundarios: M2 Bloque 1 ajustado a 83,3 % (mín 75,0 %, 4 omisiones) y M3 a 38/39 (97,4 %, 1 omisión); Bloque 2 M2 al 100 % y M3 21/21 (100 %). Clasificador de bloqueantes fuera de alcance no cuenta como falsos positivos.
- **PR-6 (Servidor MCP stdio):** Servidor JSON-RPC 2.0 en stdlib puro (`scripts/mcp_server.py`) con `sqf_analyze`, `sqf_wiki_query` y `sqf_mode`. Flag `--serve-mcp` en el CLI. UTF-8 estricto forzado en `stdio` para Windows y expansión de `~` (`expanduser`). Gate PR-6 en verde (18 checks).
- **PR-7 (Paridad de agentes y publicación):** Auditoría ejecutable de los 11 agentes del plugin original en `docs/PARIDAD.md` y `tests/test_agent_port_parity.py`. Conservación de `agents/` para Antigravity y exclusión de `legacy/` fuera de git. 144 tests en verde en suites PR-5/PR-6/PR-7.

### Notas

- La variante HTTP del servidor MCP (FastAPI/uvicorn) **no está implementada**: expondría código
  SQF del usuario a la red local. El transporte publicado es exclusivamente `stdio`.
- `evals/runs/` y `legacy/` no se versionan ni se empaquetan (pueden contener código del usuario).
  La evidencia publicada es el agregado de `docs/QUALITY.md`.
- Licencia MIT.

[1.0.0]: https://github.com/TouristicAsp44/Arma3-SQF-skill/releases/tag/v1.0.0
[1.0.0-rc.1]: https://github.com/TouristicAsp44/Arma3-SQF-skill/releases/tag/v1.0.0-rc.1
