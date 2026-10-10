"""Which games did the arena's suppliers answer in ENGINE-TEMPLATE mode (their model off) and which in normal (model) mode?

Offline only: reads datasets/runs/*.json and tools/replays/raw/*.json, never the arena.
Run from the repo root:  python3 analysis/tools/supplier_mode_scan.py [CASE ...]   e.g. P10 P11

A reply is TEMPLATE when every sentence in its trace `reasons` is one of the engine's fixed sentences ("We value our
cooperation and have made a step towards you.", "Any further step needs approval from our management.", "The contract
term is reflected in the price.", ...). Normal mode adds model-written sentences ("Given our current capacity constraints,
we must maintain a firm position on pricing."). Report: analysis/cases/P10_draw.md.
Mode per session: TEMPLATE (all replies), model (none), mixed (some). A lone "Without movement from your side we cannot
move either." also reads as template: that is a hold reply, not the fallback.
"""
import datetime
import glob
import json
import re
import sys

ENGINE = [
    r"^We checked the .+ (data )?you cited; (it holds|they hold)", r"^We value our cooperation and have made a step towards you\.$",
    r"^The contract term is reflected in the price\.$", r"^Any further step needs approval from our management\.$",
    r"^Our management has approved a further step\.$", r"^Our Lieferzeit is … days\.$", r"^Which volume can you commit to\?$",
    r"^Our price reflects our costs; our calculation stays internal\.$",
    r"^Our calculation is our property; we do not share a breakdown\.$",
    r"^Which figures is that based on\? Please send us the data\.$", r"^Alternatively, with .+: €… per unit\.$",
    r"^A longer Zahlungsziel costs us interest; that is priced in\.$",
    r"^.+ (rose|fell) … in twelve months and is … of our cost\.( That remains\.)?\s*$",
    r"^A Preisgleitklausel changes who carries the material risk; priced in\.$", r"^Our price follows our main cost drivers: .+\.$",
    r"^Material accounts for about … of our cost; more detail we do not share\.$", r"^Our margin and our limits stay internal\.$",
    r"^Our general terms and conditions apply; the quote lists our standard terms\.$",
    r"^Our standard terms apply to everything the quote does not state; see attached\.$",
    r"^We can offer a Preisgleitklausel on .+\.$", r"^We are happy to discuss this in a call; until then our offer stands\.$",
    r"^Without movement from your side we cannot move either\.$", r"^Our standard Zahlungsziel is … days net\.$",
    r"^Faster payment is welcome; we can reflect it in the price\.$",
    r"^Faster payment helps our cash flow; that is reflected in the price\.$",
    r"^We need to clarify this internally - we will come back to you on price\.$",
    r"^We have clarified this internally and can move further on the price\.$",
    r"^We received a lot of material; we looked at what bears on this part\.$", r"^We have already taken that .+ into account\.$",
    r"^A binding higher volume would help us and can improve the price\.$", r"^We meet the agreed quality targets\.$",
    r"^Your figures confirm our case: that driver rose\.$", r"^We did not know that - a fair point\.$",
    r"^As to the .+ data you cited, ", r"^We see your figures, but we cannot give up margin right now\.",
    r"^We have reviewed your offer and hold our Angebot\.$",
]
ENGINE_RE = [re.compile(x) for x in ENGINE]


def engine_sentence(s):
    return any(r.search(s.strip()) for r in ENGINE_RE)


def games():
    out = {}
    for p in sorted(glob.glob("datasets/runs/*.json")):
        try:
            d = json.load(open(p))
        except Exception:
            continue
        if isinstance(d, dict) and "session" in d:
            s = d["session"]
            out[s["session_id"]] = (s.get("case_id"), s.get("created_at"), (d.get("detail") or {}).get("result") or {})
    for p in sorted(glob.glob("tools/replays/raw/*.json")):
        d = json.load(open(p))
        out.setdefault(d.get("session_id"), (d.get("case_id"), None, d.get("result") or {}))
    return out


def main(cases):
    rows = []
    for sid, (case, ts, res) in games().items():
        if cases and (case or "")[5:] not in cases:
            continue
        flags, first = [], None
        for t in res.get("trace") or []:
            if t["actor"] == "buyer" or t["round"] == 0 or not t.get("reasons"):
                continue
            flags.append(all(engine_sentence(r) for r in t["reasons"]))
            if first is None:
                mv = t["move"]
                first = ((mv.get("terms") or {}).get("unit_price"), (mv.get("signals") or {}).get("reply_delay_days"))
        if not flags:
            continue
        mode = "TEMPLATE" if all(flags) else ("model" if not any(flags) else "mixed")
        when = (datetime.datetime.fromtimestamp(ts, datetime.timezone(datetime.timedelta(hours=2))).strftime("%m-%d %H:%M:%S")
                if ts else "(raw replay)  ")
        rows.append((ts or 9e12, when, sid, (case or "")[5:], mode, first, res.get("score")))
    for _, when, sid, case, mode, first, score in sorted(rows):
        print(f"{when}  {sid}  {case:4} {mode:8}  first reply {first}  score {score if score is None else round(score, 4)}")


if __name__ == "__main__":
    main(set(a.upper() for a in sys.argv[1:]))
