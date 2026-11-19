---
description: Puntero a la fuente canónica. Sustituye al antiguo rules/AGENTS.md de Antigravity (frontmatter trigger: always_on).
---

# Invariantes SQF/HPP — Arma 3

> [!IMPORTANT]
> Este archivo es un **puntero**. La fuente canónica única de las reglas
> normativas vive en:
>
> - `skills/arma3-sqf-skill/references/invariants.md` — criterios de revisión
>   (7 categorías de BLOQUEANTE, Puerta de Calidad, honestidad técnica,
>   criterios de modo, precedencia, propiedad de reglas).
> - `skills/arma3-sqf-skill/references/sqf-standards.md` — reglas de escritura.
> - `skills/arma3-sqf-skill/references/rubrica.md` — rúbrica y participación por modo.
>
> El antiguo `trigger: always_on` es un mecanismo exclusivo de Antigravity y no
> es portable. En su lugar, los hosts que lo soporten deben injectar el canónico
> como invariante del proyecto (ver `integrations/`).

## Resumen operativo (índice N1)

- Toda variable local con `private` o `params`; sin fugas al scope global.
- Evaluación perezosa (`a && {b}`) solo cuando `b` es costosa.
- `sleep` y `waitUntil` solo en entorno scheduled.
- Lo no ejecutado en servidor dedicado se reporta `NO VERIFICADO`; nunca completo.
- Interfaz prohibida en rutas de servidor (una guarda `hasInterface` no la legitima).
- `player` no existe en servidor dedicado.
- `isServer`, `isDedicated` y `hasInterface` no son intercambiables.
- Sin esperas bloqueantes en `init.sqf`, `initServer.sqf` o `postInit`.

Para el detalle normativo, ver `references/invariants.md`.
