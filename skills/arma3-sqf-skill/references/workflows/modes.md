# Workflow: Modos de Ejecución y Escalado

Este documento describe el flujo de trabajo operativo según el modo de revisión determinado para el proyecto.

## 1. Modos de Ejecución

El modo de revisión se determina mediante el criterio determinista de `references/invariants.md`:
- **Micro**: Archivo único ≤50 líneas, sin dependencias, sin ciclo de vida, sin red.
- **Estándar**: Multi-archivo (2–3 archivos), o >50 líneas, o ciclo de vida, o señales de red.
- **Completo**: ≥4 archivos o ≥3 módulos, JIP, HC, persistencia, o encargo explícito de auditoría integral.

## 2. Matriz de Participación

La participación de disciplinas según el modo está gobernada por `CANON:PARTICIPACION` en `references/rubrica.md`:
- En **Micro**: Solo análisis estático y verificación de bloqueantes. Cero ceremonia, pero con verificación estricta de invariantes de servidor dedicado.
- En **Estándar**: Se activan las lentes correspondientes a las señales detectadas (Locality si hay red, Performance si hay scheduler, Config si hay CfgRemoteExec).
- En **Completo**: Se ejecutan todas las lentes de auditoría, generación de plan de pruebas y guía de uso.

## 3. Reglas de Escalado

1. **Escalado por Señal**: Si en modo Micro se detecta cualquier señal de red (`remoteExec`, `publicVariable`) o scheduler (`while`, `EachFrame`), el flujo escala automáticamente a **Estándar**.
2. **Escalado por Complejidad**: Si durante el análisis de Estándar se detecta JIP complejo, múltiples máquinas o persistencia, escala a **Completo**.
3. **Fallback Obligatorio**: Si no se dispone de herramientas de análisis determinista en disco, el modo por defecto es `Estándar` con estado `NO VERIFICADO`. Nunca clasificar como Micro manualmente.
