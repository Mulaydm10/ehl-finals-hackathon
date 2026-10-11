"""STATUS v6: NOT RUN - superseded 2026-10-11 by noidea_p18_harvest.py (= the cloud's noidea_p18_cross.py + a two-sheet 4th
message and harvest). Why: P18_deep.md 3.1 - a 45-d round 1 draws a 5.30 first counter in 8 of 13 games (30 d: 5.20 in 9 of
10), and after round 1 its cuts ignored our payment moves, so v6's 45 d -> 14 d switch starts one step worse for nothing.

P18 variant of the team's main agent (Dhruv's tacto/starter-kit/arena_kit/agents/noidea.py, untouched here). Gate: case:P18.
Reports: analysis/cases/P18_lever.md (cloud handoff 1-6, live v1-v5 sections 7-11, v6 section 12).

Record to beat: Codacabana 0.75595 = EUR 4.90 @ 45 d, AS-14404 clause db0. Ours: 0.727 (0c968aae, 4.91 @ 14 d db0).
Beat (exact scorer): <= 4.86 @ 14 d db0 (0.761), <= 4.89 @ 45 d db0 (0.763), <= 4.97 @ 14 d db5.

What ~35 live games say (P18_lever.md):
- Its offers move on a EUR 0.10 grid; first counter 5.20 @ 30 d (6 of 9) / 5.20-5.40 @ 45 d with price path + AS-14404 + PPI;
  round-2 cut -0.20 in ~1 of 3 sessions, -0.10 otherwise, WHATEVER our step (identical moves drew either: 0c968aae / a09d9536
  -0.20 vs Dhruv's budget_pay x3 -0.10; 6c2813ce -0.20 vs 3cb62cb9 / 0371de5b -0.10).
- Its sales contact agrees to our ask when it is within ~2% of his standing offer in his value (dossier: changes above 2% need
  the pricing committee), mostly at our 3rd message; at the 4th he mostly goes final.
- Deeper openings drew the high first counter (4.69, 4.57 -> 5.30): keep the usual opening. Never hold; never send an identical
  e-mail; no 36-month move, no contract-clause argument, no clause switch (all measured 0 or worse).
- NEW (v6): its nominal ladder ends at ~5.00 on 45 d just as on 14 d (45-d games: final / agreed 5.00 @ 45 d; 14-d games 4.91-5.00
  @ 14 d), but it values 45 d about EUR 0.10 below 14 d (it prices payment at ~24%/yr: 4 of 4 same-reply pairs). And it takes a
  SWITCH to a shorter term at the value-equivalent price: c4bcc22c (its 5.10 @ 45 d -> our 5.00 @ 14 d: agreed), 6c2813ce (its
  5.00 @ 45 d -> our 4.91 @ 30 d: countered 5.00 @ 30 d, then 4.94 @ 30 d agreed = 0.718).

v6 plan - build its ladder on 45 d, close on 14 d just under its value:
- r1: 4.77 @ 45 d / 24 m, no clause (main's opening) + price path + AS-14404 + PPI-C2431 + committee + cost-breakdown request;
- r2: 4.90 @ 45 d with its AS-14404 clause + forecast (the +0.13 step that drew -0.20 in 6c2813ce);
- r3: its offer O45 (in 45-d value). O45 <= 5.00 -> switch to 14 d at min(4.86, O45 - 0.14) (~0.8% under its value, inside the
  contact's own 2% authority) + labour index -> agreed = >= 0.761. O45 >= 5.10 -> switch to 14 d at 4.83 (+0.03 in its value) +
  labour index, to draw its 14-d price;
- r4: its 14-d value <= 4.96 -> 4.86 @ 14 d (beats if agreed); else main (monotone from our last ask);
- at every reply: if its standing offer already beats the record, accept it at once.
"""
import json
import logging

from arena_kit.agents.noidea import NoIdeaAgent as _Main
from arena_kit.cost import complete_offer, total_cost
from arena_kit.play import latest, standing

log = logging.getLogger("arena")

P18_CASES = {"case:P18"}
RECORD = 0.75595
C_OPEN, C_BEST = 295173.23, 222651.27
R1, R2, R3_FAR, CLOSE = 4.77, 4.90, 4.83, 4.86
PER_30D = 0.10  # its price for 30 days of payment (cloud: 14 d vs 45 d 0.10 cheaper, 4 of 4 same-reply pairs)
SIGN = "Kind regards,\nPurchasing, Hollerau Pumpenwerke"


