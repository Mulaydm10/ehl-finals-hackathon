"""What makes a supplier send final_offer? Every reply of every archived single-supplier game (offline, no quota).

    cd tacto/starter-kit && uv run python ../../analysis/tools/final_trigger.py [P08 ...] [--rows] [--json out.json]

One row per supplier reply to our message k: its status, our step at k (value of our best sheet for it, at its cash rate
and standard terms; % of price and share of the gap it left open before k), its own step at k-1 and at k, the gap left
after our message, new verified facts we cited, validity days. Then: where the final fell per case, and how well simple
rules (round count / our step / gap / its step) separate final from open replies. Feeds analysis/central/FINAL_TRIGGER.md.
"""

import argparse
import collections
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tacto/starter-kit"))
sys.path.insert(0, str(ROOT / "analysis/tools"))
from arena_kit.cost import supplier_value  # noqa: E402
from case_engine import std_terms  # noqa: E402
from engine_dump import load_games  # noqa: E402

CASES = ["P01", "P02", "P03", "P04", "P07", "P08", "P10", "P11", "P18"]  # P05 is an RFQ (auction): no single thread
RATES = {"P02": 0.066, "P03": 0.061}  # calibration.json; the rest 8%


def rows_for(case_id, rate):
    case = {c["case_id"]: c for c in json.loads((ROOT / "datasets/cases_practice.json").read_text(encoding="utf-8"))}[case_id]
    out = []
    for sid, g in sorted(load_games(case_id).items(), key=lambda x: x[1].get("created_at") or 0):
        r = g.get("result") or {}
        trace = r.get("trace") or []
        sup_ids = {t["actor"] for t in trace if t.get("actor") != "buyer"}
        if len(sup_ids) != 1:
            continue
        sup = sup_ids.pop()
        est = {"standard": std_terms(case, sup, g), "interest_rate": rate}

        def val(terms):
            return supplier_value(case, terms, est) if (terms or {}).get("unit_price") else None
        k, ours, its, ask, facts = 0, [], [], None, 0
        for t in trace:
            m = t.get("move") or {}
            if t.get("actor") == "buyer":
                if m.get("type") != "message":
                    continue  # accept / walk
                k += 1
                vs = [val(ts.get("terms")) for ts in m.get("term_sheets") or []]
                vs = [v for v in vs if v is not None]
                ask = max(vs) if vs else (ours[-1] if ours else None)
                ours.append(ask)
                continue
            v = val(m.get("terms"))
            res = [c.get("result") for c in m.get("claim_results") or []]
            facts = res.count("verified")
            if t.get("round", 0) == 0 or k == 0:
                its.append(v)
                continue
            prev_its = its[-1] if its else None
            its.append(v)
            if None in (prev_its, ask, v):
                continue
            prev_ask = ours[-2] if len(ours) >= 2 else None
            gap_before = prev_its - prev_ask if prev_ask is not None else None
            our_step = ask - prev_ask if prev_ask is not None else None
            its_prev_step = its[-3] - its[-2] if len(its) >= 3 and None not in its[-3:-1] else None
            out.append({
                "case": case_id[5:], "session": sid[:8], "k": k, "status": m.get("status"),
                "its": round(v, 3), "ask": round(ask, 3),
                "our_step_pct": None if our_step is None else round(100 * our_step / prev_its, 2),
                "our_share": None if not gap_before else round(our_step / gap_before, 2),
                "gap_after_pct": round(100 * (prev_its - ask) / prev_its, 2),
                "gap_left_pct": round(100 * (v - ask) / v, 2),
                "its_step_pct": round(100 * (prev_its - v) / prev_its, 2),
                "its_prev_step_pct": None if its_prev_step is None else round(100 * its_prev_step / its[-3], 2),
                "verified": facts, "validity": (m.get("signals") or {}).get("validity_days"),
                "score": r.get("score"),
            })
    return out


def acc(rows, rule):
    """(hits, total, false finals, missed finals) of rule(row)->bool vs status == final_offer."""
    ok = ff = mf = 0
    for x in rows:
        p, y = rule(x), x["status"] == "final_offer"
        ok += p == y
        ff += p and not y
        mf += y and not p
    return ok, len(rows), ff, mf


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cases", nargs="*", default=CASES)
    ap.add_argument("--rows", action="store_true")
    ap.add_argument("--json")
    a = ap.parse_args()
    allrows = []
    for c in a.cases:
        allrows += rows_for(f"case:{c}", RATES.get(c, 0.08))
    if a.json:
        Path(a.json).write_text(json.dumps(allrows, indent=1), encoding="utf-8")
    if a.rows:
        for x in allrows:
            print(" ".join(f"{k}={v}" for k, v in x.items()))
    by = collections.defaultdict(list)
    for x in allrows:
        by[x["case"]].append(x)
    print("\ncase | games | final at our msg k (count) | open replies at that k | our step % at final k: final vs open")
    for c, rs in by.items():
        fk = collections.Counter(x["k"] for x in rs if x["status"] == "final_offer")
        games = len({x["session"] for x in rs})
        modal = fk.most_common(1)[0][0] if fk else None
        open_same = [x for x in rs if x["k"] == modal and x["status"] == "open"]
        f_steps = [x["our_step_pct"] for x in rs if x["k"] == modal and x["status"] == "final_offer"]
        o_steps = [x["our_step_pct"] for x in open_same]
        print(f"{c} | {games} | {dict(sorted(fk.items()))} | {len(open_same)} | {f_steps} vs {o_steps}")
    rules = {
        "k >= case's modal final k": None,
        "gap after our msg <= 3%": lambda x: x["gap_after_pct"] <= 3,
        "our share >= 0.3": lambda x: (x["our_share"] or 0) >= 0.3,
    }
    print("\nrule accuracy per case (hits/total, false finals, missed finals):")
    for c, rs in by.items():
        fk = collections.Counter(x["k"] for x in rs if x["status"] == "final_offer")
        modal = fk.most_common(1)[0][0] if fk else 99
        line = []
        for name, rule in rules.items():
            rule = rule or (lambda x, m=modal: x["k"] >= m)
            ok, n, ff, mf = acc(rs, rule)
            line.append(f"{name}: {ok}/{n} ff{ff} mf{mf}")
        print(f"{c}: " + " | ".join(line))


if __name__ == "__main__":
    main()
