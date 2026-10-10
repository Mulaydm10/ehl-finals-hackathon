"""Team NoIdea buyer v1.2: code sets every number, the language model only writes the opening.

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

PLANNED_ROUNDS = 8  # P07 live: ~25 s per round, so an 8-minute wave fits ~12-15; keep a margin
MIN_GAIN_PTS = 1.0  # never pay more than ask - 1 pt unless it is the last word
# How far below the opening quote to anchor (src/eval/calibrate.py: best deal vs opening, practice cases)
ANCHOR_DEPTH = {"rfq": 0.20, "bundling": 0.15, "raw_material": 0.22, "capacity": 0.14, "quality": 0.09}
ANCHOR_DEPTH_BY_GOAL = {"stabilise": 0.03, "secure_supply": 0.10, "quality_first": 0.09,
                        "leverage": 0.18, "routine": 0.03}
PLAYBOOK_SECTIONS = ("What the goal means here", "Motive", "Tone")
# Qwen benchmark (notes/agent_changelog.md v1.3): it sometimes wrote the supplier's situation as ours
# ("our restructuring", "our pricing committee") or leaked our position ("our target cost") - drop such sentences
BAD_OPENING = re.compile(r"(?i)\bour (current )?(restructuring|survival|pricing committee|committee|target|budget|cost pressure|"
                         r"capacity|liquidity|cash|bank|alternative)|\bwe (must|need to) (prioriti|close|sign)|"
                         r"cost pressures we|we face|line.down|no alternative|urgent|our need to|we (urgently )?need|secure (our|full) supply|"
                         r"we depend|we cannot (afford|wait)")

SYSTEM = """You are a senior BUYER at Hollerau Pumpenwerke, a German pump maker, writing to one of
your SUPPLIERS. Write ONLY the opening paragraph of the e-mail: 2-3 sentences that respond to the
supplier's last message and set the tone the PLAYBOOK asks for.
Rules:
- "We" is always Hollerau, the buyer. Everything under SUPPLIER SITUATION is about THEM (their cash,
  their committee, their capacity, their restructuring) - never describe it as ours.
- Never reveal our position: no targets, budgets, urgency, alternatives or weaknesses.
- Do not mention materials, costs or facts that are not in their e-mail.
- Do NOT write any number, price, percentage, date or data ID - the facts and offers are added
  below your paragraph automatically. No greeting line, no sign-off, no placeholders.
