"""P05 (RFQ) per-bidder view of every archived game: our asks, its answers, cited rivals and claim results, round by round.

    cd tacto/starter-kit && .venv/Scripts/python.exe ../../analysis/tools/p05_bidders.py [--body]
"""
import glob
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BODY = "--body" in sys.argv


def sheets(m):
    out = []
    for t in m.get("term_sheets") or []:
        x = t.get("terms", t)
        out.append(f"{x.get('unit_price')}@{x.get('payment_days')}d/{x.get('lead_time_days')}lt")
    return out


def main():
    files = sorted(glob.glob(str(ROOT / "tools/replays/raw/P05_*.json")))
    lows = {}
    for f in files:
        d = json.loads(Path(f).read_text(encoding="utf-8"))
        res = d.get("result") or {}
        print(f"\n######## {Path(f).stem}  score {res.get('score')}  end {d.get('end_reason')}  deal "
              f"{res.get('supplier_id')} {(res.get('terms') or {}).get('unit_price')}")
        for sid, th in (d.get("thread_messages") or {}).items():
            print(f"  --- {sid}  final status {th.get('status')}")
            for m in th.get("messages", []):
                who = "US " if m["from"] == "buyer" else "SUP"
                extra = ""
                if who == "US ":
                    extra = f" refs={m.get('refs') or []}"
                else:
                    extra = f" [{m.get('status')}] claims={[c.get('result') for c in (m.get('claim_results') or [])]}"
                    for t in m.get("term_sheets") or []:
                        x = t.get("terms", t)
                        if x.get("unit_price") and (x.get("lead_time_days") or 99) <= 42:
                            lows.setdefault(sid, []).append((x["unit_price"], Path(f).stem[-8:], m.get("status")))
                print(f"    {who} {sheets(m)}{extra}")
                if BODY and who == "SUP":
                    print("        " + " ".join((m.get("body") or "").split())[:600])
    print("\n#### lowest valid (lead <= 42) offers per bidder:")
    for sid, v in sorted(lows.items()):
        print(" ", sid, sorted(v)[:6])


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
