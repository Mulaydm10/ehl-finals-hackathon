STATUS: DONE (task 20) - 2026-10-10 ~22:30, cloud session, offline only (0 arena sessions, no LLM calls). Agent: main `noidea.py` v2.26 (ecb1574).

# P11: does v2.26 still play the 0.80 path? Yes, with one difference at the floor round

**Short answer.**
- v2.26 replays every one of the 7 live P11 games move for move until the floor round. It keeps the three rules that made 0.80:
  - never an empty round;
  - a floor trade with a chargeback sheet;
  - accept its final's primary.
- **The one difference:** the first floor ask is now **44.90** with 45.00 + EUR 300 (v2.21d). eac20911's winning pair was 45.00 + EUR 300 with **44.95**.
- 44.95 now comes only one round later, alone.
- Experiments are all OFF.

## 1. Offline run (`offline_round.py P11`, main agent, template mode)
- **Round 1:** 42.77 at 300 ppm / EUR 0 (plus an 800 ppm sheet; live sends one). Content:
  - iron & steel -4.3% (PPI-C241);
  - scorecard (2376 ppm, OTD 63.5%);
  - 8D request;
  - **the "no chargebacks or penalties" line**;
  - **the late-payment admission** (96% late, paid on time from now on);
  - call-off schedule attached.
- **Round 2:** 43.07, electricity -17.1% (PPI-D351).
- **Round 3:** 43.51, forecast +20% plus "What is the lowest price at which you can sign these terms today?" (ask the floor).
- **Round 4:** its final, which we accept.
- Every round carries a new fact; none is empty.
- The sim scored 0.99 in 3 rounds. **Ignore that number:** `offline_round.py` uses `sim_floorstop`, a P04-calibrated model with no hard EUR 45.00 grid. Only the path is informative. The replays below are the real check.

## 2. Replays on real P11 supplier messages (`replay_cmp_cloud.py`, v2.26)
**Tool check:** eac20911's own agent (v2.21c, 5c0dd6d) replays its live turn 4 exactly (45.00 + EUR 300 / 44.95).

| game | draw | live (score) | v2.26 turns 1-3 | v2.26 floor rounds | verdict |
|---|---|---|---|---|---|
| **eac20911** (best) | low | 45.00+300 / **44.95 agreed** (0.802) | = live (42.77, 43.57, 44.01) | **44.90 / 45.00+300** instead of 45.00+300 / 44.95 | **differs** (see 3) |
| dbf506a3 | low | 44.90 / 45.00+300 refused, 44.95 refused, final 45.00 (0.794) | = live | = live | SAME |
| 3cc43596 | low | empty round 3, final (0.794, the v2.21b bug) | round 3 now carries the forecast (not empty) | - | fixed |
| 73c7ca29 | high | 45.10, 45.39 / 45.50+300, 45.45, accept 45.50 (0.710) | = live | = live | SAME |
| aced3c60 | high | 45.10 + cop line, agreed (0.777) | = live | 45.10 probe = live (cop line off) | SAME asks |
| 11e2d872, 605ed96c | high | as 73c7 (0.710) | = live | = live | SAME |

- Facts per round match the old agent's code too. The replay lists the code's claims; the live model adds more in prose, the same way in every version.
- **Turns 1-3 bisect:** 5c0dd6d, 0ad109f, 9d4a762, d990025, 1c1f096 and ecb1574 all give identical claims. v2.25 (cost-calc) and v2.26 (falling windows) leave P11 untouched.

## 3. Risks in v2.23-v2.26 for P11
1. **Experiments are OFF by default.** `EXPERIMENTS` comes only from the `NOIDEA_EXPERIMENTS` env variable, which is empty here. That covers good_bad_cop, planner, floor_gamble, price_path_all, subcent_close and account_value. Only `tools/experiments/run_plan.py` sets it. Do not run P11 through it.
2. **The two-step floor ask (v2.21d, `HAIR_DEEP = 0.0022`) is the only change from the 0.80 game.**

   | ask | result |
   |---|---|
   | 44.90 | refused 2 of 2 (7285, dbf5) |
   | 44.95 with the last facts (eac2, turn 4) | **agreed 1 of 1** |
   | 44.95 a round later with no facts left (dbf5, turn 5) | refused, then final 45.00 |

   The win came with the same-e-mail rule ("the hair sheet, delivered in the same e-mail as its last facts", GENERAL_RULES). The two-step pushes 44.95 one round later. In v2.26 that round still carries the QN fact, so it is not empty, but n = 2.
   **Option:** set `HAIR_DEEP = HAIR` (0.001), which sends the eac20911 pair (45.00 + EUR 300 / 44.95) in the first floor round. That is Dhruv's file and his call. I did not change it.
3. Memory term choice (v2.24) is gated to floor-stop suppliers. P11 is a grid holder, and the replays show no change.

## 4. Expected live result
| draw (P11 low ≈ 1 in 3) | path | outcomes | expected |
|---|---|---|---|
| **low** (46.00 first counter) | 45.00 hold, then 44.90 / 45.00+300, then 44.95 | 0.810 (44.90; 0 of 2 so far) / **0.802** (44.95; 1 of 2) / 0.7935 (final 45.00) | **~0.797** |
| **high** (46.50) | 45.50 hold, then 45.10 probe, then 45.39 / 45.50+300, then 45.45 | **0.777** if 45.10 is taken (3 of ~9 high draws) / 0.710 (accept 45.50) | **~0.73** |
| per game | | | **~0.75**; above 0.807 (TakeTheMoneyAndRun) needs a low draw and 44.90 |
