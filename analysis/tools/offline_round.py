"""One offline negotiation with an agent variant: transcript, score, and the score WITH the relationship charge
under full-cost scenarios (the simulators ignore it; stabilise / secure_supply cases pay it). No arena calls.

    cd tacto/starter-kit && uv run python ../../analysis/tools/offline_round.py P03 ../../analysis/agent_variants/noidea_neel.py [--llm] [--fc 395,400,403.2]

Supplier: sim_floorstop (live-P04-calibrated: r 0.54, stop 0.15% above its floor, patience 1).
Saves analysis/offline_runs/<case>_<variant>_<n>.json.
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
from sim_floorstop import load_agent, run  # noqa: E402

from arena_kit.cost import cost_breakdown, total_cost  # noqa: E402
from arena_kit.docs import standard_terms  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("case")
    ap.add_argument("agent_file")
    ap.add_argument("--llm", action="store_true")
    ap.add_argument("--fc", default="", help="full-cost scenarios for the relationship charge, e.g. 395,403.2")
    ap.add_argument("--rate", type=float, default=0.08)
    a = ap.parse_args()
    logging.disable(logging.CRITICAL)
    complete = None
    if a.llm:
        for line in (ROOT / "tacto/starter-kit/.env.openai").read_text().splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip()
        from arena_kit.agents.llm import llm_from_env
        complete = llm_from_env()
    Agent = load_agent(a.agent_file)
    sent = []
    orig = Agent.message

    def message(self, *args, **kw):
        m = orig(self, *args, **kw)
        sent.append({k: m["message"].get(k) for k in ("body", "refs")} | {
            "sheets": [t["terms"] for t in m["message"].get("term_sheets") or []]})
        return m

    Agent.message = message
    case = next(c for c in json.loads((ROOT / "datasets/cases_practice.json").read_text(encoding="utf-8"))
                if c["case_id"] == f"case:{a.case}")
    pr = json.loads((ROOT / "analysis/cases/openings" / f"{a.case}.json").read_text(encoding="utf-8"))
    r = pr["result"]
    score, end, n = run(Agent, case, pr["threads"], r["c_open"], r["c_best"], complete=complete, verbose=True)
    print(f"\nRESULT {a.case}: sim score {score:.2f} | {end} | {n} rounds")
    out = {"case": a.case, "variant": Path(a.agent_file).stem, "sim_score": score, "end": end, "rounds": n,
           "emails": sent, "relationship": {}}
    if a.fc and end.startswith("deal"):
        terms = eval(end[5:])  # noqa: S307 - our own repr of a dict
        sid = next(iter(pr["threads"]))
        std = standard_terms(pr["threads"][sid])
        base = {**pr["threads"][sid][0]["term_sheets"][0]["terms"], **std}
        for fc in [float(x) for x in a.fc.split(",")]:
            sup = {"standard": base, "interest_rate": a.rate, "full_cost": fc}
            C = total_cost(case, terms, std, sup)
            rel = cost_breakdown(case, terms, std, sup)["relationship"]
            s2 = (r["c_open"] - C) / (r["c_open"] - r["c_best"])
            out["relationship"][fc] = {"relationship_eur": rel, "score": s2}
            print(f"  if its full cost is EUR {fc}: relationship charge EUR {rel:,.0f} -> score {s2:.2f}")
    d = ROOT / "analysis/offline_runs"
    k = len(list(d.glob(f"{a.case}_{out['variant']}_*.json"))) + 1
    (d / f"{a.case}_{out['variant']}_{k}.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    for i, e in enumerate(sent, 1):
        print(f"\n--- e-mail {i} refs {e['refs']}\n{e['body']}")


if __name__ == "__main__":
    main()
