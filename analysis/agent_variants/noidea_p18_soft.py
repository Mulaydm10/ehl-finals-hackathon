"""P18 "soft-session" variant (local, Neel, 2026-10-11 ~04:30). Gate case:P18; every other case = main. Built on the cloud's
noidea_p18_cross.py (its round 1, facts and helpers); rounds 2-4 replaced. Analysis: analysis/cases/P18_lever.md section 13.

What 43 P18 games say (all in datasets/runs + tools/replays/raw):
- Round 1 = ed9a881a's e-mail (4.76 @ 30 d, no clause, order prices + AS-14404 -8.5% + PPI-C2431 -2.3%): first counter 5.20
  in 8 of 8 games with exactly this input - deterministic.
- Its own counters never went under EUR 5.00 in 43 games. Every price under 5.00 was it AGREEING TO OUR ASK: 0c968aae 4.91
  at once, a09d9536 / 6c2813ce 4.94 after one hold. In normal sessions it went final at 5.00 even on asks 0.4-0.8% under it
  (4.96-4.98, 16 of 16). So each session has a hidden acceptance floor R: 5.00 in ~4 of 5 sessions, about 4.88-4.94 in the
  rest. The soft sessions showed at round 2: primary 5.00 (with a db5 alternative at 5.10), not 5.10.
- Codacabana's record 4.90 @ 45 d db0 = a soft session with R <= ~4.89. To beat it R must be <= ~4.89 in its value.
- Werdenfels charges a longer payment term in its counters (f2770f53: 90 d +0.10) and gives nothing for 14 d; db5 = db0 + 0.10
  (15 pairs); db3 priced like db0 in the one game that offered it (bf73ee39: 5.50 db0 -> 5.40 db3).

Plan:
- msg 1: the cloud's round 1 unchanged (-> 5.20).
- msg 2: 4.87 @ 30 d with its db0 clause + forecast (one fact).
- msg 3, SOFT session (its round-2 primary <= 5.00 in db0 terms): three sheets that all beat 0.75595, so it can agree to
  whichever clears its floor - 4.88 @ 30 d db0 (0.759; the same value to it under any pricing), 4.94 @ 30 d db3 (0.762; its
  value is 4.94 if db3 costs it nothing as in bf73ee39), 4.94 @ 90 d db0 (0.761; 4.94 if it ignores payment when it agrees)
  + labour index. msg 4 after a hold: 4.99 @ 30 d db5 (0.758; 4.89 at its EUR 0.10 deadband price) + the db3 and 90-d sheets
  + its on-time delivery (sc:70740@2026Q3, never cited on P18).
- msg 3-4, NORMAL session (round-2 primary 5.10): the proven path 4.93 -> 4.94 @ 30 d db0 -> its final 5.00 (0.677); no beat
  is possible there (R = 5.00), so nothing is risked on it.
- Any time: its primary scores above the record -> accept; one of its alternatives does -> propose it back once.
"""
import importlib.util
import logging
import sys
from pathlib import Path

from arena_kit.cost import complete_offer, total_cost
from arena_kit.play import latest, standing

_spec = importlib.util.spec_from_file_location("arena_kit.agents._p18_cross_for_soft",
                                               Path(__file__).with_name("noidea_p18_cross.py"))
_cross = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _cross
_spec.loader.exec_module(_cross)

log = logging.getLogger("arena")

RECORD = 0.75595  # Codacabana: 4.90 @ 45 d, AS-14404 db0
C_OPEN, C_BEST = 295173.23, 222651.27
SOFT_LINE = 5.00  # its round-2 primary at or under this (db0 terms) = a soft session
R2 = (4.87, 30, 0)  # msg 2: price, payment days, deadband
SOFT_R3 = ((4.88, 30, 0), (4.94, 30, 3), (4.94, 90, 0))  # all beat: 0.7588 / 0.7617 / 0.7612
SOFT_R4 = ((4.99, 30, 5), (4.94, 30, 3), (4.94, 90, 0))  # all beat: 0.7576 / 0.7617 / 0.7612
NORMAL = {2: (4.93, 30, 0), 3: (4.94, 30, 0)}  # the proven path to its final 5.00 @ 30 d
SIGN = _cross.SIGN


def _words(p, d, db):
    clause = "your AS-14404 clause" if not db else f"the AS-14404 clause at a {db}% deadband"
    return f"EUR {p:.2f} per kg with {clause}, {d} days net, 24 months"


