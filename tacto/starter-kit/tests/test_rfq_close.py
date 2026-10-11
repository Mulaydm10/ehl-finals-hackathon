"""RFQ close invariant on the stress lab's multi-supplier cases: the agent never accepts one bidder while another live
bidder's standing offer is cheaper by its OWN cost model (stress ST047, v1: a high opener taken at its frozen take line
with two cheaper offers on the table)."""
import importlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
STRESS = ROOT / "stress"
pytestmark = pytest.mark.skipif(not (STRESS / "cases").exists(), reason="needs the stress lab (stress/)")


def rfq_cases():
    import json
    return [p for p in sorted((STRESS / "cases").glob("ST*.json")) if len(json.loads(p.read_text())["suppliers"]) > 1]


def test_an_rfq_accept_is_never_dearer_than_another_live_bidders_standing_offer():
    sys.path.insert(0, str(STRESS))
    R = importlib.import_module("run_stress")
    from arena_kit.agents.noidea_rfq import NoIdeaAgent
    from arena_kit.play import live_threads
    bad = []

    def agent():
        a = NoIdeaAgent(None)
        d0 = a.decide

        def decide(case, threads):
            d = d0(case, threads)
            act = d["message"].get("action") or {}
            sid = d["supplier_id"]
            if act.get("type") == "accept" and sid in a.sup:
                mine = a.best_sheet(case, sid, threads[sid])[2]
                others = [a.best_sheet(case, x, threads[x])[2] for x in live_threads(threads) if x in a.sup and x != sid]
                if others and min(others) < mine * 0.995:
                    bad.append((case["case_id"], sid, round(mine), round(min(others))))
            return d
        a.decide = decide
        return a

    cases = rfq_cases()
    assert cases
    for p in cases:
        R.play_case(p, agent)
    assert not bad, bad
