"""P11 round 1: its counter on OUR main structure (300/0 when we asked it) vs (a) our first e-mail labelling the gap between its
quoted ppm and its record, (b) the reply crediting our payment promise. All archived games."""
import json, re, collections
from pathlib import Path
ROOT = Path.home() / "Dhruv/ehl-finals-hackathon"
LABEL = re.compile(r"(?i)more defects than|than your (own )?record|recorded performance|your (own )?record (shows|of)|"
                   r"(quote|offer|proposal)[^.]{0,60}(looser|weaker|above|more than)[^.]{0,40}(record|performance|actual)")
PROMISE = re.compile(r"(?i)promise to pay|pay(ing)? on time|straight about the late|payment promise")
tab = collections.defaultdict(list)
for f in sorted((ROOT / "datasets/runs").glob("*.json")):
    g = json.loads(f.read_text())
    if (g.get("session") or {}).get("case_id") != "case:P11" or len(g.get("threads") or {}) != 1:
        continue
    tr = ((g.get("detail") or {}).get("result") or {}).get("trace") or []
    for i, t in enumerate(tr):
        mv = t["move"]
        if t["actor"] == "buyer" and mv.get("type") == "message" and mv.get("term_sheets"):
            rep = next((x for x in tr[i + 1:] if x["actor"] != "buyer"), None)
            if not rep:
                break
            sh = [rep["move"].get("terms") or {}] + [a.get("terms") or {} for a in rep["move"].get("alternatives") or []]
            p300 = next((s.get("unit_price") for s in sh if s.get("ppm_commitment") == 300 and not s.get("chargeback_eur_per_complaint")), None)
            lab = bool(LABEL.search(mv.get("body") or ""))
            pro = any(PROMISE.search(r) for r in rep.get("reasons") or [])
            tab[(lab, pro)].append((p300, f.stem[:8]))
            break
for (lab, pro), xs in sorted(tab.items()):
    c = collections.Counter(p for p, _ in xs)
    print(f"label-in-our-e-mail={lab!s:5}  reply-credits-promise={pro!s:5}  n={len(xs):2d}  its 300/0 counter: {dict(sorted(c.items(), key=lambda kv: (kv[0] is None, kv[0] or 0)))}")
