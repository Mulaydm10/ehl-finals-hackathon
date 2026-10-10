"""Index trends, cost justification, should-cost, payments, RFQs, clauses, news.  uv run --with pandas python src/eda/levers.py <dir>"""
import json, sys, re
from pathlib import Path
import pandas as pd, numpy as np
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40); pd.set_option("display.max_rows", 300); pd.set_option("display.max_colwidth", 120)
E = Path(sys.argv[1]); D = E / "data" / "data"
r = lambda n: pd.read_csv(D / f"{n}.csv")
neg, pc, iv, ise, cd, shc, docs, quotes, rfq, parts, src, inv, sc, cl, news, po = [r(n) for n in
 "negotiation_history price_conditions index_values index_series cost_drivers should_cost documents quotes rfqs parts sourcing invoices scorecards contract_clauses news po_lines".split()]
cases = json.load(open(E / "cases_practice.json"))
case_sups = {s: c["case_id"][5:] for c in cases for s in c["suppliers"]}

print("=== INDEX SERIES: 12m / 6m / 24m change to last month ===")
iv["month"] = iv.month.astype(str)
piv = iv.pivot(index="month", columns="series_id", values="value")
rows = []
for s in ise.itertuples():
    col = piv[s.id].dropna(); last = col.index[-1]
    def ch(n):
        y, m = map(int, last.split("-")); m -= n
        while m <= 0: m += 12; y -= 1
        k = f"{y:04d}-{m:02d}"
        return round((col[last] / col[k] - 1) * 100, 1) if k in col else None
    rows.append(dict(id=s.id, name=s.name[:55], last=last, v=col[last], ch3=ch(3), ch6=ch(6), ch12=ch(12), ch24=ch(24), peak=col.idxmax(), off_peak=round((col[last] / col.max() - 1) * 100, 1)))
idx = pd.DataFrame(rows).set_index("id"); print(idx.to_string())

print("\n=== COST DRIVERS: weight sums per part (is weight = cost share?) ===")
w = cd.groupby("part_id").weight.sum(); print(w.describe().round(2).to_dict())
cd = cd.merge(idx[["ch12"]], left_on="series_id", right_index=True, how="left")
cd["contrib"] = cd.weight * cd.ch12
just = cd.groupby("part_id").contrib.sum().round(2).rename("justified_pct_12m")

print("\n=== PRICE-INCREASE TRIGGERS vs COST-JUSTIFIED CHANGE ===")
letters = docs[docs.asked_pct.notna()].copy()
letters["part"] = letters.part_ids.str.split(";").str[0]
letters = letters.merge(just, left_on="part", right_index=True, how="left")
letters["case"] = letters.supplier_id.map(case_sups)
letters["unjustified_pts"] = letters.asked_pct - letters.justified_pct_12m
print(letters[["id", "case", "supplier_id", "part", "asked_pct", "justified_pct_12m", "unjustified_pts", "effective_date", "notice_days", "subject"]].to_string())
print("\nper-part drivers for trigger parts:")
print(cd[cd.part_id.isin(letters.part)].sort_values(["part_id", "weight"], ascending=[True, False]).to_string())

print("\n=== PAST NEGOTIATIONS vs INDEX: did asks/settlements track cost drivers? ===")
# index change over the 12m before each event, weighted by the part's drivers
def drv_change(pid, date):
    m = date[:7]; y, mm = map(int, m.split("-")); prev = f"{y-1:04d}-{mm:02d}"
    t = 0
    for d in cd[cd.part_id == pid].itertuples():
        col = piv[d.series_id].dropna()
        a = col[col.index <= prev]; b = col[col.index <= m]
        if len(a) and len(b): t += d.weight * (b.iloc[-1] / a.iloc[-1] - 1) * 100
    return t
