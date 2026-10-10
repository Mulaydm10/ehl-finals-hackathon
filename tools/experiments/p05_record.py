"""P05 record attempt (Parth): the RFQ for the HX pump shaft - walk Fuchsreiter (70250) down to its floor.

    cd tacto/starter-kit
    uv run python ../../tools/experiments/p05_record.py --sim    # offline against the 3 bidders as measured, no quota
    uv run python ../../tools/experiments/p05_record.py          # one live P05 game (archives + logs it)

Evidence (all 10 archived P05 games + back offices; analysis in analysis/cases/P05.md section 9):
- C_best EUR 223,424 = Fuchsreiter at about EUR 26.26 @ 14 d (ppm 600: the cheapest quality cost). One cent = 0.001.
  Our best 0.614 = EUR 30.00 @ 14 d; EUR 28.00 = 0.82, 27.00 = 0.924 (the board's best, 0.92), 26.90 = 0.934,
  26.50 = 0.975.
- Fuchsreiter's first counter follows our ask (~70 % of the gap) plus "the buyer shows a much lower rival quote. I give
  half the step now and check the rest" (a rival >= ~10 % below its price; its own 36.00 opening rival did nothing):
  ask 29.17-30.25 -> 31.00; ask 25.54 (d9af85e000ab3d4d) -> 28.00, then "Checked: give the rest of the step" ->
  27.50 @ 30 d / 27.00 @ 14 d (that final was lost to our crash's timeouts, not to the anchor). It agrees to our own
  price when it clears its line (30.25, 30.83 agreed in 4 games) - so our asks can beat its 0.50 price grid.
- It is cash-tight ("cash is always tight", letter 18 Aug: "invoices are overdue again ... otherwise we will have to
  review our conditions", 4 Sep: "pay within 10 days? In return we would grant a cash discount") and we paid 93 % of
  its invoices late, 11.5 days on average (invoices.csv) -> 14 days net and an honest on-time commitment.
- Only its primary sheet can be accepted by id and it puts the primary on our sheet's terms -> we send 14 d only.
- No move from us = no move from it, and an identical repeat after a hold made P04's supplier walk -> every ask
  moves up; we never resend the same price.
- Live 9ce672fffbf931a7 (0.820): ask 23.80 without the schedule -> 30.50 -> 28.50 -> final 28.00. The one game with a
  monthly call-off schedule attached (d9af, ask 25.54) got 28.00 at once ("Got the call-off schedule ... so I'm dropping
  the price" - Dralveck, e9ea): it goes in every round-1 message. After round 1 it answers ~half of each move we make
  and gives "the rest of the step" once -> bigger early moves.
- Live 1ebd6e0eb14313c8 (0.820, schedule attached, asks 24.50 -> 26.00 -> 26.50): the SAME path, 30.50 -> 28.50 ->
  28.00 final - the schedule was not it. Both runs fit one rule: first counter ~30.50 whatever we ask, then -1.00 (the
  rest of the step) and ~0.75 x each move we make, final at its 3rd reply. Final ~ 29.50 - 0.75 x (our total move) ->
  a low anchor and ONE big move: 21.00 -> 26.40 meets its floor (~26.26) at our price. Dralveck followed the same path
  (36.00 -> 30.50 -> 28.00) and WALKED after two +0.30 moves: never tiny moves.
- Dralveck (70210) ends ~30.00 and Hrvelec (70240) ~32.00 @ 42 d: kept going as backups, never accepted while
  Fuchsreiter is in.
"""

import argparse
import datetime
import json
import math
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KIT = ROOT / "tacto" / "starter-kit"
sys.path.insert(0, str(KIT))

from arena_kit.cost import complete_offer, must_haves_ok, total_cost  # noqa: E402
from arena_kit.docs import standard_terms  # noqa: E402
from arena_kit.play import latest, live_threads  # noqa: E402

