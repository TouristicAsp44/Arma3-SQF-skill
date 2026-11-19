# Instalación y Configuración para Cursor

Esta guía explica cómo configurar `arma3-sqf-skill` en el editor Cursor.

---

## Procedimiento de Instalación

1. Copia el archivo de reglas `.cursorrules` a la raíz de tu proyecto o espacio de trabajo de Cursor:
   ```bash
   cp integrations/cursor/.cursorrules .cursorrules
   ```
2. Si utilizas la estructura de reglas moderna de Cursor (`.cursor/rules/`), puedes moverlo o enlazarlo como:
   ```bash
   mkdir -p .cursor/rules
   cp integrations/cursor/.cursorrules .cursor/rules/arma3-sqf.mdc
   ```
3. Verifica que la carpeta `skills/arma3-sqf-skill/` esté disponible en el espacio de trabajo para que Cursor pueda leer las referencias y lentes bajo demanda.

---

## Verificación

Para confirmar que las reglas están bien estructuradas y que la suite de tests valida los adaptadores:
```bash
python scripts/check.py --fase PR-4
```
Salida esperada: `[ OK  ] adaptadores host — X test(s) en verde`.
