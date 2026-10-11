"""Play an agent against the stress test set offline: no network, no arena, no LLM.

    NOIDEA_EXPERIMENTS=hidden python stress/run_stress.py --label v1 --cases stress/cases [--limit N] [--jobs 4]

The case dict and the threads are built like the arena and arena_kit/play.py build them: the agent
gets the case file WITHOUT the `_hidden` key and `{supplier_id: [opening quote e-mail]}`; its
e-mails are appended as {**msg, "from": "buyer"} followed by the supplier's reply; quote PDFs come
as attachments with their text under "text" (the labels arena_kit.docs.quote_terms reads).
Multi-supplier (RFQ) cases follow play._play_threads: the agent decides for the bidders whose reply
is in (`agent.focus`); a bidder it just wrote to is "pending" until every other ready bidder has had
its turn (offline stand-in for the parallel sends of the real runner).
Error handling follows play.py: an invalid e-mail (the arena's 422) crashes a single-supplier case
(play() re-raises) and is dropped in an RFQ (_play_threads resyncs); an accept of an unknown or an
alternative ("-a") term sheet id is refused and the agent decides again (recover_close); a message
past the round limit gets the arena's 409 (the offer stands) - after 3 of them, or 120 decisions,
the harness closes the case with play.closing_move (what the runner does at a wave's cap).

Scoring (arena_kit.cost): C_open = cheapest opening quote that keeps the must-haves (all openings if
none does); C_deal = total_cost of the accepted sheet closed on the supplier's standard terms, the
relationship term priced with the supplier's hidden full cost and cash rate; C_best = the cheaper
of the alternative and the best package any hidden supplier would ever accept - every allowed
combination of the non-price terms at any price from its absolute floor (all levers applied) up,
must-haves kept (gen_cases.yardsticks / sim_supplier.best_package_cost). No deal scores the
alternative (0 without one); a broken must-have scores 0; a crashed case is no deal.
"""

import argparse
import copy
import json
import os
import statistics as st
import sys
import time
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
KIT = REPO / "tacto" / "starter-kit"

ENDED = {"walked_away", "no_bid"}
MAX_DECISIONS = 120


def _paths():
    for p in (str(KIT), str(HERE)):
        if p not in sys.path:
            sys.path.insert(0, p)


def latest(events):
    return next(m for m in reversed(events) if m.get("from") != "buyer")


def live(threads):
    return [s for s, ev in threads.items() if latest(ev).get("status") not in ENDED]


class Invalid(Exception):
    pass


def validate(case, msg, sup):
    """The arena's 422 rules for an e-mail with term sheets."""
    sheets = msg.get("term_sheets") or []
    if len(sheets) > 3:
        raise Invalid("more than 3 term sheets")
    if len(msg.get("body") or "") > 8000 or len(msg.get("refs") or []) > 20:
        raise Invalid("body over 8,000 characters or more than 20 refs")
    neg = set(case["negotiable"])
    for ts in sheets:
        t = ts.get("terms") or {}
        if set(t) != neg:
            raise Invalid(f"a term sheet carries exactly the negotiable fields {sorted(neg)}; got {sorted(t)}")
        p = t.get("unit_price")
        if not isinstance(p, (int, float)) or p <= 0:
            raise Invalid(f"unit_price {p!r}")
        for f, v in t.items():
            opts = (case.get("term_options") or {}).get(f)
            if f != "unit_price" and opts and v not in opts and v != sup.std.get(f):
                raise Invalid(f"{f}={v!r} is not one of {opts}")


def closing_move(case, threads, sups):
    from arena_kit.cost import must_haves_ok, total_cost
    from arena_kit.docs import standard_terms

    alt = case["buyer"].get("alternative") or {}
    c_alt = total_cost(case, alt["terms"]) if (alt.get("terms") or {}).get("unit_price") else float("inf")
    best = None
    for sid in live(threads):
        sheets = latest(threads[sid]).get("term_sheets") or []
        if not sheets or not sheets[0].get("term_sheet_id"):
            continue
        terms, std = sheets[0]["terms"], standard_terms(threads[sid])
        if must_haves_ok(case, terms, std) and (c := total_cost(case, terms, std)) < c_alt:
            best = min(best or (c, sid, sheets[0]["term_sheet_id"]), (c, sid, sheets[0]["term_sheet_id"]))
    if best is None:
        return {"supplier_id": (live(threads) or list(threads))[0], "message": {"action": {"type": "walk_away"}}}
    return {"supplier_id": best[1], "message": {"action": {"type": "accept", "term_sheet_id": best[2]}}}


