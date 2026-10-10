"""How suppliers reacted to every kind of cited data, from all our archived games (offline, no quota).

    tacto/starter-kit/.venv/Scripts/python.exe analysis/tools/mine_claims.py

Reads datasets/runs/*.json (Dhruv's archive) and tools/replays/raw/*.json (Neel's), de-duplicated by session, and
counts the supplier's fixed reactions ("We checked the <kind> data you cited; it holds and we took it into account" /
"... but it does not change our calculation" / "Your figures confirm our case" / "We did not know that - a fair
point" / "We received a lot of material") per data kind, overall and per case. Writes
analysis/central/claim_reactions.json, which analysis/agent_variants/central.py reads.
"""

import collections
import glob
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "analysis" / "central" / "claim_reactions.json"

KINDS = {"volume change": "volume_change", "price history": "po_prices", "index change": "index_change",
         "rival quote": "rival_quote", "should cost": "should_cost", "quality record": "scorecard_ppm",
         "delivery record": "scorecard_otd", "notice period": "notice_period"}
CHECKED = re.compile(r"(?i)we checked the (.+?) data you cited; it holds(,| and)(?: but)? (it does not change|we took it)")
ALREADY = re.compile(r"(?i)already (taken|been fully accounted|factored).{0,40}?(volume change|price history|index change|"
                     r"notice period|rival quote|should cost)?")


def sessions():
    seen = {}
    for f in glob.glob(str(ROOT / "datasets/runs/*.json")):
        s = json.loads(Path(f).read_text(encoding="utf-8"))
        d = s.get("detail") or {}
        if d.get("session_id"):
            seen[d["session_id"]] = (d.get("case_id"), (d.get("result") or {}).get("trace") or [])
    for f in glob.glob(str(ROOT / "tools/replays/raw/*.json")):
        s = json.loads(Path(f).read_text(encoding="utf-8"))
        if s.get("session_id") and s["session_id"] not in seen:
            seen[s["session_id"]] = (s.get("case_id"), (s.get("result") or {}).get("trace") or [])
    return seen


def main():
    total = collections.defaultdict(collections.Counter)
    by_case = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
    general = collections.Counter()
    games = sessions()
    for sid, (case, trace) in games.items():
        for t in trace:
            if t.get("actor") == "buyer":
                continue
            for r in t.get("reasons") or []:
                if (m := CHECKED.search(r)):
                    kind = KINDS.get(m.group(1).lower(), m.group(1).lower())
                    verdict = "taken" if "took" in m.group(3) else "no_change"
                    total[kind][verdict] += 1
                    by_case[case][kind][verdict] += 1
                if re.search(r"(?i)confirm our case", r):
                    general["rising_index_backfired"] += 1
                    by_case[case]["index_change"]["confirm_case"] += 1
                    total["index_change"]["confirm_case"] += 1
                if re.search(r"(?i)fair point|did not know that", r):
                    general["fair_point"] += 1
                if re.search(r"(?i)lot of material", r):
                    general["padding"] += 1
                if re.search(r"(?i)which figures is that based on|please send us the data", r):
                    general["asked_for_data"] += 1
                if ALREADY.search(r):
                    general["already_counted"] += 1
    out = {"games": len(games),
           "by_kind": {k: dict(v) for k, v in sorted(total.items())},
           "by_case": {c: {k: dict(v) for k, v in ks.items()} for c, ks in sorted(by_case.items())},
           "signals": dict(general)}
    for k, v in out["by_kind"].items():
        n = sum(v.values())
        v["take_rate"] = round(v.get("taken", 0) / n, 2) if n else 0.0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"{len(games)} games")
    for k, v in sorted(out["by_kind"].items(), key=lambda x: -x[1]["take_rate"]):
        print(f"  {k:<15} {v}")
    print("  signals", out["signals"])
    print("  P03", out["by_case"].get("case:P03"))


if __name__ == "__main__":
    main()
