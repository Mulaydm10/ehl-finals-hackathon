"""P18 candidate comparison (offline, no arena, no LLM): exact scores of every outcome of each candidate for the next live run,
under Werdenfels' measured acceptance rule (analysis/cases/P18_lever.md 16-19):
  it agrees only to an ask < 2% under its current db0 offer, in its own value terms (db5 = db0 + EUR 0.10), and at or above the
  conversation's hidden floor; its counters never go under 5.00; identical conversations get identical replies.

    cd tacto/starter-kit && .venv/Scripts/python.exe ../../analysis/tools/p18_candidates.py
"""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("pcc", ROOT / "analysis/tools/p18_cross_check.py")
pcc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pcc)
BEST, RECORD = 0.7271, pcc.RECORD


def s(p, d, db):
    return pcc.score({"unit_price": p, "payment_days": d, "contract_months": 24, "index_clause": pcc.CLAUSE[db]})


def row(name, outcomes):
    print(f"\n{name}")
    for lbl, (p, d, db), note in outcomes:
        v = s(p, d, db)
        tag = "RECORD" if v > RECORD else "> our 0.727" if v > BEST + 1e-4 else "= our best" if abs(v - BEST) < 1e-4 else ""
        print(f"  {lbl:34s} {p:.2f} @ {d:>2} d db{db}  {v:.4f}  {tag:12s} {note}")


print(f"our best {BEST}  record {RECORD}")
row("A. 0c968aae state (5.00 @ 14 d), one shot at msg 3 (non-acceptance = its final)", [
    ("db0 4.91 (known accepted)", (4.91, 14, 0), "0c968aae: agreed"),
    ("db5 5.01 (= 4.91 to it)", (5.01, 14, 5), "accepted if its db5 price is exactly 0.10"),
    ("fallback final", (5.00, 14, 0), "4.86/4.89/4.90 db0 and 4.97-5.00 db5 all drew this or 5.10 db5"),
])
row("B. 6c2813ce state (5.00 @ 45 d), msg 3 then msg 4 (it HELD at msg 3 there)", [
    ("msg 3 db0 4.93", (4.93, 45, 0), "floor at 30 d in (4.91, 4.94]; 45 d not credited in that game"),
    ("msg 4 db0 4.94", (4.94, 45, 0), "6c2813ce agreed 4.94 at msg 4 (on 30 d)"),
    ("fallback final", (5.00, 45, 0), ""),
])
row("C. B with each ask also on db5 at the same value to it (two sheets per message)", [
    ("msg 3 db5 5.03", (5.03, 45, 5), "= 4.93 db0 to it"),
    ("msg 3 db0 4.93", (4.93, 45, 0), ""),
    ("msg 4 db5 5.04", (5.04, 45, 5), "= 4.94 db0 to it"),
    ("msg 4 db0 4.94", (4.94, 45, 0), ""),
    ("fallback final", (5.00, 45, 0), ""),
])
row("D. record lines (what a record needs)", [
    ("14 d db0 <= 4.86", (4.86, 14, 0), "2.8% under 5.00: outside its 2% authority"),
    ("45 d db0 4.90 (Codacabana)", (4.90, 45, 0), "exactly 2.0%: a tie, not a beat"),
    ("45 d db5 5.00", (5.00, 45, 5), "= 4.90 to it: needs a floor <= 4.90 (never reached in 58 games)"),
    ("60 d db0 4.91", (4.91, 60, 0), "needs 60 d uncharged after round 1 (45 d and 90 d were charged)"),
])
