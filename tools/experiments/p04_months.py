"""P04: the 12-month test (Parth) - the supplier's own standard contract length, never offered in 8 P04 games.

    cd tacto/starter-kit
    uv run python ../../tools/experiments/p04_months.py --dry-run     # print the plan, no arena calls
    uv run python ../../tools/experiments/p04_months.py               # one live P04 game (archives + logs it)

Why: every P04 game so far offered 36 months (our sheets) and every final sat at one cash floor S in (4.870, 4.875]
-> 4.89 @ 45 d = 0.874, the ceiling IF its floor is the same at every contract length. But with whole-cent prices the
cheapest packages at or above C_best are (offline, arena_kit.total_cost, every price x payment x months):
    4.91 @ 90 d / 12 m   C = C_best + EUR 1    0.999
    4.85 @ 14 d / 24 m   C = C_best + EUR 24   0.990   (refused-range: its 14-day floor price is 4.86 at 36 m)
    4.90 @ 60 d / 24 m   C = C_best + EUR 41   0.982   (refused live in the probe 62a17f4abde590c7)
    4.88 @ 60 d / 12 m   C = C_best + EUR 56   0.976
A whole-cent package within EUR 1 of C_best (one cent at 12 m / 90 d is EUR 199) is either a 1-in-25 coincidence or
the arena's own best package - a term sheet carries whole cents. At 12 months, 4.92 @ 90 d already scores 0.914.
Plan: p04_record's proven messages at 12 months, two sheets a round with 90 d worth more to it (its primary goes to
the sheet worth most to it), +2-3 cents a round, data only in round 1; take its primary at once if it is <= 4.91 @
90 d, and at final_offer. If its 12-month 90-day final is 4.94 (its 36-month floor price), the floor does not depend
on the contract length and 0.874 stands.
"""

import argparse
import datetime
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import p04_record as P  # noqa: E402

P.MONTHS = 12  # P04RecordAgent.sheet() reads it
P.RECORD = (4.91, 90)  # C_best + EUR 1 at 12 months -> 0.999: take its primary at once at or under this
P.FLOOR_45 = (4.92, 90)  # 0.914 (beats 0.874): lock it from our LOCK_FROM-th message
PLAN_12 = [
    ((4.82, 90), (4.75, 60), ["ppi", "po", "fc"]),
    ((4.85, 90), (4.78, 60), []),
    ((4.87, 90), (4.80, 60), []),
    ((4.88, 90), (4.81, 60), []),
    ((4.89, 90), (4.82, 60), []),
]


class TwelveMonthAgent(P.P04RecordAgent):
    def __init__(self):
        super().__init__(send_alternative_back=True, plan=PLAN_12)

    def offer(self, case, sid, k, high, low, facts):
        out = super().offer(case, sid, k, high, low, facts)
        body = out["message"]["body"]
        body = body.replace(
            "We would like to renew on a multi-year basis: a binding 20,000 pieces a year for 36 months - the kind of "
            "agreement your colleagues told us changes prices.",
            "We would like to renew for 12 months, your standard contract length: a binding 20,000 pieces a year.",
        ).replace("both for 36 months", "both for 12 months")
        out["message"]["body"] = body
        return out


def play_live(reserve):
    import run_plan

    from arena_kit.cli import load_env
    from arena_kit.client import ArenaClient
    from arena_kit.play import RemoteTable, play

    os.chdir(P.KIT)
    load_env(".env")
    client = ArenaClient()
    left = run_plan.quota_left(client)
    if left is not None and left <= reserve:
        sys.exit(f"practice quota left {left} <= reserve {reserve}: not playing")
    cases = {c["case_id"]: c for c in client.cases("practice")}
    table, error, agent = RemoteTable(client), None, TwelveMonthAgent()
    try:
        result = play(table, P.CASE_ID, agent)
    except Exception as e:  # never lose the game: record our own session
        if not table.session_id:
            raise
        error, result = f"{type(e).__name__}: {e}", run_plan.wait_for_end(client, table.session_id)
    run_plan.archive(client, table.session_id, P.CASE_ID)
    final = client.session(table.session_id).get("result") or result
    m = run_plan.measure(cases[P.CASE_ID], final)
    row = {
        "exp": "P04-12-months",
        "case": "P04",
        "session": table.session_id,
        "switches": ["months=12"],
        "commit": run_plan.git_commit(),
        "model": "scripted (no model)",
        "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        **m,
        "rounds": agent.notes,
    }
    if error:
        row.update(error=error, end_reason=final.get("end_reason"))
    with (P.ROOT / "analysis" / "experiments" / "results.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    sc = f"{m['score']:.3f}" if m["score"] is not None else "no score"
    with (P.ROOT / "notes" / "quota_log.md").open("a", encoding="utf-8") as f:
        f.write(
            f"| {row['time']} | Parth | P04 | p04_months {row['commit']} (12-month sheets, 90 d primary) / scripted | "
            f"{sc}{' - CRASHED: ' + error[:80] if error else ''} | {table.session_id} |\n"
        )
    terms = final.get("terms") or {}
    print(
        f"\nP04 {table.session_id}: score {sc}  deal {terms.get('unit_price')} @ {terms.get('payment_days')} d / "
        f"{terms.get('contract_months')} m  end {final.get('end_reason') or ''}   (team best 0.874)"
    )
    for r in agent.notes:
        print(f"  after our msg {r['k']}: {r['status']:12} {r['sheets']}  -> {r.get('do')}")
    print(f"quota left: {run_plan.quota_left(client)}")


def dry_run():
    case = next(
        c
        for c in json.loads((P.ROOT / "datasets/cases_practice.json").read_text(encoding="utf-8"))
        if c["case_id"] == P.CASE_ID
    )
    agent = TwelveMonthAgent()
    for k, (high, low, facts) in enumerate(PLAN_12[:2]):
        agent.notes.append({})
        m = agent.offer(case, P.SUPPLIER, k, high, low, facts)["message"]
        print(f"--- message {k + 1}: {[t['terms'] for t in m['term_sheets']]}\n{m['body']}\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--reserve", type=int, default=40)
    a = ap.parse_args()
    if a.dry_run:
        dry_run()
    else:
        play_live(a.reserve)
