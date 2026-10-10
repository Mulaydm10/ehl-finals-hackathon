STATUS: tasks 3+4 DONE - 2026-10-10 evening, cloud session, offline only. Task 5 (REGRESSION.md) next.

# Supplier engines of the 10 hosted practice cases

How each supplier moves its price, from every archived game (`analysis/tools/case_engine.py <case>`,
`analysis/tools/engine_dump.py <case>`). Per-case detail: `analysis/cases/<case>_engine.md`.
"Step ratio" = its value step / our value step, median over rounds (with / without a new verified fact).

| case | type | step ratio (no data / data) | final at our msg | our best | house | best gap-closing lever | expected | sessions |
|---|---|---|---|---:|---:|---|---:|---:|
| P04 | floor-stop | ~0 / ~0 | 2-3 | 0.86 | ? | one cent: 1 cent = 0.17. Its own valid quote EUR 4.63 (quote:7200019) + near-close at EUR 4.93 @ 90 d | 0.95+ | 1-2 |
| P05 | auction (rival-quote) | half the step per cited rival | 6-16 (RFQ) | 0.61 | ? | cite the current market low to every bidder every round; ask 5-10% under it; keep 2 alive | 0.68-0.75 | 2 |
| P08 | partial mirror, hedged | 0.47 / 0.50 | 3 | 0.65 | 0.75 | clause-free asks in round 2; its own EUR 5.45 quote + order prices + cold-drawing -2.3% | 0.70-0.76 | 1-2 |
| P18 | mirror | 0.80 / 0.90 | 3 | 0.68 | ? | 30%-of-gap steps (it mirrors 0.10 for 0.10); AS-14404 -8.5% (not hedged here) | 0.72-0.76 | 1-2 |
| P11 | holder (data only) | 0.0 / 0.3-1.0 | 4-5 | 0.79 | ? | one new kind per message: 4 QNs on this part (quality case) + labour | 0.82-0.86 | 1 |
| P07 | mirror | 0.60 / 0.68 | 4 | 0.75 | ? | 30%-of-gap steps; fasteners -1.6% + QNs | 0.78-0.82 | 1 |
| P10 | one-shot (final at msg 1) | - | 1 | 0.66 | 0.69 | all data in msg 1: should-cost + order prices + QNs; lead 56 | 0.67-0.70 | 1 |
| P01 | mirror, data-naive | 0.45 / 1.36 | rarely (5) | 0.91 | ? | April start + 14 d; should-cost (never cited, 4.3% under its quote) | 0.92-0.95 | 1 |
| P02 | mirror | 0.50 / 1.00 | 4 | 0.82 | 0.74 | (done) 30%-of-gap steps + one fact per round | 0.82-0.85 | 0 |
| P03 | holder | 0 / cut per kind | 3+ | 0.94 | 0.925 | (done) no data kind left | 0.94 | 0 |

Ranked by expected gain over our best: **P04 (+0.09), P05 (+0.10), P08 (+0.08), P18 (+0.06), P11 (+0.05), P07 (+0.05),
P10 (+0.03), P01 (+0.02).** House scores marked "?" are not recorded anywhere in the repo.

## What generalises to the hidden suppliers
1. **Mirror** (P01, P02, P07, P08, P18 - 5 of 10): its step follows ours. Bigger steps (30% of the gap) buy bigger steps
   until its final; the final comes at a fixed message count (3-4), so slow steps leave money on the table.
2. **Holder** (P03, P11): only a NEW verified fact moves it. One new kind per message, keep rounds going while data is left.
3. **Floor-stop** (P04): pinned to a value from its first counter; only the cent grid and a near-close matter.
4. **One-shot** (P10, capacity): final at message 1, so everything (structure + all data) goes into message 1.
5. **Auction** (RFQ P05): rival offers are the only data that moves bidders.
6. **Never cited in any game, true and checkable, in 8 of 10 cases:** supplier-caused quality notifications on the part
   in the last 12 months (`qn:` IDs); the supplier's OWN recent quote (P01, P04, P08, P11); order-price history (P04, P08, P10).

## Classifier (task 4): `analysis/central/engine_rules.py`
`classify(events, rivals=0)` reads only the live thread (its e-mails, statuses, primary sheets, our sheets).
Test: `cd tacto/starter-kit && uv run python ../../analysis/tools/test_engine_rules.py` (all archived games, round by round):
- **70% of all replies; 78% after its 2nd reply, 87-88% after its 3rd/4th; 87% at the end of a thread (93 of 107).**
- Perfect: P04 floor-stop, P05 auction, P07 / P08 mirror, P10 one-shot. Weak: holder vs mirror on P03 (8/14) and P11 (2/5);
  P11 also moves without data in some games, so its label is itself borderline.
- After its first counter it can't tell (35%: "unknown"), except one-shot (final at once) and auction (rivals > 0).
  Default for "unknown": treat as mirror (5 of 10 practice suppliers).
