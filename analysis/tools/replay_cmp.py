"""Counterfactual replay: feed a live game's real supplier messages to two agent files and compare our asks turn by turn.
No arena, no LLM (complete=None -> template wording). It reproduces our live asks to the cent.

    cd tacto/starter-kit && .venv/Scripts/python.exe ../../analysis/tools/replay_cmp.py ../../tools/replays/raw/P03_14ab701cbfba6767.json
Compares analysis/agent_variants/.tmp_replay/noidea_neel.py (copy the old version there, with central.py) against the current file."""
import glob
import importlib.util
import json
import logging
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\neels\ehl-finals-hackathon")
sys.path.insert(0, str(ROOT / "tacto/starter-kit/src"))
logging.disable(logging.CRITICAL)


def load(path, name):
    spec = importlib.util.spec_from_file_location(f"arena_kit.agents.{name}", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod.NoIdeaAgent


cases = {c["case_id"]: c for c in json.loads((ROOT / "datasets/cases_practice.json").read_text(encoding="utf-8"))}
A = load(ROOT / "analysis/agent_variants/.tmp_replay/noidea_neel.py", "_base")
B = load(ROOT / "analysis/agent_variants/noidea_neel.py", "_new")


def asks(Agent, case, msgs, sid):
    ag, out = Agent(None), []
    for i, m in enumerate(msgs):
        if m["from"] != "buyer":
            continue
        threads = {sid: [dict(x) for x in msgs[:i]]}
        try:
            d = ag.decide(case, threads)["message"]
        except Exception as e:  # noqa: BLE001
            out.append(f"ERR {type(e).__name__}: {e}")
            continue
        out.append(d.get("action", {}).get("type") if d.get("action") else
                   [(u["unit_price"], u.get("payment_days"), u.get("contract_months")) for t in d.get("term_sheets", []) for u in [t.get("terms", t)]]
                   + sorted(d.get("refs") or []))
    return out


for f in sys.argv[1:]:
    d = json.loads(Path(f).read_text(encoding="utf-8"))
    case = cases[d["case_id"]]
    for sid, th in d["thread_messages"].items():
        msgs = th["messages"]
        a, b = asks(A, case, msgs, sid), asks(B, case, msgs, sid)
        live = [[(t["terms"]["unit_price"], t["terms"].get("payment_days")) for t in (m.get("term_sheets") or [])]
                for m in msgs if m["from"] == "buyer"]
        print(f"=== {Path(f).name} score {d['result'].get('score'):.3f}  {'SAME' if a == b else 'DIFFERENT'}")
        for k, (x, y, z) in enumerate(zip(a, b, live)):
            flag = "" if x == y else "   <-- changed"
            print(f"  turn {k + 1}: live {z}\n           base {x}\n           new  {y}{flag}")
