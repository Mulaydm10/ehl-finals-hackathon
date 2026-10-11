"""Offline checks of analysis/agent_variants/noidea_p18_coda2.py (no arena session). Reads tacto/starter-kit/.env.openai
(gitignored) for gpt-6-astra, which writes main's prose only if main takes over (msg 5+ or final/agreed handling).

    cd tacto/starter-kit && .venv/Scripts/python.exe ../../analysis/tools/p18_coda2_check.py

1. the four planned messages on the expected path (5.20 @ 45 -> 5.00 @ 45 + 5.10 db5 -> ...): full bodies, sheets, refs;
   msg 1 must be 6c2813ce's msg 1 byte for byte (body, sheets, refs); msg 2 must be new after that msg 1 (no recorded game
   sent it after 6c2813ce's msg 1) and 6c2813ce's own msg 2 must not be sent;
2. branches: first counter 5.30 / 5.40; round-2 normal 5.10; after msg 3: agreed (db5 / db0), counter 4.90 (cut), hold 5.00,
   final 5.00, counter 4.85 (record); after msg 4: agreed / final;
3. exact scores of every planned and fallback sheet.
"""
import glob
import importlib.util
import json
import logging
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KIT = ROOT / "tacto/starter-kit"
sys.path.insert(0, str(KIT))
for line in (KIT / ".env.openai").read_text().splitlines():
    if "=" in line and not line.lstrip().startswith("#"):
        k, v = line.split("=", 1)
        os.environ[k.strip()] = v.strip()
spec = importlib.util.spec_from_file_location("pcc", ROOT / "analysis/tools/p18_cross_check.py")
pcc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pcc)
logging.basicConfig(level=logging.WARNING)
from arena_kit.agents.llm import llm_from_env  # noqa: E402

CASE, SID, CL = pcc.CASE, pcc.SID, pcc.CLAUSE
A = pcc.load(ROOT / "analysis/agent_variants/noidea_p18_coda2.py", "_coda2_check").NoIdeaAgent
raw, calls = llm_from_env(), []


def astra(system, user):
    t = time.time()
    try:
        return raw(system, user)
    finally:
        calls.append(time.time() - t)


src = json.loads((ROOT / "datasets/runs/6c2813cee1fcf116.json").read_text(encoding="utf-8"))["threads"][SID]["messages"]
OPENING = src[0]  # its opening quote (6.10 @ 30 d / 12 m), the same in every game


def lab(t):
    return pcc.lab(t) if t.get("unit_price") is not None else str(t)


def sup(status, *sheets, n=1):
    """sheets: (price, days, db) ...; ids offer:70740-n (primary) and offer:70740-n-a (alternative)."""
    ts = [{"term_sheet_id": f"offer:70740-{n}" + ("-a" if j else ""),
           "terms": {"unit_price": p, "payment_days": d, "contract_months": 24, "index_clause": CL[db]}}
          for j, (p, d, db) in enumerate(sheets)]
    return {"from": "sales@70740", "status": status, "body": "Dear customer,\nOur offer stands.", "claim_results": [],
            "term_sheets": ts}


def run(replies, show_body=False, tag=""):
    """Play our agent against scripted replies; returns the agent's last decision."""
    ag, thread = A(astra), [dict(OPENING)]
    d = None
    for n, rep in enumerate([None] + replies):
        if rep is not None:
            thread.append(rep)
        d = ag.decide(CASE, {SID: [dict(x) for x in thread]})
        m = d["message"]
        if m.get("action"):
            print(f"  {tag} after reply {n}: ACTION {m['action']}")
            return d, thread
        if n == len(replies):
            print(f"  {tag} msg {n + 1}: SEND {[lab(x['terms']) for x in m['term_sheets']]} refs {m.get('refs')}")
            if show_body:
                print("    " + m["body"].replace("\n", "\n    "))
            return d, thread
        thread.append({**m, "from": "buyer"})
    return d, thread


print("== 1. planned path (5.20 @ 45 -> soft 5.00 + 5.10 db5)")
R1 = sup("open", (5.20, 45, 0), (5.30, 45, 5), n=1)
R2 = sup("open", (5.00, 45, 0), (5.10, 45, 5), n=2)
for k, reps in enumerate([[], [R1], [R1, R2]]):
    d, _ = run(reps, show_body=True, tag="planned")
m1 = run([], tag="(msg 1)")[0]["message"]
m2 = run([R1], tag="(msg 2)")[0]["message"]
b6 = [m for m in src if m.get("from") == "buyer" and m.get("term_sheets")]
same1 = (m1["body"] == b6[0]["body"] and m1["term_sheets"] == b6[0]["term_sheets"]
         and sorted(m1.get("refs") or []) == sorted(b6[0].get("refs") or []))
after1 = []  # msg 2 bodies recorded after 6c2813ce's msg 1
for f in glob.glob(str(ROOT / "datasets/runs/*.json")) + glob.glob(str(ROOT / "tools/replays/raw/P18_*.json")):
    g = json.loads(Path(f).read_text(encoding="utf-8"))
    if ((g.get("session") or {}).get("case_id") or g.get("case_id")) != "case:P18":
        continue
    th = (g.get("threads") or {}).get(SID)
    ms = th.get("messages") if isinstance(th, dict) else None
    if not ms:
        tm = (g.get("thread_messages") or {}).get(SID)
        ms = tm.get("messages") if isinstance(tm, dict) else tm
    b = [m for m in (ms or []) if isinstance(m, dict) and m.get("from") == "buyer" and m.get("term_sheets")]
    if len(b) >= 2 and b[0].get("body") == b6[0]["body"]:
        after1.append((Path(f).stem, b[1].get("body")))
