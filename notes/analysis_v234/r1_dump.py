"""Round-1 (and optional round-2) dump of the agent on every hosted case, no LLM, no quota: the real opening of the latest
archived game per case -> decide() -> sheets, refs, code lines. Diff two dumps to see which cases a change touches.
    cd tacto/starter-kit && .venv/bin/python /tmp/r1_dump.py [--r2] > /tmp/r1_before.txt"""
import json, sys, glob, logging, re
from pathlib import Path
ROOT = Path.home() / "Dhruv/ehl-finals-hackathon"
sys.path.insert(0, str(ROOT / "tacto/starter-kit"))
logging.disable(logging.CRITICAL)
from arena_kit.agents.noidea_rfq import NoIdeaAgent  # the final's agent
cases = {c["case_id"]: c for c in json.loads((ROOT / "datasets/cases_practice.json").read_text())}
latest = {}
for f in glob.glob(str(ROOT / "datasets/runs/*.json")):
    g = json.loads(Path(f).read_text())
    cid = (g.get("session") or {}).get("case_id")
    if cid in cases and cases[cid].get("hosted"):
        t = (g.get("session") or {}).get("created_at") or 0
        if cid not in latest or t > latest[cid][0]:
            latest[cid] = (t, g)
r2 = "--r2" in sys.argv
for cid in sorted(latest):
    g = latest[cid][1]
    case = cases[cid]
    threads = {sid: [m for m in th["messages"][:1]] for sid, th in g["threads"].items()}
    a = NoIdeaAgent()
    try:
        d = a.decide(case, threads)
    except Exception as e:
        print(f"=== {cid}: ERROR {e!r}")
        continue
    m = d.get("message") or {}
    print(f"=== {cid} -> {d.get('supplier_id')}")
    print("  sheets:", [{k: v for k, v in ts["terms"].items() if k in case["negotiable"]} for ts in m.get("term_sheets") or []])
    print("  refs  :", m.get("refs"))
    print("  attach:", [x.get("name") for x in m.get("attachments") or []])
    body = m.get("body") or ""
    for s in re.split(r"(?<=[.!?])\s+", body):
        if s.strip():
            print("   |", s.strip()[:160])
    if r2:
        # round 2: its real 2nd message from the same archived game, if any (prices are then that game's, not ours)
        sid = d.get("supplier_id")
        msgs = g["threads"].get(sid, {}).get("messages") or []
        sup2 = [x for x in msgs[1:] if x.get("from") != "buyer"]
        if sup2:
            ev = [msgs[0], {"from": "buyer", "body": body, "term_sheets": m.get("term_sheets"), "refs": m.get("refs")}, sup2[0]]
            d2 = a.decide(case, {**threads, sid: ev})
            m2 = d2.get("message") or {}
            print("  R2 sheets:", [{k: v for k, v in ts["terms"].items() if k in case["negotiable"]} for ts in m2.get("term_sheets") or []],
                  "refs", m2.get("refs"), "action", (m2.get("action") or {}).get("type"))
            for s in re.split(r"(?<=[.!?])\s+", m2.get("body") or ""):
                if s.strip():
                    print("   2|", s.strip()[:160])
