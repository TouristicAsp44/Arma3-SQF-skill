<!-- GENERATED FROM: evals/harness.py | DO NOT EDIT -->
<!-- SOURCE-HASH: 0a2a0a83ed3b805d7061f851c6501e7ab3d168957846c3c0ac7a5b3af25502a2 -->

# Informe Formal de Calidad y Métricas de Evaluación — `arma3-sqf-skill`

Este documento consolida la evaluación formal de precisión, robustez y cobertura de la skill portable `arma3-sqf-skill` a través de sus arneses deterministas y ejecuciones en hosts.

## 1. Definición y Denominadores de Métricas (R4, R5)

- **M1 (Motor Determinista / Script)**: Exactitud de detección en categorías normativas Cat. 1–2 sobre el dataset de goldens deterministas mediante `sqf_orchestrator.py --lint`. **Objetivo: 100 %**.
- **M2 (Modelo en Modo Archivo)**: Detección de bloqueantes en categorías Cat. 3–7 con acceso al sistema de archivos del repositorio ($N=3$, reportando media y mínimo). **Objetivo: $\ge 90\%$**.
- **M3 (Modelo en Modo Pegado)**: Proporción de $(\text{DETECTADO} + \text{NO\_VERIFICADO justificado}) / \text{esperables en pegado}$ bajo el paquete inline P1–P4. **Objetivo: 100 %, 0 falsos PASA**.

---

## 2. Tablas Consolidadas de Calidad por Dataset y Host

### 2.1 Bloque 1 — Dataset Señalizado (`g01`–`g13`, N=14)

*Mide la conformidad del informe (categoría, severidad, formato v1 y disciplina) y la ausencia de falsos positivos en código con contexto anunciado en comentarios.*

| Host | Modelo | Versión | N | Cobertura | M1 (Script) | M2 (Modo Archivo) | M3 (Modo Pegado) | Falsos PASA | Omisiones | Conclusión |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Local (Deterministic Engine)** | Python `sqf_orchestrator.py` | 1.0 | 1 | 3/3 (Cat. 1–2) | **100.0 %** | N/A (solo script) | N/A (solo script) | 0 | 0 | **PASA** (Cat. 1 determinista 100 %, 0 falsos positivos en snippets limpios) |
| **Antigravity (Modo Archivo)** | gemini-3.8-flash-high | 1.0 | 3 | 14/14 | N/A | 83.3 % (mín 75.0 %) | N/A | 0 | 4 | **EVALUADO / NO PASA OBJETIVO (83.3 % < 90.0 %)** (Calculado sobre 42 trazas en modo archivo; cobertura 14/14 goldens) |
| **Antigravity (Modo Pegado)** | gemini-3.8-flash-high | 1.0 | 3 | 14/14 | N/A | N/A | 38/39 (0 FALSO_PASA) | 0 | 1 | **EVALUADO / NO PASA OBJETIVO (97.4 % < 100.0 %)** (Calculado sobre 42 trazas en modo pegado; cobertura 14/14 goldens) |
| **Claude Code** | N/A (sin ejecución) | N/A | 0 | 0/14 | N/A | NO VERIFICADO | N/A | 0 | 0 | **NO_VERIFICADO** (Sin trazas válidas en modo 'archivo' para host 'claude-code' en este entorno (Regla R1)) |
| **Claude Desktop** | N/A (sin ejecución) | N/A | 0 | 0/14 | N/A | N/A | NO VERIFICADO | 0 | 0 | **NO_VERIFICADO** (Sin trazas válidas en modo 'pegado' para host 'claude-desktop' en este entorno (Regla R1)) |
| **Cursor** | N/A (sin ejecución) | N/A | 0 | 0/14 | N/A | NO VERIFICADO | N/A | 0 | 0 | **NO_VERIFICADO** (Sin trazas válidas en modo 'archivo' para host 'cursor' en este entorno (Regla R1)) |
| **OpenAI / Codex** | N/A (sin ejecución) | N/A | 0 | 0/14 | N/A | NO VERIFICADO | N/A | 0 | 0 | **NO_VERIFICADO** (Sin trazas válidas en modo 'archivo' para host 'openai-codex' en este entorno (Regla R1)) |
| **ChatGPT Custom GPT** | N/A (sin ejecución) | N/A | 0 | 0/14 | N/A | N/A | NO VERIFICADO | 0 | 0 | **NO_VERIFICADO** (Sin trazas válidas en modo 'pegado' para host 'chatgpt' en este entorno (Regla R1)) |
| **Google Gemini** | N/A (sin ejecución) | N/A | 0 | 0/14 | N/A | N/A | NO VERIFICADO | 0 | 0 | **NO_VERIFICADO** (Sin trazas válidas en modo 'pegado' para host 'gemini' en este entorno (Regla R1)) |

