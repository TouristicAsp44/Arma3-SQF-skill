================================================================================
INSTRUCCIONES PARA MEJORAR, ACTUALIZAR Y OPTIMIZAR LA PLANEACIÓN (v2.4 → v2.5)
================================================================================

CONTEXTO: el Plan v2.4 cerró los 12 puntos de la revisión anterior (niveles
N1/N2/N3, CANON vs CANON-EXTRACT, `check.py --fase`, paquete inline P1–P4,
veredictos DETECTADO/NO_VERIFICADO/SILENCIO/FALSO_PASA, `contexto_cargado`,
`evals/runs/` en .gitignore, DoD con "Aplicable desde", skill EN medida,
riesgos nuevos). NO se repiten.

Esta ronda tiene dos novedades:
  (1) el repositorio YA CAMBIÓ: PR-1 está parcialmente ejecutado. El plan
      asume un estado que ya no es cierto, y hay divergencias entre lo
      ejecutado y lo planificado (sección ESTADO DE EJECUCIÓN).
  (2) el plan define el contrato del informe v1 SIN consultar el código que
      lo produce: el formato real lleva prefijo de severidad y hay DOS
      formatos de `RESUMEN:` distintos en el mismo motor. Verificado en
      `skills/arma3-sqf-skill/scripts/sqf_models.py`.

VERIFICADO en esta ronda (lectura directa del repo):
  - `skills/arma3-sqf-skill/scripts/sqf_models.py:307`
      `lines.append(f"[{f.severity}] {f.file}:{f.line} ({f.discipline}): {f.description}")`
    → el formato real es `[BLOQUEANTE] archivo:linea (disciplina): descripcion`
    (CON prefijo de severidad). El plan v2.4 lo define SIN prefijo.
  - `sqf_models.py:318`
      `RESUMEN: bloqueantes={n}; sugerencias={n}; no_verificado={n}`  (informe de hallazgos)
  - `sqf_models.py:328`
      `RESUMEN: modo={modo}; escalado={si|no}`  (consulta de modo) → SEGUNDO RESUMEN
      con esquema distinto, en el mismo motor y en la misma salida de `--mode-query`.
  - El script NO emite `REPORT_SCHEMA_VERSION` en ninguna parte.
  - `format_findings_report` vive en `sqf_models.py`, NO en `sqf_orchestrator.py`.
  - `.gitignore` NO contiene `evals/runs/` (1.n-bis pendiente).
  - No existen `scripts/check.py` ni `scripts/measure_tokens.py`.
  - No existe `references/invariants.md` (1.g-bis, la tarea bloqueante, pendiente).
  - `skills/arma3-sqf-skill/SKILL.md` sigue siendo el original (~30 KB).
  - Coexisten `agents/` (11 .md) y `legacy/agents/` (11 .md): la migración de
    1.e se ejecutó como COPIA, no como movimiento.
  - Sigue existiendo `rules/AGENTS.md` (1.f pendiente).
  - El fichero real es `references/diferencial-misiones-addons.md` (plural);
    el plan lo llama `diferencial-mision-addon.md` (singular).

================================================================================
PARTE A — CONTRATO DEL INFORME (lo que el plan define mal)
================================================================================

A.1 EL FORMATO DE LÍNEA ESPECIFICADO NO ES EL QUE EMITE EL CÓDIGO (gravedad: BLOQUEANTE)
--------------------------------------------------------------------------------
Plan v2.4, 2.f: "Formato de línea: `archivo:linea (disciplina): descripcion`".
Código real (`sqf_models.py:307`): `[SEVERIDAD] archivo:linea (disciplina): descripcion`.
Diferencia: el prefijo `[BLOQUEANTE]` / `[SUGERENCIA]` / `[NO_VERIFICADO]`.
Consecuencia: si `references/report_format.md` se escribe tal como dice el
plan, el prompt (que dice "responde SIEMPRE con el formato v1")ENUERA un
formato que el script no produce, y el matcher del harness (M1/M2/M3) no
encontrará las líneas que espera → las métricas darían 0 detecciones y el
fallo se atribuiría a la skill en vez de al contrato.
CORRECCIÓN: `report_format.md` v1 debe declarar LITERALMENTE el formato real:
  `[BLOQUEANTE|SUGERENCIA|NO_VERIFICADO] archivo:linea (disciplina): descripcion`
y añadir el test que lo verifica contra la salida real (ver A.4).

