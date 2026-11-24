---
description: Fuente canónica de reglas normativas SQF (Arma 3): 7 Bloqueantes P0, Puerta de Calidad, Honestidad Técnica, Modos, Precedencia y Propiedad.
---

# Invariantes SQF — Arma 3 (fuente canónica)

Única fuente canónica de reglas normativas. Artefactos derivados ([lentes](lens-architect.md), workflows, adaptadores, inline) pueden citarlo o resumirlo, pero no redefinirlo.

## Propiedad de documentos canónicos

| Documento | Anclas | Reglas |
| :--- | :--- | :--- |
| `references/invariants.md` | `CANON:BLOQUEANTES`, `CANON:PUERTA`, `CANON:HONESTIDAD`, `CANON:MODOS`, `CANON:PRECEDENCIA`, `CANON:PROPIEDAD` | Invariantes normativos y disciplinas. |
| [`references/sqf-standards.md`](sqf-standards.md) | `CANON:ESTANDAR` | Estándar de escritura SQF. |
| [`references/rubrica.md`](rubrica.md) | `CANON:RUBRICA`, `CANON:PARTICIPACION` | Severidad y matriz por modo. |

Propiedad disjunta: reglas únicas. N2 en `CANON-EXTRACT`/inline; N3 exclusivamente en su canónico.

## Niveles de contenido normativo

| Nivel | Longitud | Ámbito | Verificación |
| :--- | :---: | :--- | :--- |
| **N1** (Índice) | ≤25 tok/l | Capa 0, extractos, inline | Conteo exacto |
| **N2** (Resumen) | ≤60 tok/í | `CANON-EXTRACT`, inline | Hash canónico |
| **N3** (Definición) | Completo | Canónico propietario | Falla si duplica |

---

<!-- CANON:BLOQUEANTES -->
## Definición precisa de Bloqueante (P0)

ÚNICA definición normativa; no duplicar, referir.

1. **Errores de sintaxis SQF**: errores por `references/run_sqflint.py` (exit code 1) o variables locales fugadas al scope exterior sin `private`/`params` (warning de scope es BLOQUEANTE; no reconocidos son Sugerencia a contrastar con Biki).
2. **Softlocks potenciales, bucles infinitos o bloqueos de init**: `waitUntil` sin condición alcanzable garantizada ni timeout de seguridad, bucles infinitos sin cadencia (`while {true}` sin suspensión o PFH), retrasos bloqueantes (`sleep`/`uiSleep`/`waitUntil`) en hilo principal de init (`init*.sqf`, `postInit`) que congelan la misión (delegar a `spawn` o PFH), o esperas cruzadas cliente-servidor indefinidas.
3. **Violaciones críticas de dedicado**: uso de `player` o `waitUntil {!isNull player}` en servidor dedicado (`isDedicated == true`, donde `player` es permanentemente `objNull`), o comandos GUI (`hint`, `dialog`, etc.) en servidor — una guarda `if (hasInterface)` NO lo legitima (la retroalimentación va por `remoteExec` al cliente).
4. **Suspensión en contexto unscheduled**: `sleep`, `uiSleep` o `waitUntil` donde `canSuspend == false` (`preInit = 1`, Event Handlers del motor, `remoteExecCall` o invocación unscheduled). Ambos (`sleep` y `uiSleep`) requieren scheduled.
5. **Violaciones de whitelist en `CfgRemoteExec`**: invocaciones remotas (`remoteExec`, `remoteExecCall`) de funciones ausentes de la lista blanca de `CfgRemoteExec >> Functions` cuando `mode = 1`.
6. **Contratos de interfaz rotos o parámetros incompatibles**: discrepancias en cantidad, orden o tipos de datos requeridos en `params` entre módulos o llamadas de función.
7. **Inyección no permitida de dependencias de framework**: uso de CBA o ACE3 (`CBA_fnc_*`, `ace_*`) cuando el perfil del proyecto declara `CBA: no` o `ACE3: no`.
<!-- /CANON:BLOQUEANTES -->

<!-- CANON:PUERTA -->
## Puerta de Calidad Infranqueable

