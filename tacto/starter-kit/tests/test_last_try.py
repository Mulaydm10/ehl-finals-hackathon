"""(v3) Last try before walking: when the supplier's final costs us more than our alternative, the case ends at the
alternative's score whatever we send, so one last sheet that beats the alternative goes out before we walk. Stress lab
ST077 (P08 copy): its own '-a' sheet (6.20 @ 30 d / 12 months) beat our alternative while its final did not - v2 walked
(0.000), v3 proposes that sheet back and it agrees (0.404). ST116 (P12 copy): a sheet just under the alternative is
agreed (0.326 -> 0.348). Opt-out `no_last_try` restores v2."""
import importlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
STRESS = ROOT / "stress"
pytestmark = pytest.mark.skipif(not (STRESS / "cases_v2" / "ST077.json").exists(), reason="needs the stress lab (stress/)")


def _play(name):
    sys.path.insert(0, str(STRESS))
    R = importlib.import_module("run_stress")
    from arena_kit.agents.noidea_rfq import NoIdeaAgent
    return R.play_case(STRESS / "cases_v2" / f"{name}.json", lambda: NoIdeaAgent(None))


def test_its_own_alternative_that_beats_ours_is_proposed_before_walking():
    r = _play("ST077")
    assert r["end"] == "accepted", r["end"]
    assert r["c_deal"] < r["c_alt"]
    assert r["score"] > 0.4


def test_a_sheet_just_under_our_alternative_goes_out_before_walking():
    r = _play("ST116")
    assert r["end"] == "accepted", r["end"]
    assert r["c_deal"] < r["c_alt"]
