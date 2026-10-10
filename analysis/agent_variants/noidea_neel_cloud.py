"""Team NoIdea buyer - Neel's variant of v1.5 (ef489c6) with the P04 live lessons (d3050f951dc2c45b):
  1. near-close: when the supplier stalls, ask for a hair (CLOSE_STEP) below its standing value, priced up
     to the next cent per structure, and send only the sheet(s) cheapest for us (P04: 0.86 -> 0.94 in the
     calibrated sim, analysis/tools/sim_floorstop.py);
  2. cite only indices that fell or stayed flat ("Your figures confirm our case: that driver rose");
  3. ask for the cost breakdown once (it refused the second time: "company policy");
  4. UTF-8 file reads (Windows), "Write in English" (Astra wrote a German paragraph offline).

Team NoIdea buyer v1.2: code sets every number, the language model only writes the opening.

Sources: docs/EDA_FINDINGS.md, datasets A/C (datasets/), Neel's playbooks (playbooks/) and case
deep dives (analysis/cases/). Change log with evidence: notes/agent_changelog.md.

  - anchor: calibrated per goal/type on the 9 probed practice cases (src/eval/calibrate.py): the
    best deal sits 0.3-2% below the opening in stabilise cases, 13-22% in leverage, bundling and
    capacity cases. Price increases also use the cost-justified change (drivers x 12 m indices).
  - the supplier: cost floor from should-cost / current / quoted price, cash rate from its motives
  - term sheets: every combination of the negotiable options, priced to a target supplier value,
    ranked by OUR total cost incl. the relationship charge; 3 different ones go out, never above the
    supplier's standing price (playbooks/_common.md 2)
  - concession: reciprocal - never more per round than the supplier gave; 8 planned rounds
  - arguments: checked sentences from dataset C, each ID cited once per case, the better of the
    6/12-month index windows, rival offers in RFQs; binding volume and term stated in every e-mail
  - signals: agreed -> accept; final_offer -> one last non-price ask, then accept (or walk if the
    alternative is cheaper)
"""

import itertools
import json
import logging
import math
import os
import re
from pathlib import Path

from ..cost import complete_offer, must_haves_ok, supplier_value, total_cost
from ..docs import standard_terms
from ..play import latest, live_threads, moves_left, standing

log = logging.getLogger("arena")


