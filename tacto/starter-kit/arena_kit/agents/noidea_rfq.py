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
from arena_kit.cost import complete_offer, supplier_value
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
RFQ_BELOW_LOW = 0.10  # ... and stays at least 10% under the lowest standing offer (6% -> 0.755, 10% -> 0.824 live, 12% -> 0.761 with a timeout)
# experiments: hold the ask deeper under the market low (P05 f841e571: 70210 AGREED to our 28.57 = its floor is lower;
# record 0.924 ~ 27.00 @ 14 d; an extreme anchor made both bidders walk - Parth run 3)
import os as _os
_EXP = {x.strip() for x in _os.environ.get("NOIDEA_EXPERIMENTS", "").split(",") if x.strip()}
EXPERIMENTS_RFQ = _EXP
if "rfq_low10" in _EXP:
    RFQ_BELOW_LOW = 0.10
if "rfq_low12" in _EXP:
    RFQ_BELOW_LOW = 0.12


class NoIdeaAgent(_Main):
    def value_target(self, case, sid, events):
        """5. RFQ asks: data moves these bidders, our steps only hand them a deal. Live 737bacd270dea248: 70210 went
        36.00 -> 30.50 on the alloy fall + a rival, then AGREED to our 29.05 when we stepped up from 28.61 (0.705) -
        its floor was below our ask. Hold low, creep slowly, stay under the market low."""
        if case["type"] != "rfq":
            return super().value_target(case, sid, events)
        s = self.sup[sid]
        hist = s.get("ours")
        if not hist:
            return super().value_target(case, sid, events)  # round 1: the market anchor
        lows = []  # every live bidder's standing offer, valued with THIS bidder's cash rate (our asks are values)
        for other in live_threads(self.threads_ref):
            if other in self.sup:
                t = standing(self.threads_ref[other])[1] or {}
                if t.get("unit_price"):
                    lows.append(supplier_value(case, complete_offer(case, t), s["est"]))
        cap = min(lows) * (1 - RFQ_BELOW_LOW) if lows else hist[-1] + RFQ_CREEP
        nxt = max(hist[-1], min(hist[-1] + RFQ_CREEP, cap))
        hist.append(nxt)
        log.info("%s RFQ ask: %.2f (creep %.2f, cap %.2f = %.0f%% under the market low)", sid, nxt, RFQ_CREEP, cap,
                 RFQ_BELOW_LOW * 100)
        return nxt

    def decide(self, case, threads):
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
