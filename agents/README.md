# Definiciones de Subagentes para Google Antigravity

Este directorio (`agents/`) contiene las definiciones de subagentes heredadas del plugin original `arma3-sqf-review`, conservadas para usuarios que ejecuten la skill dentro del entorno Google Antigravity.

## 1. Alcance y No Portabilidad

> [!IMPORTANT]
> Los archivos `.md` de este directorio **NO son portables**.
> Su frontmatter YAML contiene campos específicos de la infraestructura de subagentes de Google Antigravity:
> `subagent: true`, `mainAgent: false`, `model: pro|flash`, `commandExecutionPolicy: sandbox` y directivas de herramientas (`tools: [...]`).

En otros hosts (como **Claude Code**, **Cursor**, **OpenAI Codex**, **ChatGPT Custom GPT** o **Google Gemini**):
- Estos archivos **no se cargan ni se interpretan**.
- Ninguna funcionalidad se pierde en hosts externos, ya que toda la inteligencia técnica, rúbricas de auditoría, invariantes y flujos de trabajo han sido portados a **artefactos universales portables** (lentes planas bajo demanda en `references/lens-*.md`, flujos en `references/workflows/` y scripts deterministas en `scripts/`).

## 2. Tabla de Equivalencia: Agente Original vs Artefacto Portable

| # | Agente Original (Antigravity) | Artefacto Portable Equivalente | Tipo de Artefacto |
| :- | :--- | :--- | :--- |
| 1 | `sqf-locality-auditor.md` | `skills/arma3-sqf-skill/references/lens-locality.md` | Lente modular |
| 2 | `sqf-performance-auditor.md` | `skills/arma3-sqf-skill/references/lens-performance.md` | Lente modular |
| 3 | `sqf-architect.md` | `skills/arma3-sqf-skill/references/lens-architect.md` | Lente modular |
| 4 | `sqf-mission-config-auditor.md` | `skills/arma3-sqf-skill/references/lens-config.md` | Lente modular |
| 5 | `sqf-best-practices-reviewer.md` | `skills/arma3-sqf-skill/references/lens-best-practices.md` | Lente modular |
| 6 | `sqf-claim-verifier.md` | `skills/arma3-sqf-skill/references/lens-claims.md` + `scripts/sqf_wiki_reader.py` / DB FTS5 | Lente + herramienta |
| 7 | `sqf-static-analyzer.md` | `skills/arma3-sqf-skill/scripts/sqf_orchestrator.py --lint` | Herramienta determinista CLI pura |
| 8 | `sqf-test-plan-generator.md` | `skills/arma3-sqf-skill/references/workflows/test_plan.md` | Flujo de trabajo |
| 9 | `sqf-doc-writer.md` | `skills/arma3-sqf-skill/references/workflows/documentation.md` | Flujo de trabajo |
| 10 | `sqf-developer.md` | `skills/arma3-sqf-skill/references/workflows/implementation.md` | Flujo de trabajo |
| 11 | `sqf-innovator.md` | `skills/arma3-sqf-skill/references/workflows/innovation.md` | Flujo de trabajo |

## 3. Precedencia Normativa

Los artefactos portables y los documentos canónicos constituyen la **única fuente de verdad técnica y normativa**. Ante cualquier discrepancia entre un subagente de `agents/` y los documentos canónicos (`references/invariants.md`, `references/sqf-standards.md`, `references/rubrica.md`), **prevalece estrictamente el canónico**.

## 4. Histórico y Depuración

- Los snapshots históricos obsoletos de agentes heredados del plugin original (`legacy/`) fueron purgados en la versión 2.0.0 para garantizar limpieza del árbol y máxima ligereza.
- La versión vigente para Antigravity reside en `agents/` (`sqf-claim-verifier.md` con rutas agnósticas de procedencia y resolución multiplataforma).
