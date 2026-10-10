STATUS: DONE (task 12) - 2026-10-10 evening, cloud session, offline only (0 arena sessions, no LLM calls).
Data: all 11 P08 games (6912fd89 included). Values = cash per kg at 8% and its 30-day standard, db0-equivalent (db5 = +0.12).
Sim: `cd tacto/starter-kit && uv run python ../../analysis/tools/sim_donautal.py [agent ...] [--validate]`; runs in
`analysis/offline_runs/P08_sim_v2_*.json`.

# P08 round 2: the payment term we ask decides the cut

## 1. Round-2 cut vs the payment terms (all 11 games)

| game | draw | its r1 headline | its r1 alternative | our r2 ask | its r2 | **r2 cut (value)** |
|---|---|---|---|---|---|---:|
| c387f780 | low | 5.41 @ 90 = 5.338 | 5.45 @ 14 db5 | 4.80 @ **14**, clause-free | 5.16 @ 14 | **-0.160** |
| cae4b621 | low | 5.41 @ 90 = 5.338 | 5.45 @ 14 db5 | 4.80 @ **14**, clause-free | 5.15 @ 14 | **-0.170** |
| 136352b4 | high | 5.53 @ 90 = 5.456 | 5.45 @ 14 db0 | 4.80 @ **14**, clause-free | 5.28 @ 14 | **-0.157** |
| db7d315a | high | 5.53 @ 90 = 5.456 | 5.45 @ 14 db0 | 4.97 @ **60**, clause-free | 5.33 @ 60 | **-0.162** |
| a43d77c0 | low | 5.41 @ 45 = 5.392 | 5.49 @ 14 db5 | 4.84 @ 45 (stay), clause-free | 5.26 @ 45 | **-0.149** |
| **6912fd89** | low | 5.41 @ 90 = 5.338 | 5.45 @ 14 db5 | 4.97 @ **90 (stay)**, clause-free | 5.29 @ 90 | **-0.118** |
| 325d6e71 | high | 5.51 @ 30 | - | 4.82 @ 30, its db0 clause | 5.42 @ 30 | -0.090 |
| ab473a1c | low | 5.41 @ 45 | 5.49 @ 14 db5 | 4.80 @ 14 / 4.84 @ 45, its db0 clause | 5.36 @ 45 | -0.050 |
| 586a9adf | high | 5.53 @ 45 | 5.49 @ 14 db0 | 4.80 @ 14 / 4.84 @ 45, db5 | 5.50 @ 45 db5 | -0.150 |
| 9bfa8610 | high | 5.53 @ 45 | 5.49 @ 14 db0 | 4.88 @ 14, db5 | 5.55 @ 14 db5 | -0.062 |
| 1f27ac1b | low | 5.41 @ 45 | 5.49 @ 14 db5 | 4.80 @ 14 / 4.84 @ 45, db5 | 5.41 @ 45 (hold) | 0.000 |

**Its cash rate, from same-round primary/alternative pairs at different payment days (13 pairs):**
- 6.5-8.7%, mean 7.7%: about 7.0% on the 90 / 14-day pairs, about 8.5% on the 45 / 14-day pairs. Within one round, payment days are value-neutral for it.
- Round 1 is the exception: the headline is the same nominal 5.41 / 5.53 at 45, 30 or 90 days. Its 90-day headline is therefore 0.054 cheaper in
  value than its 45-day one. Its alternative is derived from that headline (5.41 @ 90 -> 5.33 db0-eq @ 14, against 5.37 @ 14 after a 45-day headline).

**Reading (clause-free rounds only):**

| our round-2 payment term | games | cut |
|---|---:|---|
| moved off its 90-day headline (to 14 or 60 d) | 4 | -0.157 / -0.160 / -0.162 / -0.170 (spread 0.013) |
| stayed on its 45-day headline | 1 | -0.149 |
| **stayed on its 90-day headline** | 1 | **-0.118** |

- Staying on 90 days is 0.04 below the four switchers. Those four lie within ±0.007 of each other, so -0.118 is unlikely to be ordinary noise, but it is n = 1.
- The simplest explanation fitting all 6 games: in round 2 it re-prices by value, and when we keep its 90-day term it claws back part
  (~0.04 of 0.054) of the round-1 nominal 90-day bonus.
