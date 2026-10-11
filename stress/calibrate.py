"""Calibration: replay the REAL buyer e-mails of archived games through sim_supplier.py and compare
the simulated replies with the real ones; fit the hidden parameters per hosted practice supplier.

    python stress/calibrate.py [--cands 160] [--seed 7]

For every hosted practice supplier: games are split by game id into a FIT half and a HOLD-OUT half.
A random search (then a local refinement) over the dynamics parameters minimises, on the FIT half,
  mean |value(sim reply) - value(real reply)| / value(opening)      (in % of the opening)
  + 2 x share of replies whose status differs (open / final_offer / agreed / walked_away)
  + for single-supplier cases, the C_best anchor: |C_best(sim) - C_best(real)| / (C_open - C_best(real))
The comparison of a thread stops at the first reply where one side has ended (agreed, walked) and
the other has not - the real buyer's next e-mail answers a different situation. Writes
stress/fitted_params.json (used by gen_cases.py for the `mirror` archetype) and
stress/calibration_report.json / .md with the fit on both halves.
"""

import argparse
import glob
import hashlib
import json
import math
import random
import statistics as st
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(REPO / "tacto" / "starter-kit"))
sys.path.insert(0, str(HERE))

from arena_kit.cost import must_haves_ok, total_cost  # noqa: E402
from gen_cases import HOSTED, combos, drivers_for  # noqa: E402
from sim_supplier import Session, SimSupplier, best_package_cost  # noqa: E402

FACTS = json.loads((REPO / "tacto" / "data" / "facts.json").read_text())
CASES = {c["case_id"]: c for c in json.loads((REPO / "datasets" / "cases_practice.json").read_text())}


def load_games():
    games = []
    for f in sorted(glob.glob(str(REPO / "datasets" / "runs" / "*.json"))):
        d = json.loads(Path(f).read_text())
        det = d["detail"]
        res = det.get("result") or {}
        if not res.get("trace"):
            continue
        games.append({"game": det["session_id"], "case": det["case_id"], "trace": res["trace"],
                      "c_best": res.get("c_best"), "c_open": res.get("c_open")})
    return games


def infer_grid(games, sid):
    prices = []
    for g in games:
        for t in g["trace"]:
            m = t["move"]
            if t["actor"] == sid and t["round"] > 0 and m.get("status") in ("open", "final_offer") and m.get("terms"):
                prices.append(m["terms"]["unit_price"])
    for grid in (0.5, 0.1, 0.05, 0.01):
        if prices and all(abs(p / grid - round(p / grid)) < 1e-6 for p in prices):
            return grid, len(prices)
    return 0.01, len(prices)


def base_params(case, sid):
    h = HOSTED[sid]
    std, opening = dict(h["standard"]), dict(h["opening"])
    fixed = case.get("fixed_terms", {})
    for f in case["negotiable"]:
        if f != "unit_price" and f not in std:
            std[f] = fixed.get(f, (case.get("term_options", {}).get(f) or [None])[0])
    for f in ("lead_time_days", "incoterm", "volume_per_year", "contract_months", "tooling_eur", "payment_days"):
        if f in fixed:
            std[f] = fixed[f]
    std.setdefault("chargeback_eur_per_complaint", 0.0)
    std.setdefault("incoterm", fixed.get("incoterm", "DAP"))
    std.setdefault("tooling_eur", fixed.get("tooling_eur", 0))
    sc = FACTS.get(f"sc:{sid.split(':')[1]}@2026Q3") or {}
    return {
        "standard": std, "opening": opening, "drivers": drivers_for(set(case["parts"])), "strict_drivers": True,
        "ppm_real": int(sc.get("ppm") or std.get("ppm_commitment") or 500), "full_cost_frac": 0.94,
        "p_walk_final": 0.8, "patience": 5, "insult": 0.1, "min_move": 0.0, "hazard": 0.0,
        "rival_premium": 0.0, "lt_cost": 0.005, "vol_elast": 0.1, "ppm_cost": 0.02, "contract_bonus": 0.003,
        "ix_base": 0.03, "ix_slope": 0.004, "max_payment_days": None, "trust_penalty": 0.0, "alt_std": False,
    }


