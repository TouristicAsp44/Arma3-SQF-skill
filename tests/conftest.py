import sys
from pathlib import Path

plugin_root = Path(__file__).resolve().parent.parent
scripts_root = plugin_root / "scripts"
scripts_dir = plugin_root / "skills" / "arma3-sqf-skill" / "scripts"
references_dir = plugin_root / "skills" / "arma3-sqf-skill" / "references"

for d in [plugin_root, scripts_root, scripts_dir, references_dir]:
    sd = str(d)
    if sd not in sys.path:
        sys.path.insert(0, sd)
