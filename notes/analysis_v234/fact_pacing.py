"""Is a fact worth more in round 1 or later? Per case, from every archived trace (no quota).
For each supplier reply to one of our priced messages: how many verified claims that message carried, and how far the
supplier's price moved (% of its previous price, primary sheet, same-structure only). Round 1 vs later rounds."""
import json, collections, statistics
from pathlib import Path
ROOT = Path.home() / "Dhruv/ehl-finals-hackathon"
rows = collections.defaultdict(list)   # (case, phase, n_verified) -> [cut %]
lotmat = collections.Counter()
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
    last_sup, nbuy = None, 0
    pending = None
    for t in tr:
        mv = t["move"]
        if t["actor"] == "buyer":
            if mv.get("type") == "message" and mv.get("term_sheets"):
                nbuy += 1
                pending = (nbuy, len((mv.get("interpreted") or {}).get("claims") or []))
            continue
        p = (mv.get("terms") or {}).get("unit_price")
        if pending and last_sup and p and last_sup.get("unit_price"):
            same = all(mv["terms"].get(k) == last_sup.get(k) for k in mv["terms"] if k != "unit_price")
            ver = sum(r.get("result") == "verified" for r in mv.get("claim_results") or [])
            if same:
                cut = 100 * (last_sup["unit_price"] - p) / last_sup["unit_price"]
                phase = "r1" if pending[0] == 1 else "later"
                rows[(cid, phase, min(ver, 3))].append(cut)
            if any("lot of material" in r for r in t.get("reasons") or []):
                lotmat[(cid, pending[1])] += 1
            pending = None
        if p:
            last_sup = mv.get("terms")
cases = sorted({c for c, _, _ in rows})
for c in cases:
    print(f"\n{c}")
    for ph in ("r1", "later"):
        line = []
        for n in range(4):
            xs = rows.get((c, ph, n))
            if xs:
                line.append(f"{n} facts: {statistics.mean(xs):5.2f}% (n={len(xs)})")
        print(f"  {ph:5s} " + " | ".join(line))
print("\n'lot of material' replies by (case, claims in our msg):", dict(lotmat))
