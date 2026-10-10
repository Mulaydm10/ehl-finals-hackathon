"""One practice case's engine profile from every archived game (offline, no quota).

    cd tacto/starter-kit && uv run python ../../analysis/tools/case_engine.py P01 [--rate 0.08]

Prints: each game's price path (cash value to the supplier) with its status, the tally of the supplier's fixed
reactions per data kind, the behaviour signals in its reasons (mirror, full authority, committee, wants data, hedge,
final / walk), every checkable fact not yet cited, and the price needed for target scores on the best deal's terms
(calibrated supplier from analysis/central/calibration.json, or one fitted from the relationship charge of a real deal).
Feeds analysis/cases/<case>_engine.md and analysis/central/ENGINES.md.
"""

import argparse
import collections
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tacto/starter-kit"))
sys.path.insert(0, str(ROOT / "analysis/tools"))
sys.path.insert(0, str(ROOT / "analysis/agent_variants"))
from arena_kit.cost import supplier_value, total_cost  # noqa: E402
from engine_dump import load_games  # noqa: E402

KINDS = {"volume change": "volume", "price history": "po_prices", "index change": "index", "rival quote": "rival_quote",
         "should cost": "should_cost", "quality record": "quality", "delivery record": "otd", "notice period": "notice"}
CHECKED = re.compile(r"(?i)we checked the (.+?) data you cited; it holds(,| and)(?: but)? (it does not change|we took it)")
SIGNALS = {
    "mirror": r"(?i)in response to your (step|movement|move|adjustment)|your (step|movement)|meet you|towards our position|"
              r"reciprocat|matching your",
    "full_authority": r"(?i)full authority|within my (remit|authority)|delegated authority",
    "committee": r"(?i)committee|management (has|approved|authoris|review)|escalat|my (boss|director)|managing director",
    "wants_data": r"(?i)which figures is that based on|send us the data|verifiable data|verified data|supporting data",
    "no_new_data_final": r"(?i)no new (verified|verifiable) data|without (new|additional) (verified )?data|lacks new",
    "hedge": r"(?i)not our reality|covered at fixed prices|hedg",
    "confirm_case": r"(?i)confirm our case",
    "padding": r"(?i)lot of material",
    "duplicate": r"(?i)duplicate|already (taken|been|factored|accounted)",
    "irrelevant": r"(?i)irrelevant|outdated",
    "fair_point": r"(?i)fair point|did not know that",
    "price_fixed": r"(?i)frozen|price list applies|cannot (go|move) (any )?further|maximum (possible )?concession|best possible price",
    "wants_volume": r"(?i)which volume can you commit|binding higher volume",
    "lead_premium": r"(?i)lead time|lieferzeit|capacity",
    "closed_book": r"(?i)calculation stays internal|do not share|property",
}


def est_for(case_id, sid, case, games, rate):
    cal = json.loads((ROOT / "analysis/central/calibration.json").read_text(encoding="utf-8")).get(case_id, {}).get(sid)
    if cal:
        return {"full_cost": cal["full_cost"], "interest_rate": cal["interest_rate"], "source": "calibration.json"}
    if case["buyer"]["category_goal"] not in ("stabilise", "secure_supply"):
        return None
    for g in games.values():  # fit full cost on one real deal's relationship charge at `rate`
        r = g.get("result") or {}
        if r.get("deal") and r.get("supplier_id") == sid and (r.get("cost_breakdown") or {}).get("relationship", 0) > 1:
            std = std_terms(case, sid, g)
            lo, hi = r["terms"]["unit_price"] * 0.5, r["terms"]["unit_price"] * 1.3
            for _ in range(60):
                mid = (lo + hi) / 2
                c = total_cost(case, r["terms"], std, {"standard": std, "interest_rate": rate, "full_cost": mid})
                lo, hi = (mid, hi) if c < r["c_deal"] else (lo, mid)
            return {"full_cost": round(lo, 3), "interest_rate": rate, "source": f"fit on {r.get('offer_id')} at rate {rate}"}
    return None