- El conteo de bloqueantes y la lista de `archivo:línea` provienen directamente del informe estructurado emitido por `sqf_orchestrator.py --lint` (`RESUMEN: bloqueantes=N...`) y de los revisores semánticos.
- Si tras **3 iteraciones** todavía queda **AL MENOS UN BLOQUEANTE** abierto:
  1. **DETENER** el proceso de forma inmediata.
  2. **INFORMAR AL USUARIO** con el desglose exacto de cada bloqueante sin resolver (disciplina detector, archivo, línea, causa raíz e intentos fallidos extraídos del informe).
  3. **PROHIBIDO DECLARAR "TERMINADO" O ENTREGAR COMO FINAL**. El resultado se marca como `DETENIDO (NO PASA)` y se solicita intervención humana. Se elimina cualquier cláusula de entrega permisiva; código con bloqueantes jamás se entrega como terminado.
- Solo se avanza a Plan de prueba, Documentación y Entrega si el número de bloqueantes abiertos es **CERO**.
- **Regla del ciclo**: solo los defectos **Bloqueantes** reinician el ciclo de corrección (máx. 3 iteraciones, orden locality → performance → best-practices).
<!-- /CANON:PUERTA -->

<!-- CANON:HONESTIDAD -->
## Principio de Honestidad Técnica (Invariante de Entorno)

- Lo no ejecutado en servidor dedicado se reporta **NO VERIFICADO**; nunca se declara completo.
- Si `sqflint` no está disponible (`SQFLINT_NO_DISPONIBLE`), el análisis estático se reporta obligatoriamente como `NO VERIFICADO` (JAMÁS como `PASA`).
- Los ítems correspondientes a ejecución real en servidor dedicado se marcan `NO VERIFICADO` **salvo que el Perfil del Proyecto declare que el entorno existe y se haya ejecutado en esta máquina, en esta sesión**.
- Si el wiki lookup no pudo ejecutarse (réplica `a3ref` ausente → estado `SIN_REPLICA`), toda afirmación técnica dependiente de la BIKI queda `NO VERIFICADO`, nunca `PASA`.
- Estados formales permitidos por ítem: `PASA`, `NO PASA`, `NO VERIFICADO` y `NO APLICA` únicamente si el componente no aplica al modo.
- Prohibido presentar como `PASA` cualquier ítem que no se haya comprobado con una fuente primaria.
<!-- /CANON:HONESTIDAD -->

<!-- CANON:MODOS -->
## Criterios de modo y escalado

Determinación obligatoria: `python scripts/sqf_orchestrator.py --root <raíz> --mode-query` (`0` éxito, `1` error, `10` `NO VERIFICADO`).

| Modo | Criterio determinista |
| :--- | :--- |
| Sin flujo | Typo, ajuste puntual, consulta conceptual |
| **Micro** | 1 archivo `.sqf`, ≤50 líneas, sin dependencias ni ciclo de vida (`init*.sqf`, `description.ext`), sin red ni scheduler |
| **Estándar** | Multi-archivo (2–3), >50 líneas, ciclo de vida, señales de red o modificación con red |
| **Completo** | ≥4 archivos o ≥3 módulos, JIP, HC, persistencia o auditoría completa |

- **Inventario vacío**: 0 archivos devuelve `NO VERIFICADO`, se pide ruta; jamás Micro por defecto.
- **Fallback obligatorio**: sin script, modo es `Estándar` con `NO VERIFICADO`; NUNCA Micro manual.
- **Override**: `--mode <modo>` respeta selección (salvo Micro con red: advertir y escalar).
- **Escalado**: señales de red o scheduler escalan Micro → Estándar.
<!-- /CANON:MODOS -->

<!-- CANON:PRECEDENCIA -->
## Precedencia ante conflictos

1. Correctitud de red y estabilidad en servidor dedicado (locality, desync, softlock, JIP).
2. Rendimiento y scheduler.
3. Estilo y legibilidad.

Una optimización de rendimiento **JAMÁS** se aplica si compromete la estabilidad o la localidad. Ante un conflicto entre hallazgos, prevalece la categoría de mayor precedencia, y el hallazgo subordinado se reporta como `Sugerencia`, no como `Bloqueante`.
<!-- /CANON:PRECEDENCIA -->

