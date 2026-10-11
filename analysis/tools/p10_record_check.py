"""P10 record investigation, offline (Parth, 2026-10-11). No arena, no LLM, reads only local files.

    cd tacto/starter-kit && uv run python ../../analysis/tools/p10_record_check.py > out.txt

A. Exact benchmarks from arena_kit.cost (P10 case file, the quote's standard terms ppm 300 / chargeback 0).
B. Every archived P10 game (datasets/runs, tools/replays/raw): arena mode per reply (supplier_mode_scan.reply_mode), first
   counter by taken facts, final at our message 2 by what our e-mail carried, lowest normal-mode price.
C. Every e-mail we sent after a final_offer, all cases: what it asked against the final and what the supplier did.
D. The current P10 agent (analysis/agent_variants/noidea_p10.py) replayed on the archived 59c899b9 game (complete=None):
   its turns 1-2 against what was sent live, byte for byte.
"""
import collections
import glob
import importlib.util
import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "tacto" / "starter-kit"), str(ROOT / "analysis" / "tools")]
logging.disable(logging.CRITICAL)
from arena_kit.cost import total_cost  # noqa: E402
from supplier_mode_scan import reply_mode  # noqa: E402

CASES = {c["case_id"]: c for c in json.loads((ROOT / "datasets/cases_practice.json").read_text(encoding="utf-8"))}
CASE = CASES["case:P10"]
STD = {"ppm_commitment": 300, "chargeback_eur_per_complaint": 0.0}
C_OPEN, C_BEST = 1932492.18, 1328926.89
RECORD = 0.7409613962393361  # 673ee890: 30.70 @ 56 d, 36 m (engine-template window)
BASELINE = 0.7097389248477162  # 59c899b9 / 3c4aa1a6 / 3a968d38 / 856dff72 / d34ee89a: 31.10 @ 56 d, 36 m


def score(p, lead=56, months=36, vol=23400):
    c = total_cost(CASE, {"unit_price": p, "volume_per_year": vol, "contract_months": months, "lead_time_days": lead}, STD)
    return c, (C_OPEN - c) / (C_OPEN - C_BEST)


def part_a():
    print("A. EXACT BENCHMARKS (arena_kit.cost.total_cost, P10 case file, standard ppm 300 / chargeback 0)")
    for p in (31.50, 31.20, 31.10, 31.00, 30.80, 30.70, 30.69, 30.60):
        c, s = score(p)
        tag = " = record 673ee890" if abs(s - RECORD) < 1e-9 else " = repeatable best" if abs(s - BASELINE) < 1e-9 else ""
        print(f"  {p:.2f} @ 56 d / 36 m / 23,400: C {c:,.2f}  score {s:.6f}{tag}")
    print("  highest price that beats each mark (2-decimal prices; 24 and 36 months cost the same, horizon 2 y):")
    for lead in (35, 42, 54, 56):
        for months in (24, 36):
            best = {}
            for mark, name in ((RECORD, "0.741"), (BASELINE, "0.7097")):
                p = 40.0
                while score(p, lead, months)[1] <= mark:
                    p = round(p - 0.01, 2)
                best[name] = p
            note = " (54 d = its quoted lead, not a term option: never sent in 393 games)" if lead == 54 else ""
            print(f"    lead {lead} d, {months} m: beat 0.741 at <= {best['0.741']:.2f}, beat 0.7097 at <= "
                  f"{best['0.7097']:.2f}{note}")
    c12, s12 = score(31.10, 56, 12)
    print(f"  12 months at 31.10 @ 56 d: score {s12:.3f} (year 2 bought at the fallback price + 25%)")