def play_case(path, new_agent):
    _paths()
    from arena_kit.cost import cost_breakdown, closing_terms, must_haves_ok, score, total_cost
    from sim_supplier import Session, SimSupplier

    full = json.loads(Path(path).read_text())
    hidden = full.pop("_hidden")
    case = full  # what the agent sees: the case file as the arena sends it
    facts = FACTS_CACHE.setdefault("facts", json.loads((REPO / "tacto" / "data" / "facts.json").read_text()))
    sess = Session(case, facts)
    seed = case["case_id"]
    sups = {sid: SimSupplier(case, sid, hidden["suppliers"][sid], sess, seed) for sid in case["suppliers"]}
    threads = {sid: [s.opening_message()] for sid, s in sups.items()}
    ev = {"invalid": 0, "bad_accept": 0, "over_limit": 0, "forced_close": None, "crash": None, "decisions": 0,
          "decide_s": 0.0, "held_first": 0}
    t_start = time.time()
    end, deal_sid, deal_terms = None, None, None
    try:
        agent = new_agent()
        rfq = len(threads) > 1
        pending = []  # RFQ: [(sid, buyer msg, reply)] sent but not yet "arrived", oldest first

        def arrive(i=0):
            sid, m, r = pending.pop(i)
            threads[sid] += [{**m, "from": "buyer"}, r]

        while True:
            lv = live(threads)
            if not lv and not pending:
                end = "supplier_walked"
                break
            ready = [s for s in lv if s not in {p[0] for p in pending}]
            if not ready:
                arrive()
                continue
            if ev["decisions"] >= MAX_DECISIONS or ev["over_limit"] >= 3:
                ev["forced_close"] = "max_decisions" if ev["decisions"] >= MAX_DECISIONS else "round_limit"
                while pending:
                    arrive()
                decision = closing_move(case, threads, sups)
            else:
                if rfq and hasattr(agent, "focus"):
                    agent.focus = set(ready)
                t0 = time.time()
                decision = agent.decide(copy.deepcopy(case), threads)
                ev["decide_s"] += time.time() - t0
                ev["decisions"] += 1
            sid, msg = decision["supplier_id"], decision["message"]
            action = msg.get("action")
            if rfq and sid in {p[0] for p in pending} and not action:
                arrive()  # it chose a bidder whose reply is still out: wait for one
                continue
            if action:
                if action.get("type") == "walk_away":
                    end = "buyer_walked"
                    break
                if action.get("type") != "accept":
                    raise Invalid(f"unknown action {action}")
                tsid = action.get("term_sheet_id")
                owner = next((k for k, s in sups.items() if s.offer_id == tsid and not s.closed and s.status not in ENDED), None)
                if owner is None:
                    ev["bad_accept"] += 1
                    if ev["bad_accept"] > 5:
                        raise Invalid(f"accept of {tsid} refused 5 times")
                    for k in threads:  # recover_close: retire the refused id, the agent decides again
                        for ts in latest(threads[k]).get("term_sheets") or []:
                            if ts.get("term_sheet_id") == tsid:
                                ts["term_sheet_id"] = None
                    continue
                deal_sid, deal_terms = owner, dict(sups[owner].standing)
                end = "accepted"
                break
            sup = sups[sid]
            if sup.closed or sup.status in ENDED:
                ev["invalid"] += 1  # 409: the thread has ended
                if ev["invalid"] > 5:
                    raise Invalid("kept writing to an ended thread")
                continue
            try:
                validate(case, msg, sup)
            except Invalid:
                ev["invalid"] += 1
                if not rfq or ev["invalid"] > 5:
                    raise
                continue
            if sup.round >= case.get("round_limit", 10):
                ev["over_limit"] += 1  # 409 round limit: play.py appends the arena's view, the offer stands
                note = {"from": "arena", "status": sup.status, "attachments": [], "missing_fields": [],
                        "term_sheets": [{"term_sheet_id": sup.offer_id, "terms": dict(sup.standing)}],
                        "body": "(round limit reached: accept the standing offer or walk away)"}
                threads[sid] += [{**msg, "from": "buyer"}, note]
                continue
            if not rfq and getattr(agent, "hold_first", False) and not any(m.get("from") == "buyer" for m in threads[sid]):
                ev["held_first"] += 1
                sup.timeout()  # play.py holds the first e-mail past one timeout round
            reply = sup.respond(msg)
            if rfq:
                pending.append((sid, msg, reply))
            else:
                threads[sid] += [{**msg, "from": "buyer"}, reply]
    except Exception as e:  # one broken case must not stop the others
        ev["crash"] = f"{type(e).__name__}: {e}"
        ev["trace"] = traceback.format_exc()[-1500:]
        end = "crash"
    # ---- result
    b = case["buyer"]
    c_open, c_best, c_alt = hidden["c_open"], hidden["c_best"], hidden["c_alt"]
    res = {"case_id": case["case_id"], "template": hidden["template"], "type": case["type"],
           "goal": b["category_goal"], "suppliers": len(sups),
           "archetypes": {k: v["archetype"] for k, v in hidden["suppliers"].items()},
           "end": end, "deal": end == "accepted", "c_open": c_open, "c_best": c_best, "c_alt": c_alt}
    if end == "accepted":
        s = sups[deal_sid]
        t = closing_terms(case, deal_terms, s.std)
        c_deal = total_cost(case, deal_terms, s.std, s.relationship_supplier(deal_terms))
        ok = must_haves_ok(case, deal_terms, s.std)
        res.update(supplier_id=deal_sid, terms=t, c_deal=c_deal, must_haves_ok=ok,
                   score=score(c_open, c_deal, c_best) if ok else 0.0,
                   breakdown={k: round(v, 2) for k, v in cost_breakdown(case, deal_terms, s.std, s.relationship_supplier(deal_terms)).items()},
                   deal_value_vs_floor=round(s.value(deal_terms) / s.r_min - 1, 4))
    else:
        res.update(c_deal=None, must_haves_ok=None, score=score(c_open, c_alt, c_best) if c_alt else 0.0)
    res["threads"] = {sid: {"rounds": s.round, "status": s.status, "closed": s.closed, "archetype": s.hp["archetype"],
                            "history": s.history} for sid, s in sups.items()}
    res["events"] = {k: v for k, v in ev.items() if k != "trace"}
    if ev.get("trace"):
        res["crash_trace"] = ev["trace"]
    res["seconds"] = round(time.time() - t_start, 2)
    return res


