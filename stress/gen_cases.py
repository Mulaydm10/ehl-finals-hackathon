"""Generate the FIXED, seeded stress test set: synthetic cases that copy the 19 practice cases
(parts, suppliers, data, negotiable fields, term options, buyer block, refs) but give every supplier
NEW hidden behaviour, drawn from distributions somewhat wider than the ones measured in the archived
real games (stress/ENGINE_MODEL.md), and a perturbed opening price.

    python stress/gen_cases.py [--per 10] [--seed 20261011] [--out stress/cases]

Each case file is the practice case file as the arena would send it, plus the key `_hidden` (the
harness strips it before the agent sees the case): template, per-supplier archetype and parameters,
standard terms, opening, and the yardsticks c_open / c_best / c_alt with the best package.
Hosted practice templates start from parameters fitted to their real games
(stress/fitted_params.json, written by stress/calibrate.py); the 9 practice cases that were never
hosted start from the pooled ranges.
"""

import argparse
import csv
import itertools
import json
import math
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(REPO / "tacto" / "starter-kit"))
sys.path.insert(0, str(HERE))

from arena_kit.cost import must_haves_ok, total_cost  # noqa: E402
from sim_supplier import Session, SimSupplier, best_package_cost  # noqa: E402

PRACTICE = REPO / "datasets" / "cases_practice.json"
FACTS = REPO / "tacto" / "data" / "facts.json"
DRIVERS = REPO / "tacto" / "data" / "data" / "cost_drivers.csv"
FITTED = HERE / "fitted_params.json"

# Standard terms and opening quote of the hosted practice suppliers, read off the archived games
# (opening term sheets; deal terms closed on standard terms; "Our standard Zahlungsziel is ..").
HOSTED = {
    "sup:70110": {"standard": {"payment_days": 30, "ppm_commitment": 900, "effective_date": "2026-11-01"},
                  "opening": {"unit_price": 138.55, "effective_date": "2026-11-01"}},
    "sup:70510": {"standard": {"payment_days": 30, "ppm_commitment": 250, "index_clause": None},
                  "opening": {"unit_price": 370.96, "payment_days": 30, "index_clause": None}},
    "sup:70530": {"standard": {"payment_days": 30, "ppm_commitment": 350, "contract_months": 12, "volume_per_year": 4580},
                  "opening": {"unit_price": 438.21, "payment_days": 30, "contract_months": 12, "volume_per_year": 4580}},
    "sup:70620": {"standard": {"payment_days": 30, "ppm_commitment": 150, "contract_months": 12},
                  "opening": {"unit_price": 4.96, "payment_days": 30, "contract_months": 12}},
    "sup:70210": {"standard": {"payment_days": 30, "ppm_commitment": 1200, "lead_time_days": 28},
                  "opening": {"unit_price": 36.0}},
    "sup:70240": {"standard": {"payment_days": 45, "ppm_commitment": 1400, "lead_time_days": 52},
                  "opening": {"unit_price": 31.5, "lead_time_days": 52}},
    "sup:70250": {"standard": {"payment_days": 30, "ppm_commitment": 600, "lead_time_days": 28},
                  "opening": {"unit_price": 38.5}},
    "sup:70610": {"standard": {"payment_days": 30, "ppm_commitment": 80, "contract_months": 12},
                  "opening": {"unit_price": 5.74, "payment_days": 30, "contract_months": 12}},
    "sup:70710": {"standard": {"payment_days": 30, "ppm_commitment": 50, "contract_months": 12, "index_clause": None},
                  "opening": {"unit_price": 6.05, "payment_days": 30, "index_clause": None, "contract_months": 12}},
    "sup:70410": {"standard": {"payment_days": 30, "ppm_commitment": 300, "lead_time_days": 54, "volume_per_year": 19890, "contract_months": 12},
                  "opening": {"unit_price": 32.2, "lead_time_days": 54, "volume_per_year": 19890, "contract_months": 12}},
    "sup:70140": {"standard": {"payment_days": 60, "ppm_commitment": 6400, "chargeback_eur_per_complaint": 0.0},
                  "opening": {"unit_price": 47.0, "ppm_commitment": 6400}},
    "sup:70740": {"standard": {"payment_days": 30, "ppm_commitment": 70, "contract_months": 12, "index_clause": None},
                  "opening": {"unit_price": 6.1, "payment_days": 30, "index_clause": None, "contract_months": 12}},
}
# margin (%) at the opening value, from the real relationship charges: P01 6.3, P02 0.7, P03 9.2; P10 deals never
# paid one (margin >= 10 % at the deal), so its opening margin is set to 14 %
OPEN_MARGIN = {"sup:70110": 6.3, "sup:70510": 0.7, "sup:70530": 9.2, "sup:70410": 14.0}
LEVER_TYPES = ["index_change", "should_cost", "price_history", "quality", "volume_change", "news", "notice", "contract"]
ARCHETYPES = [("mirror", 0.44), ("boulware", 0.09), ("conceder", 0.09), ("data_driven", 0.1), ("cash_short", 0.09),
              ("walker", 0.09), ("monopolist", 0.1)]