def _central():
    """analysis/agent_variants/central_cloud.py (cloud copy of central.py) - the team's shared learnings (loaded by path: this file is loaded by path)."""
    import importlib.util
    import sys
    if "noidea_central_cloud" in sys.modules:
        return sys.modules["noidea_central_cloud"]
    spec = importlib.util.spec_from_file_location("noidea_central_cloud", Path(__file__).with_name("central_cloud.py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["noidea_central_cloud"] = mod
    spec.loader.exec_module(mod)
    return mod


central = _central()

ALT_BAND = 1.003  # cloud fix #3: alternative sheets within 0.3% of our best C
PLANNED_ROUNDS = 8  # P07 live: ~25 s per round, so an 8-minute wave fits ~12-15; keep a margin
MIN_GAIN_PTS = 1.0  # never pay more than ask - 1 pt unless it is the last word
CLOSE_STEP = 0.0008  # near-close: ask for 0.08% below its standing cash value. Live P04 5f80eb75c793f352: 0.2% below
# (EUR 4.85 @ 14 d / 4.90 @ 60 d) was refused - "we must maintain our price" - and it went final on a worse term (0.81);
# its stop sat at a cash value of ~4.874-4.877 in both live games, 0.15% above the floor C_best implies
STALL_DROP = 1 / 3  # it stalled when its last move (share of the gap) fell below a third of the one before
STALL_MIN = 0.02  # ...or below 2% of the gap
STALL_NOISE = 0.10  # a small move UP (cent rounding on another structure) still counts; a big one doesn't
TIE_BAND = 0.0001  # sheets within 0.01% of our best cost count as a tie (0.015% and 0.05% made P02 worse: 0.94 -> 0.86)
ESCALATE_GIVEBACK = (0.15,)  # 0.30 (EUR 432.48 @ 90 d in P03) scored below the house agent (0.925)  # escalation: also offer to pay back 30% / 45% of its cash loss (live P03: it countered 433.09 = ~50%)
LIMIT_HIT = re.compile(r"(?i)maximum (flexibility|extension)|within (our|my) (delegated |approval )?(authority|remit)|"
                       r"(base )?prices? (are|is|remain)s? (strictly |currently )?(fixed|frozen)|price freeze|"
                       r"cannot reduce the (unit )?price|unable to (reduce|accommodate any further price)|"
                       r"approval of (our|the) (pricing )?committee|guidelines?|prohibit|absolute (minimum|limit)|"
                       r"no further (price )?(reduction|concession)|(cannot|can't) go (any )?lower")
# live P03 1db1ce07b2f78a35 "base prices are currently frozen"; 78f03f1c9dcde080 "group pricing guidelines strictly
# prohibit further price reductions" / "absolute minimum price" - the wording changes every game, so the trigger
# is also behavioural: its price did not move between its last two replies (see decide)
EDGE_PLUS = 0.0004  # edge sheet: its approval threshold + 0.04% (P03: 2.04% beats the house agent, 2.00% scores 0.919)
FREEZE_CUT = 0.01  # escalation under a price freeze: also offer its own structure 1% lower
CLOSE_GAP = 0.005  # cloud fix #5 (was 0.015): near-close only within 0.5% of its standing value; a stop 0.6% above its floor is still worth creeping to (live P04: 1.0% gap)
# How far below the opening quote to anchor (src/eval/calibrate.py: best deal vs opening, practice cases)
ANCHOR_DEPTH = {"rfq": 0.20, "bundling": 0.15, "raw_material": 0.22, "capacity": 0.14, "quality": 0.09}
ANCHOR_DEPTH_BY_GOAL = {"stabilise": 0.035,  # 0.03 in v1.5; 0.035 best offline for P02/P03 (3 sims; 0.04+ worse)
                         "secure_supply": 0.10, "quality_first": 0.09,
                        "leverage": 0.18, "routine": 0.03}
PLAYBOOK_SECTIONS = ("What the goal means here", "Motive", "Tone")
# Qwen benchmark (notes/agent_changelog.md v1.3): it sometimes wrote the supplier's situation as ours
# ("our restructuring", "our pricing committee") or leaked our position ("our target cost") - drop such sentences
BAD_OPENING = re.compile(r"(?i)\bour (current )?(restructuring|survival|pricing committee|committee|target|budget|cost pressure|"
                         r"capacity|liquidity|cash|bank|alternative)|\bwe (must|need to) (prioriti|close|sign)|"
                         r"cost pressures we|we face|line.down|no alternative|urgent|"
                         # live P03 27e05be06bb4181f: "...to your pricing committee ... while maintaining the offered price"
                         # (asks it to keep its price) and "within your existing approval limits" (pulls the decision
                         # back from the committee to the sales person)
                         r"maintain\w* (the |your )?(offered |current |quoted )?price|keep\w* (the |your )?price|"
                         r"within (your|the) (existing |current )?(approval|authority|limits|remit)")

SYSTEM = """You are a senior BUYER at Hollerau Pumpenwerke, a German pump maker, writing to one of
your SUPPLIERS. Write ONLY the opening paragraph of the e-mail: 1-2 sentences that respond to the
supplier's last message and set the tone the PLAYBOOK asks for.
Style - German business culture (the supplier is a German-speaking company):
- Get to the point. Acknowledge their last message in one factual sentence, then state our position.
- Direct and specific. No hedging ("perhaps", "could you explore", "if possible"), no flattery, no small
  talk, no jokes or anecdotes, no emotional appeals - facts over emotions. Respectful and formal.
- Respect their process: acknowledge their approval rules plainly. Never write "without escalation". If
  OUR MOVE asks for escalation, ask them clearly to put our proposal to the committee or manager who can decide.
Rules:
- "We" is always Hollerau, the buyer. Everything under SUPPLIER SITUATION is about THEM (their cash,
  their committee, their capacity, their restructuring) - never describe it as ours.
- Never reveal our position: no targets, budgets, urgency, alternatives or weaknesses.
- Do not mention materials, costs or facts that are not in their e-mail.
- Do NOT write any number, price, percentage, date or data ID - the facts and offers are added
  below your paragraph automatically. No greeting line, no sign-off, no placeholders.
Write in English only.
Reply with the paragraph only."""


def _repo():
    if os.environ.get("NOIDEA_REPO"):
        return Path(os.environ["NOIDEA_REPO"])
    # works from tacto/starter-kit/arena_kit/agents/ and from analysis/agent_variants/
    return next(p for p in Path(__file__).resolve().parents if (p / "datasets" / "A_dossiers.json").exists())


def _sections(text, wanted):
    """The '## ' sections of a playbook whose heading starts with one of `wanted`."""
    out, keep = [], False
    for line in text.splitlines():
        if line.startswith("## "):
            keep = any(line[3:].startswith(w) for w in wanted)
        if keep:
            out.append(line)
    return "\n".join(out)


class NoIdeaAgent:
    def __init__(self, complete=None):
        self.complete = complete
        root = _repo()
        self.dossiers = json.loads((root / "datasets/A_dossiers.json").read_text(encoding="utf-8"))
        self.claims = [json.loads(line) for line in (root / "datasets/C_arguments.jsonl").read_text(encoding="utf-8").splitlines()]
        self.ch = {(c["series"], c.get("window_months")): (c["figure"], c) for c in self.claims if c["kind"] == "index_change"}
        pb = root / "playbooks"
        self.playbooks = {p.stem: p.read_text(encoding="utf-8") for p in pb.glob("*.md")} if pb.exists() else {}
        self.correspondence = root / "tacto/data/correspondence"
        self.facts = json.loads((root / "tacto/data/facts.json").read_text(encoding="utf-8"))
        self._opening_price = None
        # today's price of every part at every supplier (for kit calculations)
        self.part_prices = {}
        for sid, d in self.dossiers.items():
            for p in d.get("parts", []):
                if p.get("current_price"):
                    self.part_prices.setdefault(p["part"], []).append(
                        (sid, p["current_price"], float(p.get("price_unit") or 1), p["description"]))
        self.case_id = None

    # ---- preparation (once per case) --------------------------------------------------------------
    def prepare(self, case, threads):
        b = case["buyer"]
        self.case_id, self.sup, self.cited, self.final_asked = case["case_id"], {}, set(), set()
        alt = b.get("alternative") or {}
        self.c_alt = total_cost(case, alt["terms"]) if (alt.get("terms") or {}).get("unit_price") else math.inf
        part = case["parts"][0]
        for sid, events in threads.items():
            d = self.dossiers.get(sid, {})
            motives = d.get("motives", {})
            std = {**{k: v for k, v in (d.get("standard_terms") or {}).items() if v is not None},
                   **standard_terms(events)}
            std.setdefault("payment_days", b["reference_payment_days"])
            std.setdefault("incoterm", case.get("fixed_terms", {}).get("incoterm", "FCA"))
            pinfo = next((p for p in d.get("parts", []) if p["part"] == part), {})
            justified = sum((dr["weight"] or 0) * self.ch.get((dr["series"], 12), (0.0, None))[0]
                            for dr in pinfo.get("cost_drivers", []))
            open_terms = standing(events)[1]
            cur = b.get("current_unit_price") or open_terms.get("unit_price")
            should = [c for c in self.claims if c["kind"] == "should_cost" and c["part"] == part and c["supplier"] == sid]
            ref = min(x for x in (cur, open_terms.get("unit_price")) if x)  # the quote can be below today's price
            full_cost = min(should[0]["figure"], ref) * 0.94 if should else ref * 0.94
            rate = 0.25 if "cash_short" in motives else 0.14 if "wants_faster_payment" in motives else 0.08
            # central layer: its hidden full cost and cash rate, fitted on the relationship charge of our real deals
            # (P03: EUR 395.30 / 6.1%, P02: EUR 367.60 / 6.6% - both reproduce every c_deal to the cent)
            if (cal := central.calibrated(case["case_id"], sid)):
                full_cost, rate = cal["full_cost"], cal["interest_rate"]
            est = {"standard": std, "interest_rate": rate, "usual_rate": rate if cal else 0.08, "full_cost": full_cost}
            # cloud fix (REGRESSION_FIX.md #2, ported from noidea.py v2.16): a chargeback is cash out at the defect rate it
            # REALLY runs (scorecard ppm), x2 for a cash-short supplier; without this the sheet search treats chargebacks
            # as free, asks the EUR 500 maximum and the supplier prices it in (P11 floor-stop sim 0.99 -> 0.80)
            real_ppm = next((c["figure"] for c in self.claims if c["kind"] == "scorecard_ppm" and c["supplier"] == sid
                             and c.get("figure")), None)
            if real_ppm and "chargeback_eur_per_complaint" in case["negotiable"]:
                est["ppm"] = real_ppm * (2.0 if "cash_short" in motives else 1.0)
            ask_pct = (open_terms["unit_price"] / cur - 1) * 100 if cur and open_terms.get("unit_price") else 0.0
            self._opening_price = open_terms.get("unit_price")
            self.sup[sid] = {"dossier": d, "std": std, "est": est, "justified": justified, "cur": cur, "calibrated": bool(cal),
                             "ask_pct": ask_pct, "open_terms": open_terms,
                             "args": self.rank_args(case, sid, ask_pct),
                             "kit": self.kit_calc(case, sid) if case["type"] == "bundling" else None}
            log.info("prep %s: ask %+.1f%%, justified %+.1f%%, full_cost~%.2f, cash_rate %.2f, motives %s",
                     sid, ask_pct, justified, full_cost, rate, list(motives))

    def rank_args(self, case, sid, ask_pct):
        """Checked claims that help us, best first; each data ID is cited once per case."""
        part = case["parts"][0]
        mine = [c for c in self.claims if c["supplier"] == sid and c["checked_by_arena"]]
        out = [c for c in mine if c["kind"] == "notice_period" and c.get("short_notice")]
        if case["type"] == "quality":
            out += [c for c in mine if c["kind"] == "scorecard_ppm"] + [c for c in mine if c["kind"] == "scorecard_otd"]
        else:  # its quality record as one more verified fact for a later round (taken in P11; untested elsewhere)
            out += [c for c in mine if c["kind"] == "scorecard_ppm"]
        # per driver series: the window (6 or 12 m) with the lower change, if it is below the ask.
        # When the quote is already below today's price (bundles, RFQs, renewals at a cut), the ask is
        # negative and the useful comparison is "no cost push": drivers that moved < 3% (P07 live: the
        # supplier said "our price follows our main cost drivers" and we had cited nothing)
        bar = ask_pct if ask_pct > 0 else 3.0
        parts = set(case["parts"])
        best = {}
        hedged = central.hedged_series(case, self.dossiers.get(sid, {}).get("motives", {}))
        mine = [c for c in mine if not (c["kind"] == "index_change" and c.get("series") in hedged)]
        for c in mine:
            if c["kind"] == "index_change" and c["part"] in parts and c["figure"] < bar and c["figure"] <= 0.0:
                k = c["series"]
                if k not in best or c["figure"] < best[k]["figure"]:
                    best[k] = c
        out += sorted(best.values(), key=lambda c: (c["figure"] - ask_pct) * (c.get("weight") or 0))
        out += [c for c in mine if c["kind"] == "should_cost" and c["part"] in parts
                and c.get("price_vs_should_cost_pct", -1) > 3]
        # flat price history is the argument when there's no increase to fight - but not for kits:
        # P07 live, part-level history "does not change our calculation" for a bundle (kit_calc instead)
        # price increases too, as the LAST item (spread over rounds; live P02 de6192e39dd86084: with no data left in
        # round 4 it went final - "it lacks new verifiable data")
        if case["type"] != "bundling":
            out += [c for c in mine if c["kind"] == "po_prices" and c["part"] in parts]
        if case["type"] in ("capacity", "price_increase"):
            out += [c for c in mine if c["kind"] == "scorecard_otd" and (c["figure"] or 100) < 85]
        # central layer: data suppliers take into account. Live P03 x6: round 1 carried NO checkable claim (every driver
        # rose) and it answered "Which figures is that based on? Please send us the data" (26 such replies in 54 games).
        opening = (self.sup.get(sid) or {}).get("open_terms", {}).get("unit_price") or self._opening_price
        out += central.should_cost_claims(mine, sid, parts, opening)
        out += central.volume_claims(case, self.facts)
        out += central.weak_delivery_claims(mine, sid)
        if central.mirror_supplier(case["case_id"]):  # keep its rounds going with verified facts (P02)
            out = [c for c in out if c["kind"] != "scorecard_otd"] + central.quality_notification_claims(
                case, self.facts, sid) + central.delivery_year_claims(self.facts, sid)
        if not best:  # no falling 6/12-month window: the steepest fall in any window the arena checks
            drivers = {dr["series"]: dr.get("weight") or 0.0 for p in self.dossiers.get(sid, {}).get("parts", [])
                       if p["part"] in parts for dr in p.get("cost_drivers", []) if dr["series"] not in hedged}
            out += central.falling_window_claims(case, drivers)
        # quality notifications on the part (never cited before; cloud ENGINES.md: in 8 of 10 cases)
        if not central.mirror_supplier(case["case_id"]):
            out += central.quality_notification_claims(case, self.facts, sid)
        # a green scorecard is not an argument ("our service levels remain within acceptable parameters", P02/P03/P08)
        out = [c for c in out if not (c["kind"].startswith("scorecard") and c.get("colour") == "green"
                                      and not c.get("keep_alive") and case["type"] != "quality")]
        seen, ranked = set(), []
        for c in central.rank(out, case["case_id"]):
            # a FALL of a cost driver is judged on its own: P08's 5 "does not change" were all on the hedged AS-14404
            falling = c["kind"] == "index_change" and (c.get("figure") or 0) < 0
            if c["sentence"] not in seen and (central.take_rate(c["kind"], case["case_id"]) > 0 or c.get("keep_alive")
                                              or falling):
                seen.add(c["sentence"])
                ranked.append(c)
        return ranked

    def kit_calc(self, case, sid):
        """Bundling: the kit priced at the supplier's OWN current prices, plus today's best price for the
        parts it does not sell us yet. P07 live: verified part-level price history "does not change our
        calculation" for a kit; its final message asked for "the specific data or calculations" behind our
        kit target. Returns None if the kit memo can't be read (e.g. a hidden case without the memo)."""
        doc = case.get("trigger_doc") or ""
        path = self.correspondence / f"{doc.removeprefix('doc:')}.md"
        if not path.exists():
            return None
        lines = re.findall(r"-\s*(\d+)\s*x\s*(.+?)\s*\((part:\d+)\)", path.read_text(encoding="utf-8"))
        if not lines:
            return None
        items, total = [], 0.0
        for qty, desc, part in lines:
            offers = self.part_prices.get(part, [])
            own = [o for o in offers if o[0] == sid]
            src = own[0] if own else (min(offers, key=lambda o: o[1] / o[2]) if offers else None)
            if src is None:
                return None
            unit = src[1] / src[2]
            total += int(qty) * unit
            items.append({"qty": int(qty), "desc": desc.split(",")[0], "part": part, "price": src[1],
                          "per": int(src[2]), "own": bool(own)})
        return {"items": items, "kit_at_own_prices": round(total, 2)}

    def kit_sentence(self, case, sid, ask_price, k):
        kit = self.sup[sid]["kit"]
        if not kit:
            return None
        opening = self.sup[sid]["open_terms"].get("unit_price")
        total = kit["kit_at_own_prices"]
        if k > 0:  # later rounds: restate the result briefly, it asked for the calculation
            return (f"As calculated, your own current prices give EUR {total:.2f} per kit; our offer reflects "
                    f"a fair bundle discount for a multi-year single-source agreement.")
        own = [f"{i['qty']} x {i['desc']} at EUR {i['price']:g}/{i['per']}" for i in kit["items"] if i["own"]]
        new = [f"{i['qty']} x {i['desc']} at today's EUR {i['price']:g}/{i['per']}" for i in kit["items"] if not i["own"]]
        txt = "Our kit calculation: at your own current prices (" + "; ".join(own) + ")"
        if new:
            txt += " plus the part" + ("s" if len(new) > 1 else "") + " you do not supply us yet (" + "; ".join(new) + ")"
        txt += f", the kit costs EUR {total:.2f}."
        if opening and opening < total:
            txt += (f" Your offer of EUR {opening:.2f} is a {(1 - opening / total) * 100:.1f}% bundle discount for the whole kit"
                    f" on a multi-year single-source volume; we consider EUR {ask_price:.2f} a fair kit price.")
        return txt

    def next_args(self, sid, n):
        """The next `n` arguments whose IDs were not cited yet (re-citing reads as padding)."""
        picked = []
        for c in self.sup[sid]["args"]:
            if len(picked) == n:
                break
            # one index claim per e-mail: two or more drew "We received a lot of material" 11 of 11 times
            if c["kind"] == "index_change" and any(x["kind"] == "index_change" for x in picked):
                continue
            if not any(i in self.cited for i in c["ids"]):
                picked.append(c)
        return picked

    # ---- term sheets ---------------------------------------------------------------------------
    def combos(self, case, base):
        opts = case.get("term_options", {})
        fields = [f for f in case["negotiable"] if f != "unit_price" and opts.get(f) and f != "index_clause"]
        for values in itertools.product(*(opts[f] for f in fields)):
            yield {**base, **dict(zip(fields, values))}

    def sheets_at(self, case, sid, value, cap_price=None):
        """The 3 different term sheets that give the supplier `value` per unit at the lowest cost to us."""
        s = self.sup[sid]
        ranked = []
        for t in self.combos(case, dict(s["open_terms"])):
            t = complete_offer(case, {**t, "unit_price": 100.0})
            v1 = supplier_value(case, t, s["est"])
            slope = (supplier_value(case, {**t, "unit_price": 200.0}, s["est"]) - v1) / 100.0
            if slope <= 0:
                continue
            exact = 100.0 + (value - v1) / slope
            # closing: round UP to the cent (never undershoot the value we ask for); otherwise nearest cent
            price = math.ceil(exact * 100 - 1e-6) / 100 if s.get("closing") else exact
            t = complete_offer(case, {**t, "unit_price": price})
            if t["unit_price"] is None or t["unit_price"] <= 0 or not must_haves_ok(case, t, s["std"]):
                continue
            if cap_price and t["unit_price"] > cap_price:  # never above its standing price (P01, score 0)
                continue
            ranked.append((total_cost(case, t, s["std"], s["est"]), t))
        # on a cost tie prefer the LONGER contract: beyond the horizon it "neither costs nor earns" for us
        # (api.md) but is security for the supplier (P07: its final sat at ~EUR 5.50 on 24 m in 4 games)
        # P08 / cloud ENGINES.md: 36 m was priced higher than 24 m (P07, P10) at equal cost to us -> prefer the horizon
        # length; committee suppliers keep the longest (P03: "reflecting the value of the binding 36-month contract")
        horizon = 12 * (case["buyer"].get("horizon_years") or 1)
        longest = central.committee_round1(s["dossier"].get("motives", {}))
        ranked.sort(key=lambda x: (round(x[0], 0), -(x[1].get("contract_months") or 0) if longest
                                   else abs((x[1].get("contract_months") or horizon) - horizon)))
        # approval ladder / price freeze (P03 offline run 1: we cut its EUR 438.21 by 2.7-3.3%, above the 2% its
        # pricing committee allows): among sheets of ~equal cost to us, lead with the smallest headline price cut
        if ranked and {"approval_ladder", "price_frozen"} & set(s["dossier"].get("motives", {})):
            tight = [x for x in ranked if x[0] <= ranked[0][0] * (1 + TIE_BAND)]
            ranked = sorted(tight, key=lambda x: -x[1]["unit_price"]) + ranked[len(tight):]
        out = []
        # the supplier may pick ANY sheet we send: only offer ones we'd be glad to have accepted
        # (offline eval P10: a 12-month sheet at equal supplier value cost us +33% and got picked)
        # cloud fix (REGRESSION_FIX.md #3): alternatives within 0.3% of our best C, not 1%. With chargebacks priced at the
        # real defect rate, P11 filled slot 2 with 800 ppm at the same price: same value to it, +EUR 4.7k to us (0.98 -> 0.93)
        band = ranked[0][0] * ALT_BAND if ranked else 0
        for c, t in ranked:  # 3 genuinely different options: same-cost duplicates waste a slot
            if c > band:
                break
            if all(t != o and abs(c - oc) > 1.0 for oc, o in out):
                out.append((c, t))
            if len(out) == 3:
                break
        return out

    def value_target(self, case, sid, events):
        """Supplier value we ask for this round: calibrated anchor, then reciprocal concession."""
        s = self.sup[sid]
        goal, kind = case["buyer"]["category_goal"], case["type"]
        base = complete_offer(case, s["open_terms"])
        v = lambda price: supplier_value(case, {**base, "unit_price": price}, s["est"])
        opening = s["open_terms"].get("unit_price") or s["cur"]
        depth = ANCHOR_DEPTH.get(kind, ANCHOR_DEPTH_BY_GOAL.get(goal, 0.05))
        if kind in ("price_increase", "renewal") and goal in ANCHOR_DEPTH_BY_GOAL:
            depth = ANCHOR_DEPTH_BY_GOAL[goal]
        # central: a mirroring supplier meets us in the middle (P02 ee98266bedd37231: its cut was ~half our step), so the
        # meeting point follows OUR anchor; its first answer did not depend on the anchor (374.84 for 361.96 and 364.69)
        if central.mirror_supplier(case["case_id"]):
            depth = max(depth, central.MIRROR_ANCHOR)
        anchor_price = opening * (1 - depth)
        if kind == "price_increase":  # the cost-justified change (EDA 3) when it is lower
            anchor_price = min(anchor_price, s["cur"] * (1 + s["justified"] / 100))
        limit_price = s["cur"] * (1 + (s["ask_pct"] - MIN_GAIN_PTS) / 100)
        anchor, limit = v(anchor_price), v(min(limit_price, opening))
        # the relationship charge: never ask below its full cost - a guess. With a calibrated supplier the sheets are
        # ranked by the exact charge instead (P02: real full cost EUR 367.60 vs its EUR 370.96 quote; the guard pinned
        # our ask at 369.51 = 0.51, while 364 @ 60 d scores 0.96 charge included)
        if goal in ("stabilise", "secure_supply") and not s.get("calibrated"):
            anchor = max(anchor, min(s["est"]["full_cost"], limit))
        hist = s.setdefault("ours", [])
        k = len(hist)
        if not hist:
            hist.append(anchor)
            return anchor
        f = min(1.0, k / max(1, PLANNED_ROUNDS - 1)) ** 1.3
        scheduled = anchor + (limit - anchor) * f
        # reciprocity (P07 live: it moved 5.56 -> 5.52 while a fixed schedule took us 5.25 -> 5.43)
        stand = [standing([m])[1] for m in events if m.get("from") != "buyer" and m.get("term_sheets")]
        vals = [supplier_value(case, complete_offer(case, t), s["est"]) for t in stand[-2:]]
        # near-close (P04 live d3050f951dc2c45b: it moved 55% of the gap to our ask, then 5%, then said final_offer
        # at that price while we still asked ~1% lower - 0.86; one cent lower on the right payment term: 0.94-0.98).
        # Stall = its last move, as a share of the gap to our ask, collapsed (< STALL_DROP x its previous share, or
        # < STALL_MIN): a steady mover (offline_eval: 30% or 10% every round) is not at its floor yet.
        sv = [supplier_value(case, complete_offer(case, t), s["est"]) for t in stand]
        fr = [(sv[j - 1] - sv[j]) / (sv[j - 1] - hist[j - 1]) for j in range(1, min(len(sv), len(hist) + 1))
              if sv[j - 1] - hist[j - 1] > 1e-9]
        # a big move UP (it switched to a structure worth more to it) is not a stall (offline_eval stubborn P04: 0.98 -> 0.37)
        stalled = len(fr) >= 2 and fr[-1] > -STALL_NOISE and fr[-2] > 0 and (fr[-1] < STALL_DROP * fr[-2] or fr[-1] < STALL_MIN)
        if stalled and sv[-1] - hist[-1] <= CLOSE_GAP * sv[-1]:
            s["closing"] = True
            hist.append(max(hist[-1], min(sv[-2:]) * (1 - CLOSE_STEP)))
            return hist[-1]
        theirs = max(0.0, vals[0] - vals[1]) if len(vals) == 2 else (limit - anchor) / PLANNED_ROUNDS
        step = min(scheduled - hist[-1], max(theirs, (limit - anchor) / (2 * PLANNED_ROUNDS)))
        # central: a mirroring supplier answers our step with its own - step a share of the remaining gap, but stay a
        # near-close below its standing value (the deal is its price; our ask only has to pull it down)
        # cloud fix (REGRESSION_FIX.md #4): keep stepping big only while it answers in kind. From our 3rd ask on, if its
        # last step was < 0.3x our last step (in value), it is not mirroring here: back to the schedule. Round 2 (the P02
        # recipe) is unchanged; a non-mirroring supplier now costs at most one big step.
        answered = True
        if len(hist) >= 2 and len(sv) >= 2 and hist[-1] - hist[-2] > 1e-9:
            answered = (sv[-2] - sv[-1]) >= 0.3 * (hist[-1] - hist[-2])
        if sv and answered and (central.mirror_supplier(case["case_id"]) or central.MIRROR.search(latest(events).get("body") or "")):
            gap = sv[-1] - hist[-1]
            step = max(step, central.MIRROR_SHARE * gap)
            hist.append(min(limit, hist[-1] + max(0.0, min(step, gap - sv[-1] * CLOSE_STEP))))
            return hist[-1]
        hist.append(min(limit, hist[-1] + max(0.0, step)))
        return hist[-1]

    # ---- the move ------------------------------------------------------------------------------
    def decide(self, case, threads):
        if case["case_id"] != self.case_id:
            self.prepare(case, threads)
        self.threads_ref = threads
        live = [s for s in live_threads(threads) if s in self.sup]
        # talk to the supplier whose thread is furthest behind (RFQ round-robin)
        sid = min(live, key=lambda s: sum(m.get("from") == "buyer" for m in threads[s]))
        # cloud fix (REGRESSION_FIX.md #1, ported from noidea.py v2.9): in an RFQ a bidder that says agreed / final_offer
        # is handled first, the cheapest of them - not whoever's turn it is (live P05 f8604d43d3fbf92f accepted the
        # dearest bid; floor-stop sim P05 0.76 -> 0.00: an agreed bidder was never answered)
        if len(live) > 1:
            closing = [x for x in live if latest(threads[x]).get("status") in ("agreed", "final_offer")]
            if closing:
                cs = {x: self.best_sheet(case, x, threads[x]) for x in live}
                cost = {x: total_cost(case, cs[x][1], self.sup[x]["std"], self.sup[x]["est"]) if cs[x][0] else math.inf
                        for x in live}
                best = min(closing, key=lambda x: cost[x])
                if cost[best] <= min(cost.values()) + 1:
                    sid = best
        events, s = threads[sid], self.sup[sid]
        sheet_id, terms = self.best_sheet(case, sid, events)
        status = latest(events).get("status")
        k = sum(m.get("from") == "buyer" and bool(m.get("term_sheets")) for m in events)
        c_stand = total_cost(case, terms, s["std"], s["est"]) if sheet_id else math.inf
        ok = bool(sheet_id) and must_haves_ok(case, terms, s["std"]) and c_stand < self.c_alt
        accept = {"supplier_id": sid, "message": {"action": {"type": "accept", "term_sheet_id": sheet_id}}}
        walk = {"supplier_id": sid, "message": {"action": {"type": "walk_away"}}}
        best_elsewhere = min(self.best_standing(case, threads, skip=sid))

        if status == "agreed" and ok and c_stand <= best_elsewhere:
            return accept
        if status == "final_offer" or moves_left(case, events) <= 1 or k >= PLANNED_ROUNDS + 1:
            if not ok:
                return walk if self.c_alt < math.inf or len(live) > 1 else accept if sheet_id else walk
            # final_offer = its last word: ACCEPT. P07 v1.3 live (c5d845883158676c): one "small" extra ask
            # (90 instead of 30 payment days at its EUR 5.40) made it walk away -> no deal, 0.12 instead of ~0.73.
            # The brief warns: "final_offer: push further and it may walk". final_tweak() is kept but unused.
            if c_stand <= best_elsewhere:
                return accept
        # escalation (live P03 fef482f41a6e1e8f, 0.86): after one 2% move the KAM said "60 days net already represents
        # the maximum extension available within our authority" / "base prices strictly fixed", and we kept asking
        # "within your approval authority, without escalation" until its final_offer. Ask once - before any
        # final_offer - for its best non-price lever at its own price, to be put to its committee.
        motives = set(s["dossier"].get("motives", {}))
        # its answer to our escalation (management / committee): take it if it beats what stood before. Live P03
        # 47a88b4d0bb75ce3: management offered EUR 433.08 @ 90 d (0.90); we near-closed on 60/45/30 d, it reverted
        # to EUR 431.61 @ 60 d final (0.86)
        if s.get("escalated") and s.get("pre_escalation_c") and ok and c_stand < s.pop("pre_escalation_c") - 1:
            log.info("%s: escalation answered (C %.0f) - accepting", sid, c_stand)
            return accept
        if (status == "open" and k >= 1 and ok and not s.get("escalated") and moves_left(case, events) > 2
                and {"approval_ladder", "price_frozen"} & motives
                and (LIMIT_HIT.search(latest(events).get("body") or "") or self.price_held(events))):
            esc = self.escalation_sheets(case, sid, terms, c_stand)
            if esc:
                s["escalated"] = s["escalate_now"] = True
                s["pre_escalation_c"] = c_stand
                log.info("%s escalation: %s", sid, [(t["unit_price"], t.get("payment_days")) for t in esc])
                return self.message(case, sid, events, esc, k)
        cap = terms.get("unit_price") if sheet_id else None
        sheets = self.sheets_at(case, sid, self.value_target(case, sid, events), cap)
        if not sheets:
            return accept if ok else walk
        committee = central.committee_round1(motives)
        if central.FULL_AUTHORITY.search(latest(events).get("body") or "") or central.full_authority(case["case_id"]):
            s["no_committee"] = True
            s.pop("committee_sent", None)
        # central: while unused verified data remains, keep the round going - no near-close, no early accept. Live P03
        # d1bfa5a91489432b: copper data in round 2 cut its price again (432.54 -> 432.49); P03 never moved in a later
        # round WITHOUT data (12 games)
        if status == "open" and k >= 1 and moves_left(case, events) > 2 and self.next_args(sid, 1):
            if s.pop("closing", False):
                log.info("%s: data left - no near-close yet", sid)
            if ok and c_stand <= sheets[0][0] * 1.0005:
                return accept
            out = [t for _, t in sheets]
            if sheet_id and case["type"] != "rfq":  # stay on the structure it priced
                out = [t for t in out if central.same_structure(t, terms)][:1] or out[:1]
            log.info("%s round %d: new data + step %s", sid, k, [(t["unit_price"], t.get("payment_days")) for t in out])
            return self.message(case, sid, events, out, k)
        # central: management escalation, once, when the data is used up and it signals its own limit (P02
        # ee98266bedd37231: "our best effort ... without requiring management escalation", then we near-closed without
        # data and it went final at 368.55). A real step (half the gap), on the structure it priced, to its management.
        if (status == "open" and k >= 1 and ok and not s.get("mgmt_escalated") and moves_left(case, events) > 1
                and central.ESCALATION_HINT.search(latest(events).get("body") or "")):
            s.pop("closing", None)
            hist = s.get("ours") or []
            v_now = supplier_value(case, complete_offer(case, terms), s["est"])
            if len(hist) >= 2 and v_now > hist[-2]:
                hist[-1] = hist[-2] + central.MIRROR_SHARE * (v_now - hist[-2])
            esc = self.sheets_at(case, sid, hist[-1] if hist else v_now, cap)
            out = [t for _, t in esc if central.same_structure(t, terms)][:1] or [t for _, t in esc][:1]
            if out:
                s["mgmt_escalated"] = s["mgmt_now"] = True
                log.info("%s round %d: management escalation %s", sid, k, [(t["unit_price"], t.get("payment_days")) for t in out])
                return self.message(case, sid, events, out, k)
        # central 3c: once it priced our lead structure, stay on it (P03 47a88b4d0bb75ce3: management gave 433.08 @ 90 d,
        # we asked 60/45/30 d and its final fell back to 431.61 @ 60 d: 0.90 -> 0.86)
        # P08 cloud: switching structure drew "hold" (1f27ac1b2856c285); payment days were neutral for it
        if k >= 1 and sheet_id and case["type"] != "rfq":
            same = [x for x in sheets if central.same_structure(x[1], terms)]
            if same and same[0][0] <= sheets[0][0] * 1.003:
                sheets = same
        # accept when the supplier meets our current ask, or when we are within 0.3% late in the game
        if ok and k > 0 and c_stand <= best_elsewhere and not s.get("closing") and (
                c_stand <= sheets[0][0] * 1.0005 or (k >= PLANNED_ROUNDS - 2 and c_stand <= sheets[0][0] * 1.003)):
            return accept
        log.info("%s round %d: our best C %.0f vs standing %.0f (alt %.0f)", sid, k, sheets[0][0], c_stand, self.c_alt)
        if s.pop("closing", False):
            if ok and sheets[0][0] >= c_stand - 1:  # the closing ask is no better than what stands: take it
                return accept
            # one near-close only: the second one was a 1-cent "nominal adjustment" (live P03 2e4bf89ac2967a45: "a nominal
            # adjustment does not enable us to further reduce our price") - take what stands instead
            if ok and s.get("near_closed") and c_stand <= best_elsewhere:
                return accept
            s["near_closed"] = True
            # it may pick any sheet: only offer ones within a quarter of the remaining gain
            band = sheets[0][0] + 0.25 * max(0.0, c_stand - sheets[0][0])
            sheets = [x for x in sheets if x[0] <= band]
            log.info("%s near-close: %s", sid, [(t["unit_price"], t.get("payment_days")) for _, t in sheets])
        out = [t for _, t in sheets]
        # central 3b: approval ladder -> put ONE structure to its committee in round 1 (Dhruv's v2.7 P03 game
        # 8c2816f2d571b367 got the committee's 90-day price in round 1, the best first answer in 7 P03 games; with 3
        # sheets its KAM picked 60 d and stopped at its 2% limit in all 6 of ours)
        if committee and k == 0:
            out = out[:1]
            if not s.get("no_committee"):
                s["escalate_now"] = s["committee_r1"] = s["committee_sent"] = True
            log.info("%s round 1 to the committee: %s", sid, [(t["unit_price"], t.get("payment_days")) for t in out])
        alt_prose = self.prose_alternative(case, sid, events)
        # only when it is near our ask or late in the game: it may pick any sheet (P10 lesson),
        # so an early far-off prose offer in our sheets would just be accepting its number
        if alt_prose and alt_prose[1] not in out and (alt_prose[0] <= sheets[0][0] * 1.01 or k >= PLANNED_ROUNDS - 3):
            # its own prose offer as a binding option: it can simply agree to what it proposed
            out = out[:2] + [alt_prose[1]]
        return self.message(case, sid, events, out, k)

    @staticmethod
    def price_held(events):
        """Its standing price did not move between its last two replies (after we asked for more)."""
        prices = [(m.get("term_sheets") or [{}])[0].get("terms", {}).get("unit_price")
                  for m in events if m.get("from") != "buyer" and m.get("term_sheets")]
        return len(prices) >= 3 and prices[-1] is not None and abs(prices[-1] - prices[-2]) < 0.005

    def best_sheet(self, case, sid, events):
        """Its standing term sheet that is cheapest for us. Live P03: it offered two each round (EUR 431.61 @ 60 d
        AND 430.88 @ 45 d); v1.5 only looked at the first."""
        s = self.sup[sid]
        sheets = latest(events).get("term_sheets") or []
        if not sheets:
            return None, {}
        ok = [x for x in sheets if must_haves_ok(case, x["terms"], s["std"])] or sheets
        best = min(ok, key=lambda x: total_cost(case, x["terms"], s["std"], s["est"]))
        return best["term_sheet_id"], best["terms"]

    def escalation_sheets(self, case, sid, terms, c_stand):
        """Its own price with the best non-price lever (needs its committee), and the same lever with a little of
        its cash loss paid back - only sheets clearly cheaper for us than its standing one."""
        s = self.sup[sid]
        tweak = self.final_tweak(case, sid, terms)
        if not tweak:
            return None
        v = lambda t: supplier_value(case, t, s["est"])  # noqa: E731
        loss = v(complete_offer(case, terms)) - v(tweak)
        out = [tweak]
        if loss > 0:
            slope = v({**tweak, "unit_price": tweak["unit_price"] + 1.0}) - v(tweak)
            for share in ESCALATE_GIVEBACK:
                t = complete_offer(case, {**tweak, "unit_price": round(tweak["unit_price"] + share * loss / slope, 2)})
                if t not in out:
                    out.append(t)
        # "edge" sheet: its approval threshold on its own quote, priced onto our best payment term with ITS per-day
        # payment pricing (live P03 x5: +EUR 0.049 per day = 4.1% a year, half our 8%; its KAM gave 1.84%, limit 2%)
        if (edge := self.edge_sheet(case, sid, tweak)) is not None and edge not in out:
            out.append(edge)
        # its "frozen" base price sits above today's price (P03: EUR 431.61 vs 412.74): offer its own structure
        # 1% lower too - a frozen price argues for today's price, not for an increase
        if self.freeze_gap(sid, terms) > 0:
            t = complete_offer(case, {**terms, "unit_price": round(max(s["cur"], terms["unit_price"] * (1 - FREEZE_CUT)), 2)})
            if t not in out:
                out.append(t)
        gain = c_stand - total_cost(case, tweak, s["std"], s["est"])
        return [t for t in out if c_stand - total_cost(case, t, s["std"], s["est"]) >= 0.4 * gain][:3]

    def payment_slope(self, case, sid):
        """EUR per payment day in its own offers: two of its sheets that differ only in price and payment days."""
        events = self.threads_ref.get(sid, [])
        pts = {}
        for m in events:
            if m.get("from") == "buyer":
                continue
            for x in m.get("term_sheets") or []:
                t = x["terms"]
                key = tuple(sorted((k, json.dumps(v)) for k, v in t.items() if k not in ("unit_price", "payment_days")))
                if t.get("payment_days") is not None and t.get("unit_price"):
                    pts.setdefault(key, {})[t["payment_days"]] = t["unit_price"]
        best = None
        for by_day in pts.values():
            if len(by_day) >= 2:
                d0, d1 = min(by_day), max(by_day)
                slope = (by_day[d1] - by_day[d0]) / (d1 - d0)
                if slope > 0 and (best is None or d1 - d0 > best[1]):
                    best = (slope, d1 - d0)
        return best[0] if best else None

    def approval_threshold(self, sid):
        """'price changes above 2 % need the approval of their pricing committee' -> 0.02 (None if not stated)."""
        s = self.sup[sid]
        for doc in s["dossier"].get("motives", {}).get("approval_ladder", {}).get("evidence", []):
            path = self.correspondence / f"{doc.removeprefix('doc:')}.md"
            if path.exists() and (m := re.search(r"above (\d+(?:[.,]\d+)?)\s?%", path.read_text(encoding="utf-8"))):
                return float(m.group(1).replace(",", ".")) / 100
        return None

    def edge_sheet(self, case, sid, tweak):
        """Our best structure at its approval threshold (+EDGE_PLUS) on its opening quote, via its payment pricing."""
        s = self.sup[sid]
        slope, thr = self.payment_slope(case, sid), self.approval_threshold(sid)
        o = s["open_terms"]
        d_std = o.get("payment_days") or s["std"].get("payment_days")
        if not (slope and thr and o.get("unit_price") and d_std and tweak.get("payment_days")):
            return None
        base = o["unit_price"] * (1 - thr - EDGE_PLUS)
        price = round(base + slope * (tweak["payment_days"] - d_std), 2)
        s["edge_note"] = (o["unit_price"], d_std, slope, thr, base, price, tweak["payment_days"])
        return complete_offer(case, {**tweak, "unit_price": price})

    def freeze_gap(self, sid, terms):
        """% its standing price sits above today's price when its motives say prices are frozen (else 0)."""
        s = self.sup[sid]
        if "price_frozen" not in s["dossier"].get("motives", {}) or not s["cur"] or not terms.get("unit_price"):
            return 0.0
        return max(0.0, (terms["unit_price"] / s["cur"] - 1) * 100)

    def final_tweak(self, case, sid, terms):
        """Its final offer with the one non-price option that helps us most (same price)."""
        s, best = self.sup[sid], None
        base = complete_offer(case, terms)
        c0 = total_cost(case, base, s["std"], s["est"])
        for f in case["negotiable"]:
            for o in case.get("term_options", {}).get(f, []):
                if f in ("unit_price", "index_clause") or o == base.get(f):
                    continue
                t = complete_offer(case, {**base, f: o})
                if must_haves_ok(case, t, s["std"]) and (c := total_cost(case, t, s["std"], s["est"])) < c0 - 1:
                    if best is None or c < best[0]:
                        best = (c, t)
        return best[1] if best else None

    MONTHS = {m: i for i, m in enumerate(["january", "february", "march", "april", "may", "june", "july",
                                          "august", "september", "october", "november", "december"], 1)}

    def prose_alternative(self, case, sid, events):
        """Signal 'prose_alternative' (src/eval/signals.py; P01 live: "Alternatively, with valid from
        ... January ...: EUR ... per unit"). Only term sheets bind, so turn it into one. Returns
        (C, terms) if it is cheaper for us than its standing sheet."""
        body = latest(events).get("body") or ""
        s = self.sup[sid]
        _, terms = standing(events)
        best = None
        for sent in re.split(r"(?<=[.!?])\s+|\n+", body):
            if not re.search(r"(?i)\balternativ", sent):
                continue
            price = re.search(r"(?:€|EUR)\s?([\d]+(?:[.,]\d+)?)|([\d]+(?:[.,]\d+)?)\s?(?:€|EUR)?\s?per unit", sent)
            if not price:
                continue
            t = dict(terms, unit_price=float((price.group(1) or price.group(2)).replace(",", ".")))
            iso = re.search(r"\d{4}-\d{2}-\d{2}", sent)
            word = re.search(r"(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", sent)
            if iso:
                t["effective_date"] = iso.group(0)
            elif word and word.group(2).lower() in self.MONTHS:
                t["effective_date"] = f"{word.group(3)}-{self.MONTHS[word.group(2).lower()]:02d}-{int(word.group(1)):02d}"
            if (days := re.search(r"(\d{1,3})\s*(?:-\s*)?(?:days|Tage)", sent)):
                t["payment_days"] = int(days.group(1))
            t = complete_offer(case, t)
            if must_haves_ok(case, t, s["std"]):
                c = total_cost(case, t, s["std"], s["est"])
                if best is None or c < best[0]:
                    best = (c, t)
        if best and best[0] < total_cost(case, terms, s["std"], s["est"]) - 1:
            log.info("%s: prose alternative %s is cheaper - putting it in a term sheet", sid, best[1])
            return best
        return None

    def best_standing(self, case, threads, skip=None):
        out = [math.inf]
        for sid in live_threads(threads):
            if sid in self.sup and sid != skip:
                sh, t = self.best_sheet(case, sid, threads[sid])
                if sh:
                    out.append(total_cost(case, t, self.sup[sid]["std"], self.sup[sid]["est"]))
        return out

    # ---- the words -----------------------------------------------------------------------------
    def message(self, case, sid, events, sheets, k, final=False):
        # later rounds: up to 2 NEW data kinds - live P03 2e4bf89ac2967a45: a counter without data got "Which figures
        # is that based on? Please send us the data", and P03 never moved in a later round without data (12 games)
        # spread the data: P02/P03 cut their price for each NEW fact and went final once none was left - so keep one
        # fact for each of the next 3 rounds and send 1 per later round
        left = sum(not any(i in self.cited for i in c["ids"]) for c in self.sup[sid]["args"])
        reserve = 4 if central.mirror_supplier(case["case_id"]) else 3  # a mirroring supplier cuts in every data round
        if (fa := central.final_at(case["case_id"])):  # it goes final at our fa-th message: all data must land by then
            reserve = min(reserve, max(0, fa - 1))
        # round 1 does most of the work (P03: the committee priced round 1's data; P08 goes final at our 3rd message):
        # up to 3 facts; only a mirroring supplier (cuts in every data round) keeps more back for later rounds
        first = max(2, min(3, left - reserve)) if central.mirror_supplier(case["case_id"]) else min(3, left)
        args = self.next_args(sid, first if k == 0 else 1)
        s = self.sup[sid]
        if s.get("escalate_now") and not s.get("committee_r1") and (gap := self.freeze_gap(sid, self.best_sheet(case, sid, events)[1])) > 0:
            # live P03 x4: "our base prices are strictly frozen" while charging +4.6% on today's EUR 412.74.
            # Use its own words: a freeze means today's price continues. Our order prices back it (checked claim).
            po = [c for c in self.claims if c["supplier"] == sid and c["kind"] == "po_prices"
                  and c["part"] in case["parts"] and not any(i in self.cited for i in c["ids"])]
            args = po[:1] + [c for c in args if c not in po][:1]
            s["freeze_note"] = (f"You write that your base prices are frozen. Our current price is EUR {s['cur']:.2f}; "
                                f"EUR {self.best_sheet(case, sid, events)[1]['unit_price']:.2f} is an increase of "
                                f"{gap:.1f}% on it. Under a price freeze we would expect today's price to continue - our "
                                f"proposal already accepts most of that increase.")
        rival = self.rival_offer(case, sid) if case["type"] == "rfq" else None
        refs = sorted({i for c in args for i in c["ids"]} | ({rival[0]} if rival else set()))
        self.cited.update(refs)
        msg = {"subject": f"Re: {case['title']}"[:300],
               "body": self.write(case, sid, events, sheets, k, [c["sentence"] for c in args], rival, final),
               "term_sheets": [{"terms": t} for t in sheets],
               "refs": refs[:20]}
        if (att := self.call_off(case, sid, events, sheets, k)):
            msg["attachments"] = [att]
            msg["body"] = msg["body"].replace("\n\nKind regards", "\n\nAttached: our monthly call-off schedule for the "
                                              "full contract term.\n\nKind regards")
        return {"supplier_id": sid, "message": msg}

    def call_off(self, case, sid, events, sheets, k):
        """A monthly call-off schedule (CSV, the arena reads csv attachments). Live P07 x5: "Which volume can you
        commit to?" / "please provide a firm release schedule" every round, never answered with data; P03's
        renewal e-mail asks "Please let us know your expected volumes". Sent in round 1, and again when asked."""
        s = self.sup[sid]
        asked = re.search(r"(?i)release schedule|call-?off|which volume|expected volume|volume figures|"
                          r"documentation supporting", latest(events).get("body") or "")
        if s.get("schedule_sent") and not asked or (k > 0 and not asked):
            return None
        t0 = {**case.get("fixed_terms", {}), **sheets[0]}
        vol = t0.get("volume_per_year") or case["buyer"]["need_per_year"]
        months = min(int(t0.get("contract_months") or 12) or 12, 36)
        start = t0.get("effective_date") or min(case.get("term_options", {}).get("effective_date") or ["2027-01-01"])
        y, m = int(start[:4]), int(start[5:7])
        rows, left = ["month,quantity"], vol * months // 12
        for i in range(months):
            q = round(vol / 12) if i < months - 1 else left
            left -= q
            rows.append(f"{y + (m - 1 + i) // 12}-{(m - 1 + i) % 12 + 1:02d},{q}")
        s["schedule_sent"] = True
        import base64
        return {"name": "call_off_schedule.csv", "type": "csv",
                "content_b64": base64.b64encode(("\n".join(rows) + "\n").encode()).decode()}

    def rival_offer(self, case, sid):
        """RFQ: the best competing standing offer, citable once per supplier (playbooks/rfq.md)."""
        best = None
        for other, s in self.sup.items():
            if other == sid or other not in self.threads_ref:
                continue
            sh, t = standing(self.threads_ref[other])
            if sh and t.get("unit_price") and must_haves_ok(case, t, s["std"]):
                if best is None or t["unit_price"] < best[1]:
                    best = (sh, t["unit_price"])
        if best and (sid, best[0]) not in self.cited:
            self.cited.add((sid, best[0]))
            return best
        return None

    @staticmethod
    def say(field, v):
        """A term in words (Tacto: write as to a person; v1.5 sent "index_clause None, payment_days 14")."""
        if field == "unit_price":
            return f"EUR {v:,.2f} per unit"
        if field == "index_clause":
            return "no price-adjustment clause" if not v else (
                f"{v['series']} price-adjustment clause ({v['material_share'] * 100:.0f}% material share, "
                f"{v['deadband_pct']:g}% deadband)")
        fmt = {"payment_days": "{} days net", "contract_months": "{}-month contract",
               "volume_per_year": "{:,} units per year", "lead_time_days": "{} days lead time",
               "effective_date": "valid from {}", "ppm_commitment": "{:,} ppm quality commitment",
               "chargeback_eur_per_complaint": "EUR {:,.0f} chargeback per complaint", "incoterm": "{}",
               "tooling_eur": "EUR {:,.0f} tooling"}.get(field)
        try:  # format only this field (P01: a date through "{:,}" crashed the e-mail)
            return fmt.format(v) if fmt else f"{field} {v}"
        except (ValueError, TypeError):
            return f"{field} {v}"

    NAME = re.compile(r"^[A-ZÄÖÜÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][\w'’-]+(?: [A-ZÄÖÜÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][\w'’-]+){1,3}$")

    def contact(self, events):
        """The person who signed its latest e-mail ("Birgit Mayrhofer" above "Key Account Manager, Selvbrunn ...")."""
        for m in reversed(events):
            if m.get("from") == "buyer":
                continue
            lines = [x.strip() for x in (m.get("body") or "").splitlines() if x.strip()]
            if len(lines) >= 2 and "," in lines[-1] and self.NAME.match(lines[-2]):
                return lines[-2]
        return None

    def write(self, case, sid, events, sheets, k, args, rival, final):
        s = self.sup[sid]
        d = s["dossier"]
        name = d.get("name", "your company")
        motives = d.get("motives", {})
        offers = "; ".join((f"option {chr(65 + i)}: " if len(sheets) > 1 else "") + ", ".join(
            self.say(f, v) for f, v in t.items() if f in case["negotiable"]) for i, t in enumerate(sheets))
        opening = "Thank you for your message."
        if self.complete:
            levers = "; ".join(f"{m}: {v['lever']}" for m, v in motives.items() if k == 0 or m != "open_book")
            playbook = _sections(self.playbooks.get(case["type"], ""), PLAYBOOK_SECTIONS)[:2500]
            user = (f"SUPPLIER: {name}\nCASE: {case['title']} ({case['type']}, goal {case['buyer']['category_goal']})\n"
                    f"ROUND: {k + 1}{' (its final offer - make one last small request, then we close)' if final else ''}\n"
                    + ("OUR MOVE: we make a clear step towards them; ask them plainly to take our proposal to their "
                       "management for a decision, since they said further movement needs management.\n"
                       if s.get("mgmt_now") else
                       "OUR MOVE: our price proposal is above what their key account manager may approve alone - ask "
                       "them plainly to put OUR PRICE to their pricing committee for approval. Never suggest they keep "
                       "or maintain their price.\n" if s.get("committee_r1") else
                       "OUR MOVE: their pricing committee has already reviewed our proposal - ask them to take our revised "
                       "price back to the committee. Never mention their own approval limits.\n"
                       if s.get("committee_sent") and not s.get("escalate_now") else
                       "OUR MOVE: we keep their price and ask for a longer payment term / their best non-price term, "
                       "which needs their committee or management - ask them to put it to them.\n"
                       if s.get("escalate_now") else "")
                    + f"SUPPLIER SITUATION (about THEM, not us) and how we respond: {levers or 'n/a'}\n"
                    f"PLAYBOOK (our negotiation guidance):\n{playbook}\n"
                    f"THEIR LAST E-MAIL:\n{latest(events).get('body', '')[:900]}\n")
            try:
                text = " ".join(self.complete(SYSTEM, user).split())
                # the model must not carry figures (those come from code and are checked)
                text = " ".join(x for x in re.split(r"(?<=[.!?])\s+", text)
                                if not any(ch.isdigit() for ch in x) and not BAD_OPENING.search(x))
                if 30 < len(text) < 700:
                    opening = text
                else:
                    log.warning("LLM paragraph rejected (len %d)", len(text))
            except Exception as e:  # a slow or broken model must not cost the round
                log.warning("LLM failed (%s) - plain opening used", e)
        t0 = {**case.get("fixed_terms", {}), **sheets[0]}
        vol, months = t0.get("volume_per_year") or case["buyer"]["need_per_year"], t0.get("contract_months")
        unit = "kits" if case["type"] == "bundling" else "units"
        # German business style (negotiationacademy.com, how-to-negotiate-with-germans): a clear agenda, specific and
        # measurable, evidence, risks addressed upfront, no details left open. Numbered sections; figures from code.
        total = vol * months // 12 if months else vol
        sec1 = f"Volume and term: we confirm a binding volume of {vol:,} {unit} per year" + (
            f" for {months} months, {total:,} {unit} in total." if months else ".")
        p0 = sheets[0].get("unit_price")
        worth = f" about EUR {p0 * total:,.0f} over the term." if p0 else ""
        sec2 = f"Our proposal: {offers}." + (
            (f" Option A amounts to{worth}" if len(sheets) > 1 else f" This amounts to{worth}") if worth else "")
        basis = []
        if case["type"] == "bundling":
            if k == 0:
                basis.append("We want one partner for the complete kit, which bundles parts we buy from several suppliers today.")
            if (kit := self.kit_sentence(case, sid, sheets[0]["unit_price"], k)):
                basis.append(kit)
        # how big the deal is for it (needs-volume suppliers; P07: the kit is ~4x our business with it)
        spend = (d.get("spend_by_fy") or [[None, 0]])[-1][1]
        deal = vol * (s["cur"] or 0)
        if spend and deal > 1.5 * spend and ({"needs_volume", "bundle", "wants_commitment"} & set(motives)):
            basis.append(f"That is about EUR {deal:,.0f} a year, around {deal / spend:.0f} times our current business with you.")
        if rival:
            basis.append(f"We have an offer at EUR {rival[1]:.2f} per unit ({rival[0]}).")
        # its own recent quote for this part, in words (cloud P08_engine.md: EUR 5.45 on 2026-09-10 vs its 6.05 opening)
        if k == 0 and (oq := central.own_quote_note(self.facts, sid, set(case["parts"]), s["open_terms"].get("unit_price"))):
            basis.insert(0, oq)
        basis += args
        nxt = []
        # ask once: skip if the LLM paragraph already asked (P04 offline: it was asked twice in one e-mail)
        if k == 0 and "open_book" in motives and not re.search(r"(?i)breakdown|calculation|xlsx", opening):
            what = "the kit" if case["type"] == "bundling" else "this part"
            nxt.append(f"Please send us your cost breakdown for {what}.")
        if k == 0 and case["type"] == "quality":
            nxt.append("Please send us your 8D report and a binding ppm commitment.")
        if k == 0 and "we_pay_late" in motives:
            nxt.append("We have put our invoice processing in order and will pay on the agreed due date.")
        if (note := s.pop("freeze_note", None)):
            basis.insert(0, note)
        if (e := s.pop("edge_note", None)) and any(abs(t.get("unit_price", 0) - e[5]) < 0.005 for t in sheets):
            op, d0, slope, thr, base, price, d1 = e
            basis.insert(0, f"Your own offers price payment terms at EUR {slope:.3f} per day. At that rate EUR {price:.2f} "
                            f"at {d1} days equals EUR {base:.2f} at your standard {d0} days - {(1 - base / op) * 100:.2f}% "
                            f"below your quote of EUR {op:.2f}, at your {thr * 100:g}% approval threshold. So far the "
                            f"concession is {(1 - (self.best_sheet(case, sid, events)[1]['unit_price'] - slope * (self.best_sheet(case, sid, events)[1].get('payment_days', d0) - d0)) / op) * 100:.2f}%.")
        if s.pop("mgmt_now", False) and total and p0:
            nxt.append(f"We have made a clear step towards you. Please take this proposal to your management for a decision: "
                       f"a binding {months or 12}-month agreement for {total:,} {unit}, about EUR {p0 * total:,.0f}. On "
                       f"your written confirmation we issue the order the same day and pay every invoice on the due date.")
        if s.pop("committee_r1", False) and total and p0:
            s.pop("escalate_now", None)
            thr = self.approval_threshold(sid)
            nxt.append((f"You told us that price changes above {thr * 100:g}% need your pricing committee. " if thr else "")
                       + f"Please put this proposal to your pricing committee: a binding {months or 12}-month agreement "
                       f"for {total:,} {unit}, about EUR {p0 * total:,.0f}. On the committee's written confirmation we "
                       f"issue the order the same day, and we pay every invoice on the due date.")
        if s.pop("escalate_now", False) and total and p0:
            nxt.append(f"We ask you to put this proposal to your pricing committee: a binding {months or 12}-month "
                       f"agreement for {total:,} {unit}, about EUR {p0 * total:,.0f}, justifies a decision beyond the "
                       f"standard approval limit. Your base price stays unchanged in option A. On your confirmation of "
                       f"any option we confirm the order in writing the same day, and we pay every invoice on the due "
                       f"date - no further rounds.")
        if not any("committee's written confirmation" in x or "management for a decision" in x for x in nxt):
            nxt.append("All other terms as in your quote; on your written confirmation of "
                       + ("one option" if len(sheets) > 1 else "these terms") + " we will issue the order.")
        if final:
            body = "As our final step, we can accept your offer with this one change (attached)."
        else:
            parts = [sec1, sec2] + ([" ".join(basis)] if basis else []) + [" ".join(nxt)]
            labels = ["", "", "Basis: ", "Next step: "] if basis else ["", "", "Next step: "]
            body = "\n".join(f"{i}. {lab}{txt}" for i, (lab, txt) in enumerate(zip(labels, parts), 1))
        who = self.contact(events)
        greet = f"Dear {who}," if who else f"Dear {name} team,"
        return f"{greet}\n\n{opening}\n\n{body}\n\nKind regards,\nPurchasing, Hollerau Pumpenwerke"
