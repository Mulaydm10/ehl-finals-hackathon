"""Replay the real P08 game (a43d77c01405cba4) up to each supplier reply: what does the agent offer now?"""
import json, logging, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tacto/starter-kit"))
logging.basicConfig(level=logging.INFO, format="   log: %(message)s")
from arena_kit.agents.noidea import NoIdeaAgent
from arena_kit.cost import total_cost
case = next(c for c in json.loads((ROOT / "datasets/cases_practice.json").read_text()) if c["case_id"] == "case:P08")
co, cb = 1135887, 960309
ms = json.loads((ROOT / "datasets/runs/a43d77c01405cba4.json").read_text())["threads"]["sup:70710"]["messages"]
sup_idx = [i for i, m in enumerate(ms) if m.get("from") != "buyer"]
a = NoIdeaAgent(None)
for i in sup_idx[:3]:
    d = a.decide(case, {"sup:70710": ms[: i + 1]})["message"]
    sheets = d.get("term_sheets") or []
    print(f"after supplier msg {i} ({ms[i].get('status')}):", d.get("action") or [
        (t["terms"]["unit_price"], t["terms"]["payment_days"], (t["terms"].get("index_clause") or {}).get("deadband_pct", "none"),
         f"score {(co - total_cost(case, t['terms'])) / (co - cb):.2f}") for t in sheets])
print("clause_required:", a.sup["sup:70710"].get("clause_required"), "| k:", a.sup["sup:70710"].get("k"))
for db in (0, 3, 5):
    t = {"unit_price": 5.21 + 0.024 * db, "payment_days": 45, "contract_months": 24,
         "index_clause": {"series": "AS-14404", "material_share": 0.45, "deadband_pct": db, "base_month": "2026-08"}}
    print(f"its price for db{db} ~{t['unit_price']:.3f} @45d -> score {(co - total_cost(case, t)) / (co - cb):.3f}")
