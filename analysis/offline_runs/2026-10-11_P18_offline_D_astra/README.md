# P18 offline run D (2026-10-11 ~05:15, gpt-6-astra configured; no arena session): verify the record attempt noidea_p18_pay14.py

Commands (strictly local):
    cd tacto/starter-kit
    .venv/Scripts/python.exe ../../analysis/tools/p18_pay14_check.py                          -> pay14_check.txt
    .venv/Scripts/python.exe ../../analysis/tools/p18_replay_agents.py replay noidea_p18_pay14   -> archived_replay_pay14.txt
    set -a && . ./.env.openai && set +a
    .venv/Scripts/python.exe ../../src/eval/offline_eval.py --agent-file ../../analysis/agent_variants/noidea_p18_pay14.py --llm --show P18

| check | result |
|---|---|
| msgs 1-2 vs 6c2813ce | byte for byte equal (subject, body, sheets, refs) |
| msg 3 | 6c2813ce's msg 3 + "We now offer payment in 14 days net instead of 45 days ..." + the two record sheets 4.97 @ 14 d db5 (0.7593) / 4.86 @ 14 d db0 (0.7611); prose = sheets; refs = its labour index (verified there) |
| agreed on either sheet | accept its primary |
| hold 5.00 (45 d or 30 d) / counter 5.00 @ 14 d / off-track 4.95 | msg 4 = its msg 4 + on-time delivery 81.0% (sc:70740@2026Q3, a new fact) + 5.00 @ 14 d db5 (0.7393) / 4.90 @ 14 d db0 (0.7339) |
| counter 4.85 @ 14 d (a record) | accept at once |
| final | accept its primary (never an '-a' id) |
| archived replay | see the line below; 0 errors |
| documented simulator + Astra | 0.94 at msg 1 (not predictive, Run 1); 0 Astra calls (code-written P18 messages) |

Expected (judgement): record if its 2% rule reads its value or its primary price AND 14 d is worth ~+0.10 to it in this
conversation (~0.4); else msg 4 at value 5.00 (0.739 / 0.734, over our 0.727) if its floor allows; else its final (~0.67-0.69).
**Selected for the single live game.**
- archived replay: 42 games, 0 errors