def std_terms(case, sid, game):
    d = json.loads((ROOT / "datasets/A_dossiers.json").read_text(encoding="utf-8")).get(sid, {})
    std = {k: v for k, v in (d.get("standard_terms") or {}).items() if v is not None}
    op = (game.get("opening") or {}).get(sid) or {}
    std.update({k: v for k, v in (op.get("terms") or {}).items() if k != "unit_price"})
    std.setdefault("payment_days", case["buyer"]["reference_payment_days"])
    return std


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("case")
    ap.add_argument("--rate", type=float, default=0.08)
    a = ap.parse_args()
    case_id = f"case:{a.case}"
    case = {c["case_id"]: c for c in json.loads((ROOT / "datasets/cases_practice.json").read_text(encoding="utf-8"))}[case_id]
    games = load_games(case_id)
    print(f"# {case_id} {case['type']} {case['buyer']['category_goal']} suppliers {case['suppliers']} negotiable {case['negotiable']}")
    tally = collections.defaultdict(collections.Counter)
    sig = collections.Counter()
    finals, cited_ids = collections.Counter(), set()
    c_open = c_best = None
    best = None
    for sid_, g in sorted(games.items(), key=lambda x: (x[1].get("result") or {}).get("score") or 0):
        r = g.get("result") or {}
        c_open, c_best = r.get("c_open") or c_open, r.get("c_best") or c_best
        if r.get("deal") and (best is None or r["score"] > best[1]["score"]):
            best = (sid_, r)
        path, our = [], 0
        for t in r.get("trace") or []:
            m = t.get("move") or {}
            if t.get("actor") == "buyer":
                our += 1
                cited_ids |= {i for c in (m.get("interpreted") or {}).get("claims") or [] for i in c.get("refs") or []}
                cited_ids |= set(m.get("refs") or [])
                continue
            sid = t["actor"]
            std = std_terms(case, sid, g)
            prim = m.get("terms") or {}
            v = supplier_value(case, prim, {"standard": std, "interest_rate": a.rate}) if prim.get("unit_price") else None
            tag = {"open": "", "final_offer": "F", "agreed": "A", "walked_away": "W", "no_bid": "N"}.get(m.get("status"), "?")
            path.append(f"{sid[-5:]}:{'-' if v is None else round(v, 3)}{tag}")
            if m.get("status") == "final_offer":
                finals[our] += 1
            for x in t.get("reasons") or []:
                if (mm := CHECKED.search(x)):
                    k = KINDS.get(mm.group(1).lower(), mm.group(1).lower())
                    tally[k]["taken" if "took" in mm.group(3) else "no_change"] += 1
                for s, rx in SIGNALS.items():
                    if re.search(rx, x):
                        sig[s] += 1
        print(f"  {sid_} score {r.get('score') if r.get('score') is None else round(r['score'], 3)} {g.get('end_reason')} | " + " ".join(path))
    print(f"  final_offer at our msg #: {dict(finals)}   c_open {c_open} c_best {c_best}")
    print("  data reactions:", {k: dict(v) for k, v in tally.items()})
    print("  signals (count of reason lines):", dict(sig.most_common()))
    if not best:
        return
    sid, r = best
    g = games[sid]
    std = std_terms(case, r["supplier_id"], g)
    est = est_for(case_id, r["supplier_id"], case, games, a.rate)
    if est:
        est = {**est, "standard": std}
    base = dict(r["terms"])  # full closing terms (standard ppm etc. included)
    print(f"  model check: C {total_cost(case, base, std, est):.2f} vs real {r['c_deal']:.2f}")
    print(f"  best deal {sid}: { {k: v for k, v in base.items() if k in case['negotiable']} } score {r['score']:.3f}; supplier estimate {est and {k: est[k] for k in ('full_cost', 'interest_rate', 'source')}}")

    def score(p, terms=base):
        c = total_cost(case, {**terms, "unit_price": p}, std, est)
        return (c_open - c) / (c_open - c_best)
    p0 = base["unit_price"]
    grid = [p0 * (0.80 + i * 0.0005) for i in range(500)]
    for target in (0.75, 0.8, 0.9, 1.0):
        ok = [p for p in grid if score(p) >= target]
        print(f"  price for {target} on the best deal's terms: {max(ok):.3f} ({(max(ok) / p0 - 1) * 100:+.2f}% vs deal)" if ok
              else f"  price for {target}: unreachable on these terms")
    print("  1% price =", round(score(p0 * 0.99) - score(p0), 3), "score")
    # uncited facts
    import central
    facts = json.loads((ROOT / "tacto/data/facts.json").read_text(encoding="utf-8"))
    d = json.loads((ROOT / "datasets/A_dossiers.json").read_text(encoding="utf-8"))
    print("  cited IDs so far:", sorted(cited_ids)[:40])
    for s in case["suppliers"]:
        dd = d.get(s, {})
        parts = [p for p in dd.get("parts", []) if p["part"] in case["parts"]]
        drivers = {x["series"]: x["weight"] for p in parts for x in p.get("cost_drivers", [])}
        print(f"  -- {s} {dd.get('name')} motives {list(dd.get('motives', {}))} drivers {drivers}")
        for c in central.falling_window_claims(case, drivers, per_series=1, min_fall=-0.2):
            new = not (set(c["ids"]) & cited_ids)
            print(f"     falling {c['series']} w {c['weight']} {c['figure']:+.2f}% {c['ids']} {'NEW' if new else 'cited'}")
        for part in case["parts"]:
            pid = part.split(":")[1]
            fcs = sorted(k for k in facts if k.startswith(f"fc:{pid}@"))
            if fcs:
                print(f"     latest fc {fcs[-1]} {facts[fcs[-1]].get('change_pct')} {'cited' if fcs[-1] in cited_ids else 'NEW'}")
            if (cost := facts.get(f"cost:{pid}")):
                op = ((g.get("opening") or {}).get(s) or {}).get("terms", {}).get("unit_price")
                print(f"     should-cost {cost.get('unit_cost')} vs its opening quote {op} {'cited' if f'cost:{pid}' in cited_ids else 'NEW'}")
            pos = sorted((k, v["unit_price"]) for k, v in facts.items() if k.startswith("po:") and v.get("part") == part and v.get("supplier") == s)
            if pos:
                print(f"     po history ({len(pos)}): {[p for _, p in pos[-8:]]} last ids {[k for k, _ in pos[-3:]]} "
                      f"{'cited' if any(k in cited_ids for k, _ in pos) else 'NEW'}")
            qs = [(k, v.get("unit_price"), v.get("date")) for k, v in facts.items() if k.startswith("quote:") and v.get("part") == part]
            print(f"     quotes for the part: {qs}")
            qn = [k for k, v in facts.items() if k.startswith("qn:") and v.get("supplier") == s and v.get("part") == part
                  and (v.get("date") or "") >= "2025-10-01"]
            if qn:
                print(f"     QNs last 12 m on this part: {len(qn)} {qn[:4]} {'cited' if set(qn) & cited_ids else 'NEW'}")
        scs = sorted(k for k in facts if k.startswith(f"sc:{s.split(':')[1]}@"))
        if scs:
            f = facts[scs[-1]]
            print(f"     scorecard {scs[-1]} otd {f.get('otd_pct')} ppm {f.get('ppm')} {f.get('colour')}")
        print(f"     motives detail: { {m: v.get('lever') for m, v in dd.get('motives', {}).items()} }")


if __name__ == "__main__":
    main()
