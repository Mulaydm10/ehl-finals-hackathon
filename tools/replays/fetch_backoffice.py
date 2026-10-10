"""Fetch the suppliers' BACK OFFICE for every ended session of our team. Read-only: GET calls only, no quota.

    cd tacto/starter-kit && uv run python ../../tools/replays/fetch_backoffice.py

api.md: GET /v1/sessions/{sid}/backoffice = "the supplier's roles talking internally (who asked whom,
approvals, documents attached) ... only after the case has ended". This is where a supplier's stop shows:
which role capped the price, which approval was asked and refused, what our e-mail triggered. Nobody had
pulled it yet. Writes tools/replays/backoffice/<case>_<session>.json and prints a digest per session.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "analysis" / "tools"))
from arena_env import client  # noqa: E402

OUT = Path(__file__).resolve().parent / "backoffice"


def main():
    c = client()
    OUT.mkdir(parents=True, exist_ok=True)
    rows = [r for set_ in ("practice", "sandbox") for r in c.sessions(set_)]
    for r in rows:
        sid, case = r.get("session_id"), (r.get("case_id") or "case:unknown").split(":")[-1]
        path = OUT / f"{case}_{sid}.json"
        if path.exists():
            continue
        try:
            bo = c.backoffice(sid)
        except Exception as e:  # 403 while a session is still open
            print(f"{case} {sid}: skipped ({e})")
            continue
        path.write_text(json.dumps(bo, indent=1, ensure_ascii=False), encoding="utf-8")
        items = bo if isinstance(bo, list) else bo.get("messages") or bo.get("items") or [bo]
        print(f"\n=== {case} {sid} ({len(items)} entries)")
        for m in items[:40]:
            if isinstance(m, dict):
                who = f"{m.get('from', '?')} -> {m.get('to', '?')}"
                print(f"  {who}: {str(m.get('text') or m.get('body') or m)[:300]}")


if __name__ == "__main__":
    main()
