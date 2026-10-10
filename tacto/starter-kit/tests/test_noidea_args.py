"""Round 1 carries our strongest verified arguments whatever the language model picks.

Live: the model chose which arguments to send and dropped the decisive one - P10 v2.x sent only the
forecast (its should-cost had moved the first counter 0.55 -> 0.66 in 2d91214cf7693eff), P18 9d4d288eb4ae6789
sent 1 of 4. The order follows what moved suppliers' first counters live: price history (P18 +0.2),
should-cost (P10 +0.11), forecast (P02 +0.13), then falling indices. A volume trend counts once per case
(P07: a second forecast came back `duplicate`).
"""

import json
from pathlib import Path

import pytest

from arena_kit.agents.noidea import NoIdeaAgent

ROOT = Path(__file__).resolve().parents[3]
OPENINGS = ROOT / "analysis" / "cases" / "openings"


def load(cid):
    case = next(c for c in json.loads((ROOT / "datasets" / "cases_practice.json").read_text())
                if c["case_id"] == f"case:{cid}")
    return case, json.loads((OPENINGS / f"{cid}.json").read_text())["threads"]


def no_args_model(system, user):
    """A model that picks the first candidate sheet and NO arguments."""
    return json.dumps({"sheets": [0], "args": [], "opening": "Thank you for your offer and the details.",
                       "notes": {}})


@pytest.mark.skipif(not OPENINGS.exists(), reason="needs the probed openings")
@pytest.mark.parametrize("cid,first", [("P10", "should_cost"), ("P18", "po_prices")])
def test_round_one_carries_the_top_arguments(cid, first):
    case, threads = load(cid)
    agent = NoIdeaAgent(no_args_model)
    msg = agent.decide(case, threads)["message"]
    sid = next(iter(threads))
    pool = agent.sup[sid]["args"]
    assert pool[0]["kind"] == first
    want = {i for c in pool[:3] for i in c["ids"]}
    assert want <= set(msg["refs"]), (sorted(want - set(msg["refs"])), msg["refs"])


@pytest.mark.skipif(not OPENINGS.exists(), reason="needs the probed openings")
def test_a_volume_trend_is_cited_once():
    case, threads = load("P07")
    agent = NoIdeaAgent(None)
    agent.decide(case, threads)
    kinds = [c["kind"] for c in agent.sup[next(iter(threads))]["args"]]
    assert kinds.count("forecast") <= 1, kinds
