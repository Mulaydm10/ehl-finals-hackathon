# P18 live a9711492eacdd9a7 (2026-10-11 06:13 CEST, local, `noidea_p18_replay.py` with P18_MSG3=5.01/14/5): **0.673 - in the 0c968aae state 5.01 db5 is not worth its 4.91**

User: "run both" (the record attempt v2, then this). Offline G (509033f) had dry-run this exact ask.

| our msg | sheets (24 m) | its answer |
|---:|---|---|
| 1-2 | 0c968aae's msgs 1-2 byte for byte | 5.20 @ 30 d, then **5.00 @ 14 d**: the 0c968aae state, reproduced again (within a second) |
| 3 | 0c968aae's msg 3 with only the sheet: **5.01 @ 14 d db5** (0.7327; 1.76% under its 5.10 db5; 4.91 to it if db5 = +0.10) | **hold 5.10 @ 14 d db5**: "For the requested terms including a 5% deadband ... we must hold firm at EUR 5.10"; labour "negligible" |
| 4 | (the replay agent's hold branch) a09d9536's msg 4 with 5.00 @ 30 d db5 + 4.90 @ 30 d db0 | **final 5.10 @ 14 d db5**: "To maintain the price of EUR 5.10 per unit, we must hold firm on the 14-day payment term ... Which figures is that based on? Please send us the data." |
| - | accept | 5.10 @ 14 d db5 = **0.6727** (C 246,386.78) |

## What it establishes
- **In the 0c968aae state the db5 sheet is priced on its own 5.10 db5 offer, not as db0 + 0.10.** 4.91 db0 was agreed at msg 3 there;
  5.01 db5 (the same value at +0.10) drew a hold at 5.10 db5. With 2782c270 (5.00 db5 -> final 5.10 db5) and d05baf28 (4.97 db5 ->
  final 5.10 db5): its db5 limit in this state is above 5.01, so in acceptance db5 is worth less than 0.10 to us here, or its db5
  limit is set separately. The 0c968aae state is fully mapped: 4.91 @ 14 d db0 (0.727) is its only beat-our-best ask.
- The hold branch's msg 4 moved to 30 d, which this conversation prices a step (lever 17); a 14-d msg 4 would not have reached 0.727
  either (4.91 db0 after 5.01 db5 is no step in its value).
- Team best on P18 stays 0.727 (0c968aae); record 0.756 (Codacabana). Practice sessions left: 324.
