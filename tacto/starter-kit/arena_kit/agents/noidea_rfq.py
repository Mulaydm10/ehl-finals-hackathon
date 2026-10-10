"""RFQ layer of the team agent (Neel noidea_p05.py, ported into the kit 2026-10-10 22:15; was the P05 variant (Dhruv's tacto/starter-kit/arena_kit/agents/noidea.py, untouched here).

Four changes, each from the 11 archived P05 games (analysis/tools/p05_bidders.py) and analysis/central/LEARNINGS.md:
1. Cost drivers for an RFQ part. The bidders' dossiers do not list the new part (part:320070), so the main agent found
   no drivers and never cited an index in P05. Every bidder writes "Our price follows our main cost drivers: LCI-C,
   PPI-C2431, AS-14404, PPI-D351" and asks "Which figures is that based on? Please send us the data." The weights come
   from data/cost_drivers.csv (category team estimate). Falling windows: AS-14404 -8.5%, PPI-D351 -17.1%,
   PPI-C2431 -2.3%, LCI-C -0.3%. None of the bidders is hedged.
2. Rival offers at any lead time. api.md: "another supplier's offer in this session" is checked by its price. The main
   agent cited only offers meeting OUR must-haves, so 70240's EUR 31.50 (52 days) - the lowest real offer in round 0 -
   was never cited. Back office: "The buyer shows a much lower rival quote. I give half the step now and check the rest."
3. No walk-risk accept while another bidder is still in the game: live f60b3c3a6a65593f took 70250's EUR 31.00 in its
   round 2 ("it repeats its objection") while 70210 had just matched 31.00 - 0.510. 70250 agreed at 30.25 / 30.00 when
   asked again (7a89bc8f, e9eaf87e).
4. A bidder quoting a lead time above our must-have whose own frame contract sets one inside it (70240: quoted 52 d,
   ctr:4600070240 #5.1 = 42 d, and it charges EUR 2 for "42 days is too tight"): we say so, in prose, without the
   clause ID (a lone ctr ID is only checked for notice periods).
5. (v2) Hold the RFQ ask low: after round 1 it creeps at most EUR 0.15 a round and stays 6% under the market low. Live
   737bacd270dea248 (v1, 0.705): 70210 went 36.00 -> 30.50 on data, then agreed to our 29.05 once we stepped up from 28.61.
6. (v2) The first agreement is shown to the other live bidders above it for one round before it is accepted.
"""
import csv
import logging
from pathlib import Path

from arena_kit.agents.noidea import NoIdeaAgent as _Main
from arena_kit.cost import complete_offer, must_haves_ok, supplier_value
from arena_kit.play import latest, live_threads, standing

log = logging.getLogger("arena")
ROOT = next(p for p in Path(__file__).resolve().parents if (p / "datasets" / "A_dossiers.json").exists())


def _drivers(part):
    try:
        with open(ROOT / "tacto/data/data/cost_drivers.csv", encoding="utf-8") as f:
            return [{"series": r["series_id"], "weight": float(r["weight"])} for r in csv.DictReader(f)
                    if r["part_id"] == part]
    except OSError:
        return []


def _contract_days(facts, sid, kind):
    """Days of the clause of `kind` (delivery, payment ...) in our frame contract with this supplier, or None."""
    for k, v in facts.items():
        if k.startswith("ctr:") and "#" in k and v.get("supplier") == sid and v.get("type") == kind:
            return v.get("days")
    return None


RFQ_CREEP = 0.15  # 5. after round 1 our ask creeps at most EUR 0.15 (value) a round ...
RFQ_BELOW_LOW = 0.12  # ... at least 12% under the market low (live P05: 6% 0.755, 10% 0.81-0.82, 12% 0.871, 15% 0.865)
# experiments: hold the ask deeper under the market low (P05 f841e571: 70210 AGREED to our 28.57 = its floor is lower;
# record 0.924 ~ 27.00 @ 14 d; an extreme anchor made both bidders walk - Parth run 3)
import os as _os
_EXP = {x.strip() for x in _os.environ.get("NOIDEA_EXPERIMENTS", "").split(",") if x.strip()}
EXPERIMENTS_RFQ = _EXP
if "rfq_low10" in _EXP:
    RFQ_BELOW_LOW = 0.10
if "rfq_low15" in _EXP:
    RFQ_BELOW_LOW = 0.15
if "rfq_low12" in _EXP:
    RFQ_BELOW_LOW = 0.12


