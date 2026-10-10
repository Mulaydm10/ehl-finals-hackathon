STATUS: DONE (P04 deep analysis, user request) - 2026-10-11 ~02:30, cloud session, offline only (0 arena sessions, no LLM calls).
Sources: all 15 P04 games (datasets/runs, tools/replays/raw and backoffice), the data package for sup:70620 / part:360020, the team's
P04 files (P04.md, P04_plan, P04_engine, P04_lever §1-7, p04_record.py, p04_last_cent.py, sim_floorstop.py), supplier memory,
GENERAL_RULES 78/84/87/88. Agent: `analysis/agent_variants/noidea_p04.py` (default = main).

# P04: 0.8737 is a proven ceiling. The board's 0.874 can be tied (we have), never beaten

## 1. The answer
| question | answer | proof |
|---|---|---|
| What is the 0.874 record? | **4.89 @ 45 d, 24 or 36 months (exact 0.8737)**. Ours is the same deal (6 games). | §2 |
| Can any team beat it? | **No.** No whole-cent deal the supplier can accept scores above 0.8737, for every cash rate its own quotes allow. | §3 |
| What would beat it? | 4.87 @ 30 d (0.940), 4.85 @ 14 d (0.990), 4.90 @ 60 d (0.982), 4.88 @ 45 d (1.0). Each needs the supplier's cash rate at **≥ 7.90 / 8.19 / 8.45 / 8.88%**. Its quotes cap it at **7.69%**. 4.93 @ 90 d is always under its floor. | §3 |
| Why did 1992e28a get only 0.700? | A path effect, not a new floor: after the 30-d detour its target stayed a hair above the floor, so 4.89 @ 45 d was refused and its final was 4.90 @ 45 d. | §5 |
| What to do | Stop P04. Keep main's 45-d path (0.8737, 6 of 6). Never hop payment terms after its first counter. Spend quota where the board can move (§7). | §7 |

## 2. The board, decoded
C_open 198,846.33, C_best 196,529.32. One cent = EUR 400 of C = 0.17 score.

| team | score | deal |
|---|---:|---|
| makeAnother.md (record) | 0.8737 | 4.89 @ 45 d (24 or 36 m) |
| **NoIdea** | **0.8737** | 4.89 @ 45 d / 36 m: 6ecd1862, ffef2938, 0cccb384, 5c8773bf, f0df0653, 24cf72ca |
| "+=" (EUR 1,994 saved) | 0.8604 | 4.94 @ 90 d = the house deal (our d3050f95, d94cb598) |

Score by price and payment term (36 m; 24 m is identical; 12 m costs 0.125, e.g. 4.89 @ 45 d = 0.749):

| payment | -2 cents | -1 cent | **its floor cent** | +1 cent |
|---|---:|---:|---:|---:|
| 14 d | 4.84 = 1.000 | 4.85 = 0.990 | **4.86 = 0.815** | 4.87 = 0.641 |
| 30 d | 4.86 = 1.000 | 4.87 = 0.940 | **4.88 = 0.766** | 4.89 = 0.592 |
| **45 d** | 4.87 = 1.000 | 4.88 = 1.000 | **4.89 = 0.874** | 4.90 = 0.700 |
| 60 d | 4.89 = 1.000 | 4.90 = 0.982 | **4.91 = 0.810** | 4.92 = 0.637 |
| 90 d | 4.92 = 1.000 | 4.93 = 1.000 | **4.94 = 0.860** | 4.95 = 0.689 |

The "floor cent" column is the cheapest cent it has ever accepted or given as its final on each term. All five are reproduced by the model in §3.

## 3. The proof
**(a) Its floor is the arena's 1.0 line.**
- Score 1.0 = C_best = the cheapest deal the supplier can accept. On P04 that is **4.935 @ 90 d** (equal cost: 4.885 @ 45, 4.865 @ 30, 4.895 @ 60, 4.845 @ 14).
- No deal in any case has ever crossed C_best. The closest is P01 ca304e36 at **EUR 0.01 above** it (score 0.9999998).
- The supplier values a deal as price x (1 - rate x (days - 30) / 360) (api.md, its standard 30 d). Its rate is below our 8%, so 90 d is the term worth most to it at our cost. Its floor is therefore **F = 4.935 x (1 - rate/6)**.

**(b) Its cash rate is pinned by its own quotes.** It prices all sheets of one message from one value target, rounding up to the cent. Every multi-sheet message of 15 games must fit one target:
- **[4.94 @ 90, 4.87 @ 14]** (5f80 r2, d305 r2) gives **rate < 7.69%**. This needs no floor assumption: it is its own pair of prices.
- 4.89 @ 45 d was agreed in 5 games (and was its final in 6ecd and bd2e), so 4.89 @ 45 must clear F, which gives **rate ≥ 7.28%**.
- **Rate 7.28-7.69%, floor F = EUR 4.8717-4.8751** (value). The same holds with round-to-nearest (7.28-7.68%).
- The fit includes every final and every refused ask (4.88 @ 45 in 5 games, 4.93 @ 90 in 3, 4.87 @ 30 and 4.90 @ 60 in 2 each, plus all the lower asks), 1992e28a included.