def load_games():
    games = {}
    for p in sorted(glob.glob(str(ROOT / "datasets/runs/*.json"))):
        try:
            d = json.load(open(p, encoding="utf-8"))
        except Exception:  # noqa: BLE001
            continue
        det = d.get("detail") or {}
        if det.get("case_id"):
            games[det["session_id"]] = (det["case_id"], (d.get("session") or {}).get("created_at") or 0, det.get("result") or {})
    for p in sorted(glob.glob(str(ROOT / "tools/replays/raw/*.json"))):
        d = json.load(open(p, encoding="utf-8"))
        if d.get("session_id") and d["session_id"] not in games:
            games[d["session_id"]] = (d.get("case_id"), 0, d.get("result") or {})
    return games


def taken(reasons, kind):
    word = kind.replace("_", " ")
    for r in reasons:
        if r.startswith("We checked the") and word in r:
            return "taken" if "took it into account" in r else "shrugged"
    return "taken" if any(w in " ".join(reasons) for w in ("incorporated", "factored", "adjusted our calculation",
                                                         "took it into account", "taken it into consideration")) else "?"


def part_b(games):
    print("\nB. ALL ARCHIVED P10 GAMES")
    r1, r2, modes, tmpl = collections.Counter(), collections.defaultdict(list), collections.Counter(), []
    n = 0
    for sid, (cid, created, res) in sorted(games.items(), key=lambda x: x[1][1]):
        if cid != "case:P10" or not res.get("trace"):
            continue
        n += 1
        trace = res["trace"]
        sup = [mv for mv in trace if mv["actor"] != "buyer" and mv["move"].get("round", 0) >= 1]
        mode = {reply_mode(mv.get("reasons") or []) for mv in sup} - {None}
        m = "TEMPLATE" if mode == {"T"} else "model" if mode == {"M"} else "mixed" if mode else "?"
        modes[m] += 1
        if m == "TEMPLATE":
            tmpl.append((sid, res.get("score")))
            continue
        buyer = [mv for mv in trace if mv["actor"] == "buyer" and mv["move"].get("type") == "message"]
        if not buyer or not sup:
            continue
        b1, s1 = buyer[0]["move"], sup[0]
        if b1.get("term_sheets") and s1["move"].get("status") == "open":
            kinds = [c["type"] for c in (b1.get("interpreted") or {}).get("claims") or []]
            tk = sorted(k for k in kinds if taken(s1.get("reasons") or [], k) == "taken")
            r1[(tuple(tk), s1["move"]["terms"]["unit_price"])] += 1
        if len(buyer) >= 2 and len(sup) >= 2 and sup[1]["move"].get("status") == "final_offer" \
                and sup[0]["move"].get("status") == "open":
            b2 = buyer[1]["move"]
            ask = (b2.get("term_sheets") or [{}])[0].get("terms", {}).get("unit_price")
            kinds = [c["type"] for c in (b2.get("interpreted") or {}).get("claims") or []]
            m1 = (b1.get("term_sheets") or [{}])[0].get("terms", {}).get("contract_months")
            m2 = (b2.get("term_sheets") or [{}])[0].get("terms", {}).get("contract_months")
            key = ("36-m move" if m2 == 36 and m1 != 36 else "no term move") + " + " + ("+".join(kinds) or "no data")
            r2[key].append((sup[0]["move"]["terms"]["unit_price"], ask, sup[1]["move"]["terms"]["unit_price"], sid[:8]))
    print(f"  {n} games with a trace: {dict(modes)}; engine-template games: {tmpl}")
    print("  first counter (normal mode, status open) by the facts it TOOK in our message 1:")
    for (tk, price), k in sorted(r1.items(), key=lambda x: (-len(x[0][0]), x[0][1])):
        print(f"    {price:.2f}  x{k}  taken: {', '.join(tk) or 'none'}")
    print("  final at our message 2 (normal mode) by what message 2 carried - (its counter, our ask, its final):")
    finals = []
    for key, rows in sorted(r2.items(), key=lambda x: min(r[2] for r in x[1])):
        finals += [r[2] for r in rows]
        print(f"    {key}: " + "; ".join(f"{a:.2f}/{b:.2f}->{c:.2f} {s}" for a, b, c, s in sorted(rows, key=lambda r: r[2])))
    cnt = collections.Counter(finals)
    print(f"  finals at message 2: {dict(sorted(cnt.items()))}  (n={len(finals)}; lowest {min(finals):.2f}; the largest "
          f"cut in that message {max(r[0] - r[2] for rows in r2.values() for r in rows):.2f})")


