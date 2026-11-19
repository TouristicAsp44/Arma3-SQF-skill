# Protocolo de Ejecución de Goldens para Hosts Externos (PR-5)

Este documento describe el procedimiento normativo para ejecutar la suite de goldens (`evals/goldens/`) en hosts con LLMs reales (Claude Code, Antigravity, Cursor, OpenAI Codex, ChatGPT, Gemini), capturar la evidencia y registrar trazas reproducibles.

---

## 1. Requisitos de Ejecución

Para generar evidencia válida que pueda poblar las métricas **M2** y **M3** en `docs/QUALITY.md`, se requiere:
- Un entorno con acceso a modelo de lenguaje real (API key activa o suscripción interactiva).
- Repositorio situado en la raíz de trabajo: `arma3-sqf-skill/`.
- Temperatura fijada entre `0.1` y `0.3` (baja variabilidad / determinismo).
- Parámetro $N = 3$ ejecuciones independientes por caso para medir media y dispersión.

---

## 2. Protocolo por Modo de Ejecución

### Modo A: Modo Archivo (Claude Code, Cursor, Codex con filesystem)
1. Para cada golden en `evals/goldens/<id>/`:
   - El agente debe leer `evals/goldens/<id>/code.sqf` (y `description.ext` si existe).
   - Contexto cargado: `skills/arma3-sqf-skill/SKILL.md` + lentes pertinentes.
2. Prompt estándar:
   ```
   Actúa como revisor experto SQF de Arma 3 siguiendo skills/arma3-sqf-skill/SKILL.md.
   Audita el archivo evals/goldens/<id>/code.sqf.
   Emite tu informe respetando estrictamente el esquema REPORT_SCHEMA_VERSION = 1:
   [BLOQUEANTE|SUGERENCIA|NO_VERIFICADO] archivo:linea (disciplina): descripcion
   RESUMEN: bloqueantes=N; sugerencias=N; no_verificado=N
   ```
3. Guarda la respuesta sin editar en la traza JSON.

### Modo B: Modo Pegado (ChatGPT, Gemini, Claude Desktop)
1. Inyecta primero el paquete inline correspondiente:
   - ChatGPT: `integrations/chatgpt/custom_gpt_instructions.md`
   - Gemini: `integrations/gemini/system_instruction.md`
   - Claude Desktop: `integrations/claude/claude_desktop_paste.md`
2. Pega el contenido textual de `code.sqf`.
3. Guarda la respuesta emitida.

---

## 3. Esquema Formal de la Traza (`evals/runs/<fecha>/<host>/<golden>.json`)

Toda traza debe guardarse obligatoriamente en un archivo JSON bajo la ruta:
`evals/runs/<YYYY-MM-DD>/<host_id>/<golden_id>.json`

```json
{
  "golden_id": "g01_syntax_scope",
  "host": "claude-code",
  "modelo": "claude-3-7-sonnet-20250219",
  "version": "1.0",
  "temperatura": 0.2,
  "fecha": "2026-11-18T15:00:00Z",
  "modo_evaluacion": "archivo",
  "prompt_enviado": "...",
  "respuesta_cruda": "REPORT_SCHEMA_VERSION: 1\n[BLOQUEANTE] code.sqf:4 (Scope): ...\nRESUMEN: bloqueantes=1; sugerencias=0; no_verificado=0",
  "contexto_cargado": [
    {
      "archivo": "skills/arma3-sqf-skill/SKILL.md",
      "sha256": "..."
    }
  ],
  "veredicto_por_hallazgo": [
    {
      "categoria": 1,
      "esperado_linea": 4,
      "detectado_linea": 4,
      "veredicto": "DETECTADO"
    }
  ],
  "bloqueantes_detectados": 1,
  "sugerencias_detectadas": 0
}
```

---

## 4. Ingesta en el Harness

Una vez guardadas las trazas en `evals/runs/`, ejecuta el harness para calcular M2 y M3 y actualizar la tabla de calidad:

```bash
python evals/harness.py --write
```

El harness verificará criptográficamente cada traza y volcará los resultados consolidados en `docs/QUALITY.md`.
