================================================================================
INSTRUCCIONES PARA MEJORAR, ACTUALIZAR Y OPTIMIZAR LA PLANEACIÓN (v2.2 → v2.3)
================================================================================

CONTEXTO: el Plan v2.2 cerró los 19 puntos de la revisión anterior (R6, 1.c-bis,
1.g-bis, 1.m/1.n/1.o, 2.f-bis, 2.g-bis, 2.g-ter, 2.h Fase 2, 2.k, 4 intenciones,
métrica 6/6 por categoría, juez determinista, EN como skill separada, DoD de 17
filas, riesgos reencuadrados). NO se repiten.

Esta ronda es la última antes de ejecutar. El plan está en condiciones de
arrancar, pero conserva 3 defectos que harían fallar sus propios criterios de
salida, y 11 ajustes de completitud. Se listan como A.1–A.14.

Verificado leyendo el repo en esta ronda:
  - `skills/arma3-sqf-review/references/` contiene `checklist-entrega.md`,
    `diferencial-misiones-addons.md`, `sqf-standards.md`, `wiki-cache.md`.
  - El `SKILL.md` actual define comportamientos que NO son "agentes" y que
    el plan no enumera en ningún sitio: la PRECEDENCIA de conflictos
    (locality > performance > estilo), la PROPIEDAD de reglas (tabla de dueño
    único por tema), la tabla de participación por modo y el checklist de
    salida A–I. Son rules normativas, no tareas.

================================================================================
PARTE A — DEFECTOS QUE HACEN FALLAR UN CRITERIO DE SALIDA
================================================================================

A.1 LA MÉTRICA DEL MODO PEGADO ES INALCANZABLE POR CONSTRUCCIÓN (gravedad: BLOQUEANTE)
--------------------------------------------------------------------------------
PR-4 exit: "Smoke tests S1–S3 (6/6) en modo pegado en ≥ 2 hosts".
DoD #14: "6/6 hallazgos en ≥ 2 hosts/modelos".
Pero de los 6 hallazgos del smoke test, en modo pegado (código pegado en el
chat, sin filesystem) NO son todos detectables:
  - Cat. 1 (scope sin private) → detectable leyendo el snippet.
  - Cat. 2 (softlock / waitUntil sin salida) → detectable leyendo el snippet.
  - Cat. 3 (UI/`player` en ruta de servidor) → detectable leyendo el snippet.
  - Cat. 4 (suspensión en contexto unscheduled) → DETECTABLE SOLO si el
    snippet incluye el contexto de invocación (preInit, EH, remoteExecCall).
    Un snippet pegado sin ese contexto NO permite afirmarlo → el veredicto
    correcto es `NO VERIFICADO`, no BLOQUEANTE.
  - Cat. 5 (whitelist CfgRemoteExec) → requiere leer `description.ext` /
    `config.cpp`. NO es detectable desde un snippet → `NO VERIFICADO`.
  - Cat. 7 (dependencia CBA/ACE3 no autorizada) → requiere el PERFIL
    declarado (CBA: no). Si el perfil no está declarado → `NO VERIFICADO`.
Por tanto, en modo pegado el máximo honesto es 3–4/6 como BLOQUEANTE
detectados; los otros 2–3 deben salir como `NO VERIFICADO` — que es
exactamente lo que exige el principio de honestidad y lo que exige 4.e.
El DoD, tal como está escrito, PUNTUA COMO FALLO al comportamiento correcto.
CORRECCIÓN: redefinir la métrica por modo como "aciertos sobre esperables":
  - Modo archivo: 6/6 hallazgos BLOQUEANTE detectados con categoría correcta.
  - Modo pegado: (BLOQUEANTES detectados + NO VERIFICADOS correctamente
    declarados) = 6/6, es decir 3–4 detectados + 2–3 `NO VERIFICADO`
    explícitos, y CERO affirmaciones*PASA* sobre lo no verificable.
  - El DoD #14 se reescribe: "Modo pegado: 6/6 esperables resueltos (detectado
    o `NO VERIFICADO` con justificación), ≥1 `NO VERIFICADO` por test que lo
    requiere, 0 falsos `PASA`".
