"""P05 long game (Parth): the 0.965 path with every thread run to its round limit - for the board's rounds highlight.

    cd tacto/starter-kit
    uv run python ../../tools/experiments/p05_rounds.py --dry-run     # print the notes, no arena calls
    uv run python ../../tools/experiments/p05_rounds.py               # one live P05 game (archives + logs it)

Rounds do not score: practice ranks the best score per case, and in the final fewer rounds win a tie. The session's
`rounds` = our messages + timeouts over all threads; each thread has a limit of 10 rounds, so 3 bidders cap it at
~30-33. Plan: Fuchsreiter on the record path (hold round 1, 25.54 + rival + 2 facts, 26.60 -> agreed in 27e15c33),
then short no-price questions about the order until its round limit, then accept its standing offer. Dralveck and
Hrvelec: their round-1 asks, then no-price questions until their limit. A message without a term sheet is answered
and the quote stands (api.md). The record (0.965) stays on the board whatever this game scores.
"""

import argparse
import datetime
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import p05_hold as H  # noqa: E402

LIMIT = 10  # rounds per thread (case round_limit)
NOTES_TARGET = [
    "Please confirm that your order confirmation will reference our monthly call-off schedule.",
    "Which packaging do you plan for the shafts - single-piece protection or layered trays?",
    "Can you send the first-article inspection report with the first delivery?",
    "Please name your contact for call-offs and delivery notes.",
    "Is your material certificate 3.1 to EN 10204 included with each lot?",
    "Do you need our drawing revision B as a controlled copy, or is the PDF enough?",
    "Please confirm your delivery address and goods-receipt hours at Hollerau are noted.",
    "Thank you - we are completing the paperwork and will send the order shortly.",
]
NOTES_BACKUP = [
    "Thank you. We are completing the comparison of the bids and will come back to you shortly.",
    "One question in the meantime: is your quoted lead time firm for the call-offs from March 2027?",
    "Could you tell us which material certificate you supply with each lot?",
    "Which packaging would you use for the shafts?",
    "Do you need our drawing revision B as a controlled copy?",
    "Please name your contact for call-offs.",
    "Is your quote valid until the end of October?",
    "Thank you for your patience - we will come back to you shortly.",
    "Thank you - we are finalising our decision.",
]


