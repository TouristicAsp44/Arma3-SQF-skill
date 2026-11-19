# INSTRUCCIÓN PARA ANTIGRAVITY — PR-7: Planificación por fases para publicar `arma3-sqf-skill` en GitHub

> **Este documento es la instrucción de planificación.** Define las fases, su orden, las tareas de
> cada una y los criterios de aceptación. **No** es un informe de resultados: no incluyas aquí
> salidas de ejecución, solo el plan y sus criterios.

**Destinatario:** Antigravity (ejecutor de las fases)
**Supervisor:** Mavis (auditoría independiente; revisa cada fase y emite la siguiente)
**Directorio de trabajo:** `C:\Users\Touri\Documents\EDEN EDITOR\Skills Antigravity\arma3-sqf-skill`
**Repositorio destino:** `https://github.com/TouristicAsp44/Arma3-SQF-skill` (público, nuevo)
**Fecha de emisión:** 2026-11-19
**Idioma de todos los entregables:** español

---

## 0. Objetivo final

Publicar `arma3-sqf-skill` como repositorio público propio en
`https://github.com/TouristicAsp44/Arma3-SQF-skill`, en dos versiones:

| Versión | Momento | Contenido |
| :--- | :--- | :--- |
| `1.0.0-rc.1` | Final de la **Fase 1** | Estado actual verificado del proyecto, con las URLs del repositorio ya corregidas. |
| `1.0.0` | Final de la **Fase 5** | Estado final: sin residuo documental, README revisado y skill libre de rutas del equipo local. |

**No se publica en ningún marketplace de plugins** (decisión del usuario): se entrega el
repositorio con `SKILL.md`, integraciones por host y `plugin.json`.

---

## 1. Estado real verificado por Mavis (2026-11-19) — no repetir, no suponer

Estos hechos están **medidos**, no supuestos. Si al ejecutar una fase observas algo distinto,
**repórtalo como discrepancia**: no lo ajustes silenciosamente.

- **Tests:** `python -m pytest tests/ -q` → **144 passed**.
- **Gates:** `python scripts/check.py --fase PR-5 | PR-6 | PR-7` → **TODO EN VERDE** en las tres.
- **Lint:** `python -m ruff check .` → *All checks passed*.
- **Documento generado sincronizado:** `python evals/harness.py --check` → *OK*.
- **Paquetes inline:** `python scripts/generate_inline_packages.py --check` → *OK*.
- **Presupuesto de tokens respetado:** frontmatter 184/250 · Capa 0 1186/1200 · lente más larga
  547 (`claims.md`) · turno máx 1733/2500. **Capa 0 tiene 14 tokens de margen: no lo toques.**
- **Métricas publicadas (`docs/QUALITY.md`, generado por el arnés):**
  - Bloque 1 (señalizado, 14 goldens): M1 100 % · **M2 83,3 % (mín 75,0 %) — NO PASA OBJETIVO
    (≥ 90 %), 4 omisiones** · **M3 38/39 (97,4 %) — NO PASA OBJETIVO, 1 omisión**.
  - Bloque 2 (ciego, 6 goldens): **M2 100 %** · **M3 21/21 (100 %), 0 falsos PASA**.
  - 120 trazas reales, 0 descartadas por hash de contexto (Regla R3).
- **Git:** el repositorio local **ya está inicializado** (`git init` hecho por Mavis):
  - commit `8949351` — *"Release 1.0.0: skill universal arma3-sqf-skill"* (180 ficheros).
  - tag local `v1.0.0` **existe y no está publicado en ningún remoto**. Hay que renombrarlo a
    `v1.0.0-rc.1` en la Fase 1 (reescribir un tag local no publicado no tiene riesgo).
  - **No hay remoto configurado.** No hay credenciales de GitHub en el gestor de credenciales de
    git (`git credential fill` sin resultado) y **`gh` CLI no está instalado**.
  - Identidad local ya configurada: `TouristicAsp44` / `TouristicAsp44@users.noreply.github.com`.
