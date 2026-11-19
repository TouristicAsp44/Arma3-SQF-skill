params ["_unit"];

// Los Event Handlers del motor corren en contexto unscheduled (canSuspend == false)
_unit addEventHandler ["Killed", {
    params ["_unit", "_killer"];
    sleep 2;
    deleteVehicle _unit;
}];