CASE_ID = "case:P05"
TARGET, DRALVECK, HRVELEC = "sup:70250", "sup:70210", "sup:70240"
NAMES = {TARGET: "Ms Fuchsreiter", DRALVECK: "Mr Dralveck", HRVELEC: "Ms Procházková"}
# our asks, message by message (the last repeats +0.10 a round so we always move)
ASKS = {
    TARGET: [21.00, 26.40, 26.80, 26.95],  # live: first counter ~30.50 whatever we ask; then -1.00 + ~0.75 x our move
    DRALVECK: [21.50, 26.60, 26.90, 27.10],  # same play; +0.30 moves made it walk (1ebd6e0eb14313c8)
    HRVELEC: [24.00, 27.50, 28.50, 29.50],
}
LEAD = {TARGET: 28, DRALVECK: 28, HRVELEC: 42}  # its standard 28 d; Hrvelec's 52 d breaks our must-have (<= 42)
TAKE_AT = 26.95  # the board's best is 0.92 = 27.00 @ 14 d: any open price below it at 14 d we take at once
MUCH_LOWER = 0.90  # a rival at <= 90 % of its price drew "much lower rival quote" (36.00 vs 38.50 did not)
SIGN = "Kind regards\nPurchasing, Hollerau Pumpenwerke"


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
    """The monthly call-off schedule the agent attached in d9af85e000ab3d4d (4,200 a year = 350 a month, 24 months)."""
    import base64

    y, m = start
    rows = ["month,quantity"] + [
        f"{y + (m - 1 + i) // 12}-{(m - 1 + i) % 12 + 1:02d},{per_month}" for i in range(months)
    ]
    return {
        "name": "call_off_schedule.csv",
        "type": "csv",
        "content_b64": base64.b64encode(("\n".join(rows) + "\n").encode()).decode(),
    }