- **Inventario del directorio:** raíz con 6 ficheros `PLAN-IMPROVEMENTS*.md` (~116 KB) y
  `docs/` con 10 `INSTRUCCION-ANTIGRAVITY-*.md` (~157 KB) + `docs/ESTADO-PR.md` (37 KB).
  `legacy/` (11 ficheros) está congelado y fuera de git. `evals/runs/` (120 trazas, 2,7 MB) está
  fuera de git. `.gitignore` y `MANIFEST.in` ya excluyen ambos.
- **Puntos que contienen rutas del equipo local** (hallados por Mavis): `docs/INSTRUCCION-ANTIGRAVITY-PR6.md`
  (2 rutas `C:/Users/Touri/...`), y las 10 instrucciones `INSTRUCCION-*` + 6 `PLAN-IMPROVEMENTS*`
  (rutas `C:\Users\Touri\Documents\EDEN EDITOR\...`).
- **URLs que apuntan al repositorio antiguo** `TouristicAsp44/Arma3-SQF-review` (el del plugin
  original, que **no se toca**): `pyproject.toml` (3 URLs), `CONTRIBUTING.md` (1),
  `CHANGELOG.md` (1 enlace de release).

---

## 2. Reglas duras (no negociables)

1. **No tocar** `C:\Users\Touri\Documents\EDEN EDITOR\Skills Antigravity\arma3-sqf-review\` (el
   plugin original): es solo lectura. Todo el trabajo ocurre en `arma3-sqf-skill`.
2. **No maquillar métricas.** `evals/goldens/*/expected.json` es contrato: cambiar un valor
   esperado cambia el contrato y **requiere aprobación explícita del usuario**. No se toca.
3. **Honestidad técnica:** lo no ejecutado = `NO VERIFICADO`. Prohibido inventar modelos, métricas,
   procedencias o resultados de ejecución.
4. **R3 — sin enlaces a ficheros ilegibles:** si borras un documento, toda referencia a él
   (incluida la generada por el arnés) debe actualizarse en la misma fase.
5. **R6 — texto normativo fuera del canónico = GENERATED + hash.** `references/invariants.md`,
   `rubrica.md` y `sqf-standards.md` son la fuente canónica única. No dupliques su contenido.
6. **Deps:** `dependencies = []` se mantiene vacío. Solo biblioteca estándar de Python ≥ 3.11.
7. **Sin rutas absolutas** en runtime ni en material distribuible (ver Fase 4).
8. **Borrado en Windows:** prohibido `Remove-Item`. Usa `rm -- "<ruta>" --trash` desde la raíz de
   sesión (mavis-trash). Nada se borra de forma permanente ni fuera del directorio de trabajo.
9. **Idioma:** todos los entregables, mensajes de commit y notas de release en español.
10. **Iteración:** máximo 3 intentos por fase. Si una fase no converge, **documenta el bloqueo con
    su límite exacto** y pasa a la siguiente; no lo maquilles ni lo ocultes.
11. **No publiques sin el Fase 0 resuelta:** la autenticación es responsabilidad de Antigravity y
    del usuario (sesión de GitHub en Antigravity). Si no hay credenciales, **te detienes y lo
    informas**; nunca pidas un token por chat ni inventes credenciales.

---

## 3. Fase 0 — Línea base, autenticación y repositorio remoto

**Objetivo:** confirmar la línea base, dejar el remoto preparado y tener acceso a GitHub.

**Tareas**

- F0.1 Ejecutar la línea base completa y pegar la salida literal en el informe de fase:
  ```powershell
  Set-Location 'C:\Users\Touri\Documents\EDEN EDITOR\Skills Antigravity\arma3-sqf-skill'
  python -m pytest tests/ -q
  python scripts/check.py --fase PR-5
  python scripts/check.py --fase PR-6
  python scripts/check.py --fase PR-7
  python -m ruff check .
  python evals/harness.py --check
  python scripts/generate_inline_packages.py --check
  python scripts/measure_tokens.py
  git log --oneline -1 ; git tag -l ; git status --short
  ```
- F0.2 **Autenticación.** El usuario está iniciando sesión en Antigravity y ha declarado que de la
  autenticación se encarga Antigravity. Procedimiento:
  1. Comprueba si hay autenticación disponible: `gh auth status` (si `gh` no está instalado,
     comprueba si Antigravity expone un canal GitHub autenticado o una credencial ya presente).
  2. Si hay sesión autenticada → úsala.
  3. Si no hay ninguna y no puedes abrir un canal autenticado → **detente**, informa del bloqueo
     exacto y deja las fases 1–5 preparadas pero no ejecutadas en el paso de publicación. No
     pidas el token en el chat ni lo escribas en ficheros del proyecto.
- F0.3 **Crear el repositorio remoto** (solo cuando F0.2 tenga sesión):
  ```powershell
  gh repo create TouristicAsp44/Arma3-SQF-skill --public --description "Skill universal de análisis y revisión SQF para Arma 3 (Claude, ChatGPT, Cursor, Codex, Gemini, Antigravity)" --disable-issues=false
  git remote add origin https://github.com/TouristicAsp44/Arma3-SQF-skill.git
  ```
  Si `gh` no está disponible pero hay otro canal autenticado, crea el repositorio por ese canal
  con **las mismas características**: nombre `Arma3-SQF-skill`, **público**, descripción
  equivalente, sin wiki, sin issues… salvo que se decida lo contrario en el informe.
- F0.4 Verificar que el remoto quedó accesible y **vacío** (sin `main`):
  `git ls-remote origin`.

**Criterios de aceptación**
- [ ] Línea base completa en verde y reproducida en el informe.
- [ ] Sesión de GitHub autenticada **o** bloqueo documentado con el motivo exacto.
- [ ] Remoto `origin` apuntando a `TouristicAsp44/Arma3-SQF-skill` (público) y vacío.

**Entregable:** informe de fase con la salida literal de los comandos, el resultado de F0.2 y la
URL del remoto.

---

## 4. Fase 1 — Publicación de `1.0.0-rc.1`

**Objetivo:** publicar el estado actual verificado, con las URLs del repositorio ya corregidas.

**Tareas**

- F1.1 Corregir **todas** las referencias al repositorio antiguo
  `TouristicAsp44/Arma3-SQF-review` → `TouristicAsp44/Arma3-SQF-skill`:
  - `pyproject.toml` (`Homepage`, `Repository`, `Issues`).
  - `CONTRIBUTING.md` (línea de `git clone`).
  - `CHANGELOG.md` (enlace de release de la versión 1.0.0).
  - Búsqueda de confirmación: `Select-String -Path <ficheros> -Pattern 'Arma3-SQF-review'`.
  - **No cambies** las referencias a `arma3-sqf-review` que son **históricas o técnicas** (la
    línea de linter heredada citada en `docs/QUALITY.md` §4, el nombre del plugin original en la
    tabla de diferencias del README, y la génesis del proyecto). Distinguir *URL del repositorio
    de esta skill* de *plugin original*.
- F1.2 Versión `1.0.0-rc.1` en `pyproject.toml` y `plugin.json` (`"version": "1.0.0-rc.1"`).
- F1.3 Reetiquetar el tag local (nunca publicado, sin riesgo):
  ```powershell
  git tag -d v1.0.0
  git tag -a v1.0.0-rc.1 -m 'arma3-sqf-skill v1.0.0-rc.1'
  ```
- F1.4 Commit y push:
  ```powershell
  git add -A
  git commit -m 'chore(release): URLs del repositorio arma3-sqf-skill y version 1.0.0-rc.1'
  git push -u origin main
  git push origin v1.0.0-rc.1
  ```
- F1.5 Verificar en GitHub: rama `main` presente, tag `v1.0.0-rc.1` visible, README renderizado
  con la tabla de badges correcta.

**Criterios de aceptación**
- [ ] Cero referencias a `TouristicAsp44/Arma3-SQF-review` que apunten a *esta* skill.
- [ ] `main` y el tag `v1.0.0-rc.1` publicados y visibles.
- [ ] `pyproject.toml` y `plugin.json` con versión `1.0.0-rc.1` coherentes entre sí.

---

## 5. Fase 2 — Limpieza y depuración de residuo

**Objetivo:** eliminar del directorio de trabajo el material de proceso que no es necesario para
usar la skill (decisión del usuario: **borrar del directorio de trabajo**).

**Tareas**

- F2.1 **Antes de borrar**, volcar a `CHANGELOG.md` (sección "Estado de la evidencia" y una
  línea por fase PR-2 a PR-7 con su resultado) todo el contenido de trazabilidad que vivía en
  `docs/ESTADO-PR.md`, de modo que **no se pierda el histórico**. Después, borrarlo.
- F2.2 **Borrar exactamente estos 17 ficheros** (lista explícita; no uses comodines, porque
  `docs/INSTRUCCION-ANTIGRAVITY-PR7.md` —este documento— debe sobrevivir):
  - Raíz (6): `PLAN-IMPROVEMENTS.md`, `PLAN-IMPROVEMENTS-v2.md`, `PLAN-IMPROVEMENTS-v3.md`,
    `PLAN-IMPROVEMENTS-v4.md`, `PLAN-IMPROVEMENTS-v5.md`, `PLAN-IMPROVEMENTS-v6.md`.
  - `docs/` (11): `ESTADO-PR.md`, `INSTRUCCION-ANTIGRAVITY-PR2.md`, `INSTRUCCION-ANTIGRAVITY-PR3.md`,
    `INSTRUCCION-ANTIGRAVITY-PR4.md`, `INSTRUCCION-ANTIGRAVITY-PR5.md`,
    `INSTRUCCION-ANTIGRAVITY-PR5BIS.md`, `INSTRUCCION-ANTIGRAVITY-PR5TER.md`,
    `INSTRUCCION-ANTIGRAVITY-PR6.md`, `INSTRUCCION-ANTIGRAVITY-PR6PREP.md`,
    `INSTRUCCION-ANTIGRAVITY-PARIDAD-AGENTES.md`, `INSTRUCCION-ANTIGRAVITY-BLIND-GOLDENS.md`.
  - Procedimiento: `rm -- "<ruta>" --trash` (recuperable). Nada de `Remove-Item`.
- F2.3 **Reparar las referencias rotas** (R3). Obligatorio, porque el arnés genera enlaces:
  - `evals/harness.py` (líneas ~945 y ~988): las dos cadenas que dicen *"está documentada en
    `docs/ESTADO-PR.md`"* y *"Los casos concretos y su análisis están en `docs/ESTADO-PR.md`"* →
    reescribirlas apuntando al documento vigente (por ejemplo `docs/QUALITY.md` §4/§6 o
    `CHANGELOG.md`) **sin cambiar ninguna cifra**.
  - `docs/COMPATIBILIDAD.md` línea ~70: la referencia a `docs/ESTADO-PR.md` (Track C).
  - `integrations/common/skill-layout.md` línea ~59: el árbol de layout que lista
    `ESTADO-PR.md`.
  - `docs/QUALITY.md` es **GENERADO**: no lo edites a mano; se corrige regenerando con
    `python evals/harness.py --write` tras arreglar el harness.
- F2.4 **Tests que referencian los ficheros borrados** (si no los ajustas, la suite se rompe):
  - `tests/test_canonical_uniqueness.py` (excluye por nombre `PLAN-IMPROVEMENTS`).
  - `tests/test_no_stale_references.py` (lista de prefijos `docs/INSTRUCCION-ANTIGRAVITY-`,
    `docs/ESTADO-PR.md`, `PLAN-IMPROVEMENTS`).
  - Ajusta las listas **al conjunto nuevo de ficheros válidos** y amplía la comprobación para que
    detecte enlaces a ficheros inexistentes. **No rebajes cobertura para que pase**: si el test
    pierde alcance, está mal.
- F2.5 **Cachés y artefactos de build** (no versionados, pero ensucian el árbol): `__pycache__`,
  `.pytest_cache`, `.ruff_cache`, `skills/.../__pycache__`, `evals/__pycache__`, `.vscode/` (vacío).
  Verifica antes con `git status --ignored --short` que no hay nada versionado en esas rutas.
- F2.6 **Decidir y documentar** (no borrar sin criterio) el resto del residuo:
  - `legacy/` (11 ficheros de agentes congelados): **se conservan en disco y fuera de git**
    (decisión previa 1.o). Verifica que `.gitignore` y `MANIFEST.in` lo excluyen y que
    `git ls-files legacy/` no devuelve nada.
  - `evals/runs/` (120 trazas): **se conservan en disco y fuera de git** (decisión del usuario:
    el repo publica el agregado `docs/QUALITY.md`). Verifica la exclusión y que
    `MANIFEST.in` mantiene `prune evals/runs`.
  - `fixtures/test_scope.sqf` (17 bytes) y `rules/AGENTS.md` (puntero a la fuente canónica):
    **se conservan**. `rules/AGENTS.md` está referenciado por `agents/sqf-claim-verifier.md`,
    `docs/PARIDAD.md` y `CONTRIBUTING.md`: no lo borres.
  - `assets/logo.png` (1 MB) referenciado por `plugin.json`: **se conserva**. Si decides
    optimizarlo, no rompas la referencia.
- F2.7 **`.gitignore` y `MANIFEST.in`**: actualízalos para que reflejen el estado final (p. ej.
  excluir `PLAN-IMPROVEMENTS*` por si alguien los reintroduce) y añade `include CHANGELOG.md`
  si no está (ya lo está: verificar).

**Criterios de aceptación**
- [ ] Los 17 ficheros borrados; recuperables; **este documento (`INSTRUCCION-ANTIGRAVITY-PR7.md`) intacto**.
- [ ] `grep`/`Select-String` sin resultados de `ESTADO-PR.md`, `PLAN-IMPROVEMENTS`,
  `INSTRUCCION-ANTIGRAVITY-PR2..PR6PREP`, `BLIND-GOLDENS`, `PARIDAD-AGENTES` en ficheros vivos.
- [ ] `python evals/harness.py --write` regenera `docs/QUALITY.md` **sin** referencias a ficheros
  borrados y **con las mismas cifras** que la versión anterior.
- [ ] `pytest` sigue en verde (144 tests o más, nunca menos por pérdida de cobertura).

---

## 6. Fase 3 — README: título, procedencia y tabla de diferencias

**Objetivo:** que el README se presente como el proyecto `arma3-sqf-skill`, explique de dónde
viene y de qué se diferencia técnicamente respecto al plugin original.

**Tareas**

- F3.1 **Título.** El encabezado principal (H1) debe llevar el nombre del proyecto, no una
  descripción genérica. Propuesta a validar: `# Arma 3 SQF Skill — \`arma3-sqf-skill\``
  (o `# arma3-sqf-skill`, si prefieres el nombre de paquete puro). El subtítulo explica en una
  línea qué es.
- F3.2 **Procedencia.** Sección nueva, visible al principio, que aclare:
  - Origen: port del plugin **`arma3-sqf-review`** de Antigravity (repo
    `TouristicAsp44/Arma3-SQF-review`), del mismo autor (`TouristicAsp44`), licencia MIT.
  - Motivo de la separación: la skill es **independiente del plugin**, portable a 6 hosts y sin
    dependencia de Antigravity; el plugin original se mantiene intacto y ambos conviven.
  - Relación entre ambos productos (ver tabla de diferencias).
  - Estado y madurez: versión, fecha, número de goldens, hosts medidos y `NO VERIFICADO` en los
    demás.
  - Qué **no** incluye (dataset `a3ref`, binario de `sqflint`, dependencias de terceros).
- F3.3 **Tabla de diferencias skill vs plugin.** Tabla de dos columnas (`Skill` / `Plugin
  original`) con las dimensiones reales, extraídas de `docs/PARIDAD.md` (fuente de verdad ya
  auditada). Ejes mínimos: propósito y público; entorno de ejecución (6 hosts vs Antigravity);
  orquestación (SKILL.md + lentes + motor determinista vs 11 subagentes-Agentes); motor
  determinista (Cat. 1–2 y su CLI); categorías y rigor del informe; fuente canónica de reglas
  (`references/`); wiki y base de datos; transporte MCP (stdio, propio) vs integración del
  plugin; integraciones por host; evaluación y evidencia (20 goldens, 120 trazas, M1/M2/M3);
  dependencias (`dependencies = []`); instalación; licencia y procedencia. **Cada celda debe ser
  verificable**: si la afirmación no está respaldada por un fichero del repo, se omite o se marca
  como no verificado.
- F3.4 **Badges y metadatos**: actualizar el badge de versión y el de tests al estado real
  (144 tests), añadir el del repo nuevo, y corregir el enlace del logo si procede.
- F3.5 **Enlaces**: todos los enlaces internos del README deben apuntar a ficheros que existen
  tras la Fase 2 (comprueba `README.md`, `INSTALL.md`, `docs/*`, `integrations/*`). Los enlaces
  externos (GitHub, BIKI) se comprueban con `web_fetch`/curl y se anotan los que fallen.
- F3.6 **Secciones a revisar además**: "Quickstart por Host", "Instalación y Requisitos",
  "Estado medido de la evidencia" (las cifras **no se tocan**: 83,3 % / 38-39 / 21-21) y
  "Documentación" (enlaces a `docs/`).

**Criterios de aceptación**
- [ ] H1 con el nombre del proyecto.
- [ ] Sección de procedencia presente y veraz (sin afirmar "misma calidad" que el plugin:
      R5 — solo hay un host medido).
- [ ] Tabla de diferencias presente, con celdas verificables y con la fuente (`docs/PARIDAD.md`)
      indicada.
- [ ] Cero enlaces rotos en el README.
- [ ] Cifras de calidad idénticas a las de `docs/QUALITY.md`.

---

## 7. Fase 4 — Localidad: la skill no debe apuntar a los directorios del equipo

**Objetivo:** ninguna ruta del equipo local aparece en runtime, documentación ni artefactos
distribuibles. Todo lo específico del entorno local se resuelve por variables de entorno o
rutas relativas al repositorio.

**Tareas**

- F4.1 **Inventario de rutas locales.** Barrido completo y con salida literal:
  ```powershell
  Select-String -Path (Get-ChildItem -Recurse -File -Include *.md,*.py,*.json,*.yml,*.toml -Exclude *.pyc).FullName `
                 -Pattern 'C:\\Users\\','C:/Users/','/Users/','EDEN EDITOR','a3ref','\.a3ref'
  ```
  Clasifica cada hallazgo en una de estas categorías:
  1. **Ruta del equipo local → corregir.** Ejemplos confirmados:
     `docs/INSTRUCCION-ANTIGRAVITY-PR6.md` (líneas 60–61: `cwd` y `SQF_WIKI_DB_PATH` con
     `C:/Users/Touri/...`). Tras la Fase 2 ese fichero ya no existe, pero el patrón puede
     repetirse en `docs/MCP.md`, `docs/WIKI-DB.md`, `INSTALL.md`, `integrations/**` y
     `skills/arma3-sqf-skill/scripts/**`.
  2. **Referencia al dataset público `a3ref` → es legítima, pero debe ser neutra.** El dataset
     es un proyecto público (`github.com/a3ref/data`); el uso de `~/.a3ref/data` como ruta por
     defecto en `HOME` es correcto y portable. **No lo elimines**: solo verifica que ninguna
     variante apunte a una ruta específica de esta máquina y que la documentación explique que
     es configurable por `SQF_WIKI_DATA_PATH` / `SQF_WIKI_DB_PATH`.
  3. **Autor/proyecto → legítima.** `TouristicAsp44`, `Arma3-SQF-review` (plugin original),
     `TouristicAsp44@users.noreply.github.com` en la identidad de git.
- F4.2 **Sustituciones canónicas** en runtime y material distribuible:
  - Rutas del wiki: solo `SQF_WIKI_DATA_PATH` / `SQF_WIKI_DB_PATH` / `~/.a3ref/...` o rutas
    relativas al repositorio. Ningún `C:\...` ni `/Users/<nombre>/...`.
  - Rutas de proyecto de ejemplo: `<TU_PROYECTO>`, `RUTA_A_TU_PROYECTO` o `$(pwd)`.
  - Ficheros de ejemplo (`.cursorrules`, `CLAUDE.md`, `AGENTS.md`, snippet JSON de Claude
    Desktop): placeholders, nunca rutas reales.
  - `skills/arma3-sqf-skill/scripts/mcp_server.py`, `sqf_orchestrator.py`,
    `sqf_wiki_reader.py`, `wiki_db_builder.py`, `sync_wiki_cache.py`: **cero** rutas absolutas
    y **cero** literales `C:\Users`; el código debe resolver todo con `Path.home()`,
    `expanduser()`, variables de entorno o rutas relativas al propio paquete.
- F4.3 **Test de localidad.** Ya existe `tests/test_no_absolute_paths.py`. **Amplíalo** para que
  cubra: (a) literales `C:\Users\`, `C:/Users/`, `/Users/`, `/home/<usuario>` y la cadena
  `EDEN EDITOR` en todo el material versionado; (b) rutas absolutas en el paquete distribuible;
  (c) `Path.home()` como única fuente de rutas de usuario. El test debe ser **real**: usa
  `git ls-files` (o la lista de ficheros versionados) como universo de comprobación, no un
  subconjunto convenientemente pequeño.
- F4.4 **Snippet de Claude Desktop** (`integrations/claude/claude_desktop_config_snippet.json`):
  verificar que no hay `cwd` absoluto ni rutas reales; los valores `~/.a3ref/...` son correctos.
- F4.5 **Documentos de wiki** (`docs/WIKI-DB.md`, `docs/MCP.md`): los ejemplos de comando deben
  usar `~`/variables de entorno y declarar explícitamente que son opcionales; si la réplica no
  está, el estado es `SIN_REPLICA` / `NO VERIFICADO`.

**Criterios de aceptación**
- [ ] Cero apariciones de `C:\Users\`, `C:/Users/`, `/Users/`, `EDEN EDITOR` en ficheros
      versionados (verificado con el test ampliado y con salida literal del barrido).
- [ ] El test de localidad nuevo está en verde y **no** es tautológico (debe fallar si se
      reintroduce una ruta absoluta: verifícalo introduciendo una y revirtiéndola).
- [ ] El runtime sigue funcionando: `pytest` en verde y `harness --check` OK.

---

## 8. Fase 5 — Verificación integral y publicación de `1.0.0`

**Objetivo:** con el árbol ya limpio y la skill portable, publicar la versión estable.

**Tareas**

- F5.1 Ejecutar la **batería completa** (los 8 comandos) y pegar la salida literal:
  ```powershell
  python -m pytest tests/ -q
  python scripts/check.py --fase PR-5
  python scripts/check.py --fase PR-6
  python scripts/check.py --fase PR-7
  python -m ruff check .
  python evals/harness.py --check
  python scripts/generate_inline_packages.py --check
  python scripts/measure_tokens.py
  ```
  Si `harness --check` falla por el texto regenerado en la Fase 2 → regenera con
  `python evals/harness.py --write` y vuelve a comprobar.
- F5.2 **Verificación del paquete distribuible**: construir el sdist y comprobar su contenido
  (no debe incluir `legacy/`, `evals/runs/`, `.pytest_cache`, `__pycache__`, bases de datos ni
  ficheros de residuo):
  ```powershell
  python -m build --sdist        # si `build` no está instalado: pip install build
  ```
  y listar el contenido del `.tar.gz` generado en el informe.
- F5.3 **Revisión de enlaces** de todo el repo: cada enlace Markdown relativo debe resolver a un
  fichero existente (script de barrido o test). Sin excepciones.
- F5.4 Versión final `1.0.0` en `pyproject.toml` y `plugin.json`; actualizar `CHANGELOG.md`
  (sección `[1.0.0]` con fecha, resumen y el estado de la evidencia) y el badge del README.
- F5.5 Commit, tag y push:
  ```powershell
  git add -A
  git commit -m 'release: 1.0.0 — limpieza de residuo, README revisado y skill libre de rutas locales'
  git tag -a v1.0.0 -m 'arma3-sqf-skill v1.0.0'
  git push origin main
  git push origin v1.0.0
  ```
- F5.6 **Notas de release en GitHub** (texto en español, sin inventar):
  ```powershell
  gh release create v1.0.0 --title 'arma3-sqf-skill v1.0.0' --notes-file <fichero-con-las-notas>
  ```
  Las notas deben incluir: qué es, procedencia, evidencia medida **con las cifras reales**
  (M1 100 %; Bloque 1 M2 83,3 % / M3 38-39, ambos `NO PASA OBJETIVO`; Bloque 2 M2 100 % / M3 21-21;
  120 trazas; 6 hosts en `NO VERIFICADO`), instalación por host y la advertencia de que la
  variante HTTP del MCP no está implementada.
- F5.7 Verificación final en el repo público: `main` y `v1.0.0` visibles, README renderizado,
  release publicada, enlace a `https://github.com/TouristicAsp44/Arma3-SQF-skill` correcto.

**Criterios de aceptación**
- [ ] Batería completa en verde con salida literal en el informe.
- [ ] sdist sin residuo ni datos del usuario.
- [ ] `v1.0.0` publicado con release y notas honestas.
- [ ] `docs/QUALITY.md` idéntico en cifras al de la Fase 1 (sin deriva de métricas).

---

## 9. Informe final (obligatorio)

Al terminar, entrega un informe **en español** con:

1. **Resumen por fase**: F0–F5, qué se hizo, qué quedó sin hacer y por qué.
2. **Salida literal** de los 8 comandos de verificación en la Fase 5.
3. **Tabla de ficheros borrados** (Fase 2) con su ruta y su propósito original.
4. **URLs finales**: repositorio, tag `v1.0.0-rc.1`, tag `v1.0.0`, enlace de la release.
5. **Cifras publicadas** (copiadas de `docs/QUALITY.md`, sin reinterpretar).
6. **Discrepancias** encontradas respecto del §1 (estado verificado por Mavis): qué no coincidió y
   qué se hizo. **Ninguna discrepancia se corrige cambiando un número de la sección 1.**
7. **Limitaciones abiertas**: los 6 hosts en `NO VERIFICADO`, M2/M3 del Bloque 1 por debajo de
   objetivo, MCP-HTTP no implementado, trazas no publicadas (agregado sí).

---

## 10. Lo que NO se hace en esta instrucción

- **No** se modifica `expected.json` de ningún golden.
- **No** se reescribe `docs/QUALITY.md` a mano (es GENERADO).
- **No** se tocan `references/invariants.md`, `rubrica.md` ni `sqf-standards.md` (fuente canónica
  única, R2/R6) ni el presupuesto de tokens de la Capa 0 (14 tokens de margen).
- **No** se prepara ni se publica en ningún marketplace de plugins.
- **No** se publica en `TouristicAsp44/Arma3-SQF-review` (ese repo es el del plugin original).
- **No** se borra nada del repositorio original `arma3-sqf-review`.
