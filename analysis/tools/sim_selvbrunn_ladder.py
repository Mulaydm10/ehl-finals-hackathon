"""P03 (Selvbrunn, sup:70530) in NORMAL mode as the measured ladder - offline, no arena, no LLM.

    cd tacto/starter-kit && uv run python ../../analysis/tools/sim_selvbrunn_ladder.py [agent_file ...]

Rules, each from the 20 recorded P03 games (analysis/cases/P03_deep.md):
- committee (our e-mail names its pricing committee): EUR 433.08 @ 90 d, minus one cut per NEW verified kind it takes:
  should-cost 0.79, electronics PPI-C2611 falling window 0.48, our order price PATH (>= 2 POs, rising) 1.26, forecast
  fc:...@2026-09 0.14, copper 0.06, labour 0.02; its own quote "irrelevant"; OTD / ppm / QNs / a flat run 0.
  Other payment terms: EUR 0.049 a day (431.47 @ 60 d next to 432.94 @ 90 d).
- it counters at its line (never below it) and AGREES at our ask when a sheet of ours is at or above its line
  (fe4d8455, f8082c20: 430.81 agreed with the line at ~430.55);
- `final_offer` in its reply to our 5th message; agreed / final -> the agent's own accept rule.
- RIVAL scenario = what the 2025 benchmark quote (quote:7100051, EUR 429.18) is worth: 0 (shrugged / irrelevant), a cut
  in EUR, or "match" (its line goes to 429.18 @ 90 d).
Scores use the arena-exact cost (full cost 395.30, cash rate 6.1%: reproduces the live c_deal to the cent).
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
FACTS = json.loads((ROOT / "tacto/data/facts.json").read_text(encoding="utf-8"))
C_OPEN, C_BEST = 4246314.02, 3909043.10
STD = {"payment_days": 30, "contract_months": 12, "volume_per_year": 4580, "ppm_commitment": 350, "lead_time_days": 49,
       "incoterm": "DAP", "effective_date": "2027-01-01", "index_clause": None, "tooling_eur": 0}
EST = {"standard": STD, "interest_rate": 0.061, "full_cost": 395.30}
BASE90, PER_DAY, FINAL_AT = 433.08, 0.049, 5
CUT = {"should_cost": 0.79, "idx:PPI-C2611": 0.48, "path": 1.26, "forecast": 0.14, "idx:CU-NOTATION": 0.06,
       "idx:LCI-C": 0.02}


def score(t):
    return (C_OPEN - total_cost(CASE, complete_offer(CASE, t), STD, EST)) / (C_OPEN - C_BEST)


def kinds(refs):
    """Map the refs of one e-mail to the kinds the committee prices (one entry per kind)."""
    out, pos = {}, [r for r in refs if r.startswith("po:")]
    for r in refs:
        if r.startswith("cost:"):
            out["should_cost"] = "verified"
        elif r.startswith("fc:") and r.endswith("@2026-09"):
            out["forecast"] = "verified"
        elif r.startswith("idx:"):
            out[r.split("@")[0]] = "verified"
        elif r.startswith("quote:"):
            sup = FACTS.get(r, {}).get("supplier")
            out["rival" if sup and sup != "sup:70530" else "own_quote"] = "verified" if sup != "sup:70530" else "irrelevant"
    prices = [FACTS[p]["unit_price"] for p in sorted(pos, key=lambda p: FACTS[p]["date"])]
    if len(prices) >= 2 and prices[-1] > prices[0]:
        out["path"] = "verified"
    elif pos:
        out["flat_run"] = "verified"
    return out


def load(path):
    name = "arena_kit.agents._ladder_" + re.sub(r"\W", "_", Path(path).stem)
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod.NoIdeaAgent


def run(Agent, rival=0.0, verbose=True):
    threads = {sid: [dict(m) for m in ms] for sid, ms in PROBE["threads"].items()}
    sid = next(iter(threads))
    events, agent, taken, committee, n = threads[sid], Agent(None), set(), False, 0
    while n < 10:
        msg = agent.decide(CASE, threads)["message"]
        if (act := msg.get("action")):
            if act["type"] == "walk_away":
                return 0.0, "walk", n
            sheet = next(x for x in events[-1]["term_sheets"] if x["term_sheet_id"] == act.get("term_sheet_id"))
            return score(sheet["terms"]), f"deal {sheet['terms']['unit_price']} @ {sheet['terms']['payment_days']} d", n
        n += 1
        if events[-1].get("status") == "final_offer":
            return 0.0, "pushed after final_offer", n
        committee = committee or bool(re.search(r"(?i)committee", msg.get("body") or ""))
        ks = kinds(msg.get("refs") or [])
        results = [{"index": i, "result": v} for i, v in enumerate(ks.values())]
        cuts = []
        for k in ks:
            if k not in taken:
                taken.add(k)
                cuts.append(CUT.get(k, 0.0) if k != "rival" else (0.0 if rival == "match" else rival))
        line90 = round(BASE90 - sum(CUT.get(k, 0.0) for k in taken)
                       - (rival if "rival" in taken and rival != "match" else 0.0), 2)
        if "rival" in taken and rival == "match":
            line90 = min(line90, 429.18)
        sheets = [complete_offer(CASE, x["terms"]) for x in msg["term_sheets"]]
        at = lambda d: round(line90 - PER_DAY * (90 - d), 2)  # noqa: E731
        ok = [t for t in sheets if t["unit_price"] >= at(t["payment_days"]) - 1e-9]
        if ok:  # it agrees at OUR price (the best sheet for it)
            t, status = max(ok, key=lambda t: t["unit_price"] - at(t["payment_days"])), "agreed"
        else:
            t = complete_offer(CASE, {**sheets[0], "unit_price": at(90), "payment_days": 90})
            status = "final_offer" if n >= FINAL_AT else "open"
        if verbose:
            print(f"   msg {n}: ours {[(x['unit_price'], x['payment_days']) for x in sheets]} refs {msg.get('refs')}"
                  f" -> {status} {t['unit_price']} @ {t['payment_days']} d (score {score(t):.5f})")
        body = ("We have reviewed your offer and can adjust our Angebot as follows. "
                + " ".join(f"We checked the {k} data you cited; it holds and we took it into account." for k in ks)
                + " Our management has frozen all price reductions until December 2027. We can talk about the terms"
                  " instead - payment, volume or contract length.")
        events += [{**msg, "from": "buyer"},
                   {"from": f"sales@{sid}", "status": status, "body": body, "claim_results": results,
                    "term_sheets": [{"term_sheet_id": f"offer:{sid}-{n}", "terms": t}]}]
    return 0.0, "ran out of messages", n


if __name__ == "__main__":
    paths = sys.argv[1:] or [str(ROOT / "analysis/agent_variants/noidea_p03.py")]
    for path in paths:
        for rival in (0.0, 0.30, 0.60, "match"):
            print(f"== {Path(path).name}  rival quote worth: {rival}")
            s, end, n = run(load(path), rival)
            print(f"   => score {s:.5f}  {end}  ({n} messages)  {'BEATS' if s > 0.97350 else 'below'} '+=' 0.97350")
