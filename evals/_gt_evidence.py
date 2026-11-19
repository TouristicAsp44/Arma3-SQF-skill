"""Evidencia para la correccion del ground truth: que reporta el modelo y donde."""

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "evals"))
sys.path.insert(0, str(REPO / "skills" / "arma3-sqf-skill" / "scripts"))

from harness import parse_report_output

runs = REPO / "evals" / "runs"

for gid in ("g01_syntax_scope", "g03_dedicated_player", "g08_forbidden_cba", "b06_dependencia"):
    print(f"\n{'=' * 78}\n{gid}")
    code = REPO / "evals" / "goldens" / gid / "code.sqf"
    print("--- code.sqf numerado:")
    for i, line in enumerate(code.read_text(encoding="utf-8").splitlines(), 1):
        print(f"  {i:2}: {line}")
    print("--- esperado:")
    exp = json.loads((REPO / "evals" / "goldens" / gid / "expected.json").read_text(encoding="utf-8"))
    for h in exp.get("hallazgos", []):
        print(f"  cat{h['categoria']} L{h['linea']} [{h['severidad']}] {h['disciplina']} — {h['descripcion']}")
    print(f"  bloqueantes_esperados={exp.get('bloqueantes_esperados')}")
    print("--- detectado por el modelo (rep1, modo archivo):")
    p = next(iter(runs.rglob(f"{gid}_rep1.json")), None)
    if p:
        t = json.loads(p.read_text(encoding="utf-8"))
        for f in parse_report_output(t.get("respuesta_cruda", "")):
            if f.severity == "BLOQUEANTE":
                print(f"  [BLOQUEANTE] L{f.line} ({f.discipline}) cat={f.category}")
                print(f"      {f.description[:220]}")
