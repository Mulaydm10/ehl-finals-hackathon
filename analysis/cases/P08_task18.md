STATUS: DONE (task 18) - 2026-10-10 evening, cloud session, offline only (0 arena sessions, no LLM calls).
Goal: P08 above our record 0.7323 (cae4b621: 5.10 @ 14) in one live game; house 0.752. Agent: `noidea_neel_cloud.py` = main
`noidea_neel.py` (d3f51b2 / d32ed1f) + the floor-trade pair below. Task 17 (P03) was cancelled; its commit is reverted on this branch
(it never reached main).

# P08 task 18: the current recipe plus one free lottery ticket (floor trade at the final message)

## 1. New teammate learnings since loop report 3, and whether they apply to P08

| learning | source | applies to P08? |
|---|---|---|
| 63 ask the floor; let its answer choose the ladder | Dhruv v2.19b, P11 | no gain: P08's final IS its floor (r1 - budget). Naming it changes nothing; asking at msg 3 would take the deferral round |
| 64 check every new rule on every case offline | Dhruv | yes: done (sim both draws, 76 replays) |
| 65 supplier memory (H_supplier_memory.json: agreed / refused / finals per structure) | Dhruv v2.20 | **yes, as a gate**: 70710 has 18 games, finals per structure, but **no agreed or refused ask ever** (we never asked near its price). The lowest final by value (5.118, cae4) gates the hair sheet below |
| 66 floor trade: at a hard floor, trade a term that is cheap for it + a hair-under sheet | Dhruv v2.21, P11 | **yes, adapted**: P08's "term" is its own clause structure (it insists on AS-14404 in 18 of 18 games). Untested live on P11 (the trade never got a round) |
| P11 loop 8/8: floor 45.00 hard (0 of 9 asks under it); "lead the first probe WITH the trade pair" | Dhruv | P08 has no grid and no probe round; the pair goes out at the one message that is not final: our 4th, after the deferral |
| 67-71 final trigger, budget, nominal first counter, deferral, cent grid | ours (section J) | in the agent already |
| 72 mirror gap steps (not for hedged suppliers) | Parth | correctly gated off for P08 |
| 73-75 weak facts only on a holder; QNs only if quality is a problem; ≤ 8 IDs per claim | Parth | P08 is green (75 ppm): our message-3 QN claim is 7 IDs (≤ 8). It drew "do not impact our pricing" 6 of 6, but it is the deferral round's filler: the step, not the fact, defers |
| 76 order history as a PATH | Parth | P08's order history is flat (5.43-5.45): no path, "does not change" 6 of 6 |
| 77-78 credible anchor (P10), floor-stop recipe (P04) | Parth | no |

## 2. Unfixed or new in the last 4 loop runs

| run | score | what happened | cost | status |
|---|---:|---|---:|---|
| ad042765 | 0.710 | model-written opening: "We reject a price increase for shorter payment terms" (misread) | 0 measured | fixed (prompt rule, task 14) |
| 94e77b7b | 0.721 | none; 36 m headline 5.40 | - | - |
| 8180d389 | 0.721 | deep anchor: headline 5.41, round 2 took 0.16, so no deferral | 0 (budget) | reverted (task 16) |
| b1ca3790 | 0.677 (high draw, best high) | none; 36 m did NOT lower the high headline (5.53); budget 0.291; 60 d final 5.20 | - | - |
| all | - | the model-written opening still asks for "a deadband" and "no adjustment before your coverage ends" (not in our sheets) | 0 | harmless, left |
| all | - | message 3's QN claim and message 4's order history are always "does not change" | 0 | fillers by design (an empty round drew "Which figures ...?") |

## 3. What maximises P(score > 0.7323)

The record needs a final below value ~5.113 on the 60-day grid (5.15 @ 60 = 0.7329 or lower), and only a low draw can get there (high draws
end 5.165-5.198).

