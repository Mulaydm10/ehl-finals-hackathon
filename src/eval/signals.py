"""Categorise every signal the arena's suppliers sent us, and surface the ones we don't handle yet.

Reads the session list and each session's trace (GET /v1/sessions, /v1/sessions/{sid}: no practice
quota) plus the opening e-mails and quote PDFs from Neel's probes. Each supplier reason / sentence
is matched against SIGNALS (category -> regex); unmatched ones are printed as candidates for new
signals. Writes datasets/E_supplier_signals.json.

    cd tacto/starter-kit && .venv/bin/python ../../src/eval/signals.py
"""
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tacto/starter-kit"))
import httpx  # noqa: E402

# category -> (regex, what our agent should do)
SIGNALS = {
    "asks_volume": (r"which volume|volume can you commit|specific volume|exact volume|expected annual quantity|volume figures",
                    "state the binding volume and term (done in v1.2)"),
    "volume_helps_price": (r"higher volume would help|binding .*volume.* improve|volume .* improve the price",
                           "offer more volume / longer term if the need allows"),
    "data_verified_no_effect": (r"holds, but it does not change|does not (alter|change) (the|our) (overall )?calculation|do not fully represent",
                                "drop that kind of argument for this supplier; bring a different lever"),
    "data_disarmed": (r"did not know that|a fair point|we took it into account",
                      "data works on this supplier: keep citing NEW facts"),
    "data_already_counted": (r"already (been )?(taken|factored|fully accounted)|received a lot of material",
                             "stop re-citing; each ID counts once"),
    "cost_drivers_named": (r"price follows our main cost drivers", "cite exactly those series (helps us if they moved little)"),
    "asks_calculation": (r"share the (specific )?data or calculations|basing it on|target pricing",
                         "send a calculation (kit_calc for bundles, driver maths otherwise)"),
    "concession_with_trade": (r"in return for|in response to your (latest|improved) (offer|proposal)|we can (further )?(reduce|revise|offer)",
                              "it moves when we move: keep reciprocal steps"),
    "partnership_appeal": (r"partnership|pride|long-standing|reliabl|pleasure to work",
                           "acknowledge the relationship; no threats"),
    "standard_terms": (r"standard (terms|zahlungsziel)|general terms and conditions",
                       "state every negotiable field; unstated terms close on its standard terms"),
    "cost_pressure_story": (r"energy|raw material|wage|labou?r cost|sustained increases|rose .* in twelve months",
                            "counter with the real driver indices"),
    "approval_needed": (r"management|committee|approval|head office|my boss|director",
                        "smaller steps; give the boss a reason (volume, years)"),
    "final_word": (r"final offer|cannot go further|last word|our limit", "one last non-price ask, then accept"),
    "validity": (r"remains valid|valid for \S+ days|validity:|price valid from", "note quote validity"),
    # new signals found by this script (2026-10-10, 14 sessions)
    "prose_alternative": (r"^alternatively|alternatively,", "only term sheets bind: put the alternative into our next sheet"),
    "closed_book": (r"calculation stays internal|cannot share our (cost|calculation)", "stop asking for a cost breakdown"),
    "term_conceded": (r"we accept your proposed|pleased to accommodate|willing to accept the", "lock that term in, move on to price"),
    "nearing_close": (r"bridge the remaining gap|mutually agreeable conclusion|reach an agreement", "it is near its limit: be ready to accept"),
    "acknowledges_our_move": (r"step towards our position|movement towards our position|continued movement|improved offer",
                              "reciprocity works: keep small, steady steps"),
    "absorb_pushback": (r"cannot simply absorb|verified cost increases", "its story is firm: trade terms, not data"),
    "eager_new_business": (r"eager to show you|what we can do", "new or hungry supplier: push price, it wants the deal"),
    "boilerplate": (r"thank you for your enquiry|find our angebot|mit freundlichen|dear sir or madam|do not hesitate|any questions|look forward|inside sales|export manager|zahlungsziel",
                    "ignore"),
}


def client():
    env = {}
    for line in (ROOT / "tacto/starter-kit/.env").read_text().splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    url = os.environ.get("ARENA_URL", env.get("ARENA_URL", "https://arena.tacto.ai"))
    return httpx.Client(base_url=url, headers={"X-API-Key": env["ARENA_API_KEY"]}, timeout=60)


def sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", text or "") if len(s.strip()) > 15]


def main():
    c = client()
    items = []  # (case, session, round, source, text)
    for s in c.get("/v1/sessions").json():
        d = c.get(f"/v1/sessions/{s['session_id']}").json()
        r = d.get("result", d)
        for t in r.get("trace") or d.get("trace") or []:
            if t.get("actor") == "buyer":
                continue
            for reason in t.get("reasons") or []:
                items.append((s["case_id"], s["session_id"], t.get("round"), "reason", reason))
            for x in sentences((t.get("move") or {}).get("body")):
                items.append((s["case_id"], s["session_id"], t.get("round"), "email", x))
    for f in (ROOT / "analysis/cases/openings").glob("*.json"):
        for sid, ms in json.loads(f.read_text())["threads"].items():
            for m in ms:
                for x in sentences(m.get("body")):
                    items.append((f"case:{f.stem}", "probe", 0, "opening", x))
                for att in m.get("attachments") or []:
                    for x in sentences(att.get("text")):
                        if re.search(r"(?i)remark|note|valid|surcharge|condition", x):
                            items.append((f"case:{f.stem}", "probe", 0, "quote_pdf", x))

    by_cat, unmatched = defaultdict(list), Counter()
    for case, sid, rnd, src, text in items:
        cats = [k for k, (rx, _) in SIGNALS.items() if re.search(rx, text, re.I)]
        for k in cats:
            by_cat[k].append({"case": case, "session": sid, "round": rnd, "source": src, "text": text})
        if not cats and src in ("reason", "opening", "quote_pdf"):
            unmatched[re.sub(r"€\s?…|\d[\d.,]*", "#", text)] += 1

    print(f"{len(items)} supplier sentences from {len({i[1] for i in items})} sessions/probes\n")
    print(f"{'signal':26} {'n':>4} {'cases':24} action")
    for k, (rx, action) in SIGNALS.items():
        hits = by_cat.get(k, [])
        print(f"{k:26} {len(hits):4} {','.join(sorted({h['case'][5:] for h in hits}))[:24]:24} {action}")
    print("\nNOT MATCHED (candidate new signals):")
    for text, n in unmatched.most_common(40):
        print(f"  [{n}x] {text[:200]}")
    out = {k: {"action": SIGNALS[k][1], "examples": v[:12], "n": len(v)} for k, v in by_cat.items()}
    out["_unmatched"] = [{"text": t, "n": n} for t, n in unmatched.most_common()]
    (ROOT / "datasets/E_supplier_signals.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
