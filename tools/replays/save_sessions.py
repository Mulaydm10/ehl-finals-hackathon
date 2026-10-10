"""Save every arena session of our team (practice + sandbox) as raw JSON. Read-only: GET calls only, no quota.

    cd tacto/starter-kit && uv run python ../../tools/replays/save_sessions.py [session_id ...]

Writes tools/replays/raw/<case>_<session_id>.json = GET /v1/sessions/{sid} (state, threads, result with trace,
cost breakdown and replay_url) + `thread_messages`: GET .../threads/{supplier} per supplier (full e-mails). Ended sessions are saved once; open ones are skipped until they end.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "analysis" / "tools"))
from arena_env import client  # noqa: E402

RAW = Path(__file__).resolve().parent / "raw"


def save(c, sid, case_id=None, force=False):
    RAW.mkdir(parents=True, exist_ok=True)
    done = list(RAW.glob(f"*_{sid}.json"))
    if done and not force:
        return done[0], False
    s = c.session(sid)
    if s.get("status") != "ended":
        return None, False
    # the full e-mails (bodies with figures, attachments, signals) live in the thread endpoint
    s["thread_messages"] = {sup: c.thread(sid, sup) for sup in (s.get("threads") or {})}
    path = RAW / f"{(case_id or s.get('case_id', 'case:unknown')).split(':')[-1]}_{sid}.json"
    path.write_text(json.dumps(s, indent=1, ensure_ascii=False), encoding="utf-8")
    return path, True


def main(ids, force=False):
    c = client()
    rows = [{"session_id": i, "case_id": None} for i in ids] or [
        r for set_ in ("practice", "sandbox") for r in c.sessions(set_)]
    new = 0
    for r in rows:
        path, fresh = save(c, r["session_id"], r.get("case_id"), force)
        new += fresh
        print(f"{'saved' if fresh else 'have ' if path else 'open '} {r.get('case_id') or ''} {r['session_id']}"
              f" score {r.get('score')} -> {path.name if path else '-'}")
    print(f"{new} new, {len(rows)} sessions")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--force"]
    main(args, "--force" in sys.argv)  # --force: re-save (e.g. to add thread_messages)