class P05RecordAgent:
    def __init__(self):
        self.focus = None  # set by play(): the bidders whose reply is in
        self.k = {}  # messages sent per bidder
        self.asked = {}  # the price we last asked per bidder (we never resend it)
        self.cited = {}  # rival offer ids cited per bidder (each counts once per supplier)
        self.notes = []
        share, days = late_payment(TARGET)
        self.late_line = (
            f"Straight talk on payment: over the last 12 months we paid {share * 100:.0f}% of your invoices "
            f"late, on average {days:.1f} days after the due date - your letter of 18 August was right. That "
            "ends with this contract: 14 days net, every invoice paid on the due date."
        )

    # ---- the numbers
    def cost(self, case, sid, events, terms):
        return total_cost(case, complete_offer(case, terms), standard_terms(events))

    def primary(self, events):
        sheets = [s for s in latest(events).get("term_sheets") or [] if (s.get("terms") or {}).get("unit_price")]
        return sheets[0] if sheets and sheets[0].get("term_sheet_id") else None

    def offer_price(self, events):
        p = self.primary(events)
        return p["terms"]["unit_price"] if p else None

    def best_valid(self, case, threads, sids):
        """(C, sid, sheet) of the cheapest standing primary sheet that keeps the must-have, among `sids`."""
        best = None
        for sid in sids:
            ev = threads[sid]
            p = self.primary(ev)
            if p and must_haves_ok(case, complete_offer(case, p["terms"]), standard_terms(ev)):
                c = self.cost(case, sid, ev, p["terms"])
                if best is None or c < best[0]:
                    best = (c, sid, p)
        return best

    # ---- the decision
    def decide(self, case, threads):
        live = live_threads(threads)
        target_live = TARGET in live
        ready = [s for s in (self.focus or live) if s in live] or live
        # 1. close: any bidder that agreed, said final or stands at the take-price (14 d) - take the cheapest of those,
        #    once Fuchsreiter is among them or one of them beats Fuchsreiter at the take-price
        closable = []
        for sid in live:
            ev = threads[sid]
            st, p = latest(ev).get("status"), self.primary(ev)
            if not p or not must_haves_ok(case, complete_offer(case, p["terms"]), standard_terms(ev)):
                continue
            at_take = p["terms"]["unit_price"] <= TAKE_AT and p["terms"].get("payment_days") == 14
            if st in ("agreed", "final_offer") or at_take:
                closable.append((self.cost(case, sid, ev, p["terms"]), sid, p, st))
        if closable:
            c_take = self.cost(
                case,
                TARGET,
                threads[TARGET],
                {"unit_price": TAKE_AT, "payment_days": 14, "lead_time_days": LEAD[TARGET]},
            )
            best = min(closable, key=lambda x: x[0])
            if not target_live or any(x[1] == TARGET for x in closable) or best[0] <= c_take:
                return self.accept(best[1], best[2], f"{best[3]} {best[2]['terms']} - cheapest of {len(closable)}")
        if not target_live:  # it has gone: take the cheapest valid standing sheet before the others go too
            best = self.best_valid(case, threads, live)
            if best:
                return self.accept(best[1], best[2], "Fuchsreiter gone - cheapest valid backup")
        # 2. answer a bidder whose reply is in - Fuchsreiter first
        sid = TARGET if TARGET in ready else ready[0]
        return self.counter(case, threads, sid)

    def accept(self, sid, sheet, why):
        self.notes.append({"sid": sid, "do": f"accept {sheet['term_sheet_id']} ({why})"})
        return {"supplier_id": sid, "message": {"action": {"type": "accept", "term_sheet_id": sheet["term_sheet_id"]}}}

    def counter(self, case, threads, sid):
        events = threads[sid]
        k = self.k.get(sid, 0)
        st, its = latest(events).get("status"), self.offer_price(events)
        if st == "final_offer" and sid != TARGET:  # a backup's last word: keep its quote standing, push nothing
            self.k[sid] = k + 1
            self.notes.append({"sid": sid, "k": k, "status": st, "its": its, "do": "hold note (no sheet)"})
            return {
                "supplier_id": sid,
                "message": {
                    "subject": "RFQ pump shaft HX (part:320070)",
                    "body": f"Dear {NAMES[sid]},\n\nthank you for your offer. We are completing the comparison "
                    f"and will come back to you shortly.\n\n{SIGN}",
                },
            }
        plan = ASKS[sid]
        ask = plan[k] if k < len(plan) else round(plan[-1] + 0.10 * (k - len(plan) + 1), 2)
        if self.asked.get(sid) is not None and ask <= self.asked[sid]:
            ask = round(self.asked[sid] + 0.10, 2)  # always a move
        if its is not None and ask >= its:  # never ask above its own price: take its price instead
            ask = its
        # a rival at least 10 % below its current price, not cited to it before (a rival's offer counts once each)
        rival = None
        for other in threads:
            if other == sid:
                continue
            for s in latest(threads[other]).get("term_sheets") or []:
                oid, price = s.get("term_sheet_id"), (s.get("terms") or {}).get("unit_price")
                if oid and price and its and price <= MUCH_LOWER * its and oid not in self.cited.get(sid, set()):
                    if rival is None or price < rival[1]:
                        rival = (oid, price)
        lines = []
        if k == 0:
            lines.append(
                "thank you for your offer. We are awarding the HX pump shaft (part:320070) for the series "
                "start in March 2027: 4,200 pieces a year, binding for 24 months."
            )
            if sid == TARGET:
                lines.append(self.late_line)
                lines.append("It is steady work for the second shift you told us has been on hold since spring.")
        else:
            lines.append("thank you for your reply. We move again.")
        if rival:
            self.cited.setdefault(sid, set()).add(rival[0])
            lines.append(f"We have an offer at EUR {rival[1]:.2f} per piece ({rival[0]}).")
        days = 14
        terms = complete_offer(case, {"unit_price": ask, "payment_days": days, "lead_time_days": LEAD[sid]})
        lines.append(
            f"We propose EUR {ask:.2f} per piece, {days} days net, {LEAD[sid]} days lead time (term sheet attached)."
        )
        self.k[sid], self.asked[sid] = k + 1, ask
        self.notes.append(
            {
                "sid": sid,
                "k": k,
                "status": st,
                "its": its,
                "do": f"ask {ask}@{days}/{LEAD[sid]}" + (f" + cite {rival[0]} {rival[1]}" if rival else ""),
            }
        )
        msg = {"subject": "RFQ pump shaft HX (part:320070)", "term_sheets": [{"terms": terms}]}
        if k == 0:  # d9af85e000ab3d4d: the only game with it - first counter 28.00 vs 30.50-31.00 without
            lines.append("Attached: our monthly call-off schedule for the full contract term.")
            msg["attachments"] = [call_off_schedule()]
            self.notes[-1]["do"] += " + call-off schedule"
        msg["body"] = f"Dear {NAMES[sid]},\n\n" + "\n\n".join(lines) + f"\n\n{SIGN}"
        return {"supplier_id": sid, "message": msg}


