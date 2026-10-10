"""P04 record script (tools/experiments/p04_record.py) against the supplier fitted on the three live P04 games.

One cent is 0.17 score in P04; at its floor the supplier's 45-day price is EUR 4.89 (0.874, the practice record) and
its 30-day price EUR 4.87 (0.940) if its cash rate is >= 7.5 %, else 4.88. Only its primary sheet can be accepted by
id, and its primary follows our higher-priced sheet's payment term.
"""

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "tools" / "experiments" / "p04_record.py"
pytestmark = pytest.mark.skipif(
    not (ROOT / "analysis/cases/openings/P04.json").exists(), reason="needs the probed P04 opening"
)


def load():
    spec = importlib.util.spec_from_file_location("p04_record", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.parametrize("rate,want", [(0.0693, 0.8737), (0.0720, 0.8737), (0.0760, 0.9399), (0.0769, 0.9399)])
@pytest.mark.parametrize("share", [0.57, 0.3])
def test_it_ends_on_the_best_cent_its_floor_allows(rate, want, share):
    p = load()
    score, end, _ = p.simulate(rate, share=share, verbose=False)
    assert score == pytest.approx(want, abs=1e-4), end


def test_safe_mode_keeps_the_45_day_floor_price_when_it_would_walk():
    p = load()
    score, end, _ = p.simulate(
        0.0760, share=0.3, walk_after_final=1.0, verbose=False, agent=p.P04RecordAgent(send_alternative_back=False)
    )
    assert score == pytest.approx(0.8737, abs=1e-4), end


def test_main30_takes_the_record_by_its_id_without_sending_anything_back():
    p = load()
    score, end, agent = p.simulate(
        0.0760, share=0.3, walk_after_final=1.0, verbose=False, agent=p.P04RecordAgent(True, p.PLAN_MAIN30)
    )
    assert score == pytest.approx(0.9399, abs=1e-4), end
    assert not any("ask for" in (r.get("do") or "") for r in agent.notes)


def test_every_offer_keeps_both_sheets_below_its_floor_and_the_primary_on_our_higher_price():
    p = load()
    for plan, high_days in ((p.PLAN, 45), (p.PLAN_MAIN30, 30)):
        for high, low, _ in plan:
            assert high[1] == high_days and high[0] > low[0]
            for price, days in (high, low):
                assert price < {45: 4.89, 30: 4.87}[days]


@pytest.mark.parametrize(
    "rate,cut,want",
    [(0.0720, 0.0, 0.8737), (0.0760, 0.0, 0.9399), (0.0720, 0.003, 1.0), (0.0693, 0.002, 1.0), (0.0752, 0.002, 0.9399)],
)
def test_probe_takes_a_record_sheet_when_one_clears_its_floor_else_closes_on_the_45_day_floor_price(rate, cut, want):
    """--probe: a supplier agrees to a sheet below its standing offer when the sheet clears its floor (P11
    b1f94bfec7792ffb) and takes the one worth most to it; `cut` = what our pay-on-time promise could take off that
    floor. 4.93 @ 90 d needs only 0.002: its 90-day floor price is 4.9319."""
    p = load()
    score, end, agent = p.simulate(
        rate,
        share=0.3,
        verbose=False,
        agent=p.P04RecordAgent(True, p.PLAN_PROBE, probe=True),
        floor_agree=True,
        patience=3,
        cut=cut,
    )
    assert score == pytest.approx(want, abs=1e-4), end
    for r in agent.notes:  # never the 45-day floor price next to the probe: it would take the sheet worth more to it
        assert not ("probe" in (r.get("do") or "") and "4.89@45" in r["do"])


def test_the_late_payment_line_is_our_true_record():
    p = load()
    line = p.late_payment_line()
    assert "84% of your invoices late" in line and "due date" in line
