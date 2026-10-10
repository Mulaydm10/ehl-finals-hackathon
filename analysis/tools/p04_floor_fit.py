"""P04 ceiling proof (analysis/cases/P04_deep.md section 3). Offline, no arena calls.

    cd tacto/starter-kit && uv run python ../../analysis/tools/p04_floor_fit.py

1. C_best prices per payment term: the price at which each term costs us exactly C_best.
2. The supplier's cash rate, from every P04 game. One value target per message, rounded up (or to nearest) to the cent.
   Refused asks are worth less than its new target. Its target never sits under its floor
   F = (C_best price @ 90 d) x (1 - rate/6). Agreed sheets clear F.
3. For every feasible rate: the cheapest whole-cent price it can accept on each term and its score.
4. The rate each record-beating cent would need.
"""
import glob
import json
import math
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tacto/starter-kit"))
from arena_kit.cost import complete_offer, score, total_cost  # noqa: E402

CASE = next(c for c in json.loads((ROOT / "datasets/cases_practice.json").read_text(encoding="utf-8"))
            if c["case_id"] == "case:P04")
C_OPEN, C_BEST = 198846.33, 196529.32  # every P04 result
STD = {"unit_price": 4.96, "payment_days": 30, "contract_months": 12, "volume_per_year": 20000, "lead_time_days": 7,
       "incoterm": "DAP", "tooling_eur": 0, "index_clause": None, "effective_date": "2027-01-01", "ppm_commitment": 150}
TERMS = (14, 30, 45, 60, 90)


def sc(p, d, m=36):
    return score(C_OPEN, total_cost(CASE, complete_offer(CASE, {"unit_price": p, "payment_days": d, "contract_months": m}), STD),
                 C_BEST)


def f(r, d):  # the supplier's value of one euro of price on payment term d (its standard term: 30 d)
    return 1 - r * (d - 30) / 360


def cbest_price(d, m=36):
    lo, hi = 4.5, 5.2
    for _ in range(80):
        mid = (lo + hi) / 2
        c = total_cost(CASE, complete_offer(CASE, {"unit_price": mid, "payment_days": d, "contract_months": m}), STD)
        lo, hi = (lo, mid) if c > C_BEST else (mid, hi)
    return lo


def games():
    out = {}
    for fn in glob.glob(str(ROOT / "datasets/runs/*.json")):
        d = json.loads(Path(fn).read_text(encoding="utf-8"))
        s = d.get("session") or {}
        if s.get("case_id") == "case:P04":
            out[s["session_id"]] = d["threads"]["sup:70620"]["messages"]
    for fn in glob.glob(str(ROOT / "tools/replays/raw/P04_*.json")):
        sid = os.path.basename(fn)[4:-5]
        th = (json.loads(Path(fn).read_text(encoding="utf-8")).get("thread_messages") or {}).get("sup:70620")
        if th and sid not in out:
            out[sid] = th["messages"]
    return out


def observations(gs):
    obs = []
    for ms in gs.values():
        ask = None
        for i, m in enumerate(ms):
            ts = [(t["terms"]["unit_price"], t["terms"]["payment_days"]) for t in m.get("term_sheets") or []
                  if t["terms"].get("unit_price")]
            if m["from"] == "buyer":
                ask = ts or ask
            elif i:
                obs.append((m.get("status"), ts, ask))
    return obs


def feasible(r, obs, p90, mode, use_floor=True):
    floor = p90 * f(r, 90)
    for status, ts, ask in obs:
        if status == "walked_away":
            continue
        if status == "agreed":
            if use_floor and any(p * f(r, d) < floor - 1e-12 for p, d in ts):
                return False
            continue
        lo, hi = -1.0, 9.0
        for p, d in ts:
            a, b = ((p - 0.01) * f(r, d), p * f(r, d)) if mode == "up" else ((p - 0.005) * f(r, d), (p + 0.005) * f(r, d))
            lo, hi = max(lo, a), min(hi, b)
        if lo >= hi or (use_floor and hi < floor - 1e-12):
            return False
        if any(p * f(r, d) >= hi for p, d in (ask or [])):
            return False
    return True


def main():
    p = {d: cbest_price(d) for d in TERMS}
    print("C_best price per term:", {d: round(v, 4) for d, v in p.items()})
    obs = observations(games())
    for mode in ("up", "nearest"):
        rs = [x / 10000 for x in range(500, 1100) if feasible(x / 10000, obs, p[90], mode)]
        rs0 = [x / 10000 for x in range(500, 1100) if feasible(x / 10000, obs, p[90], mode, use_floor=False)]
        print(f"rounding {mode}: rate {min(rs):.2%}-{max(rs):.2%} (quotes alone: {min(rs0):.2%}-{max(rs0):.2%}), "
              f"floor F {p[90] * f(max(rs), 90):.4f}-{p[90] * f(min(rs), 90):.4f}")
        best = {}
        for r in rs:
            floor = p[90] * f(r, 90)
            for d in TERMS:
                cent = math.ceil(round(floor / f(r, d) * 100, 6)) / 100
                best[d] = max(best.get(d, (0, 0)), (round(sc(cent, d), 4), cent))
        print("   best acceptable deal per term (score, price):", best)
    for price, d in [(4.88, 45), (4.87, 30), (4.90, 60), (4.85, 14), (4.93, 90)]:
        need = [x / 100000 for x in range(5000, 12000) if price * f(x / 100000, d) >= p[90] * f(x / 100000, 90)]
        print(f"{price} @ {d} d (score {sc(price, d):.3f}) needs rate >= {min(need):.3%}" if need else
              f"{price} @ {d} d: never acceptable")


if __name__ == "__main__":
    main()
