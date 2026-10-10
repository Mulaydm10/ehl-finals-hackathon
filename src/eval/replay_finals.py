"""Replay the REAL final offers from the archive through the current agent: which sheet does it accept now?
Since v2.4 it judges every term sheet a supplier sends ('-a' alternatives included), not only the first.

    cd tacto/starter-kit && .venv/bin/python ../../src/eval/replay_finals.py
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
cases = {c["case_id"]: c for c in json.loads((ROOT / "datasets/cases_practice.json").read_text(encoding="utf-8"))}
probes = {f.stem: json.loads(f.read_text(encoding="utf-8")).get("result", {}) for f in (ROOT / "analysis/cases/openings").glob("*.json")}
probes["P01"] = {"c_open": 1153779.74, "c_best": 1096815.78}
gain = []
for f in sorted((ROOT / "datasets/runs").glob("*.json")):
    g = json.loads(f.read_text(encoding="utf-8"))
    cid = g["session"]["case_id"]
    if cid not in cases or len(g["threads"]) != 1:
        continue
    sup, th = next(iter(g["threads"].items()))
    ms = th.get("messages", [])
    idx = [i for i, m in enumerate(ms) if m.get("from") != "buyer" and m.get("status") == "final_offer"]
    if not idx or len(ms[idx[0]].get("term_sheets") or []) < 2:
        continue
    i, case, p = idx[0], cases[cid], probes.get(cid[5:])
    a = NoIdeaAgent(None)
    d = a.decide(case, {sup: ms[: i + 1]})
    act = d["message"].get("action") or {}
    sc = lambda t: (p["c_open"] - total_cost(case, t)) / (p["c_open"] - p["c_best"]) if p else float("nan")
    sheets = {x["term_sheet_id"]: x["terms"] for x in ms[i]["term_sheets"]}
    first = ms[i]["term_sheets"][0]["term_sheet_id"]
    chosen = act.get("term_sheet_id")
    got = sc(sheets[chosen]) if chosen in sheets else float("nan")
    print(f"{cid[5:]} {g['session']['session_id']}: " + " | ".join(f"{k} {sc(t):.3f}" for k, t in sheets.items())
          + f"  -> agent {act.get('type')} {chosen} ({got:.3f}; first sheet {sc(sheets[first]):.3f})")
    if chosen in sheets:
        gain.append(got - sc(sheets[first]))
if gain:
    print(f"mean gain vs always taking the first sheet: {sum(gain) / len(gain):+.3f} over {len(gain)} finals")
