"""Crash test of the final's agent on ALL practice cases (hosted or not): a simple simulated supplier (opens ~6% above
today's price on its standard terms, then meets us halfway on our structure, final_offer in round 4). Calls the inner
logic (no safety net) so any exception shows with its traceback; then the outer decide() to check the safety net.
    cd tacto/starter-kit && NOIDEA_EXPERIMENTS=hidden .venv/bin/python crash_test.py"""
import json, sys, logging, traceback, copy
from pathlib import Path
ROOT = Path.home() / "Dhruv/ehl-finals-hackathon"
sys.path.insert(0, str(ROOT / "tacto/starter-kit"))
logging.disable(logging.CRITICAL)
from arena_kit.agents.noidea_rfq import NoIdeaAgent
from arena_kit.cost import complete_offer
cases = json.loads((ROOT / "datasets/cases_practice.json").read_text())
dos = json.loads((ROOT / "datasets/A_dossiers.json").read_text())

def opening(case, sid, j):
    d = dos.get(sid, {})
    part = case["parts"][0]
    p = next((x for x in d.get("parts", []) if x["part"] == part), {})
    cur = case["buyer"].get("current_unit_price") or p.get("current_price") or 50.0
    t = {"unit_price": round(float(cur) * (1.06 + 0.02 * j), 2)}
    std = d.get("standard_terms") or {}
    for f in case["negotiable"]:
        if f == "unit_price":
            continue
        opts = case.get("term_options", {}).get(f) or []
        if f in std and std[f] is not None and (not opts or std[f] in opts):
            t[f] = std[f]
        elif opts:
            t[f] = opts[0]
    num = sid.split(":")[-1]
    return {"from": f"sales@{num}", "status": "open", "body": "Thank you for your enquiry. Please find our offer below.",
            "term_sheets": [{"term_sheet_id": f"offer:{num}-0", "terms": t}]}

def reply(case, sid, ev, msg, n):
    num = sid.split(":")[-1]
    prev = next(m for m in reversed(ev) if m.get("from") != "buyer")
    pp = prev["term_sheets"][0]["terms"]["unit_price"]
    ours = (msg.get("term_sheets") or [{}])[0].get("terms") or prev["term_sheets"][0]["terms"]
    ask = ours.get("unit_price") or pp
    t = {**ours, "unit_price": round((pp + ask) / 2, 2)}
    st = "final_offer" if n >= 4 else "open"
    return {"from": f"sales@{num}", "status": st, "body": "We checked the data you cited; it holds. Our margin stays internal.",
            "term_sheets": [{"term_sheet_id": f"offer:{num}-{n}", "terms": t}]}

bad = 0
for case in cases:
    cid = case["case_id"]
    threads = {sid: [opening(case, sid, j)] for j, sid in enumerate(case["suppliers"])}
    a = NoIdeaAgent()
    path, err = [], None
    for n in range(1, 9):
        try:
            d = a._decide_layer(case, copy.deepcopy(threads)) if hasattr(a, "_decide_layer") else a._decide(case, threads)
        except Exception:
            err = traceback.format_exc(limit=6)
            d = a.decide(case, copy.deepcopy(threads))  # the safety net must still give a move
            path.append(f"SAFE:{list((d.get('message') or {}).keys())}")
            break
        sid, msg = d["supplier_id"], d["message"]
        if msg.get("action"):
            path.append(f"{msg['action']['type']}")
            break
        p = (msg.get("term_sheets") or [{}])[0].get("terms", {}).get("unit_price")
        path.append(f"{sid.split(':')[-1]}:{p}")
        threads[sid] = threads[sid] + [{**msg, "from": "buyer"}, reply(case, sid, threads[sid], msg, n)]
    status = "CRASH" if err else "ok"
    bad += bool(err)
    print(f"{cid} {case['type']:14s} hosted={case.get('hosted')!s:5s} {status:5s} {' -> '.join(path)}")
    if err:
        print("   " + err.replace("\n", "\n   ")[:1500])
print("crashes:", bad)
