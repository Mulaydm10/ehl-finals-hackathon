"""Mine every archived practice game for supplier signals that generalise (Parth, 2026-10-11).

    python tools/experiments/mine_signals.py            # writes analysis/experiments/signals/replies.csv + prints stats

One row per supplier answer (e-mail or timeout round): case, supplier, round, status, its primary price, our best ask
before it, the moves on both sides, claim results, and text markers ("clarify internally", "the rest of the step",
"without movement", "cannot give up margin", "which figures", ...). The summary measures what each signal predicts.
"""

import csv
import glob
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "analysis" / "experiments" / "signals"
MARKERS = {
    "half_step": r"clarify this internally|come back to you on price|check the rest",
    "rest_step": r"clarified this internally|move further on the price|rest of the step",
    "no_move": r"[Ww]ithout movement",
    "margin": r"cannot give up margin",
    "cash": r"[Ff]aster payment|paid on time|fast money|getting paid",
    "final_words": r"final offer|letztes Angebot|last price|absolute limit|best possible proposal",
    "figures": r"Which figures|send us the data",
    "taken": r"took it into account|factored it in|we took that into account|took them into account",
    "no_change": r"does not change our calculation",
    "not_reality": r"not our reality",
    "material": r"received a lot of material",
    "match": r"match your other offer|beats your other offer",
}


def price(sheet):
    return ((sheet or {}).get("terms") or {}).get("unit_price")


def our_ask(msg):
    """Our most generous price in an e-mail (its primary follows the sheet worth most to it)."""
    ps = [price(s) for s in msg.get("term_sheets") or [] if price(s) is not None]
    return max(ps) if ps else None


def rows():
    for f in sorted(glob.glob(str(ROOT / "datasets/runs/*.json"))):
        g = json.loads(Path(f).read_text(encoding="utf-8"))
        d = g.get("detail") or {}
        case, sid = d.get("case_id"), Path(f).stem
        multi = len(g.get("threads") or {}) > 1
        for sup, th in (g.get("threads") or {}).items():
            msgs = th.get("messages") or []
            timeouts = {t.get("round"): t for t in th.get("timeouts") or []}
            # rebuild the round sequence: replies in order, timeouts slotted in by their round number
            seq, rnd = [], 0
            ours = None
            for m in msgs:
                if m.get("from") == "buyer":
                    if m.get("action"):
                        continue
                    ours = m
                    continue
                while rnd in timeouts and rnd > 0:  # timeout rounds before this reply
                    t = timeouts.pop(rnd)
                    seq.append(("timeout", rnd, None, t))
                    rnd += 1
                seq.append(("reply", rnd, ours, m))
                ours = None
                rnd += 1
            for r, t in sorted(timeouts.items()):
                seq.append(("timeout", r, None, t))
            prev_its, prev_ask = None, None
            for kind, r, ours_msg, m in seq:
                if kind == "timeout":
                    body, status = m.get("text") or "", m.get("status")
                    its = (m.get("terms") or {}).get("unit_price")
                    ask, claims = None, []
                else:
                    body, status = m.get("body") or "", m.get("status")
                    its = price((m.get("term_sheets") or [None])[0])
                    ask = our_ask(ours_msg) if ours_msg else None
                    claims = [c.get("result") for c in m.get("claim_results") or []]
                row = {
                    "case": (case or "").replace("case:", ""),
                    "session": sid,
                    "supplier": sup,
                    "rfq": multi,
                    "round": r,
                    "kind": kind,
                    "status": status,
                    "its": its,
                    "its_prev": prev_its,
                    "its_move": round(its - prev_its, 4) if its is not None and prev_its is not None else None,
                    "ask": ask,
                    "ask_prev": prev_ask,
                    "our_move": round(ask - prev_ask, 4) if ask is not None and prev_ask is not None else None,
                    "no_sheet": kind == "reply" and ours_msg is not None and not (ours_msg.get("term_sheets") or []),
                    "claims": "/".join(c for c in claims if c),
                    **{k: bool(re.search(rx, body)) for k, rx in MARKERS.items()},
                }
                yield row
                if its is not None:
                    prev_its = its
                if ask is not None:
                    prev_ask = ask


