---
description: Reglas canónicas de escritura y diseño SQF de Arma 3 para desarrolladores y revisores del equipo.
---

# Estándar SQF del equipo (fuente única)

Lo usan developer (para escribir), reviewers (para revisar) y orquestador (checklist Micro).
Es la fuente canónica de las **reglas de escritura** del equipo.

> [!IMPORTANT]
> **Propiedad:** este documento es canónico de las reglas de ESCRITURA
> (`CANON:ESTANDAR`). Los criterios de revisión (qué es bloqueante, la puerta de
> calidad, la honestidad técnica, los modos, la precedencia y la propiedad de
> reglas) viven en `references/invariants.md` y en `references/rubrica.md`.
> La propiedad es disjunta: ninguna regla se define en los tres.

<!-- CANON:ESTANDAR -->
## Reglas de código
1. Toda variable local con `private _x = …;`. En funciones/EH, `params` tipado con defaults al inicio: `params [["_unit", objNull, [objNull]], ["_n", 0, [0]]];`
2. Evaluación perezosa `a && {b}` cuando `b` es costoso, tiene efectos o puede fallar con `a` falso. No en condiciones triviales.
3. Nombres: camelCase, significativos; `_i` solo en índices; constantes `MAYUS_CON_GUION`; globales y claves `setVariable` con prefijo `TAG_`; funciones `TAG_fnc_nombre`.
4. Funciones globales: `compileFinal` o CfgFunctions. Sin código ejecutable suelto en variables globales.
5. `call` por defecto (cero sobrecoste de scheduler); `spawn` solo si hace falta suspensión (`sleep`, `uiSleep`, `waitUntil`).
   - **Contextos UNSCHEDULED (`canSuspend == false`)**: `preInit` (`preInit = 1`), Event Handlers del motor (`addEventHandler`, `addMissionEventHandler`), `remoteExecCall`, y funciones atómicas ejecutadas en `call` dentro de ellos. NUNCA usar `sleep`, `uiSleep` ni `waitUntil` en unscheduled (provoca error de script inmediato o detención silenciosa).
   - **Contextos SCHEDULED (`canSuspend == true`)**: `init.sqf`, `initServer.sqf`, `initPlayerLocal.sqf`, `initPlayerServer.sqf`, funciones `postInit` (`postInit = 1`), y scripts ejecutados mediante `spawn` o `execVM`.
   - **Regla de arranque en scripts de inicialización**: Aunque `init.sqf`, `initServer.sqf` y `postInit` se ejecutan en entorno scheduled, se PROHÍBE el uso de `sleep` o `waitUntil` bloqueantes prolongados en su flujo principal para evitar retrasar el arranque de la misión o congelar la pantalla de carga de los jugadores. Toda espera prolongada o bucle continuo debe delegarse a un `spawn` desacoplado o a un Per-Frame Handler (PFH).
   - **`sleep` vs `uiSleep`**: Ambos requieren obligatoriamente un entorno scheduled (`canSuspend == true`). `sleep` se rige por el tiempo de simulación (`time`) y se pausa con el menú de pausa o con `accTime == 0`. `uiSleep` se rige por el tiempo de sistema (`uiTime` / `diag_tickTime`) y continúa contando durante pausas, briefings o pantallas de carga. Ninguno funciona en unscheduled.
   - *Referencias oficiales de la Biki (consultadas 2026-10-03)*:
     * Event Scripts: https://community.bistudio.com/wiki/Event_Scripts
     * Functions Library (preInit/postInit): https://community.bistudio.com/wiki/Functions_Library_(Arma_3)
     * sleep: https://community.bistudio.com/wiki/sleep
     * uiSleep: https://community.bistudio.com/wiki/uiSleep
     * canSuspend: https://community.bistudio.com/wiki/canSuspend
6. `waitUntil` siempre con cadencia de suspensión (`sleep` / `uiSleep`) y condición alcanzable con salida obligatoria por timeout. Jamás usar `waitUntil` en contextos unscheduled.
7. Sin `execVM` repetido en bucles; sin lecturas repetidas de la misma global en un bucle; `getVariable [n, default]`; `isEqualTo` para tipos mixtos; `findIf`/`count`/`apply` cuando simplifican.
8. Red: target explícito en `remoteExec`; `publicVariableServer/Client` si el destino es conocido; no broadcast de alta frecuencia; JIP con ID guardado y borrado explícito; nada de `BIS_fnc_MP`. Toda función invocada de forma remota (`remoteExec` o `remoteExecCall`) debe estar registrada en la whitelist de `CfgRemoteExec >> Functions` (`mode = 1`) para evitar fallos silenciosos en servidores dedicados.
   - Fuente oficial: https://community.bistudio.com/wiki/Arma_3:_CfgRemoteExec (consultado 2026-10-03: VERIFICADO).
