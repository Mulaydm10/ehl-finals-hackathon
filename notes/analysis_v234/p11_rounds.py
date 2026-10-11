"""P11 (or any case): cut per supplier reply by OUR message number and verified facts in it; and whether a payment
promise/admission was credited in its reasons. Same structure only."""
import json, sys, collections, statistics
from pathlib import Path
ROOT = Path.home() / "Dhruv/ehl-finals-hackathon"
case = "case:" + (sys.argv[1] if len(sys.argv) > 1 else "P11")
rows = collections.defaultdict(list)
for f in sorted((ROOT / "datasets/runs").glob("*.json")):
    g = json.loads(f.read_text())
    if (g.get("session") or {}).get("case_id") != case or len(g.get("threads") or {}) != 1:
        continue
    tr = ((g.get("detail") or {}).get("result") or {}).get("trace") or []
    nb, last = 0, None
    for i, t in enumerate(tr):
        mv = t["move"]
        if t["actor"] != "buyer":
            if mv.get("terms", {}).get("unit_price"):
                last = mv["terms"]
            continue
        if mv.get("type") != "message" or not mv.get("term_sheets"):
            continue
        nb += 1
        rep = next((x for x in tr[i + 1:] if x["actor"] != "buyer"), None)
        if not rep or not last or not (rep["move"].get("terms") or {}).get("unit_price"):
            continue
        p0, p1 = last["unit_price"], rep["move"]["terms"]["unit_price"]
        same = all(rep["move"]["terms"].get(k) == last.get(k) for k in rep["move"]["terms"] if k != "unit_price")
        if not same or nb == 1:
            continue
        ver = sum(r.get("result") == "verified" for r in rep["move"].get("claim_results") or [])
        promise = any(("pay" in r.lower() and ("promise" in r.lower() or "on time" in r.lower())) for r in rep.get("reasons") or [])
        rows[(min(nb, 5), min(ver, 2), promise)].append(round(p0 - p1, 2))
for k in sorted(rows):
    xs = rows[k]
    print("our msg %s  facts %s  promise-credited %-5s n=%-3d mean cut %.3f  cuts %s" % (k[0] if k[0] < 5 else "5+", k[1], k[2], len(xs), statistics.mean(xs), sorted(collections.Counter(xs).items())))
