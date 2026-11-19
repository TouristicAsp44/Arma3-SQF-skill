# Instalación y Configuración para OpenAI / Codex CLI

Esta guía detalla el uso de `arma3-sqf-skill` en entornos basados en OpenAI Codex o la CLI de OpenAI.

---

## Procedimiento

1. Coloca el archivo `AGENTS.md` en la raíz de tu espacio de trabajo o pásalo como archivo de instrucciones de contexto:
   ```bash
   cp integrations/openai/AGENTS.md AGENTS.md
   ```
2. Si invocas la CLI de OpenAI o un agente que soporta archivos de instrucciones del sistema, referencia `AGENTS.md` como system prompt o system instructions.
3. Asegúrate de que las herramientas locales (`sqf_orchestrator.py`, `sqf_wiki_reader.py`) puedan ser ejecutadas mediante llamadas a herramientas (function calling / tool calling) si el agente soporta ejecución de terminal.

---

## Verificación

Para comprobar que el adaptador y las reglas cumplen con los estándares de validación:
```bash
python scripts/check.py --fase PR-4
```
Salida esperada: `[ OK  ] adaptadores host — X test(s) en verde`.
