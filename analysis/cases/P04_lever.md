STATUS: DONE (P04 deep lever analysis) - 2026-10-11 ~01:30, cloud session, offline only (0 arena sessions, no LLM calls).
Verdict: **0.874 is a hard ceiling under the arena rules: nobody can beat it unless the supplier's floor falls.** It never fell in 13 games. Agent: `analysis/agent_variants/noidea_p04.py` (`P04_SHOT`, default OFF = main).

# P04: the record is a cent-grid ceiling; one lottery ticket (4.87 @ 30 d) is all that is left

## 1. The board, decoded (C_open 198,846.33, C_best 196,529.32: EUR 23.17 = 0.01 score)
| team | score | deal |
|---|---:|---|
| **makeAnother.md (record)** | **0.8737** | **4.89 @ 45 d, 24 or 36 m** (C 196,822.00) |
| NoIdea (us) | 0.8737 | the same, 6 times (main noidea.py 5 of 5) |
| "+=" (EUR 1,994 saved) | 0.8604 | 4.94 @ 90 d = the house deal |

Negotiable are only price, payment (14 / 30 / 45 / 60 / 90 d) and contract (12 / 24 / 36 m). Lead time, volume (20,000), DAP, start date and tooling are fixed.

**The score depends on (price cent, payment term) only:**
- 24 m = 36 m;
- 12 m costs 0.125 (year 2 at the fallback);
- the only other cost item is quality (EUR 570), which is not negotiable.

| price (36 m) | 14 d | 30 d | 45 d | 60 d | 90 d |
|---|---:|---:|---:|---:|---:|
| its final (live) | 4.86 = 0.815 | 4.88 = 0.766 | **4.89 = 0.874** | 4.91 = 0.810 | 4.94 = 0.860 |
| one cent under | 4.85 = 0.990 | **4.87 = 0.940** | 4.88 = 1.000 | 4.90 = 0.982 | 4.93 = 1.000 |

**One cent is 0.17 score** (EUR 400). Prices are whole cents (api.md), so the cent grid decides everything.

## 2. The supplier, fitted on every game
- It accepts any sheet whose value to it is ≥ S, where value = price x (1 - r x (days - 30) / 360). It quotes its floor rounded UP to the cent on the term of our highest-value sheet.
- Fit: all 5 distinct finals (4.86 @ 14, 4.88 @ 30, 4.89 @ 45, 4.91 @ 60, 4.94 @ 90) and all 9 refused asks (4.88 @ 45 x5, 4.93 @ 90 x2, 4.90 @ 60, 4.87 @ 30).
  - **Floor S in (4.8701, 4.8753], cash rate r = 6.8-8.4%.** 562 (S, r) pairs fit everything.
  - The same S explains every game: **its floor is fixed, not drawn per session** (unlike P11's).
- **Over all 562 pairs the best deal it can accept is 4.89 @ 45 d = 0.8737.** Every other term rounds worse.
- So the ceiling is proven for any team, as long as S stays where it is. The board agrees: 16 teams beat the house, and none is above 0.874.

## 3. Everything that could lower S, and what it did
| lever | what happened | verdict |
|---|---|---|
| index data (PPI-C2815, LCI-C), forecast +4.2%, order prices | "it holds, but it does not change our calculation" (every time); rising indices "confirm our case" | dead |
| **rising order PRICE PATH 4.29 -> 4.39** (the P03 lever: -1.26 there) | 24cf72ca: "We checked the price history data you cited; it holds, but it does not change our calculation"; first counter 4.90 @ 45 as always | dead on P04 (a floor-stop, not a committee) |
| its own quotes 7200019 (4.63) / 7300004 (4.39 list) | "irrelevant" (not in the case refs) | dead |
| open book / cost breakdown (M6) | asked 3 times: "company policy: we do not share detailed internal cost calculations" | dead |
| late-payment admission + on-time promise | 62a17f4a: first counter 4.88 @ 30, same as without | dead |
| account value line, 36 m commitment (M2) | first counter unchanged; 36 m already in every game | in use / 0 |
| "A binding higher volume would help us" | volume is a fixed term (20,000) | not possible |
| asks a cent under its floor | 4.88 @ 45 x5, 4.93 @ 90 x2, 4.90 @ 60 x1, 4.87 @ 30 x1: all refused; resending the same probe made it **walk** (62a17f4a) | its floor is hard |
| sub-cent price (e.g. 4.885) | api.md: EUR with 2 decimals | outside the spec |

## 4. The only remaining ticket: 4.87 @ 30 d
How far the floor would have to fall for each one-cent-under ask (over the 562 fitted pairs):

| ask | score if agreed | floor fall needed (median / max) | fallback if refused |
|---|---:|---|---:|
| **4.87 @ 30 d** | 0.940 | **0.05% / 0.11%** | 4.88 @ 30 = 0.766, or our 3rd message 4.89 @ 45 = 0.874 if it stays open |
| 4.90 @ 60 d | 0.982 | 0.07% / 0.13% | 4.91 @ 60 = 0.810 |
| 4.93 @ 90 d | 1.000 | 0.10% / 0.20% | 4.94 @ 90 = 0.860 |
| 4.85 @ 14 d | 0.990 | 0.12% / 0.21% | 4.86 @ 14 = 0.815 |
| 4.88 @ 45 d (main's memory close) | 1.000 | 0.16% / 0.20% | 4.89 @ 45 = 0.874 |

- 4.87 @ 30 d is the closest to its floor. It was refused once (62a17f4a, as one of three sheets), so it works only if something lowers the floor in that session.
- **Honest chance: a few %.** Only the best practice score per case counts, so a miss costs one session of quota, not score.

## 5. Agent `noidea_p04.py` (subclass of main noidea.py; gate `case:P04`; switch `P04_SHOT`)
- `P04_SHOT = False` (default): main exactly (0.874, 5 of 5).
- `P04_SHOT = True`:

  | message | what it sends | if... |
  |---|---|---|
  | 1 | as main (4.83 @ 45 d / 36 m -> its 4.90 @ 45) | - |
  | 2 | **4.87 @ 30 d alone**, no new data | agreed -> **0.940** |
  | 3 | 4.89 @ 45 d alone, only if its reply was still open | it agrees -> **0.874** |
  | - | if its reply was final_offer: main accepts its primary | 4.88 @ 30 = 0.766 (the board keeps 0.874) |

**Replays** (`replay_cmp_cloud.py`, main -> noidea_p04):
- With the shot ON (13 P04 games):
  - turn 1 is SAME in all 13;
  - turn 2 = [4.87 @ 30] in all 13;
  - turn 3 = [4.89 @ 45] in the 3 games that stayed open (5f80, 62a1, d305).
- With the shot OFF (default): 47 of 47 threads SAME (P04 13, P01, P03, P08).

## 6. Recommendation
1. **Do not expect to beat 0.874 on P04.** The rules make it a tie at best; our 0.874 already equals the record.
2. If the team wants the one free lottery ticket: play ONE game with `P04_SHOT = True`.
3. Then stop: a second refusal of 4.87 @ 30 d confirms the floor is fixed for good.
4. **Better use of quota: cases where a data kind still cuts.** P03's order price path was the lever (0.963). Next, check every committee / holder supplier for a rising order path we never sent.
