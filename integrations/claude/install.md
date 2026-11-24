# Instalación y Configuración para Claude (Claude Code y Claude Desktop)

Esta guía detalla el procedimiento de instalación, configuración y verificación de `arma3-sqf-skill` para el ecosistema Anthropic Claude.

---

## 1. Claude Code (CLI / Terminal)

Claude Code es el host recomendado principal: cuenta con acceso nativo al sistema de archivos del repositorio y ejecución de herramientas de terminal.

### Procedimiento
1. Abre tu terminal en la raíz del repositorio clonado:
   ```bash
   cd RUTA_A_TU_PROYECTO
   ```
2. Asegúrate de contar con Python 3.11 o superior instalado (el núcleo utiliza exclusivamente la biblioteca estándar, sin paquetes externos requeridos).
3. Inicia Claude Code en el repositorio:
   ```bash
   claude
   ```
4. El archivo `integrations/claude/CLAUDE.md` es detectado e indexado automáticamente por Claude Code al iniciar.

### Verificación
Para validar que el entorno y las reglas de Claude Code están operativos:
```bash
python scripts/check.py --fase PR-5
```
Salida esperada: `TODO EN VERDE para la fase solicitada.`

---

## 2. Claude Desktop

Claude Desktop soporta dos modalidades de integración:

### Opción A: Modo Pegado (Host Degradado, sin servidor MCP)
Ideal para consultas rápidas sin configuración de procesos locales.
1. Abre el archivo generado `integrations/claude/claude_desktop_paste.md`.
2. Copia todo su contenido y pégalo como mensaje inicial en tu chat de Claude Desktop.
3. El modelo adoptará el protocolo de revisión estandarizado P1–P4.
4. Si el servidor MCP presenta incidencias o no está disponible en tu entorno, esta modalidad actúa como fallback inmediato y seguro.

### Opción B: Claude AI Skills (Subida directa de ZIP)
Ideal para usuarios de Claude AI en la web o aplicación:
1. Descarga el paquete distribuible [arma3-sqf-skill.zip](https://github.com/TouristicAsp44/Arma3-SQF-skill/releases/download/v2.0.0/arma3-sqf-skill.zip) o constrúyelo localmente con `python scripts/package_skill.py`.
2. En Claude AI, accede a **Settings > Skills** y selecciona **Upload Skill**.
3. Selecciona `arma3-sqf-skill.zip`.
4. El contenedor Linux de Claude AI desempaquetará el skill y ejecutará automáticamente `scripts/bootstrap.sh`, clonando superficialmente la réplica `a3ref` en `~/.a3ref_cache/` y habilitando el motor SQLite FTS5.
5. El skill queda inmediatamente disponible para auditorías SQF con capacidades offline completas.
