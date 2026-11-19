================================================================================
INSTRUCCIONES PARA MEJORAR, ACTUALIZAR Y OPTIMIZAR LA PLANEACIÓN (v2.3 → v2.4)
================================================================================

CONTEXTO: el Plan v2.3 cerró los 14 puntos de la revisión anterior (M1/M2/M3 con
denominadores, `NO VERIFICADO` como acierto en modo pegado, modelo de generación
por regiones con `generated.lock.json`, CANON:PRECEDENCIA + CANON:PROPIEDAD,
18 comportamientos normativos en PARIDAD, `docs/QUALITY.md`, trazas en
`evals/runs/`, sin symlinks, tests con nombre, ≤20 archivos de Knowledge).
NO se repiten.

El plan ya no tiene huecos de diseño: lo que queda son 3 contradicciones
internas (A.1–A.3) que harían fallar sus propios gates, 4 defectos de
ejecución (A.4–A.7) y 5 ajustes de completitud (A.8–A.12).

VERIFICADO en esta ronda:
  - El `SKILL.md` actual se reescribe en PR-2 (2.a/2.b); por tanto, en PR-1 la
    Capa 0 todavía no existe (o es la vieja, con 30 KB). Cualquier test que
    la mida en PR-1 falla o mide lo viejo.
  - `references/invariants.md` no existe hoy; lo crea PR-1.
  - `REPORT_SCHEMA_VERSION` se añade en PR-2 (2.c), no en PR-1.
  - `scripts/measure_tokens.py` se crea en PR-2, pero PR-1 1.j lo incluye ya en
    `check.py`.

================================================================================
PARTE A — CONTRADICCIONES QUE BLOQUEAN LOS GATES DEL PLAN
================================================================================

A.1 EL GATE DE SALIDA DE PR-1 ES INALCANZABLE (gravedad: BLOQUEANTE)
--------------------------------------------------------------------------------
PR-1 exit: "`python scripts/check.py` verde (pytest + test rutas + test unicidad
Fase 1 + test report schema + test skill structure)".
Pero `test_skill_structure.py` (1.j-bis) comprueba "4 intenciones en Capa 0,
7 líneas de índice, `measure_tokens.py` dentro del presupuesto", y la Capa 0
nueva se redacta en PR-2 (2.b). En PR-1 el `SKILL.md` sigue siendo el viejo
(~30 KB, sin Capa 0) → ese test falla.
Además `test_report_schema.py` verifica `REPORT_SCHEMA_VERSION=1`, que se
añade en 2.c (PR-2). Y 1.j mete `measure_tokens.py` en `check.py`, pero
`measure_tokens.py` se crea en PR-2 → import error en PR-1.
CORRECCIÓN: el gate de PR-1 debe incluir solo lo que PR-1 produce:
  PR-1 exit = pytest + test rutas + test unicidad Fase 1 (anclas).
Y el resto debe quedar en estado "no aplicable hasta PR-2" de forma EXPRESA,
con dos mecanismos (elegir uno y dejarlo escrito):
  (a) el test se marca con un skip explícito si el fichero que verifica no
      existe (`pytest.mark.skipif(not path.exists(), reason="PR-2")`), y el DoD
      solo considera aplicable el test cuando el artefacto existe; o
  (b) `check.py` acepta un flag `--fase PR-1` que ejecuta solo las
      verificaciones de esa fase.
Recomiendo (b): `python scripts/check.py --fase PR-1` / `--fase PR-2` ...
Además, la tabla DoD necesita una columna "Aplicable desde" para que ningún
criterio se evalúe antes de que su artefacto exista.

A.2 EL TEST DE ANCLAS Y EL MODELO DE GENERACIÓN SE CONTRADICEN (gravedad: BLOQUEANTE)
--------------------------------------------------------------------------------
DoD #7: "6 anclas `<!-- CANON:* -->` solo en `invariants.md`".
Test Fase 1 (1.j-bis): "Fase 1: anclas CANON solo en `invariants.md`".
Modelo de generación (v2.3, "Modelo de generación por regiones"): cada lente
contiene `<!-- CANON:BLOQUEANTES (extracto) --> ... <!-- /CANON:BLOQUEANTES -->`
y las integraciones de host llevan sección CANON inyectada.
→ Los ficheros generados CONTIENEN anclas CANON fuera de `invariants.md` → el
test Fase 1 los marca como duplicados → CI rojo por diseño.
CORRECCIÓN: separar el identificador del ancla canónica del marcador de
inserción:
  - Ancla canónica (única, solo en `invariants.md`):
      `<!-- CANON:BLOQUEANTES -->` … `<!-- /CANON:BLOQUEANTES -->`
  - Marcador de extracto (permitido en generados, validado por hash):
      `<!-- CANON-EXTRACT:BLOQUEANTES -->` … `<!-- /CANON-EXTRACT:BLOQUEANTES -->`
