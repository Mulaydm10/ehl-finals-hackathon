"""P18 "cross + harvest" (local, Neel, 2026-10-11) = the cloud's noidea_p18_cross.py UNCHANGED (round 1 4.76 @ 30 d, 90 d
from round 2, asks 4.87 / 4.93 / 4.94, guard back to 30 d, harvest at final_offer; analysis/cases/P18_deep.md) plus one change
for the NORMAL draw and two safety rules. Gate case:P18; every other case = main.

Why: on 90 d only the soft draw (its round-2 counter 5.00, about 1 game in 5) can beat 0.75595. In the normal draw
(5.20 -> 5.10 -> 5.00) our 4th message draws its final at the standing price (16 of 16): 5.00 @ 90 d = 0.721, no beat.
But a final can carry an ALTERNATIVE, and proposing its own alternative back was agreed 3 of 3 on P18 (a99d02eb, 06f8f4f5,
c4599331). It writes one when we send two payment terms: our shorter term 0.10 cheaper (06f8f4f5 final 5.30 @ 30 | 5.20 @ 14,
c4599331 final 5.40 @ 45 | 5.30 @ 14, 928a3878, 92616dfb) or the shorter term with db5 at the same price (6833e98f x3,
c4599331 / 9d4d288e / 92616dfb round 1); its primary stays on the term that is best for it (the longer one at our prices).
With 5.00 @ 90 d as its final, both kinds beat the record: 4.90 @ 60 d db0 = 0.767, 5.00 @ 60 d db5 = 0.773.

1. Our 4th message after its round-3 CUT (the normal-draw signature): two sheets, 4.94 @ 90 d (the cloud's ask) and
   4.84 @ 60 d (0.10 less for 30 days shorter, the way its own alternatives price it), same db0 clause, 24 m, one new
   fact. After a HOLD (soft draw) the cloud's single 4.94 stays: after a hold that ask was agreed 2 of 2 (a09d9536,
   6c2813ce). After the 30-d fallback the second sheet is 14 d (no beat possible there; 4.90 @ 14 = 0.734 > 5.00 @ 30).
2. Its primary scores above the record -> accept at once.
3. One of its alternatives scores above the record (open or final) -> propose it back once (its own sheet).
Not run before 2026-10-11 ~03:40 CEST. Replay: scratchpad rpv over all 40 games + the cloud's p18_cross_check.py.
"""
import importlib.util
import logging
import sys
from pathlib import Path

from arena_kit.cost import complete_offer, total_cost
from arena_kit.play import latest, standing

_spec = importlib.util.spec_from_file_location("arena_kit.agents._p18_cross_base",
                                               Path(__file__).with_name("noidea_p18_cross.py"))
_cross = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _cross
_spec.loader.exec_module(_cross)

log = logging.getLogger("arena")

RECORD = 0.75595  # Codacabana: 4.90 @ 45 d, AS-14404 db0
C_OPEN, C_BEST = 295173.23, 222651.27
STEP = 0.10  # its alternatives price one shorter payment step at EUR 0.10 (P18_deep.md 3.6)
SIGN = _cross.SIGN


