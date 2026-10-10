"""€ per lever for a case WITHOUT a probe (non-hosted practice cases, hidden-case stand-ins).

    cd tacto/starter-kit && uv run python ../../analysis/tools/lever_grid.py P09 \
        '{"unit_price": 16.02, "payment_days": 30, "lead_time_days": 35}' [--full-cost 15.4 --rate 0.12]

The JSON is an assumed opening (anything left out: the case's fixed terms, then the buyer's plan).
Prints C of that base sheet, ΔC for each single-field change in `term_options`, € per 1% price,
the price that holds C equal for each option (break-even), and C_alt. With --full-cost the
relationship charge is included (stabilise / secure_supply), using --rate as the supplier's cost of
money (default 0.08). Compare with case_levers.py, which needs a probe in openings/.
"""

import json
import sys

from case_dump import case

from arena_kit.cost import cost_breakdown, must_haves_ok, supplier_value, total_cost


def args(argv):
    cid, base = argv[1], json.loads(argv[2])
    opts = dict(zip(argv[3::2], argv[4::2]))
    return cid, base, float(opts["--full-cost"]) if "--full-cost" in opts else None, float(opts.get("--rate", 0.08))


def main():
    cid, base, full_cost, rate = args(sys.argv)
    c = case(cid)
    std = {k: v for k, v in base.items() if k != "unit_price"}
    sup = {"standard": std, "interest_rate": rate, "full_cost": full_cost} if full_cost else None

    def C(t):
        return total_cost(c, t, std, sup)

    c0 = C(base)
    alt = c["buyer"]["alternative"]
    c_alt = total_cost(c, alt["terms"]) if alt.get("terms") else None
    one_pct = C({**base, "unit_price": base["unit_price"] * 0.99}) - c0
    print(f"{cid} base {base}\nC_base = {c0:,.0f}   C_alt = {c_alt and f'{c_alt:,.0f}'}   1% price = {one_pct:,.0f}")
    print({k: round(v) for k, v in cost_breakdown(c, base, std, sup).items() if v})
    if sup:
        print(f"supplier value/unit {supplier_value(c, base, sup):.2f} vs full cost {full_cost}")
    print(f"\n{'field':<30}{'option':>10}{'ΔC':>12}{'Δ in % price':>14}{'must-have':>11}")
    for field, options in c.get("term_options", {}).items():
        for v in options:
            t = {**base, field: v}
            d = C(t) - c0
            print(f"{field:<30}{str(v):>10}{d:>12,.0f}{d / -one_pct:>13.2f}%{'ok' if must_haves_ok(c, t, std) else 'BROKEN':>11}")


if __name__ == "__main__":
    main()