n2 = neg.dropna(subset=["asked_pct"]).copy()
n2["drv12"] = [drv_change(p, d) for p, d in zip(n2.part_id, n2.date)]
print(n2[["asked_pct", "settled_pct", "drv12"]].corr().round(2))
n2["asked_minus_drv"] = n2.asked_pct - n2.drv12; n2["settled_minus_drv"] = n2.settled_pct - n2.drv12
print(n2[["drv12", "asked_minus_drv", "settled_minus_drv"]].describe().round(2).T)
X = np.c_[np.ones(len(n2)), n2.asked_pct, n2.drv12]; beta = np.linalg.lstsq(X, n2.settled_pct, rcond=None)[0]
print("OLS settled = %.2f + %.2f*asked + %.2f*drv12" % tuple(beta), " R2=%.3f" % (1 - ((n2.settled_pct - X @ beta) ** 2).sum() / ((n2.settled_pct - n2.settled_pct.mean()) ** 2).sum()))
print("gap distribution:", n2.eval("asked_pct-settled_pct").round(1).value_counts().sort_index().to_dict())

print("\n=== SHOULD-COST vs CURRENT PRICE ===")
cur = pc[(pc.valid_from <= "2026-09-30") & (pc.valid_to.isna() | (pc.valid_to >= "2026-09-30"))].sort_values("valid_from").groupby(["part_id", "supplier_id"]).last().reset_index()
s2 = shc.merge(cur[["part_id", "supplier_id", "price"]], on=["part_id", "supplier_id"], how="left")
s2["price_over_cost_pct"] = ((s2.price / s2.unit_cost - 1) * 100).round(1); s2["case"] = s2.supplier_id.map(case_sups)
print(s2[["id", "part_id", "supplier_id", "case", "cost_base", "unit_cost", "price", "price_over_cost_pct", "material_eur", "conversion_eur", "overhead_eur", "confidence_pct", "method"]].to_string())

print("\n=== PAYMENT BEHAVIOUR (we as buyer) ===")
inv["late"] = (pd.to_datetime(inv.paid_date) - pd.to_datetime(inv.due_date)).dt.days
print(inv.late.describe().round(1).to_dict()); print("discount_taken:", inv.discount_taken.value_counts().to_dict())
lt = inv.groupby("supplier_id").late.agg(late_share=lambda x: (x > 0).mean(), mean_late="mean", max_late="max").round(2)
lt["case"] = lt.index.map(case_sups); print(lt.sort_values("mean_late", ascending=False).head(15).to_string())

print("\n=== RFQs & QUOTES ===")
print(rfq.purpose.value_counts().to_dict(), rfq.status.value_counts().to_dict())
q = quotes.merge(rfq[["id", "qty_per_year", "purpose"]], left_on="rfq_id", right_on="id", suffixes=("", "_rfq"))
q["rank"] = q.groupby("rfq_id").unit_price.rank(); q["n"] = q.groupby("rfq_id").unit_price.transform("size")
q["vs_min_pct"] = ((q.unit_price / q.groupby("rfq_id").unit_price.transform("min") - 1) * 100).round(1)
print("awarded quote price rank:", q[q.awarded == True]["rank"].value_counts().to_dict())
print("spread within RFQ (max/min-1 %):", q.groupby("rfq_id").vs_min_pct.max().describe().round(1).to_dict())
print("missing_fields:", q.missing_fields.fillna("").value_counts().head(8).to_dict())
print("remarks:"); print(q.remarks.dropna().value_counts().to_string())
aw = q[q.awarded == True]; print("awarded but not cheapest:"); print(aw[aw["rank"] > 1][["rfq_id", "supplier_id", "unit_price", "vs_min_pct", "lead_time_days", "payment_days", "remarks"]].to_string())

print("\n=== CONTRACT CLAUSES ===")
print(cl.type.value_counts().to_dict())
print(cl[cl.type.isin(["index", "price"])][["id", "type", "series", "material_share", "deadband_pct", "days", "text"]].head(30).to_string())

print("\n=== NEWS topics ===")
news["case"] = news.supplier_id.map(case_sups); print(news.topic.value_counts().to_dict())
print(news[["date", "supplier_id", "case", "topic", "headline"]].to_string())

print("\n=== DOCUMENTS: kind x subject ===")
print(pd.crosstab(docs.subject, docs.kind).to_string())
