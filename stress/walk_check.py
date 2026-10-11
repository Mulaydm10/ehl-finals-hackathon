"""Before/after check of the walk rules: replay every real buyer e-mail of the archived games through the simulator
(fitted parameters, walk parameters drawn per thread from the `mirror` distribution of walk model 1 = stress/cases and
walk model 2 = stress/cases_v2) and count the same events walk_stats.py counts in the real replies. Also counts the
walks in stress runs (report_<label>.json).

    python stress/walk_check.py [--runs v1 v1_c2]   -> stress/walk_check.json
"""

import argparse
import json
import random
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "tacto" / "starter-kit"))
sys.path.insert(0, str(HERE))

from calibrate import CASES, FACTS, base_params, load_games  # noqa: E402
from gen_cases import walk_v2  # noqa: E402
from sim_supplier import Session, SimSupplier  # noqa: E402

FIT = json.loads((HERE / "fitted_params.json").read_text())
STATS = json.loads((HERE / "walk_stats.json").read_text())


def walk_v1(wr):
    return {"walk_model": 1, "patience": wr.randint(4, 6), "insult": wr.uniform(0.08, 0.15), "min_move": wr.uniform(0.0, 0.05),
            "hazard": 0.0 if wr.random() < 0.9 else wr.uniform(0.01, 0.04), "p_walk_final": wr.uniform(0.6, 1.0)}


def replay_counts(model):
    c = Counter()
    for g in load_games():
        case = CASES[g["case"]]
        rfq = len(case["suppliers"]) > 1
        kind = "rfq" if rfq else "single"
        sess = Session(case, FACTS)
        for t in g["trace"]:
            m = t["move"]
            if t["actor"] != "buyer" and m.get("offer_id") and m.get("terms"):
                sess.offers[m["offer_id"]] = (t["actor"], m["terms"])
        sups = {}
        for sid in case["suppliers"]:
            hp = dict(base_params(case, sid))
            hp.update(FIT[sid])
            wr = random.Random(f"check:{g['game']}:{sid}")
            hp.update(walk_v1(wr) if model == 1 else walk_v2(wr, "mirror", rfq))
            hp["archetype"] = "mirror"
            sups[sid] = SimSupplier(case, sid, hp, sess, g["game"])
            c[f"{kind} threads"] += 1
        last_kind = {}
        for t in g["trace"]:
            m = t["move"]
            if t["actor"] != "buyer":
                continue
            sid = m.get("supplier_id")
            s = sups.get(sid)
            if s is None or s.closed:
                continue
            if m.get("type") == "timeout":
                s.timeout()
                last_kind[sid] = "timeout"
                continue
            if m.get("type") != "message":
                continue
            msg = {"body": m.get("body") or "", "refs": m.get("refs") or [],
                   "term_sheets": [{"terms": {f: ts["terms"].get(f, s.std.get(f)) for f in case["negotiable"]}}
                                   for ts in (m.get("term_sheets") or []) if ts.get("terms")]}
            before = s.status
            rep = s.respond(msg)
            if before == "final_offer":
                c[f"{kind} push -> {rep['status']}"] += 1
            if rep["status"] == "walked_away" and before == "open":
                c[f"{kind} open-thread walks"] += 1
    return c


def run_counts(label):
    path = HERE / f"report_{label}.json"
    if not path.exists():
        return None
    rep = json.loads(path.read_text())
    c = Counter()
    for r in rep["results"]:
        kind = "rfq" if r["suppliers"] > 1 else "single"
        for sid, t in r["threads"].items():
            c[f"{kind} threads"] += 1
            walks = [h for h in t["history"] if h.get("kind") == "walk"]
            for w in walks:
                why = w.get("why", "")
                if "final" in why:
                    c[f"{kind} walks after a push past final"] += 1
                elif "capacity" in why:
                    c[f"{kind} open-thread walks (hazard)"] += 1
                else:
                    c[f"{kind} open-thread walks (patience: insult / no move / slow / contradicted)"] += 1
            c[f"{kind} pushes past final"] += sum(1 for h in t["history"] if h.get("kind") == "final_hold") + sum(1 for w in walks if "final" in w.get("why", ""))
    return c


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", nargs="*", default=["v1", "v1_c2"])
    a = ap.parse_args()
    out = {"real": {"single threads": STATS["threads_by_kind"]["single"], "rfq threads": STATS["threads_by_kind"]["rfq"],
                    "open-thread walks": len(STATS["open_walks"]), "push": STATS["push"], "push_vs_final": STATS["push_vs_final"],
                    "nomove_next": STATS["nomove_next"], "insult_5pct_next": STATS["insult_next"].get("5%")},
           "replay_walk_model_1": dict(replay_counts(1)), "replay_walk_model_2": dict(replay_counts(2))}
    for lab in a.runs:
        rc = run_counts(lab)
        if rc is not None:
            out[f"run_{lab}"] = dict(rc)
    (HERE / "walk_check.json").write_text(json.dumps(out, indent=1))
    for k, v in out.items():
        print(k, json.dumps(v, sort_keys=True))


if __name__ == "__main__":
    main()
