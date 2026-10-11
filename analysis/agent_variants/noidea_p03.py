"""P03 variant of Neel's agent (analysis/agent_variants/noidea_neel.py, untouched here). Gate: case:P03 only.
Reports: analysis/cases/P03_lever.md (v1: path in round 2, live 722dee8e 0.9633) and analysis/cases/P03_deep.md (v2, this).

STATUS v2 (2026-10-11, cloud, offline): target "+=" 0.97350 = EUR 429.87 @ 90 d (set 23:54 CEST in the arena's
engine-template window). Normal-mode Selvbrunn is a deterministic ladder: committee 433.08 @ 90 d minus one cut per NEW
verified kind it takes (should-cost 0.79, electronics -2.3% 0.48, order price path 1.26, forecast 0.14, copper 0.05-0.07,
labour 0.02-0.03); it counters at its line, agrees at OUR ask when the ask is at or above it, goes final at its reply to
our 5th message. Measured kinds alone end at ~430.33 (0.9639); 429.86 needs a new kind worth >= 0.47.

v2 changes (switches below; sim: analysis/tools/sim_selvbrunn_ladder.py, replays in analysis/cases/P03_deep.md):
- Claim order stays v1's MEASURED one: round 1 should-cost + forecast + electronics (431.67, 5 of 5), round 2 the order
  price path (430.41, live), then copper and labour one per e-mail. PATH_IN_ROUND1 (path with should-cost + electronics
  in round 1) is built but OFF: its round-1 cut is only known to be >= 1.00 (v2.34 asked 430.81 with those three and was
  agreed), not the 1.26 measured in round 2, and both orders end at the same line when cuts add up.
- ASK_BELOW_LINE: every ask stays EUR 0.60 under its standing price. Without it the agent closes at its 5th message
  (accept rule: standing within 0.05% of our ask) and the 5th e-mail is never sent; and v2.34 (main) asked 430.81 with
  three facts in round 1 and Selvbrunn AGREED at our ask, 3 of 3 (fe4d8455, f8082c20, 5c74eff5: 0.954).
- RIVAL_QUOTE_P03: our 5th e-mail (the one its final answers) carries the one kind never sent to P03: the second source's
  quote from our February 2025 benchmark RFQ, quote:7100051 = EUR 429.18 (sup:70540, part:350020), stated with its date.
  Untested: a rival quote was "verified" but shrugged in P01 (it was dearer there); own quotes are "irrelevant". Last,
  so it cannot displace a measured cut. Worth >= 0.47 -> beats "+="; worth 0 -> 430.33 (0.9639, still a team best).
"""
import importlib.util
import logging
import sys
from datetime import date
from pathlib import Path

from arena_kit.cost import complete_offer, supplier_value
from arena_kit.play import standing

_spec = importlib.util.spec_from_file_location("arena_kit.agents._noidea_neel_p03base",
                                               Path(__file__).with_name("noidea_neel.py"))
_base = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _base
_spec.loader.exec_module(_base)
central = _base.central
log = logging.getLogger("arena")

P03_CASES = {"case:P03"}
PRICE_PATH_P03 = True  # our order price path (taken live: 431.67 -> 430.41 in 722dee8e)
PATH_IN_ROUND1 = False  # built, OFF: path in round 1 cuts >= 1.00 (unmeasured exactly); round 2 = 1.26 (live)
OWN_QUOTE_AFTER_PATH = True  # v1: its own quote after the path (only if DROP_OWN_QUOTE is False)
DROP_OWN_QUOTE = True  # live 722dee8e (0.9633): quote:7300003 was "irrelevant" (read as a rival quote)
ASK_BELOW_LINE = 0.60  # v2: EUR under its standing price for every ask (None = v1 asks)
RIVAL_QUOTE_P03 = True  # v2: the February 2025 benchmark quote of the second source, in the last data slot
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November",
          "December"]


