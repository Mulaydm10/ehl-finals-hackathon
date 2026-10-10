"""P04 record attempt (Parth): steer the supplier's PRIMARY sheet to 45 days, try for EUR 4.87 at 30 days.

    cd tacto/starter-kit
    uv run python ../../tools/experiments/p04_record.py --sim        # offline against the fitted supplier, no quota
    uv run python ../../tools/experiments/p04_record.py              # one live P04 game (archives + logs it)
    uv run python ../../tools/experiments/p04_record.py --safe       # never send its alternative back after final
    uv run python ../../tools/experiments/p04_record.py --main30     # its primary on 30 d (after a game showed 4.87)
    uv run python ../../tools/experiments/p04_record.py --probe      # pay-on-time promise, then probe 4.87 @ 30 d

Why (evidence: analysis/cases/P04.md section 9 - live games d3050f951dc2c45b, 53f2239cea14a247, 5f80eb75c793f352):
- One cent is 0.17 score here (span EUR 2,317 on 40,000 pieces), so the cent rounding decides the score.
- The supplier prices every payment term from ONE value target at its own cash rate (6.9-7.7 %, fitted on all
  its sheets) and rounds UP to the cent. At its floor (= the C_best floor): 14 d 4.86 (0.815), 30 d 4.88 (0.766)
  or 4.87 (0.940 - only if its rate is >= 7.5 %), 45 d 4.89 (0.874), 60 d 4.91 (0.810), 90 d 4.94 (0.860, our
  old best). 4.88 @ 45 d and 4.93 @ 90 d cost less than C_best: it can never take them.
- Only its PRIMARY sheet can be accepted by id ('-a' alternatives are refused: 422), and its primary is always
  on the payment term of our highest-priced sheet (8 of 8 messages) -> we send exactly two sheets, 45 d priced
  above 30 d, so the primary is 45 d and the alternative shows its 30-day price.
- It reaches its floor in the round it says final_offer, and it counters (instead of holding) when our offer is
  well below its target (d305 R3: counter at a 0.9 % gap; 5f80 R3: held at 0.1-0.2 %) -> our sheets stay >= 0.6 %
  below it.
Plan: one new verified fact per round, +2-3 cents per round; accept its primary at final_offer (4.89 @ 45 d =
0.874). A 30-day sheet <= EUR 4.87 (0.940): its primary -> accept; its alternative in an open round -> send exactly
that sheet (it agrees); its alternative in its final -> one clean "we accept your alternative" message, no new
asks (agreed 4 of 5 in our games; the one walk came with new asks and data, P08 1f27ac1b2856c285).

--probe (after 6ecd1862cf32d939 = 0.874 and 6ed05f043e2164b0 = 0.766): we never once SENT 4.87 @ 30 d in an open round -
we only read its own counters. A supplier agrees to a sheet below its standing offer when the sheet clears its floor
(P11 b1f94bfec7792ffb: standing 45.50, our probe 45.10 agreed). Round 1: no data (5 of 5 "does not change our
calculation", and data in round 2 brought its final a round earlier: 53f2, 6ecd, 6ed0 vs d305, 5f80), but our own
record, true and from invoices.csv: we paid 84 % of its invoices late (3.6 days) - promised on time from now, worth
~EUR 0.003 a piece to it. Rounds 2 and 3: probe every sheet that beats 0.874, each one cent under its floor price on
that term - 4.93 @ 90 d (1.0; its 90-day floor price is 4.9319, so a cut of 0.002 is enough), 4.90 @ 60 d (0.982),
4.87 @ 30 d (0.940). Not taken: ask for 4.89 @ 45 (its own 45-day floor price, 0.874). Never 4.89 @ 45 next to the
probe: it would pick the sheet worth more to it. Risk: a final during the probe holds its primary on 90 d (4.94 =
0.860 or worse) - the board keeps our 0.874 either way.
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

from arena_kit.cost import complete_offer, total_cost  # noqa: E402
from arena_kit.docs import standard_terms  # noqa: E402
from arena_kit.play import latest, moves_left  # noqa: E402

CASE_ID, SUPPLIER = "case:P04", "sup:70620"
MONTHS = 36
RECORD = (4.87, 30)  # 0.940
FLOOR_45 = (4.89, 45)  # 0.874 - its 45-day price at its floor
FACTS = {
    "ppi": "Producer prices for bearings changed -0.1% from 2026-04 to 2026-05 "
    "(idx:PPI-C2815@2026-04, idx:PPI-C2815@2026-05).",
    "po": "Our recent orders for the 6306-2Z C3 were at EUR 4.39 per piece "
    "(po:4500014329-10, po:4500014389-10, po:4500014467-10).",
    "fc": "Our demand forecast for this bearing is up +4.2% (fc:360020@2026-09).",
    "lci": "Labour costs in manufacturing changed -0.3% from 2025-10 to 2026-01 "
    "(idx:LCI-C@2025-10, idx:LCI-C@2026-01).",
    "quote": "Your own quotation of 20 September for this bearing is at EUR 4.63 (quote:7200019).",
}


def late_payment_line(supplier=SUPPLIER, months=12):
    """Our own payment record with the supplier (invoices.csv, last `months` before its latest invoice): true, checked
    here, not a data claim (invoices are not citable facts)."""
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
    return (
        f"Straight talk: over the last {months} months we paid {100 * len(late) / len(days):.0f}% of your invoices "
        f"late, on average {sum(late) / len(late):.1f} days after the due date. That is on us, and it ends with this "
        "contract: every invoice paid on the due date."
    )


FACTS["latepay"] = late_payment_line()
# per message we send: ((price, days) of the sheet we price HIGHER - its primary goes there -, (price, days) of the
# other sheet, facts); the last line repeats. Every sheet stays below its floor price on that term (4.89 / 4.87).
PLAN = [
    ((4.79, 45), (4.77, 30), ["ppi", "po", "fc"]),
    ((4.82, 45), (4.80, 30), ["lci", "quote"]),
    ((4.84, 45), (4.82, 30), []),
    ((4.85, 45), (4.83, 30), []),
    ((4.86, 45), (4.84, 30), []),
]
# --main30 (once a game has shown 4.87 @ 30 d at its floor): its primary on 30 d -> 4.87 @ 30 d is accepted by id
PLAN_MAIN30 = [
    ((4.78, 30), (4.76, 45), ["ppi", "po", "fc"]),
    ((4.80, 30), (4.79, 45), ["lci", "quote"]),
    ((4.82, 30), (4.81, 45), []),
    ((4.83, 30), (4.82, 45), []),
    ((4.84, 30), (4.83, 45), []),
]
# --probe: no data, our pay-on-time promise in round 1; rounds 2-3 the probe (see docstring)
PLAN_PROBE = [((4.84, 90), (4.80, 30), ["latepay"])]
# every sheet that beats 0.874, each one cent under its floor price on that term: 4.93 @ 90 d = 1.0 (0.19 cents
# under its 90-day floor price 4.9319), 4.90 @ 60 d = 0.982, 4.87 @ 30 d = 0.940. The highest price (90 d) carries
# its primary.
PROBE = [(4.93, 90), (4.90, 60), (4.87, 30)]
LOCK_FROM = 6  # from our 6th message on, take its primary if it is at least the 45-day floor price
SIGN = "Kind regards\nPurchasing, Hollerau Pumpenwerke"


class P04RecordAgent:
    def __init__(self, send_alternative_back=True, plan=PLAN, probe=False):
        self.send_alternative_back, self.plan, self.probe, self.probes = send_alternative_back, plan, probe, 0
        self.asked = None  # the sheet we asked for after its final_offer (asked once)
        self.notes = []

    def sheet(self, case, price, days):
        return complete_offer(case, {"unit_price": price, "payment_days": days, "contract_months": MONTHS})

    def decide(self, case, threads):
        sid = next(iter(threads))
        events = threads[sid]
        sup, std = latest(events), standard_terms(events)
        k = sum(m.get("from") == "buyer" for m in events)  # messages sent so far
        sheets = [s for s in sup.get("term_sheets") or [] if (s.get("terms") or {}).get("unit_price") is not None]
        primary = sheets[0] if sheets and sheets[0].get("term_sheet_id") else None
        cost = lambda t: total_cost(case, complete_offer(case, t), std)  # noqa: E731
        c_record = cost(self.sheet(case, *RECORD))
        c_floor45 = cost(self.sheet(case, *FLOOR_45))
        status = sup.get("status")
        self.notes.append(
            {
                "k": k,
                "status": status,
                "sheets": [
                    (s["terms"].get("unit_price"), s["terms"].get("payment_days"), round(cost(s["terms"]), 2))
                    for s in sheets
                ],
            }
        )

        def accept(why):
            self.notes[-1]["do"] = f"accept {primary['term_sheet_id']} ({why})"
            return {
                "supplier_id": sid,
                "message": {"action": {"type": "accept", "term_sheet_id": primary["term_sheet_id"]}},
            }

        if primary and (status == "agreed" or cost(primary["terms"]) <= c_record + 0.01):
            return accept("agreed" if status == "agreed" else "record sheet")
        alts = sorted(sheets[1:], key=lambda s: cost(s["terms"]))
        if status == "final_offer" or moves_left(case, events) <= 1:
            # its last word: accept the primary - unless an alternative is far cheaper for us (>= EUR 100 = 0.04)
            if (
                self.send_alternative_back
                and not self.asked
                and alts
                and primary
                and moves_left(case, events) > 1
                and cost(alts[0]["terms"]) <= cost(primary["terms"]) - 100
            ):
                self.asked = alts[0]["terms"]
                return self.ask_for(case, sid, alts[0]["terms"], final=True)
            if primary:
                return accept("final_offer" if status == "final_offer" else "last move")
            return {"supplier_id": sid, "message": {"action": {"type": "walk_away"}}}
        if self.asked:  # we asked for one of its own sheets and it has not agreed yet: hold it, never offer less
            return self.ask_for(case, sid, self.asked, final=False)
        record = next((s for s in alts if cost(s["terms"]) <= c_record + 0.01), None)
        if record:  # its 30-day alternative is at the record price in an open round: ask for exactly it
            self.asked = record["terms"]
            return self.ask_for(case, sid, record["terms"], final=False)
        at_floor45 = primary and cost(primary["terms"]) <= c_floor45 + 0.01
        if (
            self.probe and k >= 1
        ):  # from our 2nd message: the record sheets, twice; then close on the 45-day floor price
            if self.probes < 2:
                self.probes += 1
                return self.probe_offer(case, sid)
            if at_floor45:
                return accept("probe not taken - its primary is the 45-day floor price")
            self.asked = self.sheet(case, *FLOOR_45)  # it can take 4.89 @ 45 d (its own floor price): ask for it
            return self.ask_for(case, sid, self.asked, final=False)
        if k + 1 >= LOCK_FROM and at_floor45:
            return accept("lock the 45-day floor price")
        high, low, facts = self.plan[min(k, len(self.plan) - 1)]
        return self.offer(case, sid, k, high, low, facts)

    def probe_offer(self, case, sid):
        opts = "; ".join(f"EUR {p:.2f} with {d} days net" for p, d in PROBE)
        body = (
            f"Dear Mr Gruber,\n\nthank you - we are close. We can sign today on any of these: {opts} - each for 36 "
            f"months and 20,000 pieces a year, every invoice paid on the due date. The term sheets are attached."
            f"\n\n{SIGN}"
        )
        self.notes[-1]["do"] = "probe " + " / ".join(f"{p}@{d}" for p, d in PROBE)
        return {
            "supplier_id": sid,
            "message": {
                "subject": "Renewal of framework agreement 4600070620 - 6306-2Z C3",
                "body": body,
                "term_sheets": [{"terms": self.sheet(case, p, d)} for p, d in PROBE],
            },
        }

    def offer(self, case, sid, k, high, low, facts):
        lines = [FACTS[f] for f in facts]
        if k == 0:
            head = (
                "thank you for your offer. We would like to renew on a multi-year basis: a binding 20,000 pieces "
                "a year for 36 months - the kind of agreement your colleagues told us changes prices."
            )
        elif facts:
            head = "thank you for your revised offer."
        else:
            head = "thank you. To close this quickly we move again."
        body = (
            f"Dear Mr Gruber,\n\n{head}\n\n"
            + ("\n".join(lines) + "\n\n" if lines else "")
            + f"We propose the two attached term sheets: EUR {high[0]:.2f} at {high[1]} days net, "
            f"or EUR {low[0]:.2f} at {low[1]} days net, both for 36 months and 20,000 pieces a year.\n\n{SIGN}"
        )
        self.notes[-1]["do"] = f"offer {high[0]}@{high[1]} / {low[0]}@{low[1]} + {facts}"
        return {
            "supplier_id": sid,
            "message": {
                "subject": "Renewal of framework agreement 4600070620 - 6306-2Z C3",
                "body": body,
                "term_sheets": [{"terms": self.sheet(case, *high)}, {"terms": self.sheet(case, *low)}],
            },
        }

    def ask_for(self, case, sid, terms, final):
        t = complete_offer(case, terms)
        what = (
            f"EUR {t['unit_price']:.2f} per piece, {t['payment_days']} days net, {t['contract_months']} months, "
            f"20,000 pieces a year"
        )
        lead = (
            "thank you for your final offer. We accept your alternative as you proposed it"
            if final
            else "thank you - your option works for us"
        )
        self.notes[-1]["do"] = f"ask for {t['unit_price']}@{t['payment_days']} ({'after final' if final else 'open'})"
        return {
            "supplier_id": sid,
            "message": {
                "subject": "Renewal of framework agreement 4600070620 - 6306-2Z C3",
                "body": f"Dear Mr Gruber,\n\n{lead}: {what}. "
                f"The term sheet is attached for your confirmation.\n\n{SIGN}",
                "term_sheets": [{"terms": t}],
            },
        }


# ---------- offline: the supplier as fitted on the three live games (no arena calls) ----------
def simulate(rate, share=0.57, walk_after_final=0.0, verbose=True, agent=None, floor_agree=False, patience=1, cut=0.0):
    """The P04 supplier as measured: one value target T (cash at 30 d, money at `rate`), every sheet = T priced at
    its term and rounded UP to the cent; T_new = max(S, T - share x (T - our best value)); final_offer when it
    reaches S or moves less than a cent; agrees when one of our sheets is worth >= T_new; after final_offer it
    agrees to a sheet worth >= S (or walks with probability `walk_after_final`). S = the C_best floor.
    floor_agree: in open rounds it agrees to any sheet worth >= S (P11's probe). patience: no final_offer before that
    round. cut: what our pay-on-time promise takes off its floor (EUR a piece, value at 30 d)."""
    import random

    probe = json.loads((ROOT / "analysis/cases/openings/P04.json").read_text(encoding="utf-8"))
    case = next(
        c
        for c in json.loads((ROOT / "datasets/cases_practice.json").read_text(encoding="utf-8"))
        if c["case_id"] == CASE_ID
    )
    res = probe["result"]
    c_open, c_best = res["c_open"], res["c_best"]
    fac = lambda d: 1 - rate * (d - 30) / 360  # noqa: E731
    S = (c_best - 570) / 40000 / (1 + 0.08 * (60 - 90) / 360) * fac(90) - cut  # the floor (90 d optimal, rate < 8 %)
    value = lambda t: t["unit_price"] * fac(t["payment_days"])  # noqa: E731
    price = lambda T, d: math.ceil(round(T / fac(d) * 100, 6)) / 100  # noqa: E731
    events = [dict(m) for m in probe["threads"][SUPPLIER]]
    std = standard_terms(events)
    agent = agent or P04RecordAgent()
    T, final, n = 4.96, False, 0
    while n < 12:
        d = agent.decide(case, {SUPPLIER: events})
        msg = d["message"]
        if msg.get("action"):
            if msg["action"]["type"] != "accept":
                return 0.0, "walked away", agent
            t = next(
                s["terms"]
                for s in latest(events)["term_sheets"]
                if s["term_sheet_id"] == msg["action"]["term_sheet_id"]
            )
            sc = min(1.0, max(0.0, (c_open - total_cost(case, t, std)) / (c_open - c_best)))
            return round(sc, 4), f"deal {t['unit_price']} @ {t['payment_days']} d", agent
        n += 1
        ours = [complete_offer(case, s["terms"]) for s in msg["term_sheets"]]
        best = max(ours, key=value)
        if final:
            ok = [t for t in ours if value(t) >= S - 1e-9]
            if not ok or random.random() < walk_after_final:
                return 0.0, "it walked after final_offer", agent
            reply = {"status": "agreed", "sheets": [max(ok, key=value)]}
        else:
            T_new = max(S, T - share * (T - value(best)))
            ok = [t for t in ours if value(t) >= (S if floor_agree else T_new) - 1e-9]
            if ok:
                reply = {"status": "agreed", "sheets": [max(ok, key=value)]}
            else:
                final = n >= patience and (T_new <= S + 1e-9 or T - T_new < 0.01 * fac(30) * 0.5)
                T = T_new
                main = max(ours, key=lambda t: t["unit_price"])
                rest = [t for t in ours if t["payment_days"] != main["payment_days"]][:1]
                reply = {
                    "status": "final_offer" if final else "open",
                    "sheets": [{**t, "unit_price": price(T, t["payment_days"])} for t in [main] + rest],
                }
        sheets = [
            {"term_sheet_id": f"offer:70620-{n}" + ("-a" if i else ""), "terms": t}
            for i, t in enumerate(reply["sheets"])
        ]
        if verbose:
            print(
                f"  r{n}: ours {[(t['unit_price'], t['payment_days']) for t in ours]} -> {reply['status']} "
                f"{[(t['unit_price'], t['payment_days']) for t in reply['sheets']]}  (T {T:.4f}, floor {S:.4f})"
            )
        events += [
            {**msg, "from": "buyer"},
            {"from": "sales@70620", "status": reply["status"], "body": "", "term_sheets": sheets},
        ]
    return 0.0, "no end", agent


def play_live(args):
    import run_plan  # archive(), measure(), quota_left(), git_commit() - same records as the experiment runner

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
    table, error = RemoteTable(client), None
    agent = P04RecordAgent(
        not args.safe, PLAN_PROBE if args.probe else PLAN_MAIN30 if args.main30 else PLAN, args.probe
    )
    try:
        result = play(table, CASE_ID, agent)
    except Exception as e:  # never lose the game: record our own session
        if not table.session_id:
            raise
        error, result = f"{type(e).__name__}: {e}", run_plan.wait_for_end(client, table.session_id)
    run_plan.archive(client, table.session_id, CASE_ID)
    m = run_plan.measure(cases[CASE_ID], result)
    flags = [f for f in ("safe", "main30", "probe") if getattr(args, f)]
    row = {
        "exp": "P04-record",
        "case": "P04",
        "session": table.session_id,
        "switches": flags,
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
            f"| {row['time']} | Parth | P04 | p04_record {row['commit']}{''.join(' --' + f for f in flags)} / scripted"
            f" | {sc}{' - CRASHED: ' + error[:80] if error else ''} | {table.session_id} |\n"
        )
    print(
        f"\nP04 {table.session_id}: score {sc}  deal {(result.get('terms') or {}).get('unit_price')} @ "
        f"{(result.get('terms') or {}).get('payment_days')} d"
        "   (record to beat: 0.87; 4.87@30 = 0.940, 4.89@45 = 0.874)"
    )
    for r in agent.notes:
        print(f"  after our msg {r['k']}: {r['status']:12} {r['sheets']}  -> {r.get('do')}")
    print(f"quota left: {run_plan.quota_left(client)}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--sim", action="store_true", help="offline, against the fitted supplier at several cash rates")
    ap.add_argument("--safe", action="store_true", help="never send its alternative back after final_offer")
    ap.add_argument("--main30", action="store_true", help="its primary on 30 days (once a game showed 4.87 @ 30 d)")
    ap.add_argument(
        "--probe", action="store_true", help="pay-on-time promise, then probe 4.87 @ 30 d at its 45-day floor"
    )
    ap.add_argument("--reserve", type=int, default=40)
    a = ap.parse_args()
    if a.sim:
        for rate in (0.0693, 0.0720, 0.0752, 0.0760, 0.0769):
            print(f"supplier cash rate {rate:.4f}:")
            plan = PLAN_PROBE if a.probe else PLAN_MAIN30 if a.main30 else PLAN
            sc, end, _ = simulate(
                rate,
                share=0.3,
                agent=P04RecordAgent(not a.safe, plan, a.probe),
                floor_agree=a.probe,
                patience=3 if a.probe else 1,
            )
            print(f"  -> score {sc}  ({end})\n")
    else:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        play_live(a)
