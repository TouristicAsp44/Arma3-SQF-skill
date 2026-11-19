---
description: Checklist de entrega y criterios de verificación deterministas para proyectos SQF de Arma 3 (misiones y addons).
---

# Checklist de Entrega y Salida — arma3-sqf-skill

Guía normativa de control de calidad e invariantes de multijugador para misiones y addons de Arma 3.
Es la fuente de los **criterios de verificación** (lo que se evalúa como `PASA`, `NO PASA` o `NO VERIFICADO`).
Las **reglas de escritura** canónicas se definen en `sqf-standards.md`, al cual este checklist referencia para evitar duplicidad de contenido.
Ningún desarrollo se considerará finalizado sin haber evaluado la totalidad de los bloques aplicables.

---

## 1. Regla de Estados

Cada punto de control debe evaluarse de forma determinista y honesta bajo uno de los siguientes tres estados formales:

- **`PASA`**: Comprobado positivamente mediante análisis estático (`sqf_orchestrator.py --lint`), inspección de código o evidencia lógica verificada en documentación oficial.
- **`NO PASA`**: Defecto, discrepancia o violación de invariante detectada. Constituye un **Bloqueante** que detiene el flujo y prohíbe la entrega como finalizado.
- **`NO VERIFICADO`**: Punto de control no comprobable en este entorno (p. ej., pruebas de ejecución dinámica en runtime de `Arma3Server` o máquina virtual `sqfvm` por ausencia de binarios en el host, o linter no disponible). Debe declararse explícitamente en el informe final; **NUNCA** se asume como `PASA`.

---

## 2. Bloques de Verificación (A – I)

### Bloque A: Compilación y Sintaxis
- [ ] **A.1 Parseo determinista y análisis estático**: El código analizado mediante el script orquestador (`python skills/arma3-sqf-skill/scripts/sqf_orchestrator.py --root <raíz> --lint`) finaliza sin errores fatales (exit code `0`) y reporta `bloqueantes=0` en su resumen. Solo se marca como `PASA` si el informe contiene cero bloqueantes sintácticos o de scope. Si el script devuelve código `10` o el linter no está instalado (`SQFLINT_NO_DISPONIBLE`), el ítem se reporta obligatoriamente como `NO VERIFICADO` (NUNCA como `PASA`). Si devuelve código `1` o contiene bloqueantes, se reporta como `NO PASA`.
- [ ] **A.2 Compatibilidad de versión**: Todos los comandos SQF utilizados están soportados y vigentes según la versión declarada en el Perfil del Proyecto (`ARMA_VERSION`).
- [ ] **A.3 Ausencia de comandos obsoletos**: Prohibido el uso de primitivas obsoletas de red o scripting (p. ej., `BIS_fnc_MP`, reemplazado por `remoteExec`/`remoteExecCall`).
- [ ] **A.4 Resolución de directivas e inclusión**: Todas las directivas `#include`, `#define` y rutas relativas resuelven archivos existentes sin enlaces rotos ni dependencias locales del autor.

#### Ítem 9 del Checklist de Entrega
| Ítem / Disciplina | Estado | Regla de Cobertura Documental |
|---|---|---|
| 9. Verificación de Comandos en Wiki / Biki | PASA / NO VERIFICADO | Regla de Cobertura Documental:<br>- PASA: 100% de tokens candidatos del código contrastados contra réplica offline a3ref (commit: <git_sha_runtime>; 0 ausentes; 0 bloqueantes asociados).<br>- NO VERIFICADO: < 100% contrastados o sqflint no disponible (SQFLINT_NO_DISPONIBLE). Acompañado del número de hallazgos Bloqueantes por comando no identificado. |

### Bloque B: Invariantes de Servidor Dedicado
- [ ] **B.1 Arranque headless y RPT limpio**: No existen errores de script ni warnings de pre-inicialización al cargar en un servidor dedicado sin interfaz humana.
- [ ] **B.2 Aislamiento de entidad `player`**: Cero referencias a la variable `player` en hilos exclusivos del servidor (`isDedicated == true`), donde `player` devuelve permanentemente `objNull`.
- [ ] **B.3 Prohibición de softlock por espera de jugador**: NUNCA utilizar `waitUntil {!isNull player}` en `initServer.sqf` o en funciones exclusivas del servidor (provoca bloqueo infinito del arranque).
- [ ] **B.4 Interfaz en servidor dedicado**: Sin comandos de interfaz en rutas de servidor; verificación conforme a la Regla 11 de `sqf-standards.md` (prohibición estricta de `hint`, `cutText`, diálogos UI en servidor, no legitimados por `hasInterface`).
- [ ] **B.5 Prohibición de suspensión en unscheduled**: Cero llamadas a `sleep`, `uiSleep` o `waitUntil` en contextos unscheduled; verificación conforme a la Regla 5 de `sqf-standards.md`.
- [ ] **B.6 Acotamiento de `waitUntil`**: Todo `waitUntil` implementa cadencia de verificación y condición de salida por tiempo límite (timeout) conforme a la Regla 6 de `sqf-standards.md`.

