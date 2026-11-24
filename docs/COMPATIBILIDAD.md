# Matriz de Compatibilidad y Protocolos de Degradación por Host

Este documento establece la matriz oficial de soporte de `arma3-sqf-skill` en los diferentes entornos de ejecución (hosts), detallando capacidades soportadas, funciones degradadas, límites de plataforma y mecanismos de compensación.

---

## 1. Matriz de Compatibilidad por Host

| Host | Mecanismo | Lectura de archivos | Soporte | Qué se pierde | Límite | Compensación (fichero + mecanismo) | Fallback de modo |
| :--- | :--- | :---: | :---: | :--- | :--- | :--- | :--- |
| **Antigravity** | Agente nativo con tools / CLI | Sí (completo) | **Completo** | Ninguna (orquestación de agentes nativa, lectura de workspace y ejecución de scripts locales; definiciones exclusivas en `agents/` documentadas en [`agents/README.md`](../agents/README.md)). | Ventana de contexto del modelo activo. | `skills/arma3-sqf-skill/SKILL.md` + lectura de `references/` y CLI `scripts/sqf_orchestrator.py`. | No requiere (ejecuta `sqf_orchestrator.py --mode-query`). |
| **Claude Code** | CLI interactiva en repo (`CLAUDE.md`) | Sí (completo) | **Completo** | Subagentes paralelos simultáneos (sustituido por lentes modulares secuenciales). | Límite de contexto del modelo Claude (200k tokens). | `integrations/claude/CLAUDE.md` + lectura bajo demanda de `references/lens-*.md` y CLI `scripts/sqf_orchestrator.py`. | No requiere (ejecuta `sqf_orchestrator.py --mode-query`). |
| **Claude Desktop** | Modo Pegado o subida de Skill (`arma3-sqf-skill.zip`) | No (pegado) / Sí (sandbox) | **Parcial** | En modo pegado pierde ejecución local y lectura de disco; en Claude AI Skills dispone de entorno sandbox completo. Evidencia en `NO VERIFICADO` hasta registrar trazas reales (R5). | Ventana de contexto estándar; sin terminal nativa interactiva. | `integrations/claude/claude_desktop_paste.md` (pegado) o importación directa de `arma3-sqf-skill.zip`. | En modo pegado: `Estándar + NO VERIFICADO` (prohibido Micro manual). |
| **Cursor** | Reglas de proyecto (`.cursorrules` / `.cursor/rules/`) | Sí (completo) | **Parcial** | Orquestación multi-paso autónoma de subagentes en hilos de conversación independientes. | Ventana de contexto del modelo activo en Cursor. | `integrations/cursor/.cursorrules` + inyección de lentes de disciplina como reglas adicionales. | Si no ejecuta CLI: `Estándar + NO VERIFICADO` (prohibido Micro manual). |
| **OpenAI / Codex** | Instrucciones de agente (`AGENTS.md`) / CLI | Variable según entorno | **Parcial** | Subagentes multi-rol concurrentes y orquestación dinámica nativa de subprocesos. | Tokens de contexto de OpenAI; disponibilidad de tool-calling. | `integrations/openai/AGENTS.md` con checklist condensado N2 inline y rutas relativas. | Si no ejecuta CLI determinista: `Estándar + NO VERIFICADO` (prohibido Micro manual). |
| **ChatGPT Custom GPT** | Instructions + Knowledge (RAG) | No directa (solo RAG no determinista) | **Degradado** | Modo archivo determinista, ejecución de sqflint/a3ref local; verificación estricta de Cat. 4, 5 y 7 pasa a `NO VERIFICADO`. | <= 8.000 caracteres en Instructions; <= 20 archivos en Knowledge. | `integrations/chatgpt/custom_gpt_instructions.md` (paquete inline P1–P4) + `integrations/chatgpt/knowledge_manifest.md` (18 archivos curados). | `Estándar + NO VERIFICADO` (prohibido conceder Micro por criterio manual). |
| **Google Gemini / AI Studio** | Instrucción de sistema (System Instruction) | No (sin acceso local) | **Degradado** | Ejecución local de linters/scripts; lectura de referencias del repositorio en disco. | Sin ejecución de terminal nativa en la UI web de AI Studio. | `integrations/gemini/system_instruction.md` (paquete inline P1–P4 autocontenido en texto plano). | `Estándar + NO VERIFICADO` (prohibido conceder Micro por criterio manual). |

---

## 2. Reglas Invariables de Degradación

1. **Protocolo para Hosts Degradados (ChatGPT Custom GPT, Gemini, Claude Desktop pegado)**:
   - Todo host que no disponga de acceso directo a la terminal local para ejecutar `scripts/sqf_orchestrator.py` debe aplicar el **paquete inline P1–P4**.
   - Los artefactos de estos hosts no contienen enlaces `file://` ni rutas markdown a archivos que el modelo no pueda leer en su entorno (Regla R3).

