"""Open a case, save the opening quotes + quote PDFs, walk away, save the result (c_open, c_best, c_alt).

One practice session per case. Log each one in notes/quota_log.md (this script appends the line).

    cd tacto/starter-kit && uv run python ../../analysis/tools/probe_open.py P02 P03 ...
"""

import json
import sys
from datetime import datetime

from arena_env import ROOT, client

from arena_kit.docs import quote_terms, read_document

OUT = ROOT / "analysis" / "cases" / "openings"
LOG = ROOT / "notes" / "quota_log.md"


def probe(c, cid):
    cid = cid if cid.startswith("case:") else f"case:{cid}"
    s = c.open_session(cid)
    sid = s["session_id"]
    quotes = {}
    for sup, msgs in s["threads"].items():
        for m in msgs:
            for att in m.get("attachments") or []:
                text = read_document(att["name"], c.attachment(sid, att["attachment_id"]))
                att["text"] = text
                if att["name"].startswith("quote"):
                    quotes[sup] = quote_terms(text)
    c.walk_away(sid)
    result = c.session(sid).get("result", {})
    rec = {"case_id": cid, "session_id": sid, "threads": s["threads"], "opening": s.get("opening"),
           "quote_terms": quotes,
           "result": {k: result.get(k) for k in ("c_open", "c_deal", "c_alt", "c_best", "score")}}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{cid.split(':')[1]}.json").write_text(json.dumps(rec, indent=1, ensure_ascii=False), encoding="utf-8")
    now = datetime.now().strftime("%Y-%m-%d %H:%M")  # local time (CEST), as in the log header
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"| {now} | Neel | {cid.split(':')[1]} | probe: open + walk away (exact c_open/c_best) "
                f"| {result.get('score') or 0:.2f} | {sid} |\n")
    print(cid, sid, rec["result"], "remaining", c.practice_remaining)
    return rec


if __name__ == "__main__":
    c = client()
    for cid in sys.argv[1:]:
        probe(c, cid)
