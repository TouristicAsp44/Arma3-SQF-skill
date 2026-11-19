# Especificación del Esquema de Informe v1

Este documento especifica el contrato del formato de salida estructurado generado por el motor de análisis y esperado por todos los consumidores (skill prompts, evals, MCP servers).

## 1. Contrato General

- **Versión de esquema**: `REPORT_SCHEMA_VERSION = 1`
- Toda salida estructurada comienza con la cabecera `REPORT_SCHEMA_VERSION: 1` en la primera línea.
- Existen **dos tipos de informes disjuntos**:
  1. **Informe de Hallazgos** (análisis estático y semántico).
  2. **Informe de Modo** (triage de complejidad del proyecto).
- **Regla del matcher**: El informe de hallazgos se distingue inequívocamente porque su línea `RESUMEN:` contiene `bloqueantes=`. El informe de modo contiene `modo=`.

---

## 2. Informe de Hallazgos (Salida de `--lint`)

### Formato Literal

```
REPORT_SCHEMA_VERSION: 1
[SEVERIDAD] archivo:linea (disciplina): descripcion
RESUMEN: bloqueantes=N; sugerencias=N; no_verificado=N
```

### Campos
- `SEVERIDAD`: `BLOQUEANTE`, `SUGERENCIA` o `NO_VERIFICADO`.
- `archivo:linea`: Ruta al archivo SQF y número de línea base 1.
- `(disciplina)`: Disciplina detectora (p. ej. `Scope`, `Sintaxis`, `Locality`, `Performance`).
- `descripcion`: Explicación concisa y accionable del hallazgo.
- `RESUMEN:`: Totales exactos de bloqueantes, sugerencias y estados no verificados.

### Ejemplo Real

```
REPORT_SCHEMA_VERSION: 1
[BLOQUEANTE] fn_init.sqf:1 (Scope): Local variable "_z" is not from this scope (not private)
[SUGERENCIA] fn_init.sqf:1 (Sintaxis): Variable "_y" not used
RESUMEN: bloqueantes=1; sugerencias=1; no_verificado=0
```

---

## 3. Informe de Modo (Salida de `--mode-query`)

### Formato Literal

```
REPORT_SCHEMA_VERSION: 1
MODO: <Micro|Estándar|Completo>
MOTIVO: <descripcion concisa del criterio cumplido>
RESUMEN: modo=<modo>; escalado=<si|no>
```

### Ejemplo Real

```
REPORT_SCHEMA_VERSION: 1
MODO: Micro
MOTIVO: Archivo único autocontenido sin señales de red ni scheduler
RESUMEN: modo=Micro; escalado=no
```