| setup | P(beat) per low draw | per run (low draws 62%: 10 of 16) | mean low | notes |
|---|---:|---:|---:|---|
| main as is (36 m, 60 d, deferral) | 34% (5.40 headline 54%, 5.41 13%) | **~21%** | 0.729 | the noise model of loop report 3 |
| **+ floor-trade pair at msg 4 (cloud)**, its floor HARD (P11-like) | 34% | ~21% | 0.729 | refused -> its usual final: no cost (sim identical) |
| + floor-trade pair, floor soft by ≥ 1 cent | ~90% (agreed at 5.14 / 5.15 @ 60 whenever the deferral happens, 6 of 7) | ~56% | 0.744 | the pair is the only way under its final |
| weighted (prior 15-20% that its floor is soft: P11's was hard 0 of 9) | ~44% | **~26%** | | |
| + "ask the floor" at msg 3 | - | ≤ 21% | | it would spend the deferral round; the answer equals its final anyway |
| + 2nd deferral (DEFER_TIMES 2) | - | 21% | | under the budget model it only spreads the same total |

**Floor-trade pair** (`HAIR_HEDGED`, `HAIR_CENTS = 1`, P08 only):
- **When:** at our 4th message, only after its 3rd message stayed open (the deferral).
- **What:** two sheets.
  - our usual clause-free normal step;
  - ITS structure (AS-14404 db0 clause, its payment term, its contract length) at **one cent under its expected final** (standing value minus its last step, which is how the deferral splits the rest, 6 of 6).
- **Gate:** sent only if that hair is worth less to it than every final it ever gave (supplier memory: < 5.118), i.e. only on a low draw. On a high draw the clause sheet only risks its smaller clause budget (sim 0.666 -> 0.644 without the gate; ab47 / 325d took the clause and got -0.09 / -0.15 totals).
- **Outcomes:** refused -> it goes final at its floor as always (message 4 is its final message anyway). Agreed -> we accept the agreed sheet (5.14 @ 60 = 0.7441, or 5.15 @ 60 = 0.7329 after a 5.41 headline).

## 4. Planned e-mails (low draw, 36 m)

| msg | our sheets (clause-free, 36 m) | data | expected its answer |
|---:|---|---|---|
| 1 | 4.79 @ 90 (first, +1 cent), 4.73 @ 45, 4.70 @ 14 | own 5.45 quote in words; forecast +1.9%; PPI-C2431 -2.3%; cross-sell; call-off schedule | 5.40 / 5.41 @ 90 (value 5.328 / 5.338) |
| 2 | 30% step re-priced at **60 d** (4.93 @ 60) | LCI-C -0.3% | -0.10 to -0.12 (gap rule) |
| 3 | +0.18x its last step (deferral) | 7 QNs (≤ 8 IDs) + cross-sell reminder | open, half the rest (-0.05) |
| 4 | normal step **+ its structure: AS-14404 db0, 60 d, 36 m at its expected final - 1 cent** (e.g. 5.14 @ 60) | order history | final 5.15 @ 60 (0.7329, hard floor) **or agreed 5.14 @ 60 (0.7441)** |
| close | accept its final's primary, or the agreed sheet | - | - |

## 5. Checks
- **sim_donautal**:
  - `--validate` over 57 replies: median |diff| 0.010.
  - Agent: low 0.7329 / high 0.6661 with a hard floor (identical to main).
  - Soft floor by 0.01 or 0.02: **low 0.7441** (agreed 5.14 @ 60), high 0.6661.
- **Replays vs main (d32ed1f)**:
  - SAME: P01-P05, P07, P10, P11 (8), P18, and 11 of 12 P08 threads.
  - Changed: only 6912fd89 turn 4, which adds its-structure 5.18 @ 90, one cent under that game's live final of 5.19.

**Conclusions.**
1. Nothing new moves P08's budget. The record is a coin we win in ~21% of runs (60-day cent grid on a 5.40 / 5.41 low-draw headline).
2. The one new idea that can beat its final, the floor trade (rule 66): its own clause structure one cent under its expected final, at the message after the deferral, gated by supplier memory to low draws. It costs nothing if its floor is hard and wins the record if it is soft. P(beat 0.7323) ≈ 21% (hard floor) to ~56% (soft), about 26% weighted.
3. Beating the house (0.752 = 5.08 @ 14 / 5.13 @ 60) still needs a 2-cent soft floor or a lucky budget (~1-2%).
