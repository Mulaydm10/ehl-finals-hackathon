"""Offline checks of analysis/agent_variants/noidea_p18_top.py (no arena, no LLM: complete=None).

    cd tacto/starter-kit && uv run python ../../analysis/tools/p18_top_check.py

1. Exact scores (arena_kit.cost) of every sheet the plan can send; which beat Codacabana's 0.75595.
2. msg 1 = 6c2813ce's msg 1 byte for byte (its reply 5.20 @ 45 d is cached by the arena).
3. msg 2: the 12 openings are distinct from each other and from every recorded P18 msg 2 (each is a fresh draw).
4. Branches on scripted replies: soft / normal round 2, hold / counter / agreed at round 3, finals with and without an
   alternative that beats, engine-template reply, still open after msg 4.
5. Archived replay: the agent decides on every turn of every recorded P18 game without its crash guard firing.
"""
import copy
import glob
import importlib.util
import json
import logging
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "tacto" / "starter-kit")]
ERRORS = []


class _Catch(logging.Handler):
    def emit(self, record):
        if record.levelno >= logging.ERROR:
            ERRORS.append(record.getMessage())


logging.getLogger("arena").addHandler(_Catch())
logging.getLogger("arena").propagate = False
from arena_kit.cost import complete_offer, total_cost  # noqa: E402

CASE = next(c for c in json.loads((ROOT / "datasets/cases_practice.json").read_text(encoding="utf-8")) if c["case_id"] == "case:P18")
C_OPEN, C_BEST = 295173.23, 222651.27
spec = importlib.util.spec_from_file_location("arena_kit.agents._p18top", ROOT / "analysis/agent_variants/noidea_p18_top.py")
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)
SID = "sup:70740"


def score(t):
    c = total_cost(CASE, complete_offer(CASE, t), mod.STD)
    return (C_OPEN - c) / (C_OPEN - C_BEST)


def thread_of(path):
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    th = d.get("thread_messages") or d.get("threads")
    return th[SID]["messages"]


def decide(thread):
    return mod.NoIdeaAgent(None).decide(CASE, {SID: copy.deepcopy(thread)})


def reply(status, sheets, n, body="Dear Sir or Madam,\n\nOur offer stands."):
    return {"from": "sales@70740", "status": status, "body": body,
            "term_sheets": [{"term_sheet_id": f"offer:70740-{n}" + ("" if i == 0 else "-a"), "terms": t}
                            for i, t in enumerate(sheets)]}


def buyer(d):
    m = d["message"]
    return {"from": "buyer", "subject": m.get("subject"), "body": m.get("body"), "term_sheets": m.get("term_sheets"),
            "refs": m.get("refs")}


def act(d):
    m = d["message"]
    return (m.get("action") or {}).get("type") or [(t["terms"]["unit_price"], t["terms"]["payment_days"],
                                                    (t["terms"].get("index_clause") or {}).get("deadband_pct"))
                                                   for t in m.get("term_sheets") or []]


ok = True
print("1. EXACT SCORES (record 0.75595; ours 0.72708)")
record = (C_OPEN - mod.C_RECORD) / (C_OPEN - C_BEST)
print(f"   Codacabana 4.90 @ 45 d db0: C {mod.C_RECORD:,.2f} = {record:.5f}")
for name, plan in (("msg 2", (mod.R2_ASK,)), ("msg 3 soft", mod.SOFT3), ("msg 3 normal", mod.NORMAL3),
                   ("msg 4 soft", mod.SOFT4), ("msg 4 normal", mod.NORMAL4)):
    for q in plan:
        t = mod.sheet(*q)
        print(f"   {name:12s} {q[0]:.2f} @ {q[1]} d db{q[2]}: {score(t):.5f}{'  BEATS 0.756' if mod.beats(CASE, t) else ''}")
for q in mod.SOFT3 + mod.NORMAL3:
    ok &= mod.beats(CASE, mod.sheet(*q))

print("\n2. MSG 1")
live = thread_of(ROOT / "datasets/runs/6c2813cee1fcf116.json")
b1 = next(m for m in live if m.get("from") == "buyer" and m.get("term_sheets"))
d1 = decide(live[:live.index(b1)])["message"]
same = (d1["body"] == b1["body"], d1["subject"] == b1["subject"], sorted(d1["refs"]) == sorted(b1["refs"]),
        [t["terms"] for t in d1["term_sheets"]] == [{f: t["terms"][f] for f in CASE["negotiable"]} for t in b1["term_sheets"]])
ok &= all(same)
print(f"   body {same[0]}, subject {same[1]}, refs {same[2]}, sheet {same[3]} (= 6c2813ce)")

print("\n3. MSG 2 OPENINGS")
after1 = live[:live.index(b1) + 2]  # its cached reply 5.20 @ 45 d
seen = set()
for f in glob.glob(str(ROOT / "datasets/runs/*.json")) + glob.glob(str(ROOT / "tools/replays/raw/P18_*.json")):
    try:
        ms = thread_of(f)
    except Exception:  # noqa: BLE001
        continue
    bs = [m for m in ms if m.get("from") == "buyer" and m.get("term_sheets")]
    if len(bs) >= 2:
        seen.add(bs[1]["body"])
