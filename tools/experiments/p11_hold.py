"""P11 hold path (Parth): the P05 levers on Kalwisz - hold round 1, one new verified fact per round, then ONE ask a hair
under its grid counter (it agrees at our price once that clears its line).

    cd tacto/starter-kit
    uv run python ../../tools/experiments/p11_hold.py --dry-run          # print the plan, no arena calls
    uv run python ../../tools/experiments/p11_hold.py                    # one live P11 game (archives + logs it)
    uv run python ../../tools/experiments/p11_hold.py --hold none        # control: first ask in round 1

Evidence (35 archived P11 games, analysis/cases/P11.md; P05 record analysis/cases/P05.md section 13):
- No P11 game ever held round 1: every first counter came in round 1 (46.00 in 9 games, 46.50 in 24). On P05 the first
  counter in round 2 (after one timeout) was 2.50 lower than in round 1 for the same ask.
- Kalwisz cuts for new verified facts (quality record, steel, forecast in msg 1; energy in msg 2), holds without one,
  and counters on a 0.50 grid rounded up - but agrees at our price above its line: 44.95 agreed (eac2), 44.90 refused
  (7285) when its counter showed 45.00.
- Best so far 0.8019 = 44.95 @ 300 ppm / EUR 0 (eac20911ec06e2d6). 0.81 = 44.90, 0.85 = 44.48, 0.90 = 44.35.
Plan: hold round 1 (silence ~65 s), then eac2's facts round by round (42.77 + quality record + steel + forecast + our
true late-payment record; 43.57 + energy; 44.01 + labour), then one ask `--hair` under its counter, and accept.
"""

import argparse
import base64
import datetime
import json
import os
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KIT = ROOT / "tacto" / "starter-kit"
sys.path[:0] = [str(KIT), str(Path(__file__).resolve().parent)]

from arena_kit.cost import complete_offer, must_haves_ok  # noqa: E402

CASE_ID = "case:P11"
SUP = "sup:70140"
SUBJECT = "Bearing bracket HN (part:310020) - quality commitment and price 2027"
SIGN = "Kind regards,\nPurchasing, Hollerau Pumpenwerke"
HOLD_S = 65  # its opening + 60 s = one timeout round


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


def call_off_schedule(per_year=15900, start=(2027, 1), months=12):
    y, m = start
    rows = ["month,quantity"] + [
        f"{y + (m - 1 + i) // 12}-{(m - 1 + i) % 12 + 1:02d},{per_year // 12 + (1 if i < per_year % 12 else 0)}"
        for i in range(months)
    ]
    return {
        "name": "call_off_schedule.csv",
        "type": "csv",
        "content_b64": base64.b64encode(("\n".join(rows) + "\n").encode()).decode(),
    }


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
            ("margin", r"cannot give up margin"),
            ("final", r"final offer|letztes Angebot|last price"),
            ("figures?", r"Which figures"),
        )
        if re.search(rx, msg.get("body") or "")
    ]
    print(
        f"  {tag}: {msg.get('status')} "
        + " | ".join(
            f"{s.get('term_sheet_id')} {s['terms'].get('unit_price')}@{s['terms'].get('ppm_commitment')}"
            f"/{s['terms'].get('chargeback_eur_per_complaint')}"
            for s in sheets
        )
        + f"  claims {[c.get('result') for c in msg.get('claim_results') or []]} {flags}",
        flush=True,
    )


