"""Collect every real supplier e-mail (full text, real figures) from our practice sessions.

GET /v1/sessions and /v1/sessions/{sid}/threads/{supplier} - no practice quota. Writes
datasets/F_supplier_emails.jsonl: one line per supplier message, with the case, round, status, its standing
term sheet and the body. Test set for the agent's reply reader (noidea.read_reply).

    cd tacto/starter-kit && .venv/bin/python ../../src/eval/collect_threads.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src/eval"))
from signals import client  # noqa: E402

c = client()
out, n = [], 0
for s in c.get("/v1/sessions").json():
    sess = c.get(f"/v1/sessions/{s['session_id']}").json()
    for sup in (sess.get("threads") or {}):
        th = c.get(f"/v1/sessions/{s['session_id']}/threads/{sup}").json()
        rnd = 0
        for m in th.get("messages", []):
            if m.get("from") == "buyer":
                rnd += 1
                continue
            sheets = m.get("term_sheets") or []
            out.append({"case": s["case_id"], "session": s["session_id"], "supplier": sup, "round": rnd,
                        "status": m.get("status"), "standing": sheets[0]["terms"] if sheets else None,
                        "body": m.get("body", "")})
            n += 1
(ROOT / "datasets/F_supplier_emails.jsonl").write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in out) + "\n")
print(f"{n} supplier e-mails from {len({x['session'] for x in out})} sessions -> datasets/F_supplier_emails.jsonl")
alts = [x for x in out if "lternativ" in x["body"]]
print(f"{len(alts)} contain 'Alternatively'; statuses:", {st: sum(x['status'] == st for x in out) for st in {x['status'] for x in out}})
