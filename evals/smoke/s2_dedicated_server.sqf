/*
    Caso S2: player en init de servidor + hint en ruta de servidor
    Esperado:
      - Cat. 3: BLOQUEANTE por uso de player en contexto de inicialización que corre en dedicado (player es objNull).
      - Cat. 3: BLOQUEANTE por comando de interfaz (hint) en ruta de servidor (con y sin guarda hasInterface; la guarda NO legitima).
*/

// Cat. 3: player en script de inicialización global (en servidor dedicado player es objNull)
waitUntil {!isNull player};
player setDamage 0;

// Cat. 3: comando UI directo en ruta del servidor
if (isServer) then {
    hint "Servidor inicializado correctamente";
};

// Cat. 3: comando UI con guarda hasInterface en ruta de servidor (la guarda evita el error pero no el trabajo inútil; debe ir por remoteExec)
if (isServer) then {
    if (hasInterface) then {
        hint "Host o jugador en servidor";
    };
};