Test Fase 1 = "el ancla canónica aparece exactamente 1 vez en el repo".
Test Fase 2 = "todo CANON-EXTRACT coincide con el canónico (hash)".
Regla derivada: el canónico NUNCA se copia literalmente a un fichero
generado; solo se inyecta el extracto marcado.

A.3 EL EXTRACTO INYECTADO DUPLICA LAS DEFINICIONES QUE EL DOD PROHÍBE
    (gravedad: BLOQUEANTE)
--------------------------------------------------------------------------------
DoD #8: "0 DEFINICIONES fuera de `invariants.md`".
El modelo de regiones inyecta "Categorías aplicables" en cada lente. Si el
extracto es la definición (categoría + descripción + condiciones + excepciones),
es una definición normativa duplicada → viola DoD #8 y R2.
Y si el extracto es solo el título de la categoría, no aporta nada: el modelo
que lee `lenses/locality.md` no sabe qué significa "Cat. 5" sin abrir el
canónico, lo cual rompe la idea de que la lente es autocontenida.
CORRECCIÓN: definir explícitamente los TRES NIVELES de bloque normativo:
  N1 ÍNDICE    : título de la categoría (≤25 tokens). Permitido en Capa 0, en
                 los extractos y en los artefactos inline. No es definición.
  N2 RESUMEN   : 1 frase con el criterio y la excepción (≤60 tokens). Permitido
                 SOLO dentro de un extracto CANON-EXTRACT y en las copias
                 inline de hosts degradados, porque sin filesystem no hay otra
                 forma. Contabilizado como "definición resumida": el test de
                 unicidad la permite únicamente dentro de regiones marcadas y
                 verificadas por hash.
  N3 DEFINICIÓN: texto normativo completo. Prohibido fuera de `invariants.md`.
El test Fase 2 se reescribe en función de estos niveles (N3 = 0 fugas;
N2 solo en regiones marcadas; N1 libre). Y el DoD #8 se enuncia con los tres
niveles, no con un binario.

A.4 EL HARNESS PUEDE MEDIR UN MODELO QUE NUNCA VIO LA SKILL (gravedad: alta)
--------------------------------------------------------------------------------
5.c-ter define la invocación (`claude -p` con `--model` pineado) y las trazas,
pero no define el CONTENIDO DEL PROMPT. En modo print, la skill se activa por
coincidencia de `description` — y una ejecución aislada puede no activar la
skill. Si el harness manda solo el snippet, M2/M3 miden a un modelo sin
instrucciones: las métricas saldrán Mal y parecerá un fallo de la skill.
Peor: en modo pegado, el artefacto del host (custom_gpt_instructions.md /
system_instruction.md) es justamente lo que debe estar en el prompt.
CORRECCIÓN: 5.c-ter-bis (nueva) — "Composición del prompt de evaluación":
  - Modo archivo: prompt = prompt de sistema del host (Claude Code con la
    skill instalada Y forzada: se pasa el path del `SKILL.md` o se invoca con
    el flag de skill) + `references/invariants.md` si el modelo lo pide +
    el código pegado. La traza registra EXACTAMENTE qué ficheros se leyeron.
  - Modo pegado: prompt = TEXTO ÍNTEGRO de `custom_gpt_instructions.md` o
    `system_instruction.md` (el que corresponda al host evaluado) + el snippet.
  - La traza registra un campo `contexto_cargado`: lista de ficheros leídos y
    su hash, para demostrar que el modelo tuvo acceso a la skill.
  - El harness DEBE fallar (o marcar la corrida como inválida) si
    `contexto_cargado` está vacío en modo archivo.

A.5 "ESPERABLE RESUELTO" NO ESTÁ DEFINIDO PARA EL SILENCIO (gravedad: media-alta)
--------------------------------------------------------------------------------
4.f y DoD #12/#15 definen el acierto en modo pegado como "BLOQUEANTE detectado
O `NO VERIFICADO` justificado". Falta el tercer caso: el modelo NO menciona la
categoría en absoluto (silencio). Eso no es un acierto (no resolvió el
esperable) ni un falso `PASA` (no afirmó nada) → queda fuera de la métrica.
CORRECCIÓN: definir los TRES veredictos del matcher por hallazgo esperado:
  - `DETECTADO`   : BLOQUEANTE con categoría correcta (±2 líneas).
  - `NO_VERIFICADO`: declara `NO VERIFICADO` con justificación (categoría o
                     ítem nombrado).
  - `SILENCIO`    : no menciona la categoría → NO CUENTA como acierto, y se
                     cuenta aparte como `omisiones`.
  - Falso `PASA`  : afirma PASA sobre algo no verificable → falta grave.
