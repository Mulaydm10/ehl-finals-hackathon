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
    # the top 3 that can share one e-mail: one index claim per e-mail (2+ drew "a lot of material" 11/11), no ID twice
    top = []
    for c in pool:
        if c.get("other_part") or c.get("late") or any(set(c["ids"]) & set(x["ids"]) for x in top):
            continue
        # one index claim per e-mail - two (different series) in round 1 of a raw-material case (P18 0.707, rule 91)
        n_idx = sum(x["kind"] == "index_change" for x in top)
        if c["kind"] == "index_change" and (n_idx >= (2 if case["type"] == "raw_material" else 1)
                                            or any(x.get("series") == c.get("series") for x in top)):
            continue
        top.append(c)
    want = {i for c in top[:3] for i in c["ids"]}
    assert want <= set(msg["refs"]), (sorted(want - set(msg["refs"])), msg["refs"])


@pytest.mark.skipif(not OPENINGS.exists(), reason="needs the probed openings")
def test_a_volume_trend_is_cited_once():
    case, threads = load("P07")
    agent = NoIdeaAgent(None)
    agent.decide(case, threads)
    kinds = [c["kind"] for c in agent.sup[next(iter(threads))]["args"]]
    assert kinds.count("forecast") <= 1, kinds


@pytest.mark.skipif(not OPENINGS.exists(), reason="needs the probed openings")
def test_other_parts_price_history_comes_last_and_only_as_an_experiment(monkeypatch):
    import arena_kit.agents.noidea as noidea

    case, threads = load("P18")
    sid = next(iter(threads))
    off = NoIdeaAgent(None)
    off.decide(case, threads)
    assert all(c["part"] in case["parts"] for c in off.sup[sid]["args"] if c["kind"] == "po_prices")
    monkeypatch.setattr(noidea, "EXPERIMENTS", {"all_parts_po"})
    on = NoIdeaAgent(None)
    msg = on.decide(case, threads)["message"]
    args = on.sup[sid]["args"]
    others = [i for i, c in enumerate(args) if c.get("other_part")]
    assert others, [c["kind"] for c in args]
    assert not any(i in msg["refs"] for j in others for i in args[j]["ids"])  # never in round 1
    assert all(args[j]["part"] not in case["parts"] for j in others)


def _p02_after_two_rounds(primary_days):
    """P02 opening, our 90-d asks, its two counters with PRIMARY at `primary_days` and a 30-d alternative in round 1."""
    case, threads = load("P02")
    sid = next(iter(threads))
    ev = list(threads[sid])
    def sup(n, price, days, alt=None):
        sheets = [{"term_sheet_id": f"offer:70510-{n}", "terms": {"unit_price": price, "payment_days": days, "index_clause": None}}]
        if alt:
            sheets.append({"term_sheet_id": f"offer:70510-{n}-a", "terms": {"unit_price": alt, "payment_days": 30, "index_clause": None}})
        return {"from": "sales@70510", "status": "open", "body": "Alternatively, with Zahlungsziel 30 days net: EUR 368.42 per unit.",
                "term_sheets": sheets}
    ours = lambda price: {"from": "buyer", "body": "x", "term_sheets": [{"terms": {"unit_price": price, "payment_days": 90, "index_clause": None}}]}
    ev += [ours(364.69), sup(1, 372.52, primary_days, alt=368.42 if primary_days == 90 else None), ours(365.31), sup(2, 370.85, primary_days)]
    return case, {sid: ev}, sid


@pytest.mark.skipif(not OPENINGS.exists(), reason="needs the probed openings")
def test_a_model_read_limit_needs_two_refusals_of_our_term():
    """P02 load test 791a535b: the model read its 30-d ALTERNATIVE as "payment max 30" while its primary stayed at our 90 d;
    the hard filter made us hop to 30 d (0.531). A limit counts only when its primary refused our term twice."""
    for primary_days, expect_30 in ((90, False), (30, True)):
        case, threads, sid = _p02_after_two_rounds(primary_days)
        agent = NoIdeaAgent()
        agent.decide(case, {sid: threads[sid][:1]})  # prepare
        agent.sup[sid]["last_main"] = {"unit_price": 365.31, "payment_days": 90, "index_clause": None}
        agent.sup[sid]["limits"] = {"payment_days": (None, 30)}  # what the model's notes said
        agent.threads_ref = threads
        sheets = agent._sheets_at(case, sid, 360.0, None, n=3)
        days = {t["payment_days"] for _, t in sheets}
        assert (days <= {14, 30}) == expect_30, (primary_days, days)
