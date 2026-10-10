STATUS: DONE (task 17) - 2026-10-10 evening, cloud session, offline only (0 arena sessions, no LLM calls).
Goal: beat 0.9363 (431.58 @ 90 d, 36 m; 2483e3891d076863 / 14ab701cbfba6767) in one live game; floor target 0.92.
Agent: `analysis/agent_variants/noidea_neel_cloud.py` + `central_cloud.py` (from main 2385483).

# P03: one data kind left untried - its own quote of 5 Sep, by ID

## 1. What sets P03's price (15 games)
**Price = committee stop (433.08 @ 90 d) - one cut per NEW verified data kind it takes** (LEARNINGS §5-6). Identical inputs give
identical answers. Measured cuts:

| kind | cut |
|---|---:|
| should-cost | 0.79 |
| electronic components -2.27% | 0.48 |
| forecast +10.3% | 0.14 |
| copper -2.21% | 0.07 (0.06 with quality alongside) |
| labour -0.26% | 0.02-0.03 |
| quality 0 ppm | ~0 (14ab: copper + quality = 0.06) |
| OTD, price history | 0 ("does not change our calculation") |
| 2nd window of a series | "duplicate" (2483 round 2: "Which figures is that based on?") |
| window ending ≥ 12 months back | "irrelevant" |

The supplier's own lines: "We can talk about the terms instead - payment, volume or contract length";
"As no new verified data or increased volume commitment has been provided, we cannot adjust our calculation further"; final at our
5th message (FINAL_TRIGGER.md).

**Score sensitivity at 90 d (live):** 431.67 = 0.9342, 431.58 = 0.9363, so **1 cent = +0.00023**. Anything at or below **431.57** beats the record.

## 2. Untried levers (searched: facts.json for sup:70530 / part:350020 / 350021, dossier, contract, 4 letters, 15 traces)

