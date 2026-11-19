# Postura de Privacidad y Seguridad por Construcción — `arma3-sqf-skill`

Este documento establece los principios normativos de privacidad, confinamiento y seguridad de datos que rigen la arquitectura de `arma3-sqf-skill` y sus herramientas de integración.

---

## 1. Privacidad por Construcción (No por Política)

La privacidad en `arma3-sqf-skill` no depende de acuerdos de nivel de servicio ni de promesas contractuales: **está garantizada por el diseño de la arquitectura**.

### 1.1 Ejecución 100% Local
- Todos los scripts de análisis (`sqf_orchestrator.py`, `mcp_server.py`, `sqf_wiki_reader.py`) se ejecutan íntegramente en la máquina del usuario.
- **Sin sockets de red**: El código fuente de las herramientas no importa librerías de red (`socket`, `http.server`, `urllib.request`, `requests`, `aiohttp`, `fastapi`, `uvicorn`).
- **Sin llamadas salientes ni telemetría**: La skill no realiza ningún tipo de llamada a servidores externos, analítica de uso ni verificación de licencias.

### 1.2 Transporte stdio Confinado
El servidor Model Context Protocol (MCP) se comunica exclusivamente a través de los flujos estándar de entrada y salida (`stdin` / `stdout`) del proceso hijo invocado por el cliente host (ej. Claude Desktop).
- Los mensajes no abandonan la memoria del proceso local.
- No se expone ningún puerto TCP/IP ni interfaz de loopback que pueda ser sondeada por otros procesos o servicios en red.
- El transporte se fuerza a **UTF-8** al arrancar (`force_utf8_stdio()`), que es lo que exige la especificación MCP. Con ello, un cliente nunca recibe bytes ilegibles por una configuración regional del sistema (`cp1252` en una instalación estándar de Windows). Esta medida no afecta a la privacidad: sigue sin haber red.

### 1.3 Cero Persistencia de Código del Usuario
- Durante las llamadas a la herramienta `sqf_analyze`, el código SQF a auditar se procesa en memoria o en estructuras temporales del sistema (`tempfile.TemporaryDirectory`).
- Al completarse la petición, el directorio temporal y su contenido son eliminados de forma inmediata e incondicional por el recolector de contexto (`finally`).
- Ningún archivo con código SQF del usuario se almacena en el árbol del repositorio, cachés permanentes ni carpetas de registro.

### 1.4 Sin Credenciales ni Claves de API
- La skill y su servidor MCP no solicitan, almacenan ni transmiten claves de API (`API_KEY`), tokens de autenticación ni credenciales personales.

---

## 2. Variante HTTP (Track B HTTP — Extra Opt-in Futuro)

### Estado Actual: No Implementado
La variante HTTP/FastAPI no forma parte del núcleo distribuible ni de este hito de entrega.

### Criterios Obligatorios ante una Futura Implementación
Si en versiones posteriores se introduce soporte opt-in para transporte HTTP:
1. **Dependencia Opcional Estricta**: Debe empaquetarse exclusivamente como extra opcional (`[project.optional-dependencies] http = ["fastapi", "uvicorn"]`). El núcleo base debe seguir operando con `dependencies = []` sin requerir `pip install`.
2. **Aviso Explicito de Exposición**: Exponer un endpoint HTTP accesible en red implica un cambio fundamental de superficie de ataque (riesgo de fuga de código SQF de addons/misiones propietarias a través de la red local o reverse proxies). Requiere decisión explícita y consciente del usuario.
3. **Mecanismos de Protección Mandatorios**:
   - Autenticación por token bearer obligatorio.
   - Limitador de tasa (rate limiting).
   - Enlace restringido a `127.0.0.1` por defecto (prohibido `0.0.0.0` sin configuración explícita).
   - Política de no retención de payloads ni registros de código analizado en logs del servidor HTTP.
