"""Offline evaluation of a buyer agent on the probed practice cases - no practice quota used.

A crude simulated supplier stands in for the arena's: it starts from the REAL opening quote (Neel's
probes, analysis/cases/openings/*.json) and the EXACT C_open / C_best of the case.
  - it agrees to one of our sheets as soon as that sheet costs us at least C_best (C_best is the
    cheapest package any supplier in the case accepts), picking the one dearest for us;
  - otherwise it takes over the structure of our cheapest sheet and moves its price a share `r` of
    the way to ours, never below the price at which that structure costs C_best; at that floor it
    says final_offer.
`responsive` uses r = 0.30, `stubborn` r = 0.10. It ignores arguments, tone and the relationship
charge, so it ranks strategies; it does not predict arena scores. Validate the winners live.

    cd tacto/starter-kit && .venv/bin/python ../../src/eval/offline_eval.py [--agent-file F] [cases...]
"""
import argparse
import importlib.util
import json
import logging
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tacto/starter-kit"))
from arena_kit.cost import complete_offer, total_cost  # noqa: E402
from arena_kit.docs import standard_terms  # noqa: E402

P01 = {"c_open": 1153779.74, "c_best": 1096815.78,  # from sessions a44d..., e3e0...
       "threads": {"sup:70110": [{"from": "sales@70110", "status": "open", "body": "Price adjustment +9.5 %.",
                                  "term_sheets": [{"term_sheet_id": "offer:70110-0", "terms": {
                                      "unit_price": 138.55, "payment_days": 30, "effective_date": "2026-11-01"}}]}]}}


def load_agent(path):
    if not path:
        from arena_kit.agents.noidea import NoIdeaAgent
        return NoIdeaAgent
    spec = importlib.util.spec_from_file_location("arena_kit.agents._eval_agent", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod.NoIdeaAgent


def price_for(case, terms, std, c_target):
    """The unit price at which `terms` cost us exactly c_target (C is linear in the price)."""
    a = total_cost(case, {**terms, "unit_price": 100.0}, std)
    b = total_cost(case, {**terms, "unit_price": 200.0}, std)
    return 100.0 + (c_target - a) / ((b - a) / 100.0)


def simulate(Agent, case, opening, c_open, c_best, r, max_rounds=10):
    threads = {sid: [dict(m) for m in ms] for sid, ms in opening.items()}
    agent, n = Agent(None), {sid: 0 for sid in threads}
    for _ in range(max_rounds * len(threads) + 2):
        d = agent.decide(case, threads)
        sid, msg = d["supplier_id"], d["message"]
        events = threads[sid]
        std = standard_terms(events)
        act = msg.get("action")
        if act:
            if act["type"] == "walk_away":
                if len([s for s in threads if threads[s][-1].get("status") not in ("walked_away",)]) > 1:
                    threads[sid].append({"from": sid, "status": "walked_away", "body": ""})
                    continue
                c_alt = agent.c_alt
                return (0.0 if c_alt == math.inf else max(0.0, (c_open - c_alt) / (c_open - c_best))), "walk", sum(n.values())
            sheet = events[-1]["term_sheets"][0]["terms"]
            c = total_cost(case, sheet, std)
            return max(0.0, min(1.0, (c_open - c) / (c_open - c_best))), "deal", sum(n.values())
        n[sid] += 1
        sheets = [complete_offer(case, t["terms"]) for t in msg["term_sheets"]]
        costs = [total_cost(case, t, std) for t in sheets]
        ok = [(c, t) for c, t in zip(costs, sheets) if c >= c_best - 1]
        prev = events[-1]["term_sheets"][0]["terms"] if events[-1].get("term_sheets") else sheets[0]
        if ok:
            c, t = max(ok, key=lambda x: x[0])
            reply = {"status": "agreed", "terms": t}
        else:
            t = min(zip(costs, sheets), key=lambda x: x[0])[1]
            floor = price_for(case, t, std, c_best)
            p = max(floor, prev["unit_price"] - r * (prev["unit_price"] - t["unit_price"]))
            reply = {"status": "final_offer" if p <= floor + 0.005 or n[sid] >= max_rounds else "open",
                     "terms": {**t, "unit_price": round(p, 2)}}
        events += [{**msg, "from": "buyer"},
                   {"from": f"sales@{sid}", "status": reply["status"], "body": "",
                    "term_sheets": [{"term_sheet_id": f"offer:{sid}-{n[sid]}", "terms": reply["terms"]}]}]
    return 0.0, "timeout", sum(n.values())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cases", nargs="*")
    ap.add_argument("--agent-file")
    a = ap.parse_args()
    logging.basicConfig(level=logging.WARNING)
    Agent = load_agent(a.agent_file)
    cases = {c["case_id"][5:]: c for c in json.loads((ROOT / "datasets/cases_practice.json").read_text())}
    probes = {f.stem: json.loads(f.read_text()) for f in (ROOT / "analysis/cases/openings").glob("*.json")}
    probes["P01"] = P01
    names = a.cases or sorted(probes)
    rows = []
    for cid in names:
        p = probes[cid]
        res = p.get("result", p)
        out = [simulate(Agent, cases[cid], p["threads"], res["c_open"], res["c_best"], r) for r in (0.30, 0.10)]
        rows.append((cid, out))
        print(f"{cid}  responsive {out[0][0]:.2f} ({out[0][1]}, {out[0][2]} msgs)   stubborn {out[1][0]:.2f} ({out[1][1]}, {out[1][2]} msgs)")
    mean = lambda i: sum(o[i][0] for _, o in rows) / len(rows)
    print(f"MEAN responsive {mean(0):.3f}   stubborn {mean(1):.3f}   (n={len(rows)})")


if __name__ == "__main__":
    main()
