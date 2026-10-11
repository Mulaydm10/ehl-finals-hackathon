"""The agent's ranked argument list for one case (kind, ids, figure, weight, late/filler/weak): python args_dump.py P11"""
import json, sys, logging
from pathlib import Path
ROOT = Path.home() / "Dhruv/ehl-finals-hackathon"
sys.path.insert(0, str(ROOT / "tacto/starter-kit"))
logging.disable(logging.CRITICAL)
from arena_kit.agents.noidea_rfq import NoIdeaAgent
cid = "case:" + sys.argv[1]
case = next(c for c in json.loads((ROOT / "datasets/cases_practice.json").read_text()) if c["case_id"] == cid)
import glob
g = max((json.loads(Path(f).read_text()) for f in glob.glob(str(ROOT / "datasets/runs/*.json"))
         if json.loads(Path(f).read_text()).get("session", {}).get("case_id") == cid), key=lambda g: g["session"].get("created_at") or 0)
threads = {sid: th["messages"][:1] for sid, th in g["threads"].items()}
a = NoIdeaAgent()
a.prepare(case, threads)
for sid in a.sup:
    print(sid, "r1_facts", a.r1_facts(case, sid), "patience", a.sup[sid]["patience"])
    for c in a.sup[sid]["args"]:
        print("  %-20s %-45s fig=%-7s w=%-6s late=%s filler=%s weak=%s" % (c["kind"], ",".join(c["ids"])[:45], c.get("figure"),
              c.get("weight"), c.get("late", False), c.get("filler", False), a.weak(c)))
