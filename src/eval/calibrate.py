"""How far below the opening quote is the best deal? Calibrates the agent's anchors.

Uses Neel's exact probe results (analysis/cases/openings/*.json: c_open, c_best) and the score-1.0
packages from analysis/cases/README.md. Run from the repo root:  python3 src/eval/calibrate.py
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
cases = {c["case_id"][5:]: c for c in json.loads((ROOT / "datasets/cases_practice.json").read_text())}
readme = (ROOT / "analysis/cases/README.md").read_text().splitlines()

print(f"{'case':4} {'type':14} {'goal':13} {'current':>9} {'opening':>9} {'best':>9} {'best/open':>9} {'best/cur':>9}  score-1 package")
for f in sorted((ROOT / "analysis/cases/openings").glob("*.json")):
    cid = f.stem
    d, c = json.loads(f.read_text()), cases[cid]
    prices = [m["term_sheets"][0]["terms"].get("unit_price") for ms in d["threads"].values()
              for m in ms if m.get("term_sheets")]
    opening = min(p for p in prices if p)
    row = next(l for l in readme if l.startswith(f"| [{cid}]")).split("|")[-2].strip()
    m = re.findall(r"€\s?([\d.]+)", row)
    best = float(m[0]) if m else None
    cur = c["buyer"]["current_unit_price"]
    print(f"{cid:4} {c['type']:14} {c['buyer']['category_goal']:13} {cur:9.2f} {opening:9.2f} {best or 0:9.2f} "
          f"{(best / opening - 1) if best else 0:+9.1%} {(best / cur - 1) if best else 0:+9.1%}  {row[:70]}")
