# Lente de Auditoría: Rendimiento y Scheduler

<!-- AUTHORED -->
## Disciplina: Rendimiento y Scheduler

Audita el impacto de ejecución a escala (jugadores, IA, entidades):
- **Disparadores**: `while`, `waitUntil`, `EachFrame`, `onEachFrame`, `Draw3D`, `allUnits`, `allGroups`, `allMissionObjects`, `nearestObjects`, `nearEntities`, `spawn`, `execVM`.
- **Scheduler**: Verificar cadencia de `sleep`/`uiSleep`. Prohibidos bucles infinitos no controlados sin suspensión. En inicialización (`init*.sqf`, `postInit`), evitar esperas prolongadas en el hilo principal.
- **Por frame**: Handlers de alta frecuencia (`EachFrame`) no deben realizar escaneos globales, `format` continuo ni iteraciones pesadas.
- **Colecciones**: Reemplazar `_a = _a + [x]` por `pushBack`. Usar `createHashMap` para búsquedas en colecciones grandes. Evitar `forEach` anidados con complejidad cuadrática.
- **Fugas**: Toda entidad, grupo o handler creado debe tener mecanismo de limpieza (`deleteVehicle`, `deleteGroup`, `removeEventHandler`).
<!-- /AUTHORED -->

### Invariantes normativos aplicables

<!-- CANON-EXTRACT:BLOQUEANTES -->
2. **Softlocks potenciales, bucles infinitos o bloqueos de init**
<!-- /CANON-EXTRACT:BLOQUEANTES -->

<!-- CANON-EXTRACT:PRECEDENCIA -->
1. Correctitud de red y estabilidad en servidor dedicado (locality, desync, softlock, JIP).
2. Rendimiento y scheduler.
3. Estilo y legibilidad.

Una optimización de rendimiento **JAMÁS** se aplica si compromete la estabilidad o la localidad. Ante un conflicto entre hallazgos, prevalece la categoría de mayor precedencia, y el hallazgo subordinado se reporta como `Sugerencia`, no como `Bloqueante`.
<!-- /CANON-EXTRACT:PRECEDENCIA -->
