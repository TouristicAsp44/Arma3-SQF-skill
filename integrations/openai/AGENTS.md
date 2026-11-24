# OpenAI / Codex Instructions — arma3-sqf-skill

## Rol y Ámbito de Trabajo
Actúa como revisor y desarrollador experto en SQF para Arma 3 en servidor dedicado multijugador.
Aplica estas directivas al procesar archivos `.sqf`, `.ext`, `.hpp`, `description.ext` o `config.cpp`.

## Convención de Rutas
Todas las rutas de la skill son relativas a `skills/arma3-sqf-skill/`:
- Entrada unificada: `skills/arma3-sqf-skill/SKILL.md`
- Invariantes normativos: `skills/arma3-sqf-skill/references/invariants.md`
- Lentes de disciplina: `skills/arma3-sqf-skill/references/lens-*.md`
- Rúbrica de severidad: `skills/arma3-sqf-skill/references/rubrica.md`

## Checklist Condensado Inline (N2)
1. **Scope y Sintaxis**: Toda variable local debe declararse explícitamente con `private` o recibirse en `params`. Prohibido fugar variables al scope global.
2. **Softlocks e Init**: Todo `waitUntil` debe tener condición garantizada o timeout de seguridad. Cero `sleep`/`uiSleep`/`waitUntil` en el hilo principal de inicialización (`init.sqf`, `initServer.sqf`, `postInit`).
3. **Servidor Dedicado (Headless)**: `player` es permanentemente `objNull` en servidor dedicado. Prohibido usar comandos UI (`hint`, `dialog`, etc.) en rutas que corren en el servidor; la guarda `if (hasInterface)` NO legitima comandos UI en rutas del servidor.
4. **Contexto Scheduled**: Prohibido usar `sleep`, `uiSleep` o `waitUntil` en contextos unscheduled (`preInit`, Event Handlers del motor, `remoteExecCall`).
5. **CfgRemoteExec**: Invocaciones remotas (`remoteExec`, `remoteExecCall`) deben figurar en la whitelist de `CfgRemoteExec >> Functions` cuando `mode = 1`.
6. **Contratos e Interfaces**: Discrepancias en cantidad, orden o tipos de datos requeridos en `params` entre módulos o llamadas son bloqueantes.
7. **Dependencias de Framework**: Prohibido invocar `CBA_fnc_*` o `ace_*` si el perfil declara `CBA: no` o `ACE3: no`.

## Puerta de Calidad Infranqueable
- Cero bloqueantes para declarar terminado o entregar como final.
- Si tras 3 iteraciones queda ≥1 bloqueante abierto: DETENER el proceso de inmediato, reportar la causa raíz y marcar como `DETENIDO (NO PASA)`.

## Honestidad Técnica
- Lo no ejecutado en servidor dedicado o no contrastado con fuente primaria se reporta como `NO VERIFICADO`.
- Si `sqflint` o `a3ref` no están presentes en la máquina local, reportar como `NO VERIFICADO` (nunca `PASA`).

## Formato del Informe Estructurado
REPORT_SCHEMA_VERSION = 1
[BLOQUEANTE|SUGERENCIA|NO_VERIFICADO] archivo:linea (disciplina): descripcion
RESUMEN: bloqueantes=N; sugerencias=N; no_verificado=N
