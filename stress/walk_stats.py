"""Walk and patience rules measured from the archived real games (raw data only).

    python stress/walk_stats.py            -> prints the measured rates, writes stress/walk_stats.json

For every supplier thread of every archived game, in trace order:
  push        a buyer e-mail (not accept / walk / timeout) to a supplier whose standing status is final_offer
  no-move     a buyer e-mail with term sheets whose best value to the supplier is not above its previous best
  insult      a buyer e-mail whose best value is below the supplier's lowest value ever conceded in any archived
              game of that case by more than X % (X = 5, 10, 15, 20)
  contradicted  a reply that reports at least one `contradicted` claim
and what the supplier answered next (open / final_offer / agreed / walked_away). Values use the fitted value
function (stress/fitted_params.json) so sheets on different terms compare.
"""

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "tacto" / "starter-kit"))
sys.path.insert(0, str(HERE))

from calibrate import CASES, FACTS, base_params, load_games  # noqa: E402
from sim_supplier import Session, SimSupplier  # noqa: E402

FIT = json.loads((HERE / "fitted_params.json").read_text())


def supplier_model(case, sid):
    hp = dict(base_params(case, sid))
    hp.update(FIT[sid])
    hp["archetype"] = "fit"
    return SimSupplier(case, sid, hp, Session(case, FACTS), 0)


def main():
    games = load_games()
    models = {}
    lowest = defaultdict(lambda: 9.0)  # (case, sid) -> lowest conceded value / opening value
    for g in games:
        case = CASES[g["case"]]
        for t in g["trace"]:
            m, sid = t["move"], t["actor"]
            if sid == "buyer" or not m.get("terms") or m.get("terms", {}).get("unit_price") is None or t["round"] == 0:
                continue
            key = (g["case"], sid)
            if key not in models:
                models[key] = supplier_model(case, sid)
            s = models[key]
            lowest[key] = min(lowest[key], s.value(s.full(m["terms"])) / s.v_open)
    out = {"push": Counter(), "push_detail": [], "nomove": Counter(), "nomove_streak": Counter(), "insult": defaultdict(Counter),
           "contradicted": Counter(), "open_walks": [], "threads": 0, "threads_by_kind": Counter(), "replies": Counter()}
    for g in games:
        case = CASES[g["case"]]
        rfq = len(case["suppliers"]) > 1
        kind = "rfq" if rfq else "single"
        status, prev_best, streak, pending = {}, {}, Counter(), {}
        seen_threads = set()
        for t in g["trace"]:
            m = t["move"]
            if t["actor"] == "buyer":
                sid = m.get("supplier_id")
                if m.get("type") != "message" or (g["case"], sid) not in models:
                    pending[sid] = None
                    continue
                s = models[(g["case"], sid)]
                sheets = [ts.get("terms") for ts in (m.get("term_sheets") or []) if ts.get("terms")]
                vb = max((s.value(s.full(x)) / s.v_open for x in sheets), default=None)
                info = {"vb": vb, "status_before": status.get(sid, "open"), "nomove": False}
                if vb is not None and sid in prev_best and vb <= prev_best[sid] + 1e-9 and status.get(sid, "open") == "open":
                    info["nomove"] = True
                if vb is not None:
                    prev_best[sid] = max(prev_best.get(sid, -1), vb)
                pending[sid] = info
                continue
            sid = t["actor"]
            if t["round"] == 0:
                status[sid] = m.get("status")
                if (g["game"], sid) not in seen_threads:
                    seen_threads.add((g["game"], sid))
                    out["threads"] += 1
                    out["threads_by_kind"][kind] += 1
                continue
            info = pending.pop(sid, None)
            new = m.get("status")
            out["replies"][kind] += 1
            if info:
                key = (g["case"], sid)
                if info["status_before"] == "final_offer":
                    s = models[key]
                    fin = info.get("final_v")
                    met = None
                    out["push"][(kind, new)] += 1
                    out["push_detail"].append({"game": g["game"], "case": g["case"], "sid": sid, "kind": kind, "next": new,
                                               "buyer_v": info["vb"], "final_v": final_v.get((g["game"], sid))})
                if info["nomove"]:
                    streak[sid] += 1
                    out["nomove"][(kind, new)] += 1
                    out["nomove_streak"][(kind, streak[sid], new)] += 1
                elif info["vb"] is not None:
                    streak[sid] = 0
                if info["vb"] is not None and info["status_before"] == "open":
                    for x in (5, 10, 15, 20):
                        if info["vb"] < lowest[key] * (1 - x / 100):
                            out["insult"][x][(kind, new)] += 1
                if new == "walked_away" and info["status_before"] == "open":
                    out["open_walks"].append({"game": g["game"], "case": g["case"], "sid": sid, "round": t["round"],
                                              "buyer_v": info["vb"], "lowest_v": lowest[key], "nomove": info["nomove"]})
            if any(c.get("result") == "contradicted" for c in m.get("claim_results") or []):
                out["contradicted"][new] += 1
            if new == "final_offer" and m.get("terms"):
                s = models[(g["case"], sid)]
                final_v[(g["game"], sid)] = s.value(s.full(m["terms"])) / s.v_open
            status[sid] = new
    # pushes: did the buyer meet the final?
    met = Counter()
    for p in out["push_detail"]:
        if p["buyer_v"] is None or p["final_v"] is None:
            met[(p["kind"], "no sheet", p["next"])] += 1
        else:
            met[(p["kind"], "meets final" if p["buyer_v"] >= p["final_v"] - 1e-6 else f"below final", p["next"])] += 1
            p["below_pct"] = round((1 - p["buyer_v"] / p["final_v"]) * 100, 2)
    res = {
        "threads": out["threads"], "threads_by_kind": dict(out["threads_by_kind"]), "replies": dict(out["replies"]),
        "push": {f"{k[0]}->{k[1]}": v for k, v in sorted(out["push"].items())},
        "push_vs_final": {" / ".join(k): v for k, v in sorted(met.items())},
        "push_walks": [p for p in out["push_detail"] if p["next"] == "walked_away"],
        "push_below_final_pct": sorted((p["kind"], p.get("below_pct"), p["next"]) for p in out["push_detail"] if p.get("below_pct") is not None),
        "nomove_next": {f"{k[0]}->{k[1]}": v for k, v in sorted(out["nomove"].items())},
        "nomove_streak": {f"{k[0]} streak {k[1]} -> {k[2]}": v for k, v in sorted(out["nomove_streak"].items())},
        "insult_next": {f"{x}%": {f"{k[0]}->{k[1]}": v for k, v in sorted(c.items())} for x, c in out["insult"].items()},
        "contradicted_next": dict(out["contradicted"]),
        "open_walks": out["open_walks"],
    }
    (HERE / "walk_stats.json").write_text(json.dumps(res, indent=1))
    for k, v in res.items():
        print(k, json.dumps(v)[:900])


final_v = {}
if __name__ == "__main__":
    main()
