# P18 Run 1 - offline baseline with gpt-6-astra (2026-10-11 04:36, code aee97f3; no arena session)

**Model:** gpt-6-astra (provider openai, from tacto/starter-kit/.env.openai, gitignored). **Qwen:** not used - the documented
local Qwen server (Dhruv's Mac, MLX, port 8081) is not reachable from this laptop (curl localhost:8081 -> exit 7), and the user
said "dont use qwen. use astra everywhere".

**Commands** (strictly local: src/eval/offline_eval.py imports only the cost model, the simulator and the LLM client - no arena
client; p18_cross_check.py reads datasets/runs only):
    cd tacto/starter-kit && set -a && . ./.env.openai && set +a
    .venv/Scripts/python.exe ../../src/eval/offline_eval.py [--agent-file ../../analysis/agent_variants/<agent>.py] --llm --show P18
    (agents: main noidea.py, noidea_p18_cross, noidea_p18_soft (v2), noidea_p18_replay with P18_MSG3=4.91/14/0)
    .venv/Scripts/python.exe ../../analysis/tools/p18_cross_check.py --replay

| agent | sim (responsive / stubborn) | msgs | Astra calls | file |
|---|---|---:|---:|---|
| main noidea.py | 0.94 / 0.94 (deal) | 1 | 2 (15.5 s mean, 18.2 s max, 0 errors) | sim_main.txt |
| noidea_p18_cross | 0.94 / 0.94 (deal) | 1 | 0 | sim_noidea_p18_cross.txt |
| noidea_p18_soft v2 | 0.94 / 0.94 (deal) | 1 | 0 | sim_noidea_p18_soft.txt |
| noidea_p18_replay (4.91) | 0.94 / 0.94 (deal) | 1 | 0 | sim_noidea_p18_replay.txt |
| archived replay (cross over 41 games) | - | - | 0 | archived_replay_cross.txt (0 errors) |

**What Run 1 establishes**
1. **The documented simulator cannot rank P18 strategies.** It agrees to any sheet that costs us at least C_best; our 4.76 @ 30 d
   no-clause opening costs 227,143 > C_best 222,651, so every agent "closes" at message 1 (0.94). The real Werdenfels counters
   5.20 with its AS-14404 clause (8 of 8 with this opening) and never counters under 5.00. Simulated scores here are NOT forecasts.
2. **Astra is exercised only by main** (round-1 prose). The P18 variants write rounds 1-4 in code (0 LLM calls), so the hosted
   run's P18 messages do not depend on the model.
3. **Main's Astra round 1 = the same facts as our best games** (order prices 5.26 -> 5.84 with po IDs, AS-14404 -8.5%
   2024-11 -> 2025-10, PPI-C2431 -2.3% 2026-06 -> 08, all verified live before) plus two ID-less sentences: the 80% PPI clause
   that "raised our price by 11% this year" (5.26 -> 5.84 = +11.0%, true) and "other suppliers quote about EUR 5.45" (true:
   quote:7300008, sup:70710, 2026-09-10; outside the case refs, so not cited by ID).
4. **The hosted outcome of every existing candidate is already known**, because Werdenfels answers an identical conversation
   identically (15438619 x6, 0c968aae replayed x8): cross -> its f2770f53 path, 90 d charged, final 5.00 @ 30 d = 0.677;
   soft v2 -> 0.677 (15438619); replay with 4.91 -> 0c968aae again = 0.727 (a tie, no gain); replay default 4.97 db5 -> 0.673.
   **No existing candidate can improve on 0.727 in one hosted run.** Run 2 must test a new input with a real chance above 0.727.
