STATUS: DONE (task 9) - 2026-10-10 evening, cloud session, offline only (9 P08 games incl. c387f78034601d57; no arena, no LLM).
Values = its price as a 30-day, db0 cash value at 8% (engine_dump.py P08 --rate 0.08). Our ask value = the sheet best for it.

# P08: is there a lever after round 1 worth 2-3 cents?

Round 2 so far: every clause-free game stepped **+0.10 in value = 16% of the gap** (5.34-5.46 vs our 4.717) and drew
**-0.15 / -0.16 / -0.17** (a43d, c387 / 1363, cae4). The final is **-0.05** whatever we do (-0.10 once, high draw). House 0.752 = value 5.10.

## Lever 1: a bigger round-2 step (30% of the gap)
| evidence | numbers |
|---|---|
| Pooled fit, 132 steps in the mirror cases | its share of the gap = 0.08 + **0.19** x our share (r 0.36) |
| per case | P02 slope **0.40** (r 0.65), P07 **0.24** (r 0.68), P08 0.13 (r 0.20), P01 / P18 ~0 (r ~ -0.1) |
| P08 round 2 | only ever tested at our 12-16% (taking its clause: 0.07; clause-free: **0.21-0.27**) |
| P08 round 3 | our 31-43% steps still got 0.10-0.14 of the gap = the fixed ~0.05 final: **round 3 does not respond** |
| expected | +0.087 value more from us -> its extra cut **1.1 cents (P08 fit) / 1.7 (pooled) / 3.5 (P02-like)** = +0.01 to +0.04 score |
| risk | low: the ask (EUR 4.97 @ 90 = value 4.90) stays 0.23-0.44 under its round-2 price. Worst case = today's path. Offline sims: responsive 0.93 -> 0.89 / stubborn 0.96 -> 0.95 (sim suppliers agree at the case floor, so a bigger step "overshoots"; live P08 has never agreed to a clause-free sheet; if it did, EUR 4.97 @ 90 d clause-free would score > 0.9) |

## Lever 2: stay on 90 d in rounds 2-3 (instead of switching to 14 d)
| evidence | numbers |
|---|---|
| Round 1 headline is nominal | EUR 5.41 at 45 d (a43d, ab47, 1f27) **and** at 90 d (cae4, c387): 90 d = 0.05 lower value |
| Round 2 is NOT nominal | same term 45 -> 45 (a43d): headline -0.15 = value -0.15; switch 90 -> 14 (cae4, c387, 1363): headline -0.25/-0.26, **value -0.16/-0.17**. It prices by value from round 2 on |
| final | value -0.05 on 45 d (a43d) and on 14 d (switch games) alike |
| expected | **~0 cents** (its rate ~8% = ours, so payment days are neutral after round 1). Keeping the 90-day structure is still the "hold the structure it priced" rule and costs nothing |

## Lever 3: anything else in the 9 games
| what | round-2 value step | final step |
|---|---|---|
| no data (a43d) / order history "no change" (cae4) / labour "taken" (c387, 1363) | -0.15 / -0.17 / -0.16, -0.16 | - |
| final with: forecast (5 games) / QNs (c387, 1363) / nothing (cae4) | - | -0.03 to -0.06 / -0.05, -0.10 / -0.05 |
| taking its clause in round 2 (ab47, 325d) | **-0.05, -0.09** (vs -0.16 clause-free) | |
| db5 asks below its price (1f27, 586a, 9bfa) | 0 (hold), -0.03, +0.06 | |
Data after round 1 adds nothing measurable; the clause-free round-2 ask (already in the agent) is the only big lever. Nothing else.

## Recommendation: ONE change for the next live P08 game - lever 1
- **Msg 1: unchanged** (3 sheets 45 / 14 / 90 d clause-free, cold drawing -2.3% + forecast, own quote in words).
- **Msg 2: EUR 4.97 @ 90 d, 24 m, no clause** (value 4.90 = +0.19 = 30% of the gap; was EUR 4.80 @ 14 d), + labour -0.3%.
  Stays on the 90-day term it priced in round 1.
- **Msg 3: the agent's schedule from there** (+~0.06 value, still >= 0.15 under its price) + QNs, no figure; then accept its final.
- Expect low draw 5.10-5.12 (0.73-0.75, house 0.752 within reach), high draw 5.18-5.22. One game decides it; if its round-2 step
  stays at -0.16, revert (nothing lost).

## In the cloud copy and replay check
`analysis/agent_variants/noidea_neel_cloud.py` = main's noidea_neel.py (d58bdd6) + `R2_HEDGED_SHARE = 0.30`: round 2 only, only when
the dossier motive is `hedged_forward` (P08 among the practice cases; hidden suppliers carry it from the data package).
`analysis/tools/replay_cmp_cloud.py OLD NEW games...` (replay_cmp.py with both files as arguments), old = main d58bdd6:
| game | result |
|---|---|
| P02 552fb056e31d24d1, 8d4c4d5d7dff80bb (0.847) | **SAME** |
| P03 2483e3891d076863, 14ab701cbfba6767 (0.936) | **SAME** |
| P11 c0d6894ce2cf586a (latest, 0.710) | **SAME** |
| P08 c387f78034601d57 (0.721), cae4b621695f8161 (0.732) | turn 2 only: EUR 4.80 @ 14 -> **4.97 @ 90**; turns 1, 3, 4 same |