**(c) The cheapest cent it can accept on each term, over the whole feasible range** (every rate, both roundings):

| term | cheapest acceptable cent | score | rate the next cent down would need |
|---|---:|---:|---:|
| 14 d | 4.86 | 0.815 | 4.85: ≥ 8.19% |
| 30 d | 4.88 | 0.766 | 4.87: **≥ 7.90%** (closest: still 0.21 points above 7.69%) |
| **45 d** | **4.89** | **0.8737** | 4.88: ≥ 8.88% |
| 60 d | 4.91 | 0.810 | 4.90: ≥ 8.45% |
| 90 d | 4.94 | 0.860 | 4.93: never (4.93 < 4.935) |

**So no acceptable whole-cent deal beats 0.8737.**
- How tight 4.89 @ 45 d is: it clears the floor by only 0.004-0.26 cents of value. The supplier must concede practically all the way.
- **Only loophole: a sub-cent price.** 4.885 @ 45 d = 1.000, but api.md fixes "EUR with 2 decimals" (P04 price_unit 1). That is outside the rules; not recommended.

## 4. All 15 games
| game | path (our sheets -> its answers) | end | score |
|---|---|---|---:|
| ffef2938, 0cccb384, 5c8773bf, f0df0653, 24cf72ca | 4.83 @ 45 -> 4.90 @ 45; 4.88 @ 45 -> 4.89 @ 45; 4.89 @ 45 -> agreed | **4.89 @ 45** | **0.8737** |
| 6ecd1862 | [4.79 @ 45, 4.77 @ 30] -> 4.90 @ 45 + 4.88 @ 30; [4.82 @ 45, 4.80 @ 30] -> final 4.89 @ 45 | 4.89 @ 45 | 0.8737 |
| d3050f95 | 14/60/30 -> 4.91 @ 60 + 4.88 @ 30; 90/14/60 -> 4.94 @ 90 + 4.87 @ 14; 45/90/14 -> final 4.94 @ 90 + 4.89 @ 45 (alt, cannot be accepted by id) | 4.94 @ 90 | 0.8604 |
| d94cb598 | 4.88 @ 90 -> 4.94 @ 90; 4.93 @ 90 -> final 4.94 @ 90 | 4.94 @ 90 | 0.8604 |
| 53f2239c | [4.79 @ 14, 4.84 @ 60] -> 4.91 @ 60 + 4.87 @ 14; 4.80 @ 14 + forecast -> final 4.86 @ 14 | 4.86 @ 14 | 0.8153 |
| 5f80eb75 | 3 terms each round, final 4.91 @ 60 + 4.87 @ 14 | 4.91 @ 60 | 0.8098 |
| 6ed05f04 | [4.78 @ 30, 4.76 @ 45] -> 4.88 @ 30; [4.80 @ 30, 4.79 @ 45] -> **hold**, final 4.88 @ 30 | 4.88 @ 30 | 0.7661 |
| **1992e28a** | 4.83 @ 45 -> 4.90 @ 45; **4.87 @ 30 -> 4.88 @ 30; 4.89 @ 45 -> final 4.90 @ 45** | 4.90 @ 45 | **0.7005** |
| bd2eabf9 | as 6ecd, then 4.93 @ 90 after its final -> **walked** | - | 0 |
| 62a17f4a | [4.84 @ 90, 4.80 @ 30] -> 4.88 @ 30; probe [4.93 @ 90, 4.90 @ 60, 4.87 @ 30] -> hold; same probe -> **walked** | - | 0 |
| 21d24256 | probe (open + walk) | - | 0 |

What else the games show:
- **Back office calls:** counter / counter (/ counter) on the 0.87 paths. "hold" when its price on our term was already at the floor cent (6ed0, 62a1). walk_away after a push past its final, or a repeated probe.
- **Data:** 0 of 17 claims taken (supplier memory: shrugged 6 index, 4 price history, 7 volume). "It holds, but it does not change our calculation". The rising price path 4.29 -> 4.39 too (24cf). Its own quotes are "irrelevant".
- **Its primary is on the term of our highest-VALUE sheet.** A `-a` alternative cannot be accepted by id (422).

## 5. What 1992e28a showed (and my mistake)
- The model in §3 fits 1992e28a too (rate range unchanged). **Its floor did not move; its target did not reach it.**
  - After our 4.87 @ 30 d (a term hop, small gap) it answered 4.88 @ 30 d: its target stayed in (4.87, 4.88].
  - At our 4.89 @ 45 d its target was still above that sheet's value (by ≤ 0.1 cent), so it went final at ceil(target / 45-d factor) = 4.90.
  - On the 45-d path its target reaches the floor zone, where 4.89 @ 45 d clears.
