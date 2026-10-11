"""Replay a team-best game through OUR agent (the one the final runs): per round its move, ours on the same state. (no quota)"""
import json, sys, logging
from pathlib import Path
ROOT = Path.home() / "Dhruv/ehl-finals-hackathon"
sys.path.insert(0, str(ROOT / "tacto/starter-kit"))
logging.basicConfig(level=logging.INFO, format="   log: %(message)s")
for n in ("httpx", "openai", "httpcore"):
    logging.getLogger(n).setLevel(logging.WARNING)
from arena_kit.agents.noidea_rfq import NoIdeaAgent
cid, sess = sys.argv[1], sys.argv[2]
case = next(c for c in json.loads((ROOT / "datasets/cases_practice.json").read_text()) if c["case_id"] == cid)
f = ROOT / f"datasets/runs/{sess}.json"
if not f.exists():
    f = next((ROOT / "tools/replays/raw").glob(f"*{sess}*.json"))
g = json.loads(f.read_text()); sid, th = next(iter(g["threads"].items())); ms = th["messages"]
res = (g.get("detail") or {}).get("result") or {}
neg = case["negotiable"]
print("=====", cid, sess, round(res.get("score") or 0, 3))
a = NoIdeaAgent(lambda s_, u: json.dumps({"sheets": [0], "args": [], "opening": "x", "notes": {}}))
for n in range(1, len(ms)):
    m = ms[n - 1]
    if m.get("from") == "buyer" or m.get("status") in ("agreed",):
        continue
    if m.get("status") == "final_offer":
        print(f"  its FINAL {[{k: x['terms'].get(k) for k in neg} for x in (m.get('term_sheets') or [])][:1]}"); break
    d = a.decide(case, {sid: ms[:n]})["message"]; a.cited |= set(d.get("refs") or [])
    theirs = [{k: x["terms"].get(k) for k in neg} for x in (m.get("term_sheets") or [])][:1]
    real = ms[n] if n < len(ms) and ms[n].get("from") == "buyer" else {}
    real_s = [{k: x["terms"].get(k) for k in neg} for x in (real.get("term_sheets") or [])][:1] or (real.get("action") or {}).get("type")
    ours = (d.get("action") or {}).get("type") or [{k: x["terms"].get(k) for k in neg} for x in d["term_sheets"]][:1]
    print(f"  it: {theirs}\n     WINNER sent: {real_s} refs {len(real.get('refs') or [])}\n     OURS sends : {ours} refs {len(d.get('refs') or [])} {(d.get('refs') or [])[:4]}")
