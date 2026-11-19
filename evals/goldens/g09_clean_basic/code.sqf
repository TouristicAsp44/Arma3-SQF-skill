params [
    ["_basePos", [0, 0, 0], [[]], [3]],
    ["_radius", 100, [0]]
];

private _offsetX = random [-_radius, 0, _radius];
private _offsetY = random [-_radius, 0, _radius];

private _targetPos = [
    (_basePos select 0) + _offsetX,
    (_basePos select 1) + _offsetY,
    _basePos select 2
];

_targetPos
