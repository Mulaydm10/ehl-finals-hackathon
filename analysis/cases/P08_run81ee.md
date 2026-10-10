STATUS: DONE (task 19) - 2026-10-10 evening, cloud session, offline only (0 arena sessions, no LLM calls).
Run: 81ee4b1e4096514b = 0.633, LOW draw, main 0bb9fad (36 m, round 2 on 60 d, deferral, floor trade; P03 own-quote change gated off).

# Run 81ee: round 2 on 60 d (plus an anchoring opening line) raised its floor by 0.08 - back to 14 d

## 1. Mistakes report, e-mail by e-mail

| msg | ours (value) | its reply (value) | trace reasons | mistake? | cost |
|---:|---|---|---|---|---:|
| 1 | 4.79 @ 90 / 4.73 @ 45 / 4.70 @ 14, 36 m, clause-free; own quote in words; cross-sell; forecast; PPI -2.3% | 5.41 @ 90 = 5.338 (alt 5.45 @ 14 db5) | index and volume taken; "appreciate the prospect of future business"; "**Building on your preference for 14-day payment terms**, we can offer ..." | none (24-month level 5.41, not 36 m's 5.40) | 0 |
| 2 | **4.94 @ 60** (30% step) = 4.907, LCI-C. Opening: "**We require pricing no higher than the current level until that coverage expires**" | **5.34 @ 60 = 5.304 (-0.033)** | LCI-C "factored it into our calculation"; "**Accommodating your requested 60-day payment terms**, we can offer a revised base price"; "Our standard Zahlungsziel is … days net" | **yes: round 2 on 60 d, and an opening that names an acceptable price level (the current 5.45, above all its offers)** | **-0.08** (floor 5.205 vs 5.12-5.14) |
| 3 | 4.95 @ 60 (+0.01 = 0.30x its step), 7 QNs | 5.29 @ 60 = 5.255 open (-0.049): deferral | QNs "do not warrant a price reduction" | none | 0 |
| 4 | 5.03 @ 60 (normal step), order history; **floor trade not sent** (its expected final 5.205 is above every final in memory: gate correct) | final 5.24 @ 60 = 5.205 (-0.050) | order history "does not reflect our current cost structure" | none | 0 |
| close | accepted its primary | 5.24 @ 60 = 0.633 | - | correct | - |

The deferral split what was left evenly (0.049 / 0.050), so after round 2 its floor was already **round-1 value - 0.133**: round 2 moved the
floor itself, not just the path.

## 2. The -0.033: what differs from the other low draws

| game | draw | our round 2 (value) | gap | round-2 cut | total | final | "current level" line |
|---|---|---|---:|---:|---:|---:|---|
| 94e77b7b | low | 4.88 @ **14** (4.897) | 0.431 | 0.099 | 0.200 | 5.128 | - |
| a4b92d2f | low | 4.89 @ **14** (4.907) | 0.440 | 0.109 | 0.210 | 5.138 | - |
| ad042765 | low | 4.89 @ **14** (4.907) | 0.430 | 0.099 | 0.200 | 5.138 | msg 3 |
| 6912fd89 | low | 4.97 @ 90 (4.904) | 0.434 | 0.118 | 0.217 | 5.121 | - |
| **81ee4b1e** | **low** | **4.94 @ 60 (4.907)** | **0.431** | **0.033** | **0.133** | **5.205** | **msg 2** |
| db7d315a | high | 4.97 @ 60 (4.937) | 0.519 | 0.162 | 0.281 | 5.175 | - |
| b1ca3790 | high | 4.97 @ 60 (4.937) | 0.519 | 0.172 | 0.291 | 5.165 | - |

- **Ruled out:**
  - the size of our step: the same value (4.907) as a4b9 / ad04;
  - the gap: 0.431, the same as 94e7 / ad04;
  - the gap rule: it predicts 0.110;
  - 36 m: 94e7 was 36 m and normal.
- **Nominal vs value:** its pairs price payment at 6.5-8.7%, so 60 d is value-neutral for it. Its own words moved: round 1 "building on your
  preference for 14-day payment terms", round 2 "accommodating your requested 60-day payment terms" (a concession it charged for).
- **Two candidates, confounded in this one game:**
  1. **60 d on a low draw.** n = 1; the two 60-d high draws were normal or better (db7d, b1ca), so 60 d alone is not proven.
  2. **The opening line "We require pricing no higher than the current level"** in round 2: it names an acceptable price level, the current 5.45, above every offer it made. In ad042765 the same line came at msg 3 (the deferral round) and the total was 0.200, at the low end of the band.
- **Not explained by noise:** total 0.133 vs 0.199-0.220 in 8 low draws (≈ 9 sd).
- **Decision:** fix both, at no cost. 14 d is the proven term (6 low draws, totals 0.200-0.220), and the 60-d grid gain was only +0.0006.

## 3. Fixes (`noidea_neel_cloud.py`, from main b6f22ce; the P03 `OWN_QUOTE_ID` change is kept)
- `PAY_DAYS_HEDGED = None`: round 2 goes back to the shortest term, 14 d (task 12 behaviour). Messages 3-4 then hold its term.
- **Prompt rule:** "Never name a price level we could accept ('no higher than the current level', 'around EUR X'): the figures below are our only position."
- **Floor trade unchanged:** it correctly did not fire here (expected final above every final in memory).

## 4. Sim refit (sim_donautal.py, 19 games)
- High-draw budget 0.278 (1363 .258, db7d .281, b1ca .291).
- `LOW_60_BUDGET = 0.133` with a round-2 cut of 0.033 for a low draw on 60 d (81ee, n = 1).
- Deferral threshold 0.35x (it deferred at 0.18-0.30x live; went final at ≥ 0.9x).
- `--validate` over 61 replies: median |diff| 0.010. 81ee reproduces within 0.01 at every step.

| agent | low draw | high draw |
|---|---:|---:|
| main 0bb9fad (60 d) | 0.644 (live 0.633) | 0.677 (live b1ca 0.677) |
| **cloud (14 d)** | **0.7323** (5.10 @ 14 = the record) | 0.676 |

**P(score > 0.7323) per run with 14 d** (loop report 2 noise model): 20% per low draw at a 5.40 headline, 2% at 5.41, so ≈ 11% per low
draw and ≈ 7% per run. Add the floor trade's upside if its floor is soft (task 18).

**Replays vs main b6f22ce:**
- SAME: P01-P05 (P03 13 incl. the own-quote change), P07, P10, P11 (8), P18.
- P08: round 2 goes 60 d -> 14 d at the same value (81ee: 4.94 @ 60 -> 4.89 @ 14); later turns are unchanged.

**Conclusions.**
1. Run 81ee lost 0.08 in round 2 alone: its floor that session was 5.205, against 5.12-5.14 in every other low draw. Its cause is either round 2 on 60 d (its first low draw) or the opening line naming "the current level" as acceptable, or both.
2. Both are reverted or blocked: round 2 on 14 d (6 low draws, totals 0.20-0.22) and a prompt rule against naming any acceptable price level.
3. The 60-d cent-grid idea is withdrawn: +0.0006 is not worth an untested structure. The user has not approved another live run; this is ready if they do.