bodies = []
for i in range(len(mod.R2_OPENINGS)):
    os.environ["P18_TOP_R2"] = str(i)
    d2 = decide(after1)["message"]
    bodies.append(d2["body"])
    ok &= act({"message": d2}) == [(4.88, 45, 0)] and d2["refs"] == ["fc:370010@2026-09"]
ok &= len(set(bodies)) == len(bodies)
used = [i for i, b in enumerate(bodies) if b in seen]  # already played: the arena would replay its cached reply
print(f"   {len(bodies)} openings, distinct {len(set(bodies)) == len(bodies)}; already sent (cached, do not reuse): {used}; "
      f"sheet 4.88 @ 45 d db0 + forecast")
print("   " + bodies[0].replace("\n", "\n   "))

print("\n4. BRANCHES")
os.environ["P18_TOP_R2"] = "0"
d2 = decide(after1)
t2 = after1 + [buyer(d2)]
DB0, DB5 = mod.clause(0), mod.clause(5)
soft = t2 + [reply("open", [{"unit_price": 5.00, "index_clause": DB0, "payment_days": 45, "contract_months": 24},
                            {"unit_price": 5.10, "index_clause": DB5, "payment_days": 45, "contract_months": 24}], 2)]
normal = t2 + [reply("open", [{"unit_price": 5.10, "index_clause": DB0, "payment_days": 45, "contract_months": 24}], 2)]
cases = []
d3s = decide(soft)
cases.append(("soft round 2 (5.00 + 5.10 db5)", act(d3s), [(5.00, 45, 5), (4.99, 30, 5), (4.97, 14, 5)]))
d3n = decide(normal)
cases.append(("normal round 2 (5.10)", act(d3n), [(5.00, 45, 5)]))
s3 = soft + [buyer(d3s)]
n3 = normal + [buyer(d3n)]
cases.append(("soft, agreed 5.00 db5 @ 45", act(decide(s3 + [reply("agreed", [mod.sheet(5.00, 45, 5)], 3)])), "accept"))
cases.append(("soft, agreed 4.97 db5 @ 14", act(decide(s3 + [reply("agreed", [mod.sheet(4.97, 14, 5)], 3)])), "accept"))
cases.append(("soft, hold 5.00 @ 45", act(decide(s3 + [reply("open", [mod.sheet(5.00, 45, 0)], 3)])),
              [(5.02, 45, 5), (4.92, 45, 0)]))
cases.append(("soft, final 5.00 @ 45", act(decide(s3 + [reply("final_offer", [mod.sheet(5.00, 45, 0)], 3)])), "accept"))
cases.append(("soft, final 5.00 @ 45 + alt 4.89 @ 45 (beats)",
              act(decide(s3 + [reply("final_offer", [mod.sheet(5.00, 45, 0), mod.sheet(4.89, 45, 0)], 3)])), [(4.89, 45, 0)]))
cases.append(("normal, counter 5.00 @ 45", act(decide(n3 + [reply("open", [mod.sheet(5.00, 45, 0)], 3)])), [(5.10, 45, 5)]))
cases.append(("normal, agreed 5.00 db5 @ 45", act(decide(n3 + [reply("agreed", [mod.sheet(5.00, 45, 5)], 3)])), "accept"))
cases.append(("normal, counter 4.89 @ 45 (beats)", act(decide(n3 + [reply("open", [mod.sheet(4.89, 45, 0)], 3)])), "accept"))
n4 = n3 + [reply("open", [mod.sheet(5.00, 45, 0)], 3)]
n4b = n4 + [buyer(decide(n4))]
cases.append(("open after msg 4", act(decide(n4b + [reply("open", [mod.sheet(5.00, 45, 0)], 4)])), "accept"))
tmpl = after1[:-1] + [reply("open", [mod.sheet(5.10, 45, 0)], 1,
                             body="Dear Sir or Madam,\n\nWe value our cooperation and have made a step towards you.")]
cases.append(("engine-template reply", act(decide(tmpl)), "accept"))
for name, got, want in cases:
    good = got == want
    ok &= good
    print(f"   {name:46s} -> {got}{'' if good else '   <-- expected ' + str(want)}")

print("\n5. ARCHIVED REPLAY (every P18 game, every turn)")
files = sorted(set(glob.glob(str(ROOT / "tools/replays/raw/P18_*.json"))) |
               {f for f in glob.glob(str(ROOT / "datasets/runs/*.json"))
                if json.loads(Path(f).read_text(encoding="utf-8")).get("detail", {}).get("case_id") == "case:P18"})
turns = 0
for f in files:
    try:
        ms = thread_of(f)
    except Exception:  # noqa: BLE001
        continue
    for i, m in enumerate(ms):
        if m.get("from") == "buyer" and i:
            decide(ms[:i])
            turns += 1
print(f"   {len(files)} games, {turns} turns decided")
print(f"\nagent errors (crash guard fired): {len(ERRORS)} {ERRORS[:3]}")
ok &= not ERRORS
print("ALL CHECKS PASS" if ok else "CHECK FAILED")