class RoundsGame(H.Game):
    def __init__(self, client, case, args):
        super().__init__(client, case, args)
        self.backups_done = {H.DRALVECK: False, H.HRVELEC: False}

    def rounds_used(self, sup):
        return sum(m.get("from") == "buyer" for m in self.threads.get(sup) or [])

    def safe_send(self, sup, msg):
        """send(); None when the thread is over (round limit, ended session) - never crash a long game."""
        from arena_kit.client import ArenaError

        try:
            return self.send(sup, msg)
        except ArenaError as e:
            print(f"  {sup}: stop ({e.status} {e.detail})", flush=True)
            return None

    def note_msg(self, sup, text):
        name = {H.TARGET: "Ms Fuchsreiter", H.DRALVECK: "Mr Dralveck", H.HRVELEC: "Ms Procházková"}[sup]
        return {"subject": H.SUBJECT, "body": f"Dear {name},\n\n{text}\n\n{H.SIGN}"}

    def run_backup(self, sup):
        try:
            reply = self.safe_send(sup, self.backup_r1(sup))
            n = 0
            while reply and not self.ended and "result" not in reply:
                if reply.get("status") in ("walked_away", "no_bid"):
                    break
                if n >= len(NOTES_BACKUP) or self.rounds_used(sup) >= LIMIT:
                    break
                reply = self.safe_send(sup, self.note_msg(sup, NOTES_BACKUP[n]))
                n += 1
                if reply:
                    price = (H.primary(reply) or {}).get("terms", {}).get("unit_price")
                    print(f"  {sup} note {n} -> {reply.get('status')} {price}", flush=True)
        finally:
            self.backups_done[sup] = True
            print(f"  {sup}: done after {self.rounds_used(sup)} messages", flush=True)

    def play(self):
        opened = self.client.open_session(H.CASE_ID)
        t_open = time.monotonic()
        self.sid = opened["session_id"]
        self.threads = {s: list(ev) for s, ev in opened["threads"].items()}
        print(f"session {self.sid}", flush=True)
        pool = ThreadPoolExecutor(max_workers=3)
        for s in (H.DRALVECK, H.HRVELEC):
            pool.submit(self.run_backup, s)
        try:
            return self.run_target(t_open)
        finally:
            self.ended = True
            pool.shutdown(wait=False)

    def run_target(self, t_open):
        a = self.args
        time.sleep(max(H.HOLD_S - (time.monotonic() - t_open), 0))  # round 1: one timeout round
        self.note(sid=H.TARGET, k="r1", do="silence (a timeout round)")
        rivals = self.rival_offers()[:1]
        reply = self.safe_send(H.TARGET, self.target_ask(a.ask2, 0, rivals))
        self.note(sid=H.TARGET, k="ask1", do=f"ask {a.ask2} + {rivals} + news + AS-14404 + late-pay")
        H.show(f"{H.TARGET} reply", reply or {})
        if reply and reply.get("status") not in ("agreed", "final_offer", "walked_away"):
            reply = self.safe_send(H.TARGET, self.target_ask(a.ask3, 1))
            self.note(sid=H.TARGET, k="ask2", do=f"ask {a.ask3}")
            H.show(f"{H.TARGET} reply", reply or {})
        n, last = 0, reply  # `last`: its latest real answer (a refused note at the round limit returns None)
        while reply and "result" not in reply and reply.get("status") not in ("walked_away", "no_bid"):
            if self.rounds_used(H.TARGET) >= LIMIT or n >= len(NOTES_TARGET):
                break
            t_reply = time.monotonic()  # pace: keep its thread going until the backups have used their rounds
            while not all(self.backups_done.values()) and time.monotonic() - t_reply < a.pace:
                time.sleep(1)
            reply = self.safe_send(H.TARGET, self.note_msg(H.TARGET, NOTES_TARGET[n]))
            n += 1
            H.show(f"{H.TARGET} note {n}", reply or {})
            if reply:
                last = reply
        if last and "result" in last:
            return last["result"]
        p = H.primary(last) if last else None
        if p and last.get("status") not in ("walked_away", "no_bid"):
            return self.accept(H.TARGET, p, f"{last.get('status')} after {self.rounds_used(H.TARGET)} messages")
        best = self.best_backup()
        if best:
            return self.accept(best[1], best[2], "Fuchsreiter gone - cheapest valid backup")
        return {}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--ask2", type=float, default=25.54)
    ap.add_argument("--ask3", type=float, default=26.60)
    ap.add_argument("--pace", type=float, default=45, help="seconds we wait after its reply before the next note")
    ap.add_argument("--reserve", type=int, default=40)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    # p05_hold.Game reads these
    args.hold, args.rivals, args.facts, args.facts3, args.ask4, args.lead = "timeout", 1, True, False, 26.80, 28
    if args.dry_run:
        print("Fuchsreiter notes:\n  " + "\n  ".join(NOTES_TARGET))
        print("Backup notes:\n  " + "\n  ".join(NOTES_BACKUP))
        return
    import run_plan

    from arena_kit.cli import load_env
    from arena_kit.client import ArenaClient

    os.chdir(H.KIT)
    load_env(".env")
    client = ArenaClient()
    left = run_plan.quota_left(client)
    if left is not None and left <= args.reserve:
        sys.exit(f"practice quota left {left} <= reserve {args.reserve}: not playing")
    cases = {c["case_id"]: c for c in client.cases("practice")}
    game, error = RoundsGame(client, cases[H.CASE_ID], args), None
    try:
        result = game.play()
    except Exception as e:  # never lose the game: record our own session
        if not game.sid:
            raise
        error, result = f"{type(e).__name__}: {e}", run_plan.wait_for_end(client, game.sid)
    time.sleep(2)
    run_plan.archive(client, game.sid, H.CASE_ID)
    state = client.session(game.sid)
    final = state.get("result") or result or {}
    m = run_plan.measure(cases[H.CASE_ID], final)
    row = {
        "exp": "P05-rounds",
        "case": "P05",
        "session": game.sid,
        "switches": ["max-rounds"],
        "commit": run_plan.git_commit(),
        "model": "scripted (no model)",
        "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        **m,
        "session_rounds": state.get("rounds"),
        "rounds": game.notes,
    }
    if error:
        row.update(error=error, end_reason=final.get("end_reason"))
    with (H.ROOT / "analysis" / "experiments" / "results.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    sc = f"{m['score']:.3f}" if m["score"] is not None else "no score"
    with (H.ROOT / "notes" / "quota_log.md").open("a", encoding="utf-8") as f:
        f.write(
            f"| {row['time']} | Parth | P05 | p05_rounds {row['commit']} (max rounds: {state.get('rounds')}) / scripted"
            f" | {sc}{' - CRASHED: ' + error[:80] if error else ''} | {game.sid} |\n"
        )
    terms = final.get("terms") or {}
    print(
        f"\nP05 {game.sid}: ROUNDS {state.get('rounds')}  score {sc}  deal {final.get('supplier_id')} "
        f"{terms.get('unit_price')} @ {terms.get('payment_days')} d   (record 0.965)"
    )
    print(f"quota left: {run_plan.quota_left(client)}")


if __name__ == "__main__":
    main()
