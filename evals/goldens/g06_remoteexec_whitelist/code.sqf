params ["_target"];

// fnc_unauthorizedRemote no está en la whitelist de CfgRemoteExec (mode = 1)
[_target] remoteExec ["fnc_unauthorizedRemote", 2, false];
