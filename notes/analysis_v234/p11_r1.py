"""P11 every game: round-1 claims (verified) / sheets / its counter for 300/0 (any of its sheets) / its primary / score."""
import json, sys
from pathlib import Path
ROOT = Path.home() / "Dhruv/ehl-finals-hackathon"
case = "case:" + (sys.argv[1] if len(sys.argv) > 1 else "P11")
rows = []
for f in sorted((ROOT / "datasets/runs").glob("*.json")):
    g = json.loads(f.read_text())
    if (g.get("session") or {}).get("case_id") != case or len(g.get("threads") or {}) != 1:
        continue
    res = (g.get("detail") or {}).get("result") or {}
    tr = res.get("trace") or []
    for i, t in enumerate(tr):
        mv = t["move"]
        if t["actor"] == "buyer" and mv.get("type") == "message" and mv.get("term_sheets"):
            rep = next((x for x in tr[i + 1:] if x["actor"] != "buyer"), None)
            if not rep:
                break
            sheets = [rep["move"].get("terms") or {}] + [a.get("terms") or {} for a in rep["move"].get("alternatives") or []]
            ours = [(s["terms"].get("ppm_commitment"), s["terms"].get("chargeback_eur_per_complaint"), s["terms"].get("unit_price")) for s in mv["term_sheets"]]
            cl = [c.get("type") for c in (mv.get("interpreted") or {}).get("claims") or []]
            ver = [r.get("result") for r in rep["move"].get("claim_results") or []]
            its = [(s.get("ppm_commitment"), s.get("chargeback_eur_per_complaint"), s.get("unit_price")) for s in sheets]
            p300 = next((s.get("unit_price") for s in sheets if s.get("ppm_commitment") == 300 and not s.get("chargeback_eur_per_complaint")), None)
            rows.append(((g.get("session") or {}).get("created_at") or 0, f.stem[:8], res.get("score"), ours, cl, ver, its, p300,
                         bool((mv.get("attachments") or [])), len(mv.get("body") or "")))
            break
rows.sort()
for r in rows:
    print(r[1], "%.3f" % (r[2] or 0), "ours", r[3], "claims", r[4], "ver", r[5], "its", r[6], "300/0:", r[7], "att", r[8], "len", r[9])
