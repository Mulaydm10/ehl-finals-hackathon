"""Side by side: two archived games of a case, every move with sheets (negotiable terms), refs and its reasons.
python3 cmp2.py <sid> [<sid> ...]"""
import json, sys
from pathlib import Path
ROOT = Path.home() / "Dhruv/ehl-finals-hackathon"
cases = {c["case_id"]: c for c in json.loads((ROOT / "datasets/cases_practice.json").read_text())}
def short(t, neg):
    out = []
    for k in neg:
        v = t.get(k)
        if k == "index_clause":
            v = None if not v else f"db{v.get('deadband_pct')}"
        out.append(str(v))
    return "/".join(out)
for s in sys.argv[1:]:
    g = json.loads((ROOT / f"datasets/runs/{s}.json").read_text())
    cid = g["session"]["case_id"]; neg = cases[cid]["negotiable"]
    tr = g["detail"]["result"]["trace"]
    print(f"===== {s} {cid} score {g['detail']['result']['score']:.3f}  ({'/'.join(neg)})")
    for t in tr:
        mv = t["move"]
        if t["actor"] == "buyer":
            if mv.get("type") == "message":
                print(f"  B r{t['round']} {[short(x['terms'], neg) for x in mv.get('term_sheets') or []]} refs={len(mv.get('refs') or [])} {sorted({r.split('@')[0] for r in mv.get('refs') or []})}")
            else:
                print(f"  B r{t['round']} {mv.get('type')}")
        else:
            sh = [mv.get("terms") or {}] + [a.get("terms") or {} for a in mv.get("alternatives") or []]
            print(f"  S r{t['round']} {mv.get('status') or '':11s} {[short(x, neg) for x in sh if x]} | {' / '.join(t.get('reasons') or [])[:230]}")
