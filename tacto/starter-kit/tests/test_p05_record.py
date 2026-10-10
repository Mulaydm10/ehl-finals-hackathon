"""P05 record script (tools/experiments/p05_record.py) against the three bidders as measured in our 10 P05 games.

Fuchsreiter's first counter follows our ask (~70 % of the gap) plus half a rival step when we cite a rival >= 10 %
below its price; the rest of the step comes next round (d9af85e000ab3d4d: ask 25.54 -> 28.00 -> 27.00 @ 14 d).
"""

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "tools" / "experiments" / "p05_record.py"
pytestmark = pytest.mark.skipif(
    not (ROOT / "analysis/cases/openings/P05.json").exists(), reason="needs the probed P05 opening"
)


def load():
    spec = importlib.util.spec_from_file_location("p05_record", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.parametrize("floor,low", [(26.26, 0.97), (26.80, 0.94), (27.50, 0.87)])
def test_it_closes_with_fuchsreiter_near_its_floor(floor, low):
    p = load()
    score, end, _ = p.simulate(floor, verbose=False)
    assert score >= low and "sup:70250" in end, end


def test_first_message_to_fuchsreiter_cites_a_much_lower_rival_and_our_true_payment_record():
    p = load()
    _, _, agent = p.simulate(26.26, verbose=False)
    first = next(r for r in agent.notes if r.get("sid") == "sup:70250")
    assert "cite offer:70240-0 31.5" in first["do"] and first["do"].startswith("ask 24.5@14/28")
    assert "93% of your invoices late" in agent.late_line
    assert "call-off schedule" in first["do"]


def test_every_ask_to_a_bidder_moves_up():
    p = load()
    for sid, asks in p.ASKS.items():
        assert all(b > a for a, b in zip(asks, asks[1:], strict=False)), sid
