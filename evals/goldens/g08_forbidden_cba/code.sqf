/* Perfil del Proyecto:
   CBA: no
   ACE3: no
   DESTINO: mision
*/

params ["_key", "_val"];

// Inyección de función CBA_fnc_* en proyecto configurado como CBA: no
private _hash = [] call CBA_fnc_hashCreate;
[_hash, _key, _val] call CBA_fnc_hashSet;

_hash
