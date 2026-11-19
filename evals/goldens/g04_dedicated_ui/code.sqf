if (isServer) then {
    // Comandos de interfaz prohibidos en rutas de servidor; hasInterface no legitima
    if (hasInterface) then {
        hint "Host local del servidor inicializado";
    };
};