M3 = (DETECTADO + NO_VERIFICADO) / esperables, y se reporta `omisiones` aparte.
Sin esto, un modelo que solo dice "NO VERIFICADO" para todo pasa el 6/6.

A.6 LAS TRAZAS CONTIENEN CÓDIGO DEL USUARIO Y ACABARÁN EN GITHUB (gravedad: media)
--------------------------------------------------------------------------------
`evals/runs/<fecha>/<host>/<golden>.json` guarda el prompt enviado y la
respuesta cruda. PR-7 hace push a GitHub. Los goldens son sintéticos, pero
las trazas de pruebas manuales con código real de misión/addon acabarían
publicadas.
CORRECCIÓN: 1.n-bis (nueva): "Añadir `evals/runs/` al `.gitignore` (y a
`MANIFEST.in` exclude). Lo que se versiona es `docs/QUALITY.md` (agregado) y,
opcionalmente, un subconjunto curado y saneado de trazas en
`evals/samples/` sin código de terceros". Añadir el riesgo correspondiente.

A.7 FALTA EL DOY PARA LA SKILL EN Y FALTA EL CONTENIDO EXACTO DEL "PAQUETE INLINE"
    (gravedad: media)
--------------------------------------------------------------------------------
Dos cosas que tocan el mismo artefacto:
  (a) No hay ninguna fila del DoD para la versión EN, pese a que 7.c-bis exige
      medirla: "presupuesto medido independientemente". Añadir DoD: "SKILL.md EN:
      frontmatter ≤ 250 y cuerpo ≤ 1.200 tokens".
  (b) El "paquete inline" de los hosts degradados no está definido en su
      contenido. 3.d-bis/3.e dicen "Checklist GENERATED inline", pero un Custom
      GPT sin ese paquete no puede (i) conocer las 7 categorías, (ii) aplicar
      la puerta de calidad, (iii) declarar el fallback de modo. Sin (i) y (ii),
      el Custom GPT es un linter sin puerta.
CORRECCIÓN: definir el PAQUETE INLINE como lista cerrada y medirlo en
caracteres (no en tokens, que es lo que limita la plataforma):
  P1 índice de las 7 categorías (N1) + puerta + honestidad   [obligatorio]
  P2 fallback de modo (`Estándar + NO VERIFICADO`)            [obligatorio]
  P3 checklist priorizado por ítem (N2 resumido)              [obligatorio]
  P4 formato del informe v1 (una línea)                      [obligatorio]
  P5 criterios de modo (resumen N1)                          [opcional]
Y la regla: P1–P4 deben caber en el límite del host; si no caben, se reduce
P3 (priorizando las 7 categorías de bloqueante) y NUNCA se recortan P1, P2 o P4.
Test: el paquete inline contiene las 4 secciones obligatorias y ≤ límite.

A.8 `generated.lock.json` NO ESTÁ EN EL ÁRBOL DEL WORKSPACE (gravedad: baja)
--------------------------------------------------------------------------------
2.d-bis lo crea y el test de hash lo usa, pero el árbol de v2.3 no lo lista.
Añadirlo a `scripts/` (es un artefacto de tooling, no una referencia).

A.9 1.m DEJA UNA DECISIÓN ABIERTA QUE EL REPO YA RESUELVE (gravedad: baja)
--------------------------------------------------------------------------------
1.m dice "Declarar la decisión (3.11/3.12/3.13 o bajar a 3.10)". El repo ya
declara `requires-python = ">=3.11"` y `target-version = "py311"`: la única
opción coherente es la matriz 3.11/3.12/3.13 (bajar a 3.10 obligaría a tocar
ruff y pyright sin beneficio). Las decisiones de ejecución no deben quedar
abiertas en el plan: fija 3.11/3.12/3.13 en 1.m y elimina la alternativa.

A.10 DoD #12 Y #15 SON EL MISMO CHECK CON DOS REDACCIONES (gravedad: baja)
--------------------------------------------------------------------------------
#12: "0 falsos PASA; ≥1 NO VERIFICADO por hallazgo Cat.4/5/7".
#15: "0 trazas donde Cat. 4/5/7 aparecen como PASA".
Es el mismo script sobre las mismas trazas. Declarar #15 como subcriterio de
#12 (o fusionarlos) evita que dos personasXe Executem checks distintos y
creen "verde" por vías diferentes.

