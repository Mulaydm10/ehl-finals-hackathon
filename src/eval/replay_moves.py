"""Replay a supplier's REAL moves from a live game against the current agent - no quota used.

P07 live session 00ae513af1091e9c: the supplier went 5.56 @ 60 d -> 5.55 @ 90 d -> 5.52 @ 90 d (24 m).
Scenarios: it then holds, or it keeps giving 0.03 per round.

    cd tacto/starter-kit && .venv/bin/python ../../src/eval/replay_moves.py
"""
import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tacto/starter-kit"))
from arena_kit.agents.noidea import NoIdeaAgent  # noqa: E402
from arena_kit.cost import total_cost  # noqa: E402

logging.basicConfig(level=logging.WARNING)
case = next(c for c in json.loads((ROOT / "datasets/cases_practice.json").read_text()) if c["case_id"] == "case:P07")
opening = json.loads((ROOT / "analysis/cases/openings/P07.json").read_text())["threads"]
sid, c_open, c_best = "sup:70610", 391027.4, 299241.49
LIVE = [(5.56, 60), (5.55, 90), (5.52, 90)]
SCENARIOS = {
    "holds at 5.52 after the live moves": LIVE + [(5.52, 90)] * 7,
    "keeps giving 0.03 per round": LIVE + [(round(5.52 - 0.03 * i, 2), 90) for i in range(1, 8)],
}

for label, moves in SCENARIOS.items():
    threads, agent, path = {sid: list(opening[sid])}, NoIdeaAgent(None), []
    for k, (price, days) in enumerate(moves):
        msg = agent.decide(case, threads)["message"]
        if msg.get("action"):
            st = threads[sid][-1]["term_sheets"][0]["terms"]
            c = total_cost(case, st)
            print(f"{label}: ours {path} -> {msg['action']['type']} at {st['unit_price']} "
                  f"(score {(c_open - c) / (c_open - c_best):.2f}) after {k} messages")
            break
        path.append(min(msg["term_sheets"], key=lambda t: total_cost(case, t["terms"]))["terms"]["unit_price"])
        threads[sid] += [{**msg, "from": "buyer"},
                         {"from": f"sales@{sid}", "status": "open", "body": "", "term_sheets": [
                             {"term_sheet_id": f"offer:{sid}-{k + 1}",
                              "terms": {"unit_price": price, "payment_days": days, "contract_months": 24}}]}]
    else:
        print(f"{label}: no decision within {len(moves)} messages, ours {path}")
