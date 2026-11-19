# Guía de Contribución a Arma 3 SQF Review

¡Gracias por tu interés en contribuir a `arma3-sqf-skill`! Este proyecto busca elevar la calidad, robustez y compatibilidad de scripts SQF para la comunidad de Arma 3 en servidores dedicados.

---

## 🛠️ Configuración del Entorno de Desarrollo

1. **Clonar el repositorio**:
   ```bash
   git clone https://github.com/TouristicAsp44/Arma3-SQF-skill.git
   cd arma3-sqf-skill
   ```

2. **Crear y activar un entorno virtual (Python 3.11+)**:
   ```bash
   python -m venv .venv
   # En Windows:
   .venv\Scripts\activate
   # En Linux / macOS:
   source .venv/bin/activate
   ```

3. **Instalar dependencias de desarrollo**:
   ```bash
   pip install -r requirements-dev.txt
   ```

4. **Ejecutar la suite de pruebas**:
   ```bash
   pytest tests/ -v
   ```

---

## 📐 Estándares de Código

### Python
- El código en Python debe mantener compatibilidad con Python 3.11+.
- Usar tipado estático (`typing` / `annotations`) en funciones y clases públicas.
- Pasar el linter y formateador `ruff check .` antes de enviar cambios.

### SQF y Reglas del Plugin
- Toda regla nueva o modificación de invariantes debe quedar reflejada en:
  - `skills/arma3-sqf-skill/references/sqf-standards.md`
  - `rules/AGENTS.md`
- Respetar los principios de servidor dedicado:
  - Prohibido el uso de comandos visuales UI (`hint`, `cutText`) en rutas de servidor.
  - No asumir que `player` existe en servidores dedicados (`player == objNull`).
  - No introducir dependencias silenciosas de CBA o ACE3 si el proyecto declara Vanilla.

---

## 🧪 Pruebas Unitarias

Toda corrección o nueva funcionalidad debe incluir su correspondiente test en la carpeta `tests/`.
- Usar fixtures deterministas.
- Los tests no deben requerir conexiones de red activas (usar mocks o la réplica local `a3ref`).
- Las 48 pruebas existentes deben continuar pasando al 100%.

---

## 🚀 Proceso de Pull Request (PR)

1. Crea una rama descriptiva para tu cambio: `git checkout -b feature/nombre-mejora` o `git checkout -b fix/nombre-bug`.
2. Realiza tus cambios asegurando que `pytest tests/` pase en verde.
3. Escribe mensajes de commit claros siguiendo el estándar convencional (`feat:`, `fix:`, `docs:`, `test:`, `chore:`).
4. Abre un Pull Request describiendo el problema resuelto y la evidencia de pruebas.