def score(case, terms):
    return (C_OPEN - total_cost(case, complete_offer(case, dict(terms)))) / (C_OPEN - C_BEST)


def value_at(terms, days):
    """Its price on `days` for the same value (its payment premium ~0.10 per 30 days; db5 = db0 + 0.10)."""
    p = terms.get("unit_price")
    if p is None:
        return None
    db = float((terms.get("index_clause") or {}).get("deadband_pct") or 0)
    p -= 0.10 if db >= 5 else 0.0
    return p + PER_30D * (days - (terms.get("payment_days") or 30)) / 30


class NoIdeaAgent(_Main):
    def _claim(self, sid, kind, series=None):
        for c in self.sup[sid]["args"]:
            if c["kind"] == kind and (series is None or c.get("series") == series) \
                    and not any(i in self.cited for i in c["ids"]):
                return c
        return None

    def _send(self, case, sid, terms, body, ids):
        refs = sorted(set(ids))
        self.cited.update(refs)
        self.sup[sid]["last_main"] = dict(terms)  # main's monotone guard climbs from here
        return {"supplier_id": sid, "message": {"subject": f"Re: {case['title']}"[:300], "body": body,
                                                 "term_sheets": [{"terms": terms}], "refs": refs[:20]}}

    @staticmethod
    def _db0(case):
        return next((o for o in case["term_options"]["index_clause"] if o and not float(o.get("deadband_pct") or 0)), None)

    def _decide(self, case, threads):
        if case["case_id"] not in P18_CASES:
            return super()._decide(case, threads)
        if case["case_id"] != self.case_id:
            self.prepare(case, threads)
        sid = next((x for x in case["suppliers"] if x in self.sup), None)
        events = threads.get(sid) or []
        if not events:
            return super()._decide(case, threads)
        status = latest(events).get("status")
        sheet_id, theirs = standing(events)
        # anything it stands on that already beats the record: take it
        if sheet_id and theirs.get("unit_price") is not None and status in ("open", "final_offer", "agreed"):
            try:
                if score(case, theirs) > RECORD:
                    log.info("%s P18 v6: its %s beats the record (%.4f) - accept", sid, json.dumps(theirs), score(case, theirs))
                    return {"supplier_id": sid, "message": {"action": {"type": "accept", "term_sheet_id": sheet_id}}}
            except Exception:  # noqa: BLE001
                pass
        if status != "open":
            return super()._decide(case, threads)  # agreed / final_offer: main accepts its primary
        k = sum(m.get("from") == "buyer" and bool(m.get("term_sheets")) for m in events)
        vol = case["fixed_terms"].get("volume_per_year") or case["buyer"]["need_per_year"]
        ic = self._db0(case)
        name = "Mr Seidl" if "Seidl" in " ".join(m.get("body") or "" for m in events if m.get("from") != "buyer") \
            else "Sir or Madam"
        o45, o14 = value_at(theirs, 45), value_at(theirs, 14)
        prev = self.sup[sid].get("last_main") or {}

        def sheet(price, days, clause):
            return complete_offer(case, {"unit_price": round(price, 2), "payment_days": days, "contract_months": 24,
                                         "index_clause": clause})

        if k == 0:
            path, alloy = self._claim(sid, "po_prices"), self._claim(sid, "index_change", "AS-14404")
            ppi = self._claim(sid, "index_change", "PPI-C2431")
            if path and alloy and ppi:
                body = (f"Dear {name},\n\nThank you for your proposal of 22 September. We want to continue with you and confirm "
                        f"a binding volume of {vol} kg per year for 24 months.\n\n"
                        + path["sentence"] + " " + alloy["sentence"] + " " + ppi["sentence"] + "\n\n"
                        "We are prepared to make a longer-term commitment; please share your cost-breakdown XLSX so we can work "
                        "through the underlying elements together. We understand a change of this size needs your pricing "
                        "committee; please put this proposal to them.\n\n"
                        f"On this basis we propose EUR {R1:.2f} per kg, 45 days net, 24 months (term sheet attached).\n\n{SIGN}")
                log.info("%s P18 v6 r1: %.2f @ 45 d / 24 m + path, AS-14404, PPI-C2431", sid, R1)
                return self._send(case, sid, sheet(R1, 45, None), body, path["ids"] + alloy["ids"] + ppi["ids"])
        if k == 1 and ic:
            fc = self._claim(sid, "forecast")
            body = (f"Dear {name},\n\nThank you for your offer. We accept your AS-14404 price adjustment clause, so the alloy "
                    "risk stays covered for you.\n\n" + (fc["sentence"] + "\n\n" if fc else "")
                    + f"We propose EUR {R2:.2f} per kg with your AS-14404 clause, 45 days net, 24 months (term sheet attached)."
                    f"\n\n{SIGN}")
            log.info("%s P18 v6 r2: %.2f @ 45 d db0 + forecast (its %s)", sid, R2, json.dumps(theirs))
            return self._send(case, sid, sheet(R2, 45, ic), body, fc["ids"] if fc else [])
        if k == 2 and ic and o45 is not None:
            lab = self._claim(sid, "index_change", "LCI-C")
            if o45 <= 5.00 + 1e-9:
                ask = min(CLOSE, o45 - 0.14)
                gap = (o14 - ask) / o14 * 100 if o14 else 0
                body = (f"Dear {name},\n\nThank you for your step. To close today we move to your payment preference: 14 days "
                        "net instead of 45, so your cash comes in a month earlier.\n\n" + (lab["sentence"] + "\n\n" if lab else "")
                        + f"In your own terms that is about {max(1, round(gap))}% from your offer, inside your own pricing authority, "
                          "so no committee round is needed. "
                        + f"We propose EUR {ask:.2f} per kg with your AS-14404 clause, 14 days net, 24 months (term sheet "
                          f"attached). On your confirmation we will issue the order today.\n\n{SIGN}")
                log.info("%s P18 v6 r3: its %.2f @ 45 d-value -> switch: %.2f @ 14 d db0 (gap %.1f%% in its value)", sid, o45,
                         ask, gap)
                return self._send(case, sid, sheet(ask, 14, ic), body, lab["ids"] if lab else [])
            body = (f"Dear {name},\n\nThank you for your step. We move towards your payment preference: 14 days net instead of "
                    "45, so your cash comes in a month earlier.\n\n" + (lab["sentence"] + "\n\n" if lab else "")
                    + f"We propose EUR {R3_FAR:.2f} per kg with your AS-14404 clause, 14 days net, 24 months (term sheet "
                      f"attached).\n\n{SIGN}")
            log.info("%s P18 v6 r3: its %.2f @ 45 d-value -> switch: %.2f @ 14 d db0 to draw its 14-d price", sid, o45, R3_FAR)
            return self._send(case, sid, sheet(R3_FAR, 14, ic), body, lab["ids"] if lab else [])
        if k >= 3 and ic and o14 is not None and prev.get("payment_days") == 14 and prev.get("unit_price") is not None:
            # stay on the 14-d structure we switched to (main would pick its term and could step back - replay 6c2813ce)
            last = prev["unit_price"]
            if o14 <= 4.96 + 1e-9 and last < CLOSE - 1e-9:
                ask, beat = CLOSE, True  # inside its 2% authority and still a record
            else:
                ask, beat = round(min(o14 - 0.01, last + 0.04), 2), False
                if ask <= last + 1e-9:
                    ask = round(last + 0.01, 2)
                if ask >= o14 - 0.005 and sheet_id:
                    log.info("%s P18 v6 r%d: its %.2f @ 14 d-value is at our next ask - accept", sid, k + 1, o14)
                    return {"supplier_id": sid, "message": {"action": {"type": "accept", "term_sheet_id": sheet_id}}}
            fact = self._claim(sid, "forecast") or self._claim(sid, "index_change")
            gap = (o14 - ask) / o14 * 100
            body = (f"Dear {name},\n\nThank you. We take one more step to close today.\n\n"
                    + (fact["sentence"] + "\n\n" if fact else "")
                    + (f"Our proposal is about {max(1, round(gap))}% under your offer, inside your own pricing authority, so "
                       "no committee round is needed. " if gap <= 2.0 else "")
                    + f"We propose EUR {ask:.2f} per kg with your AS-14404 clause, 14 days net, 24 months (term sheet "
                      f"attached). On your confirmation we will issue the order today.\n\n{SIGN}")
            log.info("%s P18 v6 r%d: its %.2f @ 14 d-value -> %.2f @ 14 d db0 (gap %.1f%%%s)", sid, k + 1, o14, ask, gap,
                     ", record attempt" if beat else "")
            return self._send(case, sid, sheet(ask, 14, ic), body, fact["ids"] if fact else [])
        return super()._decide(case, threads)