def pooled(rng, price, rfq):
    """The pooled ranges: what any practice supplier showed, widened."""
    grids = [g for g in (0.01, 0.05, 0.1, 0.5) if g / price <= 0.02] or [0.01]
    hp = {
        "grid": rng.choice(grids),
        "rate": rng.uniform(0.03, 0.12),
        "r_base": 1 - rng.uniform(0.005, 0.12),
        "levers": {t: (rng.uniform(0.002, 0.02) if rng.random() < 0.4 else 0.0) for t in LEVER_TYPES},
        "lever_repeat": rng.uniform(0.2, 0.9),
        "fact_pass": rng.uniform(0.3, 1.0),
        "first_frac": rng.uniform(0.05, 0.9),
        "recip": rng.uniform(0.2, 1.2),
        "cap": rng.uniform(0.002, 0.03),
        "final_round": rng.randint(2, 7),
        "p_walk_final": rng.uniform(0.4, 1.0),
        "patience": rng.randint(2, 6),
        "insult": rng.uniform(0.03, 0.15),
        "min_move": rng.uniform(0.0, 0.12),
        "hazard": rng.uniform(0.02, 0.1) if rng.random() < 0.3 else 0.0,
        "rival_follow": rng.uniform(0.3, 1.0),
        "rival_premium": rng.uniform(0.0, 0.03),
        "lt_cost": rng.uniform(0.002, 0.008),
        "vol_elast": rng.uniform(0.0, 0.2),
        "ppm_cost": rng.uniform(0.0, 0.05),
        "contract_bonus": rng.uniform(0.0, 0.008),
        "ix_base": rng.uniform(-0.01, 0.05),
        "ix_slope": rng.uniform(0.001, 0.006),
        "max_payment_days": rng.choice([45, 60]) if rng.random() < 0.3 else None,
        "trust_penalty": rng.uniform(0.0, 0.01),
        "alt_std": rng.random() < 0.5,
        "strict_drivers": rng.random() < 0.7,
    }
    if rfq:
        hp["levers"]["rival_quote"] = rng.uniform(0.01, 0.06)
    return hp


def jitter(rng, x, rel=0.3, lo=None, hi=None):
    y = x * math.exp(rng.gauss(0, rel))
    if lo is not None:
        y = max(lo, y)
    if hi is not None:
        y = min(hi, y)
    return y


