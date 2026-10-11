"""Does our WORDING move the first counter? Per case: games whose round-1 e-mail had the SAME sheets and refs (only the text
differs) -> the first counter on our main structure, with the opening paragraph (the model's part). python3 wording.py P07"""
import json, sys, collections, re
from pathlib import Path
ROOT = Path.home() / "Dhruv/ehl-finals-hackathon"
want = set(sys.argv[1:])
groups = collections.defaultdict(list)
for f in sorted((ROOT / "datasets/runs").glob("*.json")):
    g = json.loads(f.read_text())
    cid = (g.get("session") or {}).get("case_id") or ""
    if want and cid.split(":")[-1] not in want or len(g.get("threads") or {}) != 1:
        continue
    tr = ((g.get("detail") or {}).get("result") or {}).get("trace") or []
    for i, t in enumerate(tr):
        mv = t["move"]
        if t["actor"] == "buyer" and mv.get("type") == "message" and mv.get("term_sheets"):
            rep = next((x for x in tr[i + 1:] if x["actor"] != "buyer"), None)
            if not rep:
                break
            ours = mv["term_sheets"][0]["terms"]
            key = (cid, json.dumps([ts["terms"] for ts in mv["term_sheets"]], sort_keys=True), tuple(sorted(mv.get("refs") or [])))
            sh = [rep["move"].get("terms") or {}] + [a.get("terms") or {} for a in rep["move"].get("alternatives") or []]
            same = [s.get("unit_price") for s in sh if all(s.get(k) == v for k, v in ours.items() if k != "unit_price")]
            body = mv.get("body") or ""
            para = body.split("\n\n")[1] if body.count("\n\n") >= 2 else ""
            groups[key].append((same[0] if same else None, (g.get("detail") or {}).get("result", {}).get("score"), f.stem[:8], para))
            break
for key, xs in groups.items():
    vals = [x[0] for x in xs if x[0] is not None]
    if len(xs) < 3 or len(set(vals)) < 2:
        continue
    print(f"\n=== {key[0]} n={len(xs)} same sheets+refs; first counters {sorted(collections.Counter(vals).items())}")
    for c, sc, s, para in sorted(xs, key=lambda x: (x[0] is None, x[0] or 0)):
        print(f"  {c} score {sc:.3f} {s} | {para[:330]}")
