params ["_unit"];

_pos = getPosATL _unit;

_unit setPosATL [_pos select 0, _pos select 1, (_pos select 2) + 1];
