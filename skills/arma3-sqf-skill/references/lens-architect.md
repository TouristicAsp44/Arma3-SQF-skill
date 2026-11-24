# Lente de Auditoría: Arquitectura y Contratos de Interfaces

<!-- AUTHORED -->
## Disciplina: Arquitectura y Contratos de Módulos

Audita el desacoplamiento, paso de parámetros y fronteras modulares:
- **Disparadores**: llamadas entre funciones, contratos `params`, estado compartido, namespaces globales.
- **Contratos de parámetros**: Toda función pública debe validar la cantidad, orden y tipo de sus parámetros vía `params`.
- **Estado compartido**: El estado debe aislarse en variables de espacio de nombres controlado (`setVariable` / hash maps de módulo), evitando variables globales dispersas sin prefijo del proyecto.
<!-- /AUTHORED -->

### Invariantes normativos aplicables

<!-- CANON-EXTRACT:BLOQUEANTES -->
6. **Contratos de interfaz rotos o parámetros incompatibles**
<!-- /CANON-EXTRACT:BLOQUEANTES -->
