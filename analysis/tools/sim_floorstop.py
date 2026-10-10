"""A simulated supplier calibrated on the REAL P04 supplier (live session d3050f951dc2c45b), no arena calls.

Real behaviour (trace): opening EUR 4.96 @ 30 d; round 1 its cash value fell to 4.877 (60 d), round 2 to
4.874 (90 d), round 3 `final_offer` at the same 4.874 while our sheets stayed ~1% lower; we accepted (0.86).
C_best says it would accept a cash value of ~4.864 (its floor F).

Model (cash value = arena_kit.cost.supplier_value at its standard terms, money at `rate`):
  - agrees if one of our sheets is worth >= F to it (picks the one dearest for us);
  - else counters on the structure of our highest-price sheet, moving a share `r` of the value gap, but never
    below its stop S = F x (1 + markup);
  - says final_offer once it has stood at S for `patience` rounds; pushing after final_offer: it walks.
F comes from the case's exact C_best: the value of the opening structure priced to cost us C_best.
Defaults reproduce the live P04 game (r 0.54, markup 0.15%, patience 1).

    cd tacto/starter-kit && uv run python ../../analysis/tools/sim_floorstop.py P04 [--agent-file F] [--llm]
"""

import argparse
import importlib.util
import itertools
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tacto/starter-kit"))
sys.path.insert(0, str(ROOT / "src/eval"))
from arena_kit.cost import complete_offer, supplier_value, total_cost  # noqa: E402
from arena_kit.docs import standard_terms  # noqa: E402
from offline_eval import price_for  # noqa: E402


def load_agent(path):
    if not path:
        from arena_kit.agents.noidea import NoIdeaAgent
        return NoIdeaAgent
    spec = importlib.util.spec_from_file_location("arena_kit.agents._sim_agent", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod.NoIdeaAgent


def run(Agent, case, opening, c_open, c_best, r=0.54, markup=0.0015, patience=1, rate=0.08, complete=None,
        max_rounds=10, verbose=False):
    threads = {sid: [dict(m) for m in ms] for sid, ms in opening.items()}
    sid = next(iter(threads))
    events = threads[sid]
    std = standard_terms(events)
    sup = {"standard": {**complete_offer(case, events[0]["term_sheets"][0]["terms"]), **std}, "interest_rate": rate}
    val = lambda t: supplier_value(case, complete_offer(case, t), sup)  # noqa: E731
    open_t = complete_offer(case, events[0]["term_sheets"][0]["terms"])
    # C_best = the cheapest package at value >= F, so F = the highest value any package has at C = C_best
    opts = {f: v for f, v in case.get("term_options", {}).items() if f in case["negotiable"] and f != "index_clause"}
    F = max(supplier_value(case, {**t, "unit_price": price_for(case, t, std, c_best)}, sup)  # exact, not cent-rounded
            for vals in itertools.product(*opts.values())
            for t in [complete_offer(case, {**open_t, **dict(zip(opts, vals))})])
    S = F * (1 + markup)
    if verbose:
        print(f"  supplier floor F = {F:.4f}, stop S = {S:.4f}")
    agent, at_stop, n = Agent(complete), 0, 0
    score = lambda t: (c_open - total_cost(case, t, std)) / (c_open - c_best)  # noqa: E731
    while n <= max_rounds:
        d = agent.decide(case, threads)
        msg = d["message"]
        if (act := msg.get("action")):
            if act["type"] == "walk_away":
                return 0.0, "walk", n
            t = events[-1]["term_sheets"][0]["terms"]
            return max(0.0, min(1.0, score(t))), f"deal {t}", n
        n += 1
        if events[-1].get("status") == "final_offer":
            return 0.0, "walked (pushed after final_offer)", n
        sheets = [complete_offer(case, t["terms"]) for t in msg["term_sheets"]]
        prev = complete_offer(case, events[-1]["term_sheets"][0]["terms"])
        ok = [t for t in sheets if val(t) >= F - 1e-4]
        if ok:
            t, status = max(ok, key=lambda t: total_cost(case, t, std)), "agreed"
        else:
            base = max(sheets, key=lambda t: t["unit_price"])  # live P04: it countered on our highest-price sheet
            target = max(S, val(prev) - r * (val(prev) - max(val(x) for x in sheets)))
            p1 = val({**base, "unit_price": 1.0})
            slope = val({**base, "unit_price": 2.0}) - p1
            t = complete_offer(case, {**base, "unit_price": round(1.0 + (target - p1) / slope, 2)})
            at_stop = at_stop + 1 if val(t) <= S + 0.0005 else 0
            status = "final_offer" if at_stop > patience or n >= max_rounds else "open"
        if verbose:
            print(f"  r{n}: ours {[(x['unit_price'], x.get('payment_days'), round(val(x), 3)) for x in sheets]}"
                  f" -> {status} {t.get('unit_price')} @ {t.get('payment_days')} d (value {val(t):.3f}, score {score(t):.2f})")
        events += [{**msg, "from": "buyer"},
                   {"from": f"sales@{sid}", "status": status, "body": "",
                    "term_sheets": [{"term_sheet_id": f"offer:{sid}-{n}", "terms": t}]}]
    return 0.0, "timeout", n


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("case")
    ap.add_argument("--agent-file")
    ap.add_argument("--llm", action="store_true", help="let the LLM in tacto/starter-kit/.env.openai write (paid)")
    a = ap.parse_args()
    complete = None
    if a.llm:
        import os
        for line in (ROOT / "tacto/starter-kit/.env.openai").read_text().splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip()
        from arena_kit.agents.llm import llm_from_env
        complete = llm_from_env()
    case = next(c for c in json.loads((ROOT / "datasets/cases_practice.json").read_text(encoding="utf-8"))
                if c["case_id"] == f"case:{a.case}")
    probe = json.loads((ROOT / "analysis/cases/openings" / f"{a.case}.json").read_text(encoding="utf-8"))
    res = probe["result"]
    s, end, n = run(load_agent(a.agent_file), case, probe["threads"], res["c_open"], res["c_best"],
                    complete=complete, verbose=True)
    print(f"{a.case}: score {s:.2f}  {end}  ({n} rounds)")
