"""The reasons each supplier gives in reply to our FIRST priced e-mail and to later ones, counted per case (templated:
numbers are already blanked by the arena). Shows how a supplier treats data in round 1 vs later."""
import json, collections, sys
from pathlib import Path
ROOT = Path.home() / "Dhruv/ehl-finals-hackathon"
want = set(sys.argv[1:])
cnt = collections.defaultdict(collections.Counter)
for f in sorted((ROOT / "datasets/runs").glob("*.json")):
    try:
        g = json.loads(f.read_text())
    except Exception:
        continue
    res = (g.get("detail") or {}).get("result") or {}
    cid = (g.get("session") or {}).get("case_id")
    tr = res.get("trace") or []
    if not cid or not tr or len(g.get("threads") or {}) != 1 or (want and cid.split(":")[1] not in want):
        continue
    nb = 0
    for i, t in enumerate(tr):
        if t["actor"] == "buyer" and t["move"].get("type") == "message" and t["move"].get("term_sheets"):
            nb += 1
            rep = next((x for x in tr[i + 1:] if x["actor"] != "buyer"), None)
            if rep:
                ph = "r1" if nb == 1 else "later"
                for r in rep.get("reasons") or []:
                    cnt[(cid, ph)][r[:150]] += 1
for (cid, ph), c in sorted(cnt.items()):
    print(f"\n=== {cid} {ph}")
    for r, n in c.most_common(14):
        print(f"  {n:3d}  {r}")
