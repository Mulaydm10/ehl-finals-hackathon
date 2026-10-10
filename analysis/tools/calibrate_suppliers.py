"""Fit each supplier's hidden full cost and cash rate from the relationship charge in our real deals (offline).

    tacto/starter-kit/.venv/Scripts/python.exe analysis/tools/calibrate_suppliers.py

Stabilise / secure_supply cases charge EUR per margin point the deal leaves the supplier below its sustainable
margin; the arena's cost breakdown shows that charge for every deal. Two or more deals with a non-zero charge on
different payment terms pin (full_cost, interest_rate). A fit is kept only if it reproduces every deal's c_deal
within EUR 1. Writes analysis/central/calibration.json (read by analysis/agent_variants/central.py).
"""

import glob
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tacto/starter-kit"))
from arena_kit.cost import total_cost  # noqa: E402

OUT = ROOT / "analysis" / "central" / "calibration.json"


def deals():
    seen = {}
    for f in glob.glob(str(ROOT / "tools/replays/raw/*.json")) + glob.glob(str(ROOT / "datasets/runs/*.json")):
        s = json.loads(Path(f).read_text(encoding="utf-8"))
        d = s.get("detail") or s
        r = d.get("result") or {}
        if r.get("deal") and r.get("terms") and d.get("session_id") not in seen:
            seen[d["session_id"]] = (d["case_id"], r["supplier_id"], r["terms"], r["c_deal"], r["cost_breakdown"])
    return list(seen.values())


def main():
    cases = {c["case_id"]: c for c in json.loads((ROOT / "datasets/cases_practice.json").read_text(encoding="utf-8"))}
    dossiers = json.loads((ROOT / "datasets/A_dossiers.json").read_text(encoding="utf-8"))
    groups = {}
    for case_id, sid, terms, c_deal, bd in deals():
        if (bd or {}).get("relationship", 0) > 0.01:
            groups.setdefault((case_id, sid), []).append((terms, c_deal))
    out = {}
    for (case_id, sid), rows in sorted(groups.items()):
        rows = list({json.dumps(t, sort_keys=True): (t, c) for t, c in rows}.values())
        if len({t.get("payment_days") for t, _ in rows}) < 2:
            print(f"{case_id} {sid}: {len(rows)} deal(s) on one payment term - cannot separate cost and rate")
            continue
        case = cases[case_id]
        std = {**{k: v for k, v in (dossiers.get(sid, {}).get("standard_terms") or {}).items() if v is not None},
               **case.get("fixed_terms", {})}
        price = rows[0][0]["unit_price"]
        def err(fc, rate):
            est = {"standard": std, "interest_rate": rate, "full_cost": fc}
            return max(abs(total_cost(case, t, std, est) - c) for t, c in rows)

        # per rate (0.1-point grid): the full cost that reproduces the first deal exactly (its charge rises with the
        # full cost), then the worst error over all deals; keep the best rate
        t0, c0 = rows[0]

        def fc_for(rate):
            lo, hi = price * 0.5, price * 1.2
            for _ in range(50):
                mid = (lo + hi) / 2
                est = {"standard": std, "interest_rate": rate, "full_cost": mid}
                lo, hi = (mid, hi) if total_cost(case, t0, std, est) < c0 else (lo, mid)
            return lo
        cand = [(err(fc_for(r / 1000), r / 1000), fc_for(r / 1000), r / 1000) for r in range(5, 300)]
        _, fc, rate = min(cand)
        fc, rate = round(fc, 2), round(rate, 4)
        worst = err(fc, rate)
        print(f"{case_id} {sid}: full cost EUR {fc}, rate {rate:.3f}, max error EUR {worst:.2f} over {len(rows)} deals")
        if worst <= 1.0:
            out.setdefault(case_id, {})[sid] = {"full_cost": fc, "interest_rate": rate, "deals": len(rows)}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
