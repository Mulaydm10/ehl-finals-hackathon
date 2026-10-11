"""Offline checks of analysis/agent_variants/noidea_p18_beat30.py (copy of p18_pay14_check.py with its plan) (no arena session; gpt-6-astra writes main's prose when main
takes over). Reads tacto/starter-kit/.env.openai (gitignored) for the model.

    cd tacto/starter-kit && .venv/Scripts/python.exe ../../analysis/tools/p18_beat30_check.py

1. verbatim: messages 1-2 equal 6c2813ce's byte for byte; message 3 differs only in the proposal (v2: 5.03 db5 + 4.93 db0 @ 45 d);
2. branches after message 3 on scripted replies (agreed / hold / final / counter above or below our ask / off-track);
3. exact scores of every planned and fallback deal against our 0.727 and the record 0.75595.
"""
import copy
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
A = pcc.load(ROOT / "analysis/agent_variants/noidea_p18_beat30.py", "_beat30_check").NoIdeaAgent
raw, calls = llm_from_env(), []


def astra(system, user):
    t = time.time()
    try:
        return raw(system, user)
    finally:
        calls.append(time.time() - t)


src = json.loads((ROOT / "datasets/runs/6c2813cee1fcf116.json").read_text(encoding="utf-8"))["threads"][SID]["messages"]
buyer_idx = [i for i, m in enumerate(src) if m.get("from") == "buyer" and m.get("term_sheets")]


def lab(t):
    return pcc.lab(t) if t.get("unit_price") is not None else str(t)


def sup(status, price, days=45, db=0, n=3):
    return {"from": "sales@70740", "status": status, "body": "Dear customer,\nOur offer stands.", "claim_results": [],
            "term_sheets": [{"term_sheet_id": f"offer:70740-{n}",
                             "terms": {"unit_price": price, "payment_days": days, "contract_months": 24, "index_clause": CL[db]}}]}


def show(tag, d):
    m = d["message"]
    if m.get("action"):
        print(f"  {tag}: ACTION {m['action']}")
    else:
        print(f"  {tag}: SEND {[lab(x['terms']) for x in m['term_sheets']]} refs {m.get('refs')} | ...{m['body'][-260:]!r}")
    return d


print("== 1. verbatim against 6c2813ce (its real replies)")
ag = A(astra)
for n, i in enumerate(buyer_idx[:3]):
    d = ag.decide(CASE, {SID: [dict(x) for x in src[:i]]})
    out, live = d["message"], src[i]
    same = {k: out.get(k) == live.get(k) for k in ("subject", "body", "term_sheets", "refs")}
    print(f"  msg {n + 1}: ours {[lab(x['terms']) for x in out['term_sheets']]} live {[lab(x['terms']) for x in live['term_sheets']]} same {same}")
    if n == 2:
        old = "(EUR 4.91 per unit, AS-14404 index clause (45% share, 0% deadband), 30 days payment, 24 months)"
        new = ("(EUR 5.02 per unit, AS-14404 index clause (45% share, 5% deadband), 30 days payment, 24 months; "
               "EUR 4.92 per unit, AS-14404 index clause (45% share, 0% deadband), 30 days payment, 24 months)")
        print(f"  msg 3 body = 6c2813ce's with only the proposal changed: {out['body'] == live['body'].replace(old, new)}")
        msg3 = out

print("== 2. branches after message 3 (scripted replies)")
base = [dict(x) for x in src[:buyer_idx[2]]] + [{**msg3, "from": "buyer"}]
cases = {"agreed 5.02 @ 30 db5": sup("agreed", 5.02, 30, 5), "agreed 4.92 @ 30": sup("agreed", 4.92, 30), "hold 5.00 @ 30": sup("open", 5.00, 30),
         "final 5.00 @ 30": sup("final_offer", 5.00, 30), "counter 4.90 @ 30": sup("open", 4.90, 30), "hold 5.00 @ 45": sup("open", 5.00)}
for tag, rep in cases.items():
    ag = A(astra)
    for i in buyer_idx[:3]:  # rebuild the agent state
        ag.decide(CASE, {SID: [dict(x) for x in src[:i]]})
    d = show(tag, ag.decide(CASE, {SID: base + [rep]}))
    if tag in ("hold 5.00 @ 30", "hold 5.00 @ 45"):  # then message 4 -> agreed / final
        m4 = {**d["message"], "from": "buyer"}
        for tag2, rep2 in {"  -> agreed 5.03 @ 30 db5": sup("agreed", 5.03, 30, 5, n=4), "  -> agreed 4.93 @ 30": sup("agreed", 4.93, 30, n=4), "  -> final 5.00 @ 30": sup("final_offer", 5.00, 30, n=4)}.items():
            show(tag2, ag.decide(CASE, {SID: base + [rep, m4, rep2]}))
        if tag == "hold 5.00 @ 30":
            print("    msg 4 body:", repr(m4["body"]), "refs", m4.get("refs"))

print("== 2b. off track at message 2 (first counter 5.30 @ 45 instead of 5.20)")
ag = A(astra)
ag.decide(CASE, {SID: [dict(x) for x in src[:buyer_idx[0]]]})
first = [dict(x) for x in src[:buyer_idx[1]]]
first[-1] = sup("open", 5.30, n=1)
show("r1 5.30 @ 45", ag.decide(CASE, {SID: first}))

print("== 3. exact scores (arena cost model)")
for lbl, t in {"msg 3 ask 5.02 @ 30 d db5": (5.02, 30, 5), "msg 3 ask 4.92 @ 30 d db0": (4.92, 30, 0), "msg 4 ask 5.03 @ 30 d db5": (5.03, 30, 5), "msg 4 ask 4.93 @ 30 d db0": (4.93, 30, 0), "fallback final 5.00 @ 30 d": (5.00, 30, 0),
               "its floor 5.00 @ 45 d db0 (fallback)": (5.00, 45, 0), "record line 45 d db0 4.89": (4.89, 45, 0),
               "our best 4.91 @ 14 d db0 (0c968aae)": (4.91, 14, 0), "6c2813ce close 4.94 @ 30 d db0": (4.94, 30, 0)}.items():
    p, d_, db = t
    sc = pcc.score({"unit_price": p, "payment_days": d_, "contract_months": 24, "index_clause": CL[db]})
    print(f"  {lbl:40s} {sc:.4f}  {'> 0.727' if sc > 0.7271 else ''} {'> record' if sc > pcc.RECORD else ''}")
print(f"== Astra calls {len(calls)}, mean {sum(calls) / max(1, len(calls)):.1f}s, max {max(calls, default=0):.1f}s")
