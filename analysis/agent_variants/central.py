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
              "notice_period": 0.5, "po_prices": 0.44, "index_change": 0.31, "scorecard_otd": 0.3}
MIN_SEEN = 3  # fewer observations than this: the prior decides (OTD: 1 game, P10, a supplier that took no data at all)
MIN_TAKE = 0.3  # below this a kind is only cited when nothing better is left
PROVEN = 1.5  # a kind this supplier already took into account in an earlier game ranks above every prior


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
    if seen and seen.get("taken"):
        # this very supplier took this kind before: cite it first - among proven kinds by its own take share, then
        # the prior (P18: index 4 taken / 1 "confirms our case" must not outrank price history 6 / 6)
        share = seen["taken"] / max(1, sum(v for v in seen.values() if isinstance(v, (int, float))))
        return PROVEN + share + 0.01 * PRIOR_TAKE.get(kind, 0.0)
    if seen and not seen.get("taken") and (seen.get("no_change") or seen.get("confirm_case")):
        return 0.0
    k = data.get("by_kind", {}).get(kind)
    return k["take_rate"] if k and sum(v for x, v in k.items() if x != "take_rate") >= MIN_SEEN else PRIOR_TAKE.get(kind, 0.3)


def volume_claims(case, facts):
    """ONE volume-forecast claim, the LATEST forecast for the part, only if it is a RISE (a second fc ID was marked
    "duplicate" by the arena, P07). Live P03: September +10.3% (with should-cost) -> committee EUR 432.15; the June
    snapshot +23.3% instead -> 432.54 (d1bfa5a91489432b) - the latest figure is what counts. Dhruv's v2.7 round 1 on
    P03 (8c2816f2d571b367): "it holds and we took it into account"; 12 of 19 such claims were taken."""
    parts = set(case.get("parts", []))
    fcs = {k: v for k, v in facts.items() if k.startswith("fc:") and v.get("part") in parts}
    if not fcs:
        return []
    ref = max(fcs, key=lambda k: k.split("@")[-1])
    f = fcs[ref]
    pct = f.get("change_pct")
    if pct is None or pct <= 0:
        return []
    return [{"supplier": None, "part": f.get("part"), "kind": "volume_change", "ids": [ref], "figure": pct,
             "sentence": f"Our demand forecast for this part is up {pct:+.1f}% ({ref}), and we commit "
                         f"{f.get('volume_per_year') or case['buyer']['need_per_year']:,} units a year.",
             "checked_by_arena": True}]


def should_cost_claims(claims, sid, parts, opening_price, min_gap=0.03):
    """Should-cost vs the price it QUOTES (v1.5 compared it with today's price: P03 2.4% -> never cited, though its
    quote of EUR 438.21 is 8.7% above the EUR 403.21 estimate). Taken 2 of 2 times (P10)."""
    return [{**c, "sentence": c["sentence"].replace(" per 1 (", " per unit (")} for c in claims
            if c["kind"] == "should_cost" and c["supplier"] == sid and c["part"] in parts
            and opening_price and opening_price > c["figure"] * (1 + min_gap)]


def falling_window_claims(case, drivers, per_series=1, min_fall=-0.2):
    """Falls of the cost drivers in windows the arena checks, as index claims: <= 12 months apart and ENDING within the
    last 12 months of the whole data package (live P03 d1bfa5a91489432b: a window ending 2025-09, 12 months before
    the data's 2026-09, came back "irrelevant" - "an outdated timeframe"). Per series up to `per_series` windows with
    all-new IDs (each ID counts once per case), ranked by weight x fall: the cut follows it (live P03: electronic
    components 42% x -2.3% -> -EUR 0.48 in round 1; copper 5% x -2.2% -> -EUR 0.05 in round 2, "negligible effect").
    `drivers`: {series: weight}. The agent sends at most one index claim per e-mail (padding). One window per series:
    a second window of the same series is "duplicate" (live P03 2483e3891d076863: "already taken that index change
    data into account")."""
    import csv
    data = ROOT / "tacto/data/data"
    names = {r["id"]: r["name"] for r in csv.DictReader((data / "index_series.csv").open(encoding="utf-8"))}
    vals = {}
    for r in csv.DictReader((data / "index_values.csv").open(encoding="utf-8")):
        vals.setdefault(r["series_id"], {})[r["month"]] = float(r["value"])
    last = max(m for v in vals.values() for m in v)

    def months_apart(a, b):
        return (int(b[:4]) - int(a[:4])) * 12 + int(b[5:7]) - int(a[5:7])
    out = []
    for series, weight in drivers.items():
        v = vals.get(series, {})
        used = set()
        for _ in range(per_series):
            best = None
            for b in v:
                if months_apart(b, last) >= 12 or b in used:
                    continue
                for a in v:
                    if a in used or not 0 < months_apart(a, b) <= 12:
                        continue
                    pct = (v[b] / v[a] - 1) * 100
                    if pct <= min_fall and (best is None or pct < best[0]):
                        best = (pct, a, b)
            if not best:
                break
            pct, a, b = best
            used |= {a, b}
            out.append({"supplier": None, "part": None, "kind": "index_change", "series": series,
                        "figure": round(pct, 2), "weight": weight or 0.0,
                        "ids": [f"idx:{series}@{a}", f"idx:{series}@{b}"], "checked_by_arena": True,
                        "sentence": f"{names.get(series, series)} changed {pct:+.1f}% from {a} to {b} "
                                    f"(idx:{series}@{a}, idx:{series}@{b})."})
    return sorted(out, key=lambda c: c["figure"] * (c["weight"] or 0.01))


def weak_delivery_claims(claims, sid, bar=90.0):
    """Its on-time delivery below `bar`% (P03: 84.6%) - a third, different kind of data for round 1. Mixed kinds never
    drew "We received a lot of material" (P10 / P18: three kinds, no padding); two+ index claims always did."""
    return [c for c in claims if c["kind"] == "scorecard_otd" and c["supplier"] == sid and (c.get("figure") or 100) < bar]


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