SPACE = {  # name: (low, high, log)
    "rate": (0.02, 0.15, False), "room": (0.003, 0.35, True), "lam": (0.0005, 0.04, True), "lam_rival": (0.005, 0.15, True),
    "lever_repeat": (0.1, 1.0, False), "fact_pass": (0.1, 1.0, False), "first_frac": (0.02, 0.98, False),
    "recip": (0.05, 1.5, False), "cap": (0.0005, 0.04, True), "final_round": (2, 9, None), "rival_follow": (0.2, 1.0, False),
    "lt_cost": (0.0, 0.01, False), "vol_elast": (0.0, 0.25, False), "ppm_cost": (0.0, 0.06, False),
    "contract_bonus": (0.0, 0.01, False), "ix_base": (-0.01, 0.06, False), "ix_slope": (0.0, 0.008, False),
}


def sample(rng, around=None, scale=1.0):
    out = {}
    for k, (lo, hi, log) in SPACE.items():
        if log is None:
            out[k] = rng.randint(lo, hi) if around is None else max(lo, min(hi, around[k] + rng.choice([-1, 0, 0, 1])))
        elif around is None:
            out[k] = math.exp(rng.uniform(math.log(lo), math.log(hi))) if log else rng.uniform(lo, hi)
        else:
            if log:
                out[k] = min(hi, max(lo, around[k] * math.exp(rng.gauss(0, 0.3 * scale))))
            else:
                out[k] = min(hi, max(lo, around[k] + rng.gauss(0, 0.12 * scale * (hi - lo))))
    return out


def params(case, sid, base, x, types, grid):
    hp = dict(base)
    hp.update({k: x[k] for k in ("rate", "lever_repeat", "fact_pass", "first_frac", "recip", "cap", "final_round", "rival_follow",
                                 "lt_cost", "vol_elast", "ppm_cost", "contract_bonus", "ix_base", "ix_slope")})
    hp["grid"] = grid
    hp["r_base"] = 1 - x["room"]
    hp["levers"] = {t: x["lam"] for t in types if t != "rival_quote"}
    if len(case["suppliers"]) > 1:
        hp["levers"]["rival_quote"] = x["lam_rival"]
    hp["archetype"] = "fit"
    return hp


def replay(case, game, hps, collect=False):
    """Replay one real game; returns per-supplier lists of compared steps."""
    sess = Session(case, FACTS)
    for t in game["trace"]:  # every real offer of the session is citable
        m = t["move"]
        if t["actor"] != "buyer" and m.get("offer_id") and m.get("terms"):
            sess.offers[m["offer_id"]] = (t["actor"], m["terms"])
            for i, a in enumerate(m.get("alternatives") or []):
                if a.get("offer_id"):
                    sess.offers[a["offer_id"]] = (t["actor"], a.get("terms") or {})
    sups = {sid: SimSupplier(case, sid, hps[sid], sess, game["game"]) for sid in hps}
    out = {sid: [] for sid in hps}
    stopped = set()
    last_msg = {}
    for t in game["trace"]:
        m = t["move"]
        if t["actor"] == "buyer":
            sid = m.get("supplier_id")
            if sid not in sups or sid in stopped:
                continue
            if m.get("type") == "timeout":
                last_msg[sid] = ("timeout", None)
            elif m.get("type") == "message":
                last_msg[sid] = ("msg", {"body": m.get("body") or "", "refs": m.get("refs") or [],
                                         "term_sheets": [{"terms": ts.get("terms")} for ts in (m.get("term_sheets") or []) if ts.get("terms")]})
            continue
        sid = t["actor"]
        if sid not in sups or t["round"] == 0 or sid in stopped or sid not in last_msg:
            continue
        kind, msg = last_msg.pop(sid)
        s = sups[sid]
        if s.closed:
            stopped.add(sid)
            continue
        try:
            if kind == "timeout":
                rep = s.timeout()
            else:
                msg["term_sheets"] = [{"terms": {f: ts["terms"].get(f, s.std.get(f)) for f in case["negotiable"]}} for ts in msg["term_sheets"]]
                rep = s.respond(msg)
        except Exception as e:  # noqa
            stopped.add(sid)
            continue
        real_status = m.get("status")
        sim_status = rep["status"]
        v_open = s.v_open
        rv = s.value(s.full(m["terms"])) if m.get("terms") and m["terms"].get("unit_price") else None
        sv = s.value(s.full(rep["term_sheets"][0]["terms"])) if rep["term_sheets"] else None
        err = abs(sv - rv) / v_open if (rv is not None and sv is not None) else None
        step = {"round": t["round"], "real": real_status, "sim": sim_status, "err": err, "kind": kind,
                "real_price": (m.get("terms") or {}).get("unit_price"),
                "sim_price": rep["term_sheets"][0]["terms"]["unit_price"] if rep["term_sheets"] else None,
                "real_v": rv / v_open if rv else None, "sim_v": sv / v_open if sv else None}
        out[sid].append(step)
        ended_r = real_status in ("agreed", "walked_away")
        ended_s = sim_status in ("agreed", "walked_away")
        if ended_r or ended_s:
            stopped.add(sid)
    return out


