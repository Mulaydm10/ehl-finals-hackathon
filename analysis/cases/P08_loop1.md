STATUS: DONE (task 14) - P08 loop, report 1 - 2026-10-10 evening, cloud session, offline only (0 arena sessions, no LLM calls).
Run: ad0427655e885fc1 = 0.710, low draw, main 288ce7f (task-13 copy with cross-sell). Every e-mail, claim and trace reason read (rule 62).

# Loop run 1: no cent lost against the floor; the floor (round-1 value - 0.20) was the only limit

## 1. Mistakes report, e-mail by e-mail

| msg | ours | its reply (value) | trace reasons (rule 62) | mistake? | cost | fix |
|---:|---|---|---|---|---:|---|
| 1 | 4.79 @ 90 / 4.73 @ 45 / 4.70 @ 14, clause-free 24 m; own quote 5.45 in words; **cross-sell sentence**; forecast +1.9%; PPI-C2431 -2.3%; call-off schedule | 5.41 @ 90 db0 = **5.338** (low draw; alt 5.45 @ 14 db5) | index and volume "took it into account"; "Building on your proposed 14-day payment terms..."; "Material accounts for about … of our cost; more detail we do not share" | **the cross-sell drew nothing**: no reason line; not read as a claim. Headline 5.41 as in every low draw | 0 | none (zero cost) |
| 2 | 4.89 @ 14 (30% step), LCI-C -0.3% | 5.22 @ 14 = 5.238 (**-0.100**) | LCI-C "factored it into our calculation"; "AS-14404 covered at fixed prices until March … decreases do not reduce our costs" | **model-written opening misread its sheet: "We reject a price increase for shorter payment terms"**. Its 14-day alternative is the same value, not an increase. It also asked for "a lower base price in return for accepting an index-linked clause, with a defined band" while our sheet was clause-free | 0 measured (trust risk) | prompt rule: compare like for like, never call a different payment term or clause an increase |
| 2 | (30% step) | -0.10 instead of -0.16 | - | not a mistake: the round-2 cut only splits a fixed budget (after a 16% step it is 0.16, after a 30% step 0.10-0.12) | 0 | - |
| 3 | 4.91 (+0.02 = 0.18x its step), 7 QNs, cross-sell reminder | 5.17 @ 14 = 5.188 open (-0.050), **deferral 4 of 4** | QNs "do not warrant a price reduction"; arena read the QNs as ppm 237.6 (verified); "we must maintain the AS-14404 index clause" | the model asked for "no adjustment clause until the coverage expires" - not a term option (base month fixed); harmless | 0 | - |
| 4 | 4.98 (normal step), order history 5.43-5.45 | **final** 5.12 @ 14 = 5.138 (-0.050) | price history "holds, but it does not change our calculation"; "Because our AS-14404 costs are fixed until March … we must retain the index clause" | - | 0 | - |
| close | accepted its primary (offer:70710-4) | deal 5.12 @ 14, db0, 24 m = **0.710** | - | correct (accept at final, primary id) | - | - |

**Verdict:** no data contradicted, no hold, no walk, no structure hop, no empty round. The total cut was **-0.200** (5.338 -> 5.138), the
same as a4b92d2f (-0.210, identical path at 5.42). The 0.022 below 0.732 (cae4b621) is cent rounding and the 0.01-0.02 budget spread
(0.20-0.22), not a mistake.

## 2. Floor model, 13 games (clause-free)

| game | draw | r1 value | final | total cut | rounds | our r2 step |
|---|---|---:|---:|---:|---:|---|
| c387f780 | low | 5.338 | 5.128 | -0.210 | 3 | 16% |
| cae4b621 | low | 5.338 | 5.118 | -0.220 | 3 | 16% |
| 6912fd89 | low | 5.338 | 5.121 | -0.217 | 4 | 30% @ 90 |
| a4b92d2f | low | 5.348 | 5.138 | -0.210 | 4 | 30% @ 14 |
| **ad042765** | low | 5.338 | 5.138 | **-0.200** | 4 | 30% @ 14 + cross-sell |
| a43d77c0 | low (45-d headline) | 5.392 | 5.193 | -0.199 | 3 | 16% |
| 136352b4 | high | 5.456 | 5.198 | -0.258 | 3 | 16% |
| db7d315a | high | 5.456 | 5.175 | -0.281 | 4 | 30% @ 60 |

