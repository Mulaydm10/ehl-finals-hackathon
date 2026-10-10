"""Replay the live P05 RFQ (f8604d43d3fbf92f) at the moment the agent accepted 70240's EUR 32.00:
what did it see for the other two bidders? (no quota)

    cd tacto/starter-kit && .venv/bin/python ../../src/eval/debug_rfq.py
"""
import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tacto/starter-kit"))
from arena_kit.agents.noidea import NoIdeaAgent  # noqa: E402
from arena_kit.cost import total_cost  # noqa: E402
from arena_kit.play import live_threads  # noqa: E402

logging.basicConfig(level=logging.INFO, format="   log: %(message)s")
case = next(c for c in json.loads((ROOT / "datasets/cases_practice.json").read_text()) if c["case_id"] == "case:P05")
g = json.loads((ROOT / "datasets/runs/f8604d43d3fbf92f.json").read_text())
full = {s: th["messages"] for s, th in g["threads"].items()}
# state just before our accept to 70240: 70240 up to its EUR 32.00 reply; the others as far as they were (all but last)
cut = {"sup:70240": next(i for i, m in enumerate(full["sup:70240"]) if (m.get("action") or {}).get("type") == "accept")}
threads = {s: ms[: cut.get(s, len(ms) - 1)] for s, ms in full.items()}
a = NoIdeaAgent(None)
a.decide(case, {s: ms[:1] for s, ms in full.items()})  # prepare on the openings
print("live threads:", live_threads(threads))
for s, ms in threads.items():
    sh, t, c = a.best_sheet(case, s, ms)
    print(f"{s}: last status {ms[-1].get('status')}, best sheet {sh} {t} -> C {c:,.0f} | must-haves ok:",
          __import__("arena_kit.cost", fromlist=["must_haves_ok"]).must_haves_ok(case, t or {}, a.sup[s]["std"]))
d = a.decide(case, threads)
print("decision:", d["supplier_id"], d["message"].get("action") or "send")
