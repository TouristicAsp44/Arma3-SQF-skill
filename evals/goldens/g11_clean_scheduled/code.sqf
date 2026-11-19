params [
    ["_triggerBox", objNull, [objNull]],
    ["_maxWaitSeconds", 30, [0]]
];

private _timeout = time + _maxWaitSeconds;

// waitUntil limpio con condición de salida doble garantizada por tiempo
waitUntil {
    time > _timeout || { !isNull (_triggerBox getVariable ["captured_by", objNull]) }
};

private _captured = !isNull (_triggerBox getVariable ["captured_by", objNull]);
_captured
