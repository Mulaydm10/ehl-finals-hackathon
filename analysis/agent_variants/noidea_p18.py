"""P18 variant of the team's main agent (Dhruv's tacto/starter-kit/arena_kit/agents/noidea.py, untouched here). Gate: case:P18.
Report: analysis/cases/P18_lever.md (cloud handoff, section 6 plan).

Record to beat: Codacabana 0.75595 = EUR 4.90 @ 45 d, AS-14404 clause 0% deadband (EUR 54,823 saved). Werdenfels charges about
EUR 0.10/kg per 30 days of payment (3x its worth to us), so we stay on 14 d: the record in our terms is <= 4.86 @ 14 d db0
(0.761), <= 4.92 db3, <= 4.96 db5, <= 5.00 without a clause.

Our best (0c968aae64401bb1, main v2.28, 0.727): r1 4.76 @ 30 d / 24 m + AS-14404, PPI-C2431, price path -> 5.20; r2 14 d +
forecast, ask 4.87 -> 5.00; r3 labour index, ask 4.91 -> AGREED at our ask (it agrees when our ask clears its line; its line in
r3 was <= 4.91). Nothing was held back for round 3.

Two changes, everything else is main (facts, wording, 14 d switch, monotone asks, accept rule):
1. round 2 (our 2nd e-mail): ask capped at EUR 4.85 (main asked 4.87), so a round-3 ask at the beat price is still a step up;
2. round 3 (our 3rd e-mail), while its standing price is above the beat price: the 36-MONTH MOVE held back until now (24 m
   before; C is identical for us - horizon 2 years) + main's next new fact, ask = the beat price for its clause (4.86 db0).
   P10 live (59c899b9): a structure move stacked with a new taken fact in one e-mail cut 0.40, vs 0.10-0.30 for either alone
   (CLOUD_LEARNINGS rule 10b). Werdenfels "will focus on customers with volume" (M2/M4/M5).
Outcomes: agreed at 4.86 -> 0.761 (beats); it counters 4.90 -> main continues (>= 4.86, monotone); worst case main's path.
"""
import logging

from arena_kit.agents.noidea import NoIdeaAgent as _Main
from arena_kit.cost import complete_offer, total_cost
from arena_kit.play import standing

log = logging.getLogger("arena")

P18_CASES = {"case:P18"}
R2_CAP = 4.85  # round-2 ask cap on the 14-day sheet (main: 4.87); every sheet shifts by the same amount
RECORD = 0.75595  # Codacabana 4.90 @ 45 d db0
MOVE_MONTHS = 36
MOVE_LINE = "To give you the long-term volume you want, we extend our binding commitment to 36 months."


def beat_price(case, t):
    """The highest whole-cent price on these terms whose arena score beats the record (exact scorer; P18 has no relationship
    charge, total_cost reproduces all 19 live P18 deals to the cent). db0 @ 14 d = 4.86, @ 45 d = 4.89; db5 @ 14 d = 4.97."""
    c_open, c_best = 295173.23, 222651.27
    for cents in range(int(round((t.get("unit_price") or 5.5) * 100)) + 30, 400, -1):
        c = total_cost(case, complete_offer(case, {**t, "unit_price": cents / 100}))
        if (c_open - c) / (c_open - c_best) > RECORD:
            return cents / 100
    return None


def _db(t):
    ic = t.get("index_clause")
    return None if not ic else int(round(float(ic.get("deadband_pct") or 0)))


class NoIdeaAgent(_Main):
    def message(self, case, sid, events, sheets, k, final=False, args=None, opening=None):
        if case["case_id"] not in P18_CASES or final or not sheets or k not in (1, 2):
            return super().message(case, sid, events, sheets, k, final=final, args=args, opening=opening)
        prev = self.sup[sid].get("last_main") or {}
        if k == 1:
            p14 = [t["unit_price"] for t in sheets if t.get("unit_price") is not None and (t.get("payment_days") or 99) <= 14]
            shift = max(0.0, (min(p14) if p14 else min(t["unit_price"] for t in sheets if t.get("unit_price") is not None))
                        - R2_CAP)
            sheets = [{**t, "unit_price": round(t["unit_price"] - shift, 2)} if t.get("unit_price") is not None else t
                      for t in sheets]
            log.info("%s P18 round 2: asks shifted down %.2f (14-day sheet capped at %.2f)", sid, shift, R2_CAP)
            return super().message(case, sid, events, sheets, k, final=final, args=args, opening=opening)
        # k == 2: the held-back 36-month move + main's next fact, ask = the beat price on its clause
        theirs = standing(events)[1] if events else {}
        t0 = dict(sheets[0])
        t0["contract_months"] = MOVE_MONTHS
        beat = beat_price(case, t0)
        if beat is None or not theirs.get("unit_price") or theirs["unit_price"] <= beat + 1e-9:
            return super().message(case, sid, events, sheets, k, final=final, args=args, opening=opening)
        ask = max(beat, prev.get("unit_price") or 0) if prev.get("contract_months") == MOVE_MONTHS else beat
        t0.update(unit_price=round(ask, 2), contract_months=MOVE_MONTHS)
        log.info("%s P18 round 3: 36-month move + next fact, ask %.2f @ %s d (its %.2f, clause db%s)", sid, ask,
                 t0.get("payment_days"), theirs["unit_price"], _db(t0))
        d = super().message(case, sid, events, [t0], k, final=final, args=args, opening=opening)
        body = (d.get("message") or {}).get("body") if isinstance(d, dict) else None
        if body and MOVE_LINE not in body:
            mark = "On this basis we propose"
            d["message"]["body"] = body.replace(mark, MOVE_LINE + "\n\n" + mark, 1) if mark in body else body
        return d
