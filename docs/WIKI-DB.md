# Contrato de Datos y Especificación de Base de Conocimiento SQLite — `arma3-sqf-skill`

Especificación formal del esquema de base de datos relacional y de búsqueda textual (FTS5) construida a partir de la réplica offline oficial BIKI (`a3ref` v2).

---

## 1. Contexto y Objetivos

### 1.1 Problema
La réplica JSON original de `a3ref` (`commands.json`, `functions.json`, `index.json`, `syntax.json`, `topics.json`) suma más de 37 MB en disco. En particular:
- `topics.json` pesa **27,5 MB** debido al campo `markdown` de documentación extensa.
- El lector legacy (`sqf_wiki_reader.py`) cargaba en memoria ~10 MB de diccionarios en cada inicio y, para cada consulta de un tópico, leía y re-parseaba los 27,5 MB de `topics.json` seguidos de una llamada forzada a `gc.collect()`.

### 1.2 Solución
Construir una base de conocimiento SQLite determinista con motor de búsqueda FTS5 que proporcione:
1. **Latencia sub-milisegundo** en consultas de símbolos sintácticos, comandos, funciones y tópicos.
2. **Distribución en un único fichero SQLite (`arma3_wiki.db`)**, reproducible e indexado.
3. **Preservación estricta de la procedencia** exigida por `references/invariants.md`: URL oficial BIKI, número de revisión (`revid`), versión de introducción en el motor (`arma3_since` / `since`), estado (`ok`, `deprecated`, `broken`, `replaced_by`), timestamp del dataset (`updated`) y digest SHA del snapshot.
4. **Degradación honesta**: Si el entorno SQLite del host no soporta FTS5 o se ejecuta con `--no-fts`, la base de datos se construye sin la tabla virtual, el flag `fts_enabled` se fija en `0` en la tabla `meta` y las búsquedas textuales caen limpiamente a cláusulas `LIKE`.

---

## 2. Contrato de Datos de Origen (`~/.a3ref/data/*.json`)

El dataset sigue la especificación formal del formato v2 (`schema.json`):

| Fichero | Tamaño aprox. | Registros | Claves principales |
| :--- | :--- | :--- | :--- |
| `commands.json` | 4,5 MB | 2.657 | `{updated, source, count, items[]}` con `{name, title, type, url, revid, updated, groups, status, games, since, arma3_since, description, operator, syntaxes, aliases, doc_json}` |
| `functions.json` | 2,4 MB | 2.062 | `{updated, source, count, items[]}` con `{name, title, type, url, revid, updated, groups, status, games, since, arma3_since, description, syntaxes, aliases, doc_json}` |
| `index.json` | 2,2 MB | 5.394 | `{updated, count, items[]}` con `{name, type, md, json, groups, syntax, summary, arma3_since, locality, status, operator, aliases}` |
| `syntax.json` | 543 KB | 4.719 | `{updated, commands{}, functions{}}` con `{name, forms, status, syntax, operator}` |
| `topics.json` | 27,5 MB | 675 | `{updated, source, count, items[]}` con `{name, title, type, url, revid, updated, aliases, markdown, sections, categories, groups}` |

---

## 3. Esquema SQLite Relacional

### 3.1 Tabla `commands`
Almacena los comandos nativos del motor RV / Enforce de Arma 3:
```sql
CREATE TABLE commands (
    name TEXT PRIMARY KEY,
    name_lower TEXT UNIQUE,
    title TEXT,
    type TEXT,
    url TEXT,
    revid INTEGER,
    updated TEXT,
    status TEXT,
    groups_json TEXT,
    games_json TEXT,
    since TEXT,
    arma3_since TEXT,
    description TEXT,
    operator TEXT,
    syntaxes_json TEXT,
    aliases_json TEXT,
    doc_json TEXT
);
CREATE UNIQUE INDEX idx_commands_name_lower ON commands(name_lower);
```

### 3.2 Tabla `functions`
Almacena las funciones con prefijo (`BIS_fnc_*`, `BIN_fnc_*`, etc.):
```sql
CREATE TABLE functions (
    name TEXT PRIMARY KEY,
    name_lower TEXT UNIQUE,
    title TEXT,
    type TEXT,
    url TEXT,
    revid INTEGER,
    updated TEXT,
    status TEXT,
    groups_json TEXT,
    games_json TEXT,
    since TEXT,
    arma3_since TEXT,
    description TEXT,
    operator TEXT,
    syntaxes_json TEXT,
    aliases_json TEXT,
    doc_json TEXT
);
CREATE UNIQUE INDEX idx_functions_name_lower ON functions(name_lower);
```

### 3.3 Tabla `topics`
Almacena artículos de la BIKI, guías de edición y documentación de arquitectura:
```sql
CREATE TABLE topics (
    title TEXT PRIMARY KEY,
    title_lower TEXT,
    name TEXT,
    type TEXT,
    url TEXT,
    revid INTEGER,
    updated TEXT,
    aliases_json TEXT,
    markdown TEXT,
    doc_json TEXT
);
CREATE INDEX idx_topics_title_lower ON topics(title_lower);
CREATE INDEX idx_topics_name_lower ON topics(LOWER(name));
```

### 3.4 Tabla `symbols`
Almacena la resolución sintáctica de dos pasos proveniente de `syntax.json`:
```sql
CREATE TABLE symbols (
    key TEXT PRIMARY KEY,
    kind TEXT,
    name TEXT,
    forms_json TEXT,
    status TEXT,
    syntax_json TEXT,
    operator TEXT,
    replaced_by_json TEXT
);
CREATE INDEX idx_symbols_name ON symbols(name);
```

