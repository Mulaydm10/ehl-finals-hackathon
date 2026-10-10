"""Every live game of one practice case, round by round, in the supplier's own cash terms (offline, no quota).

    cd tacto/starter-kit && uv run python ../../analysis/tools/engine_dump.py P02 [--rate 0.066] [--reasons] [--json out.json]

Reads datasets/runs/*.json and tools/replays/raw/*.json (de-duplicated by session) and tools/replays/backoffice/.
Per round: our sheets, the claims the arena read from our e-mail, its status, primary + alternative sheets, its cash
value per unit (`supplier_value` at `--rate`, its standard terms), the claim results and its reasons. Used for
analysis/cases/P02_engine.md and P08_engine.md (the method of analysis/central/LEARNINGS.md section 6).
"""

import argparse
import glob
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tacto/starter-kit"))
from arena_kit.cost import supplier_value  # noqa: E402


def load_games(case_id):
    games = {}
    for f in sorted(glob.glob(str(ROOT / "datasets/runs/*.json"))):
        s = json.loads(Path(f).read_text(encoding="utf-8"))
        d = s.get("detail") or {}
        if d.get("case_id") == case_id and d.get("session_id"):
            games[d["session_id"]] = d
    for f in sorted(glob.glob(str(ROOT / "tools/replays/raw/*.json"))):
        s = json.loads(Path(f).read_text(encoding="utf-8"))
        if s.get("case_id") == case_id and s.get("session_id") and s["session_id"] not in games:
            games[s["session_id"]] = s
    return games


def backoffice(case, sid):
    p = ROOT / f"tools/replays/backoffice/{case}_{sid}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def fmt_terms(t):
    if not t:
        return "-"
    out = [f"{t.get('unit_price')}"]
    for f, short in (("payment_days", "d"), ("contract_months", "m"), ("lead_time_days", "lt"), ("volume_per_year", "v")):
        if t.get(f) is not None:
            out.append(f"{t[f]}{short}")
    ic = t.get("index_clause")
    if "index_clause" in t:
        out.append(f"{ic['series']}db{ic['deadband_pct']:g}" if ic else "noclause")
    for f in ("ppm_commitment", "chargeback_eur_per_complaint", "effective_date"):
        if t.get(f) is not None:
            out.append(f"{f.split('_')[0]}={t[f]}")
    return " ".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("case")
    ap.add_argument("--rate", type=float, default=0.08, help="the supplier's cash rate (calibration.json)")
    ap.add_argument("--reasons", action="store_true", help="print the supplier's reasons in words")
    ap.add_argument("--json", help="write the per-round rows to this file")
    a = ap.parse_args()
    case_id = f"case:{a.case}"
    case = {c["case_id"]: c for c in json.loads((ROOT / "datasets/cases_practice.json").read_text(encoding="utf-8"))}[case_id]
    dossiers = json.loads((ROOT / "datasets/A_dossiers.json").read_text(encoding="utf-8"))
    rows = []
    for sid, g in sorted(load_games(case_id).items(), key=lambda x: x[1].get("created_at") or 0):
        r = g.get("result") or {}
        trace = r.get("trace") or []
        print(f"\n=== {sid}  score {r.get('score')}  end {g.get('end_reason')}  deal {fmt_terms(r.get('terms') if r.get('deal') else None)}"
              f"  c_deal {r.get('c_deal')}  rel {round((r.get('cost_breakdown') or {}).get('relationship', 0), 2)}")
        sup_std = {}
        for t in trace:
            m, actor = t.get("move") or {}, t.get("actor")
            if actor == "buyer":
                sheets = [fmt_terms(ts.get("terms")) for ts in m.get("term_sheets") or []]
                claims = [(c.get("type"), c.get("refs"), c.get("asserted")) for c in (m.get("interpreted") or {}).get("claims") or []]
                act = (m.get("action") or {}).get("type") if m.get("action") else m.get("type")
                print(f" R{t['round']} BUYER {act}: {sheets}  claims {claims}")
                rows.append({"session": sid, "round": t["round"], "actor": "buyer", "sheets": [ts.get("terms") for ts in m.get("term_sheets") or []],
                             "claims": claims, "body": m.get("body")})
                continue
            if not sup_std:
                d = dossiers.get(actor, {})
                sup_std = {**{k: v for k, v in (d.get("standard_terms") or {}).items() if v is not None},
                           **{k: v for k, v in (m.get("terms") or {}).items() if k != "unit_price"}}
            est = {"standard": sup_std, "interest_rate": a.rate}
            prim = m.get("terms") or {}
            val = round(supplier_value(case, prim, est), 2) if prim.get("unit_price") else None
            alts = [(fmt_terms(x.get("terms")), round(supplier_value(case, x["terms"], est), 2)) for x in m.get("alternatives") or []
                    if (x.get("terms") or {}).get("unit_price")]
            print(f" R{t['round']} {m.get('status'):<11} {fmt_terms(prim)}  value {val}  alts {alts}  claims {m.get('claim_results')}"
                  f"  validity {(m.get('signals') or {}).get('validity_days')}")
            if a.reasons:
                for x in t.get("reasons") or []:
                    print(f"      - {x}")
            rows.append({"session": sid, "round": t["round"], "actor": actor, "status": m.get("status"), "terms": prim,
                         "value": val, "alternatives": m.get("alternatives"), "claim_results": m.get("claim_results"),
                         "reasons": t.get("reasons"), "text": m.get("text")})
        bo = backoffice(a.case, sid)
        if bo and a.reasons:
            calls = [f"R{x['round']} {x['from']}->{x['to']}: {x['text']}" for x in bo
                     if "My call" in x["text"] or x["from"] != "Key Account Manager" or "approv" in x["text"].lower()]
            for c in calls:
                print(f"      BO {c}")
    if a.json:
        Path(a.json).write_text(json.dumps(rows, indent=1, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
