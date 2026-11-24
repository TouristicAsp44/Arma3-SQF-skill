# Lente de Auditoría: Locality y Multijugador

<!-- AUTHORED -->
## Disciplina: Locality, Red y Multijugador

Audita la localidad de ejecución, paso de mensajes y estabilidad en servidor dedicado para Arma 3:
- **Disparadores**: `remoteExec`, `remoteExecCall`, `publicVariable`, `publicVariableServer`, `publicVariableClient`, `addPublicVariableEventHandler`, `isDedicated`, `isServer`, `hasInterface`, `HeadlessClient`, `setOwner`.
- **Hechos BIKI**: Contrasta argumentos y efectos contra la matriz oficial `a3ref` (`locality.argument` AL/AG, `locality.effect` EL/EG). Comandos con efecto global (EG) no deben difundirse vía broadcast `remoteExec 0`. Comandos con argumento local (AL) ejecutados sobre entidades remotas fallan silenciosamente.
- **Dedicado**: Prohibido usar `player` o comandos UI en rutas del servidor (`Arma3Server.exe`).
- **JIP**: Toda llamada remota persistente debe almacenar su ID y limpiarse con `remoteExec ["", _jipId]`.
<!-- /AUTHORED -->

### Invariantes normativos aplicables

<!-- CANON-EXTRACT:BLOQUEANTES -->
3. **Violaciones críticas de dedicado**
<!-- /CANON-EXTRACT:BLOQUEANTES -->

<!-- CANON-EXTRACT:PRECEDENCIA -->
1. Correctitud de red y estabilidad en servidor dedicado (locality, desync, softlock, JIP).
2. Rendimiento y scheduler.
3. Estilo y legibilidad.

Una optimización de rendimiento **JAMÁS** se aplica si compromete la estabilidad o la localidad. Ante un conflicto entre hallazgos, prevalece la categoría de mayor precedencia, y el hallazgo subordinado se reporta como `Sugerencia`, no como `Bloqueante`.
<!-- /CANON-EXTRACT:PRECEDENCIA -->
