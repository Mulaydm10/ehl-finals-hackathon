"""Run one experiment from analysis/experiments/plan.json against the practice arena, with guard rails.

    cd tacto/starter-kit
    uv run python ../../tools/experiments/run_plan.py E1               # play experiment E1
    uv run python ../../tools/experiments/run_plan.py E1 --dry-run     # show what would be played, play nothing
    uv run python ../../tools/experiments/run_plan.py E4 --switches all_parts_po   # override the switches

Per game it
  1. stops before the practice quota would fall below the plan's `reserve` (kept for the final rehearsal);
  2. plays the case with the noidea agent and the model from .env / .env.openai - as `arena play --agent
     noidea` does - with the experiment's NOIDEA_EXPERIMENTS switches;
  3. saves the full session to datasets/runs/<session>.json and the supplier back office to
     tools/replays/backoffice/ (UTF-8, readable on every OS);
  4. appends one row to analysis/experiments/results.jsonl and to notes/quota_log.md.
At the end it prints every game against the case's baseline and the experiment's keep rule.
"""

import argparse
import collections
import datetime
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KIT = ROOT / "tacto" / "starter-kit"
sys.path.insert(0, str(KIT))

from arena_kit.cli import load_env  # noqa: E402
from arena_kit.client import ArenaClient, ArenaError  # noqa: E402
from arena_kit.cost import total_cost  # noqa: E402
from arena_kit.play import RemoteTable, play, quota_used_up  # noqa: E402


def measure(case, result):
    """What we compare across games: score, first counter (in score units), final round, timeouts, claims."""
    sc = result.get("score")
    out = {"score": round(sc, 3) if sc is not None else None, "deal": result.get("deal"), "first_counter": None,
           "final_round": None,
           "timeouts": 0, "claims": {}, "took": 0, "confirms": 0}
    if not result.get("c_open") or result.get("c_best") is None:
        return out
    base, span = result.get("terms") or {}, result["c_open"] - result["c_best"]

    def score(terms):
        return (result["c_open"] - total_cost(case, {**base, **terms})) / span if span else None

    claims = collections.Counter()
    for t in result.get("trace", []):
        mv = t.get("move") or {}
        if t.get("actor") == "buyer":
            out["timeouts"] += mv.get("type") == "timeout"
            continue
        if t.get("round") == 1 and out["first_counter"] is None and mv.get("terms"):
            sheets = [mv["terms"]] + [a["terms"] for a in mv.get("alternatives") or []]
            out["first_counter"] = round(max(score(s) for s in sheets), 3)
        if mv.get("status") == "final_offer" and out["final_round"] is None:
            out["final_round"] = t.get("round")
        claims.update(c.get("result") for c in mv.get("claim_results") or [])
        reasons = " ".join(t.get("reasons") or [])
        out["took"] += reasons.count("took it into account") + reasons.count("fair point")
        out["confirms"] += reasons.count("confirm our case")
    out["claims"] = dict(claims)
    return out


def archive(client, sid, case_id):
    """The full session in the archive format of src/eval/archive_runs.py, plus the back office."""
    detail = client.session(sid)
    threads = {sup: client.thread(sid, sup) for sup in (detail.get("threads") or {})}
    summary = {"session_id": sid, "case_id": case_id, "status": detail.get("status"), "set": "practice",
               "created_at": datetime.datetime.now(datetime.UTC).timestamp()}
    runs = ROOT / "datasets" / "runs"
    runs.mkdir(parents=True, exist_ok=True)
    (runs / f"{sid}.json").write_text(json.dumps({"session": summary, "detail": detail, "threads": threads},
                                                 ensure_ascii=False, indent=1), encoding="utf-8")
    try:
        bo = client.backoffice(sid)
        box = ROOT / "tools" / "replays" / "backoffice"
        box.mkdir(parents=True, exist_ok=True)
        (box / f"{case_id.split(':')[-1]}_{sid}.json").write_text(json.dumps(bo, ensure_ascii=False, indent=1),
                                                                   encoding="utf-8")
    except ArenaError:
        pass  # the back office shows only after the case has ended


def wait_for_end(client, sid, limit_s=900):
    """After a crash the session ends by itself (timeouts, walk-aways): wait for it, return its result."""
    import time

    t0 = time.monotonic()
    while time.monotonic() - t0 < limit_s:
        state = client.session(sid)
        if state.get("status") == "ended":
            return state.get("result") or {"deal": False, "end_reason": state.get("end_reason")}
        time.sleep(15)
    return {"deal": False, "end_reason": "still open after the crash"}


def quota_left(client):
    try:
        return (client.me().get("practice") or {}).get("left")
    except ArenaError:
        return client.practice_remaining


