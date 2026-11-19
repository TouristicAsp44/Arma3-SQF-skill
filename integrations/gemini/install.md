# Instalación y Configuración para Google Gemini / Google AI Studio

Esta guía describe cómo utilizar `arma3-sqf-skill` con Google Gemini, ya sea en la interfaz web de Google AI Studio o vía Gemini API.

---

## 1. Google AI Studio (Web UI)

1. Ingresa a [Google AI Studio](https://aistudio.google.com/).
2. Crea un nuevo Chat Prompt (**Create New Prompt** -> **Chat Prompt**).
3. Selecciona un modelo reciente recomendado (ej. Gemini 1.5 Pro o Gemini 2.0 Flash).
4. En el panel lateral, localiza el campo **System Instructions** (Instrucciones del Sistema).
5. Abre el archivo generado `integrations/gemini/system_instruction.md`, copia su contenido íntegro y pégalo en el campo **System Instructions**.
6. Ajusta la temperatura a un valor bajo (ej. `0.2` a `0.3`) para maximizar el determinismo en la aplicación de las reglas normativas.

---

## 2. Gemini API (Python SDK / REST)

Al invocar la API de Gemini mediante el SDK oficial (`google-genai`), configura el contenido de `system_instruction.md` en el objeto de configuración:

```python
from google import genai
from google.genai import types
from pathlib import Path

system_text = Path("integrations/gemini/system_instruction.md").read_text(encoding="utf-8")

client = genai.Client()
response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents="Revisa el siguiente código SQF: [...]",
    config=types.GenerateContentConfig(
        system_instruction=system_text,
        temperature=0.2,
    ),
)
print(response.text)
```

---

## 3. Verificación de Funcionamiento

Envía el siguiente snippet en el chat:
```sqf
_contador = 0;
while {true} do {
    _contador = _contador + 1;
};
```
Respuesta esperada:
- Detección de bucle infinito sin cadencia ni suspensión (`while {true}` sin `sleep`/PFH) como **BLOQUEANTE** (Cat. 2).
- Emisión del informe bajo el esquema formal:
  `[BLOQUEANTE] ... (performance/locality): bucle while {true} sin cadencia...`
  `RESUMEN: bloqueantes=1; sugerencias=0; no_verificado=...`