# HOLD PATH (Parth tools/experiments/p05_hold.py: P05 0.924 x6, 0.950, 0.965 - Fuchsreiter opened 38.50, agreed 26.60):
# a bidder opening far above the market gets ONE round without a price from us ("without movement from your side we cannot
# move either"), then a deep ask + the lowest rival ("we need to clarify this internally"), then ONE move; it then drops about
# a step a round and agrees to our standing ask. Parth held with a late reply (= a timeout); we hold with a no-price note
# (api.md: "a message without a term sheet is answered and the quote stands") - no timeout risk. Opt-out `no_hold_path`.
HOLD_HIGH = 1.15   # a bidder opening >= 15% above the lowest offer of the others is a high opener
HOLD_DEEP = 0.16   # first priced ask: 16% under the market low (Parth 25.54 vs 30.50)
HOLD_MOVE = 0.138  # the one move: 13.8% under (Parth 26.30)
HOLD_TAKE = 0.115  # take any of its offers at or under 11.5% below the market low at once (Parth 27.00)


class NoIdeaAgent(_Main):
    def _market_low_price(self, case, sid, opening=False):
        """Lowest PRICE of the OTHER bidders: their OPENING quotes, must-haves aside (the high-opener trigger in round 1),
        or their live standing offers that meet our must-haves (the hold thresholds, frozen at our first priced ask - in
        Parth's 0.965 that was 70210's first counter 30.50 -> 25.54 / 26.30 / 27.00)."""
        best = None
        for other in (self.threads_ref if opening else live_threads(self.threads_ref)):
            if other == sid or other not in self.sup:
                continue
            ev = self.threads_ref[other]
            t = complete_offer(case, (standing(ev[:1])[1] if opening else standing(ev)[1]) or {})
            if t.get("unit_price") and (opening or must_haves_ok(case, t, self.sup[other]["std"])):
                best = t["unit_price"] if best is None else min(best, t["unit_price"])
        return best

    def _high_opener(self, case, sid):
        if case["type"] != "rfq" or "no_hold_path" in EXPERIMENTS_RFQ or sid not in self.sup:
            return False
        if "hold_high" in self.sup[sid]:
            return self.sup[sid]["hold_high"]
        own = (self.sup[sid].get("open_terms") or {}).get("unit_price")
        low = self._market_low_price(case, sid, opening=True)
        self.sup[sid]["hold_high"] = bool(own and low and own >= low * HOLD_HIGH)
        if self.sup[sid]["hold_high"]:
            log.info("%s: high opener (%.2f vs market low %.2f) - hold path", sid, own, low)
        return self.sup[sid]["hold_high"]

    def value_target(self, case, sid, events):
        if self._high_opener(case, sid) and not self.sup[sid].get("hold_sent"):
            return self._value_target_rfq(case, sid, events)  # the note round: nothing priced goes out, freeze nothing
        if self._high_opener(case, sid):
            s = self.sup[sid]
            # thresholds frozen at our FIRST PRICED ask, after the note (Parth 0.965: the market low was 70210's 30.50 then)
            low = s.setdefault("hold_low", self._market_low_price(case, sid))
            hist = s.setdefault("ours", [])
            base = complete_offer(case, s["open_terms"])
            frac = HOLD_DEEP if not hist else HOLD_MOVE
            v = supplier_value(case, {**base, "unit_price": round(low * (1 - frac), 2)}, s["est"])
            v = max(v, hist[-1]) if hist else v
            hist.append(v)
            log.info("%s hold path ask: %.2f (%s)", sid, low * (1 - frac), "deep" if len(hist) == 1 else "the one move / hold")
            return v
        return self._value_target_rfq(case, sid, events)

    def _value_target_rfq(self, case, sid, events):
        """5. RFQ asks: data moves these bidders, our steps only hand them a deal. Live 737bacd270dea248: 70210 went
        36.00 -> 30.50 on the alloy fall + a rival, then AGREED to our 29.05 when we stepped up from 28.61 (0.705) -
        its floor was below our ask. Hold low, creep slowly, stay under the market low."""
        if case["type"] != "rfq":
            return super().value_target(case, sid, events)
        s = self.sup[sid]
        hist = s.get("ours")
        lows = []  # every live bidder's standing offer, valued with THIS bidder's cash rate (our asks are values)
        for other in live_threads(self.threads_ref):
            if other in self.sup:
                t = standing(self.threads_ref[other])[1] or {}
                if t.get("unit_price"):
                    lows.append(supplier_value(case, complete_offer(case, t), s["est"]))
        if not hist:
            # round 1: the base market anchor, but never above the cap - the base anchor came out at 28.61 (value) while
            # the cap was 27.45, and the no-backtracking creep kept every later ask above the cap (live fef71f65 /
            # 62a9e69f: 70210's 28.00 was below our own ask and was taken, 0.824)
            v = super().value_target(case, sid, events)
            if lows and "no_rfq_cap_r1" not in EXPERIMENTS_RFQ:
                v = min(v, min(lows) * (1 - RFQ_BELOW_LOW))
                s["ours"][-1] = v
            return v
        cap = min(lows) * (1 - RFQ_BELOW_LOW) if lows else hist[-1] + RFQ_CREEP
        nxt = max(hist[-1], min(hist[-1] + RFQ_CREEP, cap))
        hist.append(nxt)
        log.info("%s RFQ ask: %.2f (creep %.2f, cap %.2f = %.0f%% under the market low)", sid, nxt, RFQ_CREEP, cap,
                 RFQ_BELOW_LOW * 100)
        return nxt

    def decide(self, case, threads):
        try:
            return self._decide_layer(case, threads)
        except Exception:  # never crash a case: a crash ends it without a deal
            log.exception("RFQ layer failed - safe move instead")
            return self.safe_move(case, threads)

    def _decide_layer(self, case, threads):
        if case["type"] == "rfq" and case["case_id"] == getattr(self, "case_id", None):
            self.threads_ref = threads
            for sid in [x for x in live_threads(threads) if x in self.sup and self._high_opener(case, x)]:
                ev = threads[sid]
                st = latest(ev).get("status")
                t = complete_offer(case, standing(ev)[1] or {})
                low = self.sup[sid].get("hold_low")  # no take before the thresholds are frozen
                if st in ("open", "agreed", "final_offer") and t.get("unit_price") and low and \
                        t["unit_price"] <= low * (1 - HOLD_TAKE) and must_haves_ok(case, t, self.sup[sid]["std"]):
                    sh = standing(ev)[0]
                    if sh:
                        log.info("%s: hold path - its %.2f is under the take line %.2f: accept", sid, t["unit_price"],
                                 low * (1 - HOLD_TAKE))
                        return {"supplier_id": sid, "message": {"action": {"type": "accept", "term_sheet_id": sh}}}
        d = self._decide_rfq(case, threads)
        sid = d.get("supplier_id")
        if case["type"] == "rfq" and sid and self._high_opener(case, sid) and not self.sup[sid].get("hold_sent") \
                and not ((d.get("message") or {}).get("action")):
            self.sup[sid]["hold_sent"] = True
            self.sup[sid].pop("ours", None)  # the priced path starts with the deep ask next round
            log.info("%s: hold path - a note without a price this round", sid)
            return {"supplier_id": sid, "message": {
                "subject": f"Re: {case['title']}"[:300],
                "body": ("Dear team,\n\nThank you for your quote. We are comparing all offers for this part and will come "
                         "back to you with our terms.\n\nKind regards,\nPurchasing, Hollerau Pumpenwerke")}}
        return d

    def _decide_rfq(self, case, threads):
        """6. The first agreement is not accepted at once while another live bidder sits above it and has not seen it:
        that bidder gets it as a rival offer for one round (back office: "The buyer shows a much lower rival quote. I give
        half the step now and check the rest"); then the cheapest closing bidder is taken (P05_engine.md plan)."""
        if case["type"] == "rfq" and case["case_id"] == getattr(self, "case_id", None):
            self.threads_ref = threads
            live = [x for x in live_threads(threads) if x in self.sup]
            closing = [x for x in live if latest(threads[x]).get("status") in ("agreed", "final_offer")]
            if closing and len(live) > 1:
                price = {x: (standing(threads[x])[1] or {}).get("unit_price") for x in live}
                cb = min(closing, key=lambda x: price[x] or 1e9)
                # once per (other bidder, closing bidder) - never per sheet id: an unanswered bidder re-sends its offer
                # with a new id ("haven't heard back"), and the floor-stop sim looped 11 rounds on that (timeout)
                shown = self.__dict__.setdefault("_shown", set())
                pending = [x for x in live if x not in closing and price.get(x) and price[cb]
                           and price[x] > price[cb] and (x, cb) not in shown]
                if pending:
                    log.info("RFQ: %s closed at %.2f - showing it to %s before accepting", cb, price[cb], pending)
                    saved = self.focus
                    self.focus = set(pending)
                    try:
                        d = super().decide(case, threads)
                    finally:
                        self.focus = saved
                    shown.add((d.get("supplier_id"), cb))
                    if d.get("supplier_id") not in pending:  # the base turned elsewhere: don't block the close
                        shown.update((x, cb) for x in pending)
                    return d
        d = super().decide(case, threads)
        # 7. (v2.30) the base would ACCEPT an OPEN offer while other live bidders sit above it and have not seen it: show it
        #    to them first, once (live 62a9e69f: we took 70210's open 28.00 @ 30 d at once with two bidders live - 0.824).
        #    Not for agreed / final offers (handled above) and never twice per (bidder, offer).
        act = (d.get("message") or {}).get("action") or {}
        if case["type"] == "rfq" and act.get("type") == "accept" and "no_rfq_show_open" not in EXPERIMENTS_RFQ:
            sid = d.get("supplier_id")
            ev = threads.get(sid) or []
            live = [x for x in live_threads(threads) if x in self.sup]
            if ev and latest(ev).get("status") == "open" and len(live) > 1:
                price = {x: (standing(threads[x])[1] or {}).get("unit_price") for x in live}
                shown = self.__dict__.setdefault("_shown", set())
                pending = [x for x in live if x != sid and price.get(x) and price.get(sid)
                           and price[x] > price[sid] and (x, sid) not in shown]
                if pending:
                    log.info("RFQ: %s open at %.2f - showing it to %s before accepting", sid, price[sid], pending)
                    saved = self.focus
                    self.focus = set(pending)
                    try:
                        d2 = super().decide(case, threads)
                    finally:
                        self.focus = saved
                    shown.update((x, sid) for x in pending)
                    if d2.get("supplier_id") in pending and not ((d2.get("message") or {}).get("action") or {}):
                        return d2
        return d

    def rank_args(self, case, sid, ask_pct):
        if case["type"] == "rfq":  # 1. cost drivers for the RFQ part
            d = self.dossiers.setdefault(sid, {})
            parts = d.setdefault("parts", [])
            for part in case["parts"]:
                if not any(p.get("part") == part for p in parts) and (drv := _drivers(part)):
                    parts.append({"part": part, "description": "this part", "cost_drivers": drv})
                    log.info("%s: RFQ part %s gets its cost drivers %s", sid, part, [x["series"] for x in drv])
        return super().rank_args(case, sid, ask_pct)

    def rival_offer(self, case, sid):
        """2. The cheapest standing offer of any OTHER live bidder, at any lead time, if below this bidder's own."""
        if case["type"] != "rfq":
            return super().rival_offer(case, sid)
        live = set(live_threads(self.threads_ref))
        best = None
        for other in self.sup:
            if other == sid or other not in self.threads_ref or other not in live:
                continue
            sh, t = standing(self.threads_ref[other])
            if sh and t.get("unit_price") and (best is None or t["unit_price"] < best[1]):
                best = (sh, t["unit_price"])
        own = standing(self.threads_ref[sid])[1].get("unit_price") if sid in self.threads_ref else None
        if not best or (own and best[1] >= own) or (sid, best[0]) in self.cited:
            return None
        self.cited.add((sid, best[0]))
        return best

    def repeats_objection(self, events, case=None):
        """3. No walk-risk accept in an RFQ while another bidder is still in the game."""
        if case and case.get("type") == "rfq":
            others = [s for s in live_threads(self.threads_ref) if s in self.sup]
            if len(others) > 1:
                return False
        return super().repeats_objection(events, case)

    def write(self, case, sid, events, sheets, k, args, rival, final, given_opening=None):
        body = super().write(case, sid, events, sheets, k, args, rival, final, given_opening)
        # 4. its own frame contract already sets a lead time inside our must-have
        if case["type"] == "rfq" and k <= 1 and isinstance(body, str):
            quoted = (standing(events)[1] or {}).get("lead_time_days")
            ctr = _contract_days(self.all_facts, sid, "delivery")
            limit = next((m["value"] for m in case["buyer"].get("must_haves", [])
                          if m["field"] == "lead_time_days" and m["op"] in ("<=", "<")), None)
            if quoted and ctr and limit and quoted > limit >= ctr:
                line = f"Our frame contract with you already sets a delivery time of {ctr} days."
                if line not in body:
                    body = body.replace("\n\nKind regards", f"\n{line}\n\nKind regards", 1) if "\n\nKind regards" in body \
                        else body + "\n" + line
        return body
