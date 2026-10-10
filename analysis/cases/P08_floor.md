STATUS: DONE (task 13) - 2026-10-10 evening, cloud session, offline only (0 arena sessions, no LLM calls).
Data: all 12 P08 games (a4b92d2f included) and every trace reason line (rule 62). Values = cash per kg at 8% and 30 days, db0-equivalent.
Sim: `analysis/tools/sim_donautal.py` (floor model, `--validate`); runs in `analysis/offline_runs/P08_sim_v3_*.json`.

# P08 is floor-bound: the floor sits a fixed budget below ITS ROUND-1 VALUE

## 1. Floor test (clause-free games)

| game | draw | r1 headline | r1 value | path (value) | rounds | final | **total cut** |
|---|---|---|---:|---|---:|---:|---:|
| c387f780 | low | 5.41 @ 90 | 5.338 | -0.160, -0.050 F | 3 | 5.128 | **-0.210** |
| cae4b621 | low | 5.41 @ 90 | 5.338 | -0.170, -0.050 F | 3 | 5.118 | **-0.220** |
| 6912fd89 | low | 5.41 @ 90 | 5.338 | -0.118, -0.049, -0.049 F | 4 | 5.121 | **-0.217** |
| a4b92d2f | low | 5.42 @ 90 | 5.348 | -0.109, -0.051, -0.050 F | 4 | 5.138 | **-0.210** |
| a43d77c0 | low | 5.41 @ **45** | 5.392 | -0.150, -0.049 F | 3 | **5.193** | **-0.199** |
| 136352b4 | high | 5.53 @ 90 | 5.456 | -0.157, -0.101 F | 3 | 5.198 | -0.258 |
| db7d315a | high | 5.53 @ 90 | 5.456 | -0.162, -0.059, -0.060 F | 4 | 5.175 | -0.281 |

- **The floor is relative to the round-1 value, not absolute.** The total cut is 0.20-0.22 on the low draw and 0.26-0.28 on the high
  draw, whatever the data, steps, payment term or number of rounds. a43d (45-day headline, round-1 value 0.054 higher) ended 0.065 higher
  than the 90-day games. An absolute cost floor at ~5.12-5.14 would have pulled a43d down to it too.
- **The path only splits the budget.** Round 2 takes 0.16 after a ~16% step of ours, but only 0.11-0.12 after a 30% step. A deferral
  round then takes half of what is left, and the final takes the rest (6912 0.049 / 0.049, a4b9 0.051 / 0.050, db7d 0.059 / 0.060).
- **Correction to task 12.** The small round-2 cut was our 30% step, not the 90-day term: a4b92d2f moved to 14 d and still got -0.109.
  Moving to 14 d is harmless, but it is not a lever.
- **Sim fit (floor model)** over 39 replies: every clause-free game within 0.01-0.02. The misses are db5 / clause rounds (±0.04-0.08).
  Main's agent comes out at 0.721 low / 0.654 high, against live 0.710 / 0.726 (low) and 0.666 (high).

To beat the house's 5.10 on the low draw, the floor must move by **≥ 0.03** (low-draw floor 5.12-5.14): either a lower round-1 value
or a larger budget.

## 2. What the trace reasons say (rule 62; 12 games, every reason line)

| reason (count) | reading |
|---|---|
| "our whole range is at your disposal, so if there is anything else on your list, just send it over - we are happy to quote" (**21 e-mails**, nearly every game) | **its person's currency: more items on our order** (stock distributor, extensive inventory) |
| "Material accounts for about … of our cost; more detail we do not share" (18) / "strict company policy not to disclose" | no open book from Inside Sales; the owner's April offer (doc:20260421-70710-M2) is not his to keep |
| "That is not our reality: covered at fixed prices until March …" (6) | hedged series: no lever |
| "A binding higher volume would help us and can improve the price" + "Which volume can you commit to?" (2 finals: ab47, 9bfa) | volume is a price lever, but `volume_per_year` is fixed at 94800 in this case |
| "The contract term is reflected in the price" (2: a43d, 9bfa) | contract length is priced; direction unknown in P08 |
| "Faster payment helps our cash flow; that is reflected in the price" / "A longer Zahlungsziel costs us interest" | payment is priced at its ~7-8.5% rate: neutral |
| "any deadband would require a higher base price" (6912) | db5 = +0.12 |
| "We checked the … data; it holds and we took it into account" (data taken) | moves the path, not the total (budget unchanged) |

## 3. Levers that could move the floor, ranked