def grid_of(prices):
    ps = [p for p in prices if p is not None]
    for g in (1.0, 0.5, 0.25, 0.1, 0.05):
        if ps and all(abs(round(p / g) * g - p) < 1e-6 for p in ps):
            return g
    return 0.01


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    data = list(rows())
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "replies.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(data[0].keys()))
        w.writeheader()
        w.writerows(data)
    print(f"{len(data)} supplier answers from {len({r['session'] for r in data})} games -> {OUT / 'replies.csv'}\n")
    by_thread = defaultdict(list)
    for r in data:
        by_thread[(r["session"], r["supplier"])].append(r)

    # 1. half step -> what the next answer does, with and without a move from us
    nxt = Counter()
    gives = defaultdict(list)
    for seq in by_thread.values():
        for a, b in zip(seq, seq[1:]):
            if a["half_step"]:
                moved = "we moved" if (b["our_move"] or 0) > 0.001 else ("no sheet / timeout" if b["kind"] == "timeout" or b["no_sheet"] else "no move")
                nxt[(moved, "rest given" if b["rest_step"] else "no rest", b["status"])] += 1
                if b["its_move"] is not None:
                    gives[moved].append(-b["its_move"])
    print("1. after 'clarify internally' (half step), the next answer:")
    for k, v in sorted(nxt.items(), key=lambda x: -x[1]):
        print(f"   {v:3d}  {k}")
    for k, v in gives.items():
        print(f"   its next cut when {k}: n={len(v)} mean {sum(v) / len(v):.2f}  {sorted(round(x, 2) for x in v)}")

    # 2. agreed at OUR price below its last counter (its counters rounded to a grid)
    print("\n2. agreed at our ask below its last counter:")
    agreed_below = []
    for seq in by_thread.values():
        grid = grid_of([r["its"] for r in seq if r["status"] != "agreed"])
        for r in seq:
            if r["status"] == "agreed" and r["its_prev"] is not None and r["its"] is not None and r["its"] < r["its_prev"] - 1e-6:
                agreed_below.append((r["case"], grid, r["its_prev"], r["its"], round(r["its_prev"] - r["its"], 2)))
    for x in sorted(agreed_below):
        print(f"   {x[0]} grid {x[1]}: counter {x[2]} -> agreed {x[3]} (offset {x[4]})")
    print(f"   {len(agreed_below)} agreements below the counter")

    # 3. grids per case (non-agreed prices)
    print("\n3. price grid of its own counters, per case:")
    grids = defaultdict(Counter)
    for (sess, sup), seq in by_thread.items():
        grids[seq[0]["case"]][grid_of([r["its"] for r in seq if r["status"] not in ("agreed",)])] += 1
    for c in sorted(grids):
        print(f"   {c}: {dict(grids[c])}")

    # 4. walks: what came right before
    print("\n4. walk-aways and the answer before:")
    walks = Counter()
    for seq in by_thread.values():
        for a, b in zip(seq, seq[1:]):
            if b["status"] == "walked_away":
                why = []
                if a["status"] == "final_offer":
                    why.append("after its final")
                if b["kind"] == "timeout":
                    why.append("timeout")
                if b["our_move"] is not None and abs(b["our_move"]) < 1e-6:
                    why.append("we repeated our ask")
                elif b["our_move"] is not None and 0 < b["our_move"] < 0.005 * (b["ask"] or 1):
                    why.append("tiny move")
                if b["no_sheet"]:
                    why.append("no-sheet note")
                walks[(b["case"], " + ".join(why) or "other")] += 1
    for k, v in sorted(walks.items()):
        print(f"   {v:3d}  {k}")

    # 5. round of its first final_offer, per case
    print("\n5. round of its first final_offer (per thread), per case:")
    finals = defaultdict(list)
    for seq in by_thread.values():
        f = next((r["round"] for r in seq if r["status"] == "final_offer"), None)
        if f is not None:
            finals[seq[0]["case"]].append(f)
    for c in sorted(finals):
        print(f"   {c}: {Counter(finals[c])}")

    # 6. claims: what the answer's price did by claim result / marker
    print("\n6. its cut in the answer, by what it said about our data (single-supplier and RFQ):")
    eff = defaultdict(list)
    for r in data:
        if r["its_move"] is None or r["kind"] != "reply":
            continue
        tag = (
            "taken"
            if r["taken"]
            else "no_change"
            if r["no_change"]
            else "not_reality"
            if r["not_reality"]
            else ("claims, no comment" if r["claims"] else "no claims")
        )
        eff[tag].append(-r["its_move"])
    for k, v in sorted(eff.items()):
        cut = [x for x in v if x > 1e-6]
        print(f"   {k:20s} n={len(v):4d}  cut in {len(cut) / len(v) * 100:3.0f}%  mean cut {sum(v) / len(v):.3f}")


if __name__ == "__main__":
    main()
