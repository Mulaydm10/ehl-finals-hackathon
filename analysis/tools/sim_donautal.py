"""Replay supplier for P08 (Donautal, sup:70710), fitted to its 11 live games - offline, no quota, no LLM.

    cd tacto/starter-kit && uv run python ../../analysis/tools/sim_donautal.py [agent_file ...] [--validate] [--save NAME]
    (no agent file: the cloud copy analysis/agent_variants/noidea_neel_cloud.py)

Values below are its cash value per kg: price at its 30-day standard and 8% rate, db0-equivalent (db5 = +EUR 0.12, i.e.
0.024 a deadband point). Each rule and the games behind it (analysis/cases/P08_engine.md, analysis/central/FINAL_TRIGGER.md):
  - round 1: nominal headline 5.41 (low draw) or 5.53 (high draw), a per-session coin flip (5 / 5 games), on the payment
    days of the sheet of ours worth most to it (ties within 0.003 -> the longest; our 90-day sheet -> 90 d, value -0.05);
    AS-14404 db0 clause and 24 months on every sheet; an alternative at 14 d;
  - its clause is mandatory for 24 months; a clause-free ask is countered with the clause; deadband priced at +0.024/pt;
  - every reply is on the payment days of our sheet worth most to it (ties within 0.003 -> the longest);
  - round 2: -0.16 when our ask stays clause-free (5 / 5: c387 cae4 1363 a43d db7d, whatever our step: +0.10 or +0.22),
    but -0.118 when we STAY on its 90-day headline (6912fd89, n=1; analysis/cases/P08_round2_payment.md);
    -0.07 when we take its db0 clause (325d -0.09, ab47 -0.05); db5 asks -0.07 (mean of a hold 1f27, -0.15, -0.06);
  - our message 3: final_offer (-0.05; 9 / 10) unless our step there is < 0.3x its last step: then open -0.055 and the
    final (-0.055) one message later (db7d315a 0.06/0.06, 6912fd89 0.049/0.049); `max_defer` (default 1) caps it;
  - any message after its final_offer: it walks (1f27); an alternative's id ('-a') cannot be accepted (arena 422);
  - it agrees when our sheet is worth at least its next counter (clause-free sheets 0.14 less: the AS-14404 path risk);
  - data: verified, no price effect (8 kinds, 10 games); 'Which figures is that based on?' when a round cites nothing;
    an AS-14404 claim draws 'That is not our reality' (hedged until March 2027).
Scores use the arena's exact cost (all 9 live deals reproduce to 4 decimals).
"""

import argparse
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tacto/starter-kit"))
from arena_kit.cost import complete_offer, total_cost  # noqa: E402

CASE = next(c for c in json.loads((ROOT / "datasets/cases_practice.json").read_text(encoding="utf-8"))
            if c["case_id"] == "case:P08")
PROBE = json.loads((ROOT / "analysis/cases/openings/P08.json").read_text(encoding="utf-8"))
C_OPEN, C_BEST = PROBE["result"]["c_open"], PROBE["result"]["c_best"]
STD = {"payment_days": 30, "incoterm": "DAP", "ppm_commitment": 50, "chargeback_eur_per_complaint": 0.0,
       "lead_time_days": 10}
RATE, DB_PT, FREE_RISK = 0.08, 0.024, 0.14
HEADLINE = {"low": 5.41, "high": 5.53}
R2_STEP = {"free": 0.16, "db0": 0.07, "db5": 0.07}  # db5 asks: 0 (1f27, hold) / -0.15 (586a) / -0.06 (9bfa) -> the mean
# task 13 (analysis/cases/P08_floor.md): FLOOR-BOUND. With clause-free asks its final = round-1 value - BUDGET, whatever the
# path (low: c387 0.210, cae4 0.220, 6912 0.217, a4b9 0.210, a43d 0.199; high: 1363 0.258, db7d 0.281). Round 2 takes 0.16 after
# a ~16% step of ours, 0.11-0.12 after a 30% step (6912 at 90 d, a4b9 at 14 d: the step, not the payment term), 0.16 on the
# high draw; a deferral round takes half of what is left, the final the rest. XSELL: an untested floor shift (cross-sell).
BUDGET = {"low": 0.209, "high": 0.27}  # 13 games (task 14): low c387 .210 cae4 .220 6912 .217 a4b9 .210 a43d .199 ad04 .200
R2_BIG_STEP_CUT = 0.115  # low draw, our round-2 step >= 25% of the gap
FINAL_STEP, DEFER_STEP, DEFER_BELOW, FINAL_AT = 0.05, 0.055, 0.3, 3  # deferral rounds: db7d 0.06/0.06, 6912fd89 0.049/0.049
HOUSE = 0.752


