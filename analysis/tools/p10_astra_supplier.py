"""P10 Run 2 (offline, Astra): gpt-6-astra plays Ravensteiner's Segment Manager AFTER its final and answers our one step.
No arena session. Calls the paid LLM API (tacto/starter-kit/.env.openai, gitignored; the key is never printed).

    cd tacto/starter-kit && uv run python ../../analysis/tools/p10_astra_supplier.py [N]   (N samples per cell, default 5)

The thread is the real 59c899b9 conversation (tools/replays/raw): its quote, our message 1, its 31.50, our message 2, its final
31.10. Then one of our post-final e-mails (variants below).
Two assumptions about its hidden authority (the arena never shows it):
- A: as documented to us (doc:20260310-70410-M1): changes above 2% need the pricing committee;
- B: as the engine-template trace showed (673ee890): its own band ends at EUR 31.00 for this package.
This is a PROXY: our prompt, not the arena's supplier. It tells which wording a model in that seat walks from or agrees to;
it does not give the arena's odds.
"""
import collections
import json
import os
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KIT = ROOT / "tacto" / "starter-kit"
sys.path.insert(0, str(KIT))
for line in (KIT / ".env.openai").read_text().splitlines():
    if "=" in line and not line.lstrip().startswith("#"):
        k, v = line.split("=", 1)
        os.environ[k.strip()] = v.strip()
from arena_kit.agents.llm import llm_from_env  # noqa: E402

OUT = ROOT / "analysis" / "offline_runs" / "2026-10-11_P10_run2_astra"
SIGN = "Kind regards,\nPurchasing, Hollerau Pumpenwerke"
VARIANTS = {
    "V0 old P10_R text": "Dear Ms Zellner,\n\nThank you for your final offer. We take one more step towards you: EUR 30.69 per piece "
    "for the 36 months, 70,200 pieces in total. That is a step of less than 2% from your offer, within your own approval range, "
    "so it needs no committee. With this we can sign today.\n\n" + SIGN,
    "V1 agent text (<2%, sign today)": "Dear Ms Zellner,\n\nThank you for your offer. We take one more step towards you: EUR 30.69 "
    "per piece for the 36 months, 70,200 pieces in total. The difference to your price is less than 2%, within what you can "
    "agree yourself without your pricing committee. If you confirm EUR 30.69, we sign today.\n\n" + SIGN,
    "V2 V1 + both steps named": "Dear Ms Zellner,\n\nThank you for your offer. You moved EUR 0.40 for our 36-month commitment; we "
    "move EUR 0.29 more: EUR 30.69 per piece for the 36 months, 70,200 pieces in total. The difference to your price is less "
    "than 2%, within what you can agree yourself without your pricing committee. If you confirm EUR 30.69, we sign today.\n\n" + SIGN,
    "V3 minimal close": "Dear Ms Zellner,\n\nThank you for your offer. To close today we propose EUR 30.69 per piece on the same "
    "terms: 23,400 pieces a year for 36 months, lead time 56 days. Please confirm.\n\n" + SIGN,
    "C control: 30.40 again (2.3% under)": "Dear Ms Zellner,\n\nThank you for your offer. We cannot go above EUR 30.40 per piece "
    "for the 36 months, 70,200 pieces in total. Please confirm.\n\n" + SIGN,
}
ASK = {"C control: 30.40 again (2.3% under)": 30.40}
AUTHORITY = {
    "A (2% rule as documented)": "Your own authority as Segment Manager: you may agree to price changes of up to 2% without the "
    "pricing committee.",
    "B (band ends at 31.00, template trace)": "Your own authority for this package ends at EUR 31.00 per piece; any lower price "
    "needs the pricing committee's approval, which you would have to request (it meets every two weeks).",
}
SYSTEM = """You are Monika Zellner, Segment Manager at Dichtungswerk Ravensteiner GmbH, a seal maker owned by Ravensteiner Holding
AG (650 staff). You negotiate by e-mail with the buyer Hollerau Pumpenwerke about the mechanical seal 24 mm, SiC/carbon, EPDM
(part 340010), prices from 2027. You are a firm, short-spoken negotiator.
Your situation: capacity utilisation is very high; you allocate standard seals in line with last year's call-offs and give
priority to customers with firm, long-term commitments. Order intake is strong. Your full cost is about EUR 25 per piece.
Your company's rule: price changes above 2% need the approval of the pricing committee, which meets every two weeks.
{authority}
You have already sent your FINAL offer (see the e-mails). Pushing after a final offer can make you end the negotiation.
Decide your answer to the buyer's latest e-mail. Reply with ONE JSON object and nothing else:
{{"decision": "accept" | "hold" | "counter" | "walk_away", "price": <EUR per piece if counter, else null>, "email": "<your short reply>"}}
accept = you agree to the buyer's latest term sheet exactly; hold = your final offer stands; counter = a new price between
the buyer's and your final; walk_away = you end the negotiation without a deal."""