- **Low-draw budget = 0.209 ± 0.008** (6 games); high draw 0.27 (2 games).
- The 30%-step games sit slightly lower (0.200-0.217 vs 0.210-0.220): within noise.
- sim_donautal now uses budget 0.209 / 0.27. `--validate` over 46 replies: median |diff| 0.010; every clause-free reply is within 0.02.

## 3. Next lever, re-ranked with this run

| lever | evidence now | possible gain | risk | rank |
|---|---|---|---|---:|
| **36 m (round 1 onward)** | our cost identical (24 vs 36 m: 0.7886 / 0.7886 at 5.05 @ 14); its own line "The contract term is reflected in the price" (a43d, 9bfa); P03 rewarded 36 m, P10's best probes were 36 m, P07 charged ~0.7% more; **never tried in P08** | it acts on the round-1 headline, which the floor follows: a 0.04 discount -> 0.766 on the low draw (beats 0.752) | a 0.04 premium -> 0.676; visible at once in round 1 (headline vs 5.41 / 5.53) | **1 - implemented** |
| deeper round-1 anchor (all 13 games asked ~4.73) | P02 / P08 first counters did not follow inputs; P10's did | unknown | P05: a 20% market gap made a bidder walk | 2 |
| ask the floor / hair-below (rules 58 / 61) | P11: the named floor WAS the real floor (reached anyway); hair-below untested live; in P08 the floor is reached at msg 3-4 anyway | ≤ 0.01 | a hair ask needs ITS structure (clause) - taking its clause cut round 2 to -0.05..-0.09 | 3 |
| cross-sell | **measured: 0** (ad042765, total -0.200) | 0 | none | kept (zero cost) |
| round-1 data mix | headline 5.41 / 5.42 in all 6 low draws, whatever the data (1-3 kinds, taken or not) | 0 | - | - |
| deadband, payment term, volume wording, step pattern | neutral or path-only (P08_floor.md) | 0 | - | - |

## 4. The change (`noidea_neel_cloud.py`, from main 582adc5) and its expected value
- `LONG_TERM_HEDGED = True`: hedged raw-material suppliers (P08 only) get 36-month sheets from round 1. Everything else is unchanged:
  90-day headline first, 14 d from round 2, deferral at 0.18x, cross-sell, accept the final's primary.
- Prompt rule: never call a price for other payment days or another clause an increase.
- **Replays vs main 582adc5:**
  - SAME: P01, P02 (13), P03 (13), P04, P05, P07, P10, P11 (8), P18 (5);
  - P08: only the contract length changes (24 -> 36 m in all turns). Prices and claims are identical (ad042765 replay).

**Sim** (house 0.752; `term36` = the unknown round-1 value change for 36 m):

| agent | 36 m effect | low draw | high draw |
|---|---|---:|---:|
| main 582adc5 | - | 0.721 | 0.654 |
| cloud | 0.04 premium | 0.676 | 0.609 |
| cloud | none | 0.721 | 0.654 |
| cloud | **0.04 discount** | **0.766** | 0.699 |

**Expected value:** symmetric unknown, so about 0 ± 0.045 per game. It is the only remaining lever that can beat the house, it costs us
nothing at equal price, and one run settles it.

**Reading for TASK 15** (round 1 settles it):
- **Low draw** (24 m answered 5.41-5.42 @ 90): a 36-month headline below 5.41 -> keep 36 m; above 5.42 -> revert to 24 m.
- **High draw:** compare against 5.53.
- **Not answered on 36 m** (it counters 24 m): no effect -> next lever is the deeper anchor.