---

### 2.2 Bloque 2 — Dataset NO Señalizado (`b01`–`b06`, N=6)

*Mide la detección a ciega de defectos sin comentarios reveladores y la honestidad técnica (`NO_VERIFICADO`) en modo pegado ante la ausencia de `description.ext` o perfil de proyecto.*

| Host | Modelo | Versión | N | Cobertura | M1 (Script) | M2 (Modo Archivo) | M3 (Modo Pegado) | Falsos PASA | Omisiones | Conclusión |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Antigravity (Modo Archivo)** | gemini-3.8-flash-high | 1.0 | 3 | 6/6 | N/A | 100.0 % | N/A | 0 | 0 | **EVALUADO** (Calculado sobre 18 trazas en modo archivo; cobertura 6/6 goldens) |
| **Antigravity (Modo Pegado)** | gemini-3.8-flash-high | 1.0 | 3 | 6/6 | N/A | N/A | 21/21 (0 FALSO_PASA) | 0 | 0 | **EVALUADO** (Calculado sobre 18 trazas en modo pegado; cobertura 6/6 goldens) |
| **Claude Code** | N/A (sin ejecución) | N/A | 0 | 0/6 | N/A | NO VERIFICADO | N/A | 0 | 0 | **NO_VERIFICADO** (Sin trazas válidas en modo 'archivo' para host 'claude-code' en este entorno (Regla R1)) |
| **Claude Desktop** | N/A (sin ejecución) | N/A | 0 | 0/6 | N/A | N/A | NO VERIFICADO | 0 | 0 | **NO_VERIFICADO** (Sin trazas válidas en modo 'pegado' para host 'claude-desktop' en este entorno (Regla R1)) |
| **Cursor** | N/A (sin ejecución) | N/A | 0 | 0/6 | N/A | NO VERIFICADO | N/A | 0 | 0 | **NO_VERIFICADO** (Sin trazas válidas en modo 'archivo' para host 'cursor' en este entorno (Regla R1)) |
| **OpenAI / Codex** | N/A (sin ejecución) | N/A | 0 | 0/6 | N/A | NO VERIFICADO | N/A | 0 | 0 | **NO_VERIFICADO** (Sin trazas válidas en modo 'archivo' para host 'openai-codex' en este entorno (Regla R1)) |
| **ChatGPT Custom GPT** | N/A (sin ejecución) | N/A | 0 | 0/6 | N/A | N/A | NO VERIFICADO | 0 | 0 | **NO_VERIFICADO** (Sin trazas válidas en modo 'pegado' para host 'chatgpt' en este entorno (Regla R1)) |
| **Google Gemini** | N/A (sin ejecución) | N/A | 0 | 0/6 | N/A | N/A | NO VERIFICADO | 0 | 0 | **NO_VERIFICADO** (Sin trazas válidas en modo 'pegado' para host 'gemini' en este entorno (Regla R1)) |

---

## 3. Estado de Ejecución y Honestidad Técnica (Regla R1)

En este entorno de validación local:
1. **M1 queda formalmente medido y verificado al 100 %** mediante la suite determinista sobre `evals/goldens/`.
2. Para hosts con ejecuciones reales, las métricas M2 y M3 se calculan exclusivamente desde trazas reproducibles en `evals/runs/`.
3. Cualquier host sin trazas queda registrado como `NO VERIFICADO` con motivo explícito y sin atribuir modelos ficticios, cumpliendo rigurosamente con el **Principio de Honestidad Técnica** (`references/invariants.md`).
4. Para ejecutar la suite de goldens en hosts adicionales y generar trazas, consulta el protocolo en [`evals/GOLDENS-PROTOCOL.md`](../evals/GOLDENS-PROTOCOL.md).

---

## 4. Cobertura, Límites y Trazabilidad (R3, R4)

