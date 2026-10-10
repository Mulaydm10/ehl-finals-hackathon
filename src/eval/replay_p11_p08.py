"""Replay the real v2.9 P11 and P08 games turn by turn through v2.10: what would it send now? (no quota)"""
import json, logging, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tacto/starter-kit"))
logging.basicConfig(level=logging.WARNING)
from arena_kit.agents.noidea import NoIdeaAgent
cases = {c["case_id"]: c for c in json.loads((ROOT / "datasets/cases_practice.json").read_text())}
for sess, cid, keys in (("a6cb7ced9fdbae89", "case:P11", ("unit_price", "ppm_commitment", "chargeback_eur_per_complaint")),
                        ("9bfa86104bcbdd30", "case:P08", ("unit_price", "payment_days", "index_clause"))):
    g = json.loads((ROOT / f"datasets/runs/{sess}.json").read_text())
    sup, th = next(iter(g["threads"].items()))
    ms = th["messages"]
    a = NoIdeaAgent(None)
    print("=====", cid)
    for i, m in enumerate(ms):
        if m.get("from") == "buyer" or m.get("status") not in ("open", "final_offer"):
            continue
        d = a.decide(cases[cid], {sup: ms[: i + 1]})["message"]
        theirs = [{k: (x["terms"].get(k) if k != "index_clause" else (x["terms"].get(k) or {}).get("deadband_pct")) for k in keys} for x in m.get("term_sheets") or []]
        ours = d.get("action") or [{k: (t["terms"].get(k) if k != "index_clause" else (t["terms"].get(k) or {}).get("deadband_pct", "none")) for k in keys} for t in d.get("term_sheets", [])]
        print(f"  it: {theirs}\n     -> v2.10: {ours}")