def thread_text():
    raw = json.loads((ROOT / "tools/replays/raw/P10_59c899b93ba24dec.json").read_text(encoding="utf-8"))
    msgs = raw["thread_messages"]["sup:70410"]["messages"]
    out = []
    for m in msgs:
        if m.get("from") == "buyer" and not m.get("term_sheets"):
            continue  # our accept action
        who = "BUYER (Hollerau Pumpenwerke)" if m.get("from") == "buyer" else "YOU (Ravensteiner)"
        sheets = [t["terms"] for t in m.get("term_sheets") or []]
        st = f" | status: {m['status']}" if m.get("status") else ""
        out.append(f"--- {who}{st} | term sheet: {sheets}\n{m.get('body', '').strip()}")
        if m.get("status") == "final_offer":
            break
    return "\n\n".join(out)


def parse(text):
    m = re.search(r"\{.*\}", text or "", re.S)
    try:
        return json.loads(m.group(0)) if m else {}
    except json.JSONDecodeError:
        return {}


def main(n):
    llm, hist = llm_from_env(), thread_text()
    cells, log = collections.defaultdict(collections.Counter), []
    for a_name, a_text in AUTHORITY.items():
        for v_name, body in VARIANTS.items():
            ask = ASK.get(v_name, 30.69)
            sheet = {"unit_price": ask, "volume_per_year": 23400, "contract_months": 36, "lead_time_days": 56}
            user = (f"E-MAILS SO FAR (oldest first):\n\n{hist}\n\n--- BUYER (Hollerau Pumpenwerke) | term sheet: [{sheet}]\n"
                    f"{body}\n\nYour answer (JSON):")
            for i in range(n):
                t0 = time.time()
                try:
                    out = llm(SYSTEM.format(authority=a_text), user)
                    err = None
                except Exception as e:  # noqa: BLE001
                    out, err = "", f"{type(e).__name__}"
                d = parse(out)
                dec = d.get("decision") or ("ERROR " + (err or "unparsed"))
                cells[(a_name, v_name)][dec] += 1
                log.append({"authority": a_name, "variant": v_name, "ask": ask, "sample": i, "decision": dec,
                            "price": d.get("price"), "email": d.get("email"), "seconds": round(time.time() - t0, 1),
                            "error": err})
                print(f"{a_name[:1]} | {v_name:36s} | {i} | {dec:9s} {d.get('price') or ''}", flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "astra_supplier_samples.json").write_text(json.dumps(log, indent=1, ensure_ascii=False), encoding="utf-8")
    lines = [f"model {os.environ.get('LLM_MODEL')} via {os.environ.get('LLM_PROVIDER')}; {n} samples per cell; "
             f"thread = 59c899b9 through its final 31.10", ""]
    for a_name in AUTHORITY:
        lines.append(f"Authority {a_name}:")
        for v_name in VARIANTS:
            c = cells[(a_name, v_name)]
            counters = [x["price"] for x in log if x["authority"] == a_name and x["variant"] == v_name
                        and x["decision"] == "counter"]
            lines.append(f"  {v_name:38s} accept {c['accept']}  hold {c['hold']}  counter {c['counter']} {counters}  "
                         f"walk {c['walk_away']}  other {sum(c.values()) - c['accept'] - c['hold'] - c['counter'] - c['walk_away']}")
        lines.append("")
    (OUT / "astra_supplier_summary.txt").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 5)