def mirror(rng, fit, base):
    """Around the parameters fitted to the real supplier of the template - widened."""
    hp = dict(base)
    for k in ("rate", "first_frac", "recip", "cap", "fact_pass", "lever_repeat", "lt_cost", "vol_elast", "ppm_cost", "contract_bonus"):
        if k in fit:
            hp[k] = jitter(rng, max(fit[k], 1e-4), 0.35)
    if "rival_follow" in fit:
        hp["rival_follow"] = min(1.0, jitter(rng, fit["rival_follow"], 0.3))
    hp["first_frac"] = min(hp["first_frac"], 0.97)
    hp["fact_pass"] = min(hp["fact_pass"], 1.0)
    if "r_base" in fit:
        room = (1 - fit["r_base"]) * rng.uniform(0.6, 1.6)
        hp["r_base"] = 1 - room
    if "levers" in fit:
        scale = rng.uniform(0.5, 1.6)
        hp["levers"] = {t: v * scale * rng.uniform(0.6, 1.4) for t, v in fit["levers"].items()}
    if "final_round" in fit:
        hp["final_round"] = max(1, min(9, fit["final_round"] + rng.randint(-1, 2)))
    for k in ("grid", "ix_base", "ix_slope", "max_payment_days"):
        if k in fit:
            hp[k] = fit[k]
    # walking from an open thread was rare in the real games (about 2 % of threads): mild walk rules
    hp.update(patience=rng.randint(4, 6), insult=rng.uniform(0.08, 0.15), min_move=rng.uniform(0.0, 0.05),
              hazard=0.0 if rng.random() < 0.9 else rng.uniform(0.01, 0.04), p_walk_final=rng.uniform(0.6, 1.0))
    return hp


def apply_archetype(rng, name, hp):
    if name == "boulware":
        hp.update(first_frac=rng.uniform(0.02, 0.15), recip=rng.uniform(0.1, 0.4), cap=rng.uniform(0.001, 0.004),
                  final_round=rng.randint(2, 3), p_walk_final=rng.uniform(0.9, 1.0))
        hp["levers"] = {t: v * 0.5 for t, v in hp["levers"].items()}
    elif name == "conceder":
        hp.update(first_frac=rng.uniform(0.5, 0.95), recip=rng.uniform(0.8, 1.5), cap=rng.uniform(0.01, 0.04),
                  final_round=rng.randint(6, 8), p_walk_final=rng.uniform(0.3, 0.6), patience=rng.randint(5, 7))
    elif name == "data_driven":
        hp["r_base"] = 1 - rng.uniform(0.003, 0.02)
        kinds = rng.sample(LEVER_TYPES, rng.randint(3, 5))
        hp["levers"] = {t: (rng.uniform(0.01, 0.05) if t in kinds else 0.0) for t in LEVER_TYPES} | (
            {"rival_quote": hp["levers"]["rival_quote"]} if "rival_quote" in hp["levers"] else {})
        hp["fact_pass"] = rng.uniform(0.8, 1.0)
    elif name == "cash_short":
        hp["rate"] = rng.uniform(0.12, 0.24)
        hp["usual_rate"] = rng.uniform(0.04, 0.07)
    elif name == "walker":
        hp.update(patience=rng.randint(1, 3), hazard=rng.uniform(0.05, 0.15), p_walk_final=1.0,
                  insult=rng.uniform(0.02, 0.05), min_move=rng.uniform(0.1, 0.2))
    elif name == "monopolist":
        hp["r_base"] = 1 - rng.uniform(0.0, 0.01)
        hp["levers"] = {t: rng.uniform(0.0, 0.003) for t in hp["levers"]}
        hp.update(final_round=rng.randint(2, 3), first_frac=rng.uniform(0.0, 0.3))
    return hp


def drivers_for(parts):
    out = set()
    with open(DRIVERS) as f:
        for r in csv.DictReader(f):
            if r["part_id"] in parts:
                out.add(r["series_id"])
    return sorted(out)


