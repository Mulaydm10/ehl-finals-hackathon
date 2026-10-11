"""STATUS: READY TO RUN LIVE, NOT RUN (cloud session, offline only, 0 arena sessions) - 2026-10-11.
P18 "cross" variant of the team's main agent (tacto/starter-kit/arena_kit/agents/noidea.py, untouched). Gate: case:P18 only.
Report: analysis/cases/P18_deep.md (sections 4-7). The local P18 variant analysis/agent_variants/noidea_p18.py is untouched.

Target: beat Codacabana 0.75595 (EUR 4.90 @ 45 d, AS-14404 db0). Beat prices on 24 m with its db0 clause:
14 d 4.86, 30 d 4.88, 45 d 4.89, 60 d 4.91, 90 d 4.94.

The idea: our best game 0c968aae (0.727) with ONE change - from round 2 the payment term is 90 days instead of 14.
- Round 1 sets its first counter, and there the payment term counts: 4.76 @ 30 d drew 5.20 in 9 of 10 games, 4.77 @ 45 d drew
  5.30 in 8 of 13. Round 1 therefore stays exactly as in ed9a881a (same words, same facts): 4.76 @ 30 d, 24 m, no clause,
  order price path + AS-14404 -8.5% + PPI-C2431 -2.3%, cost-breakdown and committee request.
- After round 1 its cuts did not follow our payment term: from 5.20 it cut 0.20 in round 2 in 2 of 11 games when we moved to
  14 d and 1 of 3 when we stayed; the one move to LONGER payment (bf56d975, 14 -> 45 d) was not charged (5.20 -> 5.10). Whole
  games: the 30 -> 14 d path and the 45-day start scored the same (0.663 vs 0.658 mean, 10 and 12 games).
- 90 days are worth +0.055 to us against 14 d at the same price (5.00 @ 90 d = 0.721, @ 14 d = 0.666). Our three softest draws
  would all have beaten the record on 90 d: 0c968aae agreed 4.91 (0.781 on 90 d), a09d9536 4.94 (0.761), 6c2813ce 4.94 (0.761).
- Asks after round 1: 4.87, 4.93, 4.94 (= the 90-day beat price), each with a new fact (forecast, labour index, AS-14404 -5.5%
  since June). Round 3 steps +0.06: a step of +0.05 or more drew its 0.10 cut in 17 of 17 games, +0.04 or less in 2 of 9.
  Its standing offer at or under our next ask (by our cost) is taken.
- Guard: if its round-2 counter is not under its round-1 counter (90 d priced in), rounds 3-4 go back to 30 d, same asks.
- final_offer: main accepts its primary - except when that final carries a sheet that is cheaper for us by more than EUR 1,000:
  then that sheet goes back once (P18 only: 3 of 3 agreed - a99d02eb, 06f8f4f5, c4599331; main keeps this off elsewhere).
Expected (analysis/tools/p18_cross_check.py --odds, weights from the 40 games): 90 d free -> 0.725 a game, 18% to beat (normal
draw 5.00 @ 90 d = 0.721; soft draw 4.90-4.94 @ 90 d = 0.761-0.788); 90 d charged +0.10 / +0.20 -> 0.674 / 0.682, no beat.
Our 30 -> 14 d path now: 0.663 (10 games), no beat. The round-2 reply tells which: 5.10 or less on 90 d = free.
"""
import json
import logging
from pathlib import Path

from arena_kit.agents.noidea import NoIdeaAgent as _Main
from arena_kit.cost import complete_offer, total_cost
from arena_kit.play import latest, standing

log = logging.getLogger("arena")