def rival_benchmark_claims(facts, sid, part, below):
    """The second source's cheapest quote for this part from our own benchmark RFQs, when it is below `below` (its
    standing price): quote:7100051 = EUR 429.18 (2025-02-25) for P03. One price per sentence, dated - it is not current."""
    best = None
    for k, v in facts.items():
        if (k.startswith("quote:") and v.get("part") == part and v.get("supplier") not in (None, sid)
                and v.get("unit_price") and v.get("date") and v["unit_price"] < below):
            if best is None or v["unit_price"] < best[1]["unit_price"]:
                best = (k, v)
    if not best:
        return []
    k, v = best
    d = date.fromisoformat(v["date"][:10])
    return [{"supplier": sid, "part": part, "kind": "rival_quote", "ids": [k], "figure": v["unit_price"],
             "sentence": (f"In our benchmark RFQ of {MONTHS[d.month - 1]} {d.year}, the second source quoted "
                          f"EUR {v['unit_price']:.2f} per unit for this part ({k})."),
             "checked_by_arena": True}]


class NoIdeaAgent(_base.NoIdeaAgent):
    def rank_args(self, case, sid, ask_pct):
        ranked = super().rank_args(case, sid, ask_pct)
        if case["case_id"] not in P03_CASES or not PRICE_PATH_P03:
            return ranked
        desc = {p["part"]: p.get("description", "") for p in self.dossiers.get(sid, {}).get("parts", [])}
        pp = [x for x in (central.rising_price_path(self.facts, sid, pt, desc.get(pt, "")) for pt in case["parts"]) if x]
        if not pp:
            return ranked
        ids = {i for c in pp for i in c["ids"]}
        # the flat order run would repeat these IDs (duplicate): the path replaces it
        rest = [c for c in ranked if not (c["kind"] == "po_prices" and set(c["ids"]) & ids)]
        oq = [] if DROP_OWN_QUOTE else [c for c in rest if c["kind"] == "own_past_quote"]
        rest = [c for c in rest if c["kind"] != "own_past_quote"]
        first_idx = next((c for c in rest if c["kind"] == "index_change"), None)
        sc = [c for c in rest if c["kind"] == "should_cost"]
        fc = [c for c in rest if c["kind"] == "volume_change"]
        if PATH_IN_ROUND1:  # round 1: 0.79 + 0.48 + 1.26; then the forecast (0.14) leads the one-per-e-mail rounds
            head, nxt = sc + ([first_idx] if first_idx else []) + pp, fc
        else:  # v1 (live 0.9633): forecast in round 1, the path in round 2
            head, nxt = sc + fc + ([first_idx] if first_idx else []), pp
        tail = [c for c in rest if c not in head and c not in nxt]
        measured, fillers = [c for c in tail if not c.get("filler")], [c for c in tail if c.get("filler")]
        rq = []
        if RIVAL_QUOTE_P03:
            opening = (self.sup.get(sid) or {}).get("open_terms", {}).get("unit_price") or self._opening_price or 0
            rq = [c for pt in case["parts"] for c in rival_benchmark_claims(self.facts, sid, pt, opening)]
        if OWN_QUOTE_AFTER_PATH:
            return head + nxt + oq + measured + rq + fillers
        return head + nxt + measured + rq + oq + fillers

    def value_target(self, case, sid, events):
        t = super().value_target(case, sid, events)
        if case["case_id"] not in P03_CASES or not ASK_BELOW_LINE:
            return t
        stand = [standing([m])[1] for m in events if m.get("from") != "buyer" and m.get("term_sheets")]
        if not stand or not stand[-1] or not stand[-1].get("unit_price"):
            return t
        s = self.sup[sid]
        terms = complete_offer(case, stand[-1])
        v_stand = supplier_value(case, terms, s["est"])
        cap = v_stand * (1 - ASK_BELOW_LINE / terms["unit_price"])  # EUR 0.60 under its standing price, in its value
        if t > cap:
            log.info("%s P03: ask capped %.2f -> %.2f (value), EUR %.2f under its %.2f", sid, t, cap, ASK_BELOW_LINE,
                     terms["unit_price"])
            if s.get("ours"):
                s["ours"][-1] = cap
            return cap
        return t
