"""Per practice case: the supplier's price granularity in its own history (price_conditions, po_lines, quotes) and its
opening quote; plus its motives. Is a coarse price grid (P11: 0.50 steps) visible BEFORE round 1?"""
import json, sqlite3, collections
from pathlib import Path
ROOT = Path.home() / "Dhruv/ehl-finals-hackathon"
cases = json.loads((ROOT / "datasets/cases_practice.json").read_text())
cases = cases if isinstance(cases, list) else list(cases.values())
dos = json.loads((ROOT / "datasets/A_dossiers.json").read_text())
db = sqlite3.connect(ROOT / "tacto/starter-kit/data/package/world.sqlite")
def grid(prices):
    out = {}
    for g in (1.0, 0.5, 0.25, 0.1, 0.05):
        out[g] = round(sum(abs(p / g - round(p / g)) < 1e-6 for p in prices) / max(len(prices), 1), 2)
    return out
for c in cases:
    cid = c.get("case_id") or c.get("id")
    sups = [s if isinstance(s, str) else (s.get("supplier_id") or s.get("id")) for s in c.get("suppliers") or []]
    parts = [p if isinstance(p, str) else (p.get("part_id") or p.get("id")) for p in c.get("parts") or []]
    for sid in sups:
        num = (sid or "").split(":")[-1]
        pc = [r[0] for r in db.execute("select price from price_conditions where supplier_id like ? and part_id like ?", (f"%{num}", f"%{parts[0].split(':')[-1]}" if parts else "%"))]
        po = [r[0] for r in db.execute("select distinct price from po_lines where supplier_id like ? and part_id like ?", (f"%{num}", f"%{parts[0].split(':')[-1]}" if parts else "%"))]
        qu = [r[0] for r in db.execute("select unit_price from quotes where supplier_id like ?", (f"%{num}",))]
        d = dos.get(sid) or dos.get(num) or {}
        mot = sorted((d.get("motives") or {}).keys()) if isinstance(d, dict) else []
        print(cid, c.get("type"), sid, "pc", sorted(set(pc))[:8], "grid", grid(pc), "| po n", len(po), "grid", grid(po), "| quotes", qu[:5], "| motives", mot)
