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
    # trial run with the real model writing (LLM_* from the environment / .env), every e-mail printed:
    set -a; . ./.env; set +a; .venv/bin/python ../../src/eval/offline_eval.py --llm --show --only stubborn P05
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


LEAD_PREMIUM = -0.158  # EUR/unit per day of lead time, measured in both live P10 games (noidea.learn)


def _pkg(t):
    parts = [f"a price of €{t['unit_price']:.2f} per unit"]
    if t.get("payment_days") is not None:
        parts.append(f"Zahlungsziel {t['payment_days']} days net")
    if t.get("lead_time_days") is not None:
        parts.append(f"Lieferzeit {t['lead_time_days']} days")
    if t.get("volume_per_year") is not None:
        parts.append(f"a volume of {t['volume_per_year']} pcs per year")
    if t.get("contract_months") is not None:
        parts.append(f"a contract term of {t['contract_months']} months")
    return ", ".join(parts)


def arena_body(case, reply, events):
    """Supplier e-mail in the arena's template (datasets/F_supplier_emails.jsonl), so the agent's package
    parser, learner and model reader get exercised offline. Where lead time is negotiable and our offer asks
    for less than its opening lead, it adds an alternative at its opening lead priced with LEAD_PREMIUM."""
    t = reply["terms"]
    lines = ["Dear Sir or Madam,", "", "Thank you for your proposal."]
    if reply["status"] == "final_offer":
        lines.append("This is our letztes Angebot. Please decide.")
    lines.append(f"Our offer is {_pkg(t)}.")
    first = next((m for m in events if m.get("from") != "buyer" and m.get("term_sheets")), None)
    std_lead = first["term_sheets"][0]["terms"].get("lead_time_days") if first else None
    if "lead_time_days" in case["negotiable"] and std_lead and (t.get("lead_time_days") or 0) < std_lead:
        alt = {**t, "lead_time_days": std_lead,
               "unit_price": round(t["unit_price"] + LEAD_PREMIUM * (std_lead - t["lead_time_days"]), 2)}
        lines.append(f"A reduction in lead time to {t['lead_time_days']} days is difficult for our capacity.")
        lines.append(f"Alternatively, by maintaining the lead time at {std_lead} days: {_pkg(alt)}.")
    lines.append("Which volume can you commit to?")
    return "\n".join(lines + ["", "Mit freundlichen Grüßen"])


def simulate(Agent, case, opening, c_open, c_best, r, max_rounds=10, complete=None, show=False):
    threads = {sid: [dict(m) for m in ms] for sid, ms in opening.items()}
    agent, n = Agent(complete), {sid: 0 for sid in threads}
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
        if show and not act:
            print(f"\n--- {case['case_id']} msg {sum(n.values())} -> {sid} | sheets "
                  f"{[{k: v for k, v in t['terms'].items() if k in case['negotiable']} for t in msg.get("term_sheets", [])]}")
            print("    " + msg["body"].replace("\n", "\n    "))
        if events[-1].get("status") == "final_offer":  # pushing after its last word: it walks (P07 v1.3 live)
            threads[sid].append({"from": sid, "status": "walked_away", "body": ""})
            others = [s for s in threads if threads[s][-1].get("status") not in ("walked_away",)]
            if not others:
                c_alt = agent.c_alt
                return (0.0 if c_alt == math.inf else max(0.0, (c_open - c_alt) / (c_open - c_best))), "walked", sum(n.values())
            continue
        if not msg.get("term_sheets"):  # a note without a price (api.md: answered, the quote stands) - it repeats its quote
            continue
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
                   {"from": f"sales@{sid}", "status": reply["status"], "body": arena_body(case, reply, events),
                    "term_sheets": [{"term_sheet_id": f"offer:{sid.split(':')[-1]}-{n[sid]}", "terms": reply["terms"]}]}]
    return 0.0, "timeout", sum(n.values())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cases", nargs="*")
    ap.add_argument("--agent-file")
    ap.add_argument("--llm", action="store_true", help="the configured LLM writes the openings (LLM_* env)")
    ap.add_argument("--show", action="store_true", help="print every e-mail and its term sheets")
    ap.add_argument("--only", choices=["responsive", "stubborn"], help="one simulated supplier type")
    a = ap.parse_args()
    logging.basicConfig(level=logging.WARNING)
    Agent = load_agent(a.agent_file)
    complete = None
    if a.llm:
        import time
        from arena_kit.agents.llm import llm_from_env
        raw, calls = llm_from_env(), []
        def complete(system, user):
            t = time.time()
            try:
                return raw(system, user)
            finally:
                calls.append(time.time() - t)
    cases = {c["case_id"][5:]: c for c in json.loads((ROOT / "datasets/cases_practice.json").read_text())}
    probes = {f.stem: json.loads(f.read_text()) for f in (ROOT / "analysis/cases/openings").glob("*.json")}
    probes["P01"] = P01
    names = a.cases or sorted(probes)
    rows = []
    for cid in names:
        p = probes[cid]
        res = p.get("result", p)
        rs = {"responsive": (0.30,), "stubborn": (0.10,)}.get(a.only, (0.30, 0.10))
        out = [simulate(Agent, cases[cid], p["threads"], res["c_open"], res["c_best"], r, complete=complete, show=a.show)
               for r in rs]
        out = out if len(out) == 2 else out * 2
        rows.append((cid, out))
        print(f"{cid}  responsive {out[0][0]:.2f} ({out[0][1]}, {out[0][2]} msgs)   stubborn {out[1][0]:.2f} ({out[1][1]}, {out[1][2]} msgs)")
    mean = lambda i: sum(o[i][0] for _, o in rows) / len(rows)
    print(f"MEAN responsive {mean(0):.3f}   stubborn {mean(1):.3f}   (n={len(rows)})")
    if complete:
        print(f"LLM calls {len(calls)}, mean {sum(calls) / max(1, len(calls)):.1f}s, max {max(calls, default=0):.1f}s")


if __name__ == "__main__":
    main()
