params ["_vehicle"];

// waitUntil sin timeout ni garantía de salida
waitUntil {
    _vehicle getVariable ["engine_repaired", false]
};

_vehicle setFuel 1;
