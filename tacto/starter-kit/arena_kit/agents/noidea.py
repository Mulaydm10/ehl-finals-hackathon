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
                         r"we depend|we cannot (afford|wait)|above all else|prioriti[sz]e (a )?reliable supply|critical for us|our production depends|"
                         r"not (include )?a binding|rather than a binding|non-binding|keeping your (proposed |requested )?payment|"
                         r"retain(ing)? your (proposed |requested )?(payment|contract)")

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


DECIDE_SYSTEM = """You are the lead BUYER of Hollerau Pumpenwerke, a German pump maker, negotiating by e-mail with one
of your SUPPLIERS. You negotiate like the best in the world:
- Chris Voss: tactical empathy. Label what they feel or fear ("It sounds like…", "It seems that…"), ask calibrated
  how/what questions, never split the difference, never sound needy.
- Fisher & Ury: interests over positions; anchor on objective criteria (the verified facts and calculations below).
- Patrick Jane (The Mentalist): read the supplier like a mentalist. Notice what its e-mail repeats, stresses,
  softens or avoids, and what the SIGNALS and NOTES reveal. Open with ONE sharp, true observation that shows you see
  its real situation ("You mention capacity twice and price only once - it seems lead time is what really costs
  you"). Ground it ONLY in its e-mail, the signals or the notes; never invent, never manipulate, never mock.
Stance by goal: stabilise = respected long-term partner; secure_supply = commitment first, calm, never desperate;
quality_first = firm accountability; leverage = cool, factual, competitive; routine = brief and efficient.
Code has already priced every option. You READ the supplier's last e-mail, CHOOSE what to send, and write the OPENING
paragraph. Reply with ONE JSON object and nothing else:
{"notes": {"questions": ["what the supplier asked us"],
           "refusals": [{"field": "<negotiable field>", "min": <number or null>, "max": <number or null>, "why": "..."}],
           "wants": "what the supplier wants most, in a few words"},
 "sheets": [<1-3 indices from CANDIDATES>],
 "args": [<0-3 indices from ARGUMENTS>],
 "opening": "<2-3 sentences>"}
Rules:
- "We" is always Hollerau, the buyer. The supplier's situation is THEIRS, never ours.
- sheets: choose the candidates that best answer what the supplier signalled (e.g. it refused a short lead
  time -> pick candidates with a longer lead). All candidates are acceptable for us; lower rank = cheaper for us.
- args: pick the facts that answer its questions or objections. Never more than 3.
- refusals: only what it explicitly says it cannot or will not do (e.g. "lead time below 54 days is unfeasible"
  -> {"field": "lead_time_days", "min": 54}).
- opening: 2-4 sentences: the observation (label), then the interest we serve and one calibrated question. Follow
  the LESSONS. Code states our BINDING volume and lists the term sheets right below your paragraph: never say the
  volume is not binding, never offer a different volume, and never describe what the sheets contain or compare them
  with its terms ("keeping your payment terms" etc.) - talk about interests, not terms. Never reveal targets, budgets, urgency or alternatives, only mention NEGOTIABLE levers, write NO numbers,
  prices, dates or IDs (code adds them), English only, no greeting line, no sign-off."""


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
        les = root / "datasets/G_lessons.json"
        self.lessons = json.loads(les.read_text()) if les.exists() else {}
        try:  # the signal catalogue (src/eval/signals.py): category -> (regex, what works)
            import importlib.util
            spec = importlib.util.spec_from_file_location("noidea_signals", root / "src/eval/signals.py")
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            self.signal_rx = {k: (re.compile(rx, re.I), act) for k, (rx, act) in mod.SIGNALS.items() if k != "boilerplate"}
        except Exception as e:
            log.warning("signal catalogue not loaded (%s)", e)
            self.signal_rx = {}
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
            calc = self.cost_calc(case, sid, events, cur, ask_pct)
            self.sup[sid] = {"dossier": d, "std": std, "est": est, "justified": justified, "cur": cur,
                             "ask_pct": ask_pct, "open_terms": open_terms, "cost_calc": calc,
                             "args": ([calc] if calc else []) + [
                                 c for c in self.rank_args(case, sid, ask_pct)
                                 if not (calc and c["kind"] == "index_change" and c.get("series") in calc["series"])],
                             "kit": self.kit_calc(case, sid) if case["type"] == "bundling" else None}
            self.sup[sid]["k"] = self.prior_k(case, sid)
            self.sup[sid]["patience"] = self.patience_prior(case, sid)
            log.info("%s patience prior: final expected around round %d", sid, self.sup[sid]["patience"])
            body = next((m.get("body") or "" for m in events if m.get("from") != "buyer"), "")
            self.sup[sid]["story"] = self.price_story(case, sid, body)
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
        # only indices that FELL or stayed flat: a rise "confirms their case: that driver rose" even when
        # framed as "well below the ask" (P07 v1.5 and P10 live)
        out += [c for c in sorted(best.values(), key=lambda c: c["figure"] * (c.get("weight") or 0)) if c["figure"] <= 0]
        out += [c for c in mine if c["kind"] == "should_cost" and c["part"] in parts
                and c.get("price_vs_should_cost_pct", -1) > 3]
        # flat price history is the argument when there's no increase to fight - but not for kits:
        # P07 live, part-level history "does not change our calculation" for a bundle (kit_calc instead)
        # ... and when the price already jumped (P18: an index clause took it 5.26 -> 5.84 in July, +11%,
        # more than the 12-month driver change): the history shows the rise is already paid for
        pos =[c for c in mine if c["kind"] == "po_prices" and c["part"] in parts]
        if case["type"] != "bundling" and (ask_pct <= 0 or any(self.po_jump(c) >= 3.0 for c in pos)):
            out += pos
        if case["type"] in ("capacity", "price_increase"):
            out += [c for c in mine if c["kind"] == "scorecard_otd" and (c["figure"] or 100) < 85]
        out += self.forecast_args(case)
        seen, ranked = set(), []
        for c in out:
            if c["sentence"] not in seen:
                seen.add(c["sentence"])
                ranked.append(c)
        return ranked

    # Expected round of its final_offer, by what we know before round 1 (26 practice games, src/eval/archive_runs.py):
    # capacity P10 round 1 (5/5), renewal P04 round 3, bundling P07 round 4 (6/6), stabilise price increase P01
    # never within 4-5 rounds. Hidden suppliers come from the same generator; these are estimates, not rules.
    PATIENCE_BY_TYPE = {"capacity": 1, "renewal": 3, "bundling": 4, "rfq": 4, "raw_material": 4, "quality": 4,
                        "price_increase": 7}
    SHORT_FUSE_MOTIVES = {"capacity_tight", "news_allocation", "news_full_order_book", "we_are_not_strategic"}

    def patience_prior(self, case, sid):
        d = self.dossiers.get(sid, {})
        p = self.PATIENCE_BY_TYPE.get(case["type"], 4)
        if case["type"] == "price_increase" and case["buyer"]["category_goal"] != "stabilise":
            p = 4
        if self.SHORT_FUSE_MOTIVES & set(d.get("motives", {})):
            p = min(p, 2)
        return p

    def update_patience(self, case, sid, events):
        """Warning signs that its final is near: validity drops below the opening's (30 -> 7 days in the P07/P10
        finals) or its concessions shrink to under 40% of the previous one (P07: 0.18 -> 0.00 -> 0.04 -> 0.03)."""
        s = self.sup[sid]
        k = sum(m.get("from") == "buyer" for m in events)
        sup_msgs = [m for m in events if m.get("from") != "buyer"]
        val = [int(v.group(1)) for m in sup_msgs
               if (v := re.search(r"(?i)valid (?:for )?(\d{1,3}) days", m.get("body") or ""))]
        prices = [standing([m])[1].get("unit_price") for m in sup_msgs if m.get("term_sheets")]
        steps = [a - b for a, b in zip(prices, prices[1:]) if a and b]
        soon = (len(val) >= 2 and val[-1] < val[0]) or (
            len(steps) >= 2 and steps[-2] > 0 and steps[-1] < 0.4 * steps[-2])
        if soon and s["patience"] > k + 1:
            log.info("%s: final looks near (validity %s, steps %s) -> patience %d -> %d",
                     sid, val[-2:], [round(x, 3) for x in steps[-2:]], s["patience"], k + 1)
            s["patience"] = k + 1

    SHARE_RX = re.compile(r"([A-Z][A-Z0-9-]+) rose (-?\d+(?:[.,]\d+)?) ?% in twelve months and is (\d+(?:[.,]\d+)?) ?% of our cost")

    def cost_calc(self, case, sid, events, cur, ask_pct):
        """The cost calculation a supplier asks for, from ITS OWN stated cost shares. P02 live (da8d0e3d77ce091c):
        its opening said "CU-NOTATION rose 47.7 % in twelve months and is 20 % of our cost…", its final: "without
        additional verified data to substantiate your target price, our flexibility remains highly restricted".
        Shares x our index moves (6 or 12 months, whichever totals lower; arena-checked idx IDs) -> justified %.
        Returned as an argument (kind cost_calc) only when it justifies less than the ask."""
        body = next((m.get("body") or "" for m in events if m.get("from") != "buyer"), "")
        shares = [(sr, float(sh.replace(",", ".")) / 100) for sr, _, sh in self.SHARE_RX.findall(body)]
        if not shares or not cur or ask_pct <= 0:
            return None
        best = None
        for w in (6, 12):
            moves = [(sr, sh, self.ch.get((sr, w))) for sr, sh in shares]
            if any(m is None for _, _, m in moves):
                continue
            total = sum(sh * m[0] for _, sh, m in moves)
            if best is None or total < best[0]:
                best = (total, w, moves)
        if not best or best[0] >= ask_pct - 0.5:
            return None
        total, w, moves = best
        price = cur * (1 + total / 100)
        ids = [i for _, _, m in moves for i in m[1]["ids"]]
        shares_txt = ", ".join(f"{sr} {sh * 100:.0f}%" for sr, sh, _ in moves)
        moves_txt = ", ".join(f"{sr} {m[0]:+.1f}% ({m[1]['ids'][0]}, {m[1]['ids'][1]})" for sr, _, m in moves)
        window = "six" if w == 6 else "twelve"
        sentence = (f"Using your own cost shares ({shares_txt}) and the latest {window}-month index moves ({moves_txt}), "
                    f"your cost increase comes to about {total:+.1f}% of the price, not {ask_pct:+.1f}%.")
        log.info("%s cost calc from its own shares: %+.1f%% (%d-month) vs ask %+.1f%% -> EUR %.2f", sid, total, w, ask_pct, price)
        return {"kind": "cost_calc", "ids": ids, "sentence": sentence, "figure": total, "series": [sr for sr, _ in shares],
                "window": w, "price": round(price, 2), "checked_by_arena": True, "supplier": sid, "part": case["parts"][0]}
    @staticmethod
    def po_jump(claim):
        """% from the first to the last price in a po_prices sentence ("... were at 5.26, 5.84 per 1 ...")."""
        m = re.search(r"were at ([\d.]+(?:, [\d.]+)*) per", claim["sentence"]) if claim else None
        prices = [float(x) for x in m.group(1).split(", ")] if m else []
        return (prices[-1] / prices[0] - 1) * 100 if len(prices) > 1 and prices[0] else 0.0

    def price_story(self, case, sid, body):
        """Round-1 prose built from the supplier's OWN statements and our contract, all figures from code.
        P18: its quote says PPI-C2431 "is 38 % of our cost", but the current contract's index clause passes
        PPI-C2431 on at 80 % (ctr:4600070740#3.2) - that clause already took the price 5.26 -> 5.84."""
        s, d, out = self.sup[sid], self.sup[sid]["dossier"], []
        shares = re.findall(r"([A-Z][A-Z0-9-]+) (?:rose|fell|changed) [-\d.]+ % in \w+ months "
                            r"and is (\d+) % of our cost", body)
        stated = {k: float(v) for k, v in shares}
        parts = case["parts"]
        pos = [c for c in self.claims if c["supplier"] == sid and c["kind"] == "po_prices" and c["part"] in parts]
        jump = max((self.po_jump(c) for c in pos), default=0.0)
        if s["ask_pct"] > 0:
            for cl in (d.get("contract") or {}).get("clauses", []):
                share, series = float(cl.get("material_share") or 0) * 100, cl.get("series")
                if cl.get("type") == "index" and series in stated and share > stated[series] + 5:
                    tail = f"; that clause has already raised our price by {jump:.0f}% this year." if jump >= 3 else "."
                    out.append(f"Our current contract passes {series} on at {share:.0f}% weight ({cl['id']}), "
                               f"while your quote states it is {stated[series]:.0f}% of your cost{tail}")
        # the market: a recent, cheaper quote from another supplier, in prose only (past quotes may not be
        # checked as data of this case) and never in RFQs (there the rival's live offer is cited) or when
        # the goal protects the supplier's health
        if case["type"] != "rfq" and case["buyer"]["category_goal"] not in ("stabilise", "secure_supply"):
            cap = min(s["open_terms"].get("unit_price") or math.inf, s["cur"] or math.inf)
            recent = [c["figure"] for c in self.claims
                      if c["supplier"] == sid and c["kind"] == "rival_quote_context" and c["part"] in parts
                      and c.get("figure") and c["figure"] < cap
                      and (m := re.search(r"(\d{4}-\d{2}-\d{2})\)", c["sentence"])) and m.group(1) >= "2026-07-01"]
            if recent:
                out.append(f"Other suppliers currently quote this part at about EUR {min(recent):.2f}.")
        if "approval_ladder" in d.get("motives", {}):
            out.append("We understand a change of this size needs your pricing committee; "
                       "please put this proposal to them.")
        return out

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
    def combos(self, case, base, clause=None):
        """Every option combination. Index clauses stay off (they cost us whenever the index path is positive)
        unless the supplier requires one: then only clause options on its series are tried (`clause`)."""
        opts = case.get("term_options", {})
        fields = [f for f in case["negotiable"] if f != "unit_price" and opts.get(f) and f != "index_clause"]
        series = (clause or {}).get("series")
        clauses = [o for o in opts.get("index_clause") or [] if series and o and o.get("series") == series]
        for values in itertools.product(*(opts[f] for f in fields)):
            t = {**base, **dict(zip(fields, values))}
            if clauses:
                yield from ({**t, "index_clause": o} for o in clauses)
            else:
                yield t

    def required_clause(self, sid):
        """The index clause the supplier insists on: it answered our clause-free sheets with a clause on EVERY
        sheet. P18 live (a99d02eb41cafa66): "for a contract of this duration, we cannot offer a fixed price and
        must include the AS-14404 index clause"; we kept sending clause-free sheets and it moved EUR 0.10 a round."""
        events = getattr(self, "threads_ref", {}).get(sid, [])
        ours = [t.get("terms", {}) for m in events if m.get("from") == "buyer" for t in m.get("term_sheets") or []]
        theirs = [m for m in events if m.get("from") != "buyer" and m.get("term_sheets")]
        last = [t.get("terms", {}) for t in theirs[-1]["term_sheets"]] if len(theirs) > 1 else []
        if last and all(t.get("index_clause") for t in last) and any(not t.get("index_clause") for t in ours):
            return last[0]["index_clause"]
        return None

    def sheets_at(self, case, sid, value, cap_price=None, n=3):
        """The `n` different term sheets that give the supplier `value` per unit at the lowest cost to us,
        with the premiums it showed us (learn) and the limits it stated (refusals) taken into account."""
        s = self.sup[sid]
        ranked = []
        lim = s.get("limits", {})
        for t in self.combos(case, dict(s["open_terms"]), self.required_clause(sid)):
            if any((lo is not None and (t.get(f) or 0) < lo) or (hi is not None and (t.get(f) or 0) > hi)
                   for f, (lo, hi) in lim.items() if t.get(f) is not None):
                continue
            t = complete_offer(case, {**t, "unit_price": 100.0})
            adj = self.premium(sid, t)
            v1 = supplier_value(case, t, s["est"]) + adj
            slope = (supplier_value(case, {**t, "unit_price": 200.0}, s["est"]) + adj - v1) / 100.0
            if slope <= 0:
                continue
            t = complete_offer(case, {**t, "unit_price": 100.0 + (value - v1) / slope})
            if t["unit_price"] is None or t["unit_price"] <= 0 or not must_haves_ok(case, t, s["std"]):
                continue
            if cap_price and t["unit_price"] > cap_price:  # never above its standing price (P01, score 0)
                continue
            ranked.append((total_cost(case, t, s["std"], s["est"]), t))
        # on cost ties take what is EASIEST for the supplier: the option closest to its own opening terms.
        # P10 live (675fc6b9c1c8c291): lead 35 instead of our need 42 (same cost for us) was "technically
        # unfeasible" -> final_offer EUR 35.00 in round 1; P07 live: 36 m (vs its 24 m) was priced higher
        opening = s["open_terms"]
        # suppliers that want commitment price contract length as security (P10 live x2: "to reflect the increased
        # volume and extended contract duration"): on ties, the LONGER contract. Others keep closest-to-its-terms
        # (P07, which never mentioned duration, priced 36 m higher).
        wants_term = case["type"] == "capacity" or bool({"wants_commitment", "capacity_tight", "needs_multi_year"}
                                                        & set(s["dossier"].get("motives", {})))
        def strain(t):
            out = 0.0
            for f in case["negotiable"]:
                o, v = opening.get(f), t.get(f)
                if f == "unit_price" or o is None or v is None or not isinstance(v, (int, float)):
                    continue
                if f == "contract_months" and wants_term:
                    out -= v / 36  # longer = less strain for a supplier that wants security
                    continue
                if f == "lead_time_days":  # faster than we need is pure strain; slower than need costs us anyway
                    v = max(v, 0)
                out += abs(v - o) / max(abs(o), 1)
            return out
        ranked.sort(key=lambda x: (round(x[0], 0), strain(x[1])))
        out = []
        # the supplier may pick ANY sheet we send: only offer ones we'd be glad to have accepted
        # (offline eval P10: a 12-month sheet at equal supplier value cost us +33% and got picked)
        # a stable structure: after round 1 keep the non-price terms of our previous main sheet unless another
        # structure is >= 1% cheaper for us (P02 v2.4 live: the model hopped 90 -> 30 -> 45 days and the supplier
        # priced every hop; final EUR 369.55 @ 45 d instead of 372.15 @ 90 d)
        prev = s.get("last_main")
        if prev and ranked:
            same = lambda t: all(t.get(f) == prev.get(f) for f in case["negotiable"] if f != "unit_price")
            keep = [x for x in ranked if same(x[1])]
            if keep and keep[0][0] <= ranked[0][0] * 1.01:
                ranked = keep + [x for x in ranked if not same(x[1]) and x[0] < keep[0][0] * 0.99]
                ranked.sort(key=lambda x: (not same(x[1]), x[0]))
        band = ranked[0][0] * (1.01 if n <= 3 else 1.015) if ranked else 0
        for c, t in ranked:  # 3 genuinely different options: same-cost duplicates waste a slot
            if c > band:
                break
            if all(t != o and abs(c - oc) > 1.0 for oc, o in out):
                out.append((c, t))
            if len(out) == n:
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
        # NOT paced to patience: conceding faster to match an early final lost value offline (mean 0.937 -> 0.869,
        # P04 0.59) and the live finals didn't depend on our pace (P07 5.49-5.50 in every version). Patience is used
        # only to be readier to accept near its expected final (decide()).
        rounds = PLANNED_ROUNDS
        f = min(1.0, k / max(1, rounds - 1)) ** 1.3
        scheduled = anchor + (limit - anchor) * f
        # reciprocity (P07 live: it moved 5.56 -> 5.52 while a fixed schedule took us 5.25 -> 5.43)
        stand = [standing([m])[1] for m in events if m.get("from") != "buyer" and m.get("term_sheets")]
        vals = [supplier_value(case, complete_offer(case, t), s["est"]) for t in stand[-2:]]
        theirs = max(0.0, vals[0] - vals[1]) if len(vals) == 2 else (limit - anchor) / PLANNED_ROUNDS
        step = min(scheduled - hist[-1], max(theirs, (limit - anchor) / (2 * rounds)))
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
        sheet_id, terms, c_stand = self.best_sheet(case, sid, events)  # cheapest of ALL its sheets, not just [0]
        status = latest(events).get("status")
        k = sum(m.get("from") == "buyer" and bool(m.get("term_sheets")) for m in events)
        ok = bool(sheet_id) and must_haves_ok(case, terms, s["std"]) and c_stand < self.c_alt
        accept = {"supplier_id": sid, "message": {"action": {"type": "accept", "term_sheet_id": sheet_id}}}
        acc_id, acc_terms = sheet_id, terms  # names used by Parth's final-offer code below
        walk = {"supplier_id": sid, "message": {"action": {"type": "walk_away"}}}
        best_elsewhere = min(self.best_standing(case, threads, skip=sid))

        if status == "agreed" and ok and c_stand <= best_elsewhere:
            return accept
        if status == "final_offer" or moves_left(case, events) <= 1 or k >= PLANNED_ROUNDS + 1:
            if not ok:
                return walk if self.c_alt < math.inf or len(live) > 1 else accept if sheet_id else walk
            # its final message may carry a prose alternative that is cheaper for us (P10 live: "Alternatively,
            # with Lieferzeit ... days: EUR ..."): propose exactly that once - it is its own offer, not a push
            if status == "final_offer" and sid not in self.final_asked and moves_left(case, events) > 1:
                alts = [a for a in (self.refused_alternative(case, sid, events),
                                    self.prose_alternative(case, sid, events)) if a]
                alt_p = min(alts, key=lambda a: a[0]) if alts else None
                if alt_p and ok and alt_p[0] < c_stand - 1:
                    self.final_asked.add(sid)
                    return self.message(case, sid, events, [alt_p[1]], k, final=True)
            # final_offer = its last word: ACCEPT. P07 v1.3 live (c5d845883158676c): one "small" extra ask
            # (90 instead of 30 payment days at its EUR 5.40) made it walk away -> no deal, 0.12 instead of ~0.73.
            # The brief warns: "final_offer: push further and it may walk". final_tweak() is kept but unused.
            if c_stand <= best_elsewhere:
                return accept
        if k > 0:  # premiums are measured against its OPENING terms (fixed), like the value targets
            self.learn(case, sid, events)
            self.update_patience(case, sid, events)
        cap = terms.get("unit_price") if sheet_id else None
        target = self.value_target(case, sid, events)
        sheets = self.sheets_at(case, sid, target, cap)
        if not sheets:
            return accept if ok else walk
        # accept when the supplier meets our current ask, or when we are within 0.3% late in the game
        near_final = k >= max(1, s.get("patience", PLANNED_ROUNDS) - 1)
        if ok and k > 0 and c_stand <= best_elsewhere and (
                c_stand <= sheets[0][0] * 1.0005 or ((k >= PLANNED_ROUNDS - 2 or near_final) and c_stand <= sheets[0][0] * 1.003)):
            return accept
        log.info("%s round %d: our best C %.0f vs standing %.0f (alt %.0f)", sid, k, sheets[0][0], c_stand, self.c_alt)
        if self.complete:  # dynamic: the model reads its e-mail and picks among pre-priced candidates
            cands = self.sheets_at(case, sid, target, cap, n=8)
            pick = self.decide_with_model(case, sid, events, cands, k)
            if pick:
                return pick
        out = [t for _, t in sheets]
        alt_prose = self.prose_alternative(case, sid, events)
        # only when it is near our ask or late in the game: it may pick any sheet (P10 lesson),
        # so an early far-off prose offer in our sheets would just be accepting its number
        if alt_prose and alt_prose[1] not in out and (alt_prose[0] <= sheets[0][0] * 1.01 or k >= PLANNED_ROUNDS - 3):
            # its own prose offer as a binding option: it can simply agree to what it proposed
            out = out[:2] + [alt_prose[1]]
        return self.message(case, sid, events, out, k)

    def retrieve(self, case, sid, body):
        """RAG for the model: (1) signals detected in its latest e-mail with what worked, (2) our notes on this supplier,
        verbatim, ranked by word overlap with its e-mail, (3) lessons from our past games for this case type."""
        sig = [f"- {k}: {act}" for k, (rx, act) in self.signal_rx.items() if rx.search(body)]
        words = set(re.findall(r"[a-zäöüß]{5,}", body.lower()))
        docs = self.sup[sid]["dossier"].get("documents", [])
        ranked = sorted(docs, key=lambda d: -len(words & set(re.findall(r"[a-zäöüß]{5,}", d["text"].lower()))))
        notes = [f"- {d['date']} {d['kind']}: {' '.join(d['text'].split())[:260]}" for d in ranked[:4]]
        lessons = [f"- {x}" for x in self.lessons.get(case["type"], []) + self.lessons.get("general", [])]
        return ("SIGNALS IN ITS E-MAIL (and what works):\n" + ("\n".join(sig) or "- none") +
                "\nOUR NOTES ON THIS SUPPLIER (verbatim, most relevant first):\n" + ("\n".join(notes) or "- none") +
                "\nLESSONS FROM OUR PAST NEGOTIATIONS:\n" + "\n".join(lessons[:12]))

    def decide_with_model(self, case, sid, events, cands, k):
        """One model call per round: read the supplier's e-mail (questions, refusals, wants), choose 1-3 of the
        pre-priced candidate sheets and up to 3 verified arguments, write the opening. Everything it returns is
        validated; any problem -> None (the deterministic path runs instead)."""
        s = self.sup[sid]
        pool = [c for c in s["args"] if not any(i in self.cited for i in c["ids"])][:8]
        motives = s["dossier"].get("motives", {})
        levers = "; ".join(f"{m}: {v['lever']}" for m, v in motives.items())
        lines = [f"[{i}] rank {i + 1}: " + ", ".join(f"{f} {v}" for f, v in t.items() if f in case["negotiable"])
                 for i, (_, t) in enumerate(cands)]
        user = (f"SUPPLIER: {s['dossier'].get('name', sid)}\nCASE: {case['title']} ({case['type']}, goal "
                f"{case['buyer']['category_goal']})\nROUND: {k + 1}\nNEGOTIABLE: {', '.join(case['negotiable'])}\n"
                f"SUPPLIER SITUATION (theirs): {levers or 'n/a'}\n"
                f"PLAYBOOK:\n{_sections(self.playbooks.get(case['type'], ''), PLAYBOOK_SECTIONS)[:1800]}\n"
                f"THEIR LAST E-MAIL:\n{latest(events).get('body', '')[:1800]}\n\n"
                f"{self.retrieve(case, sid, latest(events).get('body', ''))}\n\n"
                f"CANDIDATES (all acceptable for us; rank 1 = cheapest for us):\n" + "\n".join(lines) +
                "\n\nARGUMENTS (verified facts, each usable once):\n" +
                "\n".join(f"[{i}] {c['sentence']}" for i, c in enumerate(pool)))
        try:
            raw = self.complete(DECIDE_SYSTEM, user)
            d = json.loads(re.search(r"\{.*\}", raw, re.S).group(0))
        except Exception as e:
            log.warning("model decision failed (%s) - deterministic path", e)
            return None
        idx = [i for i in d.get("sheets", []) if isinstance(i, int) and 0 <= i < len(cands)]
        idx = list(dict.fromkeys(idx))[:3]
        if not idx:
            return None
        aidx = [i for i in d.get("args", []) if isinstance(i, int) and 0 <= i < len(pool)][:3 if k == 0 else 2]
        # required: our strongest argument goes in round 1 whatever the model picks (P02 v2.4 live 159def0f5e514b40:
        # the model chose no argument and the cost calculation it was built for was never sent -> 0.34)
        must = [i for i, c in enumerate(pool) if k == 0 and (c["kind"] == "cost_calc" or
                                                             (c["kind"] == "notice_period" and c.get("short_notice")))]
        aidx = list(dict.fromkeys(must + aidx))
        notes = d.get("notes") or {}
        for r in notes.get("refusals") or []:  # remember its stated limits for the next rounds
            f = r.get("field")
            if f in case["negotiable"] and f != "unit_price":
                lo, hi = s.setdefault("limits", {}).get(f, (None, None))
                lo = r["min"] if isinstance(r.get("min"), (int, float)) else lo
                hi = r["max"] if isinstance(r.get("max"), (int, float)) else hi
                s["limits"][f] = (lo, hi)
        log.info("%s model: sheets %s args %s notes %s", sid, idx, aidx, json.dumps(notes)[:300])
        chosen = [cands[i][1] for i in idx]
        args = [pool[i] for i in aidx]
        opening = self.clean_opening(case, str(d.get("opening") or ""))
        return self.message(case, sid, events, chosen, k, args=args, opening=opening)

    def clean_opening(self, case, text):
        """The same filters as for the opening paragraph: no figures, no leaks, no off-table levers, English."""
        text = " ".join(text.split())
        off_table = [] if "payment_days" in case["negotiable"] else [r"payment", r"cash flow", r"liquidity", r"disburse"]
        off_table += [] if "contract_months" in case["negotiable"] else [r"longer contract", r"contract term"]
        text = " ".join(x for x in re.split(r"(?<=[.!?])\s+", text)
                        if not any(ch.isdigit() for ch in x) and not BAD_OPENING.search(x)
                        and not any(re.search(o, x, re.I) for o in off_table))
        german = len(re.findall(r"(?i)\b(wir|sie|und|der|die|das|nicht|bitte|ihre?n?|mit|für)\b", text))
        return text if 30 < len(text) < 900 and german < 3 else None

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

    PKG = re.compile(r"(?i)(?:a )?price of (?:€|EUR)\s?(\d+(?:[.,]\d+)?)")

    def parse_packages(self, case, body):
        """Every offer package in a supplier e-mail, primary and alternatives, with raw (unsnapped) values.
        The arena's e-mails are templated: "a price of €31.90 per unit, Lieferzeit 54 days, a volume of
        23400 pcs per year, a contract term of 24 months" (datasets/F_supplier_emails.jsonl: 78 real e-mails)."""
        out, hits = [], list(self.PKG.finditer(body or ""))
        for i, m in enumerate(hits):
            seg = body[m.start(): hits[i + 1].start() if i + 1 < len(hits) else len(body)]
            seg = re.split(r"\n\s*\n", seg)[0]
            t = {"unit_price": float(m.group(1).replace(",", ".")),
                 "alternative": bool(re.search(r"(?i)alternativ", body[max(0, m.start() - 160): m.start()]))}
            for f, rx in (("payment_days", r"(?i)zahlungsziel (\d{1,3})|(\d{1,3})[- ]day payment|payment (?:terms )?of (\d{1,3})"),
                          ("lead_time_days", r"(?i)lieferzeit (\d{1,3})|lead time (?:of )?(\d{1,3})"),
                          ("volume_per_year", r"(?i)volume of (\d[\d,.]*) (?:pcs|units|kits|kg|m)"),
                          ("contract_months", r"(?i)contract term of (\d{1,2}) months|(\d{1,2})-month contract")):
                if (g := re.search(rx, seg)):
                    t[f] = int(next(x for x in g.groups() if x).replace(",", "").replace(".", ""))
            iso = re.search(r"\d{4}-\d{2}-\d{2}", seg)
            word = re.search(r"(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", seg)
            if iso:
                t["effective_date"] = iso.group(0)
            elif word and word.group(2).lower() in self.MONTHS:
                t["effective_date"] = f"{word.group(3)}-{self.MONTHS[word.group(2).lower()]:02d}-{int(word.group(1)):02d}"
            out.append(t)
        return out

    def snap_feasible(self, case, raw, base):
        """A raw package -> a valid term sheet. Lead time snaps UP to the next option (shorter than it said
        is what it refused; P10 live: its 54 days snapped to 56, not 42)."""
        t = dict(base, **{k: v for k, v in raw.items() if k in case["negotiable"] or k == "unit_price"})
        opts = case.get("term_options", {}).get("lead_time_days")
        if "lead_time_days" in raw and opts and "lead_time_days" in case["negotiable"]:
            up = [o for o in sorted(opts) if o >= raw["lead_time_days"]]
            t["lead_time_days"] = up[0] if up else max(opts)
        return complete_offer(case, t)

    LEARN_FIELDS = ("lead_time_days", "contract_months", "volume_per_year")
    # Prior for round 1, before it has shown us anything: lead time below the supplier's own quoted lead costs it
    # ~0.49% of price per day (P10 live x2: -EUR 0.158/day at EUR 32.20 = 0.49%). Capacity suppliers go final in
    # round 1 (3/3 P10 games), so round 1 must already price this; learned values replace the prior.
    PRIOR_LEAD_PREMIUM_PCT = 0.0049

    def learn(self, case, sid, events):
        """In-negotiation learning: the supplier's price premium per unit of each non-cash term, from the
        packages it has shown us (P10 live: EUR 33.80 @ 42 d vs EUR 32.00 @ 54 d -> -0.15 EUR/unit per day).
        Payment is left to supplier_value (its cash rate). Stored as s["k"][field] = dPrice/dField."""
        s = self.sup[sid]
        slopes = {}
        for m in events:
            if m.get("from") == "buyer":
                continue
            pk = self.parse_packages(case, m.get("body") or "")
            pk += [{**ts["terms"], "alternative": i > 0} for i, ts in enumerate(m.get("term_sheets") or [])
                   if (ts.get("terms") or {}).get("unit_price") is not None]
            for a, b in itertools.combinations(pk, 2):
                diff = [f for f in self.LEARN_FIELDS + ("payment_days", "effective_date")
                        if a.get(f) is not None and b.get(f) is not None and a.get(f) != b.get(f)]
                if len(diff) == 1 and diff[0] in self.LEARN_FIELDS:
                    f = diff[0]
                    slopes.setdefault(f, []).append((b["unit_price"] - a["unit_price"]) / (b[f] - a[f]))
        s["k"] = {**self.prior_k(case, sid), **{f: sum(v) / len(v) for f, v in slopes.items()}}
        if s["k"]:
            log.info("%s learned premiums (EUR/unit per unit of term): %s", sid, {f: round(v, 3) for f, v in s["k"].items()})

    def prior_k(self, case, sid):
        s = self.sup[sid]
        o = s["open_terms"]
        if "lead_time_days" in case["negotiable"] and o.get("lead_time_days") and o.get("unit_price"):
            return {"lead_time_days": -self.PRIOR_LEAD_PREMIUM_PCT * o["unit_price"]}
        return {}

    def premium(self, sid, t):
        """Value adjustment for the learned premiums, relative to the supplier's latest standing terms."""
        s = self.sup[sid]
        ref = s["open_terms"]  # fixed baseline: a moving one made the price jump (offline P10: 25.81 -> 28.52)
        return -sum(k * ((t.get(f) or 0) - (ref.get(f) or 0)) for f, k in (s.get("k") or {}).items()
                    if t.get(f) is not None and ref.get(f) is not None)

    def prose_alternative(self, case, sid, events):
        """Signal 'prose_alternative' (src/eval/signals.py; P01 live: "Alternatively, with valid from
        ... January ...: EUR ... per unit"). Only term sheets bind, so turn it into one. Returns
        (C, terms) if it is cheaper for us than its standing sheet."""
        body = latest(events).get("body") or ""
        s = self.sup[sid]
        _, terms = standing(events)
        best = None
        for raw in self.parse_packages(case, body):
            if not raw["alternative"]:
                continue
            t = self.snap_feasible(case, raw, terms)
            if must_haves_ok(case, t, s["std"]) and t != complete_offer(case, terms):
                c = total_cost(case, t, s["std"], s["est"])
                if best is None or c < best[0]:
                    best = (c, t)
        for sent in ([] if best else re.split(r"(?<=[.!?])\s+|\n+", body)):  # fallback: free-form prose
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
            # "Lieferzeit / lead time / delivery N days" is a lead time; "Zahlungsziel / payment N days" is payment
            # (P10 live: "Alternatively, with Lieferzeit … days: EUR …")
            lead = re.search(r"(?i)(?:lieferzeit|lead[ -]?time|deliver\w*)\D{0,20}?(\d{1,3})\s*(?:days|tage)", sent)
            pay = re.search(r"(?i)(?:zahlungsziel|payment\w*|net)\D{0,20}?(\d{1,3})\s*(?:days|tage)|(\d{1,3})\s*(?:days|tage)\s*(?:net|netto)", sent)
            if lead and "lead_time_days" in case["negotiable"]:
                t["lead_time_days"] = int(lead.group(1))
            if pay and "payment_days" in case["negotiable"]:
                t["payment_days"] = int(pay.group(1) or pay.group(2))
            if not lead and not pay and (days := re.search(r"(\d{1,3})\s*(?:-\s*)?(?:days|Tage)", sent)):
                f = "payment_days" if "payment_days" in case["negotiable"] else "lead_time_days"
                if f in case["negotiable"]:
                    t[f] = int(days.group(1))
            t = complete_offer(case, t)
            if must_haves_ok(case, t, s["std"]):
                c = total_cost(case, t, s["std"], s["est"])
                if best is None or c < best[0]:
                    best = (c, t)
        if best and best[0] < total_cost(case, terms, s["std"], s["est"]) - 1:
            log.info("%s: prose alternative %s is cheaper - putting it in a term sheet", sid, best[1])
            return best
        return None

    def best_sheet(self, case, sid, events):
        """(term_sheet_id, terms, C) of the cheapest-for-us sheet in its latest message that keeps the must-haves.
        Suppliers often send their alternative as a SECOND term sheet with its own ID (offer:70740-3-a): Parth's
        P18 live (6833e98fbbe5ebdf) accepted term_sheets[0] and left a cheaper alternative on the table (+0.055);
        47 supplier messages in our archive carry such '-a' sheets (P07 finals 5.49 / -a 5.42)."""
        s = self.sup[sid]
        best = None
        for ts in latest(events).get("term_sheets") or []:
            t = ts.get("terms") or {}
            if ts.get("term_sheet_id") and t.get("unit_price") is not None and must_haves_ok(case, t, s["std"]):
                c = total_cost(case, t, s["std"], s["est"])
                if best is None or c < best[2]:
                    best = (ts["term_sheet_id"], t, c)
        if best is None:
            sid0, t0 = standing(events)
            return sid0, t0, (total_cost(case, t0, s["std"], s["est"]) if sid0 else math.inf)
        return best

    def refused_alternative(self, case, sid, events):
        """(C, terms) of the cheapest alternative sheet the arena would not take by its id (play.py clears
        the id after a 422): proposed back once at final_offer, like a prose alternative."""
        s = self.sup[sid]
        best = None
        for ts in latest(events).get("term_sheets") or []:
            if not ts.get("term_sheet_id"):
                t = complete_offer(case, ts["terms"])
                if must_haves_ok(case, t, s["std"]):
                    c = total_cost(case, t, s["std"], s["est"])
                    if best is None or c < best[0]:
                        best = (c, t)
        return best

    def best_standing(self, case, threads, skip=None):
        out = [math.inf]
        for sid in live_threads(threads):
            if sid in self.sup and sid != skip:
                sh, _, c = self.best_sheet(case, sid, threads[sid])
                if sh:
                    out.append(c)
        return out

    # ---- the words -----------------------------------------------------------------------------
    def message(self, case, sid, events, sheets, k, final=False, args=None, opening=None):
        if sheets and not final:
            self.sup[sid]["last_main"] = dict(sheets[0])
        args = self.next_args(sid, 3 if k == 0 else 1) if args is None else args
        if any(a["kind"] == "cost_calc" for a in args):  # it uses 3 claims: the arena checks at most 3 per e-mail
            args = [a for a in args if a["kind"] == "cost_calc"]
        rival = self.rival_offer(case, sid) if case["type"] == "rfq" else None
        refs = sorted({i for c in args for i in c["ids"]} | ({rival[0]} if rival else set()))
        self.cited.update(refs)
        return {"supplier_id": sid, "message": {
            "subject": f"Re: {case['title']}"[:300],
            "body": self.write(case, sid, events, sheets, k, [c["sentence"] for c in args], rival, final, opening),
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

    @staticmethod
    def plain(field, v):
        """A term in words for the e-mail body ("EUR 4.77 per unit", "90 days payment"); the term sheet binds."""
        if field == "unit_price":
            return f"EUR {v:.2f} per unit"
        if field == "index_clause":
            return (f"{v['series']} index clause ({v['material_share']:.0%} share, {v['deadband_pct']:g}% deadband)"
                    if v else "no index clause")
        if field == "chargeback_eur_per_complaint":
            return f"EUR {v:g} per complaint"
        words = {"payment_days": "{} days payment", "contract_months": "{} months",
                 "lead_time_days": "{} days lead time", "volume_per_year": "{:,.0f} units a year",
                 "ppm_commitment": "{} ppm", "tooling_eur": "EUR {:,.0f} tooling", "effective_date": "from {}",
                 "incoterm": "{}"}
        return words.get(field, field + " {}").format(v) if v is not None else ""

    def write(self, case, sid, events, sheets, k, args, rival, final, given_opening=None):
        s = self.sup[sid]
        d = s["dossier"]
        name = d.get("name", "your company")
        motives = d.get("motives", {})
        offers = "; ".join(", ".join(x for f, v in t.items() if f in case["negotiable"] and (x := self.plain(f, v)))
                           for t in sheets)
        opening = given_opening or "Thank you for your message."
        if self.complete and not given_opening:
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
            # no "N times our business" multiple: it can't be backed by a checkable ID and drew 3 requests for
            # "the exact figures behind" it (P07 d67da0a2d2360134)
            lines.append(f"That is a contract worth about EUR {deal:,.0f} a year.")
        if rival:
            lines.append(f"We have an offer at EUR {rival[1]:.2f} per unit ({rival[0]}).")
        lines += args
        calc = s.get("cost_calc")
        if calc and calc["sentence"] in args and sheets and sheets[0].get("unit_price") and \
                calc["price"] <= sheets[0]["unit_price"] * 1.001:  # never justify a price above our own ask
            lines.append(f"That supports a price of about EUR {calc['price']:.2f}.")
        if calc and k > 0 and not any(a is calc["sentence"] for a in args):
            lines.append(f"As calculated from your own cost shares, the cost-justified change is about {calc['figure']:+.1f}%.")
        if k == 0:
            lines += s.get("story", [])
        if k == 0 and "open_book" in motives:
            what = "the kit" if case["type"] == "bundling" else "this part"
            lines.append(f"Could you share your cost breakdown for {what}, so we can understand the drivers together?")
        if k == 0 and "we_pay_late" in motives:
            lines.append("We have also put our invoice processing in order and will pay reliably on the agreed day.")
        if k == 0 and case["type"] == "quality":
            lines.append("Please send us your 8D report and a binding ppm commitment.")
        ask = ("We accept your alternative as you proposed it; it is attached as a term sheet for your confirmation." if final else
               f"On this basis we propose the attached term sheets ({offers}). Please let us know which option works best for you.")
        return (f"Dear {name} team,\n\n{opening}\n\n" + " ".join(lines) + f"\n\n{ask}\n\nKind regards,\nPurchasing, Hollerau Pumpenwerke")
