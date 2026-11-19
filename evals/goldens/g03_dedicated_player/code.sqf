// Script de inicialización que corre en servidor dedicado (player es permanentemente objNull)
waitUntil {!isNull player};

player setVariable ["player_ready", true, true];