Aplica el mismo razonamiento a los goldens de PR-5: cada golden declara
`verificable_en: [archivo, pegado]` por hallazgo esperado, y la métrica se
calcula solo sobre los verificables en ese modo.

A.2 DoD #11 MEZCLA DOS DENOMINADORES INCOMPARABLES (gravedad: alta)
--------------------------------------------------------------------------------
5.c pide "detección por script = 100 % esperado en goldens deterministas" y
DoD #11 pide "detectados/esperados ≥ 0,90 agregado y por categoría (1–7)".
Pero el script (`sqf_orchestrator.py --lint`) solo cubre de forma determinista
la Cat. 1 (scope/fugas) y parte de la Cat. 2 (sintaxis). Las Cat. 3–7 son
semánticas: el script NO las detecta. Un agregado 0,90 sobre las 7 categorías
mezcla "el script acertó" con "el modelo acertó" y no es interpretable.
CORRECCIÓN: dos métricas separadas, con denominadores declarados:
  - M1 (script): 100 % de los hallazgos verificables-sin-LLM sobre la
    subconjunto determinista de goldens. Denominador = hallazgos de Cat. 1–2.
  - M2 (modelo): ratio de detección sobre las categorías semánticas
    (Cat. 3–7) que el host puede verificar en ese modo.
  - M3 (modelo, modo pegado): como M2 pero solo sobre los verificables sin
    filesystem, más el ratio de `NO VERIFICADO` correctos.
El DoD #11 se reescribe con M1, M2 y M3 por separado y sus denominadores.

A.3 R6 NO ES APLICABLE A LAS LENTES: EL CONTENIDO POR DISCIPLINA NO EXISTE EN EL
    CANÓNICO (gravedad: alta)
--------------------------------------------------------------------------------
La tabla de generación dice: `references/lenses/*.md` = "GENERATED FROM
invariants.md". Pero `invariants.md` contiene las 7 categorías, la puerta, la
honestidad y los modos — NO el catálogo de señales de locality, ni las heurísticas
de scheduler, ni los criterios de diseño de módulos. Un generador no puede
extraer de ahí el cuerpo específico de cada lente: el 80 % del contenido de la
lente no tiene fuente.
Peor: el hash se calcula sobre el archivo entero, luego cualquier edición
manual de una lente rompe el check (falso positivo) o, si se "regenera" desde
un canónico que no tiene ese contenido, la lente se vacía.
CORRECCIÓN: definir el modelo de generación por REGIONES:
  - Cada lente = [BLOQUE AUTORADO por disciplina] + [SECCIÓN CANON inyectada].
  - Solo la sección inyectada va dentro del hash; el bloque autorado lleva su
    propio marcador `<!-- AUTHORED --> ... <!-- /AUTHORED -->`.
  - El check verifica: (a) la sección CANON inyectada coincide con la del
    canónico; (b) la sección AUTHORED no ha cambiado respecto al último
    commit (hash en un fichero de lock, `generated.lock.json`).
  - Lo mismo para `workflows/*.md` (hoy "redactados manualmente" y por tanto
    fuera de R6: o entran en el esquema de regiones, o se declaran
    explícitamente como excepción a R6, como ya se hace con la versión EN).
Alternativa más simple y recomendada: que las lentes NO sean generadas sino
autoras, y que solo el "núcleo normativo" de cada lente (las categorías que le
aplican) se inyecte desde invariants.md. Decide una de las dos y descríbelo
en el plan; lo que no puede quedar es "GENERATED" sin fuente.

A.4 `integrations/claude/CLAUDE.md` SE ESCRIBE A MANO Y DUPLICA LA NORMA
    (gravedad: alta)