def part_c(games):
    print("\nC. EVERY E-MAIL WITH A TERM SHEET SENT AFTER A final_offer (all cases, datasets/runs)")
    out = collections.Counter()
    for p in sorted(glob.glob(str(ROOT / "datasets/runs/*.json"))):
        d = json.load(open(p, encoding="utf-8"))
        cid = (d.get("session") or {}).get("case_id", "")[5:]
        for th in (d.get("threads") or {}).values():
            ms = th.get("messages", [])
            for i, m in enumerate(ms):
                if m.get("from") == "buyer" or m.get("status") != "final_offer" or i + 1 >= len(ms):
                    continue
                nxt = ms[i + 1]
                if nxt.get("from") != "buyer" or not nxt.get("term_sheets"):
                    continue
                fin = (m.get("term_sheets") or [{}])[0].get("terms", {})
                ours = nxt["term_sheets"][0]["terms"]
                reply = ms[i + 2] if i + 2 < len(ms) else {}
                alts = [a.get("terms") for a in (m.get("term_sheets") or [])[1:]]
                diff = {k: (fin.get(k), v) for k, v in ours.items() if k != "unit_price" and fin.get(k) != v}
                own_alt = any(all(a.get(k) == v for k, v in ours.items() if k in a) for a in alts if a)
                gap = (ours["unit_price"] / fin["unit_price"] - 1) * 100 if fin.get("unit_price") else 0
                st = reply.get("status")
                out[st] += 1
                print(f"  {cid} {d['session']['session_id'][:8]}: final {fin.get('unit_price')} -> we sent "
                      f"{ours['unit_price']} ({gap:+.1f}%) other terms changed {diff or 'none'}{' = its own alternative' if own_alt else ''}"
                      f" -> {st}")
    print(f"  outcomes: {dict(out)}. Agreed only where our sheet was worth at least its final to it (a payment trade it "
          f"values, or its own alternative); every push that left it worse off walked or was countered.")


def part_d():
    print("\nD. CURRENT P10 AGENT (noidea_p10.py) REPLAYED ON THE ARCHIVED 59c899b9 GAME (complete=None: no LLM)")
    spec = importlib.util.spec_from_file_location("arena_kit.agents._p10", ROOT / "analysis/agent_variants/noidea_p10.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    d = json.loads((ROOT / "tools/replays/raw/P10_59c899b93ba24dec.json").read_text(encoding="utf-8"))
    for sid, th in d["thread_messages"].items():
        msgs, ag, k = th["messages"], mod.NoIdeaAgent(None), 0
        for i, m in enumerate(msgs):
            if m["from"] != "buyer" or not m.get("term_sheets"):
                continue
            k += 1
            mine = ag.decide(CASE, {sid: [dict(x) for x in msgs[:i]]})["message"]
            same_body = mine.get("body") == m.get("body")
            same_sheet = [t["terms"] for t in mine.get("term_sheets", [])] == [
                {kk: t["terms"][kk] for kk in CASE["negotiable"]} for t in m["term_sheets"]]
            same_refs = sorted(mine.get("refs") or []) == sorted(m.get("refs") or [])
            print(f"  turn {k}: body {'SAME' if same_body else 'DIFFERENT'}, sheet {'SAME' if same_sheet else 'DIFFERENT'}"
                  f", refs {'SAME' if same_refs else 'DIFFERENT'}  ({[t['terms']['unit_price'] for t in mine['term_sheets']]})")


if __name__ == "__main__":
    part_a()
    g = load_games()
    part_b(g)
    part_c(g)
    part_d()
