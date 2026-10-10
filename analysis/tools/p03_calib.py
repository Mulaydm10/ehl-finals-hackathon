"""P03: the arena's exact scoring of any deal, calibrated on 3 real c_deal breakdowns (offline, no quota).

    tacto/starter-kit/.venv/Scripts/python.exe analysis/tools/p03_calib.py

The relationship charge in the three P03 deals (433.08 @ 90 d: €259.63, 433.09 @ 90 d: €254.48, 431.61 @ 60 d:
€17.32) pins the supplier's hidden full cost and money rate; with them total_cost reproduces c_deal to the cent.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tacto/starter-kit"))
from arena_kit.cost import total_cost  # noqa: E402

CASE = {c["case_id"]: c for c in json.loads((ROOT / "datasets/cases_practice.json").read_text(encoding="utf-8"))}["case:P03"]
STD = {"payment_days": 30, "contract_months": 12, "volume_per_year": 4580, "ppm_commitment": 350, "lead_time_days": 49,
       "incoterm": "DAP", "effective_date": "2027-01-01", "index_clause": None, "tooling_eur": 0}
C_OPEN, C_BEST = 4246314.02, 3909043.1
HOUSE = 0.9249


def sup(fc, rate):
    return {"standard": STD, "interest_rate": rate, "full_cost": fc}


def cost(price, days, months=36, fc=395.30, rate=0.061, vol=4580):
    t = {**STD, "unit_price": price, "payment_days": days, "contract_months": months, "volume_per_year": vol}
    return total_cost(CASE, t, STD, sup(fc, rate))


def score(c):
    return (C_OPEN - c) / (C_OPEN - C_BEST)


def fit():
    real = [((433.08, 90), 3942826.22), ((433.09, 90), 3942912.07), ((431.61, 60), 3955565.46)]
    best = None
    for fc100 in range(39400, 39700):
        for r1000 in range(30, 90):
            err = sum(abs(cost(p, d, fc=fc100 / 100, rate=r1000 / 1000) - c) for (p, d), c in real)
            if best is None or err < best[0]:
                best = (err, fc100 / 100, r1000 / 1000)
    return best


if __name__ == "__main__":
    err, fc, rate = fit()
    print(f"fit: full cost EUR {fc}, rate {rate:.3f}, total abs error EUR {err:.2f}")
    print("score by price and payment days (36 m, 4,580/yr); * = beats house", HOUSE)
    for days in (30, 45, 60, 90):
        row = []
        for p in (429.0, 429.5, 430.0, 430.5, 431.0, 431.5, 431.61, 432.0, 432.05, 432.2, 432.5, 433.08):
            s = score(cost(p, days, fc=fc, rate=rate))
            row.append(f"{p:.2f}:{s:.3f}{'*' if s > HOUSE else ' '}")
        print(f"{days:>3} d  " + "  ".join(row))
    # break-even price for the house score per payment term
    for days in (30, 45, 60, 90):
        lo, hi = 400.0, 440.0
        for _ in range(60):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if score(cost(mid, days, fc=fc, rate=rate)) > HOUSE else (lo, mid)
        print(f"house break-even @ {days} d: EUR {lo:.2f} (cut {1 - lo / 438.21:.2%} from the opening price)")
