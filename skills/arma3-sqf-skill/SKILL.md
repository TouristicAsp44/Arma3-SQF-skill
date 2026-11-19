---
name: arma3-sqf-skill
description: >-
  [ES] Audita y diseña scripts SQF de Arma 3 para servidor dedicado. Activar para:
  remoteExec, publicVariable, JIP, Headless Client, init.sqf, CfgRemoteExec,
  bucles sobre allUnits, variables sin private, comandos de interfaz en servidor.
  No activar para: preguntas conceptuales, typos, código no SQF.
  [EN] Audits and designs Arma 3 SQF scripts for dedicated server. Activate for:
  remoteExec, publicVariable, JIP, Headless Client, init.sqf, CfgRemoteExec,
  loops over allUnits, unscoped variables, interface commands on server paths.
  Do not activate for: conceptual questions, typos, non-SQF code.
---

# Arma 3 SQF Universal Skill — Capa 0

Audita, diseña e implementa scripts SQF para Arma 3 en servidor dedicado (`Arma3Server.exe`), garantizando estabilidad y optimización de contexto.

## 1. Cuatro Intenciones

- **AUDITAR**: Revisión contra invariantes de calidad → `references/lenses/`
- **DISEÑAR**: Plan modular, interfaces y JIP → `references/workflows/modes.md` + `references/lenses/architect.md`
- **IMPLEMENTAR**: Escribir módulos según estándar → `references/workflows/implementation.md` + `references/lenses/best_practices.md`
- **DOCUMENTAR**: Guía de uso y pruebas → `references/workflows/documentation.md` (y `test_plan.md`)

## 2. Índice N1 de las 7 Categorías de Bloqueante (P0)

Definición completa en `references/invariants.md`:
1. Sintaxis SQF y variables no declaradas (sin `private`/`params`).
2. Softlocks, bucles infinitos y bloqueos de inicialización.
3. Violaciones de dedicado (`player` o interfaz en servidor).
4. Suspensión unscheduled (`sleep`/`uiSleep`/`waitUntil` con `canSuspend == false`).
5. Violaciones de lista blanca en `CfgRemoteExec >> Functions`.
6. Contratos de interfaz rotos e incompatibilidades en `params`.
7. Dependencias no permitidas (`CBA`/`ACE3`).

## 3. Puerta de Calidad y Honestidad Técnica

- **Puerta de Calidad**: Si tras 3 iteraciones queda ≥1 bloqueante: DETENER; PROHIBIDO entregar. Solo CERO bloqueantes.
- **Principio de Honestidad**: Sin herramientas activas (linter/wiki): reportar `NO VERIFICADO`, jamás `PASA`. Sin prueba en dedicado real no declarar completo.

## 4. Triage de Modo Determinista

Criterios de `references/invariants.md`:
- Determinación: `sqf_orchestrator.py --root <raíz del proyecto> --mode-query`
- **Micro**: Archivo único ≤50 líneas, sin ciclo de vida, red ni scheduler.
- **Estándar**: 2–3 archivos, >50 líneas, ciclo de vida o señales de red/scheduler.
- **Completo**: ≥4 archivos o ≥3 módulos, JIP, Headless Client, persistencia.
- **Fallback**: Sin disco, defecto `Estándar` (`NO VERIFICADO`). No clasificar Micro manualmente.
- **Escalado**: Señal de red o scheduler en Micro escala a `Estándar`.

## 5. Activación de Lentes y Flujos (Bajo Demanda)

Abre la lente o flujo ante su señal disparadora (subagentes equivalentes):
- `remoteExec` | `publicVariable` | `JIP` | `HC` (`sqf-locality-auditor`) → `references/lenses/locality.md`
- `allUnits` | `EachFrame` | `scheduler` (`sqf-performance-auditor`) → `references/lenses/performance.md`
- `scope` | `private` | `params` (`sqf-best-practices-reviewer`) → `references/lenses/best_practices.md`
- `CfgRemoteExec` | `CfgFunctions` (`sqf-mission-config-auditor`) → `references/lenses/config.md`
- `arquitectura` | `módulos` | `interfaz` (`sqf-architect`) → `references/lenses/architect.md`
- `BIKI` | `comandos wiki` (`sqf-claim-verifier`) → `references/lenses/claims.md`
- `implementar` (`sqf-developer`) → `references/workflows/implementation.md`
- `documentar` (`sqf-doc-writer`) → `references/workflows/documentation.md`
- `plan pruebas` (`sqf-test-plan-generator`) → `references/workflows/test_plan.md`
- `linter` (`sqf-static-analyzer`) → `python scripts/sqf_orchestrator.py --lint <archivo>`
- `innovar` (`sqf-innovator`) → `references/workflows/innovation.md`

## 6. Operación y Formato del Informe

- **Modo archivo (con filesystem)**: Ejecuta `python scripts/sqf_orchestrator.py --lint <archivo>`.
- **Modo pegado (sin filesystem)**: Checklist estático de `references/invariants.md` (degrada a `NO VERIFICADO` sin linter ni wiki).

Formato estructurado de `references/report_format.md`:
```
REPORT_SCHEMA_VERSION: 1
[BLOQUEANTE|SUGERENCIA|NO_VERIFICADO] archivo:linea (disciplina): descripcion
RESUMEN: bloqueantes=N; sugerencias=N; no_verificado=N
```

## 7. Perfil del Proyecto (7 parámetros)

Declarar al inicio (`ARMA_VERSION`, `DESTINO`, `CBA`, `ACE3`, `SERVIDOR_DEDICADO`, `SQFLINT`, `MODO`). Turnos siguientes refieren perfil declarado. Ver `references/invariants.md`.