P18_CASES = {"case:P18"}
OPEN = 4.76  # @ 30 d, 24 m, no clause (round 1 of 0c968aae / ed9a881a)
PAY = 90  # payment days from round 2 (60 = the cautious setting: beat price 4.91)
FALLBACK_PAY = 30  # rounds 3-4 when its round-2 counter on PAY days is not under its first counter
BEAT = {14: 4.86, 30: 4.88, 45: 4.89, 60: 4.91, 90: 4.94}  # highest db0 price that beats 0.75595 (24 m)
FACTS = {1: "forecast", 2: "lci", 3: "alloy_recent"}  # one new fact per e-mail (an empty repeat walked: fe806698)
OTD_FACT = False  # True: round 2 cites its on-time delivery (sc:70740@2026Q3, a case ref, never cited on P18) instead
HARVEST_EUR = 1000.0  # propose a cheaper alternative sheet back at final_offer when it saves us more than this
SIGN = "Kind regards,\nPurchasing, Hollerau Pumpenwerke"
FACTS_FILE = Path(__file__).resolve().parents[2] / "tacto/data/facts.json"


def asks(pay):
    """Our 2nd-4th asks with its db0 clause, ending at the beat price of PAY days (90 d: 4.87 / 4.93 / 4.94).
    Round 3 steps +0.06: a step of >= 0.05 drew its 0.10 cut in 17 of 17 games, <= 0.04 in 2 of 9. After a soft round-2
    counter (5.00) that same 4.93 still beats on 90 d whether it then cuts (4.90), agrees (4.93) or holds and agrees at
    our 4th ask (4.94, the a09d9536 / 6c2813ce close)."""
    top = BEAT.get(pay, 4.94)
    return {1: round(top - 0.07, 2), 2: round(top - 0.01, 2), 3: top}


