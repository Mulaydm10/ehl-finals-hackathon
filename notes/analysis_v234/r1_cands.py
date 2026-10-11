"""Round-1 candidate sheets per case with our cost C (gap vs best in %) and the supplier's standard terms: are terms near-ties?"""
import json, sys, logging, glob
from pathlib import Path
ROOT = Path.home() / "Dhruv/ehl-finals-hackathon"
sys.path.insert(0, str(ROOT / "tacto/starter-kit"))
logging.disable(logging.CRITICAL)
from arena_kit.agents.noidea_rfq import NoIdeaAgent
cases = {c["case_id"]: c for c in json.loads((ROOT / "datasets/cases_practice.json").read_text())}
want = ["case:" + x for x in sys.argv[1:]]
for cid in want:
    case = cases[cid]
    g = max((json.loads(Path(f).read_text()) for f in glob.glob(str(ROOT / "datasets/runs/*.json"))
             if json.loads(Path(f).read_text()).get("session", {}).get("case_id") == cid), key=lambda g: g["session"].get("created_at") or 0)
    threads = {sid: th["messages"][:1] for sid, th in g["threads"].items()}
    a = NoIdeaAgent(); a.prepare(case, threads)
    sid = next(iter(a.sup)); s = a.sup[sid]
    target = a.value_target(case, sid, threads[sid])
    c8 = a.sheets_at(case, sid, target, None, n=8)
    best = c8[0][0]
    print(f"=== {cid} std {s['std']}  target value {target:.3f}")
    for C, t in c8:
        print("   C %+.3f%%  %s" % ((C - best) / best * 100, {k: t.get(k) for k in case['negotiable']}))