FACTS_CACHE = {}


def _agent_factory(name):
    _paths()
    if name == "noidea":
        from arena_kit.agents.noidea_rfq import NoIdeaAgent

        return lambda: NoIdeaAgent(None)
    if name == "naive":
        import arena_kit.agents.naive as naive

        cls = next(getattr(naive, n) for n in dir(naive) if n.lower().endswith("agent") and isinstance(getattr(naive, n), type))
        return lambda: cls()
    raise SystemExit(f"unknown agent {name}")


def _worker(args):
    path, agent_name = args
    return play_case(path, _agent_factory(agent_name))


def diagnose(r):
    if r["end"] == "crash":
        return f"crash: {r['events']['crash'][:160]}"
    walks = [f"{s} walked at r{t['rounds']}" + (" (after final_offer)" if any(h.get("kind") == "walk" and "final" in h.get("why", "") for h in t["history"]) else "")
             for s, t in r["threads"].items() if t["closed"] == "walked_away"]
    if r["end"] == "supplier_walked":
        return "no deal - every supplier walked: " + "; ".join(walks)
    if r["end"] == "buyer_walked":
        return "agent walked away" + (f" (alternative c_alt={r['c_alt']:.0f})" if r["c_alt"] else " - no alternative, scores 0")
    if r["deal"] and not r["must_haves_ok"]:
        return "deal breaks a must-have"
    parts = []
    if r["deal"]:
        st_ = r["threads"][r["supplier_id"]]
        parts.append(f"deal with {r['supplier_id']} ({st_['archetype']}) at r{st_['rounds']}, status {st_['status']}")
        parts.append(f"price {r['terms']['unit_price']} vs best package {r.get('best_price')}")
        parts.append(f"deal value {100 * r['deal_value_vs_floor']:+.1f}% over the supplier's absolute floor")
        if r["c_deal"] >= r["c_open"]:
            parts.append("C_deal >= C_open")
        rel = (r.get("breakdown") or {}).get("relationship", 0)
        if rel > 0.01 * abs(r["c_open"] - r["c_best"]):
            parts.append(f"relationship charge {rel:.0f}")
        unc = (r.get("breakdown") or {}).get("uncovered_need", 0)
        if unc > 0:
            parts.append(f"uncovered need {unc:.0f}")
    if walks:
        parts.append("; ".join(walks))
    if r["events"].get("forced_close"):
        parts.append(f"harness closed it ({r['events']['forced_close']})")
    if r["events"].get("invalid"):
        parts.append(f"{r['events']['invalid']} invalid e-mails")
    return "; ".join(parts)