--------------------------------------------------------------------------------
1.f dice: "Convertir `rules/AGENTS.md` → `references/invariants.md` ...
Crear `integrations/claude/CLAUDE.md` como copia adaptada".
Ese CLAUDE.md contiene reglas normativas (invariantes de servidor dedicado) →
es un duplicado del canónico → viola R2 y DoD #8 ("DEFINICIONES fuera de
invariants.md = 0"). Además, el árbol del workspace marca `integrations/` como
"(GENERATED)", así que 1.f (PR-1) y 3.a (PR-3) se contradicen sobre el mismo
directorio.
CORRECCIÓN:
  - 1.f NO crea CLAUDE.md. Crea solo el canónico y el generador.
  - CLAUDE.md pasa a ser artefacto GENERATED (PR-3), como los de ChatGPT y
    Gemini, con su sección CANON inyectada + bloque autorado ("cómo usar esta
    skill en Claude Code", que sí es específico del host y no es normativa).
  - Si se decide que CLAUDE.md no lleve reglas (solo rutas y偏Uso), entonces no
    necesita ser generado: basta con que NO contenga definiciones normativas.
    Elige una de las dos y ajusta el árbol del workspace (hoy pone GENERATED
    en `integrations/` pero PR-3 3.a no lo dice).

A.5 LA TABLA DE PARIDAD NO CUBRE LOS COMPORTAMIENTOS NORMATIVOS (gravedad: alta)
--------------------------------------------------------------------------------
DoD #16: "Todos los ítems del plugin original clasificados". Pero el
inventario que se construye (1.k, 2.j, 5.f) son los 11 AGENTES. El plugin
tiene además comportamientos normativos que NO son agentes y que son
precisamente lo que un port pierde en silencio (verificado en el SKILL.md
actual):
  1. Las 7 categorías de BLOQUEANTE.
  2. La Puerta de Calidad Infranqueable.
  3. El principio de honestidad técnica.
  4. La rúbrica de severidad (BLOQUEANTE vs Sugerencia).
  5. La PRECEDENCIA de conflictos (locality > performance > estilo).
  6. La PROPIEDAD de reglas / dueño único por tema (tabla de 9 filas).
  7. La tabla de participación por modo (Micro/Estándar/Completo).
  8. Los criterios de modo deterministas + fallback + prohibición de Micro manual.
  9. El Perfil de Proyecto de 7 parámetros.
  10. El formato de paquete de contexto (handoff) — irrelevante en single-agent.
  11. El checklist de salida A–I (Informe Desglosado de Estados por ítem).
  12. Los criterios de entrega por DESTINO (misión vs addon).
  13. El flujo completo de 10 pasos y su orden.
  14. La regla de correcciones (máx. 3 iteraciones, orden locality→performance→BP).
  15. El formateo del informe estructurado del script.
  16. La regla de verificación wiki (fuente primaria a3ref, URL+revid+SHA, cache no es evidencia).
  17. El escalado de modo y la "puerta" de NO VERIFICADO por ítem.
  18. La separación entre lo que es pregunta conceptual (sin flujo) y lo que dispara revisión.
CORRECCIÓN: DoD #16 pasa a exigir una tabla con DOS columnas de inventario:
  - 11 agentes (mapeo ya definido) y
  - 18 comportamientos normativos (lista explícita arriba).
Cada ítem con estado `PORTADO / PORTADO-REDUCIDO / NO APLICABLE (motivo)`.
Añadir en 1.k el esqueleto con los 18 comportamientos, no solo los 11 agentes.

A.6 FALTAN DOS ANCLAS CANON NORMATIVAS (gravedad: media-alta)
--------------------------------------------------------------------------------
La lista de anclas es CANON:BLOQUEANTES, CANON:PUERTA, CANON:HONESTIDAD,
CANON:MODOS. No incluye:
  - CANON:PRECEDENCIA (locality > performance > estilo; "una optimización
    JAMÁS se aplica si compromete la estabilidad o la localidad") → es una
    regla normativa que decide entre hallazgos; sin ella, un modelo puede
    reportar una optimización que rompe estabilidad.
  - CANON:PROPIEDAD (dueño único por tema → no duplicar hallazgos entre
    lentes). En un port sin subagentes esto sigue siendo necesario: es lo que
    impide que locality y performance reporten el mismo hallazgo.
CORRECCIÓN: añadir ambas anclas a 1.g-bis (migración literal) y a la lista de
la tabla "Fuente Canónica"; el test Fase 2 las incluye en la lista de
definiciones que no pueden duplicarse.

A.7 EL HARNESS NO DICE CÓMO SE EJECUTA LA SKILL DE FORMA REPRODUCIBLE (gravedad: media-alta)
--------------------------------------------------------------------------------
5.c pide N=3 repeticiones por golden por host, con modelo/temperatura fijos, y
R5 exige que la "tabla por host" sea publicable. Pero "Claude Code" no es una
API: el harness no puede invocarlo como si fuera un endpoint. Y "modo pegado
(host A/B)" implica pegar snippets a mano en una UI. Sin mecanismo de
invocación, N=3 es una activity manual no reproducible y la tabla por host no
es evidencia.
CORRECCIÓN: especificar el mecanismo y la traza:
  - Claude Code: invocación no interactiva (`claude -p` / modo print) con
    `--model` pineado, o un runner mínimo contra la API con el mismo prompt de
    sistema; en ambos casos, el prompt EXACTO usado se guarda versionado en
    `evals/prompts/` (no solo el judge).
  - Modo pegado: cada golden se ejecuta como un turno de chat con el
    artefacto del host (custom_gpt_instructions.md / system_instruction.md),
    registrando el texto exacto enviado.
  - TRAZA OBLIGATORIA: `evals/runs/<fecha>/<host>/<golden>.json` con prompt
    enviado, respuesta cruda, modelo, versión, temperatura, veredicto del
    matcher. Sin la cruda, la tabla por host no es auditable.
  - El harness lee esas trazas y produce la tabla; el modelo no "rellena" la
    tabla a mano.

A.8 EL KNOWLEDGE DE CUSTOM GPT TIENE LÍMITE DE NÚMERO DE ARCHIVOS (gravedad: media)
--------------------------------------------------------------------------------
2.f-bis trocea `wiki-cache` por comando ("< 5 KB c/u") y 3.d crea un
`knowledge_manifest.md` con "qué archivos subir". Si el troceado por comando
produce cientos de ficheros, el manifiesto no es subible: ChatGPT tiene un
límite de número de archivos por GPT (20 en la documentación vigente de
OpenAI — VERIFICA el valor actual antes de fijarlo).
CORRECCIÓN: 3.d debe incluir un criterio de SELECCIÓN, no solo de troceado:
  - Manifiesto final ≤ 20 archivos (verificar el límite vigente).
  - Prioridad: `invariants.md` (o su recorte), `checklist-entrega.md`,
    `report_format.md`, `diferencial-mision-addon.md`, las 6 lentes.
  - `wiki-cache/` NO se sube completo: se sube un subconjunto curado de los
    comandos más usados, y el resto se documenta como "consulta con la
    réplica a3ref local (Track A modo archivo)".
  - El manifiesto declara el conteo de archivos y su motivo.

A.9 DoD #14 CHOCA CON R1 (gravedad: media)
--------------------------------------------------------------------------------
R1 dice que los hosts externos pueden quedar `NO VERIFICADO` sin bloquear.
DoD #14 exige "6/6 hallazgos en ≥ 2 hosts/modelos" en modo pegado, sin
escapatoria: si el usuario no tiene una segunda cuenta (ChatGPT/Gemini), el
Release Gate se bloquea por un criterio que R1 declara no bloqueante.
CORRECCIÓN: DoD #14 = "modo pegado en el host local disponible + ≥2 MODELOS
(o el segundo host si hay cuenta)". Es decir, la exigencia es de MODELOS
distintos, no de cuentas distintas: la misma Claude Code con dos modelos
(counta como dos ejecuciones con modelos distintos) o la misma sesión de
ChatGPT con dos Custom GPTs. Si solo hay un modelo disponible, la fila queda
`NO VERIFICADO` con motivo, y el Release Gate sigue.

A.10 R5 EXIGE UNA TABLA POR HOST QUE NO TIENE DESTINO EN EL REPO (gravedad: media)
--------------------------------------------------------------------------------
R5: "'Igual calidad que el plugin original' solo es publicable si PR-5 produce
tabla por host con modelo, versión y N=3 repeticiones". PR-5 produce la tabla
en `evals/`, y el README de 7.a solo tiene quickstarts. No hay ningún artefacto
destinado a ser LEÍDO por un usuario final que respalde la afirmación.
CORRECCIÓN: crear `docs/QUALITY.md` en PR-5 con la tabla por host (host, modelo,
versión, fecha, N, M1/M2/M3, FP, conclusión por host) y enlazarla desde el
README (7.a). Sin ese documento, R5 no se cumple y la afirmación "misma
calidad" no debe usarse en ninguna página pública.

A.11 NO HAY TAREAS DE CREACIÓN DE LOS TESTS NUEVOS (gravedad: media)
--------------------------------------------------------------------------------
1.j define qué ejecuta `check.py`, pero ninguna tarea crea los tests nuevos, y
DoD #3 solo protege los 6 tests pre-existentes. Sin los ficheros, `check.py`
no tiene nada que ejecutar más allá de pytest.
CORRECCIÓN: añadir 1.j-bis con nombres concretos:
  - `tests/test_no_absolute_paths.py` (lista blanca).
  - `tests/test_canonical_uniqueness.py` (Fase 1 anclas + Fase 2 definiciones).
  - `tests/test_generated_files_hash.py` (hash por región/archivo).
  - `tests/test_report_schema.py` (REPORT_SCHEMA_VERSION + RESUMEN:).
  - `tests/test_skill_structure.py` (4 intenciones, 7 líneas de índice, tokens).
Y que PR-5 añada `tests/test_goldens_dataset.py` (integridad del dataset:
  cada golden tiene esperados, cada categoría 1–7 cubierta, negativos
  presentes, `verificable_en` declarado).

A.12 LA SKILL EN NO PUEDE COMPARTIR REFERENCES POR SYMLINK (gravedad: media)
--------------------------------------------------------------------------------
7.c dice "references/ compartidas (symlinks o copia, según el host)".
Symlinks en Windows requieren Developer Mode o privilegios, no sobreviven a
un ZIP/wheel, y el usuario que copia solo `skills/arma3-sqf-skill-en/` se
queda sin referencias. Además, si las referencias se comparten por symlink,
el packaging (MANIFEST/wheel) debe incluirlas explícitamente.
CORRECCIÓN: sin symlinks. Definir:
  - INSTALACIÓN: `install.md` copia `references/` (o el repo completo) al
    directorio de skills del host; la copia es la norma.
  - Si se empaqueta en PyPI, `references/` va dentro del paquete y ambas skills
    referencian el mismo directorio por ruta relativa, NO por symlink.
  - Medir tokens también sobre la copia EN (ya se pide) y añadir que el test de
    hash de los GENERATED se ejecuta en la copia EN (si existe).

A.13 DoD #15 ES "REVISIÓN MANUAL": ROMPE R4 (gravedad: baja-media)
--------------------------------------------------------------------------------
R4 exige MÉTRICA + MÉTODO + ESTADO para todo criterio; "revisión manual de la
tabla" es un método no reproducible ni auditable. Y el contenido a verificar
("≥1 `NO VERIFICADO` por smoke test que requeriría linter") es perfectamente
scriptable sobre las trazas de `evals/runs/`.
CORRECCIÓN: convertirlo en un check de `check.py`/harness que recorra las
trazas y falle si algún test que exige linter no contiene `NO VERIFICADO`.

A.14 PRESUPUESTO DE `invariants.md`: PLAN DE DESBORDAMIENTO (gravedad: baja)
--------------------------------------------------------------------------------
2.f-bis fija `invariants.md < 15 KB`, pero 1.g-bis + 1.g deben meter en ese
fichero: 7 categorías + puerta + honestidad + rúbrica + precedencia +
propiedad + matriz de modo + participación por modo + lo absorbido de
`sqf-standards.md` y de `rules/AGENTS.md`. Puede no caber.
CORRECCIÓN: añadir la regla de desbordamiento explícita: "si la migración
literal supera 15 KB, la rúbrica, la matriz de participación y la tabla de
propiedad salen a `references/rubrica.md` y `references/workflows/modes.md`
(respetando las anclas), y el canónico conserva solo lo normativo
(bloqueantes, puerta, honestidad, precedencia)". Y medir el tamaño al final
de 1.g-bis, no al final de PR-2.

================================================================================
PARTE B — SECUENCIA (ajustes mínimos, el backbone no se toca)
================================================================================
  PR-1 + 1.g-ter  migrar también CANON:PRECEDENCIA y CANON:PROPIEDAD  (A.6)
        + 1.g-cua  regla de desbordamiento de tamaño de invariants.md     (A.14)
        + 1.j-bis  crear los 5 tests nuevos con nombre                    (A.11)
        + 1.k-bis  esqueleto de PARIDAD con 11 agentes + 18 comportamientos (A.5)
        + 1.f-bis  NO crear CLAUDE.md aquí (se genera en PR-3)            (A.4)
  PR-2 + 2.d-bis  modelo de generación por regiones (AUTORADO + CANON)     (A.3)
        + 2.e-bis  declarar workflows/*.md como excepción a R6 o incluirlos
                   en el esquema de regiones                               (A.3)
        + 2.f-ter  `verificable_en` por hallazgo esperado en goldens       (A.1)
  PR-3 + 3.a-bis  CLAUDE.md como artefacto GENERATED (o sin reglas)        (A.4)
        + 3.d-bis  manifiesto de Knowledge ≤ 20 archivos con criterio de
                   selección explícito                                     (A.8)
  PR-4 + 4.f      métrica por modo: "esperables resueltos" (detectado o
                   NO VERIFICADO con justificación), no "6/6 detectados"  (A.1)
  PR-5 + 5.c-bis  M1/M2/M3 con denominadores declarados                   (A.2)
        + 5.c-ter  mecanismo de invocación + trazas crudas en evals/runs/  (A.7)
        + 5.f-bis  `docs/QUALITY.md` con la tabla por host                 (A.10)
        + 5.h      test de integridad del dataset de goldens              (A.11)
  PR-7 + 7.c-bis  references por COPIA, sin symlinks; instalación documentada (A.12)
  DoD  #11 reescrito (M1/M2/M3)  #14 reescrito (modelos, no cuentas)
        #15 reescrito (check scriptable)  #16 ampliado a 18 comportamientos

================================================================================
PARTE C — ESTADO
================================================================================
- Cerrado en v2.2 y NO se repite: R1–R6, canonicidad con anclas, 1.c-bis,
  1.g-bis, 1.m/1.n/1.o, 2.f-bis, 2.g-bis, 2.g-ter, 2.h Fase 2, 2.k, 4 intenciones,
  6/6 por categoría, juez determinista, EN como skill separada, DoD de 17
  filas, riesgos reencuadrados, dataset a3ref documentado, installer por host.
- Abierto: 14 puntos (A.1–A.14): 1 bloqueante (A.1), 3 altos (A.2, A.3, A.4),
  3 medios-altos (A.5, A.6, A.7) y 7 medios o bajos.
- Los tres bloqueantes/altos de A.1–A.4 se concentran en PR-2/PR-4 y PR-5:
  son correcciones de diseñosmall y acotadas, no de estructura.
- No he ejecutado el plan ni modificado el plugin: el análisis es documental
  sobre el v2.2 y el estado real del repo (SKILL.md actual, references/
  existentes, tests/ actuales, pyproject.toml, sqf_wiki_reader.py).

================================================================================
FIN DE LAS INSTRUCCIONES v2.2 → v2.3
================================================================================
