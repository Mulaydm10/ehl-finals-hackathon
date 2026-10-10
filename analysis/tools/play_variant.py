"""Play ONE practice case live with an agent variant file - same loop as `arena play` (arena_kit.play.play).
USES ONE PRACTICE SESSION. Saves the finished session to tools/replays/raw/ and logs it in notes/quota_log.md.

    cd tacto/starter-kit && uv run python ../../analysis/tools/play_variant.py case:P04 ../../analysis/agent_variants/noidea_neel.py

LLM: tacto/starter-kit/.env.openai (LLM_PROVIDER / LLM_MODEL / LLM_API_KEY) if present, else plain openings.
"""

import importlib.util
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KIT = ROOT / "tacto" / "starter-kit"
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(ROOT / "tools" / "replays"))
from arena_env import client  # noqa: E402  (loads tacto/starter-kit/.env: ARENA_URL, ARENA_API_KEY)

from arena_kit.play import RemoteTable, play  # noqa: E402

if (KIT / ".env.openai").exists():
    for line in (KIT / ".env.openai").read_text().splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1)
            os.environ[k.strip()] = v.strip()


def main(case_id, agent_file):
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    spec = importlib.util.spec_from_file_location("arena_kit.agents._live_variant", agent_file)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    complete = None
    if os.environ.get("LLM_MODEL"):
        from arena_kit.agents.llm import llm_from_env
        complete = llm_from_env()
    c = client()
    table = RemoteTable(c)
    result = play(table, case_id, mod.NoIdeaAgent(complete))
    sid = table.session_id
    keep = ("deal", "supplier_id", "terms", "c_open", "c_deal", "c_best", "score")
    print(json.dumps({k: result.get(k) for k in keep if k in result}, indent=1))
    print("replay:", f"https://arena.tacto.ai/replay/{sid}", "| practice sessions left:", c.practice_remaining)
    from save_sessions import save
    path, _ = save(c, sid, case_id)
    print("saved:", path)
    score = result.get("score")
    with open(ROOT / "notes" / "quota_log.md", "a", encoding="utf-8") as f:
        f.write(f"| {datetime.now():%Y-%m-%d %H:%M} | Neel | {case_id.split(':')[-1]} | {Path(agent_file).stem} / "
                f"{os.environ.get('LLM_MODEL', 'no LLM')} | **{score:.2f}** | {sid} |\n")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
