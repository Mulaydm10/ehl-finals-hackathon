"""Does our round-1 WORDING predict P11's first counter (46.00 vs 46.50)? All games with the 300/0 @ 42.77 single sheet."""
import json, re, collections
from pathlib import Path
ROOT = Path.home() / "Dhruv/ehl-finals-hackathon"
rows = []
for f in sorted((ROOT / "datasets/runs").glob("*.json")):
    g = json.loads(f.read_text())
    if (g["session"].get("case_id") or g["detail"].get("case_id")) != "case:P11" or len(g["threads"]) != 1:
        continue
    ms = next(iter(g["threads"].values()))["messages"]
    if len(ms) < 3 or not ms[1].get("term_sheets"):
        continue
    sh = [(x["terms"].get("ppm_commitment"), x["terms"].get("chargeback_eur_per_complaint")) for x in ms[1]["term_sheets"]]
    if sh != [(300, 0)]:
        continue
    body = ms[1].get("body") or ""
    first = ms[2]["term_sheets"][0]["terms"]["unit_price"]
    opening = body.split("\n\n")[1] if len(body.split("\n\n")) > 1 else ""
    rows.append((first, f.stem[:8], body, opening))
print(len(rows), "games:", collections.Counter(r[0] for r in rows))
feats = {"straight talk / late pay": r"Straight talk", "call-off attached": r"call-off schedule", "punitive / penalt": r"(?i)punitive|penalt",
         "chargeback word": r"(?i)chargeback", "trust": r"(?i)trust", "confidence": r"(?i)confidence", "partnership": r"(?i)partnership",
         "question mark in opening": r"\?", "8D request": r"8D report", "documented complaints": r"(?i)documented complaints",
         "reliable/reliability": r"(?i)reliab", "prove": r"(?i)prove|proving"}
for name, rx in feats.items():
    lo = [bool(re.search(rx, r[2])) for r in rows if r[0] == 46.0]
    hi = [bool(re.search(rx, r[2])) for r in rows if r[0] == 46.5]
    print(f"{name:28s} low-draw {sum(lo)}/{len(lo)}   high-draw {sum(hi)}/{len(hi)}")
lo_len = [len(r[2].split()) for r in rows if r[0] == 46.0]; hi_len = [len(r[2].split()) for r in rows if r[0] == 46.5]
print("words: low", sorted(lo_len), " high", sorted(hi_len))
for r in rows:
    print(r[0], r[1], "|", r[3][:170].replace("\n", " "))
