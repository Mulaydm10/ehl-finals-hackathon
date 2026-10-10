"""Replay the real P02 walk-away games (and the good P02 games) through the current agent at each supplier reply:
would it now accept before the walk? (no quota)"""
import json, logging, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tacto/starter-kit"))
logging.basicConfig(level=logging.WARNING)
from arena_kit.agents.noidea import NoIdeaAgent
from arena_kit.cost import total_cost
case = next(c for c in json.loads((ROOT / "datasets/cases_practice.json").read_text()) if c["case_id"] == "case:P02")
co, cb = 2282867, 2235514
for sess in ("150fb1c103141538", "4d18bd1107811ea9", "af2439f039d0e14f", "da8d0e3d77ce091c"):
    f = ROOT / f"datasets/runs/{sess}.json"
    if not f.exists():
        continue
    g = json.loads(f.read_text())
    sup, th = next(iter(g["threads"].items()))
    ms = th["messages"]
    a = NoIdeaAgent(None)
    out = []
    for i, m in enumerate(ms):
        if m.get("from") == "buyer" or m.get("status") not in ("open", "final_offer"):
            continue
        d = a.decide(case, {sup: ms[: i + 1]})["message"]
        act = d.get("action") or {}
        if act.get("type") == "accept":
            t = next(x["terms"] for x in m["term_sheets"] if x["term_sheet_id"] == act["term_sheet_id"])
            out.append(f"round {len(out) + 1}: ACCEPT {t['unit_price']} @ {t['payment_days']} d -> score {(co - total_cost(case, t)) / (co - cb):.2f}")
            break
        out.append(f"round {len(out) + 1}: send")
    print(sess, "live end:", g["session"].get("end_reason"), round(g["session"].get("score") or 0, 2), "| now:", "; ".join(out))