def clause(db):
    return {"series": "AS-14404", "material_share": 0.45, "deadband_pct": float(db), "base_month": "2026-08"}


def f(days):
    return 1 - RATE * (days - 30) / 360


def db_of(t):
    ic = t.get("index_clause")
    return None if not ic else ic.get("deadband_pct", 0)


def value(t, free_risk=False):
    """Its cash value per kg, db0-equivalent; free_risk: a clause-free sheet minus the index risk it would carry."""
    db = db_of(t)
    v = (t["unit_price"] - DB_PT * (db or 0)) * f(t.get("payment_days") or 30)
    return v - (FREE_RISK if db is None and free_risk else 0)


def plain_value(t):
    """Price at 30 days, ignoring the clause - how FINAL_TRIGGER.md measured step ratios."""
    return t["unit_price"] * f(t.get("payment_days") or 30)


def sheet(v, days, db, months=24):
    return {"unit_price": round(v / f(days) + DB_PT * db + 1e-9, 2), "payment_days": days, "index_clause": clause(db),
            "contract_months": months}


def score(t):
    return (C_OPEN - total_cost(CASE, complete_offer(CASE, t), STD, None)) / (C_OPEN - C_BEST)


class Donautal:
    def __init__(self, draw="low", max_defer=1, xsell=0.0, term36=0.0):
        self.draw, self.max_defer, self.xsell, self.free, self.v1, self.xs = draw, max_defer, xsell, True, None, False
        self.term36, self.months = term36, 24  # term36: untested round-1 value shift for a 36-month ask (task 14)
        self.v, self.n, self.defers, self.final, self.ours = None, 0, 0, False, []
        self.its_steps, self.last_prim, self.head_days = [], None, None

    def reply(self, sheets, refs):
        """Our message (term sheets, refs) -> (status, primary, alternative, body)."""
        self.n += 1
        self.last_v_before = self.v
        self.xs = self.xs or any("invite you to quote" in (r or "") for r in [getattr(self, "body_in", "")])
        if self.final:
            return "walked_away", None, None, "We withdraw our offer."
        best = max(value(t) for t in sheets)  # it answers on the sheet of ours worth most to it (ties: the longest)
        first = max((t for t in sheets if value(t) >= best - 0.003), key=lambda t: t["payment_days"])
        if self.n == 1:
            days = self.head_days = first["payment_days"]
            self.months = 36 if first.get("contract_months") == 36 else 24
            h = round(HEADLINE[self.draw] - (self.term36 if self.months == 36 else 0), 2)
            self.v = self.v1 = h * f(days)
            prim = {"unit_price": h, "payment_days": days, "index_clause": clause(0), "contract_months": self.months}
            status, step = "open", None
        else:
            db = db_of(first)
            self.free = self.free and db is None
            floor = self.v1 - BUDGET[self.draw] - (self.xsell if self.xs else 0)
            if self.n == 2:
                kind = "free" if db is None else ("db0" if db < 2.5 else "db5")
                step = R2_STEP[kind]
                gap = self.last_v_before - plain_value(self.ours[-1])
                share = (plain_value(first) - plain_value(self.ours[-1])) / gap if gap > 0 else 0
                if kind == "free" and self.draw == "low" and share >= 0.25:
                    step = R2_BIG_STEP_CUT
            elif self.n >= FINAL_AT:
                ours = plain_value(first) - plain_value(self.ours[-1])
                last = self.its_steps[-1] if self.its_steps else 0
                if self.n == FINAL_AT + self.defers and self.defers < self.max_defer and last > 0 and ours < DEFER_BELOW * last:
                    step, self.defers = DEFER_STEP, self.defers + 1
                    if self.free:
                        step = (self.v - floor) / 2
                else:
                    step = DEFER_STEP if self.defers else FINAL_STEP
                    if self.free:
                        step = self.v - floor
                    self.final = True
            self.its_steps.append(step)
            self.v -= step
            days = first["payment_days"]
            prim = sheet(self.v, days, 0 if db is None else (5 if db >= 2.5 else 0), self.months)
            if step == 0 and self.last_prim:  # a hold keeps its standing sheet (1f27)
                prim = self.last_prim
            status = "final_offer" if self.final else "open"
        # agreement: a sheet of ours worth at least what it would offer now
        ok = [t for t in sheets if value(t, free_risk=True) >= self.v - 1e-6]
        if ok and not self.final:
            t = max(ok, key=lambda t: value(t, free_risk=True))
            self.ours.append(first)
            return "agreed", t, None, "We agree to your terms."
        alt_db = 5 if db_of(prim) == 0 else 0
        alt = sheet(self.v, prim["payment_days"] if self.n > 1 else 14, alt_db, self.months) if self.n > 1 else \
            {**prim, "unit_price": round(prim["unit_price"] + (0.04 if prim["payment_days"] == 90 else 0.08), 2),
             "payment_days": 14, "index_clause": clause(0 if self.draw == "high" else 5)}
        self.ours.append(first)
        self.last_prim = prim
        return status, prim, alt, self.body(status, prim, alt, refs)

    def body(self, status, prim, alt, refs):
        lines = ["Dear customer,", ""]
        if status == "final_offer":
            lines.append("This is our final offer (letztes Angebot). Please decide.")
        else:
            lines.append("We have reviewed your offer and can adjust our Angebot as follows.")
        lines.append(f"Our terms: a price of €{prim['unit_price']:.2f} per unit, Zahlungsziel {prim['payment_days']} days net, "
                     f"a contract term of {prim.get('contract_months', 24)} months, a Preisgleitklausel on AS-14404.")
        if any(r.startswith("idx:AS-14404") for r in refs):
            lines.append("That is not our reality: our AS-14404 is covered at fixed prices until March 2027. "
                         "It does not change our calculation.")
        if refs:
            lines.append("We checked the data you cited; it holds, but it does not change our calculation.")
        elif self.n >= 2:
            lines.append("Which figures is that based on? Please send us the data.")
        lines.append("For a 24-month contract, an AS-14404 index clause is mandatory, as we cannot absorb long-term "
                     "material price risks.")
        lines.append(f"Alternatively, with a Preisgleitklausel on AS-14404: €{alt['unit_price']:.2f} per unit.")
        lines.append("Our price follows our main cost drivers: AS-14404, PPI-C2431, LCI-C.")
        lines.append(f"Please note that this Angebot remains valid for {7 if status == 'final_offer' else 30} days.")
        return "\n".join(lines)


