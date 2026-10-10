"""Top-scoring runs per case across ALL archived team games: what did the winners do? (no quota)
Per case: the games within 0.02 of the case best vs the median game. Features: round-1 data kinds and count, sheets in
round 1, first-counter cut (% off its opening), rounds, how it closed (agreed to OUR ask / accepted its final / open),
payment term of the deal, reasons it gave when it moved most."""
import json, re, statistics, collections
from pathlib import Path
ROOT = Path.home() / "Dhruv/ehl-finals-hackathon"
KIND = [("idx:", "index"), ("po:", "price_history"), ("fc:", "forecast"), ("sc:", "scorecard"), ("qn:", "quality_notes"),
        ("cost:", "should_cost"), ("quote:", "quote"), ("offer:", "rival_offer"), ("ctr:", "contract"), ("doc:", "letter"), ("news:", "news")]
def kinds(refs):
    out = collections.Counter()
    for r in refs or []:
        for pre, k in KIND:
            if r.startswith(pre):
                out[k] += 1; break
    return out
games = collections.defaultdict(list)
for f in sorted((ROOT / "datasets/runs").glob("*.json")):
    try:
        g = json.loads(f.read_text())
    except Exception:
        continue
    det = g.get("detail") or {}; res = det.get("result") or {}
    cid = (g.get("session") or {}).get("case_id") or det.get("case_id")
    sc = res.get("score")
    if not cid or sc is None or not res.get("trace"):
        continue
    tr = res["trace"]
    sup_moves = [t for t in tr if t["actor"] != "buyer"]
    buy = [t for t in tr if t["actor"] == "buyer"]
    if not sup_moves or not buy:
        continue
    opening = (sup_moves[0]["move"].get("terms") or {}).get("unit_price")
    # first counter of the (winning) supplier
    win = res.get("supplier_id")
    wmoves = [t for t in sup_moves if t["actor"] == win] or sup_moves
    w_open = (wmoves[0]["move"].get("terms") or {}).get("unit_price")
    w_first = (wmoves[1]["move"].get("terms") or {}).get("unit_price") if len(wmoves) > 1 else None
    b1 = buy[0]["move"]
    r1 = kinds(b1.get("refs"))
    last_status = wmoves[-1]["move"].get("status")
    closed = "agreed_to_our_ask" if last_status == "agreed" else ("its_final" if any(t["move"].get("status") == "final_offer" for t in wmoves) else "accepted_open")
    deal = res.get("terms") or {}
    moved = []
    for i in range(1, len(wmoves)):
        a = (wmoves[i - 1]["move"].get("terms") or {}).get("unit_price"); b = (wmoves[i]["move"].get("terms") or {}).get("unit_price")
        if a and b:
            moved.append(((a - b) / a, " / ".join(wmoves[i].get("reasons") or [])[:220]))
    games[cid].append(dict(sess=f.stem, score=sc, r1_n=sum(r1.values()), r1=dict(r1), r1_sheets=len(b1.get("term_sheets") or []),
                           first_cut=((w_open - w_first) / w_open) if (w_open and w_first) else None, rounds=len(buy),
                           closed=closed, pay=deal.get("payment_days"), best_move=max(moved, default=(0, ""))))
summary = {}
for cid in sorted(games):
    gs = sorted(games[cid], key=lambda x: -x["score"])
    if len(gs) < 3:
        continue
    best = gs[0]["score"]; top = [x for x in gs if x["score"] >= best - 0.02]; rest = [x for x in gs if x["score"] < best - 0.02]
    med = lambda xs, k: round(statistics.median([x[k] for x in xs if x[k] is not None]), 3) if [x for x in xs if x[k] is not None] else None
    print(f"\n=== {cid}: {len(gs)} games, best {best:.3f}, top {len(top)}")
    print(f"  top : r1 facts {med(top,'r1_n')}  r1 sheets {med(top,'r1_sheets')}  first cut {med(top,'first_cut')}  rounds {med(top,'rounds')}  closed {collections.Counter(x['closed'] for x in top).most_common()}  pay {collections.Counter(x['pay'] for x in top).most_common(2)}")
    print(f"  rest: r1 facts {med(rest,'r1_n')}  r1 sheets {med(rest,'r1_sheets')}  first cut {med(rest,'first_cut')}  rounds {med(rest,'rounds')}  closed {collections.Counter(x['closed'] for x in rest).most_common()}")
    kt = collections.Counter(); kr = collections.Counter()
    for x in top: kt.update({k: 1 for k in x["r1"]})
    for x in rest: kr.update({k: 1 for k in x["r1"]})
    print("  r1 kinds top :", {k: f"{v}/{len(top)}" for k, v in kt.most_common()})
    print("  r1 kinds rest:", {k: f"{v}/{len(rest)}" for k, v in kr.most_common()})
    bm = max(top, key=lambda x: x["best_move"][0])
    print(f"  biggest move in a top game: {bm['best_move'][0]*100:.1f}% ({bm['sess']}) | {bm['best_move'][1]}")
    summary[cid] = dict(best=best, top=[x["sess"] for x in top])
json.dump(summary, open(ROOT / "notes/top_runs_summary.json", "w"), indent=1)
