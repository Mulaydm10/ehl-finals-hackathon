"""Build datasets A (supplier dossiers), B (concession profiles), C (pre-verified argument bank)
from the Tacto data package. Stdlib only, deterministic, re-runnable on the Sunday 08:00 release.

    python3 src/datasets/build_abc.py [--data tacto/data] [--out datasets]

Outputs (in --out):
    A_dossiers.json          one dossier per detailed supplier (machine-readable)
    dossiers/<sup>.md        the same dossier as prompt-ready markdown
    B_concessions.json       asked vs settled history per supplier, with summary stats
    C_arguments.jsonl        one citable claim per line: ids, figure, ready-made sentence, use-when
    build_report.json        counts + self-check of every C claim against facts.json
"""
import argparse
import csv
import json
import re
from collections import defaultdict
from datetime import date
from pathlib import Path

TODAY = "2026-09-30"  # the package's "as of" date

# Words in notes/e-mails that hint at what moves a supplier. Tag -> regex.
SIGNALS = {
    "cash_pressure": r"cash|liquidit|bank|credit|loan|pay(ment)? (faster|earlier|sooner)|early payment|prepay|skonto|insolven",
    "needs_volume": r"utili[sz]|idle|empty|short of work|more volume|fill (the|our)|order book|capacity (is )?free|spare capacity",
    "capacity_tight": r"capacity|bottleneck|full(y)? (booked|loaded)|overtime|shift|allocation|lead time",
    "succession_owner": r"owner|successor|retire|son|daughter|family|founder|generation",
    "pride_relationship": r"pride|proud|partnership|loyal|many years|long-standing|reliabl",
    "price_pressure": r"price|increase|surcharge|energy|wage|raw material|index",
    "quality": r"8d|ppm|complain|defect|quality|audit|reject",
    "competitor_or_exit": r"competitor|other customer|customer portfolio|exit|drop|walk|stop supplying|no longer",
    "data_naive": r"spreadsheet|own figures|where (do )?we get|not aware|didn't know|did not know",
}


# The correspondence is built from ~25 fixed templates (docs/EDA_FINDINGS.md section 5). Each one maps
# to a supplier motive and the lever it opens. Phrase -> (motive, lever).
MOTIVES = {
    "could pay earlier": ("cash_short", "trade faster payment for price; it does not squeeze its margin"),
    "the bank is watching": ("cash_short", "trade faster payment for price; avoid demands that cut its margin"),
    "spoke mostly about cash and the banks": ("cash_short", "trade faster payment for price"),
    "pay our invoices within": ("wants_faster_payment", "offer shorter payment days in return for price"),
    "invoices are overdue again": ("we_pay_late", "relationship strain: acknowledge, offer reliable payment"),
    "walk us through their calculation": ("open_book", "ask for the cost breakdown XLSX, negotiate on its elements"),
    "own spreadsheet, last updated two years ago": ("data_naive", "index data disarms it: cite the real driver indices"),
    "had not followed his material and energy prices": ("data_naive", "index data disarms it: cite the real driver indices"),
    "kept supplying at the old price": ("partnership_pride", "acknowledge the partnership; respectful tone; avoid hard threats"),
    "important reference customer": ("values_us_as_reference", "our name is worth something to it: appreciation, longer contract"),
    "second shift has been on hold": ("needs_volume", "offer more volume or a longer contract for price"),
    "half the shop floor was idle": ("needs_volume", "offer more volume or a longer contract for price"),
    "reviewing small accounts": ("may_drop_small_accounts", "low leverage: volume/commitment matters more than price push"),
    "'not strategic'": ("we_are_not_strategic", "low leverage; slower replies; keep it simple, consider walking"),
    "pricing committee": ("approval_ladder", "big moves need the boss: ask for moves under the threshold, be patient"),
    "frozen all price reductions": ("price_frozen", "price will not move: negotiate payment terms and call-off flexibility"),
    "price list applies to all customers": ("price_list_fixed", "price will not move: negotiate logistics and payment"),
    "standard items are not discounted": ("needs_multi_year", "only multi-year volume agreements move price: offer contract length"),
    "bought their": ("hedged_forward", "market index moves don't reach its cost yet: index arguments meet 'not our reality'"),
    "covered at fixed prices until": ("hedged_forward", "market index moves don't reach its cost yet"),
    "binding": ("wants_commitment", "firm long-term commitment buys capacity/priority"),
    "cannot confirm your full forecast": ("capacity_tight", "secure supply first: commitment and lead time over price"),
    "scorecard": ("quality_escalation", "quality case: ppm commitment and chargebacks, cite sc/qn data"),
    "We want one supplier for the kit": ("bundle", "bundling: total kit volume buys price"),
}