# ---------- offline: the bidders as measured live (9ce672fffbf931a7, 1ebd6e0eb14313c8; no arena calls) ----------
def simulate(floor_target=26.26, mirror=0.75, verbose=True, agent=None, patience=3):
    """Each bidder keeps an internal price p (shown on its 0.50 grid, rounded up). Round 1 with a much lower rival
    cited: p = 30.50 (Fuchsreiter and Dralveck alike, whatever we ask). Round 2: -1.00 (the rest of the step) and
    `mirror` x our move; later rounds: `mirror` x our move; never below its floor. It agrees when our ask >= p; final
    at its `patience`-th reply; it walks if our moves since round 1 add up to less than 1.00 by then (Dralveck).
    Fits both live runs exactly (mirror 0.75): 30.50 -> 28.50 -> 28.00."""
    probe = json.loads((ROOT / "analysis/cases/openings/P05.json").read_text(encoding="utf-8"))
    case = next(
        c
        for c in json.loads((ROOT / "datasets/cases_practice.json").read_text(encoding="utf-8"))
        if c["case_id"] == CASE_ID
    )
    res = probe["result"]
    threads = {sid: [dict(m) for m in ev] for sid, ev in probe["threads"].items()}
    floors = {TARGET: floor_target, DRALVECK: floor_target + 0.30, HRVELEC: 31.50}
    state = {sid: {"p": None, "n": 0, "ask": None, "first": None, "rival": False} for sid in threads}
    lead = {TARGET: 28, DRALVECK: 28, HRVELEC: 42}
    agent = agent or P05RecordAgent()
    grid = lambda x: math.ceil(round(x * 2, 6)) / 2  # noqa: E731
    for _ in range(60):
        agent.focus = set(live_threads(threads))
        d = agent.decide(case, threads)
        sid, msg = d["supplier_id"], d["message"]
        if msg.get("action"):
            t = next(
                s["terms"]
                for s in latest(threads[sid])["term_sheets"]
                if s["term_sheet_id"] == msg["action"]["term_sheet_id"]
            )
            c = total_cost(case, complete_offer(case, t), standard_terms(threads[sid]))
            sc = min(1.0, max(0.0, (res["c_open"] - c) / (res["c_open"] - res["c_best"])))
            return round(sc, 4), f"deal {sid} {t}", agent
        st = state[sid]
        st["n"] += 1
        sheets = msg.get("term_sheets") or []
        status, price = latest(threads[sid]).get("status"), None
        if sheets:
            ask = sheets[0]["terms"]["unit_price"]
            cited = "(offer:" in msg["body"]
            if st["p"] is None:  # its first counter
                st["p"], st["first"], st["rival"] = (30.50 if cited else 31.00), ask, cited
                if sid == HRVELEC:
                    st["p"] = 33.0
            else:
                move = max(0.0, ask - st["ask"])
                st["p"] -= (1.0 if st["rival"] and st["n"] == 2 else 0.0) + mirror * move
            st["p"] = max(st["p"], floors[sid])
            st["ask"] = ask
            if ask >= st["p"] - 1e-9:
                status, price = "agreed", ask
            elif st["n"] >= patience and ask - st["first"] < 1.0:
                status = "walked_away"
            else:
                status, price = ("final_offer" if st["n"] >= patience else "open"), grid(st["p"])
        else:
            price = latest(threads[sid])["term_sheets"][0]["terms"]["unit_price"]
        oid = f"offer:{sid.split(':')[1]}-{st['n']}"
        reply = {
            "from": f"sales@{sid}",
            "status": status,
            "body": "",
            "term_sheets": []
            if status == "walked_away"
            else [
                {"term_sheet_id": oid, "terms": {"unit_price": price, "payment_days": 14, "lead_time_days": lead[sid]}}
            ],
        }
        if verbose:
            print(f"  {sid}: ours {[x['terms']['unit_price'] for x in sheets] or 'note'} -> {status} {price}")
        threads[sid] += [{**msg, "from": "buyer"}, reply]
    return 0.0, "no end", agent


