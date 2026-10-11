"""Play ONE live P18 game with analysis/agent_variants/noidea_p18_top.py and record it. USES ONE PRACTICE SESSION.

    cd tacto/starter-kit
    uv run python ../../tools/experiments/p18_top_run.py <variant 0-11>

The variant picks msg 2's opening (P18_TOP_R2): identical text gets the identical cached reply, a new text a new draw.
Records: tools/replays/raw/P18_<sid>.json, datasets/runs/<sid>.json, tools/replays/backoffice/P18_<sid>.json,
notes/quota_log.md, analysis/experiments/p18_top_results.jsonl. Endpoints: cases, sessions, threads, backoffice, me only.
No model: the P18 path writes every e-mail in code (complete=None).
"""
import datetime
import importlib.util
import json
import logging
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KIT = ROOT / "tacto" / "starter-kit"
sys.path[:0] = [str(KIT), str(ROOT / "tools" / "experiments"), str(ROOT / "tools" / "replays")]
import run_plan  # noqa: E402  (archive(): datasets/runs + back office)
from arena_kit.cli import load_env  # noqa: E402
from arena_kit.client import ArenaClient  # noqa: E402
from arena_kit.play import RemoteTable, play  # noqa: E402
from save_sessions import save  # noqa: E402


def main(variant):
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    os.environ["P18_TOP_R2"] = str(variant)
    spec = importlib.util.spec_from_file_location("arena_kit.agents._p18top_live",
                                                  ROOT / "analysis/agent_variants/noidea_p18_top.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    load_env(str(KIT / ".env"))
    c = ArenaClient()
    table = RemoteTable(c)
    result = play(table, "case:P18", mod.NoIdeaAgent(None))
    sid = table.session_id
    print(json.dumps({k: result.get(k) for k in ("deal", "terms", "c_deal", "score") if k in result}, indent=1))
    save(c, sid, "case:P18")
    run_plan.archive(c, sid, "case:P18")
    th = c.thread(sid, "sup:70740")["messages"]
    path = []
    for m in th:
        ts = (m.get("term_sheets") or [])
        p = [f"{t['terms'].get('unit_price')}@{t['terms'].get('payment_days')}d"
             f"/db{(t['terms'].get('index_clause') or {}).get('deadband_pct', '-')}" for t in ts]
        path.append(("us " if m.get("from") == "buyer" else "it ") + (m.get("status") or "") + " " + ",".join(p))
    when = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    sc = result.get("score")
    terms = result.get("terms") or {}
    deal = (f"{terms.get('unit_price')} @ {terms.get('payment_days')} d db"
            f"{(terms.get('index_clause') or {}).get('deadband_pct', '-')}" if terms else "no deal")
    with (ROOT / "notes" / "quota_log.md").open("a", encoding="utf-8") as f:
        f.write(f"| {when} | Parth | P18 | noidea_p18_top r2 variant {variant} {os.environ.get('P18_TOP_MONTHS', '24')} m mode {os.environ.get('P18_TOP_MODE', 'top')} (6c2813ce msg 1, msg 2 variant, record sheets "
                f"inside its 2% at msg 3; no model) | {sc if sc is None else round(sc, 4)} ({deal}) | {sid} |\n")
    out = ROOT / "analysis" / "experiments" / "p18_top_results.jsonl"
    with out.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"time": when, "variant": variant, "session": sid, "score": sc, "deal": deal, "path": path,
                            "commit": run_plan.git_commit()}, ensure_ascii=False) + "\n")
    print("path:", " | ".join(path))
    print(f"session {sid} score {sc} deal {deal}; practice sessions left: {c.practice_remaining}")


if __name__ == "__main__":
    main(int(sys.argv[1]))
