"""P18 record attempt: "pay faster in the 6c2813ce state" (local, Neel, 2026-10-11 ~05:10). Gate case:P18; every other case = main.
Built on noidea_p18_state45.py (6c2813ce msg 1-2 byte for byte -> its 5.00 @ 45 d state; helpers, accept rules).

The model from all 59 games (analysis/cases/P18_lever.md 22-23):
- Its COUNTERS follow a price ladder (never under 5.00) and ignore payment after round 1.
- Its ACCEPTANCE values payment against its standard 30 d: a shorter term is worth about +0.10/kg to it, a longer one about -0.10.
  0c968aae: 4.91 @ 14 d accepted = 5.01 to it, 4.90 refused; leaving 14 d for 30 d "requires an adjustment from our previous
  14-day offer" (+0.10). c4bcc22c: its 5.10 @ 45 d -> our 5.00 @ 14 d AGREED ("14 days payment terms, which provides the payment
  certainty we value ... In exchange ... we accept"). 81b5c6de: in the 6c2813ce state 4.94 @ 45 d refused ("absolute limit for
  these terms") while 6c2813ce had 4.94 @ 30 d agreed.
- In the 6c2813ce state its floor is in (4.91, 4.94] at 30 d (4.91 @ 30 d held, 4.94 @ 30 d agreed).
So 4.97 @ 14 d db5 is worth ~4.97 to it and 4.86 @ 14 d db0 ~4.96 (db5 = -0.10): both above that floor, both above its own
offer (5.00 @ 45 d = ~4.90 to it) - and both beat the record (0.7593 / 0.7611 > 0.75595).
Open risk: its 2% approval rule (doc:20260812-70740-M3) may be checked on the NOMINAL price (4.86 is 2.8% under 5.00). Every
acceptance in 59 games was within 2% nominal of its offer, so this is a real test, not a sure thing.

Plan: msg 1-2 = 6c2813ce verbatim. msg 3 = its msg 3 (labour index fact) + a sentence offering 14 days net + the two record sheets.
If it holds: msg 4 = its msg 4 + its on-time delivery fact (a new fact: a fact-free msg 4 drew "send us the data" and its final in
81b5c6de) + 4.90 @ 14 d db0 / 5.00 @ 14 d db5 (0.7339 / 0.7393, both over our 0.727; 5.00 to it). final_offer / agreed: accept its
primary (main). Never a step back in its value (payment and deadband included).
"""
import copy
import importlib.util
import logging
import sys
from pathlib import Path

from arena_kit.play import latest, standing

_spec = importlib.util.spec_from_file_location("arena_kit.agents._p18_state45_for_pay14",
                                               Path(__file__).with_name("noidea_p18_state45.py"))
_s45 = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _s45
_spec.loader.exec_module(_s45)
_Main = _s45._Main

log = logging.getLogger("arena")
MSG3 = ((4.97, 14, 5), (4.86, 14, 0))  # 0.7593 / 0.7611 - record; 4.97 / 4.96 to it. db5 first: 0.6% nominal under its 5.00
# primary, so it passes the 2% rule whether it is read on value or on its primary price (offline run C); 4.86 db0 needs value
MSG4 = ((5.00, 14, 5), (4.90, 14, 0))  # 0.7393 / 0.7339 - over our 0.727; 5.00 to it (db5 first: 0% nominal under its primary)
PAY_SENTENCE = ("We now offer payment in 14 days net instead of 45 days: the payment certainty you value, a full month earlier. ")
OLD3, OLD4 = _s45.OLD3, _s45.OLD4
ANCHOR = "On this basis we propose the attached term sheets "


def value(p, d, db):
    """Its value of our ask in 30-d db0 terms: db5 / db3 -0.10; payment shorter than 30 d +0.10, longer -0.10 (P18_lever 23)."""
    return round(p - (0.10 if db >= 3 else 0.0) + (0.10 if d < 30 else -0.10 if d > 30 else 0.0), 2)


