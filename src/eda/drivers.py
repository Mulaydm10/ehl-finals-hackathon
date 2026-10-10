"""Supplier features vs concessions + practice case table.  uv run --with pandas python src/eda/drivers.py <dir with data/ and cases_practice.json>"""
import json, sys, re
from pathlib import Path
import pandas as pd, numpy as np
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40); pd.set_option("display.max_rows", 200)
E = Path(sys.argv[1]); D = E / "data" / "data"
r = lambda n: pd.read_csv(D / f"{n}.csv")
sup, intel, neg, pc, inv, sc, qn, shc, cd, iv, ise, news, docs, quotes, rfq, spend, src, ctr, cl, parts, po = [r(n) for n in
 "suppliers supplier_intel negotiation_history price_conditions invoices scorecards quality_notifications should_cost cost_drivers index_values index_series news documents quotes rfqs spend_cube sourcing contracts contract_clauses parts po_lines".split()]
cases = json.load(open(E / "cases_practice.json"))

print("=== PRACTICE CASES ===")
rows = []
for c in cases:
    b = c["buyer"]; alt = b.get("alternative") or {}
    rows.append(dict(case=c["case_id"][5:], type=c["type"], goal=b["category_goal"], hosted=c.get("hosted"),
        sups=",".join(s[4:] for s in c["suppliers"]), neg="/".join(c["negotiable"]), cur=b.get("current_unit_price"),
        fb=b.get("fallback_unit_price"), alt=alt.get("kind"), altp=(alt.get("terms") or {}).get("unit_price"),
        fb_risk=b.get("fallback_risk_pct"), idx_risk=b.get("index_risk_pct"), rel_eur_pt=b.get("relationship_eur_per_point"),
        sust_m=b.get("sustainable_margin_pct"), must=";".join(map(str, b.get("must_haves", []))), yrs=b.get("horizon_years"), need=b.get("need_per_year")))
print(pd.DataFrame(rows).to_string())
print("\nbuyer keys:", sorted({k for c in cases for k in c["buyer"]}))
print("negotiable fields:", pd.Series([f for c in cases for f in c["negotiable"]]).value_counts().to_dict())

print("\n=== NEGOTIATION HISTORY ===")
neg["gap"] = neg.asked_pct - neg.settled_pct
n2 = neg.dropna(subset=["asked_pct"])
print(n2[["asked_pct", "settled_pct", "gap"]].describe().round(2).T)
print("note values:", neg.note.fillna("").value_counts().to_dict())
n2 = n2.assign(year=n2.date.str[:4], up=n2.asked_pct > 0)
print(n2.groupby("year")[["asked_pct", "settled_pct", "gap"]].mean().round(2))
print("asked>0 vs <=0:\n", n2.groupby("up")[["asked_pct", "settled_pct", "gap"]].agg(["mean", "count"]).round(2))
n2["kept"] = np.where(n2.asked_pct > 0, n2.settled_pct / n2.asked_pct, np.nan)
# attach supplier features
it = intel.set_index("supplier_id")
s = sup.set_index("id")
last_sc = sc.sort_values("quarter").groupby("supplier_id").last()
fy = spend.sort_values("fiscal_year").groupby("supplier_id").last().spend_eur
src_n = src[src.status == "active"].groupby("part_id").supplier_id.nunique()
feat = pd.DataFrame(index=sup[sup.detail == "full"].id)
feat["name"] = s.name; feat["cat"] = s.category; feat["country"] = s.country; feat["abc"] = s.abc_class; feat["pay_terms"] = s.payment_days
for c in ["owner_type", "staff", "turnover_eur", "equity_ratio_pct", "credit_index", "credit_index_12m_ago", "vda63_grade", "group_parent", "founded"]:
    feat[c] = it[c]
feat["credit_delta"] = feat.credit_index - feat.credit_index_12m_ago
feat["otd"] = last_sc.otd_pct; feat["ppm"] = last_sc.ppm; feat["sc_colour"] = last_sc.colour; feat["sc_score"] = last_sc.score
feat["our_spend"] = fy; feat["share_pct"] = (fy / feat.turnover_eur * 100).round(1)
inv["late"] = (pd.to_datetime(inv.paid_date) - pd.to_datetime(inv.due_date)).dt.days
inv["paid_after"] = (pd.to_datetime(inv.paid_date) - pd.to_datetime(inv.invoice_date)).dt.days
feat["we_pay_late_share"] = inv.groupby("supplier_id").late.apply(lambda x: (x > 0).mean()).round(2)
feat["we_pay_after_d"] = inv.groupby("supplier_id").paid_after.mean().round(1)
feat["late_avg_d"] = inv[inv.late > 0].groupby("supplier_id").late.mean().round(1)
sp = src.merge(src_n.rename("n_src"), left_on="part_id", right_index=True)
feat["single_src_parts"] = sp[sp.n_src == 1].groupby("supplier_id").part_id.count()
feat["n_parts"] = src.groupby("supplier_id").part_id.count()
feat["qn_12m"] = qn[qn.qn_date >= "2025-10-01"].groupby("supplier_id").id.count()
feat["n_docs"] = docs.groupby("supplier_id").id.count()
feat["n_news"] = news.groupby("supplier_id").id.count()
g = n2.groupby("supplier_id")
feat["neg_n"] = g.size(); feat["asked_m"] = g.asked_pct.mean().round(2); feat["settled_m"] = g.settled_pct.mean().round(2)
feat["gap_m"] = g.gap.mean().round(2); feat["kept_m"] = g.kept.mean().round(2)
feat["below_cost"] = neg[neg.note.fillna("").str.contains("below")].groupby("supplier_id").size()
feat = feat.fillna({"single_src_parts": 0, "qn_12m": 0, "n_docs": 0, "n_news": 0, "below_cost": 0})
feat.to_csv(E / "features.csv")
print("\n=== SUPPLIER FEATURE TABLE ===")
print(feat.drop(columns=["name"]).to_string())

print("\n=== WHAT CORRELATES WITH CONCESSION (gap = asked - settled, kept = settled/asked) ===")
num = feat.select_dtypes("number")
print(num.corr(method="spearman")[["gap_m", "kept_m", "settled_m", "asked_m"]].round(2).sort_values("gap_m").to_string())
for col in ["owner_type", "cat", "country", "sc_colour", "vda63_grade", "abc"]:
    print(f"\nby {col}:\n", feat.groupby(col)[["gap_m", "kept_m", "asked_m", "settled_m", "share_pct", "equity_ratio_pct", "credit_index"]].mean().round(2).assign(n=feat.groupby(col).size()).to_string())
