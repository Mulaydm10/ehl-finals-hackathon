"""P10 record attempt (Parth, 2026-10-11; brief "P10 Record-Breaking Investigation"): noidea_p10 + ONE step inside the
Segment Manager's own 2% authority after its final. Log: analysis/cases/P10_experiments.md. Scripted twin:
analysis/experiments/probes/P10_R.json (tools/experiments/probe.py).

noidea_p10 sends 59c899b9's two e-mails byte for byte (live 31.50 -> final 31.10, 3 of 3: the arena answers an identical
conversation identically). Its final ends normal play (rule 24) at 0.7097; the team's record is 0.740961 (30.70, the arena's
engine-template window). This variant adds one move after the final:
- price: the highest whole-cent price whose total cost C (arena_kit.cost) beats the record deal's C on the final's own
  structure (30.69 @ 56 d / 36 m / 23,400 = 0.741742), only if it is at most 2% under the final (the step the Segment
  Manager may give without its pricing committee, doc:20260310-70410-M1) and above our own last ask (we move up, never back);
- sheet: the final's structure; e-mail written in code (no model sets a number);
- then accept whatever stands: agreed at our price (record), its final again (0.7097) or a counter. A walk ends this game
  only (0); the board keeps the best.
Odds are low (rule 127): no supplier in our archive agreed after a final to a sheet worth less to it than its final.
"""
import importlib.util
import logging
from pathlib import Path

from arena_kit.cost import complete_offer, must_haves_ok, total_cost
from arena_kit.play import latest, standing

_spec = importlib.util.spec_from_file_location("arena_kit.agents._noidea_p10_base", Path(__file__).with_name("noidea_p10.py"))
_base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_base)

log = logging.getLogger("arena")

P10_CASES = _base.P10_CASES
C_RECORD = 1485273.60  # 673ee890's c_deal (30.70 @ 56 d / 36 m / 23,400): beat it, don't tie it
AUTHORITY = 0.02  # doc:20260310-70410-M1: price changes above 2% need the pricing committee
STD = {"ppm_commitment": 300, "chargeback_eur_per_complaint": 0.0}  # its quote's standard terms
TEMPLATE_LINES = ("we value our cooperation and have made a step towards you",  # the arena's engine-template mode
                  "any further step needs approval from our management", "management has approved a further step")
BODY = ("Dear {contact},\n\nThank you for your offer. We take one more step towards you: EUR {price:.2f} per piece for the "
        "{months} months, {total:,} pieces in total. The difference to your price is less than 2%, within what you can "
        "agree yourself without your pricing committee. If you confirm EUR {price:.2f}, we sign today.\n\n{sign}")


def record_price(case, terms):
    """The highest whole-cent price whose C on `terms` is below the record deal's C (None if none is reachable)."""
    p = round(terms["unit_price"], 2)
    while p > 0 and total_cost(case, {**terms, "unit_price": p}, STD) >= C_RECORD:
        p = round(p - 0.01, 2)
    return p if p > 0 else None


class NoIdeaAgent(_base.NoIdeaAgent):
    def _decide(self, case, threads):
        if case["case_id"] not in P10_CASES:
            return super()._decide(case, threads)
        sid = next((x for x in case["suppliers"] if x in threads), None)
        events = threads.get(sid) or []
        if not events:
            return super()._decide(case, threads)
        if case["case_id"] != self.case_id:  # self.sup (its standard terms) exists only after prepare()
            self.prepare(case, threads)
        status = latest(events).get("status")
        sheet_id, theirs = standing(events)
        if any(x in (latest(events).get("body") or "").lower() for x in TEMPLATE_LINES) and sheet_id \
                and status in ("open", "final_offer", "agreed"):  # its model is off: no move that rests on that window
            log.info("%s P10: engine-template reply - accept what stands (%.2f)", sid, theirs.get("unit_price"))
            return {"supplier_id": sid, "message": {"action": {"type": "accept", "term_sheet_id": sheet_id}}}
        mine = [m for m in events if m.get("from") == "buyer" and m.get("term_sheets")]
        k = len(mine)
        if status == "final_offer" and k == 2 and theirs.get("unit_price"):
            t = complete_offer(case, {f: theirs[f] for f in case["negotiable"]})
            last_ask = mine[-1]["term_sheets"][0]["terms"]["unit_price"]
            p = record_price(case, t)
            if p is not None and last_ask < p < t["unit_price"] and p >= round(t["unit_price"] * (1 - AUTHORITY), 2) \
                    and must_haves_ok(case, t, self.sup[sid]["std"]):
                ask = {**t, "unit_price": p}
                contact = "Ms Zellner" if "Zellner" in (events[0].get("body") or "") else "Sir or Madam"
                body = BODY.format(contact=contact, price=p, months=t["contract_months"],
                                   total=t["volume_per_year"] * t["contract_months"] // 12, sign=_base.SIGN)
                log.info("%s P10 after its final %.2f: one step inside its 2%% authority, ask %.2f", sid, t["unit_price"], p)
                return self._send(case, sid, ask, body, [])
        if k == 3 and status in ("agreed", "final_offer", "open") and sheet_id \
                and must_haves_ok(case, {**case.get("fixed_terms", {}), **theirs}, self.sup[sid]["std"]):
            log.info("%s P10 after our step: %s at %.2f - accept", sid, status, theirs.get("unit_price"))
            return {"supplier_id": sid, "message": {"action": {"type": "accept", "term_sheet_id": sheet_id}}}
        return super()._decide(case, threads)
