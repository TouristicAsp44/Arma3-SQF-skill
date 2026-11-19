params ["_unit"];

_unit addEventHandler ["Killed", {
    params ["_victim", "_killer"];
    sleep 2;
    deleteVehicle _victim;
}];
