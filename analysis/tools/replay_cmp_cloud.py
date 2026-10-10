"""replay_cmp.py with the two agent files as arguments (cloud session; offline, no arena, no LLM).

    cd tacto/starter-kit && uv run python ../../analysis/tools/replay_cmp_cloud.py OLD_AGENT NEW_AGENT GAME.json [GAME.json ...]
Feeds each live game's real supplier messages to both agents and prints our asks turn by turn (SAME / DIFFERENT)."""
import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
logging.disable(logging.CRITICAL)
sys.argv, (old, new, *games) = sys.argv[:1], sys.argv[1:]
import importlib.util  # noqa: E402

spec = importlib.util.spec_from_file_location("replay_cmp_core", ROOT / "analysis/tools/replay_cmp.py")
src = (ROOT / "analysis/tools/replay_cmp.py").read_text(encoding="utf-8")
core = src.split("\nfor f in sys.argv[1:]:")[0]  # load(), asks(), cases - without the module-level run
ns = {"__file__": str(ROOT / "analysis/tools/replay_cmp.py"), "__name__": "replay_cmp_core"}
core = core.replace('A = load(ROOT / "analysis/agent_variants/.tmp_replay/noidea_neel.py", "_base")', "")
core = core.replace('B = load(ROOT / "analysis/agent_variants/noidea_neel.py", "_new")', "")
exec(compile(core, "replay_cmp_core", "exec"), ns)
A, B = ns["load"](Path(old).resolve(), "_base"), ns["load"](Path(new).resolve(), "_new")
for f in games:
    d = json.loads(Path(f).read_text(encoding="utf-8"))
    case = ns["cases"][d["case_id"]]
    for sid, th in d["thread_messages"].items():
        msgs = th["messages"]
        a, b = ns["asks"](A, case, msgs, sid), ns["asks"](B, case, msgs, sid)
        live = [[(t["terms"]["unit_price"], t["terms"].get("payment_days")) for t in (m.get("term_sheets") or [])]
                for m in msgs if m["from"] == "buyer"]
        print(f"=== {Path(f).name} score {d['result'].get('score'):.3f}  {'SAME' if a == b else 'DIFFERENT'}")
        for k, (x, y, z) in enumerate(zip(a, b, live)):
            flag = "" if x == y else "   <-- changed"
            print(f"  turn {k + 1}: live {z}\n           base {x}\n           new  {y}{flag}")