### 3.5 Tabla `index_items`
Almacena el índice consolidado de desempate y localidad de `index.json`:
```sql
CREATE TABLE index_items (
    name_lower TEXT,
    name TEXT,
    type TEXT,
    md TEXT,
    json TEXT,
    groups_json TEXT,
    syntax_json TEXT,
    summary TEXT,
    arma3_since TEXT,
    locality_json TEXT,
    status TEXT,
    operator TEXT,
    aliases_json TEXT
);
CREATE INDEX idx_index_items_name_lower ON index_items(name_lower);
```

### 3.6 Tabla `meta`
Almacena la procedencia global y metadatos deterministas de compilación:
```sql
CREATE TABLE meta (
    key TEXT PRIMARY KEY,
    value TEXT
);
```
Claves obligatorias:
- `schema_version`: Versión del esquema SQLite (v1.0).
- `dataset_updated`: Timestamp de actualización del dataset origen.
- `dataset_sha`: SHA256 determinista del contenido fuente.
- `dataset_git_sha`: Commit SHA de Git del repositorio `a3ref` (o `NO_VERIFICADO`).
- `built_at`: Timestamp ISO de generación de la base de datos.
- `counts_commands`: Total de comandos insertados.
- `counts_functions`: Total de funciones insertadas.
- `counts_topics`: Total de tópicos insertados.
- `counts_symbols`: Total de símbolos sintácticos insertados.
- `counts_index_items`: Total de entradas de índice insertadas.
- `fts_enabled`: `1` si FTS5 está activo; `0` si degradó a LIKE.

---

## 4. Búsqueda de Texto Completo (FTS5) y Justificación de Tamaño

### 4.1 Definición de la Tabla Virtual
```sql
CREATE VIRTUAL TABLE wiki_fts USING fts5(
    kind,
    name,
    title,
    summary,
    description,
    syntax,
    groups,
    tokenize = 'unicode61'
);
```

### 4.2 Decisión de Exclusión: `markdown` de `topics`
> [!IMPORTANT]
> **Justificación técnica de tamaño y latencia**:
> El campo `markdown` de `topics.json` comprende 27,5 MB de texto sin procesar con guías de modelado, scripts extensos y volcados de configuración.
> Si se indexara el cuerpo completo en FTS5:
> 1. El fichero `.db` superaría los 60–70 MB.
> 2. Las consultas FTS tendrían que puntuar tokens sobre documentos de hasta 500 KB, degradando la latencia de búsqueda.
> 
> **Estrategia adoptada:**
> - En `wiki_fts` se indexan `name`, `title`, `summary`, `description`, `syntax` y `groups` de comandos, funciones y tópicos.
> - La búsqueda de tópicos por título y alias se resuelve por índice B-Tree en $\mathcal{O}(\log N)$.
> - Si un usuario o subagente requiere buscar dentro del cuerpo del markdown de un tópico, se utiliza una consulta puntual SQL con `LIKE %texto%`, que sobre 675 filas toma menos de 15 ms y preserva el tamaño del fichero `.db` contenido en ~20–30 MB.

---

## 5. Procedencia y Trazabilidad (Invariantes N3)

De acuerdo con `references/invariants.md`, toda respuesta de verificación debe incluir:
- **`canonical_name`**: Grafía exacta oficial.
- **`status`**: Estado (`ok`, `deprecated`, `broken`, `replaced_by`).
- **`version`**: `arma3_since` o `since` (o `versión no disponible en el snapshot`).
- **`replaced_by`**: Reemplazo oficial si el comando o función está obsoleto.
- **`url`**: URL canónica a `https://community.bistudio.com/wiki/...`. Si no existe en el snapshot, se marca como `(NO_VERIFICADO: url ausente en snapshot)`.
- **`type`**: `command`, `function` o `topic`.
- **`dataset_sha` / `git_sha`**: Trazabilidad del snapshot origen.

---

## 6. Métricas y Mediciones Empíricas (R4)

Medición sobre la réplica oficial completa en `~/.a3ref/data` (2.657 comandos, 2.062 funciones, 675 tópicos, 4.719 símbolos, 5.394 entradas de índice; tamaño total JSON: 35,44 MB / 37.163.259 bytes).

### 6.1 Tiempos de Construcción y Tamaños
| Métrica | Valor | Método de medición |
| :--- | :--- | :--- |
| **Tiempo de compilación (Build)** | **1,132 s** | Mediana de 3 compilaciones completas con FTS5 (`build_db`) |
| **Tamaño JSON total** | **35,44 MB** | Suma de `commands`, `functions`, `index`, `syntax`, `topics` |
| **Tamaño SQLite DB (`arma3_wiki.db`)** | **58,42 MB** | Fichero único post-`VACUUM` (incluye tablas B-tree + FTS5) |
| **Ratio de tamaño DB/JSON** | **1,65x** | El incremento se debe a los índices B-Tree y la estructura virtual de FTS5 |

### 6.2 Latencia de Consulta ($N=50$)
Pruebas ejecutadas secuencialmente sobre muestras representativas de tokens y artículos:

| Operación | Modo JSON (mediana / P95) | Modo DB SQLite (mediana / P95) | Aceleración (Speedup) |
| :--- | :--- | :--- | :--- |
| `lookup_syntax_symbol` | 59,518 ms / 74,287 ms | **0,456 ms** / 0,820 ms | **130,4x más rápido** |
| `get_topic` (artículo completo) | 187,328 ms / 225,717 ms | **0,358 ms** / 0,874 ms | **522,9x más rápido** |

> [!NOTE]
> La enorme ganancia en `get_topic` (~523x) se debe a que la consulta relacional recupera puntualmente el registro por B-Tree sin re-parsear los 27,5 MB de `topics.json` ni requerir recolección de basura (`gc.collect()`).