A.2 HAY DOS FORMATOS DE `RESUMEN:` Y EL PLAN NO LOS DISTINGUE (gravedad: alta)
--------------------------------------------------------------------------------
El motor emite:
  - Informe de hallazgos: `RESUMEN: bloqueantes=N; sugerencias=N; no_verificado=N`
  - Consulta de modo:     `RESUMEN: modo=Micro|Estándar|Completo; escalado=si|no`
Ambos en la salida del mismo ejecutable (`--lint` vs `--mode-query`).
El plan solo dice "sección `RESUMEN:` obligatoria" y DoD #19 exige
"`REPORT_SCHEMA_VERSION=1` + `RESUMEN:` + formato de línea" sin decir cuál.
Un matcher que busque `RESUMEN:`Finderá dos formatos; un lector que copie el
RESUMEN de modo como si fuera el de hallazgos publicará un informe corrupto.
CORRECCIÓN: `report_format.md` v1 define DOS documentos con nombres y
anclas explícitos:
  - INFORME DE HALLAZGOS (v1): líneas `[SEV] archivo:linea (disciplina): desc`
    + `RESUMEN: bloqueantes=N; sugerencias=N; no_verificado=N`
  - INFORME DE MODO (v1): `MODO: ...` + `MOTIVO: ...` + `RESUMEN: modo=...; escalado=...`
Y el matcher consume SOLO el informe de hallazgos, identificándolo por la
presencia de `bloqueantes=` en la línea RESUMEN. Sin esa regla, M1/M2/M3
pueden puntuar una traza equivocada.

A.3 `REPORT_SCHEMA_VERSION` ES UNA DECLARACIÓN QUE NADIE IMPLEMENTA (gravedad: alta)
--------------------------------------------------------------------------------
El plan declara `REPORT_SCHEMA_VERSION = 1` en `invariants.md` (2.c),
`report_format.md` (2.f), en la respuesta de `sqf_review` (6.a) y en el DoD
#19. Pero el código no lo emite: no hay ninguna tarea que modifique
`sqf_models.py` para incluirlo en la salida. El contrato queda declarado en
documentación y ausente en el emisor → el DoD #19 no es verificable.
CORRECCIÓN: nueva tarea **2.f-cua**:
  - Modificar `format_findings_report()` en `skills/arma3-sqf-skill/scripts/sqf_models.py`
    para emitir la línea `REPORT_SCHEMA_VERSION: 1` (o `REPORT_SCHEMA_VERSION=1`)
    como PRIMERA línea del informe, antes de los hallazgos.
  - Decidir y documentar si `summarize_escalation()` (informe de modo) lleva
    su propia versión; lo más simple: la misma línea de versión en ambos
    documentos, con esquema declarado por documento.
  - Actualizar el golden test (6.g) y `test_report_schema.py` para comprobar
    la versión en la SALIDA REAL del script, no solo en el markdown.

A.4 LOS TESTS DEBEN CONSUMIR LA SALIDA REAL, NO EL PLANO DOCUMENTAL
    (gravedad: media-alta)
--------------------------------------------------------------------------------
`test_report_schema.py` (1.j-bis) tal como está descrito verifica el
`REPORT_SCHEMA_VERSION` declarado en un fichero .md. Eso no demuestra que el
script lo emita.
CORRECCIÓN: el test debe EJECUTAR el script sobre `fixtures/test_scope.sqf`
(`python sqf_orchestrator.py --lint <fixture>`) y comprobar sobre la salida
real: (a) primera línea de versión, (b) formato de línea con prefijo de
severidad, (c) línea `RESUMEN: bloqueantes=…; sugerencias=…; no_verificado=…`,
(d) ausencia de la forma `RESUMEN: modo=…` en el informe de hallazgos.
Es un test de contrato ejecutable, que es lo que la链条 script↔prompt↔matcher
necesita. Lo mismo aplica a `sqf_review` en PR-6.

A.5 EL PLAN NO CONTEMPLA QUE EL FORMATO CAMBIARÁ AL PORTAR (gravedad: media)
--------------------------------------------------------------------------------
`references/report_format.md` es un artefacto NUEVO (no existe hoy). Al
escribirlo, el autor puede divergir del código sin darse cuenta (A.1 es
justo eso). CORRECCIÓN: la redacción de 2.f parte de COPIAR la salida real
del script (`python sqf_orchestrator.py --lint fixtures/test_scope.sqf`) y
documentarla literalmente, en vez de escribirla de memoria. Añadir al
apartado 2.f: "Fuente de verdad: la salida real del script, no este plan".

