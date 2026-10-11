"""(v6) One time budget for all model calls of one decision: a slow or hanging API must never hold a reply past the 60 s
a supplier waits (each call alone has a 45 s timeout; two calls made a decision ~90 s)."""
import time

import pytest

from arena_kit.agents import noidea
from arena_kit.agents.noidea import NoIdeaAgent


def slow(seconds, out="ok"):
    def complete(system, user):
        time.sleep(seconds)
        return out
    return complete


class Probe(NoIdeaAgent):
    """decide() makes model calls the way the agent does; records the clock it saw."""
    def decide(self, case, threads):
        self.seen_t0 = self.decision_t0
        return [self.complete("s", "u") for _ in range(case)]


def test_fast_call_inside_a_decision_goes_through():
    a = Probe(slow(0.05))
    assert a.decide(2, None) == ["ok", "ok"]
    assert a.seen_t0 is not None and a.decision_t0 is None  # the clock runs only during the decision


def test_slow_call_is_cut_at_the_budget(monkeypatch):
    monkeypatch.setattr(noidea, "LLM_BUDGET_S", 1.0)
    monkeypatch.setattr(noidea, "LLM_MIN_S", 0.1)
    a = Probe(slow(3.0))
    t = time.monotonic()
    with pytest.raises(TimeoutError):
        a.decide(1, None)
    assert time.monotonic() - t < 2.0  # cut at ~1 s, not the call's 3 s
    assert a.decision_t0 is None


def test_spent_budget_makes_no_call(monkeypatch):
    monkeypatch.setattr(noidea, "LLM_BUDGET_S", 1.0)
    monkeypatch.setattr(noidea, "LLM_MIN_S", 0.5)
    calls = []

    def complete(system, user):
        calls.append(1)
        time.sleep(0.7)
        return "ok"
    a = Probe(complete)
    with pytest.raises(TimeoutError):  # 1st call takes 0.7 s, 0.3 s left < 0.5 s: the 2nd is never made
        a.decide(2, None)
    assert len(calls) == 1


def test_outside_a_decision_calls_through():
    a = Probe(slow(0.05))
    assert a.complete("s", "u") == "ok"


def test_opt_out_keeps_the_plain_call(monkeypatch):
    monkeypatch.setattr(noidea, "EXPERIMENTS", {"no_llm_budget"})
    f = slow(0.01)
    assert Probe(f).complete is f