def read(data, name):
    with open(data / "data" / f"{name}.csv", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def months_back(month, n):
    y, m = map(int, month.split("-"))
    m -= n
    while m <= 0:
        m += 12
        y -= 1
    return f"{y:04d}-{m:02d}"


def days_between(a, b):
    return (date.fromisoformat(b) - date.fromisoformat(a)).days


def pct_change(later, earlier):
    return round((later / earlier - 1) * 100, 1)


def build(data, out):
    facts = json.loads((data / "facts.json").read_text())
    T = {n: read(data, n) for n in [
        "suppliers", "supplier_intel", "parts", "sourcing", "contracts", "contract_clauses",
        "price_conditions", "negotiation_history", "po_lines", "invoices", "scorecards",
        "quality_notifications", "should_cost", "cost_drivers", "index_series", "index_values",
        "news", "documents", "quotes", "spend_cube"]}

    by = lambda rows, key: _group(rows, key)
    sup = {r["id"]: r for r in T["suppliers"]}
    detailed = [s for s in T["suppliers"] if s["detail"] == "full"]
    intel = {r["supplier_id"]: r for r in T["supplier_intel"]}
    parts = {r["id"]: r for r in T["parts"]}
    sourcing_by_sup, sourcing_by_part = by(T["sourcing"], "supplier_id"), by(T["sourcing"], "part_id")
    ctr = {r["id"]: r for r in T["contracts"]}
    clauses = by(T["contract_clauses"], "contract_id")
    prices = by(T["price_conditions"], "supplier_id")
    neg = by(T["negotiation_history"], "supplier_id")
    pos = by(T["po_lines"], "supplier_id")
    inv = by(T["invoices"], "supplier_id")
    scs = by(T["scorecards"], "supplier_id")
    qns = by(T["quality_notifications"], "supplier_id")
    shc = by(T["should_cost"], "part_id")
    drivers = by(T["cost_drivers"], "part_id")
    series = {r["id"]: r for r in T["index_series"]}
    idx = {(r["series_id"], r["month"]): (r["id"], float(r["value"])) for r in T["index_values"]}
    news = by(T["news"], "supplier_id")
    docs = by(T["documents"], "supplier_id")
    quotes_by_part = by(T["quotes"], "part_id")
    spend = by(T["spend_cube"], "supplier_id")

    def current_price(sid, pid):
        rows = [r for r in prices.get(sid, []) if r["part_id"] == pid and r["valid_from"] <= TODAY
                and (not r["valid_to"] or r["valid_to"] >= TODAY)]
        rows.sort(key=lambda r: r["valid_from"])
        return rows[-1] if rows else None

    def index_change(sid_series, months):
        last = series[sid_series]["last_month"]
        a, b = idx.get((sid_series, months_back(last, months))), idx.get((sid_series, last))
        if not a or not b:
            return None
        return {"ids": [a[0], b[0]], "from": months_back(last, months), "to": last,
                "pct": pct_change(b[1], a[1])}

    A, B, C = {}, {}, []

    def claim(sid, kind, ids, figure, unit, sentence, use_when, part=None, checkable=True, **extra):
        C.append({"supplier": sid, "part": part, "kind": kind, "ids": ids, "figure": figure,
                  "unit": unit, "sentence": sentence, "use_when": use_when,
                  "checked_by_arena": checkable, **extra})

    for s in detailed:
        sid = s["id"]
        it = intel.get(sid, {})
        my_parts = [r for r in sourcing_by_sup.get(sid, [])]
        contract = ctr.get(s["contract_id"]) if s["contract_id"] else None

        # ---- B: concession profile ------------------------------------------------------------
        ev = sorted(neg.get(sid, []), key=lambda r: r["date"])
        pairs = [(num(r["asked_pct"]), num(r["settled_pct"])) for r in ev
                 if num(r["asked_pct"]) is not None and num(r["settled_pct"]) is not None]
        ups = [(a, st) for a, st in pairs if a > 0]
        B[sid] = {
            "supplier": sid, "name": s["name"],
            "events": [{k: r[k] for k in ["date", "part_id", "type", "asked_pct", "settled_pct", "note"]}
                       for r in ev],
            "n_settled": len(pairs),
            "mean_asked_pct": _mean([a for a, _ in pairs]),
            "mean_settled_pct": _mean([st for _, st in pairs]),
            "mean_gap_pts": _mean([a - st for a, st in pairs]),
            # share of an asked increase the supplier actually kept (0 = gave it all up, 1 = kept all)
            "kept_share_of_increase": _mean([st / a for a, st in ups]) if ups else None,
            "ever_below_full_cost": any("below full cost" in r["note"] for r in ev),
        }

        # ---- C: argument bank -------------------------------------------------------------------
        sc_rows = sorted(scs.get(sid, []), key=lambda r: r["quarter"])
        if sc_rows:
            last = sc_rows[-1]
            claim(sid, "scorecard_otd", [last["id"]], num(last["otd_pct"]), "%",
                  f"Your on-time delivery over the last 12 months was {last['otd_pct']}% ({last['id']}).",
                  "push back on price or ask for compensation when OTD is weak (< ~90%)",
                  colour=last["colour"])
            claim(sid, "scorecard_ppm", [last["id"]], num(last["ppm"]), "ppm",
                  f"Your quality over the last 12 months was {last['ppm']} ppm ({last['id']}).",
                  "quality cases, or price cases when ppm is high (> ~500)", colour=last["colour"])

        for d in docs.get(sid, []):
            f = facts.get(d["id"], {})
            if d["asked_pct"] and contract and f.get("days") is not None:
                notice = int(contract["notice_days"] or 0)
                claim(sid, "notice_period", [d["id"], contract["id"]], f["days"], "days",
                      f"Your letter ({d['id']}) gives {f['days']} days' notice, while our contract "
                      f"({contract['id']}) requires {notice} days.",
                      "price-increase letters; strong when letter notice < contract notice",
                      short_notice=f["days"] < notice, asked_pct=num(d["asked_pct"]))

        for n in news.get(sid, []):
            claim(sid, "news", [n["id"]], None, None,
                  f"We noted: {n['headline']} ({n['id']}).", f"topic '{n['topic']}' - use if it weakens their position",
                  topic=n["topic"])

        for src in my_parts:
            pid = src["part_id"]
            cp = current_price(sid, pid)
            for sh in shc.get(pid, []):
                if sh["supplier_id"] in ("", sid) and cp:
                    price = float(cp["price"])
                    claim(sid, "should_cost", [sh["id"]], num(sh["unit_cost"]), "EUR",
                          f"Our should-cost estimate for {parts[pid]['description']} is EUR {sh['unit_cost']} "
                          f"per {cp['price_unit']} ({sh['id']}).",
                          "when price is well above should-cost; note the estimate has 5-15% error and excludes margin",
                          part=pid, current_price=price,
                          price_vs_should_cost_pct=pct_change(price, float(sh["unit_cost"])))
            for dr in drivers.get(pid, []):
                if dr["series_id"] not in series:
                    continue
                for m in (12, 6):
                    ch = index_change(dr["series_id"], m)
                    if not ch or ch["ids"][0] not in facts or ch["ids"][1] not in facts:
                        continue
                    name = series[dr["series_id"]]["name"]
                    claim(sid, "index_change", ch["ids"], ch["pct"], "%",
                          f"{name} changed {ch['pct']:+.1f}% from {ch['from']} to {ch['to']} "
                          f"({ch['ids'][0]}, {ch['ids'][1]}).",
                          "counter cost-driven increases; strongest when the change is below what they ask",
                          part=pid, series=dr["series_id"], weight=num(dr["weight"]), window_months=m)
            my_po = sorted([p for p in pos.get(sid, []) if p["part_id"] == pid], key=lambda r: r["order_date"])
            if len(my_po) >= 2:
                pick = my_po[-8:]
                claim(sid, "po_prices", [p["id"] for p in pick], None, None,
                      f"Our recent orders for {parts[pid]['description']} were at "
                      f"{', '.join(sorted({p['price'] for p in pick}))} per {pick[-1]['price_unit']} "
                      f"({', '.join(p['id'] for p in pick[-3:])}).",
                      "show the price history the supplier has accepted", part=pid)
            for q in quotes_by_part.get(pid, []):
                if q["supplier_id"] != sid:
                    claim(sid, "rival_quote_context", [q["id"]], num(q["unit_price"]), "EUR",
                          f"Another supplier quoted EUR {q['unit_price']} for this part ({q['id']}, {q['quote_date']}).",
                          "context only: the arena checks quotes of THIS case; past quotes show the market",
                          part=pid, checkable=False, rival=q["supplier_id"])

        # ---- A: dossier ------------------------------------------------------------------------
        late = [days_between(r["due_date"], r["paid_date"]) for r in inv.get(sid, []) if r["paid_date"]]
        paid_after = [days_between(r["invoice_date"], r["paid_date"]) for r in inv.get(sid, []) if r["paid_date"]]
        fy_spend = sorted(((r["fiscal_year"], float(r["spend_eur"])) for r in spend.get(sid, [])))
        turnover = num(it.get("turnover_eur"))
        last_spend = fy_spend[-1][1] if fy_spend else None
        q_rows = qns.get(sid, [])

        doc_list = []
        tags = defaultdict(list)
        motives = {}
        for n in news.get(sid, []):
            if n["topic"] not in ("noise", "renamed"):
                motives.setdefault(f"news_{n['topic']}", {"lever": n["headline"], "evidence": []})["evidence"].append(n["id"])
        for d in sorted(docs.get(sid, []), key=lambda r: r["date"]):
            text = (data / d["file"]).read_text(encoding="utf-8").strip()
            doc_list.append({"id": d["id"], "date": d["date"], "kind": d["kind"], "subject": d["subject"],
                             "author": d["author"], "text": text})
            for phrase, (motive, lever) in MOTIVES.items():
                if phrase.lower() in text.lower():
                    motives.setdefault(motive, {"lever": lever, "evidence": []})["evidence"].append(d["id"])
            for sentence in re.split(r"(?<=[.!?])\s+|\n+", text):
                for tag, rx in SIGNALS.items():
                    if re.search(rx, sentence, re.I) and len(sentence) > 20:
                        tags[tag].append(f"{sentence.strip()} [{d['id']}]")

        parts_info = []
        for src in my_parts:
            pid = src["part_id"]
            cp = current_price(sid, pid)
            others = [o["supplier_id"] for o in sourcing_by_part.get(pid, [])
                      if o["supplier_id"] != sid and o["status"] == "active"]
            parts_info.append({
                "part": pid, "description": parts[pid]["description"], "category": parts[pid]["category"],
                "quota_pct": num(src["quota_pct"]), "status": src["status"], "tooling_owner": src["tooling_owner"],
                "other_approved_suppliers": others, "single_source": not others,
                "current_price": num(cp["price"]) if cp else None, "price_unit": cp["price_unit"] if cp else None,
                "price_valid": f"{cp['valid_from']}..{cp['valid_to']}" if cp else None,
                "cost_drivers": [{"series": d["series_id"], "weight": num(d["weight"])} for d in drivers.get(pid, [])],
            })

        sc_trend = [{"quarter": r["quarter"], "otd_pct": num(r["otd_pct"]), "ppm": num(r["ppm"]),
                     "score": num(r["score"]), "colour": r["colour"]} for r in sc_rows[-4:]]
        credit, credit_ago = num(it.get("credit_index")), num(it.get("credit_index_12m_ago"))
        derived = {
            "our_share_of_their_turnover_pct": round(last_spend / turnover * 100, 1) if turnover and last_spend else None,
            "avg_days_we_pay_after_invoice": _mean(paid_after),
            "share_invoices_paid_late": round(sum(1 for x in late if x > 0) / len(late), 2) if late else None,
            "avg_days_late_when_late": _mean([x for x in late if x > 0]),
            # Creditreform-style index: 100 best .. 600 worst; >= 300 means elevated risk
            "credit_risk": None if credit is None else ("high" if credit >= 300 else "medium" if credit >= 250 else "low"),
            "credit_trend": None if credit is None or credit_ago is None else round(credit - credit_ago),
            "low_equity": num(it.get("equity_ratio_pct")) is not None and num(it.get("equity_ratio_pct")) < 20,
            "qn_last_12m": sum(1 for q in q_rows if q["qn_date"] >= "2025-10-01"),
            "recharged_eur_last_12m": round(sum(num(q["cost_recharged_eur"]) or 0 for q in q_rows
                                               if q["qn_date"] >= "2025-10-01"), 2),
        }
        A[sid] = {
            "supplier": sid, "name": s["name"], "country": s["country"], "category": s["category"],
            "abc_class": s["abc_class"],
            "standard_terms": {"payment_days": num(s["payment_days"]), "incoterm": s["incoterm"],
                               "skonto_days": num(s["skonto_days"]), "skonto_pct": num(s["skonto_pct"]),
                               "lead_time_days": num(s["standard_lead_time_days"])},
            "intel": it,
            "contract": None if not contract else {
                **contract, "clauses": [{k: c[k] for k in ["id", "type", "text", "series", "material_share",
                                                           "deadband_pct", "days"]} for c in clauses.get(contract["id"], [])]},
            "parts": parts_info,
            "spend_by_fy": fy_spend,
            "scorecards_last4": sc_trend,
            "derived": derived,
            "concessions": {k: v for k, v in B[sid].items() if k != "events"},
            "motives": motives,
            "signals": {k: v[:8] for k, v in tags.items()},
            "news": [{k: n[k] for k in ["id", "date", "topic", "headline", "body"]} for n in news.get(sid, [])],
            "documents": doc_list,
        }

    # ---- write ---------------------------------------------------------------------------------
    out.mkdir(parents=True, exist_ok=True)
    (out / "dossiers").mkdir(exist_ok=True)
    (out / "A_dossiers.json").write_text(json.dumps(A, indent=1, ensure_ascii=False))
    (out / "B_concessions.json").write_text(json.dumps(B, indent=1, ensure_ascii=False))
    with open(out / "C_arguments.jsonl", "w", encoding="utf-8") as f:
        for c in C:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    for sid, d in A.items():
        (out / "dossiers" / f"{sid.replace(':', '_')}.md").write_text(render_md(d, [c for c in C if c["supplier"] == sid]))

    report = {"suppliers": len(A), "claims": len(C), "claims_by_kind": _count(c["kind"] for c in C),
              "self_check": self_check(C, facts)}
    (out / "build_report.json").write_text(json.dumps(report, indent=1))
    return report


def self_check(C, facts):
    """Recompute every checkable claim from facts.json, using the arena's rules in brief/api.md."""
    ok = bad = 0
    problems = []
    for c in C:
        if not c["checked_by_arena"]:
            continue
        missing = [i for i in c["ids"] if i not in facts]
        if missing:
            bad += 1
            problems.append({"claim": c["sentence"], "missing": missing})
            continue
        if c["kind"] == "index_change":
            a, b = (facts[i]["value"] for i in c["ids"])
            good = abs(pct_change(b, a) - c["figure"]) <= 0.5
        elif c["kind"] == "scorecard_otd":
            good = abs(facts[c["ids"][0]]["otd_pct"] - c["figure"]) <= 0.5
        elif c["kind"] == "scorecard_ppm":
            good = abs(facts[c["ids"][0]]["ppm"] - c["figure"]) <= max(0.01, 0.005 * abs(c["figure"]))
        elif c["kind"] == "should_cost":
            good = abs(facts[c["ids"][0]]["unit_cost"] - c["figure"]) <= max(0.01, 0.005 * c["figure"])
        elif c["kind"] == "notice_period":
            good = facts[c["ids"][0]].get("days") == c["figure"]
        else:
            good = True
        ok += good
        if not good:
            bad += 1
            problems.append({"claim": c["sentence"]})
    return {"ok": ok, "bad": bad, "problems": problems[:20]}


def render_md(d, claims):
    """Prompt-ready dossier: the facts a buyer would want on one page, then the raw notes."""
    L = [f"# {d['name']} ({d['supplier']})",
         f"{d['category']} | {d['country']} | ABC {d['abc_class']} | std terms: {d['standard_terms']}"]
    it = d["intel"]
    if it:
        L.append(f"- Company: {it.get('legal_form')}, founded {it.get('founded')}, {it.get('owner_type')} owned"
                 f"{', parent ' + it['group_parent'] if it.get('group_parent') else ''}, {it.get('staff')} staff, "
                 f"turnover {it.get('turnover_eur') or it.get('turnover_band')}, equity {it.get('equity_ratio_pct')}%, "
                 f"credit index {it.get('credit_index')} (12m ago {it.get('credit_index_12m_ago')}), "
                 f"VDA 6.3 {it.get('vda63_grade')}")
    L.append(f"- Derived: {json.dumps(d['derived'])}")
    L.append(f"- Concession history: {json.dumps(d['concessions'])}")
    if d["contract"]:
        c = d["contract"]
        L.append(f"- Contract {c['id']}: {c['valid_from']}..{c['valid_to']}, notice {c['notice_days']}d, "
                 f"payment {c['payment_days']}d, {c['incoterm']}, price basis '{c['price_basis']}'")
        for cl in c["clauses"]:
            if cl["type"] in ("price", "index", "termination", "payment", "volume"):
                L.append(f"  - {cl['id']} [{cl['type']}]: {cl['text'][:240]}")
    L.append("## Parts")
    for p in d["parts"]:
        L.append(f"- {p['part']} {p['description']}: price {p['current_price']}/{p['price_unit']} ({p['price_valid']}), "
                 f"quota {p['quota_pct']}%, {'SINGLE SOURCE' if p['single_source'] else 'alt: ' + ', '.join(p['other_approved_suppliers'])}, "
                 f"tooling {p['tooling_owner']}, drivers {p['cost_drivers']}")
    if d["motives"]:
        L.append("## Motives (from notes, letters and news - the levers that move this supplier)")
        L += [f"- **{m}**: {v['lever']} ({', '.join(v['evidence'])})" for m, v in d["motives"].items()]
    L.append("## Scorecards (last 4 quarters)")
    L += [f"- {s}" for s in d["scorecards_last4"]]
    if d["signals"]:
        L.append("## Signals from notes and e-mails (keyword hits - read the source)")
        for tag, hits in d["signals"].items():
            L.append(f"- **{tag}**: " + " | ".join(h[:200] for h in hits[:4]))
    L.append("## Citable arguments (pre-checked; one per sentence, max 3 checked per e-mail)")
    for c in claims:
        if c["checked_by_arena"] and c["kind"] != "news":
            warn = ""
            if c["kind"] == "should_cost" and c["price_vs_should_cost_pct"] < 0:
                warn = f" ⚠ DO NOT CITE: current price is {c['price_vs_should_cost_pct']}% below should-cost (helps the supplier)"
            elif c["kind"] == "should_cost":
                warn = f" (price is {c['price_vs_should_cost_pct']:+}% above should-cost)"
            L.append(f"- [{c['kind']}] {c['sentence']}{warn}")
    if d["news"]:
        L.append("## News")
        L += [f"- {n['date']} {n['id']} [{n['topic']}] {n['headline']}: {n['body']}" for n in d["news"]]
    L.append("## Notes, letters and e-mails (chronological)")
    for doc in d["documents"]:
        body = re.sub(r"\s+", " ", doc["text"]).strip()
        L.append(f"- {doc['date']} {doc['id']} [{doc['kind']}] {body[:700]}")
    return "\n".join(L) + "\n"


def _group(rows, key):
    g = defaultdict(list)
    for r in rows:
        g[r[key]].append(r)
    return g


def _mean(xs):
    xs = [x for x in xs if x is not None]
    return round(sum(xs) / len(xs), 2) if xs else None


def _count(it):
    c = defaultdict(int)
    for x in it:
        c[x] += 1
    return dict(c)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="tacto/data", type=Path)
    ap.add_argument("--out", default="datasets", type=Path)
    a = ap.parse_args()
    print(json.dumps(build(a.data, a.out), indent=1))