================================================================================
PARTE B — AUDITORÍA DEL ESTADO DE EJECUCIÓN (el plan describe un repo que ya cambió)
================================================================================

B.1 EL PLAN NECESITA UNA TABLA DE ESTADO DE EJECUCIÓN (gravedad: alta)
--------------------------------------------------------------------------------
PR-1 está a medias, pero el plan no lo refleja. Cualquier revisor futuro
(partiendo del plan v2.4) creería que nada está hecho.
CORRECCIÓN: añadir al plan una sección "ESTADO DE EJECUCIÓN" con una fila por
tarea de PR-1: `[HECHO] / [EN CURSO] / [PENDIENTE] / [DIVERGENTE]`, fecha y
nota. Primera fila obligatoria: 1.a `[HECHO]`.

B.2 `agents/` Y `legacy/agents/` COEXISTEN: 1.e SE EJECUTÓ COMO COPIA (gravedad: media-alta)
--------------------------------------------------------------------------------
El plan dice "Mover originales a `legacy/agents/`". En el repo hay 11 ficheros
en `agents/` Y los mismos 11 en `legacy/agents/`. La copia de trabajo de la
skill (`skills/arma3-sqf-skill/`) no tiene `agents/`, pero la raíz sí.
Consecuencias: (a) la duplicación que R2 prohíbe sigue viva en la raíz;
(b) `plugin.json` y `pyrightconfig.json` pueden seguir apuntando a `agents/`;
(c) el escaneo de rutas y el test de unicidad podrían ver dos veces la misma
norma.
CORRECCIÓN: decidir explícitamente: borrar `agents/` (git ya conserva la
historia) o declararlo "compatibilidad Antigravity" con su propio test de
unicidad excluido. Si se conserva, 1.e pasa a "COPIAR" y hay que añadir el
`agents/` a las exclusiones de 1.n y a la lista de 1.o (decisión de plugin
legacy).

B.3 EL `.gitignore` NO EXCLUYE `evals/runs/` TODAVÍA (gravedad: media)
--------------------------------------------------------------------------------
1.n-bis está pendiente (verificado: el `.gitignore` actual termina en
`*.rpt`, sin sección de `evals/`). Es una tarea de un minuto y protege datos
de usuario antes de cualquier push. Marcarla como de las primeras de PR-1.

B.4 `rules/AGENTS.md` SIGUE VIVO Y SIN CONVERTIR (gravedad: media)
--------------------------------------------------------------------------------
1.f está pendiente: `rules/AGENTS.md` (con `trigger: always_on`, frontmatter
propio de Antigravity) sigue en la raíz. Es una fuente de reglas más (la
cuarta), no conforme a R2. Debe convertirse en `references/invariants.md` o
quedar declarado como legacy con la misma decisión de 1.o que `agents/`.

B.5 DISCREPANCIA DE NOMBRE: `diferencial-misiones-addons.md` vs plan
    (gravedad: baja)
--------------------------------------------------------------------------------
El fichero real es `references/diferencial-misiones-addons.md` (plural). El
plan v2.4 lo llama `diferencial-mision-addon.md` (singular) en el árbol, en
2.f-bis y en el inventario. Como el nombre aparece en el Capa 0 y en las
lentes (rutas de lectura), la discrepancia romperá las referencias.
CORRECCIÓN: fijar el nombre real en el plan (`diferencial-misiones-addons.md`)
y renombrarlo de forma consistente cuando se migre (o mantener el plural).

B.6 `scripts/check.py` Y `measure_tokens.py` NO EXISTEN AÚN (gravedad: baja, informativo)
--------------------------------------------------------------------------------
El plan es coherente con esto (1.j-ter y 2.f-ter). Se registra para que el
estado de ejecución no suggests que el gate ya es ejecutable: hoy NO hay
`python scripts/check.py` que correr.

B.7 EL SKILL.md SIGUE SIENDO EL ORIGINAL (~30 KB) (gravedad: informativa)
--------------------------------------------------------------------------------
Confirmado: `skills/arma3-sqf-skill/SKILL.md` es el original. 1.g-bis (la
migración bloqueante de las 7 categorías a `invariants.md`) sigue pendiente y
es la tarea que debe ejecutarse ANTES de que PR-2 reescriba el prompt. while
the plan says "2.3 (FINAL)", PR-1.1.g-bis is the next critical action.

