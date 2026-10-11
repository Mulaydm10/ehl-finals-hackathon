"""P11 variant of the team's main agent (Dhruv's tacto/starter-kit/arena_kit/agents/noidea.py, untouched here). Cloud task 21.

ONE lever: the labour index (LCI-C) is held back until the supplier's first hold, then sent ALONE with a small step.
Evidence (analysis/cases/P11_lever.md, 40 P11 games):
- In all 6 games since v2.21 (and f80f4b54), LCI-C went out with the quality notices at our 3rd message (or alone
  before any hold) -> HOLD every time.
- 77f61e47 (high draw, 46.50 -> 45.50): our 3rd message carried POs + QNs -> hold ("45.50 is our best price"); our 4th
  carried LCI-C alone with a +0.24 step -> "it's a tiny drop, but we can pass that on to you" -> 45.00 (0.794, the only
  high draw that ever reached 45.00). 4d6c9a13: the same shape (hold, then its own quote + a +0.20 step) -> 45.50 -> 45.00.
- A high draw otherwise ends 0.710 (45.50) or 0.777 (45.10 probe agreed).
At its known floor (EUR 45.00, memory) the release message asks ONE cent-level shot, 44.91 (0.8086 > the 0.807 record =
44.92), alone; refused -> main's floor round 2 asks 44.95 (eac20911: agreed, 0.802); then its final is accepted.
The 44.90 + EUR 300 chargeback pair is skipped: chargebacks are charged at its REAL defect rate (api.md; 29cbb6d6: EUR 150
cost +1.00/unit) and 44.90 was refused 4 of 4.
Gate: case:P11 only (P11_CASES); every other case runs main unchanged.
"""
import logging

from arena_kit.agents.noidea import GRID_PROBES, NoIdeaAgent as _Main
from arena_kit.cost import complete_offer, must_haves_ok, total_cost
from arena_kit.play import latest

log = logging.getLogger("arena")

P11_CASES = {"case:P11"}
RESERVE_SERIES = "LCI"  # the fact kept for the message after its first hold (labour index)
SMALL_STEP = 0.25  # our step in that message (77f61e47: +0.24; 4d6c9a13: +0.20)
SHOT = 0.002  # one ask this far under its known floor (45.00 -> 44.91 = 0.8086); then main's hair (-0.1%: 44.95)


class NoIdeaAgent(_Main):
    def prepare(self, case, threads):
        super().prepare(case, threads)
        if case["case_id"] not in P11_CASES:
            return
        for sid, s in self.sup.items():
            lab = [c for c in s["args"] if c["kind"] == "index_change" and str(c.get("series", "")).startswith(RESERVE_SERIES)]
            if lab:
                s["reserve"] = lab[0]
                s["args"] = [c for c in s["args"] if c is not lab[0]]
                log.info("%s: %s held back for the message after its first hold", sid, lab[0].get("series"))

    @staticmethod
    def _own_prices(events):
        return [ts["terms"]["unit_price"] for m in events if m.get("from") != "buyer"
                for ts in (m.get("term_sheets") or [])[:1] if (ts.get("terms") or {}).get("unit_price")]

    @staticmethod
    def _last_ask(events):
        return next((ts["terms"]["unit_price"] for m in reversed(events) if m.get("from") == "buyer"
                     for ts in (m.get("term_sheets") or [])[:1] if (ts.get("terms") or {}).get("unit_price")), None)

    def _floor(self, case, sid, terms):
        """Its lowest remembered final on this structure (P11 300 ppm / EUR 0: 45.00) - only when this structure's final
        is the cheapest remembered one for us (old 800 ppm games stood at 46.00 on 800 / EUR 150: no shot there)."""
        s = self.sup[sid]
        want = {f: terms.get(f) for f in case["negotiable"] if f != "unit_price"}
        mf = self.memory_finals(case, sid)
        fs = [p for t, p in mf if all(abs(float(t.get(f) or 0) - float(v or 0)) < 1e-9 for f, v in want.items())]
        if not fs:
            return None
        cost = lambda t, p: total_cost(case, complete_offer(case, {**terms, **t, "unit_price": p}), s["std"], s["est"])
        here = cost(want, min(fs))
        return min(fs) if all(here <= cost(t, p) + 1e-6 for t, p in mf) else None

    def _decide(self, case, threads):
        if case["case_id"] not in P11_CASES:
            return super()._decide(case, threads)
        if case["case_id"] != self.case_id:
            self.prepare(case, threads)
        sid = next((x for x in case["suppliers"] if x in self.sup), None)
        s = self.sup.get(sid) or {}
        events = threads.get(sid) or []
        status = latest(events).get("status") if events else None
        sheet_id, terms, c_stand = self.best_sheet(case, sid, events) if events else (None, {}, None)
        own = self._own_prices(events)
        holding = len(own) >= 3 and abs(own[-1] - own[-2]) < 1e-9
        floor = self._floor(case, sid, terms) if sheet_id else None
        k = sum(m.get("from") == "buyer" and bool(m.get("term_sheets")) for m in events)
        last = self._last_ask(events)
        if status != "open" or not sheet_id or not last or floor is None or not must_haves_ok(case, terms, s["std"]):
            return super()._decide(case, threads)
        at_floor = terms["unit_price"] <= floor + 1e-9
        out, args = None, None
        if s.get("reserve") and holding:
            # its first hold: the held-back fact ALONE; at its floor with the one shot, above it with a small step
            args = [s.pop("reserve")]
            if at_floor:
                out = complete_offer(case, {**terms, "unit_price": round(int(floor * (1 - SHOT) * 100) / 100, 2)})
                s["shot"] = True
            else:
                out = complete_offer(case, {**terms, "unit_price": round(min(last + SMALL_STEP, terms["unit_price"] - 0.01), 2)})
            log.info("%s: first hold at %.2f - %s alone with %.2f", sid, terms["unit_price"], args[0].get("series"),
                     out["unit_price"])
        elif at_floor and not s.get("shot") and not s.get("reserve") and k >= 2:
            # it came down to its floor after the released fact (77f61e47 pattern): the same one shot
            out = complete_offer(case, {**terms, "unit_price": round(int(floor * (1 - SHOT) * 100) / 100, 2)})
            s["shot"] = True
            log.info("%s: at its floor %.2f - one shot %.2f", sid, floor, out["unit_price"])
        if out is None:
            return super()._decide(case, threads)
        if s.get("shot"):
            # after the shot, main's floor round 2 asks the hair (44.95) once, then accepts its final; no chargeback pair,
            # no grid ladder (44.60-44.90 refused 13 of 13)
            s["cb_tried"], s["floor_tries"], s["probes"] = True, 1, GRID_PROBES
        if not must_haves_ok(case, out, s["std"]) or total_cost(case, out, s["std"], s["est"]) >= c_stand:
            return super()._decide(case, threads)
        return self.message(case, sid, events, [out], k, args=args)