### Bloque C: Red, Locality y Seguridad
- [ ] **C.1 Destinos de `remoteExec` explícitos y justificados**: Toda llamada remota define un destino concreto (`0` = global, `2` = servidor, `-2` = clientes excluyendo servidor, o ID específico de cliente); prohibido el broadcast indiscriminado (Regla 8 de `sqf-standards.md`).
- [ ] **C.2 Whitelist estricta en `CfgRemoteExec`**: Toda función invocada remotamente está registrada en `CfgRemoteExec >> Functions` con `mode = 1` y directivas `allowedTargets` coherentes con el código (Regla 8 de `sqf-standards.md`).
- [ ] **C.3 Validación de remitente en servidor**: Las funciones remotas que alteran estado sensible en el servidor validan el ID emisor con `remoteExecutedOwner`.
- [ ] **C.4 Prohibición de broadcast de alta frecuencia**: Prohibido el envío de `remoteExec`, `remoteExecCall` o `publicVariable` por frame (`EachFrame`) o en bucles rápidos sin temporizador (Regla 8 de `sqf-standards.md`).
- [ ] **C.5 Persistencia y ciclo JIP**: Las llamadas con bandera `JIP = true` cuentan con registro de JIP ID o limpieza posterior (`remoteExec ["", _jipId]`); los clientes tardíos sincronizan estado desde `initPlayerLocal.sqf`.

### Bloque D: Ciclo de Vida y Limpieza
- [ ] **D.1 Baja obligatoria de handlers y acciones**: Todo manejador (`addEventHandler`, `addMissionEventHandler`) y acción de usuario (`addAction`) cuenta con su correspondiente mecanismo de baja (`removeEventHandler`, `removeMissionEventHandler`, `removeAction`) para evitar fugas al reiniciar o finalizar la misión (Regla 10 de `sqf-standards.md`).
- [ ] **D.2 Control de variables globales y scope**: Cero fugas de variables locales al ámbito global; verificación sistemática de `private` y `params` conforme a la Regla 1 de `sqf-standards.md`.
- [ ] **D.3 Convención de nombres globales**: Nomenclatura conforme a la Regla 3 de `sqf-standards.md` (prefijo `TAG_` o `TAG_fnc_`).
- [ ] **D.4 Orden de inicialización**: Las funciones públicas están compiladas y disponibles antes de que cualquier script o evento remoto las invoque.

### Bloque E: Robustez y Manejo de Errores
- [ ] **E.1 Parámetros tipados con valores por defecto**: Uso de sintaxis extendida de `params` con defaults defensivos y tipos esperados conforme a la Regla 1 de `sqf-standards.md`.
- [ ] **E.2 Validación de límites de arrays y objetos nulos**: Validación de existencia previa con `isNull` y verificación de tamaño antes de acceder a índices mediante `select`.
- [ ] **E.3 Evaluación perezosa defensiva**: Uso de operadores perezosos `&& { ... }` y `|| { ... }` conforme a la Regla 2 de `sqf-standards.md`.
- [ ] **E.4 Integración de frameworks (CBA/ACE3)**: Verificación condicional de frameworks conforme a la sección "Reglas de Framework" de `sqf-standards.md` (respeto estricto del perfil: vanilla sin dependencias no declaradas; PFH y eventos desacoplados si CBA = sí).

### Bloque F: Rendimiento y Scheduler
- [ ] **F.1 Cadencia en bucles periódicos**: Bucles recurrentes gestionados con Per-Frame Handler (`CBA_fnc_addPerFrameHandler` si CBA = sí) o manejador `EachFrame` con delta time si CBA = no; prohibido `spawn { while {true} ... }` sin control de terminación (Reglas 10 y Framework de `sqf-standards.md`).
- [ ] **F.2 Cero compilaciones repetitivas**: Prohibido el uso de `execVM` dentro de bucles o funciones frecuentes; compilación única vía `CfgFunctions` o `compileFinal` (Reglas 4 y 7 de `sqf-standards.md`).
- [ ] **F.3 Inicialización ágil**: `init.sqf`, `initServer.sqf` y funciones `postInit` libres de trabajo pesado bloqueante prolongado para no congelar la pantalla de carga (Regla 5 de `sqf-standards.md`).

### Bloque G: Plan de Pruebas
- [ ] **G.1 Cobertura de escenarios**: Plan de pruebas manual con casos detallados para Servidor Dedicado, Cliente con interfaz, Cliente JIP tardío y desconexión/reconexión de clientes.
- [ ] **G.2 Procedimientos reproducibles**: Cada caso define precondición, acción concreta, resultado esperado y señal inequívoca de fallo.
- [ ] **G.3 Registro de RPT**: Directrices para auditar el log `arma3server.rpt` en busca de errores y advertencias de script.

### Bloque H: Entrega y Empaquetado
- [ ] **H.1 Rutas relativas universales**: Ausencia absoluta de rutas absolutas locales del equipo de desarrollo.
- [ ] **H.2 Dependencias documentadas**: Requisitos de versión y mods declarados expresamente en la documentación y en los archivos de configuración.
- [ ] **H.3 Guía de instalación y uso**: Documentación de despliegue clara y alineada exactamente con el destino del proyecto (Misión vs Addon).

### Bloque I: Honestidad Técnica
- [ ] **I.1 Desglose de estados obligatorio**: El informe final presenta la tabla completa de estados por ítem (`PASA` / `NO PASA` / `NO VERIFICADO`).
- [ ] **I.2 Cero bloqueantes abiertos**: Prohibido declarar "terminado" si existe al menos un ítem obligatorio en `NO PASA`.
- [ ] **I.3 Transparencia de limitaciones**: Las pruebas dinámicas de servidor dedicado se reportan obligatoriamente como `NO VERIFICADO` por limitación del entorno local, sin simular ejecuciones inexistentes.

---

## 3. Sección Diferencial: Misiones (Eden) vs Addons (Mods)

> Para criterios específicos según el tipo de proyecto, consultar [diferencial-misiones-addons.md](file:///skills/arma3-sqf-skill/references/diferencial-misiones-addons.md).
