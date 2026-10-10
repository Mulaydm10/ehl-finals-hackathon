"""Which kind of supplier engine is this? A pure function over what the agent sees live (no arena calls, no case data).

    from engine_rules import classify
    classify(events)            # events: the thread so far, oldest first, as play.py keeps it
    -> {"type": "mirror" | "holder" | "floor_stop" | "one_shot" | "auction" | "unknown", "signals": [...], "evidence": {...}}

Types (measured on the 10 hosted practice cases, analysis/central/ENGINES.md):
  one_shot   final_offer in its first reply to us (P10 capacity: 10 of 10). Everything must go into message 1.
  mirror     its price step follows ours (step ratio >= ~0.35: P01, P02, P07, P08, P18). Step 30% of the gap.
  holder     it moves only in replies where it took a NEW verified fact; otherwise 0 (P03, P11). One new fact per message.
  floor_stop it does not move at all after its first counter (P04). Near-close by a cent, then accept.
  auction    an RFQ bidder that reacts to cited rival offers (P05). Pass rivals=1+ for RFQ threads.
Signals (phrases in its e-mails): hedged, full_authority, committee, wants_data, wants_volume, closed_book, mirror_words,
no_new_data, repeats_objection, short_validity. Not wired into the agent; the local session decides how to use it.
"""

import re

SIGNAL_RX = {
    "hedged": r"not our reality|covered at fixed prices|hedg",
    "full_authority": r"full authority|within my (remit|authority)|delegated authority",
    "committee": r"committee|management (has )?(review|approv|authoris)|escalat",
    "wants_data": r"which figures is that based on|send us the data|verifiable data|supporting data|substantiate",
    "wants_volume": r"which volume can you commit|binding higher volume",
    "closed_book": r"calculation stays internal|do not share|our property",
    "mirror_words": r"in response to your (step|movement|move|adjustment)|your (continued )?movement|towards our position|"
                    r"meet you|in response to your step",
    "no_new_data": r"no new (verified|verifiable) data|without (new|additional) (verified )?data|lacks new|"
                   r"no new verified data or changes",
    "took_data": r"took it into account|factored|incorporated (the|your|this)|we did not know that",
    "no_change_data": r"does not change our calculation|confirm our case|not our reality",
    "rival_words": r"rival|competing offer|match (that|this|the) price|beat that|lower (rival )?quote|other offer",
}
STILL = 0.001  # its move below 0.1% of price = it held (P04 0.06%, P02 mirror steps 0.16%+)
OUR_MIN = 0.002  # our step below 0.2% of price is too small to read a ratio from
OBJECTION = re.compile(r"return(ing)? to our standard|our standard (terms|\d+-day)|must maintain|maximum (possible )?concession|"
                       r"cannot (go|move) (any )?further", re.I)


def _value(terms):
    """Price adjusted for payment days at 8% vs 30 days - comparable across payment structures without case data."""
    p = (terms or {}).get("unit_price")
    if p is None:
        return None
    return p * (1 - 0.08 * ((terms.get("payment_days") or 30) - 30) / 360)


def _ask(msg):
    vals = [_value(ts.get("terms")) for ts in msg.get("term_sheets") or []]
    vals = [v for v in vals if v is not None]
    return max(vals) if vals else None  # the sheet best for it


def _primary(msg):
    sheets = msg.get("term_sheets") or []
    return _value(sheets[0].get("terms")) if sheets else None


def classify(events, rivals=0):
    sup = [m for m in events if m.get("from") != "buyer"]
    bodies = [(m.get("body") or m.get("text") or "") for m in sup]
    signals = sorted({k for k, rx in SIGNAL_RX.items() for b in bodies[1:] if re.search(rx, b, re.I)})
    if len(bodies) >= 3 and set(x.group(0).lower() for x in OBJECTION.finditer(bodies[-1])) & \
            set(x.group(0).lower() for x in OBJECTION.finditer(bodies[-2])):
        signals.append("repeats_objection")
    if any(re.search(r"valid (for )?7 days", b, re.I) for b in bodies[1:]):
        signals.append("short_validity")
    # pair each of its replies with the buyer message it answers
    rows, last_ask = [], None
    for i, m in enumerate(events):
        if m.get("from") == "buyer":
            last_ask = (_ask(m), bool(m.get("refs")) or bool(re.search(r"\b(idx|fc|po|cost|sc|qn|doc|quote|offer):", m.get("body") or "")))
            continue
        if last_ask is None:
            continue
        rows.append({"ask": last_ask[0], "cited": last_ask[1], "value": _primary(m), "status": m.get("status"),
                     "took": bool(re.search(SIGNAL_RX["took_data"], m.get("body") or m.get("text") or "", re.I))})
        last_ask = None
    ev = {"replies": len(rows)}
    if rivals:
        return {"type": "auction", "signals": signals, "evidence": ev}
    if rows and rows[0]["status"] == "final_offer":
        return {"type": "one_shot", "signals": signals, "evidence": ev}
    ratios, still, moved_with_data, moved_without = [], 0, 0, 0
    took_any = any(r["took"] for r in rows)
    for a, b in zip(rows, rows[1:]):
        if None in (a["value"], b["value"], a["ask"], b["ask"]):
            continue
        ours, its = b["ask"] - a["ask"], a["value"] - b["value"]
        if abs(its / a["value"]) < STILL:
            still += 1
        elif b["took"]:
            moved_with_data += 1
        else:
            moved_without += 1
        if ours / a["ask"] >= OUR_MIN:  # tiny steps of ours give noise ratios (P04)
            ratios.append(its / ours)
    ev.update({"ratios": [round(r, 2) for r in ratios], "still": still, "moved_with_data": moved_with_data,
               "moved_without_data": moved_without, "took_any": took_any})
    med = sorted(ratios)[len(ratios) // 2] if ratios else None
    if not (still or moved_with_data or moved_without):
        typ = "mirror" if "mirror_words" in signals else "unknown"  # mirror = most common type (5 of 10)
    elif "no_new_data" in signals and moved_without == 0:
        typ = "holder"
    elif moved_with_data == 0 and moved_without == 0:
        typ = "holder" if took_any else "floor_stop"
    elif (med is not None and med >= 0.3) or "mirror_words" in signals:
        typ = "mirror"
    elif moved_without == 0:
        typ = "holder"
    else:
        typ = "mirror"
    return {"type": typ, "signals": signals, "evidence": ev}
