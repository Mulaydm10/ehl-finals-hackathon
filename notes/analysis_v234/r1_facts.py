"""Round 1: does a heavier first e-mail buy a lower first counter? Per case and per structure of our primary sheet:
the supplier's first counter ON THAT STRUCTURE (primary or alternative), grouped by the verified claims our first
e-mail carried. Also: the final score by that count."""
import json, collections, statistics
from pathlib import Path
ROOT = Path.home() / "Dhruv/ehl-finals-hackathon"
data = collections.defaultdict(lambda: collections.defaultdict(list))   # case -> (struct, n) -> [(counter, score, sess)]
for f in sorted((ROOT / "datasets/runs").glob("*.json")):
    try:
        g = json.loads(f.read_text())
    except Exception:
        continue
    res = (g.get("detail") or {}).get("result") or {}
    cid = (g.get("session") or {}).get("case_id")
    tr = res.get("trace") or []
    if not cid or not tr or len(g.get("threads") or {}) != 1:
        continue
    b1 = None
    for i, t in enumerate(tr):
        mv = t["move"]
        if t["actor"] == "buyer" and mv.get("type") == "message" and mv.get("term_sheets"):
            b1 = (i, mv)
            break
    if not b1:
        continue
    i, mv = b1
    ours = mv["term_sheets"][0]["terms"]
    key = tuple(sorted((k, json.dumps(v, sort_keys=True)) for k, v in ours.items() if k != "unit_price"))
    nclaims = len((mv.get("interpreted") or {}).get("claims") or [])
    nsheets = len(mv["term_sheets"])
    rep = next((t for t in tr[i + 1:] if t["actor"] != "buyer"), None)
    if not rep:
        continue
    ver = sum(r.get("result") == "verified" for r in rep["move"].get("claim_results") or [])
    sheets = [rep["move"].get("terms") or {}] + [a.get("terms") or {} for a in rep["move"].get("alternatives") or []]
    match = None
    for s in sheets:
        def eq(a, b):
            b = json.loads(b)
            return a == b or (isinstance(a, (int, float)) and isinstance(b, (int, float)) and abs(a - b) < 1e-6)
        if all(eq(s.get(k), v) for k, v in key):
            match = s.get("unit_price")
            break
    data[cid][(key, ver, nsheets)].append((match, res.get("score"), f.stem[:8]))
for cid in sorted(data):
    print(f"\n=== {cid}")
    for (key, ver, ns), xs in sorted(data[cid].items(), key=lambda kv: (str(kv[0][0]), kv[0][1], kv[0][2])):
        cs = [x[0] for x in xs if x[0] is not None]
        sc = [x[1] for x in xs if x[1] is not None]
        k = ",".join(f"{a}={b}" for a, b in key)[:70]
        print(f"  [{k}] verified={ver} sheets={ns}: n={len(xs)} counter_on_ours mean={statistics.mean(cs) if cs else None} "
              f"min={min(cs) if cs else None} score mean={statistics.mean(sc):.3f} max={max(sc):.3f}" if sc else
              f"  [{k}] verified={ver} sheets={ns}: n={len(xs)} counter={cs}")
