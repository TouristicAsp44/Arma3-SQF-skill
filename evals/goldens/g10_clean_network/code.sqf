params [
    ["_caller", objNull, [objNull]],
    ["_missionId", "", [""]]
];

if (!isServer) exitWith { false };
if (isNull _caller) exitWith { false };

private _ownerId = owner _caller;
private _payload = [_missionId, true];

// Envío dirigido al cliente solicitante sin broadcast global
_payload remoteExec ["TAG_fnc_onMissionAssigned", _ownerId, false];

true
