# Postura de Privacidad y Seguridad por Construcción — `arma3-sqf-skill`

Este documento establece los principios normativos de privacidad, confinamiento y seguridad de datos que rigen la arquitectura de `arma3-sqf-skill` y sus herramientas de integración.

---

## 1. Privacidad por Construcción (No por Política)

La privacidad en `arma3-sqf-skill` no depende de acuerdos de nivel de servicio ni de promesas contractuales: **está garantizada por el diseño de la arquitectura**.

### 1.1 Ejecución 100% Local
- Todos los scripts de análisis (`sqf_orchestrator.py`, `sqf_wiki_reader.py`, `wiki_db_builder.py`, `run_sqflint.py`) se ejecutan íntegramente en la máquina del usuario o en el sandbox efímero del host de IA.
- **Sin sockets de red**: El código fuente de las herramientas no importa librerías de red (`socket`, `http.server`, `urllib.request`, `requests`, `aiohttp`, `fastapi`, `uvicorn`).
- **Sin llamadas salientes ni telemetría**: La skill no realiza ningún tipo de llamada a servidores externos, analítica de uso ni verificación de licencias.

### 1.2 Arquitectura Confinada y Sin Daemons (Cero MCP)
La skill opera bajo el principio de Skill Pura Universal:
- No mantiene daemons residentes en segundo plano ni procesos servidor en ejecución.
- La ejecución se realiza exclusivamente bajo demanda mediante invocaciones directas CLI o análisis determinista en proceso (`python scripts/sqf_orchestrator.py`).
- No se expone ningún puerto TCP/IP ni interfaz de loopback que pueda ser sondeada por otros procesos o servicios en red.
- Todas las salidas y diagnósticos respetan estrictamente la codificación UTF-8 sin BOM.

### 1.3 Cero Persistencia de Código del Usuario
- Durante las ejecuciones de auditoría o análisis estático, el código SQF a auditar se procesa en memoria o en estructuras temporales efímeras del sistema (`tempfile.TemporaryDirectory`).
- Al completarse la petición, el directorio temporal y su contenido son eliminados de forma inmediata e incondicional por el recolector de contexto (`finally`).
- Ningún archivo con código SQF del usuario se almacena en el árbol del repositorio, cachés permanentes ni carpetas de registro.

### 1.4 Sin Credenciales ni Claves de API
- La skill no solicita, almacena ni transmite claves de API (`API_KEY`), tokens de autenticación ni credenciales personales.
