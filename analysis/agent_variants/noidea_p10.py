"""P10 variant of the team's main agent (Dhruv's tacto/starter-kit/arena_kit/agents/noidea.py, untouched here).
Report: analysis/cases/P10_deep.md. Scripted twin: analysis/experiments/probes/P10_G.json (tools/experiments/probe.py).

Record to beat: Codacabana 0.71 = EUR 31.10 @ 56 d, 23,400 a year, 24 or 36 months (EUR 428,374 saved). Ours: 0.702 = 31.20
(Parth's probe B, 991ff7c4). Ravensteiner (one-shot / short-fuse) cuts once per MOVE and once per NEW verified fact it
takes, then goes final at our 2nd message (7 of 7). No game ever stacked the cuts:
- probe B: round 1 price history + should-cost (open 31.50); round 2 the 36-month move with NO data -> final 31.20
  (-0.30, "Which figures is that based on?");
- agents 53bab007 / c283f47d: the labour index alone in round 2 -> "Reflecting the minor index change" -0.20;
- main gives 36 months away in round 1 (no move left) and spends a round-1 slot on the forecast (shrugged 11 of 11).

This variant (gate: case:P10):
- round 1 = probe B (current price 29.89 as the anchor, 24 months, lead 56, 23,400) + the rubber index fall
  (PPI-C2219 -0.3%, 2026-01 -> 2026-02, verified figure) as the third claim;
- round 2 = the 36-month move + the labour index (LCI-C -0.3%, 2025-10 -> 2026-01) + an ask EUR 1.10 under its counter
  (probe B: 31.50 -> 30.40 drew the biggest step, 0.30);
- then main: accept its final (or keep negotiating if it stays open).
"""
import logging

from arena_kit.agents.noidea import NoIdeaAgent as _Main
from arena_kit.cost import complete_offer, must_haves_ok
from arena_kit.play import latest, standing

log = logging.getLogger("arena")

P10_CASES = {"case:P10"}
R1_MONTHS, R2_MONTHS, LEAD = 24, 36, 56
R2_GAP = 1.10  # round-2 ask = its counter - 1.10 (probe B: 31.50 -> 30.40 -> final 31.20, the largest step seen)
SIGN = "Kind regards,\nPurchasing, Hollerau Pumpenwerke"


class NoIdeaAgent(_Main):
    def _claim(self, sid, kind, series=None):
        for c in self.sup[sid]["args"]:
            if c["kind"] == kind and (series is None or c.get("series") == series) \
                    and not any(i in self.cited for i in c["ids"]):
                return c
        return None

    def _send(self, case, sid, terms, body, claims):
        refs = sorted({i for c in claims for i in c["ids"]})
        self.cited.update(refs)
        self.sup[sid]["last_main"] = dict(terms)
        return {"supplier_id": sid, "message": {"subject": f"Re: {case['title']}"[:300], "body": body,
                                                 "term_sheets": [{"terms": terms}], "refs": refs[:20]}}

    def _decide(self, case, threads):
        if case["case_id"] not in P10_CASES:
            return super()._decide(case, threads)
        if case["case_id"] != self.case_id:
            self.prepare(case, threads)
        sid = next((x for x in case["suppliers"] if x in self.sup), None)
        events = threads.get(sid) or []
        status = latest(events).get("status") if events else None
        k = sum(m.get("from") == "buyer" and bool(m.get("term_sheets")) for m in events)
        b = case["buyer"]
        vol = max(o for o in case["term_options"]["volume_per_year"])
        contact = "Ms Zellner" if "Zellner" in (events[0].get("body") or "") else "Sir or Madam"
        if status == "open" and k == 0:
            claims = [c for c in (self._claim(sid, "po_prices"), self._claim(sid, "should_cost"),
                                  self._claim(sid, "index_change", "PPI-C2219")) if c]
            ask = b.get("current_unit_price")
            t = complete_offer(case, {"unit_price": ask, "volume_per_year": vol, "contract_months": R1_MONTHS,
                                      "lead_time_days": LEAD})
            if claims and ask and must_haves_ok(case, t, self.sup[sid]["std"]):
                body = (f"Dear {contact},\n\nThank you for your offer and for being open about your capacity situation.\n\n"
                        f"We are ready to give you the firm commitment you asked for: a binding {vol:,} pieces per year for "
                        f"{R1_MONTHS} months, and we accept a longer lead time of {LEAD} days so you can plan production.\n\n"
                        + "\n".join(c["sentence"] for c in claims)
                        + f"\n\nWe therefore propose to keep EUR {ask:.2f} per piece, the price we have paid since "
                          f"January 2024.\n\n{SIGN}")
                log.info("%s P10 round 1: %.2f @ %d d / %d m + %s", sid, ask, LEAD, R1_MONTHS, [c["kind"] for c in claims])
                return self._send(case, sid, t, body, claims)
        if status == "open" and k == 1:
            counter = (standing(events)[1] or {}).get("unit_price")
            lab = self._claim(sid, "index_change", "LCI-C")
            if counter:
                ask = round(counter - R2_GAP, 2)
                t = complete_offer(case, {"unit_price": ask, "volume_per_year": vol, "contract_months": R2_MONTHS,
                                          "lead_time_days": LEAD})
                if must_haves_ok(case, t, self.sup[sid]["std"]):
                    body = (f"Dear {contact},\n\nThank you for your answer. We move towards you: we extend the commitment to "
                            f"{R2_MONTHS} months, {vol * R2_MONTHS // 12:,} pieces in total.\n"
                            + (lab["sentence"] + "\n" if lab else "")
                            + f"\nWe propose EUR {ask:.2f} per piece.\n\n{SIGN}")
                    log.info("%s P10 round 2: 36 m move + %s, ask %.2f (its %.2f)", sid, "labour index" if lab else "no data",
                             ask, counter)
                    return self._send(case, sid, t, body, [lab] if lab else [])
        return super()._decide(case, threads)
