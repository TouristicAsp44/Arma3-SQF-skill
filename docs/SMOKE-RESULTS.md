<!-- GENERATED FROM: evals/smoke/run_smoke.py | DO NOT EDIT -->
<!-- SOURCE-HASH: 4ecb7a01ef283a6d7980b9627ef700fa05ca85ae55f27d1e0eb7acc20369f371 -->

# Resultados de Smoke Tests S1–S3 (Evidencia de Calidad)

Tabla oficial generada automáticamente por `evals/smoke/run_smoke.py`. Cumple estrictamente con:
- **Regla R1**: La validación local es autónoma; hosts sin CLI quedan como `NO_VERIFICADO`.
- **Regla R5 / CANON:HONESTIDAD**: Solo se reportan modelos y veredictos respaldados por trazas reales en `evals/runs/` o por el motor determinista local.

## Tabla de Ejecución de Smoke Tests

| Host | Caso | Categoría | Modelo y Versión | Veredicto | Motivo Técnico |
| :--- | :---: | :--- | :--- | :---: | :--- |
| **Local (Engine)** | S1 | Cat. 1 (Scope / Sintaxis) | Deterministic Python Engine | **DETECTADO** | Análisis estático local sobre fixtures de smoke |
| **Local (Engine)** | S1 | Cat. 2 (Softlock / Init) | Deterministic Python Engine | **DETECTADO** | Análisis estático local sobre fixtures de smoke |
| **Local (Engine)** | S2 | Cat. 3 (Servidor Dedicado) | Deterministic Python Engine | **DETECTADO** | Análisis estático local sobre fixtures de smoke |
| **Local (Engine)** | S2 | Cat. 3 (Servidor Dedicado (UI)) | Deterministic Python Engine | **DETECTADO** | Análisis estático local sobre fixtures de smoke |
| **Local (Engine)** | S3 | Cat. 5 (CfgRemoteExec) | Deterministic Python Engine | **DETECTADO** | Análisis estático local sobre fixtures de smoke |
| **Local (Engine)** | S3 | Cat. 7 (Dependencias Framework) | Deterministic Python Engine | **DETECTADO** | Análisis estático local sobre fixtures de smoke |
| **Claude Code (Modo Archivo)** | S1 | Cat. 1 (Scope / Sintaxis) | N/A (sin ejecución) | **NO_VERIFICADO** | CLI 'claude' no instalada en este entorno (Regla R1) |
| **Claude Code (Modo Archivo)** | S1 | Cat. 2 (Softlock / Init) | N/A (sin ejecución) | **NO_VERIFICADO** | CLI 'claude' no instalada en este entorno (Regla R1) |
| **Claude Code (Modo Archivo)** | S2 | Cat. 3 (Servidor Dedicado) | N/A (sin ejecución) | **NO_VERIFICADO** | CLI 'claude' no instalada en este entorno (Regla R1) |
| **Claude Code (Modo Archivo)** | S2 | Cat. 3 (Servidor Dedicado (UI)) | N/A (sin ejecución) | **NO_VERIFICADO** | CLI 'claude' no instalada en este entorno (Regla R1) |
| **Claude Code (Modo Archivo)** | S3 | Cat. 5 (CfgRemoteExec) | N/A (sin ejecución) | **NO_VERIFICADO** | CLI 'claude' no instalada en este entorno (Regla R1) |
| **Claude Code (Modo Archivo)** | S3 | Cat. 7 (Dependencias Framework) | N/A (sin ejecución) | **NO_VERIFICADO** | CLI 'claude' no instalada en este entorno (Regla R1) |

---

## Resumen de Métricas
- **Esperables resueltos localmente**: 6/6 (100 %)
- **Falsos PASA**: 0 (0 %)
- **Omisiones / Silencios**: 0 (0 %)
- **Hosts externos sin CLI en entorno actual**: Reportados como `NO_VERIFICADO` con `modelo_version = "N/A (sin ejecución)"` según R1.
