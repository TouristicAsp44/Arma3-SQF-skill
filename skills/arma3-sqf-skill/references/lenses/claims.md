# Lente de Auditoría: Verificación Documental contra BIKI

<!-- AUTHORED -->
## Disciplina: Verificación Documental y Procedencia

Audita la certeza de los comandos y dependencias externas:
- **Disparadores**: comandos SQF dudosos, sintaxis de versiones específicas, dependencias CBA/ACE3.
- **Réplica oficial y camino rápido**: Toda afirmación sobre firmas, tipos y localidad debe contrastarse contra la réplica local `a3ref` (`scripts/sqf_wiki_reader.py`), utilizando la base de datos SQLite indexada (`arma3_wiki.db`) para resolución sub-milisegundo cuando esté disponible.
- **Procedencia dinámica obligatoria**: Todo veredicto o cita documental debe incorporar el commit SHA dinámico obtenido en tiempo de ejecución (`--sha`), el `revid` del registro y la URL canónica oficial (`https://community.bistudio.com/wiki/...`).
- **Principio de Prevalencia de la Fuente Primaria**: La réplica local estructurada `a3ref` prevalece sobre la web o memorias externas. Si un término no figura en la réplica local, la búsqueda web opera únicamente como fallback secundario si existe conectividad.
- **Clasificación de certeza**: Clasificar en `confirmada` (respaldo directo con URL, revid y SHA), `probable` (deducción técnica fundada en arquitectura del motor) o `especulativa` (hipótesis sin respaldo documental que no habilitan salidas).
- **Estado de réplica**: Si la réplica no está disponible (`SIN_REPLICA`), el resultado se reporta obligatoriamente como `NO VERIFICADO`.
- **Frameworks**: Si el perfil declara `CBA: no` o `ACE3: no`, cualquier uso de `CBA_fnc_*` o macros CBA es bloqueante.
<!-- /AUTHORED -->

### Invariantes normativos aplicables

<!-- CANON-EXTRACT:BLOQUEANTES -->
7. **Inyección no permitida de dependencias de framework**: uso de funciones o identificadores de CBA o ACE3 (`CBA_fnc_*`, `ace_*`) cuando el perfil del proyecto declara `CBA: no` o `ACE3: no`.
<!-- /CANON-EXTRACT:BLOQUEANTES -->
