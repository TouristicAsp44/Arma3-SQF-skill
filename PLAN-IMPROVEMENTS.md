================================================================================
INSTRUCCIONES PARA MEJORAR, ACTUALIZAR Y OPTIMIZAR ESTA PLANEACIÓN
================================================================================

0. PREMISA DE REVISIÓN (léela antes de tocar nada)
--------------------------------------------------------------------------------
El plan actual mezcla DOS productos distintos y los trata como uno:
  (A) Una SKILL PORTÁTIL = prompt + referencias + scripts opcionales.
      Esto es lo que realmente pide el objetivo ("usar en diversos modelos de IA").
  (B) Un SERVICIO DISTRIBUIDO = FastAPI + MCP + Cloudflare Tunnel + PyPI +
      Hugging Face Spaces + Google Docs + GitHub Release.
      Esto solo sirve a UN ecosistema (ChatGPT Custom GPTs) y trae carga operativa
      real (tunnel, dominios estables, revisión de OpenAI, exposición de código).
Regla de optimización: (A) es el camino crítico y debe completarse y validarse
primero; (B) se convierte en un "Track B" opcional y reversible.

1. REESCRITURA DEL OBJETIVO CENTRAL
--------------------------------------------------------------------------------
1.1 Sustituye el "Objetivo central" por uno que mida lo que importa:
     "Convertir arma3-sqf-review en una skill portable (SKILL.md + references/
      scripts opcionales) instalable en Claude Code/Desktop, Cursor, Codex y
      cualquier host que lea Markdown, conservando la calidad de análisis
      (detección de bloqueantes + informe de estados) con presupuesto de tokens
      declarado y medido."
1.2 Elimina de todo el documento la frase "manteniendo la misma calidad de
    análisis" como afirmación no verificada: sustituye por un objetivo medible
    (ver 9.1, evals con goldens).
1.3 Declara explícitamente el no-objetivo: "No es un producto de hosting; el
    servidor HTTP es opcional y no forma parte de la promesa de portabilidad."

2. RECONFIGURACIÓN DE FASES (el error de secuenciación más grave del plan)
--------------------------------------------------------------------------------
2.1 Elimina el'eje temporal "Semana 1..5" por fases. No hay capacidad de
    ejecución declarada; usa PRs numerados (PR-1..PR-7) con criterio de entrada
    y de salida. El calendario es la parte del plan que menos valor aporta.
2.2 Nueva secuencia de PRs:
    PR-1  Sanear el repo (rutas hardcodeadas, nombres, estructura)  [antes que todo]
    PR-2  Núcleo portable: SKILL.md + references/ + progressive disclosure
    PR-3  Per-Host adapters (Claude/Cursor/Codex/generic) + prueba manual real
    PR-4  Modo degradado sin ejecución de herramientas (checklist en prompt)
    PR-5  Eval harness con goldens (calidad probada, no afirmada)
    PR-6  Track B opcional: MCP/HTTP/ChatGPT Actions
    PR-7  Distribución y publicación (con gate de aprobación explícito)
2.3 Regla de dependencia dura: ningún PR que dependa de infraestructura externa
    (tunnel, PyPI, OpenAI, Drive) puede bloquear la salida del producto
    principal. Si un PR de Track B falla, el producto sigue siendo usable.
2.4 Mueve "Publicar en PyPI", "GitHub Release", "Google Docs" y "tunnel" del
    camino crítico al PR-7, y añade en cada uno un gate explícito
    "requiere aprobación del usuario".

3. SANEAMIENTO DEL NÚCLEO (Phase 1) — AMPLIAR Y PRIORIZAR
--------------------------------------------------------------------------------
3.1 La tarea 1.4 (ruta hardcodeada en sqf_wiki_reader.py) es correcta pero está
    sobrerrepresentada: conviértela en el PR-1 e inclúyela en la checklist
    "cero rutas absolutas" del CI (test que falle si aparece "EDEN EDITOR",
    "C:\\Users", "Path.home()" en el código de runtime).
