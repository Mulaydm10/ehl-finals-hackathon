"""Archive every practice game in full and analyse supplier behaviour across them - no practice quota.

For each session: GET /v1/sessions/{sid} (result, trace with the supplier's reasons) and every thread
(both sides' e-mails, term sheets, statuses) -> datasets/runs/<session_id>.json. Idempotent: re-run after
every game. Then prints behaviour statistics across all supplier e-mails:
  - per game: rounds, when the first final_offer came, price path, alternatives offered
  - our ask gap (how far below its standing price our cheapest sheet was) vs its next status:
    does a big ask trigger an immediate final_offer? (approval-ladder hypothesis, P10)

    cd tacto/starter-kit && .venv/bin/python ../../src/eval/archive_runs.py
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src/eval"))
from signals import client  # noqa: E402

OUT = ROOT / "datasets/runs"
OUT.mkdir(parents=True, exist_ok=True)
c = client()
games = []
for s in c.get("/v1/sessions").json():
    sid = s["session_id"]
    f = OUT / f"{sid}.json"
    if f.exists() and json.loads(f.read_text()).get("session", {}).get("status") == "ended":
        games.append(json.loads(f.read_text()))
        continue
    sess = c.get(f"/v1/sessions/{sid}").json()
    threads = {sup: c.get(f"/v1/sessions/{sid}/threads/{sup}").json() for sup in (sess.get("threads") or {})}
    g = {"session": s, "detail": sess, "threads": threads}
    f.write_text(json.dumps(g, ensure_ascii=False, indent=1))
    games.append(g)
print(f"archived {len(games)} games in datasets/runs/")

gap_vs_next = defaultdict(list)  # gap bucket -> next statuses
print(f"\n{'case':4} {'session':16} {'score':>5} {'rnds':>4} {'1st final':>9}  price path (its standing per reply) | alternatives")
for g in sorted(games, key=lambda g: g["session"]["created_at"]):
    s = g["session"]
    for sup, th in g["threads"].items():
        msgs = th.get("messages", [])
        path, first_final, alts, last_stand, rnd = [], None, 0, None, 0
        for m in msgs:
            sheets = m.get("term_sheets") or []
            if m.get("from") == "buyer":
                rnd += 1
                if sheets and last_stand:
                    ours = min(x["terms"].get("unit_price") or 1e9 for x in sheets)
                    gap = (last_stand - ours) / last_stand * 100
                    nxt = next((x.get("status") for x in msgs[msgs.index(m) + 1:] if x.get("from") != "buyer"), None)
                    b = "0-3%" if gap < 3 else "3-8%" if gap < 8 else "8-15%" if gap < 15 else "15%+"
                    gap_vs_next[(s["case_id"][5:], b)].append(nxt)
                    gap_vs_next[("ALL", b)].append(nxt)
                continue
            if sheets:
                last_stand = sheets[0]["terms"].get("unit_price")
                path.append(last_stand)
            if m.get("status") == "final_offer" and first_final is None:
                first_final = rnd
            alts += "lternativ" in (m.get("body") or "")
        if rnd == 0:
            continue  # probes: opened and walked away
        print(f"{s['case_id'][5:]:4} {s['session_id']:16} {s.get('score') or 0:5.2f} {rnd:4} {str(first_final):>9}  "
              f"{' > '.join(f'{p:g}' for p in path if p)} | {alts}")

print("\nOur ask gap below its standing price -> its NEXT status")
for key in sorted(gap_vs_next):
    sts = gap_vs_next[key]
    cnt = {x: sts.count(x) for x in set(sts)}
    fin = cnt.get("final_offer", 0) / len(sts)
    print(f"  {key[0]:4} {key[1]:6} n={len(sts):2}  final_offer {fin:4.0%}  {cnt}")
