STATUS: DONE (task 11) - 2026-10-10 evening, cloud session, offline only (0 arena sessions, no LLM calls).
Sim: `cd tacto/starter-kit && uv run python ../../analysis/tools/sim_donautal.py [agent ...] [--validate] [--save NAME] [--max-defer N]`.
Runs: `analysis/offline_runs/P08_sim_v1_*.json` (every e-mail, sheet and reply). Agent: `analysis/agent_variants/noidea_neel_cloud.py`.

# P08 offline review: the cloud copy beats the house on the low draw (sim 0.792 vs 0.752)

## 1. Sim scores (house 0.752 = value 5.10)

| agent | low draw (first counter 5.41) | high draw (5.53) | mean |
|---|---:|---:|---:|
| main `noidea_neel.py` (140d4ea) | 0.722 (final at msg 3: our 3rd step 0.40x its last) | 0.666 (deferred by the schedule cap, = live db7d315a) | 0.694 |
| **cloud `noidea_neel_cloud.py`, DEFER_TIMES = 1 (recommended)** | **0.792** | 0.666 | **0.729** |
| cloud, DEFER_TIMES = 2 (untested live) | 0.859 | 0.733 | 0.796 |
| cloud, DEFER_TIMES = 3 (untested live) | 0.931 | 0.800 | 0.866 |
| Dhruv's `noidea.py` (main) | 0.622 (takes its db0 clause in round 2: -0.07, not -0.16) | 0.485 | 0.553 |

**How close the sim is to the 10 live games** (`--validate`: our real e-mails in, its reply out):
- 31 replies, median error 0.000.
- Every clause-free path matches to within 0.01, and db7d315a matches exactly at all 4 steps.
- The only misses are db5 / db0-clause rounds (586a -0.08, 1f27 +0.07) and 136352b4's unusually large final step (-0.10 against the -0.05 rule).

## 2. Value path (EUR/kg, cash at 30 d, db0-equivalent)

| msg | low draw: our ask -> its reply | high draw: our ask -> its reply | rule (games) |
|---:|---|---|---|
| 1 | **4.79 @ 90** / 4.73 @ 45 / 4.70 @ 14, clause-free -> 5.41 @ 90 = **5.338** | same -> 5.53 @ 90 = 5.456 | nominal headline on the sheet worth most to it; 90 d = -0.05 |
| 2 | 4.97 @ 90 (30% step) -> 5.25 = **5.180 (-0.16)** | 4.97 @ 60 -> 5.33 = 5.294 (-0.16) | clause-free -0.16 whatever our step (5/5) |
| 3 | **5.00 (+0.03 = 0.18x its step)** -> 5.19 = **5.121 open (-0.06)** | 5.00 (+0.03) -> 5.27 = 5.235 open | small step defers its final (db7d315a) |
| 4 | 5.08 (normal step) -> **final 5.13 @ 90 = 5.062 -> accept: 0.792** | 5.08 -> final 5.21 @ 60 = 5.175: 0.666 | final one message later (-0.06) |

## 3. Mistakes found in the offline run, and fixes (all in noidea_neel_cloud.py)

| # | e-mail | mistake | cost | fix |
|---|---|---|---|---|
| 1 | msg 1 | our 90-day sheet beat the 14-day one by only 0.0004 of value to it. If it ever picks 45 d, the headline is worth 0.05 more to it | 0.05-0.06 on any draw | round 1 (hedged raw material): longest payment sheet first, +1 cent so it is clearly worth the most (`hedged_raw`, line 609) |
| 2 | msg 3 | old agent: 3rd step 0.40x its last (low draw). 0.19x deferred live, 0.9x+ went final: 0.40 is untested | 0.07 (0.722 vs 0.792) | task-10 deferral, `DEFER_RATIO` 0.25 -> **0.18** (just under the live 0.19x) |
| 3 | msg 4+ | after small steps, the schedule catch-up could ask above its standing value (sim with 3 deferrals: 5.03 vs 5.00) | an "agreed" at our price or a refusal | ask capped at its standing value x (1 - 0.08%) for hedged raw material |
| 4 | all | thousands separators ("94,800", "EUR 942,312"); the arena read P11's "18,558" as 18.558 -> contradicted | trust (a contradicted claim: P02 f778b35c 0.61 vs 0.85 for the same recipe; P11 fa9a9d02 final at msg 3) | every `:,` format removed (GENERAL_RULES 39). Body only |
| 5 | msg 4 | "were at 5.43, 5.45 per 1" (dataset unit "1") | wording | " per 1 (" -> " per unit (" at send time |
| - | msg 1 | "Please send us your cost breakdown" - refused in every P08 game ("company policy") | none measured | left as is |
| - | msg 4 | order prices 5.43-5.45 cited when its offer is already below them | none measured (db7d: "does not change our calculation", final -0.06 as usual) | left as is; nothing else unused remains for msg 4 |
| - | msg 2 (high) | payment hop 90 -> 60 after its 90-day headline | none: payment days neutral (±0.005), db7d identical live | left as is |

**Replays** (`replay_cmp_cloud.py noidea_neel.py noidea_neel_cloud.py`):
- **SAME**: P02 552fb056 / 8d4c4d5d; P03 14ab701c / 2483e389; P18 a99d02eb; P11 b1f94bfe (latest, 0.777), 6123, 3d85, 8767, c0d6, 6b02, 4d6c.
- **P08 db7d315a**: only turn 1 changes (the 4.79 @ 90 sheet). Turn 3 is now identical to live (5.00).
- **Other P08 games**: turn 1, plus turn 3 where our round-2 ask already differed from the live one.

## 4. Final P08 recipe (messages 1-4)

| msg | ask (clause-free, 24 m) | structure | data (one kind, never AS-14404) | then |
|---:|---|---|---|---|
| 1 | 4.79 @ 90 d first, 4.73 @ 45, 4.70 @ 14 | no clause, 24 m | its own 10 Sep quote 5.45 in words + volume forecast +1.9% + PPI-C2431 -2.3% | expect 5.41 or 5.53 @ 90 |
| 2 | +30% of the gap (~4.97) | payment days of its headline or 60 | LCI-C -0.3% | expect -0.16 |
| 3 | **+0.18x its last step (~+0.03)** | same as msg 2 | 7 quality notifications (no figure) | expect open -0.06 |
| 4 | normal step (~5.08) | same | order history | **final_offer: accept its primary at once** (never push: 1f27 walked) |

- **Low draw:** 5.338 -0.16 -0.06 -0.06 = **5.06 < 5.10**, which is **0.79** and beats the house by 0.04. If the final after the deferral is
  only -0.03, the score is still 0.76. If the deferral fails (final at msg 3 after the small step), the score is about 0.72.
- **High draw:** 5.456 -0.16 -0.06 -0.06 = 5.175, which is **0.666** (db7d315a exactly). One deferral can't reach 5.10 here. Each further
  deferral is worth about -0.06 if it works (sim 0.733 with 2, 0.800 with 3), but that is untested: set `DEFER_TIMES = 2` only to test it.
  The downside is about -0.01, because a small step only gives up what our ask would have pulled.

**Conclusions.**
1. Sim, fitted to the 10 live games: the cloud copy scores 0.792 on the low draw (beats the house's 5.10) and 0.666 on the high draw. Main's agent scores 0.722 / 0.666.
2. The gain is the deferral (msg 3 at 0.18x) plus a 90-day round-1 headline that is now guaranteed. P02, P03, P11 and P18 replays are SAME.
3. On the high draw only repeated deferrals could beat the house: `DEFER_TIMES = 2` is the one live experiment worth trying (+0.06 if it works, -0.01 if not).