class NoIdeaAgent(_Main):
    _all_facts = None

    @classmethod
    def facts_all(cls):
        if cls._all_facts is None:
            cls._all_facts = json.loads(FACTS_FILE.read_text(encoding="utf-8"))
        return cls._all_facts

    def _claim(self, sid, kind, series=None):
        for c in self.sup[sid]["args"]:
            if c["kind"] == kind and (series is None or c.get("series") == series) \
                    and not any(i in self.cited for i in c["ids"]):
                return c
        return None

    def _alloy_recent(self, sid):
        """AS-14404 over the last three months (2026-06 -> 2026-09: -5.5%): the series of its own clause, a different
        window from round 1's -8.5% (2024-11 -> 2025-10). Main's argument bank does not hold it."""
        f = self.facts_all()
        a, b = f.get("idx:AS-14404@2026-06"), f.get("idx:AS-14404@2026-09")
        ids = ["idx:AS-14404@2026-06", "idx:AS-14404@2026-09"]
        if not a or not b or any(i in self.cited for i in ids):
            return None
        pct = (b["value"] / a["value"] - 1) * 100
        return {"kind": "index_change", "series": "AS-14404", "ids": ids,
                "sentence": (f"Alloy surcharge 1.4404, Isartal Edelstahlwerk (fictional mill, derived) changed {pct:+.1f}% "
                             f"from 2026-06 to 2026-09 (idx:AS-14404@2026-06, idx:AS-14404@2026-09).")}

    def _otd(self, sid):
        """Its on-time delivery last quarter (sc:70740@2026Q3 is in P18's own refs; 81.0% against the 95% target of our
        quality agreement). One figure per sentence; the target goes in the next sentence without an id."""
        sc = self.facts_all().get("sc:70740@2026Q3")
        if not sc or "sc:70740@2026Q3" in self.cited or sc.get("supplier") != sid:
            return None
        return {"kind": "scorecard_otd", "ids": ["sc:70740@2026Q3"],
                "sentence": (f"Your on-time delivery in the last quarter was {sc['otd_pct']:.1f}% (sc:70740@2026Q3). "
                             "Our quality agreement sets a target of 95%.")}

    def _fact(self, sid, k):
        if k == 1 and OTD_FACT:
            return self._otd(sid) or self._claim(sid, "forecast")
        name = FACTS.get(k)
        c = (self._claim(sid, "forecast") if name == "forecast" else self._claim(sid, "index_change", "LCI-C")
             if name == "lci" else self._alloy_recent(sid) if name == "alloy_recent" else None)
        # never an e-mail without a new fact: take the next unused one
        return c or self._alloy_recent(sid) or self._claim(sid, "index_change", "LCI-C") or self._claim(sid, "forecast")

    def _send(self, case, sid, terms, body, ids):
        refs = sorted(set(ids))
        self.cited.update(refs)
        self.sup[sid]["last_main"] = dict(terms)  # main's monotone guard climbs from here
        return {"supplier_id": sid, "message": {"subject": f"Re: {case['title']}"[:300], "body": body,
                                                 "term_sheets": [{"terms": terms}], "refs": refs[:20]}}

    @staticmethod
    def _db0(case):
        return next((o for o in case["term_options"]["index_clause"] if o and not float(o.get("deadband_pct") or 0)), None)

    @staticmethod
    def _eq0(t):
        """Its price in db0 terms: it prices the 5% deadband at +0.10 and the 3% at about +0.05 (15 pairs, P18_deep.md)."""
        d = float(((t or {}).get("index_clause") or {}).get("deadband_pct") or 0)
        return (t.get("unit_price") or 0) - (0.10 if d >= 5 else 0.05 if d >= 3 else 0.0)

    def _pay(self, sid, events):
        """PAY from round 2; FALLBACK_PAY for rounds 3-4 when its round-2 counter on PAY days was not under its first one."""
        s = self.sup[sid]
        if "p18_pay" in s:
            return s["p18_pay"]
        sheets = [m["term_sheets"][0]["terms"] for m in events if m.get("from") != "buyer" and m.get("term_sheets")]
        if len(sheets) >= 3:  # opening, first counter, round-2 counter
            p1, p2 = sheets[1], sheets[2]
            if p2.get("payment_days") != PAY:  # it answered on another term: follow it (it would not take ours)
                s["p18_pay"] = p2.get("payment_days") or FALLBACK_PAY
                priced = None
            else:
                priced = (p1.get("unit_price") is not None and p2.get("unit_price") is not None
                          and self._eq0(p2) >= self._eq0(p1) - 1e-9)
                s["p18_pay"] = FALLBACK_PAY if priced else PAY
            log.info("%s P18 cross: round-2 counter %.2f @ %s d after %.2f @ %s d -> %s d from round 3%s", sid,
                     p2.get("unit_price") or 0, p2.get("payment_days"), p1.get("unit_price") or 0, p1.get("payment_days"),
                     s["p18_pay"], " (90 d priced in)" if priced else " (its own term)" if priced is None else "")
            return s["p18_pay"]
        return PAY

    def _harvest(self, case, sid, events):
        """At final_offer: a sheet in its last message that is cheaper for us than its primary by > HARVEST_EUR goes back once."""
        s = self.sup[sid]
        if s.get("p18_harvested"):
            return None
        sheets = latest(events).get("term_sheets") or []
        if len(sheets) < 2 or not sheets[0].get("terms"):
            return None
        c0 = total_cost(case, complete_offer(case, sheets[0]["terms"]), s["std"], s["est"])
        best = None
        for ts in sheets[1:]:
            t = complete_offer(case, ts.get("terms") or {})
            if t.get("unit_price") is None:
                continue
            c = total_cost(case, t, s["std"], s["est"])
            if c < c0 - HARVEST_EUR and (best is None or c < best[0]):
                best = (c, t)
        if not best:
            return None
        s["p18_harvested"] = True
        t = best[1]
        body = ("Dear Sir or Madam,\n\nThank you for your offer. We take your alternative as you proposed it: EUR "
                f"{t['unit_price']:.2f} per kg, {t['payment_days']} days net, {t.get('contract_months')} months, with your "
                "AS-14404 clause (term sheet attached). On your confirmation we will issue the order today.\n\n" + SIGN)
        log.info("%s P18 cross: its final carries a cheaper sheet (EUR %.0f less for us): %.2f @ %s d - proposed back", sid,
                 c0 - best[0], t["unit_price"], t["payment_days"])
        return {"supplier_id": sid, "message": {"subject": f"Re: {case['title']}"[:300], "body": body,
                                                 "term_sheets": [{"terms": t}], "refs": []}}

    def _decide(self, case, threads):
        if case["case_id"] not in P18_CASES:
            return super()._decide(case, threads)
        if case["case_id"] != self.case_id:
            self.prepare(case, threads)
        sid = next((x for x in case["suppliers"] if x in self.sup), None)
        events = threads.get(sid) or []
        if not events:
            return super()._decide(case, threads)
        status = latest(events).get("status")
        if status == "final_offer" and (h := self._harvest(case, sid, events)):
            return h
        if status != "open":
            return super()._decide(case, threads)  # agreed / final_offer: main accepts its primary
        k = sum(m.get("from") == "buyer" and bool(m.get("term_sheets")) for m in events)
        vol = case["fixed_terms"].get("volume_per_year") or case["buyer"]["need_per_year"]
        s = self.sup[sid]
        sheet_id, theirs = standing(events)
        ic = self._db0(case)
        if k == 0:
            path, alloy = self._claim(sid, "po_prices"), self._claim(sid, "index_change", "AS-14404")
            ppi = self._claim(sid, "index_change", "PPI-C2431")
            if path and alloy and ppi:
                t = complete_offer(case, {"unit_price": OPEN, "payment_days": 30, "contract_months": 24, "index_clause": None})
                body = ("Dear Sir or Madam,\n\nThank you for your proposal to agree the price basis for the coming period. We "
                        f"want to continue with you and confirm a binding volume of {vol} kg per year for 24 months.\n\n"
                        + path["sentence"] + " " + alloy["sentence"] + " " + ppi["sentence"] + "\n\n"
                        "We are prepared to make a longer-term commitment; please share your cost-breakdown XLSX so we can work "
                        "through the underlying elements together. We understand a change of this size needs your pricing "
                        "committee; please put this proposal to them.\n\n"
                        f"On this basis we propose EUR {OPEN:.2f} per kg, 30 days net, 24 months (term sheet attached).\n\n{SIGN}")
                log.info("%s P18 cross r1: %.2f @ 30 d / 24 m + price path, AS-14404, PPI-C2431", sid, OPEN)
                return self._send(case, sid, t, body, path["ids"] + alloy["ids"] + ppi["ids"])
            return super()._decide(case, threads)
        if k in (1, 2, 3) and ic:
            pay = PAY if k == 1 else self._pay(sid, events)
            plan = asks(PAY)  # same prices after a fallback to 30 d (a fallback cannot beat; it keeps the steps)
            ask = plan[k]
            last = (self.sup[sid].get("last_main") or {}).get("unit_price")
            if last is not None and ask < last:  # never under our own last ask (P02: "without movement from your side")
                ask = last
            t = complete_offer(case, {"unit_price": ask, "payment_days": pay, "contract_months": 24, "index_clause": ic})
            c_ask = total_cost(case, t, s["std"], s["est"])
            if sheet_id and theirs.get("unit_price") is not None:
                c_theirs = total_cost(case, complete_offer(case, theirs), s["std"], s["est"])
                if c_theirs <= c_ask + 1:  # its standing offer already costs us no more than our next ask
                    log.info("%s P18 cross: its %.2f @ %s d is at or under our next ask %.2f @ %s d - accept", sid,
                             theirs["unit_price"], theirs.get("payment_days"), ask, pay)
                    return {"supplier_id": sid, "message": {"action": {"type": "accept", "term_sheet_id": sheet_id}}}
            fact = self._fact(sid, k)
            lead = {1: "Thank you for your offer. We accept your AS-14404 price adjustment clause with no deadband, as your "
                       "letter of 22 September proposed, and we move on price.",
                    2: "Thank you for your step. We move again.",
                    3: "Thank you. We take one more step to close today."}[k]
            body = (f"Dear Sir or Madam,\n\n{lead}\n\n" + (fact["sentence"] + "\n\n" if fact else "")
                    + f"We propose EUR {ask:.2f} per kg with your AS-14404 clause, {pay} days net, 24 months (term sheet "
                      "attached)." + (" On your confirmation we will issue the order." if k == 3 else "") + f"\n\n{SIGN}")
            log.info("%s P18 cross msg %d: %.2f @ %s d db0 (its %.2f @ %s d) + %s", sid, k + 1, ask, pay,
                     theirs.get("unit_price") or 0, theirs.get("payment_days"), fact["kind"] if fact else "no fact")
            return self._send(case, sid, t, body, fact["ids"] if fact else [])
        return super()._decide(case, threads)
