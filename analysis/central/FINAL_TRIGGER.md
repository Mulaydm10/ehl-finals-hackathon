STATUS: DONE (cloud task 10) - 2026-10-10 evening, cloud session, offline only (0 arena sessions, no LLM calls).
Tool: `cd tacto/starter-kit && uv run python ../../analysis/tools/final_trigger.py [P08 ...] [--rows]` (every reply of every archived
single-supplier game: 92 games, 353 replies; P05 left out because it is an RFQ). Values are the supplier's cash value per unit at its cash
rate (P02 6.6%, P03 6.1%, the rest 8%). "N" = the message of ours at which this supplier usually goes final.
Fix along the way: `engine_dump.load_games` skipped a session whose `datasets/runs` copy had no result yet (db7d315a was missing).

# What triggers final_offer?

## 1. Where the final falls, and three candidate rules

| case | engine | games | final at our msg k (games) | N | rule "k >= N" | rule "gap after our msg <= 3%" | rule "our step >= 30% of gap" |
|---|---|---:|---|---:|---:|---:|---:|
| P01 | mirror | 5 | 5: 1 (others closed before) | 5 | 17/18 | 10/18 | 11/18 |
| P02 | mirror | 19 | 4: 14, 5: 3 | 4 | 74/77 | 26/77 | 52/77 |
| P03 | holder | 14 | 3: 1, 5: 5 | 5 | 52/53 | 18/53 | 35/53 |
| P04 | floor-stop | 3 | 2: 1, 3: 2 | 3 | 7/8 | 6/8 | 6/8 |
| P07 | mirror | 10 | 4: 9 | 4 | 39/39 | 29/39 | 29/39 |
| P08 | partial mirror, hedged | 10 | 3: 9, **4: 1 (db7d315a)** | 3 | 30/31 | 21/31 | 25/31 |
| P18 | mirror | 10 | 2: 2, 3: 7, 4: 1 | 3 | 26/32 | 21/32 | 21/32 |
| P10 | one-shot | 18 | 1: 10, 2: 7 | 1-2 | 17/29 | 12/29 | 14/29 |
| P11 | holder | 16 | 3: 1, 4: 3, 5: 2, 6: 1, 7: 1 | - | 52/66 | 47/66 | 45/66 |
| **all** | | 92 | | | **314/353 = 89%** (95% without P10/P11) | 190/353 = 54% | 238/353 = 67% |

- P10: final at our 1st message whenever round 1 was a normal anchor (10/10). Round 1 stayed open only after a credible anchor near
  today's price (7/7), and then the final came at message 2.
- P11 (holder): the final always arrives as a "hold" (no move) after 1-3 earlier holds, so it is counted in holds, not messages.

## 2. At message N: our step versus its last step (mirror and floor-stop cases)

| case | N | our step >= 0.9x its last | 0.6-0.9x | < 0.6x | its last step <= 0 | open at N: why |
|---|---:|---|---|---|---|---|
| P02 | 4 | final 12 / open 2 | - | open 1 | final 2 | all 3 opens had **< 0.35% gap left** (552fb056 0.29, 8d4c4d5d 0.31, ee98266b 0.25): it countered once more, then went final |
| P01 | 5 | final 1 / open 1 | - | - | - | 8bdb783a: 0.29% gap left (same pattern) |
| P07 | 4 | final 9 | - | - | - | - |
| P08 | 3 | final 7 | - | **open 1 (db7d315a, 0.19x, gap 5.1%)** | final 2 | the only small step at N in 10 games |
| P18 | 3 | final 4 / open 1 | - | final 1 (06f8f4f5, 0.53x) | final 2 / open 1 | 6d61c1fd = same inputs as a99d02eb (final): chance |
| P04 | 3 | final 2 | - | - | - | - |

## 3. P08 round by round (value EUR/kg; ratio = our step / its last step)

