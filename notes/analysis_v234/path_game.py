"""compact price path of archived games: python3 path_game.py <sid> [<sid> ...]  (refs + first sheet per message)"""
import json, re, sys
for sid_ in sys.argv[1:]:
    g = json.load(open(f"datasets/runs/{sid_}.json"))
    r = ((g.get("detail") or {}).get("result") or {})
    print("##", sid_, (g.get("session") or {}).get("case_id"), "score", None if r.get("score") is None else round(r["score"], 4))
    for sup, th in g["threads"].items():
        for i, m in enumerate(th.get("messages") or []):
            sh = m.get("term_sheets") or []
            ts = []
            for s in sh:
                t = s.get("terms") or {}
                ts.append("%s@%s/%s" % (t.get("unit_price"), t.get("ppm_commitment"), t.get("chargeback_eur_per_complaint")))
            body = m.get("body") or ""
            ids = sorted(set(re.findall(r"\b(?:idx|sc|fc|q|inv|hist|ph|ord|news|rq|cd)[:][A-Za-z0-9_.@-]+", body)))
            tag = "B" if m.get("from") == "buyer" else "S"
            print("  %2d %s %-12s %-40s %s" % (i, tag, m.get("status") or "", " | ".join(ts), " ".join(ids)))