def score_steps(steps):
    errs = [x["err"] for x in steps if x["err"] is not None]
    mism = [x["real"] != x["sim"] for x in steps]
    if not steps:
        return 0.0, 0.0, 0
    return (st.mean(errs) * 100 if errs else 0.0), (sum(mism) / len(mism)), len(steps)


def c_best_of(case, sid, hp):
    sess = Session(case, FACTS)
    s = SimSupplier(case, sid, hp, sess, 0)
    c, _ = best_package_cost(case, s, total_cost, must_haves_ok, combos(case, s.std), prices=12)
    return c


def objective(case, sid, games, hp_all, anchor):
    steps = []
    for g in games:
        steps += replay(case, g, hp_all)[sid]
    e, mm, n = score_steps(steps)
    obj = e + 2.0 * mm * 100 / 100 * 1.0
    obj = e + 2.0 * mm
    if anchor:
        c_real, c_open = anchor
        cb = c_best_of(case, sid, hp_all[sid])
        obj += abs(cb - c_real) / max(1.0, c_open - c_real)
    return obj, e, mm, n


def split(games):
    fit, hold = [], []
    for g in games:
        (fit if int(hashlib.md5(g["game"].encode()).hexdigest(), 16) % 2 == 0 else hold).append(g)
    return fit, hold