| game | draw | k2: ours / its step | k3: our step (ratio) | k3 reply | k4: our step | k4 reply | final value | score |
|---|---|---|---|---|---|---|---:|---:|
| cae4b621 | low | +0.10 / -0.17 | +0.15 (0.92) | final -0.05 | - | - | 5.118 | 0.732 |
| c387f780 | low | +0.10 / -0.16 | +0.15 (0.97) | final -0.05 | - | - | 5.128 | 0.721 |
| 136352b4 | high | +0.10 / -0.16 | +0.15 (0.98) | final -0.10 | - | - | 5.198 | 0.642 |
| a43d77c0 | low | +0.11 / -0.15 | +0.15 (1.03) | final -0.05 | - | - | 5.193 | 0.647 |
| 5 others | mixed | | 1.02-2.48 or its step <= 0 | final -0.03 to -0.06 (one +0.07) | - | - | 5.30-5.53 | 0.00-0.52 |
| **db7d315a** | high | **+0.22 (30%)** / -0.16 | **+0.03 (0.19)** | **open -0.06** (validity 30) | +0.08 (1.35) | final -0.06 | **5.175** | **0.666** |

- An extra round in P08 is worth its usual ~1.1% step: about 0.05-0.06 value, so about 0.05-0.06 score (1 cent = 0.011). Against 136352b4,
  played on the same high draw, the gain was only +0.023 value / +0.024 score, because 136352b4's final step happened to be large (-0.10).
- Walk-away: 0 in 31 P08 replies. The only P08 walk (1f27ac1b) came after we pushed past its final.
- Hold: 1 in 10 games (1f27ac1b, round 2, when we switched to db5 asks below its standing price). There was no hold after the small step.

## 4. P08 recipe (in `analysis/agent_variants/noidea_neel_cloud.py`; constants `FINAL_AT_MSG`, `DEFER_RATIO`, `DEFER_FLOOR`, `DEFER_MIN_GAP`)

| our msg | ask | expected reply |
|---:|---|---|
| 1 | as now | 5.34 (low draw) or 5.46-5.51 (high draw) |
| 2 | 30% of the gap (task 9, live in main) | about -0.16 |
| 3 | **+0.25x its last step, at least 0.2% of its price; same structure** (db7d315a: +0.03 live, the code gives +0.04) | open, about -0.06 (seen 1 of 1) |
| 4 | normal step (db7d315a: +0.08) | final, about -0.06: accept it |

Defer **once only**. A second small step at message 4 is untested. Its validity was still 30 days at the open message-3 reply, so the round
limit leaves room; try it in a practice game before relying on it. Downside if it goes final at message 3 anyway: we asked ~0.1 less than
usual. Its final steps showed no clear link to our step size (-0.05 after +0.15, -0.03 to -0.06 after +0.07 to +0.09), so expect about
-0.01 value (~0.01 score) at most. Expected net gain: about +0.04 per P08 game.

**General rule (gated):** at our message `FINAL_AT_MSG[case type] = 3` (raw_material: P08 9/10, P18 7/10 go final there), and only for a
`hedged_forward` supplier, while the gap is still >= 2% and it moved last round, our step is 0.25x its last step. Hedged-only, because
P18 mirrors 0.8-0.9 of our step, so an extra round buys nothing there: 6d61c1fd went final one message late and scored 0.61, against 0.62
for its identical twin. Hidden raw-material suppliers with a hedge get the rule. Every other case type is untouched.

## 5. Replays (`replay_cmp_cloud.py noidea_neel.py noidea_neel_cloud.py`, real supplier messages)

| games | result |
|---|---|
| P02 552fb056, 8d4c4d5d (0.847) | SAME |
| P03 14ab701c, 2483e389 (0.936) | SAME |
| P11 6b02b8cc, 4d6c9a13 (0.794), 87670537, c0d6894c (0.710) | SAME |
| P18 06f8, 3620, 6833, a99d, bf73 | SAME (not hedged) |
| P08 db7d315a | turn 3 5.00 -> 5.01 and turn 4 5.08 -> 5.09 (the code reproduces the live deferral) |
| P08 cae4b621, c387f780, 136352b4 | turn 3 only: 4.95 -> 4.94-4.96 (in these replays our round-2 ask already differs from the live one, so a smaller step shows here as a different payment-day sheet) |

**Conclusions.**
1. The final comes at a fixed message count per supplier (89% of replies; 95% for mirror, holder and floor-stop). Neither the gap nor our step size triggers it.
2. Two things pushed it one message later: a gap below 0.35% (4 of 4: it counters once more to close) and a step at message N far below its own (P08, 0.19x, 1 of 1). P18 also had ±1 by pure chance.
3. P08: make one small step (0.25x) at message 3 and a normal step at message 4. Worth about +0.05 when the deferral works and about -0.01 when it doesn't. It is in the cloud copy, gated to hedged raw-material suppliers. P02, P03, P11 and P18 replays are SAME.