class Game:
    def __init__(self, client, case, args):
        self.client, self.case, self.args = client, case, args
        self.sid, self.events, self.notes = None, [], []
        share, days = late_payment(SUP)
        self.late_line = (
            f"Straight talk: over the last 12 months we paid {share * 100:.0f}% of your invoices late, on average "
            f"{days:.0f} days after the due date. That is on us, and it ends with this contract: every invoice paid on "
            "the due date, which brings your cash in about 10 days earlier than you are used to."
        )

    def note(self, **kw):
        self.notes.append(kw)
        print("  ->", kw, flush=True)

    def sheet(self, price):
        return {
            "terms": complete_offer(
                self.case, {"unit_price": price, "ppm_commitment": 300, "chargeback_eur_per_complaint": 0}
            )
        }

    # one new verified fact (kind) per message; the first carries three (the arena checks at most 3 per message)
    def rounds(self):
        a = self.args
        first = [
            "Thank you for your offer. Quality comes first for us: we need a binding commitment of 300 ppm, backed by "
            "your 8D report, and in return we will not ask you for chargebacks or any penalties: we want a binding "
            "quality commitment and your corrective-action plan, not cash out of your business.",
            self.late_line,
            "We confirm a binding volume of 15,900 units per year for 12 months.\n"
            "Your quality over the last 12 months was 2376 ppm (sc:70140@2026Q3).\n"
            "Producer prices DE: basic iron and steel, ferro-alloys changed -4.3% from 2024-10 to 2025-10 "
            "(idx:PPI-C241@2024-10, idx:PPI-C241@2025-10).\n"
            "Our demand forecast for Bearing bracket HN is up +20.0% (fc:310020@2026-09).",
        ]
        return [
            (a.ask1, first, True),
            (
                a.ask2,
                [
                    "Thank you for moving. Producer prices DE: electric power generation, transmission and "
                    "distribution changed -17.1% from 2025-02 to 2026-02 (idx:PPI-D351@2025-02, idx:PPI-D351@2026-02)."
                ],
                False,
            ),
            (
                a.ask3,
                [
                    "Thank you. Labour cost index DE, manufacturing, seasonally and calendar adjusted (quarterly, "
                    "carried to its three months) changed -0.3% from 2025-10 to 2026-01 "
                    "(idx:LCI-C@2025-10, idx:LCI-C@2026-01)."
                ],
                False,
            ),
        ]

    def message(self, price, lines, attach):
        body = (
            "Dear Odlewnia Kalwisz team,\n\n"
            + "\n\n".join(lines)
            + f"\n\nWe propose EUR {price:.2f} per piece, 300 ppm, no chargeback (term sheet attached)."
        )
        msg = {"subject": SUBJECT, "term_sheets": [self.sheet(price)]}
        if attach:
            body += "\n\nAttached: our monthly call-off schedule for the full contract term."
            msg["attachments"] = [call_off_schedule()]
        msg["body"] = body + f"\n\n{SIGN}"
        return msg

    # ---- arena calls
    def send(self, msg):
        from arena_kit.client import ArenaError

        try:
            reply = self.client.send_message(self.sid, SUP, msg)
        except ArenaError as e:
            if e.status != 409:
                raise
            t = self.client.thread(self.sid, SUP)
            outs = [
                (x.get("round"), x.get("status"), (x.get("terms") or {}).get("unit_price"))
                for x in t.get("timeouts") or []
            ]
            print(f"  409 ({e.detail}); timeouts {outs} closed={t.get('closed')}", flush=True)
            if t.get("closed"):
                return {"status": "walked_away", "term_sheets": [], "body": f"({t.get('closed')})"}
            reply = self.client.send_message(self.sid, SUP, msg)
        if "result" not in reply:
            self.events += [{**msg, "from": "buyer"}, reply]
        return reply

    def accept(self, offer, why):
        from arena_kit.client import ArenaError

        self.note(do=f"accept {offer['term_sheet_id']} {offer['terms']} ({why})")
        try:
            out = self.client.send_message(
                self.sid, SUP, {"action": {"type": "accept", "term_sheet_id": offer["term_sheet_id"]}}
            )
        except ArenaError as e:
            t = self.client.thread(self.sid, SUP)
            print(f"  accept refused ({e.status} {e.detail}); standing offer now {t.get('offer_id')}", flush=True)
            if e.status in (409, 422) and t.get("offer_id") and not t.get("closed"):
                out = self.client.send_message(
                    self.sid, SUP, {"action": {"type": "accept", "term_sheet_id": t["offer_id"]}}
                )
            else:
                raise
        return out.get("result", out)

    def close(self, reply, why):
        """Accept its standing primary if it keeps the must-have (ppm <= 1,500); else offer 300 / EUR 0 at its price."""
        p = primary(reply)
        if p and must_haves_ok(self.case, complete_offer(self.case, p["terms"])):
            return self.accept(p, why)
        price = max(
            (s["terms"]["unit_price"] for s in reply.get("term_sheets") or [] if s.get("terms", {}).get("unit_price")),
            default=None,
        )
        if price is None:
            return self.client.send_message(self.sid, SUP, {"action": {"type": "walk_away"}}).get("result", {})
        reply = self.send(self.message(price, ["Thank you. We accept your price on our quality terms."], False))
        show("reply", reply)
        return self.accept(primary(reply), "its price on 300 ppm / EUR 0")

    # ---- the game
    def play(self):
        a = self.args
        opened = self.client.open_session(CASE_ID)
        t_open = time.monotonic()
        self.sid = opened["session_id"]
        self.events = list(opened["threads"][SUP])
        print(f"session {self.sid}", flush=True)
        show("r0", self.events[-1])
        if a.hold == "timeout":
            wait = HOLD_S - (time.monotonic() - t_open)
            self.note(k="r1", do=f"silence {max(wait, 0):.0f}s more (a timeout round)")
            time.sleep(max(wait, 0))
        reply, last_price, held = None, None, 0
        for k, (ask, lines, attach) in enumerate(self.rounds()):
            reply = self.send(self.message(ask, lines, attach))
            self.note(
                k=f"ask{k + 1}",
                do=f"ask {ask}@300/0 + {re.findall(r'idx:[A-Z0-9-]+|sc:[^ )]+|fc:[^ )]+', ' '.join(lines))}",
            )
            show("reply", reply)
            if "result" in reply:
                return reply["result"]
            st, p = reply.get("status"), primary(reply)
            if st in ("walked_away", "no_bid") or not p:
                return self.client.send_message(self.sid, SUP, {"action": {"type": "walk_away"}}).get("result", {})
            if st in ("agreed", "final_offer"):
                return self.close(reply, f"{st} {p['terms'].get('unit_price')}")
            price = p["terms"]["unit_price"]
            held = held + 1 if last_price is not None and price >= last_price else 0
            last_price = price
            if held >= 1 and k >= 1:  # it stopped moving: no more facts to spend, go to the hair
                break
        # the hair: one ask just under its grid counter (it agrees at our price once that clears its line)
        hair = round(last_price - a.hair, 2)
        reply = self.send(self.message(hair, ["Thank you. We are ready to sign today on these terms."], False))
        self.note(k="hair", its=last_price, do=f"ask {hair}@300/0 (its counter - {a.hair:.2f})")
        show("reply", reply)
        if "result" in reply:
            return reply["result"]
        st = reply.get("status")
        if st in ("walked_away", "no_bid"):
            return self.client.send_message(self.sid, SUP, {"action": {"type": "walk_away"}}).get("result", {})
        return self.close(reply, f"{st} after the hair")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--hold", choices=["timeout", "none"], default="timeout")
    ap.add_argument("--ask1", type=float, default=42.77)
    ap.add_argument("--ask2", type=float, default=43.57)
    ap.add_argument("--ask3", type=float, default=44.01)
    ap.add_argument("--hair", type=float, default=0.08, help="the last ask = its standing price minus this")
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
        print(f"hold={args.hold} asks={args.ask1}/{args.ask2}/{args.ask3} hair=-{args.hair}\n")
        for k, (ask, lines, attach) in enumerate(g.rounds()):
            m = g.message(ask, lines, attach)
            print(f"--- ask {k + 1} {[x['terms'] for x in m['term_sheets']]} att={len(m.get('attachments') or [])}")
            print(m["body"] + "\n")
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
    label = f"p11_hold {args.hold} {args.ask1}/{args.ask2}/{args.ask3} hair-{args.hair}"
    row = {
        "exp": "P11-hold",
        "case": "P11",
        "session": game.sid,
        "switches": [f"hold={args.hold}", f"hair={args.hair}"],
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
    sc = f"{m['score']:.4f}" if m["score"] is not None else "no score"
    with (ROOT / "notes" / "quota_log.md").open("a", encoding="utf-8") as f:
        f.write(
            f"| {row['time']} | Parth | P11 | {label} {row['commit']} / scripted | {sc}"
            f"{' - CRASHED: ' + error[:80] if error else ''} | {game.sid} |\n"
        )
    terms = final.get("terms") or {}
    print(
        f"\nP11 {game.sid}: score {sc}  deal {terms.get('unit_price')} @ {terms.get('ppm_commitment')} ppm / "
        f"EUR {terms.get('chargeback_eur_per_complaint')}  end {final.get('end_reason') or ''}   (team best: 0.8019)"
    )
    for r in game.notes:
        print("  ", r)
    print(f"quota left: {run_plan.quota_left(client)}")


if __name__ == "__main__":
    main()
