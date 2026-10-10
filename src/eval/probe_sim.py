"""Replay real P11 games up to its last hold, then simulate a grid-floor supplier: it agrees to any ask >= floor, else holds.
Prints our probe asks and the deal for several floors. (no quota)"""
import json, sys, logging, copy
from pathlib import Path
ROOT = Path.home() / "Dhruv/ehl-finals-hackathon"
sys.path.insert(0, str(ROOT / "tacto/starter-kit"))
logging.disable(logging.WARNING)
from arena_kit.agents.noidea import NoIdeaAgent
from arena_kit.cost import total_cost, complete_offer
case = next(c for c in json.loads((ROOT / "datasets/cases_practice.json").read_text()) if c["case_id"] == "case:P11")
CO, CB = 817578, 722500
stub = lambda s_, u: json.dumps({"sheets": [0], "args": [], "opening": "x", "notes": {}})
sess, cut = sys.argv[1], int(sys.argv[2])  # use the real thread up to message index `cut` (a supplier hold)
g = json.loads((ROOT / f"datasets/runs/{sess}.json").read_text()); sid, th = next(iter(g["threads"].items()))
for floor in [float(x) for x in sys.argv[3:]]:
    a = NoIdeaAgent(stub)
    ms = copy.deepcopy(th["messages"][:cut])
    for n in range(1, cut + 1):
        if ms[n - 1].get("from") != "buyer":
            d = a.decide(case, {sid: ms[:n]})
            a.cited |= set(d["message"].get("refs") or [])
    hold = copy.deepcopy(ms[-1])
    asks, deal = [], None
    for r in range(8):
        d = a.decide(case, {sid: ms})["message"]
        if d.get("action"):
            deal = hold["term_sheets"][0]["terms"]["unit_price"] if d["action"]["type"] == "accept" else None
            break
        ask = d["term_sheets"][0]["terms"]["unit_price"]; asks.append(ask)
        ms.append({"from": "buyer", "term_sheets": d["term_sheets"], "refs": d.get("refs"), "body": d.get("body", "")})
        if ask >= floor:
            deal = ask; break
        h = copy.deepcopy(hold); ms.append(h)
    t = complete_offer(case, {**case["fixed_terms"], "unit_price": deal, "ppm_commitment": 300, "chargeback_eur_per_complaint": 0}) if deal else None
    sc = (CO - total_cost(case, t)) / (CO - CB) if t else 0
    print(f"floor {floor:.2f}: asks {asks} -> deal {deal} score {sc:.3f}")
