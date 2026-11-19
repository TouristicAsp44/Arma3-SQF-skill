---
description: Fuente canónica única de las reglas normativas de revisión SQF (Arma 3). contiene las 7 categorías de BLOQUEANTE, la Puerta de Calidad, el principio de honestidad técnica, los criterios de modo, la precedencia de conflictos y la propiedad de reglas.
---

# Invariantes SQF — Arma 3 (fuente canónica)

Este documento es la **única fuente canónica** de las reglas normativas de
revisión de esta skill. Cualquier otro artefacto (lentes, workflows,
adaptadores por host, paquetes inline) puede citarlo o resumirlo, pero no
puede redefinirlo.

## Propiedad de documentos canónicos

| Documento canónico | Anclas | Reglas que posee |
| :--- | :--- | :--- |
| `references/invariants.md` (este) | `CANON:BLOQUEANTES`, `CANON:PUERTA`, `CANON:HONESTIDAD`, `CANON:MODOS`, `CANON:PRECEDENCIA`, `CANON:PROPIEDAD` | Criterios de revisión: qué es bloqueante, cuándo se entrega, cómo se escala de modo, qué hallazgo reporta cada disciplina. |
| `references/sqf-standards.md` | `CANON:ESTANDAR` | Reglas de **escritura** de código SQF (scope, nomenclatura, cabeceras, framework). |
| `references/rubrica.md` | `CANON:RUBRICA`, `CANON:PARTICIPACION` | Rúbrica de severidad y matriz de participación por modo. |

La propiedad es **disjunta**: ninguna regla se define en dos documentos
canónicos. Un resumen (N2) solo puede existir dentro de una región marcada
`CANON-EXTRACT`, y una definición completa (N3) solo dentro del documento
canónico que la posee.

## Niveles de contenido normativo

| Nivel | Tipo | Longitud máxima | Dónde se permite | Verificación |
| :--- | :--- | :---: | :--- | :--- |
| **N1** | Índice (título de la categoría) | ≤ 25 tokens por línea | Capa 0, extractos, paquetes inline | Conteo exacto de menciones |
| **N2** | Resumen (criterio + excepción en una frase) | ≤ 60 tokens por ítem | Solo en regiones `<!-- CANON-EXTRACT:* -->` y paquetes inline | Hash contra el canónico |
| **N3** | Definición normativa completa | Texto completo | **Exclusivamente** en el documento canónico que la posee | Falla si aparece en otro archivo |

---

<!-- CANON:BLOQUEANTES -->
## Definición precisa de Bloqueante (P0)

Esta es la ÚNICA definición normativa. No la dupliques en otra sección; refiérela.

1. **Errores de sintaxis SQF**: errores detectados determinísticamente por `references/run_sqflint.py` (exit code 1) **o variables locales fugadas al scope exterior sin `private`/`params`**. (Nota: comandos no reconocidos por sqflint se tratan como Sugerencia/Pista a confirmar contra el Biki antes de tratarlos como error. Un warning de scope de sqflint cuenta como BLOQUEANTE, no como sugerencia.)
2. **Softlocks potenciales, bucles infinitos o bloqueos de init**: `waitUntil` sin condición alcanzable garantizada ni timeout de seguridad, bucles infinitos sin cadencia (`while {true}` sin suspensión o PFH), retrasos bloqueantes prolongados (`sleep`/`uiSleep`/`waitUntil`) en el hilo principal de scripts de inicialización (`init.sqf`, `initServer.sqf`, `postInit`) que congelan la carga de la misión (deben delegarse a `spawn` desacoplado o PFH), o esperas cruzadas cliente-servidor donde un nodo espera indefinidamente una variable nunca emitida.
3. **Violaciones críticas de dedicado**: uso de `player` o `waitUntil {!isNull player}` en servidor dedicado (`isDedicated == true`), donde `player` es permanentemente `objNull`; **o ejecución de comandos de interfaz UI (`hint`, `hintC`, `titleText`, `cutText`, `dialog`, `createDialog`, `ctrlCreate`, `displayCtrl`, `findDisplay`, `uiNamespace`, `ppEffect`) en cualquier ruta que pueda ejecutarse en el servidor** — una guarda `if (hasInterface)` NO lo legitima: solo evita el error, no el trabajo inútil. La retroalimentación visual va por `remoteExec` al cliente.
4. **Suspensión en contexto unscheduled**: `sleep`, `uiSleep` o `waitUntil` donde `canSuspend == false` (`preInit` con `preInit = 1`, Event Handlers del motor, `remoteExecCall`, o código invocado desde un contexto unscheduled). **Ambos** (`sleep` y `uiSleep`) requieren obligatoriamente entorno scheduled.
5. **Violaciones de whitelist en `CfgRemoteExec`**: invocaciones remotas (`remoteExec`, `remoteExecCall`) de funciones ausentes de la lista blanca de `CfgRemoteExec >> Functions` cuando `mode = 1`.
6. **Contratos de interfaz rotos o parámetros incompatibles**: discrepancias en cantidad, orden o tipos de datos requeridos en `params` entre módulos o llamadas de función.
7. **Inyección no permitida de dependencias de framework**: uso de funciones o identificadores de CBA o ACE3 (`CBA_fnc_*`, `ace_*`) cuando el perfil del proyecto declara `CBA: no` o `ACE3: no`.
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

