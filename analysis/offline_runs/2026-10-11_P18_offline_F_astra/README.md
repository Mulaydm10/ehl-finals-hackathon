# P18 offline run F (2026-10-11 ~06:00, no arena session): noidea_p18_beat30 - beat our own 0.727 in the 6c2813ce state on 30 d

User: "just run p18 on the arena ... beat your own record". Agent: `analysis/agent_variants/noidea_p18_beat30.py`.
    cd tacto/starter-kit && .venv/Scripts/python.exe ../../analysis/tools/p18_beat30_check.py -> beat30_check.txt

Why: the 6c2813ce state is reproducible (3 of 3). There 4.91 @ 30 d drew a HOLD and 4.94 @ 30 d was AGREED at msg 4: its limit at
30 d is in (4.91, 4.94]. Any accepted ask at or under 4.92 @ 30 d db0 (0.7317) or 5.02 db5 (0.7377) beats our 0.727.
| msg | sheets | scores |
|---:|---|---|
| 1-2 | 6c2813ce byte for byte | -> 5.20 @ 45, then 5.00 @ 45 + 5.10 db5 |
| 3 | 6c2813ce's msg 3 (labour) with 5.02 @ 30 db5 + 4.92 @ 30 db0 | 0.7377 / 0.7317 |
| 4 (after a hold) | 6c2813ce's msg 4 + on-time delivery 81.0% with 5.03 @ 30 db5 + 4.93 @ 30 db0 | 0.7310 / 0.7249 |
Checks: msgs 1-2 byte-equal to 6c2813ce; msg 3 body = 6c2813ce's with only the proposal changed; agreed / hold / final / counter
branches correct; 0 Astra calls. Odds (judgement): accepted at msg 3 if its limit <= 4.92 (~1 in 3); at msg 4 if <= 4.93;
otherwise its final 5.00 @ 30 d (0.677).