class NoIdeaAgent(_s45.NoIdeaAgent):
    def _out2(self, case, sid, m, old, plan, insert):
        m = copy.deepcopy(m)
        body = m["body"]
        assert old in body and ANCHOR in body, "6c2813ce text changed"
        new = "(" + "; ".join(f"EUR {p:.2f} per unit, AS-14404 index clause (45% share, {db}% deadband), {d} days payment, 24 months"
                              for p, d, db in plan) + ")"
        body = body.replace(old, new).replace(ANCHOR, insert + ANCHOR, 1)
        sheets = [{"terms": {"unit_price": p, "index_clause": dict(self._clause(case, db)), "payment_days": d,
                             "contract_months": 24}} for p, d, db in plan]
        fact_ids = getattr(self, "_p18_fact_ids", [])
        refs = sorted(set((m.get("refs") or []) + fact_ids))
        out = {"subject": m["subject"], "body": body, "term_sheets": sheets, "refs": refs}
        self.cited.update(refs)
        self.sup[sid]["last_main"] = dict(sheets[0]["terms"])
        return {"supplier_id": sid, "message": out}

    def _decide(self, case, threads):
        if case["case_id"] not in _s45._soft._cross.P18_CASES:
            return super()._decide(case, threads)
        if case["case_id"] != self.case_id:
            self.prepare(case, threads)
        sid = next((x for x in case["suppliers"] if x in self.sup), None)
        events = threads.get(sid) or []
        if not events:
            return super()._decide(case, threads)
        if self._msgs is None:
            _s45.NoIdeaAgent._msgs = _s45._src()
        s = self.sup[sid]
        status = latest(events).get("status")
        k = sum(m.get("from") == "buyer" and bool(m.get("term_sheets")) for m in events)
        sheet_id, theirs = standing(events)
        if status != "open":
            return _Main._decide(self, case, threads)  # final_offer / agreed: main accepts its primary sheet
        if k in (2, 3) and sheet_id and theirs.get("unit_price") is not None:
            plan = MSG3 if k == 2 else MSG4
            sc = self._score(case, sid, theirs)
            if sc > _s45._soft.RECORD or sc >= min(self._score(case, sid, self._sheet(case, *x)) for x in plan) - 1e-9:
                log.info("%s P18 pay14: its %.2f @ %s d scores %.4f - accept", sid, theirs["unit_price"],
                         theirs.get("payment_days"), sc)
                return {"supplier_id": sid, "message": {"action": {"type": "accept", "term_sheet_id": sheet_id}}}
        if k <= 3:
            on = (k == 0 or (k in _s45.TRACK and _s45._is(theirs, *_s45.TRACK[k]))
                  or (k == 3 and theirs.get("unit_price") is not None and abs(self._eq0(theirs) - 5.00) < 1e-9))
            if not on:
                log.info("%s P18 pay14: its reply %s @ %s d is off the 6c2813ce track at msg %d - the plan continues", sid,
                         theirs.get("unit_price"), theirs.get("payment_days"), k + 1)
            if k in (0, 1):
                log.info("%s P18 pay14 msg %d: 6c2813ce verbatim (its %s)", sid, k + 1, theirs.get("unit_price"))
                return self._out(case, sid, self._msgs[k])
            plan = MSG3 if k == 2 else MSG4
            lt = s.get("last_main") or {}
            if lt.get("unit_price") is not None:  # never a step back in its value (payment and deadband included)
                last = value(lt["unit_price"], lt.get("payment_days") or 30,
                             float((lt.get("index_clause") or {}).get("deadband_pct") or 0))
                gap = round(last + 0.01 - min(value(*x) for x in plan), 2)
                if gap > 0:
                    plan = tuple((round(p + gap, 2), d, db) for p, d, db in plan)
            self._p18_fact_ids = []
            insert = PAY_SENTENCE if k == 2 else ""
            if k == 3:  # a new fact in msg 4 (81b5c6de: a fact-free msg 4 drew "send us the data" and its final)
                f = self._next_fact(sid, ("otd", "alloy", "forecast"))
                if f:
                    insert = f["sentence"] + " "
                    self._p18_fact_ids = list(f["ids"])
            log.info("%s P18 pay14 msg %d: %s (its %.2f @ %s d) - scores %s, values to it %s", sid, k + 1, plan,
                     theirs.get("unit_price") or 0, theirs.get("payment_days"),
                     [round(self._score(case, sid, self._sheet(case, *x)), 4) for x in plan], [value(*x) for x in plan])
            return self._out2(case, sid, self._msgs[2 if k == 2 else 3], OLD3 if k == 2 else OLD4, plan, insert)
        return _Main._decide(self, case, threads)
