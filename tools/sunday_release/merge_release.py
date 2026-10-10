"""Merge the Sunday release (new news, letters, a memo - NEW IDs only) into tacto/data, which the agent and
src/datasets/build_abc.py read. Defensive: the release format is unknown until 08:00, so it
  - unions facts.json (new ids only; an existing id with a different value is reported, not overwritten),
  - appends CSV rows whose first column (the id) is new, for any CSV whose header matches ours (else copies it next to
    ours as <name>.release.csv and reports it),
  - copies every other file (letters, memo, PDFs, .md) into the same relative path if it does not exist yet.
    python3 tools/sunday_release/merge_release.py tacto/starter-kit/data/release-sunday tacto/data   [--dry]"""
import csv
import json
import shutil
import sys
from pathlib import Path

src, dst = Path(sys.argv[1]), Path(sys.argv[2])
dry = "--dry" in sys.argv
assert src.is_dir(), f"no release folder at {src}"
report = {"facts_new": 0, "facts_conflict": [], "csv_rows_new": {}, "csv_unmatched": [], "files_new": [], "files_skipped": []}
# 1. facts.json
for rel_facts in sorted(src.rglob("facts.json")):
    new = json.loads(rel_facts.read_text(encoding="utf-8"))
    ours_p = dst / "facts.json"
    ours = json.loads(ours_p.read_text(encoding="utf-8"))
    for k, v in new.items():
        if k not in ours:
            ours[k] = v
            report["facts_new"] += 1
        elif ours[k] != v:
            report["facts_conflict"].append(k)
    if not dry:
        ours_p.write_text(json.dumps(ours, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    prefixes = {}
    for k in new:
        prefixes[k.split(":")[0]] = prefixes.get(k.split(":")[0], 0) + 1
    report["facts_by_prefix"] = prefixes
# 2. CSVs + 3. other files
for f in sorted(src.rglob("*")):
    if not f.is_file() or f.name == "facts.json":
        continue
    rel = f.relative_to(src)
    target = dst / rel
    if f.suffix == ".csv":
        # find our CSV with the same name anywhere under dst (the release may not mirror the folder layout)
        ours = target if target.exists() else next(iter(sorted(dst.rglob(f.name))), None)
        rows = list(csv.reader(f.open(encoding="utf-8")))
        if ours and rows:
            our_rows = list(csv.reader(ours.open(encoding="utf-8")))
            if our_rows and our_rows[0] == rows[0]:
                have = {r[0] for r in our_rows[1:] if r}
                add = [r for r in rows[1:] if r and r[0] not in have]
                report["csv_rows_new"][str(ours.relative_to(dst))] = len(add)
                if add and not dry:
                    with ours.open("a", newline="", encoding="utf-8") as fh:
                        csv.writer(fh).writerows(add)
                continue
        side = (ours.parent if ours else target.parent) / (f.stem + ".release.csv")
        report["csv_unmatched"].append(f"{rel} -> {side.relative_to(dst)}")
        if not dry:
            side.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, side)
        continue
    if target.exists():
        report["files_skipped"].append(str(rel))
        continue
    report["files_new"].append(str(rel))
    if not dry:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, target)
print(json.dumps(report, indent=1, ensure_ascii=False)[:6000])