A.11 EL LÍMITE DE GEMINI QUEDA SIN FIJAR (gravedad: baja)
--------------------------------------------------------------------------------
3.e no fija presupuesto para `system_instruction.md` ("varía por modelo" en la
tabla). Fija un presupuesto propio y uniforme (p. ej. ≤ 8.000 caracteres,
igual que ChatGPT) y anota en la tabla que el límite real del host puede ser
menor; si lo es, el generador recorta P3 primero (regla de A.7).

A.12 FALTA UN RIESGO NUEVO Y FALTA EL RIESGO "SKILL ANTIGUA INSTALADA"
    (gravedad: baja)
--------------------------------------------------------------------------------
Riesgos a añadir a la tabla:
  - "El harness evalúa sin la skill cargada → métricas inválidas" (prob. media,
    impacto alto → contexto_cargado obligatorio y corrida marcada inválida).
  - "Omisiones silenciosas: el modelo no menciona la categoría y el matcher no
    las cuenta" (prob. media, impacto medio → veredicto SILENCIO explícito).
  - "El usuario conserva `arma3-sqf-review` instalada y las dos skills
    compiten por el mismo disparo" (prob. media, impacto medio → sección de
    migración en INSTALL.md 7.b y nota en el changelog 7.e).

================================================================================
PARTE B — SECUENCIA (cambios mínimos; el backbone no se toca)
================================================================================
  PR-1 + 1.j-ter  `check.py --fase PR-N` (o skipif) y alinear el gate de
                  salida de PR-1 con lo que PR-1 produce      (A.1)
        + 1.j-cua  CANON-EXTRACT: separador de anclas canónicas vs extractos (A.2)
        + 1.n-bis  `evals/runs/` al .gitignore                        (A.6)
        + 1.m      fijar 3.11/3.12/3.13 (eliminar la alternativa)    (A.9)
  PR-2 + 2.b-bis  definir los 3 niveles N1/N2/N3 y el PAQUETE INLINE
                  P1–P4 (obligatorio en P1–P4)                    (A.3, A.7)
        + 2.f-cua  la lente lleva N1 (índice) + N2 (resumen) del
                  canónico, nunca N3                                 (A.3)
  PR-3 + 3.d-ter  medir el paquete inline en caracteres y testear que
                  contiene P1–P4                                    (A.7)
        + 3.e-bis  presupuesto de caracteres para Gemini             (A.11)
  PR-4 + 4.f-bis  veredictos DETECTADO / NO_VERIFICADO / SILENCIO y
                  reporting de omisiones                            (A.5)
  PR-5 + 5.c-cua  composición del prompt de evaluación + `contexto_cargado`
                  obligatorio                                        (A.4)
  PR-7 + 7.c-ter  DoD para la skill EN                                (A.7)
  DoD  + columna "Aplicable desde"; #15 fusionada en #12             (A.1, A.10)
        + fila "SKILL.md EN dentro de presupuesto"                  (A.7)
        + fila "contexto_cargado no vacío en las trazas"             (A.4)

================================================================================
PARTE C — ESTADO
================================================================================
- Cerrado en v2.3 y NO se repite: M1/M2/M3 con denominadores; `NO VERIFICADO`
  como acierto en modo pegado; modelo de generación por regiones + lock file;
  CANON:PRECEDENCIA y CANON:PROPIEDAD; 18 comportamientos en PARIDAD;
  docs/QUALITY.md; trazas en evals/runs/; sin symlinks; 5 tests con nombre;
  ≤20 archivos de Knowledge; overflow de invariants.md; 1.f-bis (CLAUDE.md
  se genera en PR-3); regla de precedencia del wiki.
- Abierto: 12 puntos (A.1–A.12): 3 bloqueantes (A.1, A.2, A.3), 1 alto (A.4),
  1 medio-alto (A.5), 7 medios o bajos.
- Los 3 bloqueantes son de una sola naturaleza: el plan tiene TRES definiciones
  incompatibles de qué es "una definición normativa" y "qué se comprueba en
  qué fase". Unificar eso (A.1 + A.2 + A.3 en una sola decisión de diseño:
  niveles N1/N2/N3 + anclas canónicas vs extractos + gate por fase) cierra los
  tres de golpe y es la ÚNICA decisión de diseño que queda por tomar.
- Con esa decisión tomada, el plan v2.3 + esta revisión es ejecutable tal cual.
- No he ejecutado el plan ni modificado el plugin: el análisis es documental
  sobre el v2.3 y el estado real del repo (SKILL.md actual, references/
  existentes, tests/, pyproject.toml, sqf_wiki_reader.py).

================================================================================
FIN DE LAS INSTRUCCIONES v2.3 → v2.4
================================================================================
