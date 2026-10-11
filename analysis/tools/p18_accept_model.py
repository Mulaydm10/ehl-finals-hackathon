"""P18 acceptance-model audit (offline, no arena, no LLM). For every ask we sent in every recorded P18 game (datasets/runs +
tools/replays/raw): its standing offer before the ask, the nominal discount, the value to it under the payment/deadband model
(db5/db3 -0.10; payment shorter than 30 d +0.10, longer -0.10), and what it did next (agreed / open / final).

    cd tacto/starter-kit && .venv/Scripts/python.exe ../../analysis/tools/p18_accept_model.py

Answers: (1) was any ask accepted more than 2% (nominal) under its standing offer? (2) per conversation, the bounds on its
acceptance floor in value terms (highest refused value < floor <= lowest accepted value).
"""
import glob
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def value(p, d, db):
    return round(p - (0.10 if db >= 3 else 0.0) + (0.10 if d < 30 else -0.10 if d > 30 else 0.0), 2)


def t3(t):
    return t.get("unit_price"), t.get("payment_days") or 30, float((t.get("index_clause") or {}).get("deadband_pct") or 0)


def games():
    for f in sorted(glob.glob(str(ROOT / "datasets/runs/*.json")) + glob.glob(str(ROOT / "tools/replays/raw/P18_*.json"))):
        d = json.loads(Path(f).read_text(encoding="utf-8"))
        s = d.get("session") or {}
        if (s.get("case_id") or d.get("case_id")) != "case:P18":
            continue
        th = (d.get("threads") or {}).get("sup:70740")
        msgs = th.get("messages") if isinstance(th, dict) else None
        if not msgs:
            tm = (d.get("thread_messages") or {}).get("sup:70740")
            msgs = tm.get("messages") if isinstance(tm, dict) else tm
        if isinstance(msgs, list):
            yield (s.get("session_id") or d.get("session_id")), [m for m in msgs if isinstance(m, dict)]


seen, over2, rows = set(), [], []
for sid, msgs in games():
    if sid in seen:
        continue
    seen.add(sid)
    offer = None
    floor_lo, floor_hi = -9, 9
    for i, m in enumerate(msgs):
        if m.get("from") != "buyer":
            if m.get("term_sheets"):
                offer = m["term_sheets"][0]["terms"]
            continue
        if not m.get("term_sheets") or offer is None or i + 1 >= len(msgs) or i == 1:
            continue
        nxt = msgs[i + 1]
        st = nxt.get("status")
        op, od, odb = t3(offer)
        ov = value(op, od, odb)
        for ts in m["term_sheets"]:
            p, d, db = t3(ts["terms"])
            if p is None or op is None:
                continue
            v = value(p, d, db)
            nominal = (op - p) / op * 100
            agreed = st == "agreed" and abs((nxt["term_sheets"][0]["terms"]["unit_price"]) - p) < 1e-9 and \
                (nxt["term_sheets"][0]["terms"].get("payment_days") or 30) == d
            rows.append((sid[:8], f"{op:.2f}@{od}/db{int(odb)} (v {ov:.2f})", f"{p:.2f}@{d}/db{int(db)}", round(nominal, 2), v,
                         "AGREED" if agreed else st))
            if agreed:
                floor_hi = min(floor_hi, v)
                if nominal > 2.0 + 1e-9:
                    over2.append(rows[-1])
            elif st in ("open", "final_offer"):
                floor_lo = max(floor_lo, v)
    if floor_hi < 9:
        print(f"{sid[:8]}: accepted value {floor_hi:.2f}; highest refused value {floor_lo if floor_lo > -9 else '-'}")
print("\nall asks after its first counter (game, its offer (value to it), our ask, nominal % under, value to it, next):")
for r in rows:
    print("  ", *r)
print(f"\naccepted asks more than 2% (nominal) under its standing offer: {len(over2)} {over2}")
