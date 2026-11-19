---
description: Rúbrica de severidad y matriz de participación por modo. Documento canónico complementario de references/invariants.md.
---

# Rúbrica y participación por modo

Documento canónico complementario de `references/invariants.md`. Contiene la
**rúbrica de severidad** (qué es Bloqueante y qué es Sugerencia) y la **matriz
de participación por modo** (qué se revisa en cada modo). Las definiciones de
bloqueante, la puerta de calidad, la honestidad técnica, los criterios de
modo, la precedencia y la propiedad de reglas viven en `invariants.md` y NO se
repite aquí.

<!-- CANON:RUBRICA -->
## Rúbrica de severidad

- **Bloqueante (P0)**: ver la definición normativa en
  `references/invariants.md`, sección `CANON:BLOQUEANTES` (7 categorías). Esa
  lista es la única fuente; cualquier cambio se hace allí y se referencia desde
  aquí. Resumen: sintaxis y fugas de scope, softlocks y bloqueos de init,
  violaciones de dedicado (incluida UI en rutas de servidor), suspensión en
  unscheduled, whitelist `CfgRemoteExec`, contratos de interfaz rotos,
  dependencias de framework no autorizadas.
- **Sugerencia**: cuestiones de estilo, legibilidad, nomenclatura secundaria,
  micro-optimizaciones que no corrigen un bug activo, sugerencias de
  refactorización opcional.
- **Regla del ciclo**: solo los defectos **Bloqueantes** reinician el ciclo de
  corrección (máx. 3 iteraciones).
- **Precedencia ante conflictos**: ver `CANON:PRECEDENCIA` en
  `references/invariants.md`.
<!-- /CANON:RUBRICA -->

<!-- CANON:PARTICIPACION -->
## Matriz de participación por modo

| Disciplina / capability | Micro | Estándar | Completo |
| :--- | :--- | :--- | :--- |
| Innovación | — | opcional (si se piden mecánicas nuevas o mejoras) | ✔ si es sistema nuevo o diseño de mecánicas |
| Arquitectura | — (checklist propio) | — (mini-plan de 5 líneas del orquestador) | ✔ |
| Implementación | — (escribe el orquestador) | opcional (si hay módulos independientes) | ✔ por módulo |
| Verificación wiki (la hace el orquestador) | solo comandos no triviales | ✔ (verificando en la Biki) | ✔ (sobre el plan, antes de codificar) |
| Análisis estático | ✔ si hay archivo | ✔ si hay archivo | ✔ |
| Auditoría de configuración | — | si hay red y raíz de proyecto (misión o addon) | ✔ |
| Best-practices | 1 pasada: solo bloqueantes + máx. 3 sugerencias | ✔ | ✔ |
| Locality | — | solo con señales de red | ✔ |
| Performance | — (checklist) | solo con señales de rendimiento | ✔ |
| Plan de prueba | — | si intervino locality | ✔ |
| Documentación | — (cabecera en el código) | si hay API pública o parámetros | ✔ si el sistema tiene interfaz de uso |

**Micro** = 1–2 agentes, cero ceremonia, pero con el checklist de
autoverificación de dedicado de `sqf-standards.md` aplicado estrictamente antes
de entregar.

**Invariantes de Servidor Dedicado en Micro**: en Micro se mantienen
rigurosamente todas las invariantes de dedicado: `player` jamás se utiliza sin
verificar `hasInterface`, los comandos de interfaz UI (`hint`, `cutText`) se
consideran inútiles o prohibidos en servidor, y jamás se permite `sleep` o
`waitUntil` en contextos unscheduled.

**Análisis Estático Obligatorio en Micro**: si hay archivo en disco, se ejecuta
obligatoriamente `sqf_orchestrator.py --lint`. Códigos de salida: `0` = reporte
producido sin error fatal, `1` = error duro o ruta inválida, `10` = linter no
disponible (`NO VERIFICADO`). Si `sqflint` no está disponible
(`SQFLINT_NO_DISPONIBLE`), el análisis se reporta como `NO VERIFICADO` (NUNCA
como `PASA`).
<!-- /CANON:PARTICIPACION -->
