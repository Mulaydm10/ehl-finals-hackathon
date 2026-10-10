"""Offline run of the NoIdea agent WITH an LLM (e.g. gpt-6-astra) on probed cases. No arena sessions.

Uses Dhruv's simulated supplier (src/eval/offline_eval.simulate: real opening quote, exact C_open/C_best)
and records every e-mail the agent writes, so the LLM's prose can be reviewed. Calls the paid LLM API.

    cd tacto/starter-kit && uv run python ../../analysis/tools/offline_astra.py P02 P03 P04

Reads tacto/starter-kit/.env.openai (LLM_PROVIDER, LLM_MODEL, LLM_API_KEY; gitignored).
Writes analysis/offline_runs/<case>_<model>.json.
"""

import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KIT = ROOT / "tacto" / "starter-kit"
sys.path.insert(0, str(KIT))
sys.path.insert(0, str(ROOT / "src" / "eval"))

for line in (KIT / ".env.openai").read_text().splitlines():
    if "=" in line and not line.lstrip().startswith("#"):
        k, v = line.split("=", 1)
        os.environ[k.strip()] = v.strip()

from arena_kit.agents.llm import llm_from_env  # noqa: E402
from arena_kit.agents.noidea import NoIdeaAgent  # noqa: E402
from offline_eval import simulate  # noqa: E402

OUT = ROOT / "analysis" / "offline_runs"


def run(cid, r):
    case = next(c for c in json.loads((ROOT / "datasets/cases_practice.json").read_text(encoding="utf-8"))
                if c["case_id"] == f"case:{cid}")
    probe = json.loads((ROOT / "analysis/cases/openings" / f"{cid}.json").read_text(encoding="utf-8"))
    res = probe["result"]
    llm = llm_from_env()
    log, llm_calls = [], {"n": 0, "seconds": 0.0, "errors": 0}

    def complete(system, user):
        t0 = time.time()
        llm_calls["n"] += 1
        try:
            return llm(system, user)
        except Exception:
            llm_calls["errors"] += 1
            raise
        finally:
            llm_calls["seconds"] += time.time() - t0

    def factory(_):
        agent = NoIdeaAgent(complete)
        decide = agent.decide

        def recorded(case_, threads):
            d = decide(case_, threads)
            m = d["message"]
            log.append({"to": d["supplier_id"], "subject": m.get("subject"), "body": m.get("body"),
                        "term_sheets": [t.get("terms") for t in m.get("term_sheets") or []],
                        "refs": m.get("refs"), "action": m.get("action")})
            return d

        agent.decide = recorded
        return agent

    score, end, msgs = simulate(factory, case, probe["threads"], res["c_open"], res["c_best"], r)
    return {"case": cid, "model": os.environ["LLM_MODEL"], "supplier_r": r, "sim_score": score, "end": end,
            "messages": msgs, "llm": llm_calls, "emails": log}


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for cid in sys.argv[1:]:
        runs = [run(cid, r) for r in (0.30, 0.10)]  # responsive, stubborn supplier
        path = OUT / f"{cid}_{os.environ['LLM_MODEL']}.json"
        path.write_text(json.dumps(runs, indent=1, ensure_ascii=False), encoding="utf-8")
        for x in runs:
            print(f"{cid} r={x['supplier_r']}: sim score {x['sim_score']:.2f} ({x['end']}, {x['messages']} msgs), "
                  f"LLM calls {x['llm']['n']} ({x['llm']['seconds']:.0f}s, {x['llm']['errors']} errors)")
