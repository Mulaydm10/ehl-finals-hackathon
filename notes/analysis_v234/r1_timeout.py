"""Per game of a case: buyer moves before its first counter (timeouts / notes / messages), round of our first priced e-mail,
the counter it drew on our main structure, score. python3 r1_timeout.py P11"""
import json, sys
from pathlib import Path
ROOT = Path.home() / "Dhruv/ehl-finals-hackathon"
case = "case:" + sys.argv[1]
rows = []
for f in sorted((ROOT / "datasets/runs").glob("*.json")):
    g = json.loads(f.read_text())
    if (g.get("session") or {}).get("case_id") != case or len(g.get("threads") or {}) != 1:
        continue
    res = (g.get("detail") or {}).get("result") or {}
    tr = res.get("trace") or []
    pre, first_round, counter = [], None, None
    for i, t in enumerate(tr):
        mv = t["move"]
        if t["actor"] == "buyer":
            if mv.get("type") == "message" and mv.get("term_sheets"):
                first_round = t["round"]
                rep = next((x for x in tr[i + 1:] if x["actor"] != "buyer"), None)
                if rep:
                    sh = [rep["move"].get("terms") or {}] + [a.get("terms") or {} for a in rep["move"].get("alternatives") or []]
                    counter = sorted(s.get("unit_price") for s in sh if s.get("unit_price"))
                break
            pre.append(mv.get("type"))
    rows.append(((g.get("session") or {}).get("created_at") or 0, f.stem[:8], res.get("score"), pre, first_round, counter))
rows.sort()
for r in rows[-int(sys.argv[2]) if len(sys.argv) > 2 else 0:]:
    print(r[1], "%.3f" % (r[2] or 0), "before-first-email:", r[3], "first priced e-mail in round", r[4], "its counter(s):", r[5])