def git_commit():
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True,
                              text=True, check=True).stdout.strip()
    except Exception:
        return "?"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("experiment")
    ap.add_argument("--plan", default=str(ROOT / "analysis" / "experiments" / "plan.json"))
    ap.add_argument("--switches", help="comma-separated NOIDEA_EXPERIMENTS, overrides the plan's")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
    exp = plan["experiments"][args.experiment]
    switches = sorted(x for x in (args.switches.split(",") if args.switches is not None else exp["switches"]) if x)
    games = [cid for cid, n in exp["games"] for _ in range(n)]
    print(f"{args.experiment}: {exp['title']}\n  switches {switches or 'none'}; games {games}")
    print(f"  keep if: {exp['keep_if']}")
    if args.dry_run:
        return []

    os.chdir(KIT)  # .env, .env.openai and the data package live here
    load_env(".env")
    load_env(".env.openai")
    os.environ["NOIDEA_EXPERIMENTS"] = ",".join(switches)
    import arena_kit.agents.noidea as noidea
    from arena_kit.agents import llm_from_env

    noidea.EXPERIMENTS = set(switches)  # the module read the variable at import
    complete = llm_from_env() if os.environ.get("LLM_MODEL") else None
    client = ArenaClient()
    cases = {c["case_id"]: c for c in client.cases("practice")}
    commit, model = git_commit(), os.environ.get("LLM_MODEL", "no model")
    reserve = plan.get("reserve", 40)
    rows = []

    def one(cid):
        left = quota_left(client)
        if left is not None and left <= reserve:
            return {"case": cid, "skipped": f"quota left {left} <= reserve {reserve}"}
        table, error = RemoteTable(client), None
        try:
            result = play(table, f"case:{cid}", noidea.NoIdeaAgent(complete))
        except Exception as e:  # never lose the game: record OUR session (the team key is shared - E1 once logged a
            if isinstance(e, ArenaError) and quota_used_up(e):  # teammate's concurrent P05 session as ours)
                return {"case": cid, "skipped": "practice quota used up"}
            if not table.session_id:
                return {"case": cid, "skipped": f"no session opened: {e}"}
            error, result = f"{type(e).__name__}: {e}", wait_for_end(client, table.session_id)
        archive(client, table.session_id, f"case:{cid}")
        m = measure(cases[f"case:{cid}"], result)
        row = {"exp": args.experiment, "case": cid, "session": table.session_id, "switches": switches,
               "commit": commit, "model": model, "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), **m}
        return {**row, "error": error, "end_reason": result.get("end_reason")} if error else row

    with ThreadPoolExecutor(max_workers=max(1, min(exp.get("parallel", 1), 10))) as pool:
        rows = list(pool.map(one, games))

    played = [r for r in rows if "session" in r]
    out = ROOT / "analysis" / "experiments" / "results.jsonl"
    with out.open("a", encoding="utf-8") as f:
        for r in played:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with (ROOT / "notes" / "quota_log.md").open("a", encoding="utf-8") as f:
        for r in played:
            sc = f"{r['score']:.2f}" if r["score"] is not None else "no score"
            if r.get("error"):
                sc += f" - CRASHED: {r['error'][:80]}"
            f.write(f"| {r['time']} | Parth | {r['case']} | noidea {commit} {args.experiment}"
                    f"{' + ' + ','.join(switches) if switches else ''} / {model} | {sc} (first counter "
                    f"{r['first_counter']}, final round {r['final_round']}, timeouts {r['timeouts']}) "
                    f"| {r['session']} |\n")

    base = plan.get("baseline", {})
    print(f"\n{'case':4} {'session':16} {'score':>6} {'best':>6} {'median':>6} {'first':>6} {'best1st':>7} "
          f"{'final@':>6} {'t/o':>3}  claims")
    for r in rows:
        if "session" not in r:
            print(f"{r['case']:4} skipped: {r['skipped']}")
            continue
        b = base.get(r["case"], {})
        show = {k: "-" if r[k] is None else r[k] for k in ("score", "first_counter", "final_round")}
        print(f"{r['case']:4} {r['session']:16} {show['score']:>6} {b.get('best', '-'):>6} {b.get('median', '-'):>6} "
              f"{show['first_counter']:>6} {b.get('best_first_counter', '-'):>7} {show['final_round']:>6} "
              f"{r['timeouts']:>3}  {r['claims']} took={r['took']} confirms={r['confirms']}")
    print(f"\nkeep if: {exp['keep_if']}\nresults: {out.relative_to(ROOT)}; quota left: {quota_left(client)}")
    return rows


if __name__ == "__main__":
    main()
