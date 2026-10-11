# P18 offline run H1 (2026-10-11 ~06:20, no arena session, 0 Astra calls): branch checks of `noidea_p18_coda.py`

User: "read the highest score holder's deal and just make a better deal than them. run offline 2 times and then run on the arena".

**Command** (strictly local):
    cd tacto/starter-kit && .venv/Scripts/python.exe ../../analysis/tools/p18_coda_check.py   -> coda_check.txt

## The record holder's deal and the better deal
- Codacabana 0.75595 = **EUR 4.90 @ 45 d, AS-14404 clause db0, 24 m** (C 240,350.39; live feed 2026-10-10T22:58:07Z, normal mode).
  Their other P18 deal was 5.20 @ 45 d db5: they play 45 d throughout.
- P18's negotiable terms are only price, clause (none / db0 / db3 / db5, share 0.45, base 2026-08), payment days (14-90) and
  contract months (24 = 36 m in C; 12 m buys year 2 at the 6.13 fallback). Werdenfels never accepted no clause on 24 m (21 of 21).
- Better than theirs at the SAME value to Werdenfels: **5.00 @ 45 d db5 = 0.7618** (it prices db5 at exactly +0.10, ~15 pairs, so
  it is worth 4.90 to it, like Codacabana's deal). Or **4.89 @ 45 d db0 = 0.7627** (one cent under).

## What is new vs open45 (live 2493f26f, 0.621)
- open45's new msg 1 drew the 5.40 high draw. Here **msg 1 = 6c2813ce's msg 1 byte for byte**, which drew 5.20 @ 45 d in 4 of 4
  sessions (6c2813ce, 81b5c6de, d71cab8c, aaf4f9c6): round 1 is no longer a lottery.
- **msg 2 = open45's msg 2** (6c2813ce's paragraph + forecast + "Please also quote your price with a 5% deadband", 4.84 @ 45 d db0).
  It was never sent after 6c2813ce's msg 1, so round 2 and the conversation's acceptance limit are a fresh draw from the 5.20
  state. 6c2813ce's own msg 2 leads to the known state whose 45-d limit is > 4.94 (dead end).
- msg 3 = the record sheets 5.00 @ 45 db5 + 4.89 @ 45 db0 (+0.05/+0.06 in its value over msg 2) + labour index.
- msg 4: if it cut under 5.00, hold the record sheets with a new fact (OTD); else 5.02 db5 / 4.92 db0 (0.7486 / 0.7424, both over
  our 0.727). Accept any standing offer that beats the record or scores at least our next planned sheets; final / agreed: accept.

## Checks (coda_check.txt)
| check | result |
|---|---|
| msg 1 = 6c2813ce's msg 1 byte for byte (body, sheets, refs) | pass |
| msg 2 new after that msg 1 (4 recorded games sent it; none sent this msg 2) and not 6c2813ce's msg 2 | pass |
| planned path bodies, sheets, refs (msgs 1-3 printed in full) | pass |
| first counter 5.30 / 5.40 -> msg 2 unchanged; normal r2 5.10 -> record sheets; r2 4.89 -> accept | pass |
| after msg 3: agreed db5 / db0 -> accept; counter 4.85 -> accept; final 5.00 -> accept; counter 4.90 (tie) -> hold record sheets + OTD; hold 5.00 / cut to 5.00 -> 5.02 db5 + 4.92 + OTD; after msg 4 agreed / final -> accept | pass |
| exact scores: 5.00 @ 45 db5 0.7618, 4.89 @ 45 db0 0.7627 (> record); 5.02 db5 0.7486, 4.92 0.7424 (> 0.727); fallbacks 5.00 @ 45 0.6883, 5.10 db5 0.6957 | as planned |

## Odds (judgement, not a forecast)
5.00 at round 2 came in about 1 of 5 games from 5.20; then the conversation's 45-d limit must be <= 4.90 (Codacabana's was;
6c2813ce's was > 4.94). Chance of beating the record: roughly 5% per game. Likely outcomes otherwise: 5.02 db5 / 4.92 accepted
after a hold (0.749 / 0.742, a new team best) or its final 5.00 @ 45 d (0.688).
