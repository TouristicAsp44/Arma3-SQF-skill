# Lente de Auditoría: Estándar y Buenas Prácticas SQF

<!-- AUTHORED -->
## Disciplina: Calidad de Código y Estándar SQF

Audita la semántica, scope y estándares de escritura contra `references/sqf-standards.md`:
- **Disparadores**: variables sin declaración explícita, `private`, `params`, operadores de igualdad, evaluación perezosa.
- **Scope**: Toda variable local debe recibir scope mediante `params` o `private`. Sin fugas al ámbito exterior.
- **Evaluación perezosa**: `if (a && {b})` solo cuando la condición derecha es computacionalmente costosa o depende de la validez de la izquierda.
- **Micro-optimizaciones**: Preferir `isEqualTo` sobre `==` en tipos complejos. Usar `findIf` en lugar de bucles de búsqueda manual.
- **Inmutabilidad**: Funciones críticas precompiladas deben declararse con `compileFinal`.
<!-- /AUTHORED -->

### Invariantes normativos aplicables

<!-- CANON-EXTRACT:BLOQUEANTES -->
1. **Errores de sintaxis SQF**
<!-- /CANON-EXTRACT:BLOQUEANTES -->
