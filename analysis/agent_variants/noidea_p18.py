"""P18 variant of the team's main agent (Dhruv's tacto/starter-kit/arena_kit/agents/noidea.py, untouched here). Gate: case:P18.
Reports: analysis/cases/P18_lever.md (cloud handoff section 1-6, live v1 section 7, v2 section 8, why scores fell section 9).

Record to beat: Codacabana 0.75595 = EUR 4.90 @ 45 d, AS-14404 clause db0. Werdenfels charges ~EUR 0.10/kg per 30 days of payment,
so we stay on 14 d: beat = <= 4.86 @ 14 d db0 (0.761).

History of this file:
- v1 (fd5b66b1, 0.621): main's path + the 36-month move held for round 3 -> worth 0 ("our lowest possible price of EUR 5.20").
- v2 (a55d2e89, 0.606): our contract's index clause (October value 5.74) -> worth 0 (first counter 5.20 as without it); a smaller
  round-2 step (4.76 -> 4.84, +0.08) drew -0.10 instead of -0.20; a db5 switch in round 3 was no move -> its final.

Why recent P18 scores fell (all 25 games): main v2.34+ opens at 45 d and never switches to 14 d (7 games, 0.62-0.69); the best two
games (0c968aae 0.727, a09d9536 0.707, main v2.27/v2.28) opened at 30 d, switched to 14 d in round 2 with a +0.11 step
(5.20 -> 5.00) and closed by its agreeing at our ask (4.91 / 4.94).

v3 (this file) = that best path, plus one change that makes a record possible:
- round 1: one sheet 4.76 @ 30 d / 24 m, no clause; price path + AS-14404 -8.5% + PPI-C2431 -2.3% (main's claims) + the
  cost-breakdown request + the committee request (as in 0c968aae);
- round 2: 4.86 @ 14 d with its clause (+0.10, the best game's step size) + forecast;
- round 3: HOLD 4.86 @ 14 d db0 + the labour index (a new fact, so not an empty repeat). Agreed -> 0.761 (beats); refused -> main
  climbs monotone from 4.86 (the 0.707 / 0.727 games' path).
"""
import logging

from arena_kit.agents.noidea import NoIdeaAgent as _Main
from arena_kit.cost import complete_offer
from arena_kit.play import latest, standing

log = logging.getLogger("arena")

P18_CASES = {"case:P18"}
R1 = {"unit_price": 4.76, "payment_days": 30, "contract_months": 24, "index_clause": None}
ASK, DAYS = 4.86, 14  # round 2 ask, held in round 3 (<= 4.86 @ 14 d db0 beats 0.75595)
SIGN = "Kind regards,\nPurchasing, Hollerau Pumpenwerke"


class NoIdeaAgent(_Main):
    def _claim(self, sid, kind, series=None):
        for c in self.sup[sid]["args"]:
            if c["kind"] == kind and (series is None or c.get("series") == series) \
                    and not any(i in self.cited for i in c["ids"]):
                return c
        return None

    def _send(self, case, sid, terms, body, ids):
        refs = sorted(set(ids))
        self.cited.update(refs)
        self.sup[sid]["last_main"] = dict(terms)  # main's monotone guard climbs from here
        return {"supplier_id": sid, "message": {"subject": f"Re: {case['title']}"[:300], "body": body,
                                                 "term_sheets": [{"terms": terms}], "refs": refs[:20]}}

    def _decide(self, case, threads):
        if case["case_id"] not in P18_CASES:
            return super()._decide(case, threads)
        if case["case_id"] != self.case_id:
            self.prepare(case, threads)
        sid = next((x for x in case["suppliers"] if x in self.sup), None)
        events = threads.get(sid) or []
        if not events or latest(events).get("status") != "open":
            return super()._decide(case, threads)
        k = sum(m.get("from") == "buyer" and bool(m.get("term_sheets")) for m in events)
        vol = case["fixed_terms"].get("volume_per_year") or case["buyer"]["need_per_year"]
        theirs = standing(events)[1] or {}
        if k == 0:
            path, alloy = self._claim(sid, "po_prices"), self._claim(sid, "index_change", "AS-14404")
            ppi = self._claim(sid, "index_change", "PPI-C2431")
            if path and alloy and ppi:
                t = complete_offer(case, dict(R1))
                body = ("Dear Sir or Madam,\n\nThank you for your proposal to agree the price basis for the coming period. We "
                        f"want to continue with you and confirm a binding volume of {vol} kg per year for 24 months.\n\n"
                        + path["sentence"] + " " + alloy["sentence"] + " " + ppi["sentence"] + "\n\n"
                        "We are prepared to make a longer-term commitment; please share your cost-breakdown XLSX so we can work "
                        "through the underlying elements together. We understand a change of this size needs your pricing "
                        "committee; please put this proposal to them.\n\n"
                        f"On this basis we propose EUR {R1['unit_price']:.2f} per kg, 30 days net, 24 months (term sheet "
                        f"attached).\n\n{SIGN}")
                log.info("%s P18 v3 round 1: 4.76 @ 30 d / 24 m + price path, AS-14404, PPI-C2431", sid)
                return self._send(case, sid, t, body, path["ids"] + alloy["ids"] + ppi["ids"])
        ic = theirs.get("index_clause")
        db0 = ic is not None and not float(ic.get("deadband_pct") or 0)
        if k == 1 and ic:
            fc = self._claim(sid, "forecast")
            t = complete_offer(case, {"unit_price": ASK, "payment_days": DAYS, "contract_months": 24, "index_clause": ic})
            body = ("Dear Sir or Madam,\n\nThank you for your offer. We accept your AS-14404 price adjustment clause, and we "
                    "will pay faster: 14 days net instead of 30.\n\n" + (fc["sentence"] + "\n\n" if fc else "")
                    + f"We propose EUR {ASK:.2f} per kg with your AS-14404 clause, 14 days net, 24 months (term sheet attached)."
                    f"\n\n{SIGN}")
            log.info("%s P18 v3 round 2: %.2f @ 14 d + its clause + forecast (its %.2f)", sid, ASK, theirs.get("unit_price") or 0)
            return self._send(case, sid, t, body, fc["ids"] if fc else [])
        if k == 2 and db0 and (theirs.get("payment_days") or 99) <= DAYS and (theirs.get("unit_price") or 0) > ASK + 1e-9:
            lab = self._claim(sid, "index_change", "LCI-C")
            if lab:
                t = complete_offer(case, {"unit_price": ASK, "payment_days": DAYS, "contract_months": 24, "index_clause": ic})
                body = ("Dear Sir or Madam,\n\nThank you for your step. We are close.\n\n" + lab["sentence"] + "\n\n"
                        f"We propose EUR {ASK:.2f} per kg with your AS-14404 clause, 14 days net, 24 months (term sheet "
                        f"attached). On your confirmation we will issue the order.\n\n{SIGN}")
                log.info("%s P18 v3 round 3: hold %.2f @ 14 d db0 (its %.2f) + labour", sid, ASK, theirs["unit_price"])
                return self._send(case, sid, t, body, lab["ids"])
        return super()._decide(case, threads)
