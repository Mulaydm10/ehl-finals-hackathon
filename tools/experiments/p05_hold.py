"""P05 hold path (Parth): hold Fuchsreiter's round 1, then ask once while it still stands at 38.50, then ONE move.

    cd tacto/starter-kit
    uv run python ../../tools/experiments/p05_hold.py --dry-run          # print the plan, no arena calls
    uv run python ../../tools/experiments/p05_hold.py                    # one live P05 game (archives + logs it)
    uv run python ../../tools/experiments/p05_hold.py --hold note        # variant: a no-price note instead of silence

Evidence (all 13 archived P05 games; analysis/cases/P05.md sections 9-13):
- The only game that reached 27.00 @ 14 (= 0.924, the board's best) is d9af85e000ab3d4d: its round 1 timed out ("Without
  movement from your side we cannot move either", 38.50 held), our first ask 25.54 + a much lower rival landed in its
  round 2 -> 28.00 + "we need to clarify this internally"; round 3 (timeout, no move) -> "clarified ... move further"
  -> final 27.50 @ 30 / 27.00 @ 14.
- Asked at round 1 instead, 23.80 / 24.50 drew 30.50 and the path ended at 28.00 (9ce6, 1ebd); 21.00 drew 36.00 and a
  walk (8e94). Asks 29.17-30.25 drew 31.00 either way.
- After "clarify internally" its line drops ~1.00 the next round, and if our standing ask is above that line it AGREES
  at our price (30.25 / 30.44 agreed in 5 games). Mirror of our later moves ~0.75-1.0x on its 0.50 grid.
- The rules: a message later than 60 s counts as a timeout - our last offer repeated, its patience drops; three in a
  row end the thread. A message without a term sheet is answered and the quote stands.
Plan: hold round 1 (silence ~65 s, or a no-price note), ask 25.54 @ 14 + the lowest rival + our true late-pay record,
then one move to 26.30 (its line ~27.00 minus the mirror of our move -> agree at 26.30 or counter on the 26.50 grid).
Take any primary <= 27.00 @ 14 at once from round 3 on (27.00 = 0.924; 26.50 = 0.975; 26.30 = 0.996); never push
after a final_offer.
"""

import argparse
import base64
import datetime
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KIT = ROOT / "tacto" / "starter-kit"
sys.path[:0] = [str(KIT), str(Path(__file__).resolve().parent)]

from arena_kit.cost import complete_offer, must_haves_ok, total_cost  # noqa: E402
from arena_kit.docs import standard_terms  # noqa: E402

CASE_ID = "case:P05"
TARGET, DRALVECK, HRVELEC = "sup:70250", "sup:70210", "sup:70240"
SUBJECT = "RFQ pump shaft HX (part:320070)"
SIGN = "Kind regards\nPurchasing, Hollerau Pumpenwerke"
LEAD = {TARGET: 28, DRALVECK: 28, HRVELEC: 42}
HOLD_S = 65  # its opening + 60 s = one timeout; a second would come at +120 s
TAKE_AT = 27.00  # from round 3 on: 27.00 @ 14 = 0.924 (the board's best); anything lower beats it


def late_payment(supplier, months=12):
    """(share late, mean days late of the late ones) of our invoices to `supplier`, last `months` - our own record."""
    import csv

    rows = [
        r
        for r in csv.DictReader((ROOT / "tacto/data/data/invoices.csv").open(encoding="utf-8"))
        if r.get("supplier_id") == supplier and r.get("paid_date") and r.get("due_date")
    ]
    last = max(datetime.date.fromisoformat(r["invoice_date"]) for r in rows)
    since = last - datetime.timedelta(days=round(months * 30.44))
    days = [
        (datetime.date.fromisoformat(r["paid_date"]) - datetime.date.fromisoformat(r["due_date"])).days
        for r in rows
        if datetime.date.fromisoformat(r["invoice_date"]) >= since
    ]
    late = [d for d in days if d > 0]
    return len(late) / len(days), sum(late) / len(late)


def call_off_schedule(per_month=350, start=(2027, 1), months=24):
    y, m = start
    rows = ["month,quantity"] + [
        f"{y + (m - 1 + i) // 12}-{(m - 1 + i) % 12 + 1:02d},{per_month}" for i in range(months)
    ]
    return {
        "name": "call_off_schedule.csv",
        "type": "csv",
        "content_b64": base64.b64encode(("\n".join(rows) + "\n").encode()).decode(),
    }


