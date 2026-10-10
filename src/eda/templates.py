"""Cluster the 208 correspondence docs into their templates (names and numbers masked).
    python3 src/eda/templates.py [tacto/data]"""
import csv, re, sys, collections
from pathlib import Path
E = Path(sys.argv[1] if len(sys.argv) > 1 else "tacto/data")
docs = list(csv.DictReader(open(E / "data/documents.csv")))
names = [r["name"] for r in csv.DictReader(open(E / "data/suppliers.csv"))]
by = collections.defaultdict(list)
for d in docs:
    g = re.sub(r"\s+", " ", (E / d["file"]).read_text().split("\n", 3)[-1].strip())
    for n in names:
        g = g.replace(n, "<SUP>")
    by[d["subject"]].append((d["supplier_id"], re.sub(r"\d[\d.,]*", "#", g)[:330]))
for subj, items in sorted(by.items(), key=lambda x: -len(x[1])):
    c = collections.Counter(g for _, g in items)
    print(f"\n##### {subj} ({len(items)} docs, {len(c)} templates)")
    for g, k in c.most_common():
        print(f" [{k}x {','.join(sorted({s[4:] for s, x in items if x == g}))}] {g}")
