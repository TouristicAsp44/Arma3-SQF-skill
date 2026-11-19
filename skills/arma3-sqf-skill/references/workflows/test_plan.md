# Workflow: Plan de Pruebas en Servidor Dedicado

Este documento guía la generación del plan de pruebas manuales y verificación funcional en servidor dedicado.

## 1. Objetivo del Plan de Pruebas

Convertir los riesgos de concurrencia, red y scheduler detectados durante la auditoría estática en un conjunto concreto y reproducible de pruebas en entorno multi-máquina:
- Servidor dedicado (`Arma3Server.exe`).
- Clientes conectados simultáneamente.
- Jugadores que entran en progreso (JIP - Join in Progress).
- Headless Client (HC) si la misión lo utiliza.

## 2. Estructura del Caso de Prueba

Cada caso de prueba debe especificar:
1. **Identificador y Título**: `TEST-LOC-01`, etc.
2. **Entorno requerido**: Servidor dedicado + N clientes + HC opcional.
3. **Condiciones previas**: Estado de la misión, variables iniciales, ubicación de unidades.
4. **Paso a paso**: Acciones precisas en cada nodo cliente y servidor.
5. **Resultado esperado**: Qué debe ocurrir en la pantalla del cliente y qué debe registrarse en `Arma3Server.rpt` vía `diag_log`.
6. **Criterio de fallo**: Indicadores de desincronización, fallos de locality o congelamiento.

## 3. Pruebas Críticas Obligatorias

- **Prueba JIP**: Un cliente se conecta tras haberse ejecutado la lógica inicial; verificar que recibe el estado correcto sin duplicación de handlers ni variables corruptas.
- **Prueba de Ownership**: Cambio de propietario de un vehículo o unidad (`setOwner`); verificar que los comandos de argumento local siguen respondiendo en la máquina correcta.
- **Prueba de Carga del Scheduler**: Observar los FPS del servidor durante la ejecución concurrente para descartar caídas bruscas de rendimiento.
