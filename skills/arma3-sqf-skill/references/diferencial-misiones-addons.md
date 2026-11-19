---
description: Sección diferencial de criterios específicos para misiones de Eden Editor vs addons empaquetados (mods).
---

# Sección Diferencial: Misiones (Eden) vs Addons (Mods)

Los requisitos estructurales y de configuración varían radicalmente según el tipo de proyecto declarado en el perfil (`DESTINO: mision` vs `DESTINO: addon`):

| Característica / Criterio | Variante Misión (Eden / Campaña MP) | Variante Addon (Mod empaquetado PBO) |
|---|---|---|
| **Archivo principal de configuración** | `description.ext` en la raíz de la carpeta de la misión. | `config.cpp` (compilado a `config.bin`) en la raíz del addon. |
| **Declaración `CfgPatches`** | **NO APLICA / PROHIBIDO EXIGIR**. Las misiones no definen `CfgPatches`. | **OBLIGATORIO**. Define la clase del addon, `name`, `author`, `requiredVersion` y `requiredAddons[]`. |
| **Lista blanca de `CfgRemoteExec`** | Declarada dentro de `description.ext >> CfgRemoteExec >> Functions`. | Declarada dentro de `config.cpp >> CfgRemoteExec >> Functions`. |
| **Declaración `CfgFunctions`** | En `description.ext >> CfgFunctions`. Rutas relativas a la carpeta de la misión (ej. `file = "scripts\miFuncion.sqf";`). | En `config.cpp >> CfgFunctions`. Rutas absolutas con prefijo PBO (ej. `file = "\tag_addon\functions\fn_miFuncion.sqf";`). |
| **Scripts de ciclo de vida del motor** | `init.sqf`, `initServer.sqf`, `initPlayerLocal.sqf`, `initPlayerServer.sqf`. | No utiliza scripts de ciclo de vida de misión. Utiliza funciones con `preInit = 1` o `postInit = 1` en `CfgFunctions`. |
| **Prefijo de empaquetado ($PBOPREFIX$)** | No aplica durante la edición en Eden ni en carpetas descomprimidas de misión. | Obligatorio en el proyecto fuente para definir la ruta virtual del PBO (ej. `tag_addon`). |
| **Distribución y Empaquetado** | Carpeta de misión de Eden o archivo `.pbo` en directorio `MPMissions/`. | Compilado a archivo `.pbo` mediante herramientas como MakePBO / HEMTT, ubicado en `@tu_mod/addons/`. |
| **Parámetros de lanzamiento del servidor** | Parámetros estándar de misión en `server.cfg` (`template = "mision.mapa";`). | Lanzado mediante `-mod=@tu_mod` (clientes y servidor) o `-serverMod=@tu_mod` (exclusivo servidor). |
| **Firmas digitales y claves** | No requiere firmas `.bikey` a nivel de misión. | Requiere firmado con clave privada (`.biprivatekey`) y distribución de clave pública `.bikey` en carpeta `keys/`. |