print(f"  msg 1 = 6c2813ce's msg 1 byte for byte (body, sheets, refs): {same1}")
print(f"  recorded games that sent 6c2813ce's msg 1: {len(after1)} ({', '.join(n for n, _ in after1)})")
exp2 = b6[1]["body"].replace("(EUR 4.90 per unit, AS-14404", "(EUR 4.88 per unit, AS-14404", 1)
print(f"  msg 2 = 6c2813ce's msg 2 with only the ask 4.90 -> 4.88: {m2['body'] == exp2 and m2['body'] != b6[1]['body']}; "
      f"sheets {[lab(x['terms']) for x in m2['term_sheets']]}; refs {m2.get('refs')} (6c2813ce: {b6[1].get('refs')})")
print(f"  msg 2 is new after that msg 1 (not any of their msg 2s): {all(m2['body'] != x for _, x in after1)}")

print("== 2. branches")
run([sup("open", (5.30, 45, 0), (5.40, 45, 5), n=1)], tag="first counter 5.30 ->")
run([R1, sup("open", (4.89, 45, 0), n=2)], tag="r2 4.89 (beats) ->")
print(" -- SOFT round 2 (5.00 + 5.10 db5)")
after3 = {"agreed 5.00 db5": sup("agreed", (5.00, 45, 5), n=3), "agreed 4.89 db0": sup("agreed", (4.89, 45, 0), n=3),
          "counter 4.90 db0 (tie)": sup("open", (4.90, 45, 0), n=3), "hold 5.00 + 5.10 db5": sup("open", (5.00, 45, 0), (5.10, 45, 5), n=3),
          "final 5.00": sup("final_offer", (5.00, 45, 0), n=3), "counter 4.85 (record)": sup("open", (4.85, 45, 0), n=3)}
for tag, rep in after3.items():
    d, thread = run([R1, R2, rep], tag=f"after msg 3: {tag} ->", show_body=(tag == "hold 5.00 + 5.10 db5"))
    if tag in ("hold 5.00 + 5.10 db5", "counter 4.90 db0 (tie)"):
        for tag2, rep2 in {"agreed": sup("agreed", *[(x["terms"]["unit_price"], x["terms"]["payment_days"],
                                                    int(x["terms"]["index_clause"]["deadband_pct"]))
                                                   for x in d["message"]["term_sheets"][:1]], n=4),
                           "final 5.00": sup("final_offer", (5.00, 45, 0), n=4)}.items():
            run([R1, R2, rep, rep2], tag=f"    then msg 4 -> {tag2} ->")
print(" -- NORMAL round 2 (5.10) - the fix: msg 3 inside its 2%")
N2 = sup("open", (5.10, 45, 0), n=2)
run([R1, N2], tag="normal r2 5.10 ->", show_body=True)
run([R1, sup("open", (5.10, 45, 0), (5.20, 45, 5), n=2)], tag="normal r2 5.10 + 5.20 db5 ->")
run([R1, sup("open", (5.20, 45, 0), n=2)], tag="r2 hold 5.20 ->")
for tag, rep in {"cut to 5.00": sup("open", (5.00, 45, 0), n=3), "agreed 5.10 db5": sup("agreed", (5.10, 45, 5), n=3),
                 "final 5.10": sup("final_offer", (5.10, 45, 0), n=3), "hold 5.10": sup("open", (5.10, 45, 0), n=3)}.items():
    d, _ = run([R1, N2, rep], tag=f"after normal msg 3: {tag} ->", show_body=(tag == "hold 5.10"))
    if tag == "hold 5.10":
        run([R1, N2, rep, sup("final_offer", (5.10, 45, 0), n=4)], tag="    then msg 4 -> final 5.10 ->")

print("== 3. exact scores (arena cost model)")
for lbl, (p, d_, db) in {"msg 2 4.88 @ 45 db0": (4.88, 45, 0), "msg 3 5.00 @ 45 db5 (record)": (5.00, 45, 5),
                         "msg 3 4.89 @ 45 db0 (record)": (4.89, 45, 0), "tie 4.90 @ 45 db0 (Codacabana)": (4.90, 45, 0),
                         "msg 4 step 5.02 @ 45 db5": (5.02, 45, 5), "msg 4 step 4.92 @ 45 db0": (4.92, 45, 0),
                         "fallback 5.00 @ 45 db0": (5.00, 45, 0), "fallback 5.10 @ 45 db5": (5.10, 45, 5),
                         "fallback 5.10 @ 45 db0": (5.10, 45, 0)}.items():
    sc = pcc.score({"unit_price": p, "payment_days": d_, "contract_months": 24, "index_clause": CL[db]})
    print(f"  {lbl:34s} {sc:.4f}  {'> 0.727' if sc > 0.7271 else ''} {'> record' if sc > pcc.RECORD else ''}")
print(f"== Astra calls {len(calls)}, mean {sum(calls) / max(1, len(calls)):.1f}s, max {max(calls, default=0):.1f}s")
