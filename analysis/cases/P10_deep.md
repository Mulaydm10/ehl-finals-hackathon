STATUS: DONE (P10 deep analysis, user request) - 2026-10-11 ~03:45, cloud session, offline only (0 arena sessions, no LLM calls).
Sources: all 18 P10 games (datasets/runs, tools/replays/raw and backoffice), the P10 data package (dossier, 4 letters, contract,
facts), the team's P10 files (P10.md, P10_engine.md, probes P10_A-F + findings), supplier memory, claim reactions.
Ready to run: `analysis/experiments/probes/P10_G.json` (scripted, `tools/experiments/probe.py`) and
`analysis/agent_variants/noidea_p10.py` (agent, gate case:P10).

# P10: Codacabana's 0.71 is 31.10 @ 56 d. We beat it by stacking cuts the supplier gives but no game ever combined

## 1. The answer
| question | answer |
|---|---|
| Their deal | **EUR 31.10 @ 56 d lead, 23,400 a year, 24 or 36 months = 0.7097** (EUR 428,374 saved: an exact match, nothing else fits) |
| Ours | 31.20, same structure = 0.7019 (Parth's probe B, 991ff7c4): **one 10-cent grid step** behind |
| What beats it | **≤ EUR 31.09 @ 56 d** (0.7105); 31.00 = 0.718, 30.90 = 0.725, 30.80 = 0.733 |
| Why it is reachable | the supplier gives one cut per **move** (the 36-month extension: -0.10 to -0.30) and one per **new verified fact** it takes (should-cost, price path, labour index: about -0.20 each). No game ever put the 36-month move and a new fact in the same round, and main gives the 36 months away in round 1 |
| The plan | round 1 = probe B + the rubber index fall as a third fact; round 2 = 36 months + the labour index, ask EUR 1.10 under its counter; accept its final |
| Expected | 30.80-31.00 (0.718-0.733) if the cuts add up; 31.20 (0.702, = probe B) if they don't |

## 2. The board, decoded (C_open 1,932,492.18; C_best 1,328,926.89; one cent @ 56 d = EUR 471 = 0.00078)
| team | EUR saved | score | deal (exact C match) |
|---|---:|---:|---|
| **Codacabana (record)** | 428,374 | **0.7097** | **31.10 @ 56 d**, 23,400, 24/36 m |
| NoIdea (991ff7c4) | 423,663 | 0.7019 | 31.20 @ 56 d, 36 m |
| NightHunter | 418,951 | 0.6941 | 31.30 @ 56 d |
| Codacabana / Piloty (earlier) | 414,240 | 0.6863 | 31.40 @ 56 d (= the house) |

Every team sits on the same structure (lead 56, 23,400, 24-36 m), one 10-cent step apart.
- Lead 42 would need ≤ 31.80 (the supplier quotes 33.80-34.00 there).
- Volume below 22,230 breaks the must-have (score 0).
- 12 months scores 0.11.

## 3. How Ravensteiner prices (18 games)
| mechanic | evidence |
|---|---|
| **Structure sets the base**: 35.00 @ 35 d, 33.80-34.00 @ 42 d, 31.50-32.00 @ 56 d | 675f, afd9, 2d91 (42 d) vs all 56-d games |
| **Round-1 counter = base minus about 0.20 per taken fact**: 32.00 (forecast only, shrugged), 31.70 (should-cost), **31.50 (should-cost + price path)** | 396a/b9e6, 5acf/7e8b, 991f/a2e3/7a92/e61c/0b29 |
| **An "unrealistic" anchor ends it at once** (27.38 / 27.69 = the C_best price): final in round 1 | 10 of 10 such games |
| **An ask at or above its counter is agreed at our price** | probe A: 31.56 agreed; after "agreed" it never moves ("Our agreed offer stands") |
| **It goes final at our 2nd message** (7 of 7 open games) | final_at_2: 7 |
| **Round-2 cut, one per move or new fact**: 36 m alone -0.30 (991f) / -0.20 (a2e3, 7a92) / -0.10 (e61c, 0b29); labour index alone -0.20 (53ba: "Reflecting the minor index change") | see §4 |
| **A round-2 e-mail without data draws "Which figures is that based on? Please send us the data"** | 991f, a2e3, e61c: all finals |
| Prices on a 10-cent grid; no relationship charge in any deal (its margin stays above 10%) | all results |
| **Its floor is far away**: score 1.0 = 27.385 @ 56 d (C_best). The limit is its concession rhythm, not its cost | C_best price |

## 4. All 18 games
| game | round 1 (ask, structure, data) | its answer | round 2 | its final | score |
|---|---|---|---|---|---:|
| **991ff7c4** (probe B) | 29.89, 24 m, path + should-cost | open 31.50 | **36 m move, no data**, 30.40 | 31.20 | **0.702** |
| a2e38ea8 (F) | 30.50, 24 m, path + should-cost | open 31.50 | 36 m, 30.75 | 31.30 | 0.694 |
| 7a9294b8 (C) | 29.89, 24 m, path + should-cost | open 31.50 | 36 m + ppm (shrugged), 30.90 | 31.30 | 0.694 |
| 53bab007 (agent) | 29.57, **36 m**, path + should-cost + forecast | open 31.50 | **labour index**, 30.11 | 31.30 | 0.694 |
| e61c2818 / 0b29bc23 (D/E) | 28.94, 24 m, path + should-cost (+ppm) | open 31.50 | 36 m, 29.09 / 29.79 | 31.40 | 0.686 |
| c283f47d (agent) | 29.57, 36 m, flat history + should-cost + forecast | open 31.70 | labour index, 30.18 | 31.50 | 0.679 |
| e479da11 (A) | 31.56, 24 m, path + should-cost | **agreed 31.56** | re-asks 30.93 / 30.31 / 29.89 | "agreed offer stands" | 0.674 |
| 5acf9fdd, 7e8bb04a | 27.38, 36 m, should-cost + forecast | final 31.70 | - | - | 0.663 |
| f0a505fc, 0bba4ffd | 27.38, forecast | final 31.90 | - | - | 0.647 |
| 2d91214c | 27.69 @ 42 d, cost + forecast + sc | final 33.80 @ 42 d + alternative 31.90 @ 54 d | 31.90 @ 56 d sent back | agreed 31.90 | 0.647 |
| 396a494d, 582e0e73, b9e67662 | 27.38, 36 m, forecast | final 32.00 | - | - | 0.640 |
| afd996e3 | 27.69 @ 42 d | final 34.00 @ 42 | - | - | 0.539 |
| 675fc6b9 | 27.69 @ 35 d + cost + 2 indices | final 35.00 @ 35 | - | - | 0.461 |
| 03968142 | probe (open + walk) | - | - | - | 0 |

## 5. What it takes and what it shrugs (claim reactions over all games)
| kind | reaction | count | where it goes |
|---|---|---:|---|
| should-cost (cost:340010, EUR 24.31) | "it holds and we took it into account" | 12 of 12 | round 1 |
| order **price path** 28.94 -> 29.89 (3 POs) | taken | 7 of 8 (the one shrug was the flat run) | round 1 |
| labour index LCI-C -0.3% (2025-10 -> 2026-01) | taken: "Reflecting the minor index change" -0.20 | 2 of 2 (round 2) | **round 2, with the 36 m move** |
| rubber index PPI-C2219 -0.3% (2026-01 -> 2026-02, -0.25%) | **never sent**. Same kind and size as the labour fall; main builds it but never reached it | 0 | **round 1, third claim** |
| forecast fc +10.1% | "does not change our calculation" | 11 of 11 | never (main still sends it in round 1) |
| scorecard OTD / ppm | does not change | 1 + 1 | never |
| 7 QNs on this part in 12 months | never sent; quality record shrugged; may dilute | 0 | not used |

## 6. Every lever
| # | lever | best score if it works | evidence | verdict |
|---:|---|---:|---|---|
| 1 | **hold the 36-month move for round 2** (24 m in round 1) | part of the 0.30 step | 991f (-0.30) vs main's 36 m in round 1 (no move left) | **in the plan** |
| 2 | **a new taken fact in the same round-2 e-mail** (labour index) | -0.20 more | 53ba / c283: taken in round 2; never combined with the move | **in the plan** |
| 3 | **a third taken fact in round 1** (rubber index fall) | -0.20 off the counter | same kind as labour; one index claim per e-mail kept | **in the plan** |
| 4 | round-2 ask EUR 1.10 under its counter | best step seen (0.30) | 991f 30.40 vs 30.75 / 30.90 (0.20) / 29.09-29.79 (0.10) | in the plan |
| 5 | anchor = the price we pay (29.89) | keeps it open | 27.38 / 27.69 "unrealistic" -> final at once | in the plan |
| 6 | lead 42 / 35 | ≤ 0.70 | it prices 42 d about EUR 2.30 higher (> our EUR 0.72 late cost) | no |
| 7 | a third round | +1 more cut | final at msg 2 in 7 of 7; the plan's 3rd e-mail is ready if it stays open | bonus |
| 8 | ask at or above its counter (probe A) | 0.674 | agreed at our price, then frozen | no |
| 9 | approval ladder (moves within 2%) | - | 7a92 asked 30.90 (-1.9% of 31.50): countered 31.30, no KAM agreement | no |
| 10 | forecast / OTD / ppm / QNs | 0 | shrugged; a shrugged claim next to the move coincided with a smaller step (7a92) | left out |
| 11 | volume, payment | - | 23,400 is the only must-have-safe volume; payment fixed 30 d | n/a |

## 7. The experiment
**Scripted:** `uv run python ../../tools/experiments/probe.py ../../analysis/experiments/probes/P10_G.json`. **Agent:** `analysis/agent_variants/noidea_p10.py` (same plan; round 2 ask computed from its counter).

| our msg | sheet (all 23,400 / lead 56) | data | expected answer |
|---:|---|---|---|
| 1 | **29.89, 24 m** (the price paid since 2024) | price path (3 POs), should-cost 24.31, **rubber index -0.3%** | open **31.30-31.50** |
| 2 | **36 m**, ask = its counter - 1.10 (30.40 if 31.50) | **labour index -0.3%** | final **30.80-31.20** |
| 3 | (scripted: 30.80, if it is still open) | - | final |
| - | accept its final (agent: main's rule) | | |

| outcome | price | score | vs record 0.7097 |
|---|---:|---:|---|
| everything adds up (-0.20 rubber, -0.30 move, -0.20 labour) | 30.80 | 0.733 | **beats** |
| rubber shrugged, round 2 adds up | 31.00 | 0.718 | **beats** |
| round 2 gives one step only (0.30) | 31.20 / 31.00 | 0.702 / 0.718 | tie-break on rubber |
| like probe C (0.20) | 31.30 | 0.694 | no |

**Decision rule:**
- **Round 1 at 31.30:** the rubber index was taken. Keep it, and add "one taken fact per round" to main.
- **Round 2 ≥ 0.40 below its counter:** the move and the fact stack. This is the general rule for short-fuse suppliers.
- **31.20 or above:** the step is capped. P10 then needs a third round, which this supplier has never given.

## 8. Checks
- **Cost model** (arena_kit, standard ppm 300) reproduces 991ff7c4 to the cent (C 1,508,829.60). The four board figures match exactly one structure each (§2).
- **Replays** (`replay_cmp_cloud.py`, main -> noidea_p10), 18 P10 games:
  - turn 1 = 29.89 / 24 m + price path + should-cost + rubber index in all games (main: 29.57 / 36 m + forecast);
  - on 991ff7c4's real counter, turn 2 = 30.40 / 36 m + labour index;
  - turn 3 accepts its final.
- **Other cases:** P01, P03, P04, P08, P11, P18 (49 threads) all SAME.
- The probe JSON's figures are the facts.json values: PPI-C2219 118.9 -> 118.6 = -0.25%; LCI-C 117.6 -> 117.3 = -0.26%; written "-0.3%" (the labour version was verified twice live).

## 9. Live results (local, 2026-10-11 00:05-00:19; record by then = Dhruv v2.34b hidden 673ee890 **0.741 = 30.70 @ 56 d / 36 m**)
| game | agent | round 1 -> its counter | round 2 -> its final | score |
|---|---|---|---|---:|
| 673ee890 (Dhruv) | main v2.34b hidden | 29.57 / 36 m + should-cost + path + OTD + committee sentence -> **31.00** | forecast (shrugged) -> "management approved a further step" **30.70** | **0.741** |
| a9e2c0e4 | noidea_p10b v1 | same, rubber idx instead of OTD -> 31.50 | labour idx -> 31.30 | 0.694 |
| 67f3678f | noidea_p10b v2 | **identical to 673e** (should-cost + path + OTD + committee) -> **31.50** | labour idx -> 31.30 | 0.694 |
| **59c899b9** | **noidea_p10 (this plan)** | 29.89 / 24 m + path + should-cost + rubber idx (all verified) -> 31.50 | **36 m move + labour idx, ask 30.40 -> final 31.10 (-0.40)** | **0.710** |
- **The round-1 counter is a per-session draw:** the same e-mail drew 31.00 once (673e) and 31.50 in 67f3; 31.50 in 10 of 11 games
  with should-cost + price path.
- **Stacking works:** the 36-month move + a taken fact in the same round-2 e-mail cut 0.40 (31.50 -> 31.10), the biggest
  round-2 step on P10 (the move alone 0.10-0.30, labour alone 0.20).
- **To beat 0.741:** this plan's round 2 on a low draw (31.00 -> ~30.60 = ~0.75) - the draw is the lottery (~1 in 10).