def sheet(case, price, sid, days=14):
    return {"terms": complete_offer(case, {"unit_price": price, "payment_days": days, "lead_time_days": LEAD[sid]})}


def primary(msg):
    sheets = [s for s in (msg or {}).get("term_sheets") or [] if (s.get("terms") or {}).get("unit_price")]
    return sheets[0] if sheets and sheets[0].get("term_sheet_id") else None


def show(tag, msg):
    sheets = msg.get("term_sheets") or []
    flags = [
        k
        for k, rx in (
            ("clarify", r"clarify this internally|come back to you on price"),
            ("CLARIFIED", r"clarified this internally|move further"),
            ("no-move", r"[Ww]ithout movement"),
            ("final", r"final offer|letztes Angebot|last price"),
            ("figures?", r"Which figures"),
        )
        if re.search(rx, msg.get("body") or "")
    ]
    print(
        f"  {tag}: {msg.get('status')} "
        + " | ".join(
            f"{s.get('term_sheet_id')} {s['terms'].get('unit_price')}@{s['terms'].get('payment_days')}"
            f"/{s['terms'].get('lead_time_days')}"
            for s in sheets
        )
        + f"  claims {[c.get('result') for c in msg.get('claim_results') or []]} {flags}",
        flush=True,
    )


class Game:
    def __init__(self, client, case, args):
        self.client, self.case, self.args = client, case, args
        self.sid = None
        self.threads = {}  # supplier -> list of messages (ours with from=buyer)
        self.notes = []
        self.arrived = {}  # supplier -> when its latest reply came in
        self.ended = False
        share, days = late_payment(TARGET)
        self.late_line = (
            f"Straight talk on payment: over the last 12 months we paid {share * 100:.0f}% of your invoices "
            f"late, on average {days:.1f} days after the due date - your letter of 18 August was right. "
            "That ends with this contract: 14 days net, every invoice paid on the due date."
        )

    def note(self, **kw):
        self.notes.append(kw)
        print("  ->", kw, flush=True)

    # ---- arena calls
    def send(self, sup, msg):
        """Our e-mail; on a 409 (late = a timeout round ran) fetch the thread and send once more."""
        from arena_kit.client import ArenaError

        try:
            reply = self.client.send_message(self.sid, sup, msg)
        except ArenaError as e:
            if e.status != 409:
                raise
            t = self.client.thread(self.sid, sup)
            outs = [
                (x.get("round"), x.get("status"), (x.get("terms") or {}).get("unit_price"))
                for x in t.get("timeouts") or []
            ]
            print(f"  {sup}: 409 ({e.detail}); timeouts {outs} closed={t.get('closed')}", flush=True)
            if t.get("closed"):
                return {"status": "walked_away", "term_sheets": [], "body": f"({t.get('closed')})"}
            reply = self.client.send_message(self.sid, sup, msg)
        if "result" not in reply:
            self.threads[sup] += [{**msg, "from": "buyer"}, reply]
        self.arrived[sup] = time.monotonic()
        return reply

    KEEP_NOTE = (
        "thank you for your offer. We are completing the comparison of the bids and will come back to you shortly."
    )

    def keeper(self, sup, first):
        """A backup is insurance only: after its round-1 reply, answer each reply with a no-price note before its
        60 s run out (the quote stands), until the game ends or it leaves."""
        name = {DRALVECK: "Mr Dralveck", HRVELEC: "Ms Procházková"}[sup]
        try:
            reply = first.result()
            while not self.ended and reply.get("status") not in ("walked_away", "no_bid") and "result" not in reply:
                while not self.ended and time.monotonic() - self.arrived[sup] < 40:
                    time.sleep(1)
                if self.ended:
                    return
                reply = self.send(sup, {"subject": SUBJECT, "body": f"Dear {name},\n\n{self.KEEP_NOTE}\n\n{SIGN}"})
                print(
                    f"  {sup} keep-note -> {reply.get('status')} "
                    f"{(primary(reply) or {}).get('terms', {}).get('unit_price')}",
                    flush=True,
                )
        except Exception as e:  # never let insurance crash the game
            print(f"  {sup} keeper stopped: {type(e).__name__}: {e}", flush=True)

    def accept(self, sup, offer, why):
        from arena_kit.client import ArenaError

        self.note(sid=sup, do=f"accept {offer['term_sheet_id']} {offer['terms']} ({why})")
        try:
            out = self.client.send_message(
                self.sid, sup, {"action": {"type": "accept", "term_sheet_id": offer["term_sheet_id"]}}
            )
        except ArenaError as e:
            t = self.client.thread(self.sid, sup)
            print(f"  accept refused ({e.status} {e.detail}); standing offer now {t.get('offer_id')}", flush=True)
            if e.status in (409, 422) and t.get("offer_id") and not t.get("closed"):
                out = self.client.send_message(
                    self.sid, sup, {"action": {"type": "accept", "term_sheet_id": t["offer_id"]}}
                )
            else:
                raise
        return out.get("result", out)

    # ---- messages
    def backup_r1(self, sup):
        price = {DRALVECK: 27.20, HRVELEC: 27.00}[sup]
        lines = [
            "thank you for your offer. We are awarding the HX pump shaft (part:320070) for the series start in "
            "March 2027: 4,200 pieces a year, binding for 24 months."
        ]
        if sup == DRALVECK:
            lines.append("We have an offer at EUR 31.50 per piece (offer:70240-0).")
        lines += [
            f"We propose EUR {price:.2f} per piece, 14 days net, {LEAD[sup]} days lead time (term sheet attached).",
            "Attached: our monthly call-off schedule for the full contract term.",
        ]
        name = {DRALVECK: "Mr Dralveck", HRVELEC: "Ms Procházková"}[sup]
        return {
            "subject": SUBJECT,
            "body": f"Dear {name},\n\n" + "\n\n".join(lines) + f"\n\n{SIGN}",
            "term_sheets": [sheet(self.case, price, sup)],
            "attachments": [call_off_schedule()],
        }

    def rival_offers(self):
        """(offer id, price) per rival bidder: its lowest offer so far (Hrvelec's 31.50 opening is always there),
        cheapest first. Each rival's quote counts once per supplier we cite it to."""
        best = {HRVELEC: ("offer:70240-0", 31.50)}
        for sup in (DRALVECK, HRVELEC):
            for m in self.threads.get(sup) or []:
                p = primary(m) if m.get("from") != "buyer" else None
                if p and p["terms"].get("unit_price") and (sup not in best or p["terms"]["unit_price"] < best[sup][1]):
                    best[sup] = (p["term_sheet_id"], p["terms"]["unit_price"])
        return sorted(best.values(), key=lambda x: x[1])

    def target_ask(self, price, k, rivals=()):
        if k == 0:
            lines = [
                "thank you for your offer. We are awarding the HX pump shaft (part:320070) for the series start "
                "in March 2027: 4,200 pieces a year, binding for 24 months.",
                self.late_line,
                "It is steady work for the second shift you told us has been on hold since spring.",
            ]
            for i, (oid, price_r) in enumerate(rivals):
                lines.append(f"We have {'another' if i else 'an'} offer at EUR {price_r:.2f} per piece ({oid}).")
            if self.args.facts:  # two more checked facts (3 claims per message at most, with one rival)
                lines.append("We noted: Drehteile Fuchsreiter GmbH looks for new customers (news:20260309-03).")
                lines.append(
                    "The 1.4404 alloy surcharge changed -8.47% from 2024-11 to 2025-10 "
                    "(idx:AS-14404@2024-11, idx:AS-14404@2025-10)."
                )
        else:
            lines = ["thank you for your reply. We move again."]
            if k == 1 and self.args.facts3:  # two new checked facts for its last round (each ID counts once per case)
                lines.append(
                    "Electricity producer prices changed -17.15% from 2025-02 to 2026-02 "
                    "(idx:PPI-D351@2025-02, idx:PPI-D351@2026-02)."
                )
                lines.append(
                    "Producer prices for cold drawing of bars changed -3.77% from 2024-09 to 2025-09 "
                    "(idx:PPI-C2431@2024-09, idx:PPI-C2431@2025-09)."
                )
        lines.append(f"We propose EUR {price:.2f} per piece, 14 days net, 28 days lead time (term sheet attached).")
        msg = {"subject": SUBJECT, "term_sheets": [sheet(self.case, price, TARGET)]}
        if k == 0:
            lines.append("Attached: our monthly call-off schedule for the full contract term.")
            msg["attachments"] = [call_off_schedule()]
        msg["body"] = "Dear Ms Fuchsreiter,\n\n" + "\n\n".join(lines) + f"\n\n{SIGN}"
        return msg

    HOLD_NOTE = (
        "Dear Ms Fuchsreiter,\n\nthank you for your quote. We are evaluating the three bids for the HX series "
        "this week; our proposal follows shortly. One question in the meantime: is your quoted lead time of 28 "
        f"days firm for the call-offs from March 2027?\n\n{SIGN}"
    )

    # ---- the game
    def best_backup(self):
        best = None
        for sup in (DRALVECK, HRVELEC):
            m = next((x for x in reversed(self.threads.get(sup) or []) if x.get("from") != "buyer"), None)
            p = primary(m)
            if not p or (m or {}).get("status") in ("walked_away", "no_bid"):
                continue
            full = complete_offer(self.case, p["terms"])
            if not must_haves_ok(self.case, full):
                continue
            c = total_cost(self.case, full, standard_terms(self.threads[sup]))
            if best is None or c < best[0]:
                best = (c, sup, p)
        return best

    def play(self):
        opened = self.client.open_session(CASE_ID)
        t_open = time.monotonic()
        self.sid = opened["session_id"]
        self.threads = {s: list(ev) for s, ev in opened["threads"].items()}
        print(f"session {self.sid}", flush=True)
        for s, ev in self.threads.items():
            show(f"{s} r0", ev[-1])
        pool = ThreadPoolExecutor(max_workers=4)
        backups = {s: pool.submit(self.send, s, self.backup_r1(s)) for s in (DRALVECK, HRVELEC)}
        for s, f in backups.items():
            pool.submit(self.keeper, s, f)
        self.note(sid="backups", do="r1 asks Dralveck 27.20 (+ rival 31.50), Hrvelec 27.00 @ 42 d; then no-price notes")
        try:
            return self._play_target(t_open, backups)
        finally:
            self.ended = True
            pool.shutdown(wait=False)

    def _play_target(self, t_open, backups):
        a = self.args
        # 1. hold its round 1
        if a.hold == "note":
            show(f"{TARGET} hold-note reply", self.send(TARGET, {"subject": SUBJECT, "body": self.HOLD_NOTE}))
            self.note(sid=TARGET, k="r1", do="no-price holding note")
        elif a.hold == "timeout":
            wait = HOLD_S - (time.monotonic() - t_open)
            self.note(sid=TARGET, k="r1", do=f"silence {max(wait, 0):.0f}s more (a timeout round)")
            time.sleep(max(wait, 0))
        for s, f in backups.items():  # their round-1 counters are in by now (or we cite Hrvelec's opening)
            if f.done():
                try:
                    show(f"{s} r1", f.result())
                except Exception as e:  # a backup is insurance only
                    print(f"  {s}: {e}", flush=True)
        # 2. the one real ask while it still stands where it opened
        rivals = self.rival_offers()[: a.rivals]
        reply = self.send(TARGET, self.target_ask(a.ask2, 0, rivals))
        self.note(
            sid=TARGET,
            k="ask1",
            do=f"ask {a.ask2}@14/28 + cite {rivals}{' + news + AS-14404' if a.facts else ''} + late-pay + shift",
        )
        show(f"{TARGET} reply", reply)
        if "result" in reply:
            return reply["result"]
        k, asks = 1, [a.ask3, a.ask4, a.ask4 + 0.3, a.ask4 + 0.6]
        while True:
            st, p = reply.get("status"), primary(reply)
            if st in ("walked_away", "no_bid") or not p:
                best = self.best_backup()
                if best:
                    return self.accept(best[1], best[2], "Fuchsreiter gone - cheapest valid backup")
                return self.client.send_message(self.sid, TARGET, {"action": {"type": "walk_away"}}).get("result", {})
            price, days = p["terms"]["unit_price"], p["terms"].get("payment_days")
            take = days == 14 and price <= (TAKE_AT if k >= 2 else 26.95)
            if st in ("agreed", "final_offer") or take or k > len(asks):
                return self.accept(TARGET, p, f"{st} {price}@{days}")
            ask = asks[k - 1]
            if ask >= price:
                return self.accept(TARGET, p, f"its {price} is at or under our next ask {ask}")
            reply = self.send(TARGET, self.target_ask(ask, k))
            self.note(
                sid=TARGET,
                k=f"ask{k + 1}",
                its=price,
                do=f"ask {ask}@14/28 (move +{ask - ([a.ask2] + asks)[k - 1]:.2f})",
            )
            show(f"{TARGET} reply", reply)
            if "result" in reply:
                return reply["result"]
            k += 1


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--hold", choices=["timeout", "note", "none"], default="timeout")
    ap.add_argument("--ask2", type=float, default=25.54, help="the first real ask, after the hold")
    ap.add_argument("--ask3", type=float, default=26.30, help="the one move after its 'clarify internally'")
    ap.add_argument("--ask4", type=float, default=26.80, help="only if it is still open above 27.00 after ask3")
    ap.add_argument("--rivals", type=int, default=1, help="rival bidders' offers cited in the first ask (1-2)")
    ap.add_argument(
        "--facts", action="store_true", help="first ask also cites its free-capacity news + the 1.4404 surcharge fall"
    )
    ap.add_argument("--facts3", action="store_true", help="the move after its first counter cites two new index falls")
    ap.add_argument("--reserve", type=int, default=40)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    case = next(
        c
        for c in json.loads((ROOT / "datasets/cases_practice.json").read_text(encoding="utf-8"))
        if c["case_id"] == CASE_ID
    )
    if args.dry_run:
        g = Game(None, case, args)
        g.threads = {DRALVECK: [], HRVELEC: [], TARGET: []}
        print(f"hold={args.hold} ask2={args.ask2} ask3={args.ask3} ask4={args.ask4}\n")
        for s in (DRALVECK, HRVELEC):
            m = g.backup_r1(s)
            print(f"--- {s} r1 {[x['terms'] for x in m['term_sheets']]}\n{m['body']}\n")
        if args.hold == "note":
            print(f"--- {TARGET} r1 hold note\n{g.HOLD_NOTE}\n")
        for k, price in enumerate([args.ask2, args.ask3, args.ask4]):
            demo = [("offer:70210-2", 28.00), ("offer:70240-0", 31.50)][: args.rivals]
            m = g.target_ask(price, k, demo if k == 0 else ())
            terms = [x["terms"] for x in m["term_sheets"]]
            print(f"--- {TARGET} ask {k + 1} {terms} att={len(m.get('attachments') or [])}\n{m['body']}\n")
        return
    import run_plan

    from arena_kit.cli import load_env
    from arena_kit.client import ArenaClient

    os.chdir(KIT)
    load_env(".env")
    client = ArenaClient()
    left = run_plan.quota_left(client)
    if left is not None and left <= args.reserve:
        sys.exit(f"practice quota left {left} <= reserve {args.reserve}: not playing")
    cases = {c["case_id"]: c for c in client.cases("practice")}
    game, error = Game(client, cases[CASE_ID], args), None
    try:
        result = game.play()
    except Exception as e:  # never lose the game: record our own session
        if not game.sid:
            raise
        error, result = f"{type(e).__name__}: {e}", run_plan.wait_for_end(client, game.sid)
    time.sleep(2)
    run_plan.archive(client, game.sid, CASE_ID)
    final = client.session(game.sid).get("result") or result or {}
    m = run_plan.measure(cases[CASE_ID], final)
    label = f"p05_hold {args.hold} {args.ask2}/{args.ask3}/{args.ask4}"
    row = {
        "exp": "P05-hold",
        "case": "P05",
        "session": game.sid,
        "switches": [f"hold={args.hold}"],
        "commit": run_plan.git_commit(),
        "model": "scripted (no model)",
        "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        **m,
        "rounds": game.notes,
    }
    if error:
        row.update(error=error, end_reason=final.get("end_reason"))
    with (ROOT / "analysis" / "experiments" / "results.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    sc = f"{m['score']:.3f}" if m["score"] is not None else "no score"
    with (ROOT / "notes" / "quota_log.md").open("a", encoding="utf-8") as f:
        f.write(
            f"| {row['time']} | Parth | P05 | {label} {row['commit']} / scripted | {sc}"
            f"{' - CRASHED: ' + error[:80] if error else ''} | {game.sid} |\n"
        )
    terms = final.get("terms") or {}
    print(
        f"\nP05 {game.sid}: score {sc}  deal {final.get('supplier_id')} {terms.get('unit_price')} @ "
        f"{terms.get('payment_days')} d / {terms.get('lead_time_days')} d  end {final.get('end_reason') or ''}"
        f"   (our best before: 0.820)"
    )
    for r in game.notes:
        print("  ", r)
    print(f"quota left: {run_plan.quota_left(client)}")


if __name__ == "__main__":
    main()
