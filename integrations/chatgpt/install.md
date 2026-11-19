# Instalación y Configuración para ChatGPT Custom GPT

Esta guía describe cómo crear y configurar el Custom GPT para `arma3-sqf-skill` en ChatGPT (OpenAI).

---

## 1. Crear el Custom GPT

1. Inicia sesión en ChatGPT (cuenta Plus o Enterprise con acceso a GPT Builder).
2. Dirígete a **Explore GPTs** -> **Create**.
3. Selecciona la pestaña **Configure**.
4. Completa la ficha de identidad:
   - **Name**: `Arma 3 SQF Code Reviewer & Auditor`
   - **Description**: `Revisor experto de código SQF para Arma 3 en servidor dedicado (headless) y multijugador.`

---

## 2. Inyectar las Instrucciones del Sistema

1. Abre el archivo generado `integrations/chatgpt/custom_gpt_instructions.md`.
2. Copia todo su contenido.
3. Pégalo directamente en el campo **Instructions** de la configuración del GPT.
   *(El contenido está estrictamente optimizado para medir menos de 8.000 caracteres, respetando el límite de ChatGPT).*

---

## 3. Subir Archivos a Knowledge

1. En la sección **Knowledge**, pulsa **Upload files**.
2. Sube únicamente los **18 archivos** especificados en `integrations/chatgpt/knowledge_manifest.md`:
   - `SKILL.md`
   - Los 6 archivos base de `references/` (invariants, sqf-standards, rubrica, report_format, checklist-entrega, diferencial-misiones-addons).
   - Los 6 archivos de `references/lenses/` (architect, best_practices, claims, config, locality, performance).
   - Los 5 archivos de `references/workflows/` (audit, doc, fix_loop, new_feature, test_plan).
3. **No subas** `references/wiki-cache.md` ni archivos de código `.py`.

---

## 4. Desactivar Capacidades Innecesarias

- En la sección **Capabilities**, se recomienda:
  - **Code Interpreter**: Activo (si se desea análisis de archivos de texto subidos por el usuario en el chat).
  - **Web Browsing**: Activo (fallback secundario para consultar la BIKI de Bohemia Interactive si un comando no está en las referencias).
  - **DALL·E Image Generation**: Inactivo (no aplica).

---

## 5. Verificación de Funcionamiento

Prueba el GPT con un prompt de prueba en el panel de vista previa:
```
Revisa este bloque SQF:
hint "Hola jugador";
waitUntil {alive player};
```
Respuesta esperada:
- Detección inmediata de `hint` en ruta no filtrada (Cat. 3) y `player` / `waitUntil` sin timeout (Cat. 2 y Cat. 3) como **BLOQUEANTE**.
- Emisión del informe bajo el esquema `REPORT_SCHEMA_VERSION = 1`.