2. **Fallback Universal de Modo de Análisis**:
   - En **TODOS** los hosts degradados, ante la imposibilidad de ejecutar el cálculo determinista `--mode-query`:
     $$\text{Modo por defecto} = \textbf{Estándar} \quad (\text{estado: } \textbf{NO VERIFICADO})$$
   - Está **terminantemente prohibido** conceder o auto-asignar el modo `Micro` mediante criterio manual o subjetivo.

3. **Tratamiento de Categorías Dependientes de Entorno en Hosts Degradados**:
   - **Cat. 1 (Sintaxis / Scope)**: Se audita mediante inspección semántica exhaustiva de variables y `private`/`params`.
   - **Cat. 2 (Softlocks / Init)**: Se audita mediante análisis estático de bucles y llamadas de inicialización.
   - **Cat. 3 (Servidor Dedicado)**: Se audita aplicando la invariante de que `player` es `objNull` y prohibiendo comandos UI en rutas de servidor.
   - **Cat. 4, 5 y 7 (Scheduler / CfgRemoteExec / Frameworks)**: Al no disponer de análisis de configuración de proyecto ni verificación determinista de `canSuspend`, cualquier ítem no evidente en el fragmento analizado debe marcarse obligatoriamente como `NO VERIFICADO` (Principio de Honestidad Técnica, Regla R1).

---

## 3. Estado de Evidencia por Host (PR-5-bis / Track C)

La matriz de arriba describe **capacidades declaradas**. El estado medido de calidad es otro
documento y no se deduce de esta tabla: solo hay evidencia de ejecución en el host marcado.

| Host | Bloque / Modo | Cobertura medida | M2 / M3 | Estado |
| :--- | :--- | :--- | :--- | :--- |
| **Antigravity** | Bloque 1 (Señalizado) — Archivo | 14/14 goldens, N=3 (42 trazas) | M2 = 83,3 % (mín 75,0 %) | **NO PASA OBJETIVO** (≥ 90 %): 4 omisiones, 0 falsos PASA |
| **Antigravity** | Bloque 1 (Señalizado) — Pegado | 14/14 goldens, N=3 (42 trazas) | M3 = 38/39 (97,4 %), 0 FALSO_PASA | **NO PASA OBJETIVO** (100 %): 1 omisión |
| **Antigravity** | Bloque 2 (Ciego) — Archivo | 6/6 goldens, N=3 (18 trazas) | M2 = 100 % (12/12) | **PASA**: 0 omisiones, 0 falsos PASA (Cat. 3–7) |
| **Antigravity** | Bloque 2 (Ciego) — Pegado | 6/6 goldens, N=3 (18 trazas) | M3 = 21/21 (100 %), 0 FALSO_PASA | **PASA**: honestidad verificada en b05 (NO_VERIFICADO) |
| **Claude Code** | Archivo | 0/20 | — | `NO VERIFICADO` (sin trazas) |
| **Claude Desktop** | Pegado | 0/20 | — | `NO VERIFICADO` (sin trazas) |
| **Cursor** | Archivo | 0/20 | — | `NO VERIFICADO` (sin trazas) |
| **OpenAI / Codex** | Archivo | 0/20 | — | `NO VERIFICADO` (sin trazas) |
| **ChatGPT Custom GPT** | Pegado | 0/20 | — | `NO VERIFICADO` (sin trazas) |
| **Google Gemini / AI Studio** | Pegado | 0/20 | — | `NO VERIFICADO` (sin trazas) |

- Modelo real de la medición: `gemini-3.8-flash-high` v1.0, temperatura 0,2.
- Las 120 trazas verifican el `sha256` de su `contexto_cargado` contra los ficheros actuales del
  repo (Regla R3); 0 descartadas por contexto no reproducible.
- Detalle completo, metodología y límites: [`docs/QUALITY.md`](QUALITY.md).
- **Distinción metodológica:** El Bloque 1 (señalizado, 13/14 con comentarios) mide la
  **conformidad del informe** y la **ausencia de falsos positivos**. El Bloque 2 (no señalizado / ciego, 0/6 con comentarios) mide la **generalización cognitiva real a ciega** ante código sin pistas.
- **No se afirma equivalencia de calidad con el plugin original** para los hosts sin trazas (Regla R5).
- **Lectura honesta del resultado medido:** el modelo detecta de forma fiable el defecto principal de
  cada fichero (100 % en el dataset ciego, bloque 2), pero su *recall* sobre defectos secundarios
  dentro del mismo fichero es parcial e inconsistente (`g03:L4` 1/3 en archivo y 2/3 en pegado;
  `g08:L11` 1/3 en archivo y 3/3 en pegado). Por eso M2 en modo archivo (83,3 %) y M3 (97,4 %)
  quedan por debajo de sus objetivos y se publican como `NO PASA OBJETIVO`, no como FAIL del producto:
  el límite es de exhaustividad del modelo, no de la skill. Detalle en [`docs/QUALITY.md`](QUALITY.md) (§5 y §6) y en `CHANGELOG.md`.
