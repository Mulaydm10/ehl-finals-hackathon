"""Replay real P11 games: feed each prefix ending on a supplier message; print what the agent would send."""
import json, sys, logging
from pathlib import Path
ROOT = Path.home() / "Dhruv/ehl-finals-hackathon"
sys.path.insert(0, str(ROOT / "tacto/starter-kit"))
from arena_kit.agents.noidea import NoIdeaAgent
logging.basicConfig(level=logging.WARNING)
case = next(c for c in json.loads((ROOT / "datasets/cases_practice.json").read_text()) if c["case_id"] == "case:P11")
stub = lambda system, user: json.dumps({"sheets": [0], "args": [], "opening": "Thank you.", "notes": {}})
for sess in sys.argv[1:]:
    g = json.loads((ROOT / f"datasets/runs/{sess}.json").read_text())
    sid, th = next(iter(g["threads"].items()))
    ms = th["messages"]
    a = NoIdeaAgent(stub)
    print("====", sess)
    for n in range(1, len(ms) + 1):
        if ms[n - 1].get("from") == "buyer" or ms[n - 1].get("status") == "agreed":
            continue
        d = a.decide(case, {sid: ms[:n]})["message"]
        theirs = [(x["terms"].get("ppm_commitment"), x["terms"].get("chargeback_eur_per_complaint"), x["terms"].get("unit_price")) for x in ms[n - 1].get("term_sheets") or []]
        ours = [(x["terms"].get("ppm_commitment"), x["terms"].get("chargeback_eur_per_complaint"), round(x["terms"]["unit_price"], 2)) for x in d.get("term_sheets", [])]
        print(f"  it {ms[n-1].get('status')} {theirs} -> we {d.get('action') or ours}")
    print("  k:", {f: round(v, 4) for f, v in (a.sup[sid].get('k') or {}).items()})
