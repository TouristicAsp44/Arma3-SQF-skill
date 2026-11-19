/*
    Caso S1: Variable sin private + waitUntil sin salida garantizada
    Esperado:
      - Cat. 1: BLOQUEANTE por variable local `_leakedVar` sin private/params.
      - Cat. 2: BLOQUEANTE por waitUntil sin timeout ni garantía de salida.
*/

params ["_targetUnit"];

// Cat. 1: Variable local no declarada en private ni recibida en params (fuga al scope exterior)
_leakedVar = getPosATL _targetUnit;

// Cat. 2: waitUntil sin condición de salida garantizada ni timeout de seguridad
waitUntil {
    _targetUnit getVariable ["mission_completed", false]
};

_leakedVar
