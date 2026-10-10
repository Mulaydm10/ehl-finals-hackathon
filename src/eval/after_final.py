"""What happened every time we sent something after a supplier's final_offer (datasets/runs/, no quota).

    python3 src/eval/after_final.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KEEP = ("unit_price", "payment_days", "lead_time_days", "contract_months")
for f in sorted((ROOT / "datasets/runs").glob("*.json")):
    g = json.loads(f.read_text())
    case, sess = g["session"]["case_id"][5:], g["session"]["session_id"]
    for th in g["threads"].values():
        ms = th.get("messages", [])
        for i, m in enumerate(ms):
            if m.get("from") == "buyer" or m.get("status") != "final_offer" or i + 1 >= len(ms):
                continue
            fin = (m.get("term_sheets") or [{}])[0].get("terms", {})
            nxt = ms[i + 1]
            if nxt.get("term_sheets"):
                ours = [{k: v for k, v in x["terms"].items() if k in KEEP} for x in nxt["term_sheets"]]
                reply = ms[i + 2] if i + 2 < len(ms) else {}
                print(f"{case} {sess} final {fin.get('unit_price')} -> WE SENT {ours} -> supplier: {reply.get('status')}")
            else:
                print(f"{case} {sess} final {fin.get('unit_price')} -> we accepted")
