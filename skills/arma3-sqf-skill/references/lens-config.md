# Lente de Auditoría: Configuración y Ciclo de Vida

<!-- AUTHORED -->
## Disciplina: Configuración de Misión y Addon

Audita las declaraciones de motor y ciclo de vida:
- **Disparadores**: `description.ext`, `config.cpp`, `CfgRemoteExec`, `CfgFunctions`, `CfgPatches`, `init.sqf`, `initServer.sqf`.
- **CfgRemoteExec**: Cuando `mode = 1`, toda función invocada por `remoteExec` o `remoteExecCall` debe figurar en la whitelist `CfgRemoteExec >> Functions`.
- **CfgFunctions**: Orden y jerarquía de inicialización (`preInit`, `postInit`). Prohibido suspender (`sleep`/`waitUntil`) en funciones con `preInit = 1`.
- **Diferencial Misión vs Addon**: Contrastar contra `references/diferencial-misiones-addons.md`.
<!-- /AUTHORED -->

### Invariantes normativos aplicables

<!-- CANON-EXTRACT:BLOQUEANTES -->
5. **Violaciones de whitelist en `CfgRemoteExec`**
<!-- /CANON-EXTRACT:BLOQUEANTES -->