def load(path):
    spec = importlib.util.spec_from_file_location("arena_kit.agents._sim_agent", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod.NoIdeaAgent


def run(Agent, draw="low", max_defer=1, verbose=True, xsell=0.0, term36=0.0):
    threads = {sid: [dict(m) for m in ms] for sid, ms in PROBE["threads"].items()}
    sid = next(iter(threads))
    events, sup, agent, log = threads[sid], Donautal(draw, max_defer, xsell, term36), Agent(None), []
    for n in range(1, 11):
        d = agent.decide(CASE, threads)
        msg = d["message"]
        if (act := msg.get("action")):
            if act["type"] == "walk_away":
                return 0.0, "we walked", n - 1, log
            tid = act.get("term_sheet_id") or ""
            if tid.endswith("-a"):
                return 0.0, f"accepted alternative {tid} (arena refuses '-a' ids)", n - 1, log
            t = next(x for x in events[-1]["term_sheets"] if x["term_sheet_id"] == tid)["terms"]
            s = score(complete_offer(CASE, t))
            log.append({"n": n, "us": "accept", "id": tid})
            return s, f"deal {t['unit_price']} @ {t['payment_days']} d db{db_of(t)}", n - 1, log
        sheets = [x["terms"] for x in msg["term_sheets"]]
        refs = msg.get("refs") or []
        sup.body_in = msg.get("body") or ""
        status, prim, alt, body = sup.reply(sheets, refs)
        row = {"n": n, "ours": [(t["unit_price"], t["payment_days"], db_of(t)) for t in sheets],
               "ours_value": round(value(sheets[0]), 3), "refs": refs, "body": msg.get("body"), "status": status,
               "its": prim and (prim["unit_price"], prim["payment_days"], db_of(prim)),
               "its_value": prim and round(value(prim), 3), "score_if_accepted": prim and round(score(prim), 4)}
        log.append(row)
        if verbose:
            print(f"  m{n}: ours {row['ours']} (v {row['ours_value']}) refs {len(refs)} -> {status} {row['its']} "
                  f"v {row['its_value']} score {row['score_if_accepted']}")
        if status == "walked_away":
            return 0.0, "it walked (pushed after final_offer)", n, log
        events += [{**msg, "from": "buyer"},
                   {"from": f"sales@{sid.split(':')[1]}", "status": status, "body": body,
                    "term_sheets": [{"term_sheet_id": f"offer:70710-{n}", "terms": prim}]
                    + ([{"term_sheet_id": f"offer:70710-{n}-a", "terms": alt}] if alt else []),
                    "claim_results": [{"index": i, "result": "verified"} for i in range(min(3, len(refs)))],
                    "signals": {"reply_delay_days": 1, "validity_days": 7 if status == "final_offer" else 30}}]
    return 0.0, "timeout", 10, log


def validate():
    """Feed every live game's own e-mails to the sim (draw read off its first counter); compare reply values."""
    sys.path.insert(0, str(ROOT / "analysis/tools"))
    from engine_dump import load_games
    print("game     | m | live reply (value) | sim reply (value) | diff")
    errs = []
    for sid, g in sorted(load_games("case:P08").items()):
        trace = (g.get("result") or {}).get("trace") or []
        s1 = next((t["move"] for t in trace if t["actor"] != "buyer" and t["round"] == 1), None)
        if not s1:
            continue
        sup, n = Donautal("low" if s1["terms"]["unit_price"] < 5.47 else "high"), 0
        sup.body_in = ""
        for t in trace:
            m = t["move"]
            if t["actor"] == "buyer":
                if m.get("type") == "message":
                    ours = [x["terms"] for x in m["term_sheets"]]
                    sup.body_in = m.get("body") or ""
                    st, prim, _, _ = sup.reply(ours, m.get("refs") or [])
                    n += 1
                continue
            if t["round"] == 0 or n == 0:
                continue
            if not m.get("terms"):
                print(f"{sid[:8]} | {n} | {m['status']} | {st} |")
                continue
            lv, sv = value(m["terms"]), value(prim) if prim else None
            errs.append(abs(lv - sv))
            print(f"{sid[:8]} | {n} | {m['status'][:5]} {m['terms']['unit_price']}@{m['terms']['payment_days']} "
                  f"db{db_of(m['terms'])} ({lv:.3f}) | {st[:5]} {prim['unit_price']}@{prim['payment_days']} "
                  f"db{db_of(prim)} ({sv:.3f}) | {lv - sv:+.3f}")
    errs.sort()
    print(f"replies {len(errs)}: median |diff| {errs[len(errs) // 2]:.3f}, max {errs[-1]:.3f}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("agents", nargs="*", default=[str(ROOT / "analysis/agent_variants/noidea_neel_cloud.py")])
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--save", help="write analysis/offline_runs/P08_sim_<save>_<agent>_<draw>.json")
    ap.add_argument("--max-defer", type=int, default=1)
    a = ap.parse_args()
    if a.validate:
        validate()
        sys.exit()
    for path in a.agents:
        for draw in ("low", "high"):
            print(f"== {Path(path).name} draw {draw}")
            s, end, n, log = run(load(path), draw, a.max_defer)
            print(f"   score {s:.4f}  {end}  ({n} messages)  {'BEATS' if s > HOUSE else 'below'} house {HOUSE}")
            if a.save:
                out = ROOT / f"analysis/offline_runs/P08_sim_{a.save}_{Path(path).stem}_{draw}.json"
                out.write_text(json.dumps({"agent": Path(path).name, "draw": draw, "max_defer": a.max_defer,
                                           "score": s, "end": end, "messages": n, "log": log}, indent=1,
                                          ensure_ascii=False), encoding="utf-8")
