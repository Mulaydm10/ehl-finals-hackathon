# P18 offline run H2 (2026-10-11 ~06:25, no arena session, no LLM): archived replay of `noidea_p18_coda.py`

**Command** (strictly local):
    cd tacto/starter-kit && .venv/Scripts/python.exe ../../analysis/tools/p18_replay_agents.py replay noidea_p18_coda   -> archived_replay_coda.txt

Every recorded P18 game in datasets/runs (42 games) fed turn by turn to the agent; it prints what it would send next to what was sent live.

| check | result |
|---|---|
| games replayed | 42 |
| errors / tracebacks | 0 |
| turn 1 | 4.77 @ 45 d, no clause, 6c2813ce's refs, in every game |
| turn 2 | 4.84 @ 45 d db0 + forecast, in every game |
| turn 3 | 5.00 @ 45 d db5 + 4.89 @ 45 d db0 + labour (record sheets) |
| turn 4 | 5.02 @ 45 d db5 + 4.92 @ 45 d db0 + OTD (step) after a 5.00/5.10 reply; accept on final/agreed |

Selected for the live game (user: "run offline 2 times and then run on the arena").