9. Sin `diag_log`/debug residual en la entrega (o tras una macro/flag `TAG_debug`).
10. Rendimiento: bucles persistentes con cadencia y condición de salida; sin escaneos globales (`allUnits`, `allMissionObjects`, `nearestObjects` grandes) dentro de bucles o EH frecuentes; `pushBack` en vez de `_a = _a + [x]`; guardar el handle de todo `spawn` de larga vida; todo `addEventHandler` y objeto/grupo creado tiene su limpieza.
11. Interfaz en servidor dedicado: los comandos de interfaz, hint, hintC, titleText, cutText, dialog, createDialog, ctrlCreate, displayCtrl, findDisplay, uiNamespace, ppEffect y afines, no se usan en ninguna ruta que pueda ejecutarse en el servidor, y una guarda if hasInterface no los legitima, porque la guarda solo evita el error y no el trabajo inutil. Si hace falta retroalimentacion visual, va por remoteExec al cliente.

## Cabecera de función (BI-style, en español)
```
/*
 * Función: TAG_fnc_nombre
 * Descripción: <qué hace, 1 línea>
 * Parámetros: 0: <tipo> <nombre> - <desc> (por defecto: …)
 * Retorno: <tipo> - <desc>
 * Ejecución: <servidor|cliente|HC|todos> · <scheduled|unscheduled>
 * Efecto de red: <ninguno|remoteExec a …|publicVariable …>
 * Ejemplo: [player] call TAG_fnc_nombre;
 */
```

## Reglas de Framework: CBA y ACE3 Condicionales

El código debe adaptarse estrictamente al **Perfil del Proyecto** (`CBA: sí/no`, `ACE3: sí/no`):

### Con CBA declarado (`CBA: sí`)
1. **Bucles y Tareas Periódicas (PFH)**:
   - Prohibido crear bucles continuos mediante `spawn { while {true} do { sleep ...; }; }`.
   - Usar obligatoriamente `CBA_fnc_addPerFrameHandler` y almacenar el identificador de handle para su cancelación con `CBA_fnc_removePerFrameHandler`:
     ```sqf
     _handle = [{
         params ["_args", "_handle"];
         _args params ["_unit"];
         if (!alive _unit) exitWith { [_handle] call CBA_fnc_removePerFrameHandler; };
         // Lógica recurrente
     }, _cadenciaSegundos, [_unit]] call CBA_fnc_addPerFrameHandler;
     ```
2. **Eventos Desacoplados**:
   - Registrar escuchas: `["TAG_evento", { params ["_arg1", "_arg2"]; ... }] call CBA_fnc_addEventHandler;`.
   - Emisión orientada a localidad: `CBA_fnc_localEvent`, `CBA_fnc_serverEvent`, `CBA_fnc_globalEvent`, `CBA_fnc_targetEvent`.
3. **Detección y CfgPatches**:
   - Detección en tiempo de ejecución: `isClass (configFile >> "CfgPatches" >> "cba_main")`.
   - Fuente oficial: https://github.com/CBATeam/CBA_A3 (consultado 2026-10-03).

### Con ACE3 declarado (`ACE3: sí`)
1. **Detección e Integración**:
   - Detección en tiempo de ejecución: `isClass (configFile >> "CfgPatches" >> "ace_main")`.
   - Fuente oficial: https://ace3.acemod.org/ (consultado 2026-10-03).

### Sin CBA declarado (`CBA: no`) — Entorno Vanilla Estricto
1. **Alternativas Vanilla**:
   - Bucles periódicos: `spawn` controlado con handle almacenado, condición de parada y `sleep`/`uiSleep`, o bien `addMissionEventHandler ["EachFrame", { ... }]` con acumulador de delta de tiempo.
   - Eventos personalizados: `[missionNamespace, "TAG_evento", { params ["_arg1"]; ... }] call BIS_fnc_addScriptedEventHandler;` y emitir con `[missionNamespace, "TAG_evento", [_arg1]] call BIS_fnc_callScriptedEventHandler;`.
2. **Prohibición Absoluta de Dependencia Silenciosa**:
   - Jamás utilizar identificadores o funciones `CBA_fnc_*` ni `ace_*` si el perfil no declara explícitamente CBA/ACE3. La introducción inadvertida de CBA o ACE3 se considera un defecto **Bloqueante**.

## Checklist de autoverificación (modo Micro, obligatorio antes de entregar)
- [ ] Todas las locales con `private`/`params`; params tipados si es función.
- [ ] Sin comandos de interfaz en rutas de servidor, ni siquiera con guarda hasInterface.
- [ ] Sin `sleep`/`uiSleep`/`waitUntil` en contexto unscheduled (`preInit`, EHs, `remoteExecCall`).
- [ ] Sin `sleep` o esperas bloqueantes prolongadas en el hilo principal de `init.sqf`, `initServer.sqf` o `postInit`.
- [ ] Respetar perfil CBA/ACE3: sin dependencias silenciosas de `CBA_fnc_*` o `ace_*` si `CBA: no`; uso de PFH/eventos si `CBA: sí`.
- [ ] Funciones remotas (`remoteExec`/`remoteExecCall`) declaradas en whitelist `CfgRemoteExec >> Functions` (`mode = 1`).
- [ ] Comandos no triviales verificados (o declarados sin verificar).
- [ ] Condiciones costosas con evaluación perezosa.
- [ ] Nombres y tag correctos; cabecera presente.
- [ ] Sin globales sin tag; sin debug residual.
- [ ] Bucles con cadencia y salida; sin escaneos globales en ciclos frecuentes; EH/objetos/grupos con limpieza.
- [ ] Si aparece cualquier señal de red → escalar a Estándar.
<!-- /CANON:ESTANDAR -->