class NoIdeaAgent(_cross.NoIdeaAgent):
    def _score(self, case, sid, terms):
        s = self.sup[sid]
        return (C_OPEN - total_cost(case, complete_offer(case, dict(terms)), s["std"], s["est"])) / (C_OPEN - C_BEST)

    def _beating_alt(self, case, sid, msg):
        """(score, terms) of its best alternative sheet in msg when it beats the record and saves us more than
        HARVEST_EUR against its primary; None otherwise."""
        sheets = msg.get("term_sheets") or []
        t0 = (sheets[0].get("terms") or {}) if sheets else {}
        if len(sheets) < 2 or t0.get("unit_price") is None:
            return None
        s0 = self._score(case, sid, t0)
        best = None
        for ts in sheets[1:]:
            t = ts.get("terms") or {}
            if t.get("unit_price") is None:
                continue
            sc = self._score(case, sid, t)
            if sc > RECORD and (sc - s0) * (C_OPEN - C_BEST) > _cross.HARVEST_EUR and (best is None or sc > best[0]):
                best = (sc, complete_offer(case, dict(t)))
        return best

    def _two_sheets(self, case, sid, events):
        """Our 4th message after its round-3 cut: the cloud's 4.94 on our term plus the next shorter term 0.10 cheaper."""
        ic = self._db0(case)
        sheets = [m["term_sheets"][0]["terms"] for m in events if m.get("from") != "buyer" and m.get("term_sheets")]
        if not ic or len(sheets) < 4:
            return None
        p2, p3 = sheets[2], sheets[3]
        if p2.get("unit_price") is None or p3.get("unit_price") is None or not self._eq0(p3) < self._eq0(p2) - 1e-9:
            return None  # it held (soft draw): the cloud's single 4.94 (agreed 2 of 2 after a hold)
        pay = self._pay(sid, events)
        shorter = max((d for d in case["term_options"]["payment_days"] if d < pay), default=None)
        if shorter is None:
            return None
        s = self.sup[sid]
        ask = _cross.asks(_cross.PAY)[3]
        last = (s.get("last_main") or {}).get("unit_price")
        if last is not None and ask < last:
            ask = last
        t1 = complete_offer(case, {"unit_price": ask, "payment_days": pay, "contract_months": 24, "index_clause": ic})
        sheet_id, theirs = standing(events)
        if sheet_id and theirs.get("unit_price") is not None and \
                total_cost(case, complete_offer(case, theirs), s["std"], s["est"]) <= total_cost(case, t1, s["std"], s["est"]) + 1:
            return None  # its standing offer is at or under our ask: the cloud's code accepts it
        ask2 = round(ask - STEP, 2)
        t2 = complete_offer(case, {"unit_price": ask2, "payment_days": shorter, "contract_months": 24, "index_clause": ic})
        fact = self._fact(sid, 3)
        body = ("Dear Sir or Madam,\n\nThank you. We take one more step to close today.\n\n"
                + (fact["sentence"] + "\n\n" if fact else "")
                + f"We propose EUR {ask:.2f} per kg with your AS-14404 clause, {pay} days net, 24 months. If a shorter "
                  f"payment term suits you better, we propose EUR {ask2:.2f} per kg on {shorter} days net with the same "
                  f"clause and contract ({pay - shorter} days earlier payment for EUR 0.10 per kg). Both term sheets are "
                  f"attached; on your confirmation of either we will issue the order.\n\n{SIGN}")
        refs = sorted(set(fact["ids"] if fact else []))
        self.cited.update(refs)
        s["last_main"] = dict(t1)  # main's monotone guard climbs from our primary ask
        log.info("%s P18 harvest msg 4: %.2f @ %s d + %.2f @ %s d db0 (its %.2f -> %.2f: a cut, its final is next) + %s",
                 sid, ask, pay, ask2, shorter, p2["unit_price"], p3["unit_price"], fact["kind"] if fact else "no fact")
        return {"supplier_id": sid, "message": {"subject": f"Re: {case['title']}"[:300], "body": body,
                                                 "term_sheets": [{"terms": t1}, {"terms": t2}], "refs": refs[:20]}}

    def _decide(self, case, threads):
        if case["case_id"] not in _cross.P18_CASES:
            return super()._decide(case, threads)
        if case["case_id"] != self.case_id:
            self.prepare(case, threads)
        sid = next((x for x in case["suppliers"] if x in self.sup), None)
        events = threads.get(sid) or []
        if not events:
            return super()._decide(case, threads)
        msg = latest(events)
        status = msg.get("status")
        s = self.sup[sid]
        k = sum(m.get("from") == "buyer" and bool(m.get("term_sheets")) for m in events)
        if status in ("open", "final_offer") and k >= 1:
            sheet_id, theirs = standing(events)
            if sheet_id and theirs.get("unit_price") is not None and self._score(case, sid, theirs) > RECORD:
                log.info("%s P18 harvest: its %.2f @ %s d scores %.4f > record - accept", sid, theirs["unit_price"],
                         theirs.get("payment_days"), self._score(case, sid, theirs))
                return {"supplier_id": sid, "message": {"action": {"type": "accept", "term_sheet_id": sheet_id}}}
            alt = None if s.get("p18_harvested") else self._beating_alt(case, sid, msg)
            if alt:
                s["p18_harvested"] = True
                t = alt[1]
                body = ("Dear Sir or Madam,\n\nThank you for your offer. We take your alternative as you proposed it: EUR "
                        f"{t['unit_price']:.2f} per kg, {t['payment_days']} days net, {t.get('contract_months')} months, "
                        "with your AS-14404 clause (term sheet attached). On your confirmation we will issue the order "
                        f"today.\n\n{SIGN}")
                log.info("%s P18 harvest: its alternative %.2f @ %s d scores %.4f > record - proposed back (%s)", sid,
                         t["unit_price"], t["payment_days"], alt[0], status)
                return {"supplier_id": sid, "message": {"subject": f"Re: {case['title']}"[:300], "body": body,
                                                         "term_sheets": [{"terms": t}], "refs": []}}
        if status == "open" and k == 3 and (two := self._two_sheets(case, sid, events)):
            return two
        return super()._decide(case, threads)