def play_live(args):
    import run_plan  # archive(), measure(), quota_left(), git_commit(), wait_for_end()

    from arena_kit.cli import load_env
    from arena_kit.client import ArenaClient
    from arena_kit.play import RemoteTable, play

    os.chdir(KIT)
    load_env(".env")
    client = ArenaClient()
    left = run_plan.quota_left(client)
    if left is not None and left <= args.reserve:
        sys.exit(f"practice quota left {left} <= reserve {args.reserve}: not playing")
    cases = {c["case_id"]: c for c in client.cases("practice")}
    table, agent, error = RemoteTable(client), P05RecordAgent(), None
    try:
        result = play(table, CASE_ID, agent)
    except Exception as e:  # never lose the game: record our own session
        if not table.session_id:
            raise
        error, result = f"{type(e).__name__}: {e}", run_plan.wait_for_end(client, table.session_id)
    run_plan.archive(client, table.session_id, CASE_ID)
    m = run_plan.measure(cases[CASE_ID], result)
    row = {
        "exp": "P05-record",
        "case": "P05",
        "session": table.session_id,
        "switches": [],
        "commit": run_plan.git_commit(),
        "model": "scripted (no model)",
        "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        **m,
        "rounds": agent.notes,
    }
    if error:
        row.update(error=error, end_reason=result.get("end_reason"))
    with (ROOT / "analysis" / "experiments" / "results.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    sc = f"{m['score']:.3f}" if m["score"] is not None else "no score"
    with (ROOT / "notes" / "quota_log.md").open("a", encoding="utf-8") as f:
        f.write(
            f"| {row['time']} | Parth | P05 | p05_record {row['commit']} / scripted | {sc}"
            f"{' - CRASHED: ' + error[:80] if error else ''} | {table.session_id} |\n"
        )
    terms = result.get("terms") or {}
    print(
        f"\nP05 {table.session_id}: score {sc}  deal {result.get('supplier_id')} {terms.get('unit_price')} @ "
        f"{terms.get('payment_days')} d / {terms.get('lead_time_days')} d   (our best before: 0.614)"
    )
    for r in agent.notes:
        print("  ", r)
    print(f"quota left: {run_plan.quota_left(client)}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--sim", action="store_true", help="offline against the bidders as measured")
    ap.add_argument("--reserve", type=int, default=40)
    a = ap.parse_args()
    if a.sim:
        for floor, mirror in ((26.26, 0.75), (26.26, 0.5), (26.26, 1.0), (27.00, 0.75), (26.26, 0.4)):
            print(f"Fuchsreiter floor {floor}, mirror {mirror}:")
            sc, end, _ = simulate(floor, mirror)
            print(f"  -> score {sc} ({end})\n")
    else:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        play_live(a)