def standard_and_opening(rng, case, sid, facts, i_sup):
    """Standard terms and the opening sheet: the real ones for hosted suppliers, generated otherwise."""
    neg, opts, fixed, b = case["negotiable"], case.get("term_options", {}), case.get("fixed_terms", {}), case["buyer"]
    cur = b.get("current_unit_price") or b["fallback_unit_price"]
    if sid in HOSTED and case.get("hosted"):
        std = dict(HOSTED[sid]["standard"])
        opening = dict(HOSTED[sid]["opening"])
    else:
        sc = facts.get(f"sc:{sid.split(':')[1]}@2026Q3") or {}
        std = {"payment_days": rng.choice([30, 30, 30, 45, 60]), "ppm_commitment": max(50, int(round((sc.get("ppm") or 400) / 50) * 50)),
               "chargeback_eur_per_complaint": 0.0}
        if "lead_time_days" in neg:
            o = sorted(opts.get("lead_time_days") or [42])
            std["lead_time_days"] = rng.choice(o[len(o) // 2:]) + rng.choice([0, 0, 3, 7])
        if "volume_per_year" in neg:
            o = sorted(opts["volume_per_year"])
            std["volume_per_year"] = o[0] if case["type"] == "capacity" else o[len(o) // 2]
        if "contract_months" in neg:
            std["contract_months"] = 12
        if "index_clause" in neg:
            std["index_clause"] = None
        if "tooling_eur" in neg:
            std["tooling_eur"] = max(opts.get("tooling_eur") or [0])
        if "effective_date" in neg:
            std["effective_date"] = min(opts["effective_date"])
        if "chargeback_eur_per_complaint" in neg:
            std["chargeback_eur_per_complaint"] = 0.0
        doc = facts.get(case.get("trigger_doc") or "") or {}
        if case["type"] == "price_increase" and doc.get("asked_price"):
            price = float(doc["asked_price"])
        elif case["type"] == "rfq":
            price = cur * rng.uniform(0.85, 1.12)
        elif case["type"] == "quality":
            price = cur * rng.uniform(1.0, 1.05)
        elif case["type"] == "capacity":
            price = cur * rng.uniform(1.03, 1.10)
        else:
            price = cur * rng.uniform(0.92, 1.12)
        opening = {"unit_price": round(price, 2)}
        stated = [f for f in neg if f != "unit_price" and rng.random() < 0.7]
        for f in stated:
            opening[f] = std.get(f, fixed.get(f))
    for f in neg:  # every negotiable field has a standard value
        if f != "unit_price" and f not in std:
            std[f] = fixed.get(f, (opts.get(f) or [None])[0])
    for f in ("lead_time_days", "incoterm", "volume_per_year", "contract_months", "tooling_eur", "payment_days"):
        if f in fixed:
            std[f] = fixed[f]
    std.setdefault("chargeback_eur_per_complaint", 0.0)
    std.setdefault("incoterm", fixed.get("incoterm", "DAP"))
    std.setdefault("tooling_eur", fixed.get("tooling_eur", 0))
    return std, opening


def combos(case, std):
    fields = [f for f in case["negotiable"] if f != "unit_price"]
    opts = []
    for f in fields:
        o = list(case.get("term_options", {}).get(f) or [])
        if std.get(f) not in o:
            o.append(std.get(f))
        opts.append(o)
    return [dict(zip(fields, c)) for c in itertools.product(*opts)]


def yardsticks(case, hidden, facts):
    """c_open (cheapest opening that keeps the must-haves; all openings if none does), c_alt, c_best."""
    sess = Session(case, facts)
    sups = {sid: SimSupplier(case, sid, hp, sess, 0) for sid, hp in hidden["suppliers"].items()}
    opens = []
    for sid, s in sups.items():
        o = hidden["suppliers"][sid]["opening"]
        opens.append((must_haves_ok(case, o, s.std), total_cost(case, o, s.std, s.relationship_supplier(o)), sid))
    keep = [x for x in opens if x[0]] or opens
    c_open = min(c for _, c, _ in keep)
    alt = case["buyer"].get("alternative") or {}
    c_alt = total_cost(case, alt["terms"]) if (alt.get("terms") or {}).get("unit_price") else None
    best = (math.inf, None, None)
    for sid, s in sups.items():
        c, t = best_package_cost(case, s, total_cost, must_haves_ok, combos(case, s.std), prices=61)
        if c < best[0]:
            best = (c, t, sid)
    c_best = min(best[0], c_alt) if c_alt is not None else best[0]
    return {"c_open": round(c_open, 2), "c_alt": c_alt, "c_best": round(c_best, 2),
            "best_package": {"supplier_id": best[2], "terms": best[1], "c": round(best[0], 2)},
            "best_is_alternative": c_alt is not None and c_alt <= best[0]}


def make_hidden(rng, case, facts, fitted, variant):
    rfq = len(case["suppliers"]) > 1
    drivers = drivers_for(set(case["parts"]))
    hidden = {"template": case["case_id"], "variant": variant, "suppliers": {}}
    for i, sid in enumerate(case["suppliers"]):
        std, opening = standard_and_opening(rng, case, sid, facts, i)
        price = opening["unit_price"]
        if case.get("hosted"):  # perturbed opening price
            opening["unit_price"] = round(price * rng.uniform(0.96, 1.05), 2)
        base = pooled(rng, opening["unit_price"], rfq)
        arche = rng.choices([a for a, _ in ARCHETYPES], [w for _, w in ARCHETYPES])[0]
        fit = fitted.get(sid) if case.get("hosted") else None
        hp = mirror(rng, fit, base) if (arche == "mirror" and fit) else dict(base)
        hp = apply_archetype(rng, arche, hp)
        if rfq and "rival_quote" not in hp["levers"]:
            hp["levers"]["rival_quote"] = rng.uniform(0.01, 0.06)
        sust = case["buyer"].get("sustainable_margin_pct") or 3
        if case.get("hosted") and sid in OPEN_MARGIN:  # read off the real relationship charges (ENGINE_MODEL.md)
            m = max(sust - 0.5, OPEN_MARGIN[sid] + rng.uniform(-1.5, 1.5)) / 100
        else:  # real openings sat 0-3.3 points above the sustainable margin: widened to 0-6
            m = rng.uniform(sust, sust + 6) / 100
        sc = facts.get(f"sc:{sid.split(':')[1]}@2026Q3") or {}
        hp.update({
            "archetype": arche,
            "standard": std,
            "opening": opening,
            "drivers": drivers,
            "ppm_real": int(max(20, (sc.get("ppm") or std.get("ppm_commitment") or 500) * rng.uniform(0.7, 1.3))),
            "full_cost_frac": 1 - m,
            "usual_rate": hp.get("usual_rate", hp["rate"]),
        })
        hp["r_base"] = min(hp["r_base"], 1.0)
        hidden["suppliers"][sid] = hp
    hidden.update(yardsticks(case, hidden, facts))
    return hidden


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--per", type=int, default=10, help="variants per practice template")
    ap.add_argument("--seed", type=int, default=20261011)
    ap.add_argument("--out", default=str(HERE / "cases"))
    a = ap.parse_args(argv)
    cases = json.load(open(PRACTICE))
    facts = json.load(open(FACTS))
    fitted = json.load(open(FITTED)) if FITTED.exists() else {}
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("*.json"):
        old.unlink()
    n = 0
    summary = []
    for case in cases:
        for v in range(a.per):
            rng = random.Random(f"{a.seed}:{case['case_id']}:{v}")
            hidden = make_hidden(rng, case, facts, fitted, v)
            n += 1
            cid = f"case:ST{n:03d}"
            c = json.loads(json.dumps(case))
            c.update(case_id=cid, set="stress")
            c.pop("hosted", None)
            c["_hidden"] = hidden
            (out / f"{cid[5:]}.json").write_text(json.dumps(c, indent=1))
            summary.append({"case_id": cid, "template": case["case_id"], "type": case["type"],
                            "archetypes": {s: h["archetype"] for s, h in hidden["suppliers"].items()},
                            "c_open": hidden["c_open"], "c_best": hidden["c_best"], "c_alt": hidden["c_alt"]})
    (out / "_index.jsonl").write_text("\n".join(json.dumps(s) for s in summary) + "\n")
    print(f"wrote {n} cases to {out}")


if __name__ == "__main__":
    main()