def claim_types_seen(case, sid, games, base):
    sess = Session(case, FACTS)
    hp = dict(base, grid=0.01, r_base=1.0, levers={}, rate=0.07, lever_repeat=0.5, fact_pass=0.5, first_frac=0.1, recip=0.5,
              cap=0.01, final_round=9, rival_follow=0.5, archetype="probe")
    s = SimSupplier(case, sid, hp, sess, 0)
    seen = {}
    for g in games:
        for t in g["trace"]:
            m = t["move"]
            if t["actor"] == "buyer" and m.get("supplier_id") == sid and m.get("type") == "message":
                for ctype, refs, res in s.check_claims({"body": m.get("body") or "", "refs": m.get("refs") or []}):
                    seen[ctype] = seen.get(ctype, 0) + 1
        s.s.used.clear()
    return seen


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--cands", type=int, default=160)
    ap.add_argument("--refine", type=int, default=80)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--only", default="")
    ap.add_argument("--report-only", action="store_true", help="evaluate stress/fitted_params.json, no search")
    a = ap.parse_args(argv)
    games = load_games()
    fitted, report = {}, {}
    hosted_cases = [c for c in CASES.values() if c.get("hosted")]
    for case in hosted_cases:
        cg = [g for g in games if g["case"] == case["case_id"]]
        fit_g, hold_g = split(cg)
        sids = case["suppliers"]
        if a.only and case["case_id"] != a.only:
            continue
        bases = {sid: base_params(case, sid) for sid in sids}
        grids = {sid: infer_grid(cg, sid)[0] for sid in sids}
        types = {sid: sorted(claim_types_seen(case, sid, cg, bases[sid])) for sid in sids}
        rng = random.Random(f"{a.seed}:{case['case_id']}")
        # start every supplier from one random draw; fit suppliers one after the other (coordinate search)
        xs = {sid: sample(rng) for sid in sids}
        hp_all = {sid: params(case, sid, bases[sid], xs[sid], types[sid], grids[sid]) for sid in sids}
        single = len(sids) == 1
        anchor = (cg[0]["c_best"], cg[0]["c_open"]) if single and cg else None
        if a.report_only:
            saved = json.loads((HERE / "fitted_params.json").read_text())
            for sid in sids:
                hp = dict(bases[sid])
                hp.update(saved[sid])
                hp["archetype"] = "fit"
                hp_all[sid] = hp
        for sid in ([] if a.report_only else sids):
            best = (math.inf, None)
            for i in range(a.cands + a.refine):
                x = sample(rng) if (i < a.cands or best[1] is None) else sample(rng, best[1], scale=1.0 if i < a.cands + a.refine // 2 else 0.4)
                trial = dict(hp_all)
                trial[sid] = params(case, sid, bases[sid], x, types[sid], grids[sid])
                obj = objective(case, sid, fit_g, trial, anchor)[0]
                if obj < best[0]:
                    best = (obj, x)
            xs[sid] = best[1]
            hp_all[sid] = params(case, sid, bases[sid], best[1], types[sid], grids[sid])
        for sid in sids:
            hp = hp_all[sid]
            fitted[sid] = {k: hp[k] for k in ("rate", "lever_repeat", "fact_pass", "first_frac", "recip", "cap", "final_round",
                                              "rival_follow", "lt_cost", "vol_elast", "ppm_cost", "contract_bonus", "ix_base",
                                              "ix_slope", "grid", "r_base", "levers")}
            rep = {}
            for name, gs in (("fit", fit_g), ("holdout", hold_g)):
                steps, firsts, finals_r, finals_s, walks_r, walks_s = [], [], [], [], 0, 0
                for g in gs:
                    st_ = replay(case, g, hp_all)[sid]
                    steps += st_
                    if st_ and st_[0]["err"] is not None and st_[0]["kind"] == "msg":
                        firsts.append(st_[0])
                    fr = next((x["round"] for x in st_ if x["real"] == "final_offer"), None)
                    fs = next((x["round"] for x in st_ if x["sim"] == "final_offer"), None)
                    finals_r.append(fr)
                    finals_s.append(fs)
                    walks_r += any(x["real"] == "walked_away" for x in st_)
                    walks_s += any(x["sim"] == "walked_away" for x in st_)
                e, mm, n = score_steps(steps)
                fe = [abs(x["sim_v"] - x["real_v"]) * 100 for x in firsts if x["sim_v"] and x["real_v"]]
                fm = [(x["real_v"] - 1) * 100 for x in firsts if x["real_v"]]
                fsim = [(x["sim_v"] - 1) * 100 for x in firsts if x["sim_v"]]
                both = [(r, s) for r, s in zip(finals_r, finals_s) if r is not None or s is not None]
                rep[name] = {
                    "games": len(gs), "steps": n, "mean_abs_value_err_pct": round(e, 3), "status_mismatch": round(mm, 3),
                    "first_counter_abs_err_pct": round(st.mean(fe), 3) if fe else None,
                    "first_counter_real_pct_median": round(st.median(fm), 2) if fm else None,
                    "first_counter_sim_pct_median": round(st.median(fsim), 2) if fsim else None,
                    "final_round_same": sum(r == s for r, s in both), "final_round_pairs": len(both),
                    "final_rounds_real": [r for r, _ in both], "final_rounds_sim": [s for _, s in both],
                    "walks_real": walks_r, "walks_sim": walks_s,
                    "status_pairs": dict(sorted({f"{x['real']}->{x['sim']}": sum(1 for y in steps if (y['real'], y['sim']) == (x['real'], x['sim'])) for x in steps}.items())),
                }
            if single and cg:
                rep["c_best_real"] = cg[0]["c_best"]
                rep["c_best_sim"] = round(c_best_of(case, sid, hp_all[sid]), 2)
                rep["c_open"] = cg[0]["c_open"]
            rep["grid"] = grids[sid]
            rep["claim_types_seen"] = types[sid]
            rep["fitted"] = fitted[sid]
            report[f"{case['case_id']} {sid}"] = rep
            print(case["case_id"], sid, json.dumps({k: rep[k] for k in ("fit", "holdout")}, default=str)[:600], flush=True)
    out = HERE / "fitted_params.json"
    if not a.report_only:
        old = json.loads(out.read_text()) if out.exists() and a.only else {}
        old.update(fitted)
        out.write_text(json.dumps(old, indent=1))
    rp = HERE / "calibration_report.json"
    oldr = json.loads(rp.read_text()) if rp.exists() and a.only else {}
    oldr.update(report)
    rp.write_text(json.dumps(oldr, indent=1, default=str))


if __name__ == "__main__":
    main()
