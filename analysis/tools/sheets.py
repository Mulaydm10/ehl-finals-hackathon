"""Score candidate term sheets for a case against the probed C_open / C_best.

    cd tacto/starter-kit && uv run python ../../analysis/tools/sheets.py P02 \
        '{"unit_price": 361, "payment_days": 60}' '{"unit_price": 363.5, "payment_days": 90}'

Fields left out come from the cheapest opening quote; the supplier is the cheapest opening's
unless "_sup" is given. Optional "_fc" (full cost) and "_rate" add the relationship charge.
"""

import json
import sys

from case_levers import load, openings

from arena_kit.cost import cost_breakdown, must_haves_ok, supplier_value, total_cost


def evaluate(cid, sheet):
    c, o = load(cid)
    r = o["result"]
    ops = openings(c, o)
    sup = sheet.pop("_sup", None) or min(ops, key=lambda s: total_cost(c, *ops[s]))
    fc, rate = sheet.pop("_fc", None), sheet.pop("_rate", 0.08)
    base, std = ops[sup]
    t = {**base, **sheet}
    # its standard terms: the opening's non-price terms + the quote PDF's standard terms
    est = {"standard": closing_std(c, base, std), "interest_rate": rate, "full_cost": fc} if fc else None
    C = total_cost(c, t, std, est)
    rel = cost_breakdown(c, t, std, est)["relationship"] if est else 0.0
    score = (r["c_open"] - C) / (r["c_open"] - r["c_best"])
    val = supplier_value(c, t, est or {"standard": closing_std(c, base, std), "interest_rate": rate})
    return C, score, rel, val, must_haves_ok(c, t, std), sup


def closing_std(c, base, std):
    from arena_kit.cost import closing_terms

    return {k: v for k, v in closing_terms(c, {**base}, std).items() if k != "unit_price"}


if __name__ == "__main__":
    cid = sys.argv[1]
    for s in sys.argv[2:]:
        sheet = json.loads(s)
        shown = dict(sheet)
        C, score, rel, val, ok, sup = evaluate(cid, sheet)
        print(f"{json.dumps(shown):95s} C {C:12,.0f} score {score:5.2f} rel {rel:8,.0f} "
              f"sup_value {val:9.3f} must_ok {ok} ({sup})")