- Always write in English, even if the supplier mixes in German words.
Reply with the paragraph only."""


def _repo():
    return Path(os.environ.get("NOIDEA_REPO") or Path(__file__).resolve().parents[4])


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
        self.dossiers = json.loads((root / "datasets/A_dossiers.json").read_text())
        self.claims = [json.loads(line) for line in (root / "datasets/C_arguments.jsonl").read_text().splitlines()]
        self.ch = {(c["series"], c.get("window_months")): (c["figure"], c) for c in self.claims if c["kind"] == "index_change"}
        pb = root / "playbooks"
        self.playbooks = {p.stem: p.read_text() for p in pb.glob("*.md")} if pb.exists() else {}
        self.correspondence = root / "tacto/data/correspondence"
        facts = root / "tacto/data/facts.json"
        self.fc = {k: v for k, v in json.loads(facts.read_text()).items() if k.startswith("fc:")} if facts.exists() else {}
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
            est = {"standard": std, "interest_rate": rate, "usual_rate": 0.08, "full_cost": full_cost}
            ask_pct = (open_terms["unit_price"] / cur - 1) * 100 if cur and open_terms.get("unit_price") else 0.0
            self.sup[sid] = {"dossier": d, "std": std, "est": est, "justified": justified, "cur": cur,
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
        # per driver series: the window (6 or 12 m) with the lower change, if it is below the ask.
        # When the quote is already below today's price (bundles, RFQs, renewals at a cut), the ask is
        # negative and the useful comparison is "no cost push": drivers that moved < 3% (P07 live: the
        # supplier said "our price follows our main cost drivers" and we had cited nothing)
        # v1.5 live P07: citing drivers that rose < 3% got "Your figures confirm our case: that driver rose."
        # -> with no increase to fight, only indices that fell or stayed flat
        bar = ask_pct if ask_pct > 0 else 0.0
        parts = set(case["parts"])
        best = {}
        for c in mine:
            if c["kind"] == "index_change" and c["part"] in parts and c["figure"] < bar:
                k = c["series"]
                if k not in best or c["figure"] < best[k]["figure"]:
                    best[k] = c
        for c in sorted(best.values(), key=lambda c: (c["figure"] - ask_pct) * (c.get("weight") or 0)):
            if c["figure"] > 0:  # a rise alone "confirms their case" (P07 live): set it against the ask
                c = {**c, "sentence": c["sentence"].rstrip(".") + f", well below the {ask_pct:+.1f}% you ask for."}
            out.append(c)
        out += [c for c in mine if c["kind"] == "should_cost" and c["part"] in parts
                and c.get("price_vs_should_cost_pct", -1) > 3]
        # flat price history is the argument when there's no increase to fight - but not for kits:
        # P07 live, part-level history "does not change our calculation" for a bundle (kit_calc instead)
        if ask_pct <= 0 and case["type"] != "bundling":
            out += [c for c in mine if c["kind"] == "po_prices" and c["part"] in parts]
        if case["type"] in ("capacity", "price_increase"):
            out += [c for c in mine if c["kind"] == "scorecard_otd" and (c["figure"] or 100) < 85]
        out += self.forecast_args(case)
        seen, ranked = set(), []
        for c in out:
            if c["sentence"] not in seen:
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
        lines = re.findall(r"-\s*(\d+)\s*x\s*(.+?)\s*\((part:\d+)\)", path.read_text())
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

    def forecast_args(self, case):
        """Checked volume evidence: the latest positive demand forecast per part (`fc:` IDs, checked on
        change_pct). P07 v1.5 live asked three times for "documentation supporting the binding volume…
        Which figures is that based on? Please send us the data." """
        out = []
        for part in case["parts"]:
            ks = sorted(k for k in self.fc if k.startswith(f"fc:{part.split(':')[1]}@"))
            if ks and (ch := self.fc[ks[-1]].get("change_pct")) and ch > 0:
                desc = next((p[3] for p in self.part_prices.get(part, [])), part)
                out.append({"kind": "forecast", "ids": [ks[-1]], "figure": ch, "part": part,
                            "sentence": f"Our demand forecast for {desc.split(',')[0]} is up {ch:+.1f}% ({ks[-1]})."})
        return sorted(out, key=lambda c: -c["figure"])[:2]

    def next_args(self, sid, n):
        """The next `n` arguments whose IDs were not cited yet (re-citing reads as padding)."""
        picked = []
        for c in self.sup[sid]["args"]:
            if len(picked) == n:
                break
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
            t = complete_offer(case, {**t, "unit_price": 100.0 + (value - v1) / slope})
            if t["unit_price"] is None or t["unit_price"] <= 0 or not must_haves_ok(case, t, s["std"]):
                continue
            if cap_price and t["unit_price"] > cap_price:  # never above its standing price (P01, score 0)
                continue
            ranked.append((total_cost(case, t, s["std"], s["est"]), t))
        # v1.5 preferred the longer contract on cost ties; P07 live (0f754b1368387b8e) priced 36 m HIGHER
        # (opened 5.60 vs 5.56, final 5.56 vs 5.49): reverted to plain cost order
        ranked.sort(key=lambda x: x[0])
        out = []
        # the supplier may pick ANY sheet we send: only offer ones we'd be glad to have accepted
        # (offline eval P10: a 12-month sheet at equal supplier value cost us +33% and got picked)
        band = ranked[0][0] * 1.01 if ranked else 0
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
        anchor_price = opening * (1 - depth)
        if kind == "price_increase":  # the cost-justified change (EDA 3) when it is lower
            anchor_price = min(anchor_price, s["cur"] * (1 + s["justified"] / 100))
        limit_price = s["cur"] * (1 + (s["ask_pct"] - MIN_GAIN_PTS) / 100)
        anchor, limit = v(anchor_price), v(min(limit_price, opening))
        if goal in ("stabilise", "secure_supply"):  # the relationship charge: never ask below its full cost
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
        theirs = max(0.0, vals[0] - vals[1]) if len(vals) == 2 else (limit - anchor) / PLANNED_ROUNDS
        step = min(scheduled - hist[-1], max(theirs, (limit - anchor) / (2 * PLANNED_ROUNDS)))
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
        events, s = threads[sid], self.sup[sid]
        sheet_id, terms = standing(events)
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
        cap = terms.get("unit_price") if sheet_id else None
        sheets = self.sheets_at(case, sid, self.value_target(case, sid, events), cap)
        if not sheets:
            return accept if ok else walk
        # accept when the supplier meets our current ask, or when we are within 0.3% late in the game
        if ok and k > 0 and c_stand <= best_elsewhere and (
                c_stand <= sheets[0][0] * 1.0005 or (k >= PLANNED_ROUNDS - 2 and c_stand <= sheets[0][0] * 1.003)):
            return accept
        log.info("%s round %d: our best C %.0f vs standing %.0f (alt %.0f)", sid, k, sheets[0][0], c_stand, self.c_alt)
        out = [t for _, t in sheets]
        alt_prose = self.prose_alternative(case, sid, events)
        # only when it is near our ask or late in the game: it may pick any sheet (P10 lesson),
        # so an early far-off prose offer in our sheets would just be accepting its number
        if alt_prose and alt_prose[1] not in out and (alt_prose[0] <= sheets[0][0] * 1.01 or k >= PLANNED_ROUNDS - 3):
            # its own prose offer as a binding option: it can simply agree to what it proposed
            out = out[:2] + [alt_prose[1]]
        return self.message(case, sid, events, out, k)

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
                sh, t = standing(threads[sid])
                if sh:
                    out.append(total_cost(case, t, self.sup[sid]["std"], self.sup[sid]["est"]))
        return out

    # ---- the words -----------------------------------------------------------------------------
    def message(self, case, sid, events, sheets, k, final=False):
        args = self.next_args(sid, 3 if k == 0 else 1)
        rival = self.rival_offer(case, sid) if case["type"] == "rfq" else None
        refs = sorted({i for c in args for i in c["ids"]} | ({rival[0]} if rival else set()))
        self.cited.update(refs)
        return {"supplier_id": sid, "message": {
            "subject": f"Re: {case['title']}"[:300],
            "body": self.write(case, sid, events, sheets, k, [c["sentence"] for c in args], rival, final),
            "term_sheets": [{"terms": t} for t in sheets],
            "refs": refs[:20],
        }}

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
        # only a rival BETTER than this bidder's own standing price (playbooks/rfq.md: "don't show the
        # leader its rivals' worse prices"; P05 offline trial cited EUR 38.50 to a bidder at ~31.5)
        own = standing(self.threads_ref[sid])[1].get("unit_price") if sid in self.threads_ref else None
        if best and own and best[1] >= own:
            return None
        if best and (sid, best[0]) not in self.cited:
            self.cited.add((sid, best[0]))
            return best
        return None

    def write(self, case, sid, events, sheets, k, args, rival, final):
        s = self.sup[sid]
        d = s["dossier"]
        name = d.get("name", "your company")
        motives = d.get("motives", {})
        offers = "; ".join(", ".join(f"{f} {v}" for f, v in t.items() if f in case["negotiable"]) for t in sheets)
        opening = "Thank you for your message."
        if self.complete:
            levers = "; ".join(f"{m}: {v['lever']}" for m, v in motives.items())
            playbook = _sections(self.playbooks.get(case["type"], ""), PLAYBOOK_SECTIONS)[:2500]
            user = (f"SUPPLIER: {name}\nCASE: {case['title']} ({case['type']}, goal {case['buyer']['category_goal']})\n"
                    f"ROUND: {k + 1}{' (its final offer - make one last small request, then we close)' if final else ''}\n"
                    f"NEGOTIABLE TERMS (mention ONLY these levers; never offer anything else, e.g. payment if it "
                    f"is not listed): {', '.join(case['negotiable'])}\n"
                    f"SUPPLIER SITUATION (about THEM, not us) and how we respond: {levers or 'n/a'}\n"
                    f"PLAYBOOK (our negotiation guidance):\n{playbook}\n"
                    f"THEIR LAST E-MAIL:\n{latest(events).get('body', '')[:900]}\n")
            try:
                text = " ".join(self.complete(SYSTEM, user).split())
                # the model must not carry figures (those come from code and are checked)
                off_table = [] if "payment_days" in case["negotiable"] else [r"payment", r"cash flow", r"liquidity", r"disburse"]
                off_table += [] if "contract_months" in case["negotiable"] else [r"longer contract", r"contract term"]
                text = " ".join(x for x in re.split(r"(?<=[.!?])\s+", text)
                                if not any(ch.isdigit() for ch in x) and not BAD_OPENING.search(x)
                                and not any(re.search(o, x, re.I) for o in off_table))
                # Astra offline trial (P10 round 3) answered in German: keep the e-mail in one language
                german = len(re.findall(r"(?i)\b(wir|sie|und|der|die|das|nicht|bitte|ihre?n?|mit|für)\b", text))
                if 30 < len(text) < 700 and german < 3:
                    opening = text
                else:
                    log.warning("LLM paragraph rejected (len %d)", len(text))
            except Exception as e:  # a slow or broken model must not cost the round
                log.warning("LLM failed (%s) - plain opening used", e)
        t0 = {**case.get("fixed_terms", {}), **sheets[0]}
        vol, months = t0.get("volume_per_year") or case["buyer"]["need_per_year"], t0.get("contract_months")
        # suppliers keep asking "Which volume can you commit to?" (P07 live): answer in code
        unit = "kits" if case["type"] == "bundling" else "units"
        lines = [f"We confirm a binding volume of {vol:,} {unit} per year" + (f" for {months} months" if months else "") + "."]
        if case["type"] == "bundling":
            if k == 0:
                lines.append("We want one partner for the complete kit, which bundles parts we buy from several suppliers today.")
            if (kit := self.kit_sentence(case, sid, sheets[0]["unit_price"], k)):
                lines.append(kit)
        # how big the deal is for it (needs-volume suppliers; P07: the kit is ~4x our business with it)
        spend = (d.get("spend_by_fy") or [[None, 0]])[-1][1]
        deal = vol * (s["cur"] or 0)
        if spend and deal > 1.5 * spend and ({"needs_volume", "bundle", "wants_commitment"} & set(motives)):
            lines.append(f"That is about EUR {deal:,.0f} a year, around {deal / spend:.0f} times our current business with you.")
        if rival:
            lines.append(f"We have an offer at EUR {rival[1]:.2f} per unit ({rival[0]}).")
        lines += args
        if k == 0 and "open_book" in motives:
            what = "the kit" if case["type"] == "bundling" else "this part"
            lines.append(f"Could you share your cost breakdown for {what}, so we can understand the drivers together?")
        if k == 0 and "we_pay_late" in motives:
            lines.append("We have also put our invoice processing in order and will pay reliably on the agreed day.")
        if k == 0 and case["type"] == "quality":
            lines.append("Please send us your 8D report and a binding ppm commitment.")
        ask = ("As our final step, we can accept your offer with this one change (attached)." if final else
               f"On this basis we propose the attached term sheets ({offers}). Please let us know which option works best for you.")
        return (f"Dear {name} team,\n\n{opening}\n\n" + " ".join(lines) + f"\n\n{ask}\n\nKind regards,\nPurchasing, Hollerau Pumpenwerke")
