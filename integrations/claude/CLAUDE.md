<!-- GENERATED FROM: skills/arma3-sqf-skill/references/invariants.md | DO NOT EDIT -->
# Guía de Uso para Claude Code — arma3-sqf-skill

<!-- AUTHORED -->
## Cómo usar esta skill en Claude Code

Claude Code cuenta con acceso completo a herramientas de lectura de archivos y ejecución de terminal en este repositorio.

### Activación e Invocación
1. Cuando el usuario solicite revisar, crear o auditar código SQF de Arma 3, lee primero el punto de entrada unificado:
   `skills/arma3-sqf-skill/SKILL.md`
2. Todas las rutas de archivos dentro de la skill son relativas a la raíz del repositorio (`skills/arma3-sqf-skill/`).
3. Para consultar reglas específicas por disciplina, lee la lente correspondiente bajo demanda:
   - `skills/arma3-sqf-skill/references/lens-locality.md` (red, JIP, dedicado)
   - `skills/arma3-sqf-skill/references/lens-performance.md` (scheduler, bucles, PFH)
   - `skills/arma3-sqf-skill/references/lens-best-practices.md` (scope, nomenclatura)
   - `skills/arma3-sqf-skill/references/lens-architect.md` (diseño, contratos)
   - `skills/arma3-sqf-skill/references/lens-config.md` (CfgRemoteExec, description.ext)
   - `skills/arma3-sqf-skill/references/lens-claims.md` (verificación BIKI)

### Ejecución de Herramientas Locales
- Determinación de modo de análisis:
  `python skills/arma3-sqf-skill/scripts/sqf_orchestrator.py --root <ruta_proyecto> --mode-query`
- Análisis estático determinista (sqflint):
  `python skills/arma3-sqf-skill/scripts/sqf_orchestrator.py --lint <archivo.sqf>`
- Consulta de sintaxis y comandos BIKI (a3ref / SQLite FTS5):
  `python skills/arma3-sqf-skill/scripts/sqf_wiki_reader.py --symbol <comando>`
<!-- /AUTHORED -->

### Invariantes Normativos Obligatorios

<!-- CANON-EXTRACT:PUERTA -->
## Puerta de Calidad Infranqueable

- El conteo de bloqueantes y la lista de `archivo:línea` provienen directamente del informe estructurado emitido por `sqf_orchestrator.py --lint` (`RESUMEN: bloqueantes=N...`) y de los revisores semánticos.
- Si tras **3 iteraciones** todavía queda **AL MENOS UN BLOQUEANTE** abierto:
  1. **DETENER** el proceso de forma inmediata.
  2. **INFORMAR AL USUARIO** con el desglose exacto de cada bloqueante sin resolver (disciplina detector, archivo, línea, causa raíz e intentos fallidos extraídos del informe).
  3. **PROHIBIDO DECLARAR "TERMINADO" O ENTREGAR COMO FINAL**. El resultado se marca como `DETENIDO (NO PASA)` y se solicita intervención humana. Se elimina cualquier cláusula de entrega permisiva; código con bloqueantes jamás se entrega como terminado.
- Solo se avanza a Plan de prueba, Documentación y Entrega si el número de bloqueantes abiertos es **CERO**.
- **Regla del ciclo**: solo los defectos **Bloqueantes** reinician el ciclo de corrección (máx. 3 iteraciones, orden locality → performance → best-practices).
<!-- /CANON-EXTRACT:PUERTA -->

<!-- CANON-EXTRACT:HONESTIDAD -->
## Principio de Honestidad Técnica (Invariante de Entorno)

- Lo no ejecutado en servidor dedicado se reporta **NO VERIFICADO**; nunca se declara completo.
- Si `sqflint` no está disponible (`SQFLINT_NO_DISPONIBLE`), el análisis estático se reporta obligatoriamente como `NO VERIFICADO` (JAMÁS como `PASA`).
- Los ítems correspondientes a ejecución real en servidor dedicado se marcan `NO VERIFICADO` **salvo que el Perfil del Proyecto declare que el entorno existe y se haya ejecutado en esta máquina, en esta sesión**.
- Si el wiki lookup no pudo ejecutarse (réplica `a3ref` ausente → estado `SIN_REPLICA`), toda afirmación técnica dependiente de la BIKI queda `NO VERIFICADO`, nunca `PASA`.
- Estados formales permitidos por ítem: `PASA`, `NO PASA`, `NO VERIFICADO` y `NO APLICA` únicamente si el componente no aplica al modo.
- Prohibido presentar como `PASA` cualquier ítem que no se haya comprobado con una fuente primaria.
<!-- /CANON-EXTRACT:HONESTIDAD -->
