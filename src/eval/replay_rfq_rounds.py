"""Replay Parth's 0.965 P05 game in its REAL order (round by round across bidders) through the RFQ layer. (no quota)"""
import json, sys, logging
from pathlib import Path
ROOT = Path.home() / "Dhruv/ehl-finals-hackathon"
sys.path.insert(0, str(ROOT / "tacto/starter-kit"))
logging.basicConfig(level=logging.INFO, format="   log: %(message)s")
for n in ("httpx", "openai", "httpcore"):
    logging.getLogger(n).setLevel(logging.WARNING)
from arena_kit.agents.noidea_rfq import NoIdeaAgent
case = next(c for c in json.loads((ROOT / "datasets/cases_practice.json").read_text()) if c["case_id"] == "case:P05")
g = json.loads((ROOT / f"datasets/runs/{sys.argv[1]}.json").read_text())
full = {s: th["messages"] for s, th in g["threads"].items()}
a = NoIdeaAgent(lambda s_, u: json.dumps({"sheets": [0], "args": [], "opening": "x", "notes": {}}))
sup_idx = {s: [i for i, m in enumerate(ms) if m.get("from") != "buyer"] for s, ms in full.items()}
for r in range(max(len(v) for v in sup_idx.values())):
    th = {s: full[s][: (sup_idx[s][min(r, len(sup_idx[s]) - 1)] + 1)] for s in full}
    for s in full:
        if r >= len(sup_idx[s]) or full[s][sup_idx[s][r]].get("status") in ("agreed", "final_offer", "walked_away"):
            if r < len(sup_idx[s]):
                pass
        a.focus = {s}
        d = a.decide(case, th)
        m = d.get("message") or {}
        what = m.get("action") or ([(x["terms"]["unit_price"], x["terms"]["payment_days"]) for x in m.get("term_sheets", [])] or "NOTE (no price)")
        sp = (th[s][-1].get("term_sheets") or [{}])[0].get("terms", {}).get("unit_price")
        print(f"r{r} {s} stands {th[s][-1].get('status')} {sp} -> we to {d.get('supplier_id')}: {what}")