================================================================================
PARTE C — LAGUNAS MENORES RESTANTES
================================================================================

C.1 FALTA EL ARTEFACTO "PASTE" PARA CLAUDE DESKTOP SIN MCP (gravedad: media)
--------------------------------------------------------------------------------
La tabla de hosts dice: Claude Desktop → "MCP stdio (Track B) o paste" con
compensación "Checklist inline en paste". Pero el árbol de `integrations/claude/`
solo tiene `CLAUDE.md` (Claude Code) y `install.md`; el snippet MCP es Track B
(PR-6). Sin Track B, un usuario de Claude Desktop no tiene NINGÚN artefacto que
pegar.
CORRECCIÓN: añadir `integrations/claude/claude_desktop_paste.md` = paquete
inline P1–P4 (mismo generador que ChatGPT/Gemini, ≤ 8.000 chars), más su
`install.md`. Y una fila en el DoD (P1–P4 presente en los 3 artefactos inline).

C.2 LA COPIA DE `references/` EN LA SKILL EN PUEDE DERIVAR (gravedad: media)
--------------------------------------------------------------------------------
7.c-bis copia `references/` a la skill EN. Esa copia es una segunda fuente
de verdad potencial: nada verifica que sus extractos CANON coincidan con el
canónico ES. Solo se mide su presupuesto de tokens (DoD #20).
CORRECCIÓN: añadir un check por hash de las regiones `CANON-EXTRACT` de la
copia EN contra `references/invariants.md`, ejecutado en `check.py` (y en el
release). Regla: la copia ES de la skill EN es la canónica para esa
instalación, pero debe ser byte-idéntica en las regiones normativas.

C.3 EL GATE DE "0 OMISIONES" NO TIENE POLÍTICA DE REMEDIACIÓN (gravedad: media)
--------------------------------------------------------------------------------
DoD #13 exige "0 omisiones silenciosas" en modo pegado. Es un gate estricto:
es probable que un modelo real omita una categoría. El plan no dice qué hacer
si falla (y el plugin original sí tiene política: máx. 3 iteraciones y puerta
de calidad).
CORRECCIÓN: añadir una "Política de iteración del port", simétrica a la del
plugin original:
  - Si un gate de calidad falla (M2 < 90 %, M3 < 6/6, omisiones > 0), se
    itera sobre Capa 0 / lentes / prompt de evaluación, hasta 3 iteraciones.
  - Si tras 3 iteraciones sigue fallando: NO se publica en verde. Se marca el
    criterio como `NO VERIFICADO` con motivo en `docs/QUALITY.md`, se publica
    con la limitación explícita, y se anota como pendiente known-issue.
  - Prohibido "ajustar el golden" para que pase (cambiar un esperado = cambiar
    el contrato → requiere revisar el canónico y regenerar hashes).

C.4 UN TEST OMITIDO NO DEBE CONTAR COMO VERDE (gravedad: baja-media)
--------------------------------------------------------------------------------
1.j-bis marca 3 tests con `skipif` en PR-1. Si un test queda skip de forma
permanente (p. ej. el fichero que verifica nunca se crea), el gate pasa en
verde sin comprobar nada.
CORRECCIÓN: en `check.py --fase PR-N`, un test marcado como "esperado en esta
fase" que aparece como SKIPPED debe fallar el gate. Es decir: el skip
significa "todavía no aplica", y el gate debe distinguir "todavía no aplica"
de "se ha olvidado crearlo".

C.5 LOS MÉTODOS DEL DoD APUNTAN A EVIDENCIA NO VERSIONADA (gravedad: baja-media)
--------------------------------------------------------------------------------
DoD #12 y #13 citan "Trazas en `evals/runs/`" como método, pero `evals/runs/`
está en `.gitignore` (1.n-bis): la evidencia no se versiona y no es auditable
por terceros.
CORRECCIÓN: el método de esos criterios debe ser "traza local + fila en
`docs/QUALITY.md` (versionada)". La traza es el insumo; la evidencia
publicable es QUALITY.md.

C.6 EL PATRÓN DEL TEST DE ANCLAS DEBE SER EXPLÍCITO (gravedad: baja)
--------------------------------------------------------------------------------
DoD #4: "6 anclas `CANON:*` exactamente 1 vez". Si el test busca la cadena
`CANON:` y los extractos usan `CANON-EXTRACT:`, no hay colisión, pero el
criterio no dice el patrón exacto y el test podría casar por prefijo.
CORRECCIÓN: fijar el patrón regex `<!-- CANON:[A-Z]+ -->` (canónica) y
`<!-- CANON-EXTRACT:[A-Z]+ -->` (extracto) en el enunciado del test.

C.7 LA TABLA DE DEGRADACIÓN DEBE INCLUIR EL PAQUETE INLINE COMO COMPENSACIÓN
    CONCRETA (gravedad: baja)
--------------------------------------------------------------------------------
La tabla nombra la compensación ("Checklist GENERATED inline"), pero no nombra
el fichero ni el contenido P1–P4. Con C.1 y el paquete P1–P4 ya definidos, la
tabla puede quedar así: "compensación: `integrations/<host>/<artifact>.md`
(P1–P4)". Un lector puede así auditar la compensación sin inferirla.

C.8 FALTA UNA TAREA DE "RECONCILIAR EL PLAN CON EL ESTADO REAL" (gravedad: baja)
--------------------------------------------------------------------------------
Dado que el plan ya se desvió de la realidad (1.a ejecutado, 1.e ejecutado
como copia), conviene una tarea explícita en PR-1 que cierre el desfase:
"Actualizar la sección ESTADO DE EJECUCIÓN tras aplicar 1.a/1.e, y documentar
en el changelog de PR-1 que 1.e se ejecutó como copia (decisión: borrar
`agents/` o mantenerlo como compatibilidad Antigravity)".

================================================================================
PARTE D — SECUENCIA (mínima; el backbone no se toca)
================================================================================
  PR-1 + 2.f-cua  (tarea de CÓDIGO, no de plan): `sqf_models.py` emite
                  `REPORT_SCHEMA_VERSION` en ambos informes     (A.3)
        + 2.f-cub  test_report_schema.py EJECUTA el script y valida la
                  salida real (prefijo de severidad, RESUMEN correcto,
                  ausencia de `RESUMEN: modo=` en hallazgos)      (A.1, A.2, A.4)
        + 1.e-bis  decisión sobre `agents/` (borrar vs legacy) + exclusiones (B.2)
        + B.1      sección ESTADO DE EJECUCIÓN en el plan           (B.1)
        + B.5      unificar el nombre `diferencial-misiones-addons.md` (B.5)
  PR-3 + 3.d-ter  (sigue) + nuevo `integrations/claude/claude_desktop_paste.md`
                  (paquete P1–P4)                                  (C.1)
  PR-5 + 5.f-ter  check por hash de las regiones CANON-EXTRACT de la
                  copia EN contra el canónico                        (C.2)
        + 5.i      Política de iteración del port (3 iteraciones, luego
                  `NO VERIFICADO` documentado; prohibido ajustar goldens) (C.3)
  DoD  + método de #12/#13 → "traza + fila en docs/QUALITY.md"         (C.5)
        + fila "P1–P4 presente en los 3 artefactos inline"            (C.1)
        + criterio explícito: skip en fase esperada = fallo            (C.4)

================================================================================
PARTE E — ESTADO
================================================================================
- Cerrado en v2.4 y NO se repite: N1/N2/N3; CANON vs CANON-EXTRACT; check.py
  --fase; paquete inline P1–P4; veredictos del matcher; contexto_cargado;
  evals/runs en .gitignore; DoD con "Aplicable desde"; EN medida; riesgos.
- Abierto: 13 puntos (A.1–A.5, B.1–B.7, C.1–C.8 → 5 + 7 + 8 = 20 enunciados,
  agrupados en 13 correcciones): 1 bloqueante de contrato (A.1), 3 altos
  (A.2, A.3, B.1), 1 medio-alto de evidencia (A.4) y el resto medios/bajos.
- Carácter de esta ronda: ya no son errores de diseño del plan, sino
  (a) un contrato que debe COPIARSE del código real y no escribirse de
  memoria, (b) una tarea de código que nadie tenía asignada (emitir la versión
  del esquema), y (c) la reconciliación del plan con el repo ya modificado.
- Siguiente acción crítica y única: 1.g-bis (migrar las 7 categorías, la
  puerta, la honestidad, la precedencia y la propiedad al canónico) ANTES de
  que PR-2 reescriba el `SKILL.md`. Es la única tarea del plan cuyo orden no
  puede invertirse.
- No he ejecutado el plan ni modificado el plugin más allá de leerlos: el
  análisis es documental sobre el v2.4 y el estado real del repo.

================================================================================
FIN DE LAS INSTRUCCIONES v2.4 → v2.5
================================================================================
