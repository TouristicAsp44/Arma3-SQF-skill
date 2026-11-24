#!/usr/bin/env bash
# ==============================================================================
# bootstrap.sh - Inicialización determinista del entorno y caché BIKI offline
#
# Clona superficialmente el repositorio a3ref y compila la base de datos SQLite
# optimizada (arma3_wiki.db) en $HOME/a3ref_cache para entornos con
# filesystem de solo lectura en la raíz o entornos efímeros (Claude AI / CI).
# ==============================================================================

set -euo pipefail

# 1. Exportar variables de entorno requeridas
DEFAULT_CACHE_DIR="${HOME}/a3ref_cache"
CACHE_DIR="${A3REF_CACHE_DIR:-${DEFAULT_CACHE_DIR}}"
REPO_DIR="${CACHE_DIR}/a3ref"
DATA_DIR="${REPO_DIR}/data"
DB_PATH="${CACHE_DIR}/arma3_wiki.db"

export SQF_WIKI_DB_PATH="${DB_PATH}"
export PYTHONDONTWRITEBYTECODE=1

# Resolver directorio de este script para resolución CWD-independiente
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== [SQF Skill Bootstrap] Inicializando entorno y caché offline ==="
echo "Directorio de caché: ${CACHE_DIR}"
echo "Base de datos destino: ${DB_PATH}"

# 2. Asegurar que existe el directorio de caché
mkdir -p "${CACHE_DIR}"

# 3. Clonado superficial (shallow clone) de a3ref
if [ ! -d "${REPO_DIR}" ]; then
    echo "Clonando repositorio a3ref (shallow clone)..."
    git clone --depth 1 https://github.com/a3ref/a3ref.git "${REPO_DIR}"
else
    echo "Repositorio a3ref ya presente en ${REPO_DIR}."
fi

# 4. Construcción determinista de la base de datos SQLite
if [ ! -d "${DATA_DIR}" ]; then
    echo "ERROR: No se encontró el directorio de datos en ${DATA_DIR}" >&2
    exit 1
fi

echo "Compilando base de datos SQLite arma3_wiki.db..."
cd "${SCRIPT_DIR}"

if command -v python3 >/dev/null 2>&1; then
    python3 wiki_db_builder.py build --data "${DATA_DIR}" --out "${DB_PATH}"
else
    python wiki_db_builder.py build --data "${DATA_DIR}" --out "${DB_PATH}"
fi

# 5. Verificación de éxito
if [ -f "${DB_PATH}" ]; then
    echo "=== [SQF Skill Bootstrap] Base de datos construida exitosamente en ${DB_PATH} ==="
    echo "SQF_WIKI_DB_PATH=${SQF_WIKI_DB_PATH}"
    echo "PYTHONDONTWRITEBYTECODE=${PYTHONDONTWRITEBYTECODE}"
else
    echo "ERROR: Falló la generación de ${DB_PATH}" >&2
    exit 1
fi
