"""print one archived game: every message, its sheets, its claim ids, its body. usage: python3 show_game.py <sid> [maxbody]"""
import json, sys, textwrap
sid_ = sys.argv[1]
mx = int(sys.argv[2]) if len(sys.argv) > 2 else 900
g = json.load(open(f"datasets/runs/{sid_}.json"))
r = ((g.get("detail") or {}).get("result") or {})
print("case", (g.get("session") or {}).get("case_id"), "score", r.get("score"))
for sup, th in g["threads"].items():
    print("=== thread", sup)
    for i, m in enumerate(th.get("messages") or []):
        sheets = []
        for s in m.get("term_sheets") or []:
            t = s.get("terms") or {}
            sheets.append((s.get("id"), t.get("unit_price"), t.get("ppm_commitment"), t.get("chargeback_eur_per_complaint"), t.get("payment_days")))
        claims = m.get("claims") or []
        refs = [c.get("data_id") or c.get("ref") or c.get("id") for c in claims] if claims else (m.get("refs") or m.get("data_refs"))
        print("--- %d %s status=%s sheets=%s refs=%s" % (i, m.get("from"), m.get("status"), sheets, refs))
        print(textwrap.indent(textwrap.fill((m.get("body") or "")[:mx], 150), "    "))