- Whatever the cause, leaving 90 days costs us nothing: at equal value the score is the same within ±0.005 (cent rounding). 14 days is
  also the term it proposed itself in round 1 (c387, 1f27, 9bfa, ab47, 6912).
- No hold or walk in the 4 games that moved 90 -> 14 / 60.

## 2. Sim update (sim_donautal.py, --validate on 11 games: 35 replies)
- Clause-free round 2: -0.16, but -0.118 when we stay on its 90-day headline.
- Deferral round and the final after it: -0.055 each (db7d 0.06 / 0.06, 6912 0.049 / 0.049).
- Fit to the 35 live replies:
  - 15 exact, 9 within ±0.01 (cent rounding), 2 within ±0.02;
  - the misses are the db5 / clause rounds (586a, 9bfa, 1f27, ±0.05-0.08) and 136352b4's final (-0.10 against the -0.05 rule);
  - 6912fd89 reproduces to 0.01 at every step.

## 3. Recipe (in `noidea_neel_cloud.py`; gate `hedged_raw` = raw material + hedged_forward = P08 only among the practice cases)

| msg | ask | payment | data | expected (low / high draw value) |
|---:|---|---|---|---|
| 1 | 4.79 @ 90 first (+1 cent), 4.73 @ 45, 4.70 @ 14, clause-free 24 m | **90 headline** | own Sep quote 5.45 in words, forecast +1.9%, PPI-C2431 -2.3% | 5.338 / 5.456 |
| 2 | 30% step, **same value re-priced at 14 d** (4.89 @ 14) | **14 d** (its own proposal) | LCI-C -0.3% | -0.16: 5.178 / 5.299 |
| 3 | +0.18x its last step (~+0.03), **on its 14-day sheet** | 14 d | quality notifications | deferral, open -0.055: 5.12 / 5.24 |
| 4 | normal step | 14 d | order history | final -0.055: **5.068 / 5.188** -> accept the primary at once |

The teammate's candidate is confirmed: 5.338 - 0.16 - 0.055 - 0.055 = **5.068**. In score that is **0.789**, not 0.76: at 14 d a value of 5.07 is
5.05 nominal. The house's 5.10 is beaten by 0.03.
New in the code: (a) round 2 on the shortest payment term; (b) from message 3 the ask is re-priced on its payment term. Without (b) the sim's
3rd ask hopped 14 -> 30 d, because its structure was not among our top-3 sheets (MISTAKES.md L5).

## 4. Results

**Sim** (house 0.752):

| agent | low draw | high draw |
|---|---:|---:|
| main `noidea_neel.py` 4e93806 (stays on 90 d; live 6912fd89 = 0.726) | 0.737 | 0.655 |
| **cloud `noidea_neel_cloud.py`** | **0.789** | 0.654 |

**Replays** (`replay_cmp_cloud.py`):
- **Against the task-11 cloud copy** (isolates this change):
  - SAME: all P01, P02 (13), P03 (13), P04, P05, P07, P10, P11 (8), P18 (5);
  - changed: only P08 (6912fd89: turn 2 only, 4.97 @ 90 -> 4.89 @ 14 at the same value; turns 3-4 identical).
- **Against main 4e93806**:
  - SAME: P02, P03, P11;
  - P18, P07 and P10 differ only by the task-11 fixes (24 m; P10 lead / anchor), documented in MISTAKES.md.

**Conclusions.**
1. Staying on its 90-day headline in round 2 drew -0.118 against -0.157 to -0.170 for the four games that moved off it. That is n = 1, but the switchers are tight, and moving costs nothing at equal value.
2. Recipe: 90-day headline in round 1, 14 d in round 2 at a 30% step, deferral at 0.18x, normal step, accept the final. Sim 0.789 on the low draw (beats 5.10) and 0.654 on the high draw.
3. The high draw still cannot beat the house with one deferral. A second deferral (`DEFER_TIMES = 2`) remains the only untested lever there.