| # | lever | evidence | floor shift | cost / risk | verdict |
|---:|---|---|---|---|---|
| 1 | **Round-1 headline on our longest payment term** | a43d (45 d) final 5.193 vs 5.12-5.14 (90 d): the floor follows the round-1 value | **-0.054 (proven)** | none | in use since task 11 (90-day headline guaranteed) |
| 2 | **Cross-sell (its person's currency)**: invite it to quote for Sheet 1.4301 2 mm, a part it is qualified for at 0% quota. We buy ~72100 a year (fc:370021@2026-09) from 70730 at 4.05; it quoted it to us itself in 2024 (quote:7100069, 4.29) | its own line in 21 e-mails; rule 59 (P11: the person's currency moved the floor 45.13 -> 45.10) | unknown: P11-size 0.07% = 0.004; volume-size ("binding higher volume ... can improve the price") 0.02-0.04 | none: words only, no figure, no ID (nothing to contradict); sheets unchanged | **IMPLEMENTED (`CROSS_SELL`), the experiment** |
| 3 | 36 m instead of 24 m | our cost identical (score 0.7886 vs 0.7886 at 5.05 @ 14); "contract term is reflected in the price"; P03 paid for 36 m, P07 charged for it, P10 best at 36 m | unknown, either sign | may raise the round-1 headline (and so the floor); confounded with the draw | 2nd experiment, not now |
| 4 | Ask the floor (rule 58) + hair-below ask (rule 61) | P11 named its floor and agreed a hair below it | ≤ 0.01 (the floor is reached at msg 3-4 anyway) | a burned round | low |
| 5 | Late payment admission (rule 59) | we pay 79% of its invoices 2.9 days late; it is not cash-short (equity 33.9%, credit low risk); we already pay at 14 d | ≤ 0.001 | none | no |
| 6 | db3 / db5 deadband | +0.024 / point, scores 0.009 worse than db0 at equal value | none | - | no |
| 7 | Volume / call-off wording | volume fixed (94800); call-off schedule already attached in msg 1; forecast +1.9% taken but inside the budget | none | - | no |
| 8 | Our step pattern (16% vs 30%, deferral) | totals 0.20-0.22 for every pattern | none | - | no (deferral kept: harmless) |
| 9 | High-draw coin flip (5.53 vs 5.41) | per session, identical inputs split | - | - | not fixable |

## 4. In the code (`noidea_neel_cloud.py` + `central_cloud.py`, from main 53e150e)
- `central.cross_sell_note()` finds a part the supplier is qualified for at 0% quota, which we buy elsewhere and which it has quoted
  us before. It writes one sentence in words: *"Beyond this part, we buy Sheet 1.4301 2 mm, 2B, cut to size from another supplier
  today, in a volume close to this bar's, and you have quoted it for us before. Once this agreement is signed, we will invite you to
  quote for it."* That goes in message 1, with a one-line reminder in message 3.
- Gated by `CROSS_SELL` (on) and `hedged_raw` (raw material + hedged = P08 only).
- Replays against main 53e150e: **SAME in all 76 threads** (P01-P05, P07, P08, P10, P11, P18). The change is e-mail text only.

**Sim** (house 0.752; the cross-sell effect is a parameter, because no game has measured it):

| agent | low draw | high draw |
|---|---:|---:|
| main 53e150e | 0.721 | 0.654 |
| cloud, cross-sell moves the floor 0.00 | 0.721 | 0.654 |
| cloud, cross-sell moves the floor 0.02 | 0.744 | 0.676 |
| cloud, cross-sell moves the floor 0.04 | **0.766** | 0.699 |

## 5. ONE recommended live experiment
**P08 with `CROSS_SELL = True`, everything else as main.** The sheets, steps and data are identical to a4b92d2f / 6912fd89, so any change
in the total cut is the cross-sell. Read it off the total cut: on a low draw anything beyond -0.21 to -0.22 (final below 5.12) is the effect;
on a high draw, beyond -0.26 to -0.28.
- Expected value: 0 if it is ignored. +0.004 if it moves the floor like P11's person's currency. +0.022 to +0.045 if the engine counts
  it like volume (≥ 0.03 shift beats the house on the low draw).
- With a guess of 1/3 for a volume-size effect: **EV ≈ +0.01 score per P08 game, downside ≈ 0.**

**Conclusions.**
1. P08's final = round-1 value - 0.21 (low) / 0.27 (high) in every clause-free game. Data, steps, payment term and deferral only move the path.
2. The only proven floor mover is the round-1 value (90-day headline, -0.054, already in use). The best untested one is its own stated currency: more items on our order (cross-sell, zero cost, implemented).
3. Next lever if that fails: 36 m (free for us, direction unknown).
