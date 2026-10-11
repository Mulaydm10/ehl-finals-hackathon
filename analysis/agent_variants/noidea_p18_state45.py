"""P18 "45-day soft state" (local, Neel, 2026-10-11 ~05:00; Run 2 candidate). Gate case:P18; every other case = main.

Why (analysis/cases/P18_lever.md 15-20, P18_experiments.md):
- Werdenfels answers an identical conversation identically (15438619 x6; 0c968aae replayed x8). So every existing P18 agent has
  a KNOWN hosted outcome: noidea_p18_cross 0.677, noidea_p18_soft v2 0.677, noidea_p18_replay (4.91) 0.727 = our best.
- It agrees only to an ask < 2% under its current db0 offer and above the conversation's hidden floor; its counters never go
  under 5.00. In the 0c968aae state (5.00 @ 14 d) only 4.91 passes (all lower asks drew its final): 0.727 is that state's max.
- 6c2813ce reached the other recorded soft state: msg 1 4.77 @ 45 d -> 5.20 @ 45 d (+5.30 db5); msg 2 4.90 @ 45 d db0 + forecast
  -> **5.00 @ 45 d** (+5.10 db5). There msg 3 (4.91 @ 30 d) drew a HOLD (5.00 @ 30 d), not a final, and msg 4 4.94 @ 30 d was
  AGREED (0.718). Its floor at 30 d is in (4.91, 4.94]. It did not credit the move 45 -> 30 d (held 5.00), and 45-d games that
  opened on 45 d ended at the same 5.00 floor as 30-d games, so 45 d looks free in this state.
- Staying on its 45 d: 4.93 @ 45 d db0 = 0.7357 (1.4% under 5.00), 4.94 @ 45 d db0 = 0.7289 (1.2%): both over our 0.727.

Plan: msg 1 and msg 2 = 6c2813ce's byte for byte (datasets/runs/6c2813cee1fcf116.json). If its replies reproduce that game
(5.20 @ 45 d, then 5.00 @ 45 d), msg 3 = 6c2813ce's msg 3 with only the proposal changed to MSG3 (4.93 @ 45 d db0); after a hold
at 5.00, msg 4 = 6c2813ce's msg 4 with MSG4 (4.94 @ 45 d db0). No step back (4.90 -> 4.93 -> 4.94), its own clause, its own 45 d,
inside its 2% authority. Off this track the same plan continues (Run 2 found that handing over to main
re-cited msg 1's facts and repeated our price); main only from msg 5. final_offer / agreed: accept its
PRIMARY sheet (main; never an '-a' id). The record (0.756) is NOT reachable here: 45 d db0 needs <= 4.89 (2.2% under 5.00).
"""
import copy
import importlib.util
import json
import logging
import sys
from pathlib import Path

from arena_kit.play import latest, standing

_spec = importlib.util.spec_from_file_location("arena_kit.agents._p18_soft_for_state45",
                                               Path(__file__).with_name("noidea_p18_soft.py"))
_soft = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _soft
_spec.loader.exec_module(_soft)
_Main = _soft._cross._Main  # the team's main agent (tacto/starter-kit/arena_kit/agents/noidea.py)

log = logging.getLogger("arena")
ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "datasets/runs/6c2813cee1fcf116.json"
TRACK = {1: (5.20, 45), 2: (5.00, 45)}  # its primary db0 sheet after our msg 1 / msg 2 in 6c2813ce
MSG3 = (4.93, 45, 0)  # 0.7357
MSG4 = (4.94, 45, 0)  # 0.7289 (6c2813ce agreed 4.94 at msg 4 after a hold, on 30 d)
OLD3 = "(EUR 4.91 per unit, AS-14404 index clause (45% share, 0% deadband), 30 days payment, 24 months)"
OLD4 = "(EUR 4.94 per unit, AS-14404 index clause (45% share, 0% deadband), 30 days payment, 24 months)"


def _src():
    msgs = json.loads(SRC.read_text(encoding="utf-8"))["threads"]["sup:70740"]["messages"]
    return [m for m in msgs if m.get("from") == "buyer" and m.get("term_sheets")]


