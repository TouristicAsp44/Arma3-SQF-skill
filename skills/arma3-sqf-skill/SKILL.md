---
name: arma3-sqf-skill
description: >-
  Asistencia especializada para analizar, auditar, diseñar, implementar y
  documentar scripts SQF de Arma 3. Úsala ante consultas sobre SQF, locality,
  remoteExec, CfgRemoteExec, JIP, publicVariable, init.sqf, servidores
  dedicados, Headless Client, rendimiento, seguridad multijugador o
  arquitectura de funciones.
---

# Arma 3 SQF Universal Skill — Capa 0

## 1. Propósito

Auditar, diseñar, implementar y documentar SQF de Arma 3 en dedicado (`Arma3Server.exe`), asegurando estabilidad MP y scheduler.

## 2. Activación/Exclusión

- **Activar**: SQF, locality, `remoteExec`, `CfgRemoteExec`, JIP, `publicVariable`, `init.sqf`, dedicado, HC, scheduler, `allUnits`, variables sin scope.
- **Excluir**: Preguntas teóricas, Eden 3D, código no SQF o erratas.

## 3. Modos

- **AUDITAR**: Lentes (`references/lens-*.md`, antes `references/lenses/`) → `references/invariants.md`.
- **DISEÑAR**: Modular y JIP → `references/workflows/modes.md` + `references/lens-architect.md`.
- **IMPLEMENTAR**: SQF → `references/workflows/implementation.md` + `references/lens-best-practices.md` (`best_practices.md`).
- **DOCUMENTAR**: Pruebas → `references/workflows/documentation.md` + `references/workflows/test_plan.md`.

## 4. Triage

`sqf_orchestrator.py --root <raíz> --mode-query`:
- **Micro**: ≤50 líneas, sin init, red ni scheduler.
- **Estándar**: 2–3 archivos, >50 líneas, init o red/scheduler.
- **Completo**: ≥4 archivos o ≥3 módulos, JIP, HC o persistencia.
- **Fallback**: Sin disco: `Estándar` (`NO VERIFICADO`). Prohibido Micro manual; red escala a `Estándar`.

## 5. Protocolo

1. Perfil: 7 parámetros (`ARMA_VERSION`, `DESTINO`, `CBA`, `ACE3`, `SERVIDOR_DEDICADO`, `SQFLINT`, `MODO`).
2. Triage: modo e intención.
3. Análisis: `sqf_orchestrator.py --lint <archivo>` o checklist.
4. Lentes: `references/lens-locality.md`, `references/lens-performance.md`, `references/lens-best-practices.md`, `references/lens-config.md`, `references/lens-architect.md`, `references/lens-claims.md`, `references/workflows/innovation.md`.
5. Corrección: máx. 3 iteraciones (Locality > Rendimiento > BP). 6. Puerta: Cero bloqueantes.

## 6. 7 Bloqueantes P0

En `references/invariants.md`:
1. Sintaxis SQF y variables sin scope (`private`/`params`).
2. Softlocks, bucles infinitos y bloqueos init.
3. Violaciones de dedicado (`player` o UI en servidor).
4. Suspensión unscheduled (`sleep`/`waitUntil` con `!canSuspend`).
5. Violación de whitelist en `CfgRemoteExec >> Functions`.
6. Contratos rotos o incompatibilidad en `params`.
7. Dependencias no permitidas (`CBA`/`ACE3`).
*Puerta*: ≥1 bloqueante tras 3 iteraciones: DETENER; PROHIBIDO entregar.

## 7. Seguridad

- `CfgRemoteExec`: `mode = 1` en `Functions` (whitelist); `mode = 0` en `Commands`.
- `params` tipados en red. `compileFinal` en globales; aislamiento cliente/servidor.

## 8. Estados

- `references/rubrica.md`: `BLOQUEANTE` (P0), `SUGERENCIA`, `NO_VERIFICADO`, `NO_APLICA`.
- Honestidad: Sin linter ni wiki, reportar `NO VERIFICADO`, jamás `PASA`. Sin servidor real, no declarar verificado.

## 9. Formato de Informe P1–P4

Contrato (`references/report_format.md`):
```
REPORT_SCHEMA_VERSION: 1
[BLOQUEANTE|SUGERENCIA|NO_VERIFICADO] archivo:linea (disciplina): descripcion
RESUMEN: bloqueantes=N; sugerencias=N; no_verificado=N
```

## 10. Índice de Referencias

En `references/`: `invariants.md`, `report_format.md`, `rubrica.md`, `sqf-standards.md`, `checklist-entrega.md`, `diferencial-misiones-addons.md`, `wiki-cache.md`, `lens-*.md`, `workflows/`.

## 11. Adaptador de Anfitrión

- Archivo: `sqf_orchestrator.py --lint <archivo>`.
- Pegado: Checklist de `references/invariants.md` (`NO VERIFICADO`).
- Host: `agents/openai.yaml`, `integrations/`. Lentes portables.
