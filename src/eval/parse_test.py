"""Parser + learner on the 78 real supplier e-mails (datasets/F_supplier_emails.jsonl)."""
import json, logging, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tacto/starter-kit"))
logging.basicConfig(level=logging.WARNING)
from arena_kit.agents.noidea import NoIdeaAgent
cs = {c["case_id"]: c for c in json.loads((ROOT / "datasets/cases_practice.json").read_text())}
a = NoIdeaAgent(None)
rows = [json.loads(l) for l in (ROOT / "datasets/F_supplier_emails.jsonl").read_text().splitlines() if l]
ok = bad = 0
for r in rows:
    if not r["standing"]:
        continue
    pk = a.parse_packages(cs[r["case"]], r["body"])
    prim = [p for p in pk if not p["alternative"]]
    sp = r["standing"].get("unit_price")
    hit = any(abs(p["unit_price"] - sp) < 0.005 for p in pk)
    ok += hit; bad += not hit
    if not hit:
        print("MISS", r["case"], r["status"], sp, [p["unit_price"] for p in pk], r["body"][:160].replace("\n", " "))
print(f"standing price found in parsed packages: {ok}/{ok + bad}")
# learner on the real P10 final e-mail
p10 = [r for r in rows if r["case"] == "case:P10" and r["status"] == "final_offer"]
for r in p10:
    pk = a.parse_packages(cs["case:P10"], r["body"])
    print("P10 packages:", [{k: v for k, v in p.items()} for p in pk])
    a.sup = {"sup:70410": {"open_terms": {}, "k": {}}}
    a.learn(cs["case:P10"], "sup:70410", [{"from": "s", "body": r["body"]}])
    print("   learned k:", a.sup["sup:70410"]["k"])
