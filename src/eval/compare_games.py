"""Side-by-side of several live games of one case: our sheets, e-mail size, data IDs, attachments and opening per
round, and the supplier's sheets plus the sentences about payment/standard terms/flexibility. (no quota)

    python3 src/eval/compare_games.py <session:label> [<session:label> ...]
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for arg in sys.argv[1:]:
    sess, _, label = arg.partition(":")
    f = ROOT / f"datasets/runs/{sess}.json"
    if not f.exists():
        print("missing", sess)
        continue
    ms = next(iter(json.loads(f.read_text())["threads"].values()))["messages"]
    print("=================", label, sess)
    for m in ms:
        sheets = [(x["terms"].get("unit_price"), x["terms"].get("payment_days")) for x in (m.get("term_sheets") or [])]
        body = m.get("body") or ""
        if m.get("from") == "buyer":
            parts = body.split("\n\n")
            ids = re.findall(r"\((?:idx|fc|cost|sc|doc|ctr|po)[^)]*\)", body)
            att = [a.get("name") for a in (m.get("attachments") or [])]
            print(f"  US  {sheets or m.get('action')} words={len(body.split())} ids={len(ids)} att={att}")
            if len(parts) > 1:
                print(f"      opening: {parts[1][:240]}")
        else:
            flat = body.replace("\n", " ")
            hint = [x for x in re.split(r"(?<=[.!?])\s+", flat)
                    if re.search(r"(?i)standard|30-day|30 days|financing|balance|flexib|withdraw", x)][:2]
            print(f"  SUP {m.get('status')} {sheets} | {' / '.join(h[:150] for h in hint)}")
