# Definiciones de Subagentes para Google Antigravity

Este directorio (`agents/`) contiene las definiciones de subagentes heredadas del plugin original `arma3-sqf-review`, conservadas para usuarios que ejecuten la skill dentro del entorno Google Antigravity.

## 1. Alcance y No Portabilidad

> [!IMPORTANT]
> Los archivos `.md` de este directorio **NO son portables**.
> Su frontmatter YAML contiene campos específicos de la infraestructura de subagentes de Google Antigravity:
> `subagent: true`, `mainAgent: false`, `model: pro|flash`, `commandExecutionPolicy: sandbox` y directivas de herramientas (`tools: [...]`).

En otros hosts (como **Claude Code**, **Cursor**, **OpenAI Codex**, **ChatGPT Custom GPT** o **Google Gemini**):
- Estos archivos **no se cargan ni se interpretan**.
- Ninguna funcionalidad se pierde en hosts externos, ya que toda la inteligencia técnica, rúbricas de auditoría, invariantes y flujos de trabajo han sido portados a **artefactos universales portables** (lentes modulares bajo demanda en `references/lenses/`, flujos en `references/workflows/` y scripts deterministas en `scripts/`).

## 2. Tabla de Equivalencia: Agente Original vs Artefacto Portable

| # | Agente Original (Antigravity) | Artefacto Portable Equivalente | Tipo de Artefacto |
| :- | :--- | :--- | :--- |
| 1 | `sqf-locality-auditor.md` | `skills/arma3-sqf-skill/references/lenses/locality.md` | Lente modular |
| 2 | `sqf-performance-auditor.md` | `skills/arma3-sqf-skill/references/lenses/performance.md` | Lente modular |
| 3 | `sqf-architect.md` | `skills/arma3-sqf-skill/references/lenses/architect.md` | Lente modular |
| 4 | `sqf-mission-config-auditor.md` | `skills/arma3-sqf-skill/references/lenses/config.md` | Lente modular |
| 5 | `sqf-best-practices-reviewer.md` | `skills/arma3-sqf-skill/references/lenses/best_practices.md` | Lente modular |
| 6 | `sqf-claim-verifier.md` | `skills/arma3-sqf-skill/references/lenses/claims.md` + `scripts/sqf_wiki_reader.py` / DB FTS5 | Lente + herramienta |
| 7 | `sqf-static-analyzer.md` | `skills/arma3-sqf-skill/scripts/sqf_orchestrator.py --lint` | Herramienta determinista CLI / MCP |
| 8 | `sqf-test-plan-generator.md` | `skills/arma3-sqf-skill/references/workflows/test_plan.md` | Flujo de trabajo |
| 9 | `sqf-doc-writer.md` | `skills/arma3-sqf-skill/references/workflows/documentation.md` | Flujo de trabajo |
| 10 | `sqf-developer.md` | `skills/arma3-sqf-skill/references/workflows/implementation.md` | Flujo de trabajo |
| 11 | `sqf-innovator.md` | `skills/arma3-sqf-skill/references/workflows/innovation.md` | Flujo de trabajo |

## 3. Precedencia Normativa

Los artefactos portables y los documentos canónicos constituyen la **única fuente de verdad técnica y normativa**. Ante cualquier discrepancia entre un subagente de `agents/` y los documentos canónicos (`references/invariants.md`, `references/sqf-standards.md`, `references/rubrica.md`), **prevalece estrictamente el canónico**.

## 4. Histórico Congelado y Divergencias

- El directorio `legacy/agents/` representa el snapshot histórico congelado del plugin original. No se distribuye ni se empaqueta (excluido en `MANIFEST.in` y `.gitignore`).
- **Divergencia controlada**: `legacy/agents/sqf-claim-verifier.md` conserva intencionadamente la versión anterior a la corrección de rutas (pre-2026-11-19). La versión corregida y vigente para Antigravity reside en `agents/sqf-claim-verifier.md`.
