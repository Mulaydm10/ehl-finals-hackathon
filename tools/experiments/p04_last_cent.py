"""P04: play p04_record's plan to its final (4.89 @ 45 d = 0.874, the whole-cent ceiling), then make ONE closing ask
on the whole-cent sheet nearest its floor: EUR 4.93 @ 90 d. That sheet is worth 4.93 / 4.932 = 99.96 % of its floor
value at ANY cash rate (C_best's 90-day price is 4.932), so it is the only valid ask with a chance; if it takes it, C
is below C_best and the score clips to 1.0. If it answers with an offer we accept that offer; if it walks, this game
scores 0 - our practice best (max over games) stays 0.874.

    cd tacto/starter-kit
    uv run python ../../tools/experiments/p04_last_cent.py --sim     # offline (the fitted sim has an exact floor)
    uv run python ../../tools/experiments/p04_last_cent.py           # one live P04 game (archives + logs it)
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

LAST = (4.93, 90)


class LastCentAgent(P.P04RecordAgent):
    def __init__(self, last=LAST):
        super().__init__(send_alternative_back=False, plan=P.PLAN)
        self.last, self.pushed = last, False

    def decide(self, case, threads):
        sid = next(iter(threads))
        events = threads[sid]
        sup = P.latest(events)
        if sup.get("status") == "final_offer" and not self.pushed and P.moves_left(case, events) > 1:
            self.pushed = True
            sheets = [s for s in sup.get("term_sheets") or []
                      if (s.get("terms") or {}).get("unit_price") is not None]
            shown = [(s["terms"].get("unit_price"), s["terms"].get("payment_days")) for s in sheets]
            self.notes.append({"k": sum(m.get("from") == "buyer" for m in events), "status": "final_offer",
                               "sheets": shown, "do": f"closing ask {self.last[0]}@{self.last[1]}"})
            body = (f"Dear Mr Gruber,\n\nthank you for your final offer. We are ready to sign today on 90 days net: "
                    f"EUR {self.last[0]:.2f} per piece, 36 months, 20,000 pieces a year. The term sheet is attached "
                    f"for your confirmation.\n\n{P.SIGN}")
            return {"supplier_id": sid, "message": {
                "subject": "Renewal of framework agreement 4600070620 - 6306-2Z C3", "body": body,
                "term_sheets": [{"terms": self.sheet(case, *self.last)}]}}
        return super().decide(case, threads)  # after the ask: agreed -> accept; any offer -> accept its primary


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
    table, error, agent = RemoteTable(client), None, LastCentAgent()
    try:
        result = play(table, P.CASE_ID, agent)
    except Exception as e:  # never lose the game: record our own session
        if not table.session_id:
            raise
        error, result = f"{type(e).__name__}: {e}", run_plan.wait_for_end(client, table.session_id)
    run_plan.archive(client, table.session_id, P.CASE_ID)
    m = run_plan.measure(cases[P.CASE_ID], client.session(table.session_id).get("result") or result)
    row = {"exp": "P04-last-cent", "case": "P04", "session": table.session_id, "switches": ["last_cent"],
           "commit": run_plan.git_commit(), "model": "scripted (no model)",
           "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), **m, "rounds": agent.notes}
    if error:
        row.update(error=error, end_reason=result.get("end_reason"))
    with (P.ROOT / "analysis" / "experiments" / "results.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    sc = f"{m['score']:.3f}" if m["score"] is not None else "no score"
    with (P.ROOT / "notes" / "quota_log.md").open("a", encoding="utf-8") as f:
        f.write(f"| {row['time']} | Parth | P04 | p04_last_cent {row['commit']} (ask 4.93 @ 90 d after its final)"
                f" / scripted | {sc}{' - CRASHED: ' + error[:80] if error else ''} | {table.session_id} |\n")
    terms = result.get("terms") or {}
    print(f"\nP04 {table.session_id}: score {sc}  deal {result.get('deal')} {terms.get('unit_price')} @ "
          f"{terms.get('payment_days')} d  end {result.get('end_reason') or ''}")
    for r in agent.notes:
        print(f"  after our msg {r['k']}: {r['status']:12} {r['sheets']}  -> {r.get('do')}")
    print(f"quota left: {run_plan.quota_left(client)}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--sim", action="store_true")
    ap.add_argument("--reserve", type=int, default=40)
    a = ap.parse_args()
    if a.sim:
        for rate in (0.0693, 0.0752):
            print(f"supplier cash rate {rate:.4f}:")
            sc, end, _ = P.simulate(rate, agent=LastCentAgent())
            print(f"  -> score {sc}  ({end})\n")
    else:
        play_live(a.reserve)
