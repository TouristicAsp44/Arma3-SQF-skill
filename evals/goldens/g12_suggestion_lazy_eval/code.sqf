params ["_unit", "_zone"];

private _isAlive = alive _unit;

// Sugerencia: evaluación normal con condición costosa (inArea _zone); mejor evaluación perezosa && { ... }
if (_isAlive and (_unit inArea _zone)) then {
    _unit setVariable ["zone_active", true];
};
