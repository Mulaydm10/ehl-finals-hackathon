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
PRIOR_TAKE = {"should_cost": 1.0, "scorecard_ppm": 0.5, "quality_notification": 0.6,  # ppm: taken in P11, ~0 in P03; qn: never cited
              "rival_quote": 0.75, "volume_change": 0.63,
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
    if kind == "quality_notification":  # the arena words both as "quality record" (P08 cae4b621695f8161: no change)
        q = data.get("by_case", {}).get(case_id, {}).get("scorecard_ppm") or {}
        if q.get("no_change") and not q.get("taken"):
            return 0.0
    seen = data.get("by_case", {}).get(case_id, {}).get(kind)
    if seen and seen.get("taken"):
        # this very supplier took this kind before: cite it first - among proven kinds by its own take share, then
        # the prior (P18: index 4 taken / 1 "confirms our case" must not outrank price history 6 / 6)
        share = seen["taken"] / max(1, sum(v for v in seen.values() if isinstance(v, (int, float))))
        return PROVEN + share + 0.01 * PRIOR_TAKE.get(kind, 0.0)
    # "confirm our case" is the reaction to a RISING index, which we no longer cite - it says nothing about a fall
    # (P02: 7 rising-index games had blocked copper's -2.2% fall)
    if seen and not seen.get("taken") and seen.get("no_change"):
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
    # one number per claim sentence (the commitment is stated in section 1 of every e-mail). P08 offline: the old
    # sentence said "we commit 118,500 units a year" - the forecast's volume, not the case's fixed 94,800
    return [{"supplier": None, "part": f.get("part"), "kind": "volume_change", "ids": [ref], "figure": pct,
             "sentence": f"Our demand forecast for this part is up {pct:+.1f}% ({ref}).",
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


def quality_notification_claims(case, facts, sid):
    """Supplier-caused quality notifications on THIS part in the last 12 months of the data, as one verified quality fact
    (the arena checks qn rows as "the mean ppm if you speak of quality"). Never cited in any of our games (cloud
    session, analysis/central/ENGINES.md); P02: qn:20004698 (2025-10-16, 4,000 ppm), qn:20004826 (2026-02-18, 5,263 ppm)."""
    parts = set(case.get("parts", []))
    last = max((v.get("date") or "") for v in facts.values() if isinstance(v, dict) and v.get("date"))
    floor = f"{int(last[:4]) - 1}{last[4:]}"
    qns = sorted(k for k, v in facts.items() if k.startswith("qn:") and v.get("supplier") == sid
                 and v.get("part") in parts and (v.get("date") or "") > floor)
    if not qns:
        return []
    # ONE part, at most 8 IDs (newest first), like the 2-8 order lines api.md allows: live P07 (Parth, 79b7b274b6a77470,
    # 55db9b3de85aa78d) - 19 QN IDs over the kit's parts in one claim -> the arena answered HTTP 500 four times and the
    # agent died mid-game (abandoned case = no deal)
    by_part = {}
    for k in qns:
        by_part.setdefault(facts[k]["part"], []).append(k)
    qns = sorted(max(by_part.values(), key=len), key=lambda k: facts[k].get("date") or "", reverse=True)[:8]
    mean = sum(facts[k]["ppm"] for k in qns) / len(qns)
    return [{"supplier": sid, "part": facts[qns[0]]["part"], "kind": "quality_notification", "ids": qns,
             "figure": round(mean), "keep_alive": True, "checked_by_arena": True,
             # NO number at all: live P02 f778b35c67ecd799 wrote "2 quality notifications ... in the last 12 months, at
             # 4,632 ppm" -> "contradicted ... That costs trust" (0.607). Without a figure the arena takes the data's own.
             "sentence": f"We raised quality notifications on this part over the past year ({', '.join(qns)})."}]


def hedged_series(case, motives):
    """Series it has covered at fixed prices (motive hedged_forward): every claim on them met "That is not our reality:
    our AS-14404 is covered at fixed prices until March 2027" (P08 5 of 5). Its index-clause series."""
    if "hedged_forward" not in motives:
        return set()
    return {o["series"] for o in case.get("term_options", {}).get("index_clause", []) if o}


def final_at(case_id, data=None):
    """Our message number at which this supplier said final_offer in past games (most common), or None.
    P08: always our 3rd; P02: 4th-5th."""
    data = data or reactions()
    sig = data.get("by_case", {}).get(case_id, {}).get("_signals", {})
    counts = {int(k.split("_")[-1]): v for k, v in sig.items() if k.startswith("final_at_")}
    return max(counts, key=lambda n: (counts[n], -n)) if counts else None


def own_quote_note(facts, sid, parts, opening_price, today="2026-09-30", days=90):
    """Its OWN recent quote for this part below its opening, in words only (no ID: a quote outside the case refs would be
    "irrelevant"). P08: "On 2026-09-10 you quoted EUR 5.45" vs its EUR 6.05 opening (cloud: analysis/cases/P08_engine.md)."""
    from datetime import date
    t0 = date.fromisoformat(today)
    best = None
    for k, v in facts.items():
        if k.startswith("quote:") and v.get("supplier") == sid and v.get("part") in parts and v.get("date"):
            if (t0 - date.fromisoformat(v["date"])).days <= days and opening_price and v["unit_price"] < opening_price:
                if best is None or v["date"] > best["date"]:
                    best = v
    if not best:
        return None
    return (f"On {best['date']} you quoted us EUR {best['unit_price']:.2f} per unit for this part; your new quote is "
            f"{(opening_price / best['unit_price'] - 1) * 100:.1f}% above it.")


def cross_sell_note(facts, sid, dossier, case_parts):
    """Its person's currency (cloud task 13, analysis/cases/P08_floor.md): a stock distributor ends every e-mail with "our whole
    range is at your disposal, so if there is anything else on your list, just send it over" (P08: 21 of its e-mails). A part
    it is qualified for, at 0% quota, that we buy elsewhere and it has quoted us before -> an invitation to quote, in words
    (no ID, no figure: nothing for the arena to contradict). P08: Sheet 1.4301 2 mm (fc:370021 72100 a year, from 70730;
    its own quote:7100069 in 2024)."""
    for p in dossier.get("parts", []):
        if p["part"] in case_parts or (p.get("quota_pct") or 0) > 0 or p.get("status") != "qualified":
            continue
        pid = p["part"].split(":")[1]
        bought = any(k.startswith("po:") and v.get("part") == p["part"] and v.get("supplier") != sid for k, v in facts.items())
        quoted = any(k.startswith("quote:") and v.get("part") == p["part"] and v.get("supplier") == sid for k, v in facts.items())
        if bought and quoted and any(k.startswith(f"fc:{pid}@") for k in facts):
            return (f"Beyond this part, we buy {p['description']} from another supplier today, in a volume close to this "
                    f"bar's, and you have quoted it for us before. Once this agreement is signed, we will invite you to quote for it.")
    return None


def delivery_year_claims(facts, sid, bar=95.0):
    """On-time delivery as the mean of 4 quarterly scorecard rows, for the last 12 months and the 12 months before
    (P02: 89.3% and 83.9%). Each a verified fact with its own IDs. For a MIRRORING supplier only, as the last items:
    it cuts in every round that brings new verified data, even data it says "does not change our calculation" (P02
    552fb056e31d24d1: order history -> -1.10), and goes final in the first round without any (-> -0.30, final)."""
    rows = sorted((k for k, v in facts.items() if k.startswith(f"sc:{sid[4:]}@") and v.get("otd_pct") is not None),
                  key=lambda k: k.split("@")[-1])
    out = []
    for block in (rows[-4:], rows[-8:-4]):
        if len(block) < 4:
            continue
        mean = sum(facts[k]["otd_pct"] for k in block) / 4
        if mean >= bar:
            continue
        q0, q1 = block[0].split("@")[-1], block[-1].split("@")[-1]
        out.append({"supplier": sid, "part": None, "kind": "scorecard_otd", "ids": list(block), "figure": round(mean, 1),
                    "keep_alive": True, "checked_by_arena": True,
                    "sentence": f"Your on-time delivery averaged {mean:.1f}% from {q0} to {q1} ({', '.join(block)})."})
    return out


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
        rate = take_rate(c["kind"], case_id, data)
        if c["kind"] == "index_change":  # a FALL of a cost driver was taken in P01, P03 (x3), P18
            rate = max(rate, 0.9)
        return -rate
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


FULL_AUTHORITY = re.compile(r"(?i)hold (the )?full authority|committee is not applicable|without further committee")


def committee_round1(motives):
    return bool({"approval_ladder", "price_frozen"} & set(motives))


MIRROR = re.compile(r"(?i)in response to your (step|movement|adjustment)|significant step towards our position")
MIRROR_SHARE = 0.40  # a mirroring supplier: step 40% of the remaining gap per round (P02: 30% -> its cuts 1.67/1.40/0.90)
MIRROR_ANCHOR = 0.05  # ...and open 5% below its quote in value (stabilise default 3.5%): the meeting point follows the anchor


# its sales person signals its own limit and that management could go further. P02 ee98266bedd37231 round 4: "This
# represents our best effort to accommodate your target without requiring management escalation"; then "we cannot adjust
# our calculation without a verifiable basis" -> final. Ask ONCE, with a real step, before it goes final.
ESCALATION_HINT = re.compile(r"(?i)without (requiring )?(management|committee) (escalation|approval)|best effort|"
                             r"cannot adjust (our|the) (calculation|pricing|price)|lacks new verifiable data|"
                             r"no new verified data|maximum (flexibility|concession)")


def mirror_supplier(case_id, data=None):
    """It answers our step with a step of its own (P02: "In response to your step, we are prepared to reduce our price"
    in 4 games, 1:1 in 466f3cb54614635f; a1e2a4acb73dd3e9: "We expect a significant step towards our position"). Our
    ask is far below its price and the deal is ITS price, so a bigger step from us costs nothing and buys a bigger one."""
    data = data or reactions()
    return bool(data.get("by_case", {}).get(case_id, {}).get("_signals", {}).get("mirror"))


def full_authority(case_id, data=None):
    """Its sales person said it decides alone (P02 x4, every round of de6192e39dd86084: "I hold full authority to
    conclude this agreement ... without further committee approval"): then never mention a committee."""
    data = data or reactions()
    return bool(data.get("by_case", {}).get(case_id, {}).get("_signals", {}).get("full_authority"))


def same_structure(t, ref, fields=("payment_days", "contract_months", "volume_per_year")):
    return all(t.get(f) == ref.get(f) for f in fields if ref.get(f) is not None)


def exact_score(case, terms, std, est, c_open, c_best):
    from arena_kit.cost import total_cost  # noqa: PLC0415 (works from both folders)
    c = total_cost(case, terms, std, est)
    return (c_open - c) / (c_open - c_best) if c_open and c_best and math.isfinite(c) else None
