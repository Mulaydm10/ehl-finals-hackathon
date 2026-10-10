"""Accuracy of analysis/central/engine_rules.classify() on every archived game, round by round (offline).

    cd tacto/starter-kit && uv run python ../../analysis/tools/test_engine_rules.py

Rebuilds each thread as the agent saw it live (from the trace: our e-mails with term sheets, its e-mails with status and
primary sheet), calls classify() after each of its replies, and compares with the hand labels from task 3
(analysis/central/ENGINES.md). Prints accuracy by reply number and per case, plus the misses.
"""

import collections
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "analysis/central"))
sys.path.insert(0, str(ROOT / "analysis/tools"))
from engine_dump import load_games  # noqa: E402
from engine_rules import classify  # noqa: E402

LABELS = {"P01": "mirror", "P02": "mirror", "P03": "holder", "P04": "floor_stop", "P05": "auction", "P07": "mirror",
          "P08": "mirror", "P10": "one_shot", "P11": "holder", "P18": "mirror"}


def threads(game):
    """{supplier_id: events} rebuilt from the trace."""
    out = collections.defaultdict(list)
    for t in (game.get("result") or {}).get("trace") or []:
        m = t.get("move") or {}
        if t.get("actor") == "buyer":
            if m.get("type") != "message":
                continue
            sid = m.get("supplier_id")
            out[sid].append({"from": "buyer", "body": m.get("body"), "refs": m.get("refs"),
                             "term_sheets": [{"terms": ts.get("terms")} for ts in m.get("term_sheets") or []]})
        else:
            out[t["actor"]].append({"from": t["actor"], "body": m.get("text"), "status": m.get("status"),
                                    "term_sheets": [{"term_sheet_id": m.get("offer_id"), "terms": m.get("terms")}]
                                    if m.get("terms") else []})
    return out


def main():
    by_reply, by_case, misses = collections.defaultdict(lambda: [0, 0]), collections.defaultdict(lambda: [0, 0]), []
    for case, label in LABELS.items():
        for sid, g in load_games(f"case:{case}").items():
            th = threads(g)
            rivals = len(th) - 1
            for sup, events in th.items():
                n = 0
                for i, m in enumerate(events):
                    if m["from"] == "buyer":
                        continue
                    n += 1
                    if n < 2:  # its opening quote: nothing to classify yet
                        continue
                    got = classify(events[: i + 1], rivals=rivals)
                    ok = got["type"] == label
                    by_reply[n - 1][0] += ok
                    by_reply[n - 1][1] += 1
                    if m is [x for x in events if x["from"] != "buyer"][-1]:  # last reply of the thread
                        by_case[case][0] += ok
                        by_case[case][1] += 1
                        if not ok:
                            misses.append(f"{case} {sid} {sup}: got {got['type']} want {label} {got['evidence']}")
    tot = [sum(v[0] for v in by_reply.values()), sum(v[1] for v in by_reply.values())]
    print(f"all replies: {tot[0]}/{tot[1]} = {tot[0] / tot[1]:.0%}")
    for n in sorted(by_reply):
        ok, all_ = by_reply[n]
        print(f"  after its reply #{n}: {ok}/{all_} = {ok / all_:.0%}")
    print("end of thread, per case:")
    for case, (ok, all_) in by_case.items():
        print(f"  {case} ({LABELS[case]}): {ok}/{all_}")
    print("misses at the end of a thread:")
    for m in misses:
        print("  " + m)


if __name__ == "__main__":
    main()