<!-- CANON:PROPIEDAD -->
## Propiedad de reglas (sin hallazgos duplicados)

Dueño único por tema; el revisor que detecta un tema ajeno anota `derivado a <dueño>`:

| Dueño | Disciplina y lente de referencia |
| :--- | :--- |
| `innovator` | Mecánicas nuevas e innovación ([`lens-claims.md`](lens-claims.md)) |
| `static-analyzer` | Sintaxis y variables sin `private` vía linter ([`lens-best-practices.md`](lens-best-practices.md)) |
| `best-practices` | Scope heurístico, lazy eval, nomenclatura ([`lens-best-practices.md`](lens-best-practices.md)) |
| `locality` | `remoteExec`, JIP, `publicVariable`, esperas, HC ([`lens-locality.md`](lens-locality.md)) |
| `performance-auditor` | Scheduler, bucles, handlers por frame, fugas ([`lens-performance.md`](lens-performance.md)) |
| `config-auditor` | `CfgRemoteExec`, `CfgFunctions`, ciclo de vida ([`lens-config.md`](lens-config.md)) |
| `architect` | Arquitectura modular y contratos `params` ([`lens-architect.md`](lens-architect.md)) |
| `doc-writer` | Documentación y guías (`references/workflows/documentation.md`) |
<!-- /CANON:PROPIEDAD -->

---

## Invariantes de servidor dedicado (headless)

En servidor dedicado (`Arma3Server.exe`), `player` es permanentemente `objNull` y no hay GUI:
- Comandos GUI (`hint`, `dialog`, etc.) prohibidos en servidor; `if (hasInterface)` no los legitima (usar `remoteExec` al cliente).
- Lógica de jugador en `initPlayerLocal.sqf` o dirigida por `remoteExec` al `owner`.
- Diagnóstico vía `diag_log` (no `systemChat` ni `format` a `player`).
- Distinguir `isServer` (host/servidor), `isDedicated` (dedicado puro) y `hasInterface` (cliente).
- Prohibido `sleep`/`uiSleep`/`waitUntil` en hilo principal de inicio (delegar a `spawn`/PFH). Ver [`lens-locality.md`](lens-locality.md).

## Perfil del Proyecto (7 parámetros)

Declarado una vez por sesión (si no se declara, ítems quedan `NO VERIFICADO`):
`ARMA_VERSION` (ej. `2.22`), `DESTINO` (`mision` | `addon`), `CBA` (`sí` | `no`), `ACE3` (`sí` | `no`), `SERVIDOR_DEDICADO` (ruta | `no`), `SQFLINT` (ruta | `no`), `MODO` (`Micro` | `Estándar` | `Completo`).

## Verificación de comandos contra la BIKI

Fuente primaria: réplica local `a3ref` (`scripts/sqf_wiki_reader.py`). Caché [`wiki-cache.md`](wiki-cache.md) es fallback offline para comandos cubiertos. Sin confirmación queda `NO VERIFICADO`; prohibido asumir comandos de memoria. Ver [`lens-claims.md`](lens-claims.md).

## Contrato de esquema del informe

`REPORT_SCHEMA_VERSION = 1`. Salida estructurada según contrato en [`report_format.md`](report_format.md).

---

## Paquete Inline P1–P4 y Niveles de Severidad

Para entornos sin filesystem ni terminal (ChatGPT, Gemini):
- **P1**: 7 categorías N1, Puerta (0 bloqueantes) y Honestidad técnica.
- **P2**: Fallback `Estándar` con `NO VERIFICADO`; prohibido `Micro` manual.
- **P3**: Checklist priorizado (N2) de bloqueantes.
- **P4**: Formato `[SEVERIDAD] archivo:linea (disciplina): descripcion` y cierre `RESUMEN: bloqueantes=N; sugerencias=N; no_verificado=N`.

### Reglas de severidad
- `BLOQUEANTE`: Defecto P0 crítico; impide entrega y exige resolución inmediata.
- `SUGERENCIA`: Optimización o estilo opcional sin compromiso de estabilidad.
- `NO_VERIFICADO`: Sin comprobación determinista (sin dedicado real, linter o BIKI).
- `NO_APLICA`: Verificación no pertinente al modo de revisión activo.
