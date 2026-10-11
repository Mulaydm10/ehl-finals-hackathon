"""P18 offline checks (no arena, no LLM): feed every recorded P18 game to each P18 agent variant and print what it would send
turn by turn; then the exact beat lines and a table of all games (round-1 data, first counter, price path, score, time).

    cd tacto/starter-kit && .venv/Scripts/python.exe ../../analysis/tools/p18_replay_agents.py [replay|lines|games] [agent ...]

Agents default to noidea_p18_cross, _harvest, _soft, _db3 and _replay (analysis/agent_variants/). Games: datasets/runs + the
P18 files in tools/replays/raw. Scores use the arena cost model (reproduces every recorded P18 deal to the cent).
"""
import collections
import datetime
import glob
import importlib.util
import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("pcc", ROOT / "analysis/tools/p18_cross_check.py")
pcc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pcc)
logging.disable(logging.CRITICAL)
AGENTS = ["noidea_p18_cross", "noidea_p18_harvest", "noidea_p18_soft", "noidea_p18_db3", "noidea_p18_replay"]


def all_games():
    out = {}
    for f in sorted(glob.glob(str(ROOT / "datasets/runs/*.json")) + glob.glob(str(ROOT / "tools/replays/raw/P18_*.json"))):
        d = json.loads(Path(f).read_text(encoding="utf-8"))
        s = d.get("session") or {}
        if (s.get("case_id") or d.get("case_id")) != "case:P18":
            continue
        th = (d.get("threads") or {}).get(pcc.SID)
        msgs = th.get("messages") if isinstance(th, dict) else None
        if not msgs:
            tm = (d.get("thread_messages") or {}).get(pcc.SID)
            msgs = tm.get("messages") if isinstance(tm, dict) else tm
        if not isinstance(msgs, list):
            continue
        sid = s.get("session_id") or d.get("session_id")
        res = (d.get("detail") or d).get("result") or {}
        out[sid] = (s.get("created_at") or 0, [m for m in msgs if isinstance(m, dict)], res.get("terms"))
    return out


def replay(names):
    for name in names:
        A = pcc.load(ROOT / f"analysis/agent_variants/{name}.py", f"_rp_{name}").NoIdeaAgent
        print(f"\n######## {name}")
        pcc.replay(A)


def lines():
    def s(p, d, db):
        return pcc.score({"unit_price": p, "payment_days": d, "contract_months": 24,
                          "index_clause": None if db is None else pcc.CLAUSE[db]})
    print("Highest price that beats the record 0.75595 (24 m), and the score at that price:")
    for d in (14, 30, 45, 60, 90):
        row = []
        for db in (0, 3, 5, None):
            p = max(x / 100 for x in range(440, 560) if s(x / 100, d, db) > pcc.RECORD)
            row.append(f"{'none' if db is None else 'db' + str(db)} <= {p:.2f} ({s(p, d, db):.4f})")
        print(f"  {d:>2} d: " + " | ".join(row))
    print("Score of 5.00 (its usual floor): " + " | ".join(f"{d} d db0 {s(5.0, d, 0):.4f}" for d in (14, 30, 45, 60, 90)))


def games():
    rows = []
    for sid, (t, msgs, deal) in all_games().items():
        us = [m for m in msgs if m.get("from") == "buyer" and m.get("term_sheets")]
        sup = [m for m in msgs if m.get("from") != "buyer"]
        if not us or len(sup) < 2:
            continue
        k = collections.Counter()
        for r in us[0].get("refs") or []:
            p = r.split(":")[0]
            k[r.split(":")[1].split("@")[0] if p == "idx" else p] += 1
        path = []
        for m in sup[1:]:
            ts = (m.get("term_sheets") or [{}])[0].get("terms") or {}
            if ts.get("unit_price") is not None:
                path.append(f"{ts['unit_price']:.2f}@{ts.get('payment_days')}"
                            + (f"/db{int(ts['index_clause']['deadband_pct'])}" if ts.get("index_clause") else ""))
        r1 = " | ".join(pcc.lab(x["terms"]) for x in us[0]["term_sheets"])
        when = datetime.datetime.fromtimestamp(t).strftime("%m-%d %H:%M") if t else "      ?    "
        rows.append((t, f"{when} {sid[:8]} r1 {r1:<28} data {dict(k)} | its {' > '.join(path[:5])} | "
                        f"{('%.4f ' % pcc.score(deal)) + pcc.lab(deal) if deal else 'no deal'}"))
    for _, line in sorted(rows):
        print(line)
    print(f"{len(rows)} games")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    what = sys.argv[1] if len(sys.argv) > 1 else "replay"
    names = sys.argv[2:] or AGENTS
    {"replay": lambda: replay(names), "lines": lines, "games": games}[what]()