El modo de revisión (`Micro`, `Estándar`, `Completo`) se determina **obligatoriamente** mediante el script determinista:

```
python scripts/sqf_orchestrator.py --root <raíz del proyecto> --mode-query
```

Códigos de salida: `0` = cálculo exitoso, `1` = error duro de ruta o argumentos, `10` = completado con `NO VERIFICADO`.

| Modo | Criterio determinista |
| :--- | :--- |
| Sin flujo | Typo, ajuste de un valor puntual, pregunta conceptual |
| **Micro** | Exactamente 1 archivo `.sqf` aislado, ≤50 líneas, sin dependencias externas, sin archivos de ciclo de vida (`init*.sqf`, `description.ext`), sin señales de red ni scheduler |
| **Estándar** | Proyecto multi-archivo (2–3 archivos), o >50 líneas, o ciclo de vida de misión, o señales de red (`remoteExec`, `publicVariable`), o modificación de código con red |
| **Completo** | ≥4 archivos o ≥3 módulos, JIP, Headless Client, persistencia, o encargo explícito de auditoría completa |

**Inventario vacío:** si el script devuelve `NO VERIFICADO` por inventario vacío (cero archivos `.sqf`), **el modo no se decide y hay que preguntar la ruta**. Un modo nunca se concede por defecto ante un inventario vacío; un resultado vacío no es un resultado limpio ni es Micro.

**Fallback obligatorio:** si el script no está disponible o falla por causas del entorno, el modo por defecto es `Estándar` y se declara `NO VERIFICADO` en el informe; **NUNCA se clasifica como Micro por criterio manual**.

**Override:** si el usuario pide explícitamente un modo, se le pasa `--mode <modo>` al orquestador para no re-escalar (salvo Micro con señales de red: avisar del riesgo técnico y escalar).

**Escalado por señal:** cualquier señal de red o scheduler detectada escala Micro → Estándar.
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

Cada tema tiene un **dueño único**. Un revisor que detecta algo ajeno lo anota en una línea: "derivado a \<dueño\>", y no lo re-reporta.

| Tema | Dueño único |
| :--- | :--- |
| Propuesta y viabilidad de mecánicas nuevas (filtros red/frame/JIP/dedicado) | innovator |
| Sintaxis, variable sin `private` (detectable por linter) | static-analyzer |
| Scope/`private`/`params` si el linter no está disponible | best-practices |
| Evaluación perezosa, nomenclatura, tags de globales locales, compileFinal, micro-optimizaciones de sintaxis (`findIf`, `isEqualTo`, `getVariable` con default) | best-practices |
| remoteExec, JIP, publicVariable (tag y frecuencia), sleep/uiSleep/waitUntil, HC, softlocks | locality |
| Coste en ejecución: scheduler, bucles, handlers por frame, escaneos globales, estructuras de datos, fugas de scripts/EH/grupos/objetos, reparto servidor/HC | performance-auditor |
| CfgRemoteExec, CfgFunctions, init, allowFunctionsRecompile | config-auditor (hechos) |
| Diseño de módulos e interfaces | architect |
| Guía de uso | doc-writer |
<!-- /CANON:PROPIEDAD -->

---

## Invariantes de servidor dedicado (headless)

