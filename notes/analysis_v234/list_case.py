"""list archived games of one case, oldest first: python3 list_case.py P11 [last_n]"""
import json, sys, glob, datetime
case = "case:" + sys.argv[1]
n = int(sys.argv[2]) if len(sys.argv) > 2 else 30
rows = []
for f in glob.glob("datasets/runs/*.json"):
    g = json.load(open(f))
    s = g.get("session") or {}
    if s.get("case_id") != case:
        continue
    r = ((g.get("detail") or {}).get("result") or {})
    th = next(iter(g["threads"].values())) if g.get("threads") else {}
    ms = th.get("messages") or []
    sup = [m for m in ms if m.get("from") != "buyer" and (m.get("term_sheets") or [])]
    first = (sup[1]["term_sheets"][0].get("terms") or {}).get("unit_price") if len(sup) > 1 else None
    b1 = next((m for m in ms if m.get("from") == "buyer"), {})
    nsh = len(b1.get("term_sheets") or [])
    rows.append((s.get("created_at") or 0, f.split("/")[-1][:-5], r.get("score"), first, len(ms), nsh, len(g.get("threads") or {})))
rows.sort()
for c, sid_, sc, first, nm, nsh, nth in rows[-n:]:
    t = datetime.datetime.fromtimestamp(c).strftime("%m-%d %H:%M") if c else "?"
    print(t, sid_, "score", "-" if sc is None else "%.4f" % sc, "first_counter", first, "msgs", nm, "r1_sheets", nsh, "threads", nth)