La columna **Cobertura** indica cuántos goldens de cada bloque se evaluaron por host y modo (Bloque 1: 14 goldens; Bloque 2: 6 goldens). Una cobertura inferior al total del bloque se marca como `COBERTURA PARCIAL` en la conclusión de la fila: la métrica no es extrapolable a los goldens no ejecutados.

Una métrica que no alcanza su objetivo se marca como `NO PASA OBJETIVO` con el valor medido y el umbral público (M2 ≥ 90 %, M3 = 100 %).

Trazabilidad del contexto (R3): cada traza declara el `sha256` de los ficheros que cargó. El harness lo recalcula contra los ficheros actuales del repo (con saltos de línea normalizados a LF) y **descarta la traza si el hash no coincide**, por no ser reproducible. En esta ejecución: 0 traza(s) descartada(s) por contexto no reproducible o ausente.

**Evidencia de linter y trazabilidad histórica (Parte C.3):** 8 trazas del dataset histórico señalizado contienen en su respuesta cruda menciones a rutas del plugin original (`arma3-sqf-review`). Esta limitación está documentada en `CHANGELOG.md` (y en esta misma sección); las métricas semánticas M2/M3 no dependen de la salida del linter determinista, y las 36 trazas del dataset no señalizado están 100 % libres de rutas heredadas.

**Alcance de la evidencia:** las métricas solo son publicables como afirmación de calidad para los hosts efectivamente medidos y con la cobertura indicada. Los hosts sin trazas permanecen en `NO VERIFICADO` y no admiten afirmación de equivalencia.

---

## 5. Limitación Metodológica y Separación de Datasets (lectura obligatoria de M2 y M3)

El dataset de evaluación consta de 20 goldens divididos metodológicamente en dos bloques:

- **Bloque 1: Dataset Señalizado (14 goldens, `g01`–`g13`)**: 13 de 14 goldens incluyen en su propio `code.sqf` un comentario que describe el defecto (p. ej. `// waitUntil sin timeout`, `// Variable local sin private`).
  - **Qué mide**: la **conformidad del informe** (categoría, severidad, formato v1 y disciplina) y la **ausencia de falsos positivos** sobre código correcto (g09–g11). Mide la fiabilidad de la tubería de reporte cuando el contexto es conocido.
  - **Qué NO mide**: no mide la detección a ciega de defectos sin aviso explícito.

- **Bloque 2: Dataset NO Señalizado (6 goldens, `b01`–`b06`)**: 0 de 6 goldens contienen comentarios reveladores (0 % de señalización; blindaje verificado por test automatizado).
  - **Qué mide**: la **detección a ciega real** de defectos críticos y la **honestidad técnica** ante la ausencia de archivos de configuración (`description.ext`) en modo pegado (reportando `NO_VERIFICADO` en lugar de emitir un falso `BLOQUEANTE`).
  - **Regla estricta de modo pegado**: si un defecto requiere `description.ext` para ser comprobado (como `b05_remoteexec`) y el modelo afirma `[BLOQUEANTE]`, el arnés lo penaliza como `FALSO_PASA`. Si reporta `[NO_VERIFICADO]`, cuenta como acierto de honestidad.

Esta separación metodológica garantiza que ninguna afirmación de calidad pública extrapole la conformidad del formato a la detección de defectos no señalizados sin respaldo empírico directo.

---

## 6. Bloqueantes No Declarados en el Ground Truth (adjudicación pendiente)

El arnés empareja cada bloqueante emitido con los hallazgos declarados en `expected.json`. Los que **no** corresponden a ningún hallazgo declarado (en ninguna categoría, ni siquiera fuera del alcance del modo) se listan aquí. **No son falsos positivos verificados**: son defectos reales que el modelo detectó y que el ground truth no declara, porque varios goldens declaran un conjunto mínimo de hallazgos mientras su código contiene más de un defecto. Confirmar o descartar cada uno exige adjudicar caso por caso contra el código.

- **Dataset señalizado · modo archivo**: `g01_syntax_scope:L6(Scope)`, `g01_syntax_scope:L6(Scope)`, `g01_syntax_scope:L6(Scope)`

Los casos concretos y su análisis están documentados en `CHANGELOG.md` (sección de evidencia y trazabilidad). La cifra es reproducible: `python evals/harness.py --write`.