Este producto corre en un servidor dedicado (`Arma3Server.exe`): sin interfaz, sin jugador local, `player` es `objNull`. La máquina local es un entorno de prueba, nunca la especificación.

- **Interfaz prohibida en rutas de servidor.** `hint`, `hintC`, `titleText`, `cutText`, `dialog`, `createDialog`, `ctrlCreate`, `displayCtrl`, `findDisplay`, `uiNamespace`, `ppEffect` y afines no se usan en ninguna ruta que pueda ejecutarse en el servidor. **Una guarda `if (hasInterface)` no las legitima**: la guarda solo evita el error, no el trabajo inútil. Si hace falta retroalimentación visual, va por `remoteExec` al cliente.
- **`player` no existe en el servidor.** `player` es `objNull` permanentemente en dedicado. Si la lógica necesita al jugador, va en `initPlayerLocal.sqf` o por `remoteExec` dirigido a su `owner`.
- **Diagnóstico por `diag_log`**, no con `systemChat` ni `format` hacia `player` (invisibles en dedicado).
- **Banderas de localidad:** `isServer` (servidor o host), `isDedicated` (dedicado sin interfaz), `hasInterface` (máquina con jugador). No las confundas: un `if (isDedicated)` donde debía ir `if (isServer)` rompe el hosted.
- **Sin esperas bloqueantes en el arranque.** `sleep`, `uiSleep` y `waitUntil` en `init.sqf`, `initServer.sqf` o `postInit` retienen el hilo de inicialización. Delega a `spawn` desacoplado o Per-Frame Handler.

## Perfil del Proyecto (7 parámetros)

Se declara **una sola vez** al inicio de la sesión. Los turnos posteriores refieren "perfil declarado" y no repiten el bloque.

| Parámetro | Valores |
| :--- | :--- |
| `ARMA_VERSION` | p. ej. `2.22` |
| `DESTINO` | `mision` \| `addon` |
| `CBA` | `sí (v3.19.0)` \| `no` |
| `ACE3` | `sí (v3.21.2)` \| `no` |
| `SERVIDOR_DEDICADO` | ruta \| `no` |
| `SQFLINT` | ruta \| `no` |
| `MODO` | `Micro` \| `Estándar` \| `Completo` |

Si el perfil no está declarado, los ítems que dependen de él se reportan `NO VERIFICADO`.

## Verificación de comandos contra la BIKI

La fuente primaria obligatoria es la réplica local `a3ref` (`scripts/sqf_wiki_reader.py`). La caché (`references/wiki-cache.md`) **NO es evidencia sin procedencia**: todo comando se contrasta contra `a3ref` antes de afirmar nada. La búsqueda web es fallback secundario y únicamente cuando el comando no está en la réplica local y existe herramienta de búsqueda activa. Si un comando no está ni en la réplica ni en la web, queda `NO VERIFICADO` — prohibido terminantemente usar comandos de memoria.

---

## Contrato de esquema del informe

El esquema del informe emitido por el motor y esperado por los consumidores está versionado:

`REPORT_SCHEMA_VERSION = 1`

Toda salida de análisis debe respetar el contrato especificado en `references/report_format.md`.

---

## Paquete Inline P1–P4 (hosts degradados)

Para entornos sin sistema de archivos directo (ChatGPT Custom GPT, Gemini), las instrucciones del sistema deben incluir el paquete autocontenido de reglas:

- **P1 — Núcleo normativo (N1 + Puerta + Honestidad)**: Las 7 categorías por título de una línea, la regla de puerta de calidad infranqueable (cero bloqueantes para entregar) y el principio de honestidad técnica (`NO VERIFICADO` sin linter ni wiki).
- **P2 — Fallback de modo**: Ante la ausencia del script determinista, el modo por defecto es `Estándar` con estado `NO VERIFICADO`. Prohibido conceder `Micro` por criterio manual.
- **P3 — Checklist priorizado por ítem (N2)**: Preguntas de comprobación para las 7 categorías de bloqueante. Si el espacio de instrucciones es limitado, se recortan sugerencias pero jamás las 7 categorías normativas.
- **P4 — Formato de informe estructurado**: Formato de una línea `[BLOQUEANTE|SUGERENCIA|NO_VERIFICADO] archivo:linea (disciplina): descripcion` y línea de cierre `RESUMEN: bloqueantes=N; sugerencias=N; no_verificado=N`.
