# Workflow: Implementación de Módulos SQF

Este documento guía el desarrollo de código SQF cumpliendo con los estándares de calidad del equipo.

## 1. Reglas de Implementación

1. **Cumplimiento estricto del estándar**: Seguir `references/sqf-standards.md` en nomenclatura, scopes, cabeceras y control de flujo.
2. **Invariantes de servidor dedicado**:
   - Nunca asumir que `player` existe en rutas de ejecución del servidor.
   - Diagnósticos únicamente con `diag_log`.
   - Sin llamadas a la interfaz de usuario en el servidor.
3. **Control de ámbito**:
   - Toda función inicia con declaración explícita de parámetros mediante `params` tipados con valores por defecto.
   - Toda variable local debe declararse con `private`.
4. **Manejo de concurrencia y scheduler**:
   - Comprobar `canSuspend` antes de invocar `sleep` o `waitUntil`.
   - Si se requiere suspensión en contextos unscheduled (como Event Handlers), desacoplar la ejecución mediante `spawn` o utilizar Per-Frame Handlers si CBA está habilitado.
5. **Fronteras modulares**:
   - No acceder directamente a variables internas de otros módulos; utilizar funciones de interfaz expuestas.