3.2 Añade el resto de saneamientos que el plan NO menciona:
    - a) `skills/arma3-sqf-review/` -> renombrar a `skills/arma3-sqf-skill/`
       (el plan renombra plugin.json y pyproject.toml pero deja el nombre de la
       skill y del directorio con el nombre viejo: inconsistencia que rompe el
       descubrimiento por nombre en hosts que indexan por folder name).
    - b) TODAS las rutas invocadas desde dentro del prompt están escritas como
       `skills/arma3-sqf-review/scripts/...` (relativas a la raíz del plugin).
       Deben ser relativas a la RAÍZ DE LA SKILL y resolverse en cualquier host.
       Especifica la convención que se usará y aplícala en los 3 archivos:
       SKILL.md, references/*.md, prompts/*.md.
    - c) `python` -> `python3` / `py -3` con nota de fallback; los bloques
       ```bat``` son específicos de Windows y no portables.
    - d) `rules/AGENTS.md` usa `trigger: always_on` (mecanismo de Antigravity).
       Conviértelo en `references/invariants.md` + una copia瘦 para CLAUDE.md;
       nunca dependas de un frontmatter que solo entiende un host.
    - e) `agents/*.md` (11 subagentes): el plan nunca decide su destino.
       DECISIÓN: no son portables (requieren runtime multi-agente). Conviértelos
       en `references/lenses/<disciplina>.md` (markdown plano, inyectado bajo
       demanda) y conserva los originales en `legacy/agents/` como referencia.
    - f) `skills/arma3-sqf-review/scripts/requirements.txt` duplicado del
       raíz: consolida en uno solo y fija versiones (ver 8.3).
3.3 Reutiliza el motor que YA EXISTE en vez de crear uno paralelo:
    `sqf_orchestrator.py --mode-query` y `--lint` ya son el punto de entrada
    determinista de triaje y de linter. El plan crea 3 tools MCP nuevas
    (sqf_lint, biki_lookup, sqf_guidelines) que replicarían esa lógica y, por
    el SKILL.md existente ("nunca apliques mapeos divergentes de severidad"),
    abrirían una segunda fuente de verdad para los bloqueantes.
    DECISIÓN: los wrappers MCP deben ser candidatos FINOS (thin) sobre el
    motor existente y deben delegar, no reimplementar, el cálculo de severidad.
3.4 Separa "modo con archivo en disco" de "modo pegado en el chat". El SKILL.md
    actual asume que hay archivos .sqf en el proyecto; en ChatGPT/Gemini sin
    sistema de archivos eso no es cierto. Define ambos modos explícitamente y
    que el modo pegado degrade a checklist (ver PR-4).

4. FASE 2 (CORE PROMPT) — CORREGIR EL PRESUPUESTO, NO SOLO EL TEXTO
--------------------------------------------------------------------------------
4.1 CORRECCIÓN CRÍTICA: el objetivo de "~800 tokens" es incompatible con el
    contenido exigido. La sección actual de SKILL.md ocupa ~29.918 bytes
    (~7.500 tokens) e incluye: 7 parámetros de Perfil de Proyecto, reglas
    CBA/ACE3, tabla de modos, matriz de participación, flujo de 10 pasos,
    definición normativa de Bloqueante (7 subpuntos), Puerta de Calidad
    infranqueable, Paquete de contexto, tabla de propiedad de reglas, rúbrica
    de severidad, reglas de entrega. Eso NO cabe en 800 tokens.
    DECISIÓN: fija un presupuesto realista y por capas, y mídelo con un test:
      - Capa 0 (siempre en sistema): <= 1.200 tokens  -> invariantes +
        criterios de activación + cómo usar las referencias.
      - Capa 1 (al detectar señal): +400-900 tokens    -> una lente.
      - Capa 2 (bajo demanda): references/*.md.
      - Total por turno acotado: <= 2.500 tokens.
4.2 La calidad del plugin no vive en el token count, vive en dos artefactos
    que el plan nuevo amenaza con perder:
      (a) la definición normativa de BLOQUEANTE (7 categorías),
      (b) la PUERTA DE CALIDAD INFRANQUEABLE + Informe de estados por ítem
          (PASA / NO PASA / NO VERIFICADO / NO APLICA).
    Ambos deben sobrevivir al port. Si se caen, el port es un downgrade.
4.3 El presupuesto del prompt NO debe incluir el Perfil de Proyecto completo
    (7 parámetros) en todos los turnos: pásalo como bloque de contexto de una
    sola vez y reutilízalo; el prompt debereferir "perfil declarado" en vez de
    repetir los 7 campos.
4.4 Convierte la tabla de "Presupuesto de Tokens por Configuración" en un
    artefacto medible: script `scripts/measure_tokens.py` con tiktoken que
    falle en CI si se supera el presupuesto. Una cifra escrita a mano no es un
    criterio de aceptación.
4.5 Reemplaza "docs auxiliares que se inyectan si se detecta la señal" por un
    mecanismo real: los hosts de skill leen archivos bajo demanda con
    Read/grep; el prompt debe indicar el NOMBRE EXACTO del archivo a leer y el
    disparador (patrón) que lo activa, para que el modelo lo abra. Sin eso,
    "progressive disclosure" es solo intención.

5. ADAPTADORES POR HOST — UNIFICAR Y CORREGIR
--------------------------------------------------------------------------------
5.1 No trates cada host como una fase de desarrollo. Son artefactos pequeños
    derivados del mismo núcleo. Convierte la Fase 3 y la Fase 4 en un solo
    PR (PR-3) con una tabla de 5-6 filas, una por host.
5.2 Matriz de portabilidad por host (inclúyela en el plan):
      Claude Code       : SKILL.md nativo + CLAUDE.md        -> soporte completo
      Claude Desktop    : MCP (stdio) o paste del prompt     -> parcial
      Cursor            : .cursor/rules + MCP                -> parcial
      Codex / OpenAI    : AGENTS.md / instructions           -> parcial
      ChatGPT Custom GPT: instructions + Action + Knowledge  -> degradado
      Gemini/AI Studio  : system instruction + Function calling -> degradado
5.3 ERROR CONCRETO A CORREGIR en 4.2: `cloudflared tunnel --url` genera una URL
    ALEATORIA en cada ejecución. Un Custom GPT con una Action apuntando a esa
    URL se rompe en cuanto el túnel se reinicia. Si el Track B sigue vivo,
    exige un túnel NOMBRADO con hostname estable (o dominío propio) y
    documenta la caducidad del certificado/liveness como riesgo conocido.
5.4 En 3.2, el snippet de Claude Desktop debe usar la forma real del campo
    (`command`: ruta absoluta al intérprete o `uvx`/`python -m`), incluir
    `cwd`, y un ejemplo Windows y otro POSIX. Un snippet con "/ruta/a/tu/wiki"
    es pseudocódigo y no es instalable.
5.5 Los ficheros de contexto de la skill (sqf-standards.md, checklist,
    wiki-cache) deben ser AUTOCONTENIDOS y razonablemente pequeños: el
    límite de Knowledge de Custom GPT (archivos por fichero) y el coste de
    indexación hacen inviable subir documentos grandes sin trocear.
5.6 La entrega por host debe incluir un "smoke test" de 3 casos idénticos
    (los 3 de 3.3): ya existen en el plan, conviértelos en una tabla de
    resultados medidos (host x caso x veredicto), no en un checkbox.

6. TRACK B: SERVIDOR MCP / API — REBAJAR Y CORREGIR
--------------------------------------------------------------------------------
6.1 Reetiqueta las Fases 3/4/5 actuales como "Track B (opcional)" y muévelas
    detrás del PR-5. El PR-6 no bloquea al producto.
6.2 En el Track B, la prioridad real NO es "3 herramientas MCP": es
      (1) un único endpoint POST /api/analyze que ejecute el motor existente y
          devuelva el informe estructurado (bloqueantes + estados),
      (2) un GET /api/wiki para consultas BIKI,
      (3) un POST /api/mode para el triaje determinista.
    Tres endpoints atómicos obligan al modelo a encadenar llamadas y a
    reconciliar severidades: exactamente el fallo que el SKILL.md prohíbe.
6.3 La superficie HTTP (FastAPI) es un riesgo de seguridad y una fuga de
    código SQF de(addons/misiones) a un servicio público. Si el Track B se
    mantiene: declarar explícitamente "opt-in, sin datos persistentes, con
    límite de tasa y clave de API", y escribir la postura de privacidad en el
    README. Hoy el plan no dice nada de privacidad.
6.4 Cloudflare Tunnel NO es una dependencia de una skill. Si el objetivo es
    "que otros modelos lo usen", la ruta portable es: prompt + archivos +
    scripts opcionales + instrucciones por host. El servidor es para quien
    quiera automatizar a escala.
6.5 Elimina la dependencia de Hugging Face Spaces como mitigación mentioned en
    Riesgos: no es un plan de hosting válido (cold start, sin SLA, recursos
    efímeros). Si se mantiene hosting externo, es una decisión a tomar con
    criterios, no una mitigación de una línea.

7. DOCTENIBILIDAD Y CONSISTENCIA DEL PROPIO PLAN
--------------------------------------------------------------------------------
7.1 Hay contradicciones que el plan debe eliminar explícitamente:
    (a) "Sin push a GitHub" vs. Fase 1.6 "verificar CI verde en GitHub Actions"
        y vs. Fases 4.4/5.x que publican. RESOLUCIÓN: dos puertas:
        CI local (pytest) obligatorio en cada PR; CI remoto y publicaciones
        solo tras "Release gate" con aprobación del usuario.
    (b) "Todo el desarrollo en arma3-sqf-skill" vs. el árbol que aún muestra
        `skills/arma3-sqf-review/`. Resuelve renombrando (ver 3.2a).
    (c) El objetivo "misma calidad" vs. la supresión de la puerta de calidad
        en el prompt nuevo (ver 4.2).
7.2 Criterios de Aceptación: reescríbelos como tabla con MÉTRICA + MÉTODO DE
    MEDICIÓN + RESPONSABLE. La #4 ("<1.500 tokens medido con tiktoken") es la
    única bien escrita: conviértela en test automatizado (ver 4.4). La #3
    (Custom GPT detecta fuga de scope vía Action) depende de una revisión de
    OpenAI que puede tardar: sustitúyela por una prueba local del endpoint +
    el smoke test en la UI, y marca la revisión de OpenAI como "no bloqueante".
7.3 Añade DoD que hoy no existen:
    - Doc de portabilidad por host (5.2) con resultados reales, no theory.
    - Cero rutas absolutas (test automatizado).
    - Los 7 criterios de Bloqueante y la Puerta de Calidad presentes y
      verificables en la versión portable (test que compare el conjunto de
      secciones).
    - Eval goldens: >= N casos con deteccion esperada (ver 9).
    - Budget de tokens respetado en todas las capas (test).
7.4 Riesgos: reescribe la tabla. Hoy la mayoría de filas son suposiciones no
    verificadas. Añade al menos: "coste de mantenimiento del Track B",
    "deriva entre la skill portable y el plugin original (fuente de verdad
    duplicada)", "dependencia de sqflint no disponible en el host",
    "el modelo no usa las referencias por no leerlas (progressive disclosure
    que no ocurre)".

8. CALIDAD DE IMPLEMENTACIÓN (detalles que el plan omite)
--------------------------------------------------------------------------------
8.1 Añade un `CONTRIBUTING`/`docs/PORTING.md` con la checklist de paridad:
    cada elemento del plugin original debe mapearse a uno de estos estados en
    la skill portable: PORTADO / PORTADO-REDUCIDO / NO APLICABLE (con motivo).
    Esto es lo que evita una degradación silenciosa.
8.2 Compatibilidad de versiones: fija Python >= 3.10 (el CI ya cubre 3.11-3.13);
    fija el rango del SDK MCP; fija la versión de sqflint/dependencias; declara
    la matriz de SO (Windows/Linux/macOS) en el README.
8.3 No fijes `mcp[cli]>=1.0` en abierto: el SDK MCP cambia de API con
    frecuencia; usa un rango minor acotado y una nota de compatibilidad.
8.4 Añade en el prompt portable el "principio de honestidad técnica" como
    regla de primer nivel: si no se pudo ejecutar el linter o el wiki lookup,
    el resultado es NO VERIFICADO, nunca PASA. Es la regla que más se degrada
    al portar a un modelo sin ejecución.
8.5 Añade el modo "sin herramientas" al prompt: checklist en Markdown para
    que el modelo pueda auditar código pegado sin acceso a scripts.
8.6 Localizacion: hoy el DoD exige "documentación en español e inglés" pero el
    SKILL.md, standards y checklist son solo en español, y un prompt en español
    reduce la calidad del disparador en modelos defaults. Decide: mantener
    ES como fuente y generar EN, o al menos un `description` bilingüe en el
    frontmatter (que es lo que el host lee para decidir si activa la skill).
8.7 Nombra y descubre la skill: el `description` del frontmatter es lo que el
    host lee para activar; hoy es un párrafo largo con "No usar para...".
    Reescríbelo con: qué hace + cuándo activarla + cuándo NO + 4-6 disparadores
    concretos (remoteExec, publicVariable, JIP, HC, init.sqf, CfgRemoteExec).
    El plan actual no toca el frontmatter en ninguna fase: es el punto de entrada
    de la portabilidad.

9. EVALUACIÓN DE LA CALIDAD (falta por completo)
--------------------------------------------------------------------------------
9.1 Crea evals/ con goldens: N snippets SQF (el repo ya tiene
    fixtures/test_scope.sqf) y, por cada uno, la lista de hallazgos esperados
    (bloqueante/sugerencia/no verificado). Criterio: deteccion >= 90% de los
    bloqueantes esperados y 0 falsos positivos bloqueantes.
9.2 Evalua por host y por modelo: la MISMA skill en Claude Code, Cursor y ChatGPT
    sobre los mismos goldens, y registra una tabla de resultados. Esto es lo que
    justifica (o refuta) el claim "la misma calidad en diversos modelos".
9.3 Define el presupuesto de tokens por caso (con y sin参考资料) y por host.

10. CI, CALIDAD Y ENTREGABLES
--------------------------------------------------------------------------------
10.1 Reemplaza el checklist de DoD por bloques: ESTRUCTURA, NOMBRADO,
     COMPORTAMIENTO, DOCUMENTACIÓN, PUBLICACIÓN; cada uno con criteria
     verificable. Usa el mismo formato por ítem del plugin (PASA / NO PASA /
     NO VERIFICADO) para que el propio port se audite con el mismo rigor que
     audita SQF.
10.2 El repo ya tiene tests (test_wiring, test_sqf_wiki_reader, test_run_sqflint,
     test_orchestrator_loop, test_sqf_models). El plan dice "reutilizando
     conftest.py" pero no nombra los tests existentes que deben seguir pasando
     tras el rename. Enumerar esos tests en el PR-1 como "no debe romperse".
10.3 Añade un test de contrato del protocolo MCP (tools/list + tools/call con
     esquemas) para el Track B, y un test de golden del informe estructurado
     (formato de linea `archivo:linea (disciplina): descripcion` y `RESUMEN:`),
     porque ese formato es hoy el contrato entre el script y los subagentes.

11. ORDEN DE EJECUCIÓN RESULTANTE (sustituye las 5 fases)
--------------------------------------------------------------------------------
PR-1 Sanear repo (rutas, nombres, frontmatter, estructura) + test de rutas
PR-2 Núcleo portable: SKILL.md en capas + references/ + scripts wrappers
PR-3 Per-host adapters (5 hosts) + smoke tests medidos
PR-4 Modo degradado sin ejecución de herramientas
PR-5 Evals goldens + medición de tokens + tabla de paridad por ítem
PR-6 (opcional) Track B: MCP/HTTP/ChatGPT Action, con tunnel de hostname estable
PR-7 Release: README/INSTALL/EN-ES/publish, con gate de aprobación

================================================================================
FIN DE LAS INSTRUCCIONES
================================================================================
