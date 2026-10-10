"""€ per lever and the price needed per score, for one case, from the probed opening quotes.

    cd tacto/starter-kit && uv run python ../../analysis/tools/case_levers.py P02 [--full]

Needs analysis/cases/openings/<case>.json (probe_open.py). No relationship charge in the grid
(unknown supplier cost): read it as the upper bound of the score for stabilise / secure_supply.
"""

import itertools
import json
import sys

from case_dump import ROOT, case

from arena_kit.cost import closing_terms, cost_breakdown, must_haves_ok, total_cost


def label(v):
    if isinstance(v, dict):
        return f"{v['series']}/db{v['deadband_pct']:g}"
    return str(v)


def load(cid):
    c = case(cid)
    o = json.loads((ROOT / "analysis" / "cases" / "openings" / f"{cid}.json").read_text(encoding="utf-8"))
    return c, o


def openings(c, o):
    out = {}
    for sup, q in o["quote_terms"].items():
        std = q.get("standard", {})
        stated = {**q.get("fixed", {}), **q.get("stated", {})}
        terms = {k: stated.get(k, closing_terms(c, {}, std).get(k)) for k in c["negotiable"]}
        out[sup] = (terms, std)
    return out


def price_for(c, base, std, target):
    lo, hi = 0.0, base["unit_price"] * 3
    for _ in range(60):
        m = (lo + hi) / 2
        if total_cost(c, {**base, "unit_price": m}, std) > target:
            hi = m
        else:
            lo = m
    return lo


def main(cid, full=False):
    c, o = load(cid)
    r = o["result"]
    c_open, c_best, c_alt = r["c_open"], r["c_best"], r["c_alt"]
    span = c_open - c_best
    sc = lambda C: (c_open - C) / span  # noqa: E731
    print(f"{cid}: C_open {c_open:,.0f}  C_best {c_best:,.0f}  span {span:,.0f}  "
          f"C_alt {c_alt if c_alt is None else f'{c_alt:,.0f}'}"
          + ("" if c_alt is None else f" (alt score {max(0, sc(c_alt)):.2f})")
          + f"  | 0.01 score = EUR {span / 100:,.0f}")
    ops = openings(c, o)
    for sup, (t, std) in ops.items():
        C = total_cost(c, t, std)
        print(f"  opening {sup}: {t} std {std}  C {C:,.0f}  score {sc(C):.2f}  must_ok {must_haves_ok(c, t, std)}")
        bd = {k: round(v) for k, v in cost_breakdown(c, t, std).items() if v}
        print(f"    breakdown {bd}")
    best_sup = min(ops, key=lambda s: total_cost(c, *ops[s]) if must_haves_ok(c, *ops[s]) else 1e18)
    base, std = ops[best_sup]
    c0 = total_cost(c, base, std)
    print(f"\nlevers from {best_sup} opening (dC, dScore):")
    rows = [("price -1%", {**base, "unit_price": round(base["unit_price"] * 0.99, 4)})]
    for f, opts in c["term_options"].items():
        if f in c["negotiable"]:
            rows += [(f"{f}={label(v)}", {**base, f: v}) for v in opts if v != base.get(f)]
    for lab, t in rows:
        C = total_cost(c, t, std)
        flag = "" if must_haves_ok(c, t, std) else "  BREAKS MUST-HAVE"
        print(f"  {lab:34s} dC {C - c0:+12,.0f}  dScore {(c0 - C) / span:+.3f}{flag}")
    fields = [f for f in c["term_options"] if f in c["negotiable"]]
    combos = list(itertools.product(*[c["term_options"][f] for f in fields]))
    print(f"\nprice for score 0 / 0.5 / 0.8 / 1.0 (no relationship charge), {len(combos)} combos:")
    print("  " + " | ".join(fields))
    res = []
    for combo in combos:
        t = {**base, **dict(zip(fields, combo))}
        if not must_haves_ok(c, {**t, "unit_price": 1.0}, std):
            continue
        ps = [price_for(c, t, std, c_open - s * span) for s in (0, .5, .8, 1.0)]
        res.append((ps[3], combo, ps))
    res.sort(key=lambda x: -x[0])
    for _, combo, ps in res if full else res[:12]:
        print(f"  {' | '.join(label(v) for v in combo):45s} " + " ".join(f"{p:9.3f}" for p in ps))
    if not full and len(res) > 12:
        print(f"  ... {len(res) - 12} more (--full); worst: "
              f"{' | '.join(label(v) for v in res[-1][1])} needs {res[-1][2][3]:.3f}")


if __name__ == "__main__":
    main(sys.argv[1], "--full" in sys.argv)
