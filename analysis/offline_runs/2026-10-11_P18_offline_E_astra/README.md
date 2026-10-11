# P18 offline run E (2026-10-11 ~05:45, gpt-6-astra configured; no arena session): a new 45-day opening for the record

User: "try a new opening on 45 days for the record". Agent: `analysis/agent_variants/noidea_p18_open45.py`.

**Commands** (strictly local):
    cd tacto/starter-kit
    .venv/Scripts/python.exe ../../analysis/tools/p18_open45_check.py                        -> open45_check.txt
    .venv/Scripts/python.exe ../../analysis/tools/p18_replay_agents.py replay noidea_p18_open45  -> archived_replay_open45.txt

## What the repo data says (61 games; analysis/cases/P18_lever.md 24)
- **Codacabana set the record at 00:58 CEST** (live feed highlight 2026-10-10T22:58:07Z), in normal mode (the template window was
  23:51-23:58 CEST). It was not an engine-fault draw.
- **Its acceptance limit is set per conversation before our 3rd message.** 8 different msg 3s in the 0c968aae state and 4 in the
  6c2813ce state met the same limit. Measured (db0 value): 0c968aae ~4.91 @ 14 d; 6c2813ce (4.91, 4.94] @ 30 d and > 4.94 @
  45 d; a09d9536 (4.91, 4.94] @ 14 d; the 5.30/5.40-start games refused 5.04-5.05 (limits > 5.03). Codacabana's: <= 4.90 @ 45 d.
- **Low limits came only with 5.20 first and 5.00 at round 2.** Distinct 45-d openings: 5 drew 5.20, 8 drew 5.30, 2 drew 5.40.
  All 5 openings that mentioned its review of small accounts / focus on customers with volume drew 5.30.
- **Round 2:** the one clean A/B (83f89503 vs 15438619: same e-mail plus "Please also quote your price with a 5% deadband as an
  alternative") went 5.10 -> 5.00 + 5.10 db5.
- **Data kinds it takes:** only index change and price history, only in round 1 (trace reasons). Volume, labour, index and
  delivery data after round 1: "does not change our calculation". Quotes outside the case refs: "irrelevant" (7 of 7, rule 10d).
- 5.00 @ 45 d db5 is worth 4.90 db0 to it (db5 = +0.10), the same as Codacabana's deal, and scores 0.7618; 4.89 @ 45 d db0
  scores 0.7627. These are the only 45-d record sheets within 2% (nominal) of a 5.00 / 5.10 db5 offer.

## Plan (45 d throughout, 24 m)
| msg | sheets | data | why |
|---:|---|---|---|
| 1 | 4.77 @ 45 d, no clause | new cost-basis first paragraph + 6c2813ce's data block verbatim | new conversation; avoid the 5.30 wording |
| 2 | 4.84 @ 45 d db0 (0.7965) | 6c2813ce's msg-2 paragraph (drew 5.00 there) + forecast + the 5% deadband request | two features seen with 5.00 at round 2 |
| 3 | **5.00 @ 45 d db5 (0.7618) + 4.89 @ 45 d db0 (0.7627)** | labour index + "lowest price you can sign today" | record sheets; +0.05/+0.06 in its value over msg 2 |
| 4 | cut under 5.00: hold the record sheets; else 5.02 db5 (0.7486) + 4.92 db0 (0.7424) | on-time delivery 81.0% | new fact every round; never a step back |
Accept any offer that beats the record or scores at least our next planned sheets; final_offer / agreed: accept its primary.

## Checks
| check | result |
|---|---|
| msg 1 new (not any of 41 recorded msg 1s), 6c2813ce's data block verbatim, no small-accounts / volume-focus wording | pass |
| planned path bodies, sheets and refs (msgs 1-3 printed in full) | pass |
| first counter 5.30 / 5.40 -> msg 2 unchanged; normal round 2 (5.10) -> msg 3 record sheets | pass |
| after msg 3: agreed db5 / db0 -> accept; counter 4.85 -> accept; final -> accept; counter 4.90 (+ 5.00 db5 alt) -> hold the record sheets + OTD; hold 5.00 or cut 5.10 -> 5.00 -> step 5.02 db5 / 4.92 + OTD; then agreed / final -> accept | pass |
| archived replay over every recorded P18 game | 0 errors |
| Astra calls | 0 (all P18 messages are written in code) |

## Expected live outcome (judgement, not a forecast)
- First counter 5.20 about 1 in 3 (5.30 about 1 in 2), then 5.00 at round 2 about 1 in 5 from 5.20.
- The record needs this conversation's limit at <= 4.90 at 45 d. Our three soft conversations had ~4.91-4.94 at 14/30 d; Codacabana
  had <= 4.90 at 45 d. **Chance of a record: low single digits per game.**
- Otherwise: 5.02 db5 / 4.92 accepted after a hold (0.7486 / 0.7424, over our 0.727), or its final 5.00 @ 45 d (0.688).
