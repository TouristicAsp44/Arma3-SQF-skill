// Definición que espera 2 parámetros numéricos obligatorios
fnc_calculateVector = {
    params [
        ["_origin", [0,0,0], [[]], [3]],
        ["_magnitude", 0, [0]]
    ];
    _origin vectorMultiply _magnitude
};

// Llamada que pasa parámetros incompatibles (array de 2 elementos en vez de 3 y string en magnitud)
[["pos1", "pos2"], "invalid_scalar"] call fnc_calculateVector;
