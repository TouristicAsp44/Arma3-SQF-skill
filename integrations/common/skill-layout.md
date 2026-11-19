# Distribución y Estructura por Host — arma3-sqf-skill

Este documento define la estructura final de archivos de `arma3-sqf-skill`, la convención de rutas y la tabla de correspondencia de archivos instalables según el entorno de ejecución (host).

---

## 1. Convención de Rutas Relativas

Todas las rutas dentro de los documentos normativos, adaptadores y código de la skill son **relativas a la raíz de la skill**:
```
skills/arma3-sqf-skill/
```
Ejemplos de referencias válidas:
- `references/invariants.md`
- `references/lenses/locality.md`
- `scripts/sqf_orchestrator.py`
- `references/report_format.md`

Esta convención garantiza portabilidad universal sin suposiciones sobre directorios del sistema de archivos local ni rutas absolutas.

---

## 2. Estructura General de la Skill

```
arma3-sqf-skill/
├── skills/
│   └── arma3-sqf-skill/
│       ├── SKILL.md                          <- Entrada unificada (Capa 0)
│       ├── references/
│       │   ├── invariants.md                 <- Fuente canónica de reglas e invariantes
│       │   ├── sqf-standards.md              <- Estándar de codificación SQF
│       │   ├── rubrica.md                    <- Rúbrica de severidad y participación
│       │   ├── report_format.md              <- Contrato de esquema v1 del informe
│       │   ├── checklist-entrega.md          <- Checklist de cierre y entrega
│       │   ├── diferencial-misiones-addons.md<- Contexto misiones vs addons
│       │   ├── wiki-cache.md                 <- Resumen local de sintaxis BIKI
│       │   ├── lenses/                       <- 6 Lentes de disciplina
│       │   └── workflows/                    <- 5 Flujos de trabajo
│       └── scripts/
│           ├── sqf_orchestrator.py           <- Motor de orquestación y linter
│           ├── sqf_wiki_reader.py            <- Lector de documentación oficial
│           ├── wiki_db_builder.py            <- Generador de base FTS5 SQLite
│           └── sqf_models.py                 <- Modelos de datos del informe
├── integrations/
│   ├── claude/                               <- Adaptador Claude Code y Desktop
│   ├── cursor/                               <- Adaptador Cursor (.cursorrules)
│   ├── openai/                               <- Adaptador OpenAI / Codex (AGENTS.md)
│   ├── chatgpt/                              <- Adaptador ChatGPT Custom GPT
│   ├── gemini/                               <- Adaptador Google Gemini / AI Studio
│   └── common/                               <- Esquema y convenciones compartidas
├── scripts/
│   ├── check.py                              <- Release gate local por fases
│   ├── generate_inline_packages.py           <- Generador de paquetes P1–P4
│   └── measure_tokens.py                     <- Verificador de presupuesto de tokens
├── docs/
│   ├── COMPATIBILIDAD.md                     <- Matriz de compatibilidad y degradación
│   ├── PARIDAD.md                            <- Matriz de paridad de migración
│   └── QUALITY.md                            <- Evidencia y métricas de calidad
└── tests/                                    <- Suite de pruebas deterministas
```

---

## 3. Matriz de Destino de Archivos por Host

| Host | Archivos que se copian o configuran | Destino en el Host | Modo de Operación |
| :--- | :--- | :--- | :--- |
| **Claude Code** | `integrations/claude/CLAUDE.md` | Raíz del proyecto / repo | Modo Archivo Completo (acceso a `references/` y `scripts/`) |
| **Claude Desktop** | `integrations/claude/claude_desktop_config_snippet.json` | `claude_desktop_config.json` | Modo MCP Server (Track B) |
| **Claude Desktop** | `integrations/claude/claude_desktop_paste.md` | Chat inicial del usuario | Modo Pegado (Host degradado P1–P4) |
| **Cursor** | `integrations/cursor/.cursorrules` | `.cursorrules` en raíz | Modo Reglas (lee `references/` bajo demanda) |
| **OpenAI / Codex** | `integrations/openai/AGENTS.md` | `AGENTS.md` en raíz | Modo Instrucciones / CLI |
| **ChatGPT Custom GPT** | `integrations/chatgpt/custom_gpt_instructions.md` | Campo "Instructions" en GPT Builder | Host Degradado (Instrucciones inline P1–P4) |
| **ChatGPT Custom GPT** | 18 archivos de `integrations/chatgpt/knowledge_manifest.md` | Sección "Knowledge" en GPT Builder | Recuperación semántica complementaria (RAG) |
| **Google Gemini** | `integrations/gemini/system_instruction.md` | System Instructions en AI Studio / API | Host Degradado (Instrucciones inline P1–P4) |
