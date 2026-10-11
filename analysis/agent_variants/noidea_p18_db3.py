"""P18 "45 d + db3" variant (local, Neel, 2026-10-11 ~04:15). Gate case:P18; every other case = main. Built on
noidea_p18_soft.py (helpers, accept / harvest rules); rounds 2-4 replaced. Analysis: analysis/cases/P18_lever.md section 14.

Why (our best 0c968aae = 0.727 was a soft session; every other game stopped at its floor EUR 5.00 db0-equivalent):
- A better STRUCTURE at the same 5.00 is the only way past 0.727 in a normal session.
- 45 d is free at its floor: 8 games ended at 5.00 @ 45 d (3cb62cb9, 0371de5b, 57e43ef7, dad91454, ff6a6b20, 2ad8b190, bf56d975
  which moved 14 -> 45 d after round 1, 6c2813ce went 45 d -> 4.94 @ 30 d) - +0.011 against 30 d. 90 d is charged (+0.10, f2770f53).
- The 3% deadband: the one game that offered it (bf73ee39) got 5.40 db3 from 5.50 db0 = its normal 0.10 step, i.e. no charge;
  its replies list "a Preisgleitklausel on AS-14404, AS-14404, AS-14404" (db0 / db3 / db5). The scorer values db3 at 1.35% of
  spend under db0 (EUR 0.0675/kg). Our framework agreement already adjusts only on index moves above 3% (ctr:4600070740 3.2).
- If both hold: normal session -> final 5.00 @ 45 d db3 = 0.732 (> 0.727); soft session -> 4.91-4.94 @ 45 d db3 = 0.79-0.77
  (> 0.756). If db3 is charged (+0.10): 5.10 db3 @ 45 d = 0.666 - a practice game only counts if it is a new best.

Plan: msg 1 = the cloud's round 1 (4.76 @ 30 d, deterministic 5.20); msg 2 = 4.87 @ 45 d db3 + forecast; then on its clause
(db3 if it kept it, else its own) at 45 d: soft (round-2 primary <= 5.00 in db0 terms) 4.91 -> 4.94 (the 0c968aae / a09d9536
asks); normal 4.93 -> 4.94 -> its final. Accept at once if its primary beats the record; propose back a beating alternative.
"""
import importlib.util
import logging
import sys
from pathlib import Path

from arena_kit.play import latest, standing

_spec = importlib.util.spec_from_file_location("arena_kit.agents._p18_soft_for_db3",
                                               Path(__file__).with_name("noidea_p18_soft.py"))
_soft = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _soft
_spec.loader.exec_module(_soft)

log = logging.getLogger("arena")

PAY, DB = 45, 3
R2_PRICE = 4.87
SOFT_ASKS = {2: 4.91, 3: 4.94}
NORMAL_ASKS = {2: 4.93, 3: 4.94}
SIGN = _soft.SIGN
_words = _soft._words


class NoIdeaAgent(_soft.NoIdeaAgent):
    def _decide(self, case, threads):
        if case["case_id"] not in _soft._cross.P18_CASES:
            return super()._decide(case, threads)
        if case["case_id"] != self.case_id:
            self.prepare(case, threads)
        sid = next((x for x in case["suppliers"] if x in self.sup), None)
        events = threads.get(sid) or []
        if not events:
            return super()._decide(case, threads)
        status = latest(events).get("status")
        s = self.sup[sid]
        k = sum(m.get("from") == "buyer" and bool(m.get("term_sheets")) for m in events)
        sheet_id, theirs = standing(events)
        if status != "open" or k == 0 or k > 3 or not self._db0(case):
            return super()._decide(case, threads)  # msg 1, final / agreed, accept / harvest rules: noidea_p18_soft
        if theirs.get("unit_price") is not None and self._score(case, sid, theirs) > _soft.RECORD:
            return super()._decide(case, threads)  # noidea_p18_soft accepts a primary that beats the record
        if k == 1:
            fact = self._next_fact(sid, ("forecast", "lci", "otd"))
            body = ("Dear Sir or Madam,\n\nThank you for your offer. We accept your AS-14404 price adjustment clause, with a 3% "
                    "deadband as in our current framework agreement, where the price adjusts only when the index moves more "
                    "than 3%. We move on price and on payment.\n\n" + (fact["sentence"] + "\n\n" if fact else "")
                    + f"We propose {_words(R2_PRICE, PAY, DB)} (term sheet attached).\n\n{SIGN}")
            log.info("%s P18 db3 msg 2: %.2f @ %s d db%s (its %.2f) + %s", sid, R2_PRICE, PAY, DB,
                     theirs.get("unit_price") or 0, fact["kind"] if fact else "no fact")
            return self._sendn(case, sid, [self._sheet(case, R2_PRICE, PAY, DB)], body, fact["ids"] if fact else [])
        db = int(float((theirs.get("index_clause") or {}).get("deadband_pct") or 0)) if theirs.get("index_clause") else DB
        if "p18_soft" not in s:  # judged once, on its round-2 counter (db0 terms: db3 counted as free here)
            p0 = (theirs.get("unit_price") or 9.0) - (0.10 if db >= 5 else 0.0)
            s["p18_soft"] = p0 <= _soft.SOFT_LINE + 1e-9
            log.info("%s P18 db3: round-2 primary %.2f @ %s d db%s -> %s session", sid, theirs.get("unit_price") or 0,
                     theirs.get("payment_days"), db, "SOFT" if s["p18_soft"] else "normal")
        p = (SOFT_ASKS if s["p18_soft"] else NORMAL_ASKS)[k]
        last = (s.get("last_main") or {}).get("unit_price")
        if last is not None and p < last:
            p = last
        t = self._sheet(case, p, PAY, db)
        c_t = self._score(case, sid, t)
        if sheet_id and theirs.get("unit_price") is not None and self._score(case, sid, theirs) >= c_t - 1e-9:
            log.info("%s P18 db3: its %.2f scores at least our next ask %.2f - accept", sid, theirs["unit_price"], p)
            return {"supplier_id": sid, "message": {"action": {"type": "accept", "term_sheet_id": sheet_id}}}
        fact = self._next_fact(sid, ("lci", "otd", "forecast") if k == 2 else ("otd", "lci", "forecast"))
        lead = ("Thank you for your step. We move again." if k == 2 else
                "Thank you. We take one more step to close today.")
        body = (f"Dear Sir or Madam,\n\n{lead}\n\n" + (fact["sentence"] + "\n\n" if fact else "")
                + f"We propose {_words(p, PAY, db)} (term sheet attached)."
                + (" What is the lowest price at which you can sign these terms today?" if k == 2 else
                   " On your confirmation we will issue the order.") + f"\n\n{SIGN}")
        log.info("%s P18 db3 msg %d (%s): %.2f @ %s d db%s (its %.2f, %.4f) + %s", sid, k + 1,
                 "SOFT" if s["p18_soft"] else "normal", p, PAY, db, theirs.get("unit_price") or 0, c_t,
                 fact["kind"] if fact else "no fact")
        return self._sendn(case, sid, [t], body, fact["ids"] if fact else [])
