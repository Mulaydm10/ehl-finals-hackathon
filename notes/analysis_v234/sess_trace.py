"""Print a session's trace from the arena (any set, incl. sandbox): python sess_trace.py <session_id>"""
import json, sys
from arena_kit import ArenaClient
c = ArenaClient()
s = c.session(sys.argv[1])
r = s.get("result") or {}
print("score", r.get("score"), "deal", r.get("deal"), "supplier", r.get("supplier_id"), "terms", r.get("terms"))
print("c_open", r.get("c_open"), "c_best", r.get("c_best"), "c_deal", r.get("c_deal"), "c_alt", r.get("c_alt"))
for t in r.get("trace") or []:
    mv = t["move"]
    if t["actor"] == "buyer":
        print("B r%d %-8s -> %s %s refs=%s" % (t["round"], mv.get("type"), mv.get("supplier_id"),
              [x["terms"] for x in mv.get("term_sheets") or []], len(mv.get("refs") or [])))
    else:
        alts = [a.get("terms") for a in mv.get("alternatives") or []]
        print("S r%d %s %-11s %s alts=%s | %s" % (t["round"], t["actor"], mv.get("status"), mv.get("terms"), alts,
              " / ".join(t.get("reasons") or [])[:260]))