def summarize(results, label, experiments):
    def block(rs):
        sc = [r["score"] for r in rs]
        return {"n": len(rs), "mean": round(st.mean(sc), 4), "median": round(st.median(sc), 4), "min": round(min(sc), 4),
                "no_deal_rate": round(sum(not r["deal"] for r in rs) / len(rs), 3),
                "supplier_walk_rate": round(sum(any(t["closed"] == "walked_away" for t in r["threads"].values()) for r in rs) / len(rs), 3),
                "all_walked_rate": round(sum(r["end"] == "supplier_walked" for r in rs) / len(rs), 3),
                "buyer_walk_rate": round(sum(r["end"] == "buyer_walked" for r in rs) / len(rs), 3),
                "crashes": sum(r["end"] == "crash" for r in rs),
                "broken_must_have": sum(bool(r["deal"] and not r["must_haves_ok"]) for r in rs),
                "mean_rounds": round(st.mean(max(t["rounds"] for t in r["threads"].values()) for r in rs), 2)}

    by = lambda key: {k: block([r for r in results if key(r) == k]) for k in sorted({key(r) for r in results})}  # noqa: E731
    arche = {}
    for r in results:
        for a in set(r["archetypes"].values()):
            arche.setdefault(a, []).append(r)
    worst = sorted(results, key=lambda r: (r["score"], r["case_id"]))[:10]
    return {
        "label": label, "experiments": experiments, "cases": len(results),
        "overall": block(results),
        "by_type": by(lambda r: r["type"]),
        "by_template": by(lambda r: r["template"]),
        "by_archetype": {k: block(v) for k, v in sorted(arche.items())},
        "worst": [{"case_id": r["case_id"], "template": r["template"], "type": r["type"], "score": round(r["score"], 4),
                   "archetypes": r["archetypes"], "end": r["end"], "why": diagnose(r)} for r in worst],
    }


def markdown(rep):
    o = [f"# Stress report `{rep['label']}`", "",
         f"NOIDEA_EXPERIMENTS=`{rep['experiments']}` - {rep['cases']} cases, offline simulator (stress/sim_supplier.py).", ""]
    hdr = "| {k} | n | mean | median | min | no-deal | any supplier walked | all walked | agent walked | crashes | broken must-have | rounds |"
    sep = "|---|---|---|---|---|---|---|---|---|---|---|---|"

    def rows(title, d):
        o.extend([f"## {title}", "", hdr.format(k=title.split()[-1]), sep])
        for k, b in d.items():
            o.append(f"| {k} | {b['n']} | {b['mean']:.3f} | {b['median']:.3f} | {b['min']:.3f} | {b['no_deal_rate']:.0%} | "
                     f"{b['supplier_walk_rate']:.0%} | {b['all_walked_rate']:.0%} | {b['buyer_walk_rate']:.0%} | {b['crashes']} | "
                     f"{b['broken_must_have']} | {b['mean_rounds']} |")
        o.append("")

    rows("Overall", {"all": rep["overall"]})
    rows("By case type", rep["by_type"])
    rows("By template", rep["by_template"])
    rows("By supplier archetype", rep["by_archetype"])
    o.extend(["## 10 worst cases", "", "| case | template | type | score | archetypes | what went wrong |", "|---|---|---|---|---|---|"])
    for w in rep["worst"]:
        o.append(f"| {w['case_id']} | {w['template']} | {w['type']} | {w['score']:.3f} | {', '.join(f'{k[4:]}={v}' for k, v in w['archetypes'].items())} | {w['why']} |")
    return "\n".join(o) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    ap.add_argument("--cases", default=str(HERE / "cases"))
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--agent", default="noidea", choices=["noidea", "naive"])
    a = ap.parse_args(argv)
    if os.environ.get("PYTHONHASHSEED") != "0":  # reproducible set iteration inside the agent too
        os.environ["PYTHONHASHSEED"] = "0"
        os.execv(sys.executable, [sys.executable, *sys.argv])
    paths = sorted(p for p in Path(a.cases).glob("*.json"))
    if a.limit:
        paths = paths[: a.limit]
    experiments = os.environ.get("NOIDEA_EXPERIMENTS")
    t0 = time.time()
    if a.jobs > 1:
        import multiprocessing as mp

        with mp.get_context("fork").Pool(a.jobs) as pool:
            results = pool.map(_worker, [(str(p), a.agent) for p in paths], chunksize=1)
    else:
        results = [_worker((str(p), a.agent)) for p in paths]
    best_prices = {}
    for p in paths:
        h = json.loads(p.read_text())["_hidden"]
        best_prices[h and json.loads(p.read_text())["case_id"]] = (h["best_package"]["terms"] or {}).get("unit_price")
    for r in results:
        r["best_price"] = best_prices.get(r["case_id"])
    rep = summarize(results, a.label, experiments)
    rep["seconds"] = round(time.time() - t0, 1)
    (HERE / f"report_{a.label}.json").write_text(json.dumps({**rep, "results": results}, indent=1, default=str))
    (HERE / f"report_{a.label}.md").write_text(markdown(rep))
    print(markdown(rep))
    print(f"{len(results)} cases in {rep['seconds']} s")


if __name__ == "__main__":
    main()