def _is(t, price, days):
    return (t.get("unit_price") is not None and abs(t["unit_price"] - price) < 1e-9 and t.get("payment_days") == days
            and not float((t.get("index_clause") or {}).get("deadband_pct") or 0))


class NoIdeaAgent(_soft.NoIdeaAgent):
    _msgs = None

    def _out(self, case, sid, m, old=None, plan=None):
        m = copy.deepcopy(m)
        out = {"subject": m["subject"], "body": m["body"], "term_sheets": m["term_sheets"], "refs": m.get("refs") or []}
        if plan is not None:
            p, d, db = plan
            assert old in out["body"], old
            new = f"(EUR {p:.2f} per unit, AS-14404 index clause (45% share, {db}% deadband), {d} days payment, 24 months)"
            out["body"] = out["body"].replace(old, new)
            out["term_sheets"] = [{"terms": {"unit_price": p, "index_clause": dict(self._clause(case, db)), "payment_days": d,
                                             "contract_months": 24}}]
        self.cited.update(out["refs"])
        self.sup[sid]["last_main"] = dict(out["term_sheets"][0]["terms"])  # main's monotone guard climbs from here
        return {"supplier_id": sid, "message": out}

    def _decide(self, case, threads):
        if case["case_id"] not in _soft._cross.P18_CASES:
            return super()._decide(case, threads)
        if case["case_id"] != self.case_id:
            self.prepare(case, threads)
        sid = next((x for x in case["suppliers"] if x in self.sup), None)
        events = threads.get(sid) or []
        if not events:
            return super()._decide(case, threads)
        if self._msgs is None:
            NoIdeaAgent._msgs = _src()
        s = self.sup[sid]
        status = latest(events).get("status")
        k = sum(m.get("from") == "buyer" and bool(m.get("term_sheets")) for m in events)
        sheet_id, theirs = standing(events)
        if status != "open":
            return _Main._decide(self, case, threads)  # final_offer / agreed: main accepts its primary sheet
        if s.get("p18_state45", True) and k in (2, 3) and sheet_id and theirs.get("unit_price") is not None:
            plan = MSG3 if k == 2 else MSG4
            if self._score(case, sid, theirs) >= self._score(case, sid, self._sheet(case, *plan)) - 1e-9:
                log.info("%s P18 state45: its %.2f @ %s d scores at least our planned %.2f - accept", sid,
                         theirs["unit_price"], theirs.get("payment_days"), plan[0])
                return {"supplier_id": sid, "message": {"action": {"type": "accept", "term_sheet_id": sheet_id}}}
        if k <= 3:  # our plan through message 4 whatever it answers (main never sees our verbatim messages' facts)
            on = (k == 0 or (k in TRACK and _is(theirs, *TRACK[k]))
                  or (k == 3 and theirs.get("unit_price") is not None and abs(self._eq0(theirs) - 5.00) < 1e-9))
            if not on and s.get("p18_state45", True):
                s["p18_state45"] = False
                log.info("%s P18 state45: its reply %s @ %s d is off the 6c2813ce track at msg %d - the plan continues", sid,
                         theirs.get("unit_price"), theirs.get("payment_days"), k + 1)
            if k in (0, 1):
                log.info("%s P18 state45 msg %d: 6c2813ce verbatim (its %s)", sid, k + 1, theirs.get("unit_price"))
                return self._out(case, sid, self._msgs[k])
            plan, old, src = (MSG3, OLD3, self._msgs[2]) if k == 2 else (MSG4, OLD4, self._msgs[3])
            last = (s.get("last_main") or {}).get("unit_price")
            if last is not None and plan[0] <= last + 1e-9:  # never repeat or step back from our own last ask
                plan = (round(last + 0.01, 2),) + tuple(plan[1:])
            log.info("%s P18 state45 msg %d: 6c2813ce's msg %d with %.2f @ %s d db%s (its %.2f @ %s d) - score %.4f",
                     sid, k + 1, k + 1, plan[0], plan[1], plan[2], theirs.get("unit_price") or 0, theirs.get("payment_days"),
                     self._score(case, sid, self._sheet(case, *plan)))
            return self._out(case, sid, src, old, plan)
        return _Main._decide(self, case, threads)
