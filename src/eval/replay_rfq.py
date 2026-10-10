"""Replay the real P05 RFQ games: at each of our turns, what would the current agent ask each bidder? (no quota)"""
import json, logging, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tacto/starter-kit"))
logging.basicConfig(level=logging.WARNING)
from arena_kit.agents.noidea import NoIdeaAgent
case = next(c for c in json.loads((ROOT / "datasets/cases_practice.json").read_text()) if c["case_id"] == "case:P05")
g = json.loads((ROOT / "datasets/runs/26c6afc937d25c36.json").read_text())
full = {s: th["messages"] for s, th in g["threads"].items()}
# state after every bidder's first reply (round 1 done)
state = {s: ms[:3] for s, ms in full.items()}
a = NoIdeaAgent(None)
a.decide(case, {s: ms[:1] for s, ms in full.items()})
for s in full:
    a.sup[s].pop("ours", None)  # fresh concession path from this state
for _ in range(3):
    d = a.decide(case, state)
    sid, m = d["supplier_id"], d["message"]
    print(sid, "->", m.get("action") or [(t["terms"]["unit_price"], t["terms"].get("lead_time_days"), t["terms"].get("payment_days")) for t in m["term_sheets"]],
          "| market low for it:", a.market_low(case, sid), "| cites:", [l for l in m.get("body", "").split(". ") if "We have an offer" in l][:1])
    state[sid] = state[sid] + [{**m, "from": "buyer"}, state[sid][-1]]
