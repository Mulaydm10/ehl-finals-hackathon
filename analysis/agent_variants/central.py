"""Central layer: what all our games, agents and simulators taught us, in one place an agent can read.

Sources (details and evidence: analysis/central/LEARNINGS.md):
  - 54 archived live games (datasets/runs, tools/replays/raw): the suppliers' reasons in the traces, claim results,
    the cost breakdowns of every deal (relationship charge included);
  - Dhruv's agent changelog (notes/agent_changelog.md, v1.2-v2.8), Parth's strategy note (analysis/strategy_0.9.md),
    Neel's replay lessons / run audit (analysis/replay_lessons.md, analysis/run_audit.md);
  - the simulators (src/eval/offline_eval.py, analysis/tools/sim_floorstop.py) - they ignore text, so everything
    about WORDS below comes from live games only.

Pure functions + small data files; no arena calls. Used by analysis/agent_variants/noidea_neel.py.
"""

import json
import math
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / "datasets" / "A_dossiers.json").exists())
REACTIONS = ROOT / "analysis" / "central" / "claim_reactions.json"
CALIBRATION = ROOT / "analysis" / "central" / "calibration.json"

# ---- 1. which data to cite ---------------------------------------------------------------------------------
# Supplier reactions to verified data, 54 games (analysis/tools/mine_claims.py): "it holds and we took it into
# account" vs "it holds, but it does not change our calculation" vs "Your figures confirm our case" (a rising
# index, 7x). Prior take-rates used when the mined file is missing.
PRIOR_TAKE = {"should_cost": 1.0, "scorecard_ppm": 1.0, "rival_quote": 0.75, "volume_change": 0.63,
              "notice_period": 0.5, "po_prices": 0.44, "index_change": 0.31, "scorecard_otd": 0.0}
MIN_TAKE = 0.3  # below this a kind is only cited when nothing better is left


def reactions():
    try:
        return json.loads(REACTIONS.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"by_kind": {}, "by_case": {}}


def take_rate(kind, case_id, data=None):
    """Chance this kind of verified claim moves the supplier. A kind that only ever got "does not change our
    calculation" from THIS case's supplier (P03: price history, 2 of 2) counts as 0."""
    data = data or reactions()
    seen = data.get("by_case", {}).get(case_id, {}).get(kind)
    if seen and not seen.get("taken") and (seen.get("no_change") or seen.get("confirm_case")):
        return 0.0
    k = data.get("by_kind", {}).get(kind)
    return k["take_rate"] if k and sum(v for x, v in k.items() if x != "take_rate") >= 2 else PRIOR_TAKE.get(kind, 0.3)


def volume_claims(case, facts):
    """'Our demand forecast ... is up +X% (fc:...)' for the case's own forecast refs - only a RISE (good news for
    it). Dhruv's v2.7 round 1 on P03 (8c2816f2d571b367): "it holds and we took it into account" -> EUR 432.94 @ 90 d,
    the best first answer in 7 P03 games; v2.6 and earlier never cited it. 12 of 19 such claims were taken."""
    out = []
    for ref in case.get("refs", []):
        if not ref.startswith("fc:") or ref not in facts:
            continue
        f = facts[ref]
        pct = f.get("change_pct")
        if pct is None or pct <= 0:
            continue
        out.append({"supplier": None, "part": f.get("part"), "kind": "volume_change", "ids": [ref], "figure": pct,
                    "sentence": f"Our demand forecast for this part is up {pct:+.1f}% ({ref}), and we commit "
                                f"{f.get('volume_per_year') or case['buyer']['need_per_year']:,} units a year.",
                    "checked_by_arena": True})
    return out


def should_cost_claims(claims, sid, parts, opening_price, min_gap=0.03):
    """Should-cost vs the price it QUOTES (v1.5 compared it with today's price: P03 2.4% -> never cited, though its
    quote of EUR 438.21 is 8.7% above the EUR 403.21 estimate). Taken 2 of 2 times (P10)."""
    return [{**c, "sentence": c["sentence"].replace(" per 1 (", " per unit (")} for c in claims
            if c["kind"] == "should_cost" and c["supplier"] == sid and c["part"] in parts
            and opening_price and opening_price > c["figure"] * (1 + min_gap)]


def rank(claims, case_id, data=None):
    """Best first by take-rate; rising indices never (they "confirm our case"); kinds this supplier already shrugged
    off go last. Stable within a kind."""
    data = data or reactions()

    def key(c):
        if c["kind"] == "index_change" and (c.get("figure") or 0) > 0:
            return 9.0
        return -take_rate(c["kind"], case_id, data)
    return sorted(claims, key=key)


# ---- 2. the supplier model (exact, where we have deals) -----------------------------------------------------
# The relationship charge in a deal's cost breakdown pins the supplier's hidden full cost and cash rate. P03 from 3
# deals (433.08 @ 90 d: EUR 259.63, 433.09 @ 90 d: 254.48, 431.61 @ 60 d: 17.32): full cost EUR 395.30, rate 6.1%
# - total_cost then reproduces all three c_deal values to the cent (analysis/tools/p03_calib.py).

def calibrated(case_id, sid):
    """{'full_cost', 'interest_rate'} fitted on real deals of this case, or None."""
    try:
        cal = json.loads(CALIBRATION.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return cal.get(case_id, {}).get(sid)


def money_cheaper_for_it(est, buyer_rate):
    """Longer payment is worth more to us than it costs the supplier: lead with the longest payment term."""
    return est.get("interest_rate", buyer_rate) < buyer_rate


# ---- 3. how the suppliers decide (rules the agent follows) ---------------------------------------------------
# a) Round 1 does most of the work (Parth: mean price step 1.85% in round 1 vs 0.4-0.5% later, 107 steps). Never
#    send round 1 without checkable data: 26 replies asked "Which figures is that based on? Please send us the data"
#    - every one of our 6 P03 round-1 e-mails had no claim at all (rising indices filtered, nothing else ranked).
# b) Approval ladder: its sales person stops at the threshold; bigger moves come only from the committee. Ask for the
#    committee IN ROUND 1 on one structure (P03: KAM stop EUR 431.61 @ 60 d = exactly 2.00% below the quote in its
#    own cash terms; committee EUR 432.94-433.09 @ 90 d, 1.0-1.05% above the floor C_best implies).
# c) Stay on the structure it priced. Hopping payment terms after its committee priced one (P03 47a88b4d0bb75ce3:
#    433.08 @ 90 d -> we asked 60/45/30 d -> final 431.61 @ 60 d) loses what the committee gave.
# d) final_offer = accept (P07 walked after one "small" extra ask, P08 walked after a counter on its final).
# e) Take the cheapest of all its sheets, incl. '-a' alternatives (+0.03 mean on 15 real finals).
# f) Padding does not buy price ("We received a lot of material", 11x): max 3 claims, each ID once per case.
APPROVAL = re.compile(r"(?i)above (\d+(?:[.,]\d+)?)\s?%")


def committee_round1(motives):
    return bool({"approval_ladder", "price_frozen"} & set(motives))


def same_structure(t, ref, fields=("payment_days", "contract_months", "volume_per_year")):
    return all(t.get(f) == ref.get(f) for f in fields if ref.get(f) is not None)


def exact_score(case, terms, std, est, c_open, c_best):
    from arena_kit.cost import total_cost  # noqa: PLC0415 (works from both folders)
    c = total_cost(case, terms, std, est)
    return (c_open - c) / (c_open - c_best) if c_open and c_best and math.isfinite(c) else None