| # | lever | fact | evidence for a cut | expected cut | verdict |
|---:|---|---|---|---:|---|
| 1 | **its own recent quote, BY ID** | **quote:7300003: EUR 412.74, 2026-09-05** (12 days before its 438.21 renewal quote; = today's contract price) | a data KIND never cited in 15 games (the words-only line "On 2026-09-05 you quoted us EUR 412.74", added in task 11, carries no ID). The engine cuts once per NEW verified kind. Should-cost (8.7% gap) earned 0.79; this gap is 4.4% vs its committee price | **0 - 0.40** (0 if read as "price history" or "irrelevant": not in the case refs, no trust cost) | **IMPLEMENTED, round 2** |
| 2 | data must last to its final (msg 5) | current main sends order history (0) in round 4 and nothing in round 5 | 14ab: an empty round drew "without new data ... we cannot adjust" | keeps every cut in reach | **implemented: own quote r2, copper r3, labour r4, order history r5** |
| 3 | OTD 84.6% vs the contract's 95% target (ctr:4600070530 §6.1) | sc:70530@2026Q3 | delivery record = 0 (3091eac9: "does not change our calculation") | 0 | no |
| 4 | quality 0 ppm | sc:70530@2026Q3 | ~0 (14ab) | 0 | no (green scorecard filtered) |
| 5 | QNs on the part | qn:20004261 (2024-09), qn:20004324 (2024-11) | older than 12 months -> "irrelevant" | 0 | no |
| 6 | rival quote | quote:7200003 70540 EUR 466.99 (the case's alternative) | ABOVE its price: an argument for it | <0 | never |
| 7 | its older quote | quote:7100050 EUR 415.53, 2025-02 | outdated + same kind as #1 (duplicate) | 0 | no |
| 8 | notice period (contract §3.1: 90 days) | its letter 2026-09-17 = 105 days before year end; even today (2026-09-30) = 92 | notice was IN time: the claim would support it | <0 | never |
| 9 | auto-extension (§8.1: extends 12 months unless terminated with 90 days' notice; its e-mail says it "expires") | ctr:4600070530 | no price consequence: price changes with 90 days' notice are allowed (§3.1) | 0 | no |
| 10 | payment-term cent grid (LEARNINGS §9.4) | committee prices at 90 d; alternatives 430.20 @ 60 / 428.74 @ 30 | at equal cash, 60 d scores ~0.036 lower (calibrated model); 47a88b4d: leaving 90 d fell back to the KAM price (0.86) | <0 | keep 90 d |
| 11 | 36 / 24 / 12 m | 36 m "approved" by its management (r1, every game) | 36 m is its own lever ("terms instead ... contract length") | 0 (in use) | keep 36 m |
| 12 | ask the floor (rule 58) | committee is deterministic, its floor IS its price | P11: named floor = real floor | 0 | no |
| 13 | person's currency (rule 59): sales director "open on payment terms and call-off flexibility" (doc:20260826-70530-M1) | 90 d + call-off schedule + "we pay every invoice on the due date" already in round 1 | in use since the 0.92+ games | 0 (in use) | keep |
| 14 | late-payment admission (we pay 74% of invoices 2.9 days late) | dossier | P11 (cash-short manager): floor -0.03 on 45. P03 is not cash-driven (equity 31.7%, low risk) | ~0 | no |
| 15 | more volume (5496 / yr) | "A binding higher volume would help us" | costs us more than any cut (LEARNINGS: best possible score -1.15) | <0 | never |
| 16 | cross-sell part:350021 (qualified, 0% quota, its 2024 quote 672.00) | quote:7100053 | P08: 0 twice; not in a term sheet | 0 | no |

**Plainly:** after 15 games only #1 is a new verified kind. Everything else is measured 0, outdated, or helps the supplier.

## 3. Planned e-mails (all at 427.22 -> its asks follow the existing schedule; 1 sheet, 90 d, 36 m, 4580 / yr)

| msg | refs (new kind) | sentence(s) | expected its price @ 90 d |
|---:|---|---|---:|
| 1 | cost:350020, fc:350020@2026-09, idx:PPI-C2611@2025-01 / 2025-10 (+ its 412.74 in words) + committee sentence + call-off schedule | should-cost 403.21; forecast +10.3%; electronic components -2.3% | **431.67** (3 of 3 games) |
| 2 | **quote:7300003** | "Your own quote for this part (quote:7300003) was EUR 412.74 per unit." | **431.27 - 431.67** |
| 3 | idx:CU-NOTATION@2026-01 / 2026-03 | copper -2.2% | -0.07 |
| 4 | idx:LCI-C@2025-10 / 2026-01 | labour -0.3% | -0.02 |
| 5 | order history (po:..., filler: keeps the round from going out empty) | "Our recent orders ... were at 412.74" | final |

**Expected final:**
- **431.58** if the quote is not taken: a tie at 0.9363, never worse. Same kinds as the record, just reordered; the extra claim cannot be
  contradicted (true figure, one number).
- **~431.2-431.5** if it is taken: **0.938-0.945**, a new record.
- Floor target 0.92 is safe: round 1 alone gives 431.67 = 0.934.

## 4. Checks
- **Replays vs main 2385483:**
  - SAME: P01, P02 (13), P04, P05, P07, P08, P10, P11 (8), P18.
  - P03 (12 threads): only the claim ORDER changes. 2483e389 and 14ab701c: turn 2 cites quote:7300003, copper and labour move one turn later, order history goes to turn 5. Every price is identical.
- **sim_selvbrunn** (cloud): base 0.913 / kam_only 0.906 / house 0.938, the same as main. The sim only models committee, forecast and should-cost cuts, so it cannot score #1. Its rounds show the new order (quote:7300003 in r2).
- Switch: `OWN_QUOTE_ID = True` (gated on the `price_frozen` motive: P03 only among the practice cases).

**Conclusions.**
1. P03's price is fully explained by the kinds it took; only one honest, checkable kind was never cited: its own 5 Sep quote of 412.74 (quote:7300003).
2. The plan sends it in round 2 and keeps one new item per round up to its final at our 5th message. Worst case is a tie at 0.9363; if taken, ~0.94.
3. No other lever has a positive sign: notice was in time, the rival quote is dearer, the QNs are outdated, and OTD, quality, volume and payment term are measured 0 or negative.