- **Rule: on a cent-grid / floor-stop supplier, never hop payment terms after its first counter.** One hop cost one cent = 0.17 here (0.874 -> 0.700).
- **My fallback was wrong:**
  - After the refused shot it sent 4.89 @ 45 d (a second hop).
  - The open 4.88 @ 30 d (0.766) was the better choice.
  - `noidea_p04.py` now accepts the standing sheet in that spot. The shot itself is switched off for good (proven unreachable).

## 6. Every lever, checked
| # | lever | best score if it worked | status / evidence | verdict |
|---:|---|---:|---|---|
| 1 | term choice (5 payment x 3 contract lengths) | 0.8737 (45 d, 24/36 m) | §3: every other term rounds worse; 12 m costs year 2 at the fallback | in use (main, memory term choice) |
| 2 | one cent under its floor cent (4.88 @ 45, 4.87 @ 30, 4.90 @ 60, 4.85 @ 14, 4.93 @ 90) | 0.94-1.0 | needs rate ≥ 7.90-8.88%; feasible ≤ 7.69% (§3); live refusals: 4.88 @ 45 in 5 games, 4.93 @ 90 in 3, 4.87 @ 30 and 4.90 @ 60 in 2 each | impossible |
| 3 | sub-cent price (4.885 @ 45) | 1.0 | api.md: "EUR with 2 decimals" | outside the rules |
| 4 | data (index, forecast, order history, rising price path, labour) | - | 0 of 17 taken; P04 is a floor-stop, not a committee (the P03 path lever does not apply) | dead |
| 5 | its own quotes 7200019 (EUR 4.63, 20 Sep) / 7300004 (4.39 list) / 7100058 (4.42, 2025) | - | "irrelevant" (not in the case refs) | dead |
| 6 | open book (M6: "walk us through their calculation") | - | XLSX refused 3x: "company policy" | dead |
| 7 | multi-year (M2: "only multi-year volume agreements change prices") | - | 36 m in every game: it is what took 4.96 to ~4.89 | in use |
| 8 | account value (we also buy 6308, 7309 single source) | - | 5c8773bf: first counter unchanged | 0 |
| 9 | our late payments admitted + on-time promise | - | 62a17f4a: first counter unchanged (payment term is in the price anyway) | 0 |
| 10 | quality (6 QNs on this part in 12 m, EUR 900 recharged; OTD 85% vs contract 95%) | - | quality is not negotiable here; it is "reviewing small accounts" (M3/M5/M4), so a stick risks the walk | no |
| 11 | more volume ("A binding higher volume would help us") | - | volume is a fixed term (20,000) | not possible |
| 12 | rival 70640 (EUR 4.20 under its own contract to 2027-06) | - | our fallback for this volume is its 5.04 quote; claiming otherwise would mislead | no |
| 13 | deeper round-1 anchor / two-sheet tricks / steering the primary | - | its target is pinned by its floor, not our anchor; the record path already lands on the floor cent | done |

## 7. What to do
1. **P04 is finished at 0.8737 = the record.** It cannot be beaten, only tied. The board ranks by our mean over the cases, so the tie costs nothing.
2. **Keep main's P04 path** (`noidea.py`: memory term choice -> 45 d, one cent under its usual final, accept its final; 6 of 6). `noidea_p04.py` defaults to it. Never play P04 again for the record.
3. **Where the quota can still move the board:**
   - **P11** (ours 0.802 vs 0.807): a lottery on a low draw, see `P11_beat807.md`.
   - **P05:** Parth's 27e15c33 = 0.965 is above TakeTheMoneyAndRun's 0.924; check that the board shows it.
4. **General rule for the Live Final (cheap parts, 1 cent = big score):**
   - estimate its cash rate from its own two-sheet quotes;
   - steer its primary to the term whose floor cent scores best;
   - never hop terms after its first counter;
   - after a refused probe, take its standing sheet rather than hop back.

## 8. Checks
- **Fit:** `analysis/tools/p04_floor_fit.py` (`cd tacto/starter-kit && uv run python ../../analysis/tools/p04_floor_fit.py`) reproduces every §3 number. It scans rates 5-11% in 0.01% steps, both roundings, every message of the 15 games. It also reproduces the five floor cents and every refusal.
- **Agent** `noidea_p04.py`, replays vs main (`replay_cmp_cloud.py`):
  - default: **54 of 54 threads SAME** (14 P04 games incl. 1992e28a, P01, P03, P08, P11);
  - with the (disabled) shot switched on for the check only: 1992e28a turn 3 = accept the open 4.88 @ 30 d (0.766) instead of the hop that scored 0.700.
