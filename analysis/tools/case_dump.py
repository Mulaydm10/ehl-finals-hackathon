"""Everything the data package says about one practice case, for the N1 deep dives.

    cd tacto/starter-kit && uv run python ../../analysis/tools/case_dump.py P01

Prints: case file, trigger letter + notice check, per supplier/part the raw rows (price
conditions, negotiation history, PO prices, invoices, QNs, quotes, forecasts, spend, sourcing,
news), cost-driver justification (12m / 6m), should-cost, and the € value of each lever via
arena_kit.total_cost.
"""

import csv
import json
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tacto" / "starter-kit"))
from arena_kit.cost import cost_breakdown, total_cost  # noqa: E402

DATA = ROOT / "tacto" / "data"
T = DATA / "data"


def rows(name):
    with open(T / f"{name}.csv", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def case(cid):
    cid = cid if cid.startswith("case:") else f"case:{cid}"
    return next(c for c in json.load(open(ROOT / "datasets" / "cases_practice.json", encoding="utf-8"))
                if c["case_id"] == cid)


def h(title):
    print(f"\n## {title}")


def index_change(series, months):
    vals = sorted((r["month"], float(r["value"])) for r in IDX if r["series_id"] == series)
    last_m, last_v = vals[-1]
    y, m = map(int, last_m.split("-"))
    m -= months
    while m <= 0:
        y, m = y - 1, m + 12
    start = f"{y:04d}-{m:02d}"
    sv = dict(vals).get(start)
    return (start, last_m, None if sv is None else (last_v / sv - 1) * 100)


IDX = rows("index_values")


def dump(cid):
    c = case(cid)
    b = c["buyer"]
    sups, parts = c["suppliers"], c["parts"]
    h("Case file")
    print(json.dumps({k: c[k] for k in ("case_id", "type", "title", "negotiable", "fixed_terms",
                                        "term_options", "round_limit", "refs")}, ensure_ascii=False))
    print("briefing:", c["briefing"])
    print("buyer:", json.dumps(b, ensure_ascii=False))

    h("Trigger")
    docs = {d["id"]: d for d in rows("documents")}
    trig = docs.get(c.get("trigger_doc") or "")
    if trig:
        print({k: trig[k] for k in ("id", "date", "kind", "asked_pct", "asked_price", "effective_date", "notice_days")})
        print((DATA / trig["file"]).read_text(encoding="utf-8"))
    else:
        print("trigger_doc:", c.get("trigger_doc"))

    clauses = rows("contract_clauses")
    contracts = {r["supplier_id"]: r for r in rows("contracts")}
    for s in sups:
        ctr = contracts.get(s)
        if ctr:
            print(f"contract {ctr['id']}: {ctr['valid_from']}..{ctr['valid_to']} pay {ctr['payment_days']} "
                  f"{ctr['incoterm']} notice {ctr['notice_days']} basis {ctr['price_basis']}")
            for cl in clauses:
                if cl["contract_id"] == ctr["id"]:
                    print(f"  {cl['id']} [{cl['type']}] {cl['text']} {cl['series'] or ''} {cl['days'] or ''}")

    sup_rows = {r["id"]: r for r in rows("suppliers")}
    intel = {r["supplier_id"]: r for r in rows("supplier_intel")}
    for s in sups:
        h(f"Supplier {s} {sup_rows[s]['name']}")
        print("master:", {k: sup_rows[s][k] for k in ("country", "payment_days", "skonto_days", "skonto_pct",
                                                      "incoterm", "standard_lead_time_days")})
        print("intel:", intel.get(s))
        print("docs:", [d["id"] for d in docs.values() if d["supplier_id"] == s])
        for r in rows("news"):
            if r["supplier_id"] == s:
                print(f"  news {r['id']} {r['topic']}: {r['headline']} | {r['body']}")
        print("spend:", [(r["fiscal_year"], r["spend_eur"]) for r in rows("spend_cube") if r["supplier_id"] == s])
        print("sourcing (all its parts):", [(r["part_id"], r["status"], r["quota_pct"], r["tooling_owner"])
                                            for r in rows("sourcing") if r["supplier_id"] == s])
        print("scorecards:", [(r["quarter"], r["otd_pct"], r["ppm"], r["colour"])
                              for r in rows("scorecards") if r["supplier_id"] == s][-6:])
        inv = [r for r in rows("invoices") if r["supplier_id"] == s and r["paid_date"]]
        late = [(date.fromisoformat(r["paid_date"]) - date.fromisoformat(r["due_date"])).days for r in inv]
        if late:
            print(f"invoices: n={len(inv)} late share={sum(x > 0 for x in late) / len(late):.2f} "
                  f"mean days late (late ones)={mean([x for x in late if x > 0] or [0]):.1f} "
                  f"max={max(late)} skonto taken={sum(r['discount_taken'] == 'true' for r in inv)}")
        qns = [r for r in rows("quality_notifications") if r["supplier_id"] == s]
        recent = [r for r in qns if r["qn_date"] >= "2025-10-01"]
        by_defect = defaultdict(int)
        for r in recent:
            by_defect[r["defect"]] += 1
        print(f"QNs total {len(qns)}, last 12m {len(recent)}, recharged 12m "
              f"{sum(float(r['cost_recharged_eur'] or 0) for r in recent):.0f} EUR, defects {dict(by_defect)}")

    for p in parts:
        h(f"Part {p}")
        print("part:", next(r for r in rows("parts") if r["id"] == p))
        print("sourcing:", [(r["supplier_id"], r["status"], r["quota_pct"], r["tooling_owner"])
                            for r in rows("sourcing") if r["part_id"] == p])
        print("price_conditions:")
        for r in rows("price_conditions"):
            if r["part_id"] == p:
                print(f"  {r['supplier_id']} {r['valid_from']}..{r['valid_to']} {r['price']} {r['basis']} {r['event_id']}")
        print("negotiation_history:")
        for r in rows("negotiation_history"):
            if r["part_id"] == p:
                print(f"  {r['event_id']} {r['date']} {r['type']} asked {r['asked_pct']} settled {r['settled_pct']} {r['note']}")
        pol = [r for r in rows("po_lines") if r["part_id"] == p]
        prices = defaultdict(list)
        for r in pol:
            prices[(r["supplier_id"], r["price"])].append(r["order_date"])
        print(f"po_lines: {len(pol)}")
        for (s, pr), ds in sorted(prices.items(), key=lambda kv: min(kv[1])):
            print(f"  {s} {pr}: {len(ds)} lines {min(ds)}..{max(ds)}")
        odd = [r for r in pol if r["change_type"] or r["price_note"]]
        for r in odd[:15]:
            print(f"  ! {r['id']} {r['order_date']} {r['price']} change={r['change_type']} note={r['price_note']}")
        print("quotes:")
        rfq = {r["id"]: r for r in rows("rfqs")}
        for r in rows("quotes"):
            if r["part_id"] == p:
                q = rfq.get(r["rfq_id"], {})
                print(f"  {r['id']} {r['quote_date']} {r['supplier_id']} {r['unit_price']} lt {r['lead_time_days']} "
                      f"{r['incoterm']} pay {r['payment_days']} tool {r['tooling_eur']} awarded {r['awarded']} "
                      f"missing {r['missing_fields']} | {r['remarks']} | rfq {q.get('purpose')} {q.get('qty_per_year')}")
        fcs = [r for r in rows("forecasts") if r["part_id"] == p]
        print("forecasts (last 6 snapshots):", [(r["snapshot_month"], r["qty_next_12m"]) for r in fcs[-6:]])
        drivers = [r for r in rows("cost_drivers") if r["part_id"] == p]
        if drivers:
            print("cost drivers:")
            j12 = j6 = 0.0
            for d in drivers:
                w = float(d["weight"])
                s12, e12, c12 = index_change(d["series_id"], 12)
                s6, e6, c6 = index_change(d["series_id"], 6)
                j12 += w * (c12 or 0)
                j6 += w * (c6 or 0)
                print(f"  {d['series_id']} w={w}: 12m {s12}->{e12} {c12:+.1f}% | 6m {s6}->{e6} {c6:+.1f}%")
            print(f"  justified change: 12m {j12:+.2f}%  6m {j6:+.2f}%  (weights sum {sum(float(d['weight']) for d in drivers):.2f})")
        for r in rows("should_cost"):
            if r["part_id"] == p:
                print(f"should_cost {r['id']} {r['supplier_id']} {r['unit_cost']} (mat {r['material_eur']} conv "
                      f"{r['conversion_eur']} oh {r['overhead_eur']}) ±{r['confidence_pct']}% vs current "
                      f"{b.get('current_unit_price')}: price/cost-1 = "
                      f"{(float(b['current_unit_price']) / float(r['unit_cost']) - 1) * 100 if b.get('current_unit_price') else float('nan'):+.1f}%")

    h("Alternative")
    alt = b.get("alternative") or {}
    if alt.get("terms"):
        print(f"C_alt = {total_cost(c, alt['terms']):,.2f}  ({alt['kind']} {alt.get('ref')})")
        print(cost_breakdown(c, alt["terms"]))
    else:
        print("alternative:", alt)


def lever_table(c, base, standard=None, supplier=None):
    """€ effect of moving each lever from `base` (C(variant) − C(base)); negative = saves us money."""
    c0 = total_cost(c, base, standard, supplier)
    out = [("base", base, c0, 0.0)]

    def add(label, **chg):
        t = {**base, **chg}
        cc = total_cost(c, t, standard, supplier)
        out.append((label, t, cc, cc - c0))

    if "unit_price" in base:
        add("price -1%", unit_price=round(base["unit_price"] * 0.99, 2))
    for field, opts in c.get("term_options", {}).items():
        if field in c["negotiable"]:
            for o in opts:
                if o != base.get(field):
                    add(f"{field}={o}", **{field: o})
    return out


if __name__ == "__main__":
    dump(sys.argv[1])
