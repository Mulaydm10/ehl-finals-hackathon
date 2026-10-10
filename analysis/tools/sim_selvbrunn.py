"""Replay supplier for P03 (Selvbrunn, sup:70530), built from its 7 live games - offline, no quota.

    cd tacto/starter-kit && .venv/Scripts/python.exe ../../analysis/tools/sim_selvbrunn.py [agent_file]

What it does, each rule from the live games (analysis/central/LEARNINGS.md, P03):
  - its cash value of a deal uses its real rate 6.1% at its standard 30 days (fitted on 3 deal breakdowns);
  - key account manager: stops at its 2% approval limit - EUR 430.15 @ 30 d / 431.61 @ 60 d (6 of 6 games), quoting
    payment days at +EUR 0.0487 a day, on the payment term of our first sheet (60 d when we sent 60/45/30);
  - committee (asked in the e-mail, or price held + escalation): EUR 433.08 @ 90 d, i.e. a cash value of 428.68
    (3 of 3), and 0.14 lower for a verified claim it "took into account" (Dhruv 8c2816f2d571b367: volume forecast ->
    432.94 @ 90 d, plus 431.47 @ 60 d as an alternative); price history / rising indices: no effect;
  - holds its price; `final_offer` after 3 unchanged replies; walks if pushed after final_offer;
  - agrees to any sheet at or above its stop.
Scenarios: `base` (as live), `kam_only` (ignores a round-1 committee request, like our 6 games), `house` (committee
stop at the cash value the house agent's 0.925 implies: 427.67). Scores use the calibrated exact cost (arena-equal).
"""

import importlib.util
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tacto/starter-kit"))
from arena_kit.cost import complete_offer, total_cost  # noqa: E402

CASE = next(c for c in json.loads((ROOT / "datasets/cases_practice.json").read_text(encoding="utf-8"))
            if c["case_id"] == "case:P03")
PROBE = json.loads((ROOT / "analysis/cases/openings/P03.json").read_text(encoding="utf-8"))
C_OPEN, C_BEST = PROBE["result"]["c_open"], PROBE["result"]["c_best"]
RATE, FULL_COST, STD_DAYS = 0.061, 395.30, 30
STD = {"payment_days": 30, "incoterm": "DAP", "lead_time_days": 49}
EST = {"standard": STD, "interest_rate": RATE, "full_cost": FULL_COST}
KAM_30, SLOPE = 430.15, 0.0487
COMMITTEE_CASH = {"base": 428.68, "kam_only": 428.68, "house": 427.67}
TAKEN_STEP = 0.14 * (1 - RATE * 60 / 360)  # cash value of Dhruv's EUR 0.14 at 90 d
TAKEN = {"fc:": True, "cost:": True}  # kinds it took into account; po / idx: "does not change our calculation"


def cash(t):
    return t["unit_price"] * (1 - RATE * (t["payment_days"] - STD_DAYS) / 360)


def price_for(v, days):
    return round(v / (1 - RATE * (days - STD_DAYS) / 360), 2)


def score(t):
    return (C_OPEN - total_cost(CASE, complete_offer(CASE, t), STD, EST)) / (C_OPEN - C_BEST)


def load(path):
    spec = importlib.util.spec_from_file_location("arena_kit.agents._sim_agent", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod.NoIdeaAgent


def run(Agent, scenario="base", verbose=True):
    threads = {sid: [dict(m) for m in ms] for sid, ms in PROBE["threads"].items()}
    sid = next(iter(threads))
    events = threads[sid]
    agent, n, holds, committee, taken, standing = Agent(None), 0, 0, False, 0, None
    while n < 10:
        d = agent.decide(CASE, threads)
        msg = d["message"]
        if (act := msg.get("action")):
            if act["type"] == "walk_away":
                return 0.0, "walk", n
            sheet = next(x for x in events[-1]["term_sheets"] if x["term_sheet_id"] == act.get("term_sheet_id"))
            return score(sheet["terms"]), f"deal {sheet['terms']['unit_price']} @ {sheet['terms']['payment_days']} d", n
        n += 1
        if events[-1].get("status") == "final_offer":
            return 0.0, "walked (pushed after final_offer)", n
        sheets = [complete_offer(CASE, x["terms"]) for x in msg["term_sheets"]]
        body = msg.get("body") or ""
        new = [r for r in msg.get("refs") or [] if any(r.startswith(k) for k in TAKEN)]
        taken += len({r.split("@")[0] for r in new})
        asked = bool(re.search(r"(?i)committee|management", body)) and not (scenario == "kam_only" and n == 1)
        committee = committee or asked
        stop = (COMMITTEE_CASH[scenario] - TAKEN_STEP * taken) if committee else KAM_30
        ok = [t for t in sheets if cash(t) >= stop - 1e-6]
        if ok:
            t, status, alts = max(ok, key=lambda t: total_cost(CASE, t, STD, EST)), "agreed", []
        else:
            days = 90 if committee else sheets[0]["payment_days"]
            p = price_for(stop, days) if committee else round(KAM_30 + SLOPE * (days - 30), 2)
            t = complete_offer(CASE, {**sheets[0], "unit_price": p, "payment_days": days})
            alts = [complete_offer(CASE, {**t, "unit_price": round(price_for(stop, 60) if committee else KAM_30, 2),
                                          "payment_days": 60 if committee else 30})]
            holds = holds + 1 if standing and abs(standing - p) < 0.005 else 0
            standing = p
            status = "final_offer" if holds >= 3 else "open"
        if verbose:
            print(f"  r{n}: ours {[(x['unit_price'], x['payment_days']) for x in sheets]} refs {msg.get('refs')} -> "
                  f"{status} {t['unit_price']} @ {t['payment_days']} d (cash {cash(t):.2f}, score {score(t):.3f})")
        events += [{**msg, "from": "buyer"},
                   {"from": f"sales@{sid}", "status": status, "body": "Our management has frozen all price reductions.",
                    "term_sheets": [{"term_sheet_id": f"offer:{sid}-{n}", "terms": t}]
                    + [{"term_sheet_id": f"offer:{sid}-{n}-a", "terms": a} for a in alts]}]
    return 0.0, "timeout", n


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else str(ROOT / "analysis/agent_variants/noidea_neel.py")
    for sc in ("base", "kam_only", "house"):
        print(f"== scenario {sc}")
        s, end, n = run(load(path), sc)
        print(f"   score {s:.4f}  {end}  ({n} rounds)  {'BEATS' if s > 0.9249 else 'below'} house 0.9249")
