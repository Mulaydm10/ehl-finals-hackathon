"""Offline branch checks of noidea_p10r.py against its scripted twin P10_R.json (no arena, no LLM: complete=None).

    cd tacto/starter-kit && uv run python ../../analysis/tools/p10_r_check.py

Feeds the archived 59c899b9 game (tools/replays/raw) to the agent:
- turns 1-2 must equal what was sent live, byte for byte (body, sheet, refs);
- turn 3, after its final 31.10, must equal P10_R round 3.
Then plays each possible answer to turn 3 and prints the agent's move:
agreed 30.69 / final 31.10 again / open 31.00 / walked. Also: a final above the 2% line (31.40) and a final at message 1.
"""
import copy
import importlib.util
import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "tacto" / "starter-kit")]
ERRORS = []  # any "decide failed - safe move instead" (main's crash guard) fails the check


class _Catch(logging.Handler):
    def emit(self, record):
        if record.levelno >= logging.ERROR:
            ERRORS.append(record.getMessage())


logging.getLogger("arena").addHandler(_Catch())
logging.getLogger("arena").propagate = False
from arena_kit.cost import total_cost  # noqa: E402

CASE = next(c for c in json.loads((ROOT / "datasets/cases_practice.json").read_text(encoding="utf-8")) if c["case_id"] == "case:P10")
STD = {"ppm_commitment": 300, "chargeback_eur_per_complaint": 0.0}
C_OPEN, C_BEST = 1932492.18, 1328926.89
spec = importlib.util.spec_from_file_location("arena_kit.agents._p10r", ROOT / "analysis/agent_variants/noidea_p10r.py")
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)
DESIGN = json.loads((ROOT / "analysis/experiments/probes/P10_R.json").read_text(encoding="utf-8"))
RAW = json.loads((ROOT / "tools/replays/raw/P10_59c899b93ba24dec.json").read_text(encoding="utf-8"))
SID = "sup:70410"
LIVE = RAW["thread_messages"][SID]["messages"]
NEG = CASE["negotiable"]


def score(t):
    c = total_cost(CASE, {f: t[f] for f in NEG}, STD)
    return (C_OPEN - c) / (C_OPEN - C_BEST)


def reply(status, price, n, months=36):
    terms = {"unit_price": price, "lead_time_days": 56, "volume_per_year": 23400, "contract_months": months}
    return {"from": "sales@70410", "status": status, "body": "Dear Sir or Madam,\n...",
            "term_sheets": [] if status == "walked_away" else [{"term_sheet_id": f"offer:70410-{n}", "terms": terms}]}


def decide(thread):
    return mod.NoIdeaAgent(None).decide(CASE, {SID: copy.deepcopy(thread)})


ok = True
buyer = [m for m in LIVE if m["from"] == "buyer" and m.get("term_sheets")]
for k in (1, 2):
    i = LIVE.index(buyer[k - 1])
    m = decide(LIVE[:i])["message"]
    same = (m.get("body") == buyer[k - 1]["body"], [t["terms"] for t in m["term_sheets"]] ==
            [{f: t["terms"][f] for f in NEG} for t in buyer[k - 1]["term_sheets"]], sorted(m["refs"]) == sorted(buyer[k - 1]["refs"]),
            m.get("body") == DESIGN["rounds"][k - 1]["body"])
    ok &= all(same)
    print(f"turn {k}: body = live {same[0]}, sheet = live {same[1]}, refs = live {same[2]}, body = P10_R round {k} {same[3]}")

thread = LIVE[:LIVE.index(buyer[1]) + 2]  # through its final 31.10 (live)
fin = thread[-1]
print(f"its final (live): {fin['status']} {fin['term_sheets'][0]['terms']['unit_price']}")
d3 = decide(thread)["message"]
t3 = d3["term_sheets"][0]["terms"]
same3 = (d3["body"] == DESIGN["rounds"][2]["body"], t3 == DESIGN["rounds"][2]["sheets"][0])
ok &= all(same3) and t3["unit_price"] == 30.69
print(f"turn 3: ask {t3['unit_price']} ({score(t3):.6f} if agreed) {t3}; body = P10_R round 3 {same3[0]}; sheet = P10_R {same3[1]}")
print("  " + d3["body"].replace("\n", "\n  "))

after = thread + [{"from": "buyer", "subject": d3["subject"], "body": d3["body"], "term_sheets": d3["term_sheets"], "refs": []}]
for label, r, want in (("agreed at 30.69", reply("agreed", 30.69, 3), "accept"),
                       ("final 31.10 again (hold)", reply("final_offer", 31.10, 3), "accept"),
                       ("open, counter 31.00", reply("open", 31.00, 3), "accept")):
    d = decide(after + [r])["message"]
    act = (d.get("action") or {}).get("type")
    ok &= act == want
    print(f"after turn 3, {label}: agent -> {act} {d.get('action', {}).get('term_sheet_id', '')}  "
          f"(score {score(r['term_sheets'][0]['terms']):.6f})")
print("after turn 3, walked away: the thread has ended; the runner stops (0 for this game)")

high = LIVE[:LIVE.index(buyer[1]) + 1] + [reply("final_offer", 31.40, 2)]
d = decide(high)["message"]
act = (d.get("action") or {}).get("type")
ok &= act == "accept"
print(f"final 31.40 at message 2 (30.69 would be 2.3% under it): agent -> {act} (no push)")

early = LIVE[:LIVE.index(buyer[0]) + 1] + [reply("final_offer", 31.50, 1, months=24)]
d = decide(early)["message"]
act = (d.get("action") or {}).get("type")
ok &= act == "accept"
print(f"final at message 1 (31.50): agent -> {act}")
tmpl = LIVE[:LIVE.index(buyer[0]) + 1] + [{**reply("open", 31.00, 1, months=24), "body": "Dear Sir or Madam,\n\nWe value "
        "our cooperation and have made a step towards you. Any further step needs approval from our management."}]
d = decide(tmpl)["message"]
act = (d.get("action") or {}).get("type")
ok &= act == "accept"
print(f"engine-template reply at message 1 (31.00, the arena's model off): agent -> {act} (no move on that window)")
print(f"agent errors (crash guard fired): {len(ERRORS)} {ERRORS[:3]}")
ok &= not ERRORS
print("ALL CHECKS PASS" if ok else "CHECK FAILED")
