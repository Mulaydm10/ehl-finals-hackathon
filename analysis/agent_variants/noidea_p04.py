"""P04 variant of the team's main agent (Dhruv's tacto/starter-kit/arena_kit/agents/noidea.py, untouched here).
Full analysis: analysis/cases/P04_deep.md.

PROVEN (15 games, both rounding rules): no whole-cent deal the P04 supplier can accept scores above 0.8737.
- Its cash rate is 7.28-7.69% a year. Its own two-sheet quotes give at most 7.69% (one value target per message). The arena's
  1.0 line (C_best = its floor; no deal in any case has ever crossed it) gives at least 7.28%, because it agreed to 4.89 @ 45 d.
- Its floor is F = 4.935 x (1 - rate/6) = EUR 4.8717-4.8751 of value. The cheapest cent on each term: 14 d 4.86 (0.815),
  30 d 4.88 (0.766), **45 d 4.89 (0.8737)**, 60 d 4.91 (0.810), 90 d 4.94 (0.860); 24 m = 36 m.
- The record-beating cents need a higher rate: 4.87 @ 30 d needs >= 7.90%, 4.85 @ 14 d >= 8.19%, 4.90 @ 60 d >= 8.45%,
  4.88 @ 45 d >= 8.88%. 4.93 @ 90 d never clears it. The board's 0.874 (makeAnother.md) is this same 4.89 @ 45 d: it can be
  tied, never beaten.
- Main reaches 0.8737 every time it stays on 45 d (6 of 6). A hop costs the cent: live 1992e28a (4.87 @ 30 d shot, then
  back to 45 d) got 4.90 @ 45 d = 0.700.

So P04_SHOT stays OFF: the default is main exactly. If someone turns it on anyway, a refused shot no longer hops back to 45 d.
It accepts the standing 30-day sheet (4.88 @ 30 d = 0.766, which beats the 0.700 that the hop cost).
"""
import logging

from arena_kit.agents.noidea import NoIdeaAgent as _Main
from arena_kit.cost import complete_offer
from arena_kit.play import latest

log = logging.getLogger("arena")

P04_CASES = {"case:P04"}
P04_SHOT = False  # never enable: proven unreachable (P04_deep.md section 3); False = main unchanged (0.8737)
SHOT = {"unit_price": 4.87, "payment_days": 30, "contract_months": 36}


class NoIdeaAgent(_Main):
    def _decide(self, case, threads):
        if case["case_id"] not in P04_CASES or not P04_SHOT:
            return super()._decide(case, threads)
        if case["case_id"] != self.case_id:
            self.prepare(case, threads)
        sid = next((x for x in case["suppliers"] if x in self.sup), None)
        events = threads.get(sid) or []
        status = latest(events).get("status") if events else None
        k = sum(m.get("from") == "buyer" and bool(m.get("term_sheets")) for m in events)
        s = self.sup[sid]
        if status == "open" and k == 1 and not s.get("p04_shot"):
            s["p04_shot"] = True
            log.info("%s: P04 shot %s", sid, SHOT)
            return self.message(case, sid, events, [complete_offer(case, dict(SHOT))], k, args=[])
        if status == "open" and k == 2 and s.get("p04_shot"):
            # refused: take its standing sheet; never hop back (1992e28a: the hop to 45 d cost a cent -> 0.700)
            sheet_id = self.best_sheet(case, sid, events)[0]
            if sheet_id:
                log.info("%s: shot refused - accepting its standing sheet %s", sid, sheet_id)
                return {"supplier_id": sid, "message": {"action": {"type": "accept", "term_sheet_id": sheet_id}}}
        return super()._decide(case, threads)
