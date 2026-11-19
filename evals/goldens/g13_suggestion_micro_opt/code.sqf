params ["_targets"];

// Sugerencia: `count _targets > 0` es más lento que `!(_targets isEqualTo [])` para chequear array no vacío
if (count _targets > 0) then {
    private _first = _targets select 0;
    _first setDamage 0.5;
};