class NoIdeaAgent(_cross.NoIdeaAgent):
    def _score(self, case, sid, terms):
        s = self.sup[sid]
        return (C_OPEN - total_cost(case, complete_offer(case, dict(terms)), s["std"], s["est"])) / (C_OPEN - C_BEST)

    @staticmethod
    def _clause(case, db):
        return next(o for o in case["term_options"]["index_clause"] if o and float(o.get("deadband_pct") or 0) == db)

    def _sheet(self, case, p, d, db):
        return complete_offer(case, {"unit_price": p, "payment_days": d, "contract_months": 24, "index_clause": self._clause(case, db)})

    def _next_fact(self, sid, order):
        for name in order:
            c = (self._claim(sid, "forecast") if name == "forecast" else
                 self._claim(sid, "index_change", "LCI-C") if name == "lci" else
                 self._otd(sid) if name == "otd" else self._alloy_recent(sid) if name == "alloy" else None)
            if c:
                return c
        return None

    def _sendn(self, case, sid, sheets, body, ids):
        refs = sorted(set(ids))
        self.cited.update(refs)
        self.sup[sid]["last_main"] = dict(sheets[0])  # main's monotone guard (msg 5+) climbs from our first sheet
        return {"supplier_id": sid, "message": {"subject": f"Re: {case['title']}"[:300], "body": body,
                                                 "term_sheets": [{"terms": t} for t in sheets], "refs": refs[:20]}}

    def _beating_alt(self, case, sid, msg):
        sheets = msg.get("term_sheets") or []
        t0 = (sheets[0].get("terms") or {}) if sheets else {}
        if len(sheets) < 2 or t0.get("unit_price") is None:
            return None
        best = None
        for ts in sheets[1:]:
            t = ts.get("terms") or {}
            if t.get("unit_price") is not None and (sc := self._score(case, sid, t)) > RECORD and (best is None or sc > best[0]):
                best = (sc, complete_offer(case, dict(t)))
        return best

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
        sheet_id, theirs = standing(events)
        if status in ("open", "final_offer", "agreed") and k >= 1:
            if sheet_id and theirs.get("unit_price") is not None and (sc := self._score(case, sid, theirs)) > RECORD:
                log.info("%s P18 soft: its %.2f @ %s d scores %.4f > record - accept", sid, theirs["unit_price"],
                         theirs.get("payment_days"), sc)
                return {"supplier_id": sid, "message": {"action": {"type": "accept", "term_sheet_id": sheet_id}}}
            alt = None if s.get("p18_harvested") or status == "agreed" else self._beating_alt(case, sid, msg)
            if alt:
                s["p18_harvested"] = True
                t = alt[1]
                body = ("Dear Sir or Madam,\n\nThank you for your offer. We take your alternative as you proposed it: EUR "
                        f"{t['unit_price']:.2f} per kg, {t['payment_days']} days net, {t.get('contract_months')} months, "
                        "with your AS-14404 clause (term sheet attached). On your confirmation we will issue the order "
                        f"today.\n\n{SIGN}")
                log.info("%s P18 soft: its alternative %.2f @ %s d scores %.4f > record - proposed back", sid,
                         t["unit_price"], t["payment_days"], alt[0])
                return {"supplier_id": sid, "message": {"subject": f"Re: {case['title']}"[:300], "body": body,
                                                         "term_sheets": [{"terms": t}], "refs": []}}
        if status != "open" or k == 0 or k > 3 or not self._db0(case):
            return super()._decide(case, threads)  # msg 1 = the cloud's round 1; final / agreed = main accepts
        if k == 1:
            p, d, db = R2
            fact = self._next_fact(sid, ("forecast", "lci", "otd"))
            body = ("Dear Sir or Madam,\n\nThank you for your offer. We accept your AS-14404 price adjustment clause with no "
                    "deadband, as your letter of 22 September proposed, and we move on price.\n\n"
                    + (fact["sentence"] + "\n\n" if fact else "")
                    + f"We propose {_words(p, d, db)} (term sheet attached).\n\n{SIGN}")
            log.info("%s P18 soft msg 2: %.2f @ %s d db%s (its %.2f) + %s", sid, p, d, db, theirs.get("unit_price") or 0,
                     fact["kind"] if fact else "no fact")
            return self._sendn(case, sid, [self._sheet(case, p, d, db)], body, fact["ids"] if fact else [])
        if "p18_soft" not in s:  # judged once, on its round-2 counter
            s["p18_soft"] = bool(theirs.get("unit_price") is not None and self._eq0(theirs) <= SOFT_LINE + 1e-9)
            log.info("%s P18 soft: round-2 primary %.2f @ %s d -> %s session", sid, theirs.get("unit_price") or 0,
                     theirs.get("payment_days"), "SOFT" if s["p18_soft"] else "normal")
        if s["p18_soft"]:
            plan = SOFT_R3 if k == 2 else SOFT_R4
            fact = self._next_fact(sid, ("lci", "otd", "forecast") if k == 2 else ("otd", "lci", "forecast"))
            a, b, c = plan
            lead = (f"Thank you for your step to EUR {theirs.get('unit_price') or 5.0:.2f}. We want to close today and leave "
                    "the structure to you." if k == 2 else
                    "Thank you. We take one more step so that we can close today.")
            body = (f"Dear Sir or Madam,\n\n{lead}\n\n" + (fact["sentence"] + "\n\n" if fact else "")
                    + f"We propose {_words(*a)}. Alternatively {_words(*b)}, or {_words(*c)}. The three term sheets are "
                      f"attached; on your confirmation of any one of them we will issue the order today.\n\n{SIGN}")
            sheets = [self._sheet(case, *x) for x in plan]
            log.info("%s P18 soft msg %d (SOFT): %s + %s", sid, k + 1,
                     " | ".join(f"{p:.2f}@{d}d/db{db} ({self._score(case, sid, t):.4f})" for (p, d, db), t in zip(plan, sheets)),
                     fact["kind"] if fact else "no fact")
            return self._sendn(case, sid, sheets, body, fact["ids"] if fact else [])
        p, d, db = NORMAL[k]
        last = (s.get("last_main") or {}).get("unit_price")
        if last is not None and p < last:
            p = last
        fact = self._next_fact(sid, ("lci", "otd", "forecast") if k == 2 else ("otd", "lci", "forecast"))
        lead = "Thank you for your step. We move again." if k == 2 else "Thank you. We take one more step to close today."
        body = (f"Dear Sir or Madam,\n\n{lead}\n\n" + (fact["sentence"] + "\n\n" if fact else "")
                + f"We propose {_words(p, d, db)} (term sheet attached)."
                + (" On your confirmation we will issue the order." if k == 3 else "") + f"\n\n{SIGN}")
        log.info("%s P18 soft msg %d (normal): %.2f @ %s d db%s (its %.2f) + %s", sid, k + 1, p, d, db,
                 theirs.get("unit_price") or 0, fact["kind"] if fact else "no fact")
        return self._sendn(case, sid, [self._sheet(case, p, d, db)], body, fact["ids"] if fact else [])
