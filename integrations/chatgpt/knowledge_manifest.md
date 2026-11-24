# Manifiesto de Archivos para Knowledge — ChatGPT Custom GPT

Este documento establece la lista exacta y justificada de archivos que deben subirse a la sección **Knowledge** del Custom GPT de ChatGPT para `arma3-sqf-skill`.

---

## 1. Límite de la Plataforma y Criterio de Selección

- **Límite técnico de ChatGPT**: Máximo estricto de **20 archivos** en el panel de Knowledge por Custom GPT.
- **Total de archivos seleccionados**: **18 archivos** (cumple estrictamente el límite `<= 20`).
- **Criterio de selección**:
  1. Se priorizan documentos normativos canónicos y contratos estructurados.
  2. Se incluyen las 6 lentes especializadas para cubrir la totalidad de disciplinas de auditoría SQF.
  3. Se incluyen los 5 flujos de trabajo normativos para guiar el orden de ejecución.
  4. Solo se seleccionan archivos de texto plano / Markdown limpios sin dependencias de ejecución.

---

## 2. Inventario de Archivos a Subir (18 archivos)

| N.º | Archivo | Disciplina / Propósito | Justificación de Inclusión |
| :---: | :--- | :--- | :--- |
| 1 | `SKILL.md` | Capa 0 / Entrada | Visión general del sistema, perfiles de proyecto y modos de operación. |
| 2 | `references/invariants.md` | Canónico de Reglas | Definición de las 7 categorías de bloqueante, puerta de calidad y honestidad. |
| 3 | `references/sqf-standards.md` | Canónico de Estilo | Estándares de codificación: scope, private, params y nomenclatura. |
| 4 | `references/rubrica.md` | Canónico de Rúbrica | Criterios de severidad (Bloqueante vs. Sugerencia) y matriz de participación. |
| 5 | `references/report_format.md` | Contrato de Salida | Esquema formal del informe v1 emitido. |
| 6 | `references/checklist-entrega.md` | Verificación Final | Criterios de cierre y entrega sin bloqueantes abiertos. |
| 7 | `references/diferencial-misiones-addons.md` | Configuración | Diferencias de contexto de ejecución entre misiones (`description.ext`) y addons (`config.cpp`). |
| 8 | `references/lens-architect.md` | Lente Arquitectura | Diseño modular, contratos de interfaces y desacoplamiento. |
| 9 | `references/lens-best-practices.md` | Lente Buenas Prácticas | Evaluación perezosa, micro-optimizaciones y buenas prácticas SQF. |
| 10 | `references/lens-claims.md` | Lente Verificación | Protocolo de verificación de afirmaciones técnicas contra BIKI. |
| 11 | `references/lens-config.md` | Lente Configuración | Reglas de `CfgRemoteExec`, whitelist de funciones y orden de init. |
| 12 | `references/lens-locality.md` | Lente Locality | Reglas de multijugador, remoteExec, JIP y servidor dedicado. |
| 13 | `references/lens-performance.md` | Lente Rendimiento | Scheduler, bucles, PFH y prevención de saturación de frames. |
| 14 | `references/workflows/audit.md` | Flujo de Auditoría | Paso a paso para auditar scripts o sistemas existentes. |
| 15 | `references/workflows/doc.md` | Flujo de Documentación | Redacción de guías técnicas y documentación de API SQF. |
| 16 | `references/workflows/fix_loop.md` | Flujo de Corrección | Ciclo de corrección de bloqueantes (máximo 3 iteraciones). |
| 17 | `references/workflows/new_feature.md` | Flujo Nueva Mecánica | Proceso de diseño e implementación de nuevas mecánicas. |
| 18 | `references/workflows/test_plan.md` | Flujo Plan de Pruebas | Generación de planes de prueba para servidor dedicado y multijugador. |

---

## 3. Exclusiones Explícitas y Justificación

| Archivo o Directorio | Motivo de Exclusión |
| :--- | :--- |
| `references/wiki-cache.md` | **Excluido por tamaño y ruido en RAG**. Pesa ~35,4 MB en texto plano. Subirlo completo satura la cuota de almacenamiento, fragmenta las respuestas del modelo y diluye la relevancia de los documentos normativos críticos. La información esencial de sintaxis se cubre en las instrucciones inline y las lentes. |
| Scripts Python (`scripts/*.py`) | **Excluidos por incompatibilidad**. ChatGPT Knowledge realiza recuperación semántica de texto (RAG); no ejecuta intérprete de Python local para scripts de linteo o consultas de SQLite. |
| Base de datos SQLite (`*.db`) | **Excluida por formato binario**. La base FTS5 es un archivo binario optimizado para SQLite local, no apto para indexación de texto plano en Knowledge. |
| Archivos de test (`tests/*`) | **Excluidos por irrelevancia operativa**. Los tests verifican el desarrollo del repositorio localmente y no aportan conocimiento de dominio SQF a las respuestas del GPT. |
