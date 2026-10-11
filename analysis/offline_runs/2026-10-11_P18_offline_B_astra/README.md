# P18 offline run B (2026-10-11 04:51, gpt-6-astra configured; no arena session): verify noidea_p18_state45 v2

Code: main at e67addb (includes Dhruv's final-v2 promotion; noidea.py changed) + `analysis/agent_variants/noidea_p18_state45.py` v2.

**Commands** (strictly local):
    cd tacto/starter-kit
    .venv/Scripts/python.exe ../../analysis/tools/p18_state45_check.py                        -> state45_v2_check.txt
    .venv/Scripts/python.exe ../../analysis/tools/p18_replay_agents.py replay noidea_p18_state45  -> archived_replay_state45_v2.txt
    set -a && . ./.env.openai && set +a
    .venv/Scripts/python.exe ../../src/eval/offline_eval.py --agent-file ../../analysis/agent_variants/noidea_p18_state45.py --llm --show P18
                                                                                              -> sim_state45_v2.txt

## What run A changed (v1 -> v2)
Each ask now goes on db5 and db0 at the same value to it (it prices db5 at exactly +0.10; db5 is worth 0.1125/kg to us):
msg 3 = 5.03 @ 45 d db5 (0.7420) + 4.93 @ 45 d db0 (0.7357); msg 4 after a hold = 5.04 db5 (0.7354) + 4.94 db0 (0.7289). The
never-repeat guard now compares values to it, not raw prices.

## Results (with the new main)
| check | result |
|---|---|
| msgs 1-2 vs 6c2813ce | byte for byte equal (subject, body, sheets, refs) - the reproduced state needs this |
| msg 3 | 6c2813ce's msg 3 with only the proposal sentence changed to the two sheets; prose and sheets agree |
| agreed on db5 / on db0 (msg 3 and msg 4) | accept its primary sheet id (never an '-a' id) |
| hold 5.00 (on 45 d or 30 d) | msg 4 = the 5.04 db5 + 4.94 db0 pair |
| final 5.00 | accept its primary |
| counter 4.93 / 4.92 (at or under our db0 ask) | accept |
| off track (counter 4.95; first counter 5.30) | next pair 5.04 / 4.94; msg 2 4.90 + forecast - no repeat, no step back, no re-cited fact |
| archived replay, 42 games | 0 errors |
| documented simulator + Astra | 0.94 at msg 1 (not predictive, Run 1); 0 Astra calls (P18 messages are code-written) |

## Expected live outcome (judgement, not a forecast)
It reproduces 6c2813ce's 5.00 @ 45 d state if the arena still holds that conversation (0c968aae was reproduced 8 times, 7 h after
it was played). Then: accepted at msg 3 (0.7420 on db5 / 0.7357 on db0) if its floor is <= 4.93 in its terms; else, if it holds,
accepted at msg 4 (0.7354 / 0.7289) if the floor is <= 4.94 (6c2813ce agreed 4.94 there); else its final 5.00 @ 45 d (0.6883).
Every accepted outcome beats our 0.727; none reaches the record 0.756 (no reproducible state allows it).
**Selected for the single live game.**
