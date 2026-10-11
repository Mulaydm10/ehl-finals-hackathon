"""(v7) review F1: in an RFQ, one bidder's unusable final (it breaks a must-have) must never walk the WHOLE case - a
walk_away ends the case (api.md), and the other bidders still hold valid offers. (v7) review F4: an unreadable attachment
must not raise."""
import json
from pathlib import Path

from arena_kit.agents import noidea
from arena_kit.agents.noidea_rfq import NoIdeaAgent
from arena_kit.docs import read_document

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "datasets" / "cases_practice.json").exists())
CASES = {c["case_id"]: c for c in json.loads((ROOT / "datasets/cases_practice.json").read_text())}
DOS = json.loads((ROOT / "datasets/A_dossiers.json").read_text())


def opening(case, sid, j):  # as notes/analysis_v234/crash_test.py: ~6% above today's price, its standard terms
    d = DOS.get(sid, {})
    part = case["parts"][0]
    p = next((x for x in d.get("parts", []) if x["part"] == part), {})
    cur = case["buyer"].get("current_unit_price") or p.get("current_price") or 50.0
    t = {"unit_price": round(float(cur) * (1.06 + 0.02 * j), 2)}
    std = d.get("standard_terms") or {}
    for f in case["negotiable"]:
        if f == "unit_price":
            continue
        opts = case.get("term_options", {}).get(f) or []
        t[f] = std[f] if f in std and std[f] is not None and (not opts or std[f] in opts) else (opts[0] if opts else None)
    num = sid.split(":")[-1]
    return {"from": f"sales@{num}", "status": "open", "body": "Thank you for your enquiry. Please find our offer below.",
            "term_sheets": [{"term_sheet_id": f"offer:{num}-0", "terms": {k: v for k, v in t.items() if v is not None}}]}


def rfq_with_unusable_final():
    case = CASES["case:P05"]
    threads = {sid: [opening(case, sid, j)] for j, sid in enumerate(case["suppliers"])}
    bad = "sup:70240"
    others = [s for s in threads if s != bad]
    top = max(threads[s][0]["term_sheets"][0]["terms"]["unit_price"] for s in others)
    ours = dict(threads[bad][0]["term_sheets"][0]["terms"])
    final = {**ours, "unit_price": round(top * 1.02, 2), "lead_time_days": 56}  # dearer than the others, 56 d > 42 d
    threads[bad] += [{"from": "buyer", "term_sheets": [{"terms": ours}], "body": "Our proposal."},
                     {"from": "sales@70240", "status": "final_offer", "body": "This is our final offer.",
                      "term_sheets": [{"term_sheet_id": "offer:70240-1", "terms": final}]}]
    return case, threads, bad


def test_unusable_final_does_not_walk_the_rfq():
    case, threads, bad = rfq_with_unusable_final()
    a = NoIdeaAgent()
    a.focus = {bad}  # its reply is the one that is in
    d = a.decide(case, threads)
    assert (d["message"].get("action") or {}).get("type") != "walk_away", d
    assert d["supplier_id"] != bad


def test_opt_out_shows_the_old_walk(monkeypatch):
    monkeypatch.setattr(noidea, "EXPERIMENTS", noidea.EXPERIMENTS | {"no_rfq_keep_case"})
    case, threads, bad = rfq_with_unusable_final()
    a = NoIdeaAgent()
    a.focus = {bad}
    d = a.decide(case, threads)
    assert (d["message"].get("action") or {}).get("type") == "walk_away"  # the v6 behaviour this fix removes


def test_unreadable_attachment_reads_as_empty():
    assert read_document("cost_breakdown.pdf", b"this is not a pdf") == ""
    assert read_document("cost_breakdown.xlsx", b"this is not a workbook") == ""
    assert read_document("note.md", "plain text".encode()) == "plain text"
