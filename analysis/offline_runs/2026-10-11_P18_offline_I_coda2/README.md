# P18 offline run I (2026-10-11 ~06:20, no arena session, 0 Astra calls): `noidea_p18_coda2.py` (record attempt v2)

User: "run both" (the fixed record attempt + 5.01 @ 14 d db5 in the 0c968aae state).

**Commands** (strictly local):
    cd tacto/starter-kit
    .venv/Scripts/python.exe ../../analysis/tools/p18_coda2_check.py                         -> coda2_check.txt
    .venv/Scripts/python.exe ../../analysis/tools/p18_replay_agents.py replay noidea_p18_coda2 -> archived_replay_coda2.txt

## Changes vs v1 (noidea_p18_coda, live 07836ace = 0.621)
- **msg 2 = 6c2813ce's msg 2 byte for byte except the ask, 4.90 -> 4.88.** 6c2813ce's msg 2 drew the soft 5.00 @ 45 d + 5.10 db5;
  v1's msg 2 (4.84 + a db5 request) drew a normal 5.10. This is the closest new conversation to the soft one: a fresh round-2
  draw (and a fresh limit) with the best odds of a 5.00 reply. 4.88 leaves the record sheets a forward step (+0.02 / +0.01).
- msgs 3-4 reuse 6c2813ce's msg 3 / msg 4 texts (msg 4 + OTD, a new fact) with our sheets.
- **The fix:** when round 2 is not 5.00, msg 3 stays inside its 2% approval authority: X db5 + X-0.10 db0 against its db0 offer X
  (5.10 db5 0.6957 / 5.00 db0 0.6883 against 5.10), never under its 5.00 floor; msg 4 holds them with OTD. v1 sent the record
  sheets 4.1% under 5.10 there and drew its final at 5.10 at once.

## Checks
| check | result |
|---|---|
| msg 1 = 6c2813ce's msg 1 byte for byte (body, sheets, refs) | pass |
| msg 2 = 6c2813ce's msg 2 with only the ask 4.90 -> 4.88; new after that msg 1 (5 recorded games sent it) | pass |
| soft r2 -> record sheets 5.00 db5 + 4.89 (0.7618 / 0.7627); agreed / counter 4.85 / final -> accept; counter 4.90 -> hold the record sheets + OTD; hold 5.00 -> 5.02 db5 + 4.92 (0.7486 / 0.7424) + OTD; then agreed / final -> accept | pass |
| normal r2 5.10 -> 5.10 db5 + 5.00 db0 (inside 2%); cut to 5.00 / agreed / final -> accept; hold 5.10 -> same sheets + OTD; then final -> accept; r2 hold 5.20 -> 5.20 db5 + 5.10 | pass |
| archived replay, 42 recorded games | 0 errors |

## Odds (judgement)
Record: needs the soft round 2 (6c2813ce's text drew it once; 1 in 5 from 5.20 overall) and a 45-d limit <= 4.90: roughly 5-10%.
A new team best (> 0.727) also comes if it holds at 5.00 and then takes 4.92 / 5.02 db5. Floor on the normal branch: 0.688-0.696
if it keeps its 5.00 floor, 0.621 if it does not.
