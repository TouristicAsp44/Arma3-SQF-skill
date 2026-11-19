# Workflow: Redacción de Guía de Uso y Documentación

Este documento establece la estructura y criterios para redactar la documentación técnica y de usuario de scripts y módulos SQF terminados.

## 1. Principio Fundamental

Solo documentar lo que el código **realmente implementa y verifica**. Prohibido describir características hipotéticas o no comprobadas.

## 2. Estructura de la Documentación (README / Guía de Módulo)

1. **Resumen ejecutivo**: Propósito del módulo o script, versión y compatibilidad (misión o addon).
2. **Requisitos y dependencias**: Versión de Arma 3 requerida, compatibilidad con CBA/ACE3, necesidad de servidor dedicado o Headless Client.
3. **Instalación e integración**:
   - Para misiones: estructura de carpetas en la misión, inclusión en `description.ext` o `initServer.sqf`.
   - Para addons: configuración en `CfgPatches` y `CfgFunctions`.
4. **Contrato de API pública**:
   - Nombre de funciones y parámetros con sus tipos SQF.
   - Valores de retorno y efectos colaterales.
   - Máquina de ejecución esperada (servidor, cliente, broadcast).
5. **Comportamiento Multijugador y JIP**:
   - Cómo se sincroniza el estado inicial.
   - Manejo de desconexiones y reconexiones.
6. **Solución de problemas**:
   - Mensajes diagnósticos emitidos en el archivo `.rpt` mediante `diag_log`.
   - Errores comunes de configuración o whitelist en `CfgRemoteExec`.
