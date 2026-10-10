"""Audit every saved arena negotiation (tools/replays/raw/*.json): where points were won and lost. Offline.

    cd tacto/starter-kit && uv run python ../../analysis/tools/run_audit.py [--house]   (--house: read /v1/live once)

Per session: score vs the house agent, round-by-round value of the supplier's best standing sheet (as a score),
what our first sheets were worth, claim results, supplier phrases that signal a mistake, timeouts, and whether we
accepted the best sheet / prose offer available. Then pattern counts across all sessions.
"""

import collections
import glob
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tacto/starter-kit"))
from arena_kit.cost import complete_offer, total_cost  # noqa: E402

PHRASES = {
    "rising_data_backfired": r"confirm[s]? our case|that driver rose|reflect increasing",
    "padding": r"lot of material|already taken that .* into account|already been fully accounted",
    "asked_volume": r"which volume can you commit|binding higher volume",
    "asked_data": r"which figures is that based on|send us the data|documentation supporting|data supporting",
    "refused_breakdown": r"do not share|cannot be shared|remain(s)? (strictly )?confidential",
    "authority_limit": r"authority|committee|approval|guidelines|frozen|strictly fixed|absolute (minimum|limit)",
    "infeasible": r"technically unfeasible|incompatible|cannot (meet|deliver)|premium",
    "prose_alternative": r"alternatively",
}


def load_cases():
    return {c["case_id"]: c for c in json.loads((ROOT / "datasets/cases_practice.json").read_text(encoding="utf-8"))}


def main(house):
    cases = load_cases()
    pats = collections.Counter()
    by_case = collections.defaultdict(list)
    for f in sorted(glob.glob(str(ROOT / "tools/replays/raw/*.json"))):
        s = json.loads(Path(f).read_text(encoding="utf-8"))
        r = s.get("result") or {}
        tm = s.get("thread_messages") or {}
        msgs = [m for th in tm.values() for m in th.get("messages", [])]
        if not any(m.get("from") == "buyer" and m.get("term_sheets") for m in msgs):
            continue  # probes / no negotiation
        case = cases[s["case_id"]]
        span = r["c_open"] - r["c_best"]
        sc = lambda t: (r["c_open"] - total_cost(case, complete_offer(case, t) | {k: v for k, v in t.items()})) / span  # noqa: E731
        sup_path, our_first, worse_than_standing, timeouts = [], None, 0, 0
        for sid, th in tm.items():
            timeouts += len(th.get("timeouts") or [])
            standing_c = None
            for m in th.get("messages", []):
                sheets = [x["terms"] for x in m.get("term_sheets") or []]
                if not sheets:
                    continue
                if m.get("from") == "buyer":
                    vals = [sc(t) for t in sheets]
                    if our_first is None:
                        our_first = max(vals)
                    if standing_c is not None and min(vals) < standing_c - 1e-6:
                        worse_than_standing += 1  # a sheet of ours scoring below what already stood
                else:
                    best = max(sc(t) for t in sheets)
                    standing_c = best
                    sup_path.append(round(best, 2))
        text = " ".join((m.get("body") or "") for m in msgs if m.get("from") != "buyer")
        reasons = " ".join(" ".join(t.get("reasons") or []) for t in r.get("trace") or [])
        hits = [k for k, p in PHRASES.items() if re.search(p, text + " " + reasons, re.I)]
        claims = collections.Counter(c["result"] for m in msgs for c in m.get("claim_results") or [])
        last_status = next((m.get("status") for m in reversed(msgs) if m.get("from") != "buyer" and m.get("status")
                            not in ("agreed",)), None)
        peak = max(sup_path) if sup_path else None
        score = r.get("score") or 0.0
        left_on_table = round(peak - score, 2) if peak is not None and r.get("deal") else None
        row = {"sid": s["session_id"], "score": round(score, 3), "end": s.get("end_reason"), "path": sup_path[1:],
               "first_ours": round(our_first, 2) if our_first is not None else None, "peak": peak,
               "left": left_on_table, "below_standing": worse_than_standing, "timeouts": timeouts,
               "claims": dict(claims), "signals": hits, "last": last_status}
        by_case[s["case_id"]].append(row)
        pats.update(hits)
        if left_on_table and left_on_table > 0.02:
            pats["accepted_below_peak"] += 1
        if worse_than_standing:
            pats["offered_below_standing"] += 1
        if timeouts:
            pats["timeouts"] += 1
        if s.get("end_reason") != "accepted":
            pats[f"end_{s.get('end_reason')}"] += 1
        if our_first is not None and our_first > 1.0:
            pats["first_sheet_beyond_best"] += 1
    n = sum(len(v) for v in by_case.values())
    for cid in sorted(by_case):
        h = house.get(cid)
        print(f"\n### {cid} ({cases[cid]['type']}, {cases[cid]['buyer']['category_goal']}) house {h if h is not None else '?'}")
        for x in sorted(by_case[cid], key=lambda x: -x["score"]):
            print(f"  {x['sid']} score {x['score']:.3f} {x['end']:<11} last={x['last']} supplier path {x['path']} "
                  f"(peak {x['peak']}, left {x['left']}) first-ours {x['first_ours']} below-standing {x['below_standing']} "
                  f"timeouts {x['timeouts']} claims {x['claims']} signals {x['signals']}")
    print(f"\n### patterns across {n} negotiations")
    for k, v in pats.most_common():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    house = {}
    if "--house" in sys.argv:
        import httpx
        house = {b["case_id"]: round(b["house"], 3) for b in httpx.get("https://arena.tacto.ai/v1/live", timeout=30).json()["bots"]
                 if b.get("house") is not None}
    main(house)
