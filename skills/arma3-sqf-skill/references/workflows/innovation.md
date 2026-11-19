# Workflow: Innovación y Diseño de Mecánicas SQF

Este documento establece el proceso para proponer mecánicas viables en Arma 3 para servidor dedicado antes de escribir código.

## 1. Filtros de Viabilidad Técnica

Toda nueva mecánica propuesta debe pasar por cuatro filtros antes de considerarse viable:
1. **Filtro de Localidad y Red**: ¿Qué máquina posee la autoridad sobre los datos? ¿Cuántos bytes por segundo generará? ¿Provocará congestión o desincronización?
2. **Filtro de Scheduler y Coste por Frame**: ¿Requiere ejecución por frame o bucles continuos? ¿Puede desacoplarse a eventos bajo demanda?
3. **Filtro de Persistencia y JIP**: ¿Cómo afectará a un jugador que entra cuando la misión ya ha comenzado? ¿Requiere sincronización de estado complejo?
4. **Filtro de Entorno Dedicado**: ¿Funciona de forma idéntica en un servidor headless sin renderizado ni jugador local?

## 2. Separación de Conceptos

- **Propuesta conceptual**: Explicación de la experiencia de juego buscada.
- **Implementación técnica preliminar**: Comandos necesarios, estructura de datos y verificación de localidad.
- **Riesgos y mitigaciones**: Puntos de fallo potenciales en multijugador con alta latencia.
