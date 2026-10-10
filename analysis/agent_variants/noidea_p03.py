"""P03 variant of Neel's agent (analysis/agent_variants/noidea_neel.py = the P03 record 0.9363 path, untouched here).
Report: analysis/cases/P03_lever.md. Target: beat team "+=" 0.94449 (= EUR 431.22 @ 90 d / 36 m) -> 431.21 or lower.

ONE change, behind switches: one more NEW verified data kind per round after round 1, so the committee (price = its stop minus
one cut per new kind it takes) gets two kinds it never saw in 15 P03 games:
- round 2: OUR ORDER PRICE PATH (PRICE_PATH_P03): "Our orders for this part rose from EUR 400.19 to EUR 412.74 within nine
  months (po:4500013355-10, po:4500014465-10)." The same claim form was TAKEN by P08 (d0708ed1: "it holds and we took it into
  account", first counter 5.41 -> 5.25, 0.912), P18 and P10. Dhruv's year_rise_path() skips price-frozen suppliers, and P03
  was only ever sent the FLAT order run ("does not change our calculation").
- round 3: its own quote by ID (quote:7300003, EUR 412.74, 5 Sep; already in noidea_neel via OWN_QUOTE_ID, never played).
- rounds 4-5: copper -2.2%, labour -0.3% (the record game's 431.67 -> 431.60 -> 431.58), so data lasts to its final at our
  5th message.
Round 1 is unchanged (should-cost + forecast + electronic components -> 431.67 @ 90 d, 3 of 3 games), and so are 90 d / 36 m
/ 4580 a year, the asks and the accept rule.
"""
import importlib.util
import sys
from pathlib import Path

_spec = importlib.util.spec_from_file_location("arena_kit.agents._noidea_neel_p03base",
                                               Path(__file__).with_name("noidea_neel.py"))
_base = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _base
_spec.loader.exec_module(_base)
central = _base.central

P03_CASES = {"case:P03"}
PRICE_PATH_P03 = True  # round 2: our order price path (new kind for P03)
OWN_QUOTE_AFTER_PATH = True  # round 3: its own quote by ID (noidea_neel puts it in round 2)


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
        head = [c for c in rest if c["kind"] in ("should_cost", "volume_change")]
        first_idx = next((c for c in rest if c["kind"] == "index_change"), None)
        head += [first_idx] if first_idx else []
        oq = [c for c in rest if c["kind"] == "own_past_quote"]
        tail = [c for c in rest if c not in head and c not in oq]
        return head + pp + (oq if OWN_QUOTE_AFTER_PATH else []) + tail + ([] if OWN_QUOTE_AFTER_PATH else oq)
