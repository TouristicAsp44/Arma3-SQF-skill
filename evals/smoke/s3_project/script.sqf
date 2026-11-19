/*
    Caso S3: Invocación remoteExec no autorizada + Dependencia CBA no permitida
    Perfil del proyecto:
      CBA: no
      ACE3: no
      DESTINO: mision
    Esperado:
      - Cat. 5: BLOQUEANTE por remoteExec de fnc_unauthorizedFunction ausente de CfgRemoteExec >> Functions (mode = 1).
      - Cat. 7: BLOQUEANTE por uso de CBA_fnc_hashCreate cuando el perfil declara CBA: no.
*/

params ["_data"];

// Cat. 5: Invocación remota de función ausente en la whitelist de CfgRemoteExec (mode = 1)
[_data] remoteExec ["fnc_unauthorizedFunction", 0, false];

// Cat. 7: Inyección de dependencia de framework prohibida por el perfil (CBA: no)
private _map = [] call CBA_fnc_hashCreate;

_map
