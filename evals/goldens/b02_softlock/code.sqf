params ["_vehicle"];

waitUntil {
    _vehicle getVariable ["engine_repaired", false]
};

_vehicle setFuel 1;
