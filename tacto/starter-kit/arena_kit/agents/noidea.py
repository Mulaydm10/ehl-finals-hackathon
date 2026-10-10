"""Team NoIdea buyer v1: code sets every number, the language model only writes the e-mail.

Numbers come from the EDA (docs/EDA_FINDINGS.md) and datasets A/C (datasets/):
  - target: the cost-justified change (cost-driver weights x 12-month index moves), never worse
    than "ask - 1 pt"; past suppliers settled 1-4 pts below their ask
  - the supplier: cost floor from should-cost, cash rate from its motives (a cash-short supplier
    values faster payment more, so payment-for-price trades do not squeeze it)
  - term sheets: every combination of the negotiable options, priced so the supplier gets a target
    value, ranked by OUR total cost incl. the relationship charge; the best 3 go out
  - concession: from the anchor toward the limit over ~5 rounds (a Live Final wave is 8 minutes)
  - accept: when the standing offer costs us no more than our next sheet, or on agreed/final_offer
    if it beats the alternative and keeps the must-haves
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

PLANNED_ROUNDS = 5  # rounds we plan to use; 8 min per wave fits about 4-6
TYPICAL_MAX_GAP = 4.0  # history: suppliers settled 1.0-4.0 pts below their ask
MIN_GAIN_PTS = 1.0  # never pay more than ask - 1 pt unless it is the last word

SYSTEM = """You are a senior buyer at Hollerau Pumpenwerke, a German pump maker, writing to an
industrial supplier. Write ONLY the opening paragraph of the e-mail: 2-3 sentences that respond to
their last message and set the tone (polite, factual, firm; acknowledge the partnership when the
notes say the supplier values it; if they are short of cash or want faster payment, say we can
offer quicker payment). Do NOT write any number, price, percentage, date or data ID - the facts and
offers are added below your paragraph automatically. No greeting line, no sign-off, no
placeholders. Reply with the paragraph only."""


def _repo():
    return Path(os.environ.get("NOIDEA_REPO") or Path(__file__).resolve().parents[4])


class NoIdeaAgent:
    def __init__(self, complete=None):
        self.complete = complete
        root = _repo() / "datasets"
        self.dossiers = json.loads((root / "A_dossiers.json").read_text())
        self.claims = [json.loads(line) for line in (root / "C_arguments.jsonl").read_text().splitlines()]
        self.ch12 = {c["series"]: c["figure"] for c in self.claims
                     if c["kind"] == "index_change" and c.get("window_months") == 12}
        self.case_id = None

    # ---- preparation (once per case) --------------------------------------------------------------
    def prepare(self, case, threads):
        b = case["buyer"]
        self.case_id, self.sup = case["case_id"], {}
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
            justified = sum((dr["weight"] or 0) * self.ch12.get(dr["series"], 0.0) for dr in pinfo.get("cost_drivers", []))
            cur = b.get("current_unit_price") or standing(events)[1].get("unit_price")
            should = [c for c in self.claims if c["kind"] == "should_cost" and c["part"] == part and c["supplier"] == sid]
            # should-cost has 5-15% error and several suppliers have sold below it ("accepted below
            # full cost to keep the volume"): take the lower of should-cost and today's price, minus 6%
            full_cost = min(should[0]["figure"], cur) * 0.94 if should else cur * 0.94
            rate = 0.25 if "cash_short" in motives else 0.14 if "wants_faster_payment" in motives else 0.08
            est = {"standard": std, "interest_rate": rate, "usual_rate": 0.08, "full_cost": full_cost}
            open_terms = standing(events)[1]
            ask_pct = (open_terms["unit_price"] / cur - 1) * 100 if cur and open_terms.get("unit_price") else 0.0
            self.sup[sid] = {"dossier": d, "std": std, "est": est, "justified": justified, "cur": cur,
                             "ask_pct": ask_pct, "open_terms": open_terms, "args": self.pick_args(case, sid, ask_pct, justified)}
            log.info("prep %s: ask %+.1f%%, justified %+.1f%%, full_cost~%.2f, cash_rate %.2f, motives %s",
                     sid, ask_pct, justified, full_cost, rate, list(motives))

    def pick_args(self, case, sid, ask_pct, justified):
        """Up to 3 checked sentences that help us; the arena checks at most 3 per e-mail."""
        part, mine = case["parts"][0], [c for c in self.claims if c["supplier"] == sid and c["checked_by_arena"]]
        out = []
        for c in mine:
            if c["kind"] == "notice_period" and c.get("short_notice"):
                out.append(c)
        drivers = sorted((c for c in mine if c["kind"] == "index_change" and c["part"] == part
                          and c.get("window_months") == 12 and c["figure"] < ask_pct),
                         key=lambda c: (c["figure"] - ask_pct) * (c.get("weight") or 0))
        out += drivers[:2]
        for c in mine:
            if c["kind"] == "should_cost" and c["part"] == part and c.get("price_vs_should_cost_pct", -1) > 3:
                out.append(c)
            if c["kind"] in ("scorecard_otd",) and (c["figure"] or 100) < 88 and case["type"] in ("quality", "capacity", "price_increase"):
                out.append(c)
            if c["kind"] == "scorecard_ppm" and case["type"] == "quality":
                out.append(c)
        seen, picked = set(), []
        for c in out:
            if c["sentence"] not in seen:
                seen.add(c["sentence"])
                picked.append(c)
        return picked[:3]

    # ---- term sheets ---------------------------------------------------------------------------
    def combos(self, case, base):
        opts = case.get("term_options", {})
        fields = [f for f in case["negotiable"] if f != "unit_price" and opts.get(f)]
        fields = [f for f in fields if f != "index_clause"]  # v1: no index clauses
        for values in itertools.product(*(opts[f] for f in fields)):
            yield {**base, **dict(zip(fields, values))}

    def sheets_at(self, case, sid, value):
        """The 3 term sheets that give the supplier `value` per unit at the lowest cost to us."""
        s = self.sup[sid]
        ranked = []
        for t in self.combos(case, dict(s["open_terms"])):
            t = complete_offer(case, {**t, "unit_price": 100.0})
            v1 = supplier_value(case, t, s["est"])
            v2 = supplier_value(case, {**t, "unit_price": 200.0}, s["est"])
            slope = (v2 - v1) / 100.0
            if slope <= 0:
                continue
            t = complete_offer(case, {**t, "unit_price": 100.0 + (value - v1) / slope})
            if t["unit_price"] is None or t["unit_price"] <= 0 or not must_haves_ok(case, t, s["std"]):
                continue
            ranked.append((total_cost(case, t, s["std"], s["est"]), t))
        ranked.sort(key=lambda x: x[0])
        out = []
        for c, t in ranked:
            if all(t != o for _, o in out):
                out.append((c, t))
            if len(out) == 3:
                break
        return out

    def value_target(self, case, sid, k):
        """Concession path in supplier-value terms: anchor -> limit over PLANNED_ROUNDS."""
        s = self.sup[sid]
        cur, ask = s["cur"], s["ask_pct"]
        anchor_pct = min(s["justified"], ask - TYPICAL_MAX_GAP)
        limit_pct = ask - MIN_GAIN_PTS
        base = complete_offer(case, s["open_terms"])
        v = lambda pct: supplier_value(case, {**base, "unit_price": cur * (1 + pct / 100)}, s["est"])
        floor = s["est"]["full_cost"]  # hard floor: never ask below its estimated full cost
        anchor, limit = max(v(anchor_pct), min(floor, v(limit_pct))), v(limit_pct)
        f = min(1.0, k / max(1, PLANNED_ROUNDS - 1)) ** 1.3
        return anchor + (limit - anchor) * f

    # ---- the move ------------------------------------------------------------------------------
    def decide(self, case, threads):
        if case["case_id"] != self.case_id:
            self.prepare(case, threads)
        live = [s for s in live_threads(threads) if s in self.sup]
        # talk to the supplier whose thread is furthest behind (RFQ round-robin)
        sid = min(live, key=lambda s: sum(m.get("from") == "buyer" for m in threads[s]))
        events, s = threads[sid], self.sup[sid]
        sheet_id, terms = standing(events)
        status = latest(events).get("status")
        k = sum(m.get("from") == "buyer" and bool(m.get("term_sheets")) for m in events)
        c_stand = total_cost(case, terms, s["std"], s["est"]) if sheet_id else math.inf
        ok = sheet_id and must_haves_ok(case, terms, s["std"]) and c_stand < self.c_alt
        accept = {"supplier_id": sid, "message": {"action": {"type": "accept", "term_sheet_id": sheet_id}}}

        if status == "agreed" and ok:
            return accept
        if status == "final_offer" or moves_left(case, events) <= 1 or k >= PLANNED_ROUNDS + 1:
            if ok and c_stand <= min(self.best_standing(case, threads)):
                return accept
            if not ok:
                return {"supplier_id": sid, "message": {"action": {"type": "walk_away"}}}
        sheets = self.sheets_at(case, sid, self.value_target(case, sid, k))
        if not sheets:
            return accept if ok else {"supplier_id": sid, "message": {"action": {"type": "walk_away"}}}
        if ok and k > 0 and c_stand <= sheets[0][0] * 1.0005:
            return accept
        log.info("%s round %d: our best C %.0f vs standing %.0f (alt %.0f)", sid, k, sheets[0][0], c_stand, self.c_alt)
        refs = sorted({i for c in s["args"] for i in c["ids"]})
        return {"supplier_id": sid, "message": {
            "subject": f"Re: {case['title']}"[:300],
            "body": self.write(case, sid, events, [t for _, t in sheets], k),
            "term_sheets": [{"terms": t} for _, t in sheets],
            "refs": refs[:20],
        }}

    def best_standing(self, case, threads):
        out = [math.inf]
        for sid in live_threads(threads):
            if sid in self.sup:
                sh, t = standing(threads[sid])
                if sh:
                    out.append(total_cost(case, t, self.sup[sid]["std"], self.sup[sid]["est"]))
        return out

    # ---- the words -----------------------------------------------------------------------------
    def write(self, case, sid, events, sheets, k):
        s = self.sup[sid]
        name = s["dossier"].get("name", "your company")
        args = [c["sentence"] for c in s["args"]] if k == 0 else [c["sentence"] for c in s["args"][:1]]
        offers = "; ".join(", ".join(f"{f} {v}" for f, v in t.items() if f in case["negotiable"]) for t in sheets)
        opening = "Thank you for your message."
        if self.complete:
            levers = "; ".join(f"{m}: {v['lever']}" for m, v in s["dossier"].get("motives", {}).items())
            user = (f"SUPPLIER: {name}\nCASE: {case['title']} ({case['type']}, goal {case['buyer']['category_goal']})\n"
                    f"ROUND: {k + 1}\nWHAT MOVES THIS SUPPLIER: {levers or 'n/a'}\n"
                    f"THEIR LAST E-MAIL:\n{latest(events).get('body', '')[:900]}\n")
            try:
                text = " ".join(self.complete(SYSTEM, user).split())
                # the model must not carry figures (those come from code and are checked):
                # keep only its sentences without digits
                text = " ".join(x for x in re.split(r"(?<=[.!?])\s+", text) if not any(ch.isdigit() for ch in x))
                if 30 < len(text) < 700:
                    opening = text
                else:
                    log.warning("LLM paragraph rejected (len %d or contains figures)", len(text))
            except Exception as e:  # a slow or broken model must not cost the round
                log.warning("LLM failed (%s) - plain opening used", e)
        facts = (" ".join(args) + "\n\n") if args else ""
        return (f"Dear {name} team,\n\n{opening}\n\n{facts}"
                f"On this basis we propose the attached term sheets ({offers}). "
                "Please let us know which option works best for you.\n\nKind regards,\nPurchasing, Hollerau Pumpenwerke")
