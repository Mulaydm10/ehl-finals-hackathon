STATUS: DONE (task 8) - 2026-10-10 evening, cloud session, offline only (archived games; no arena, no LLM).
Values = the supplier's price as a cash value at its standard 30 d (engine_dump.py convention: rate 6.6% P02, 6.1% P03, else
8%; P08 db0-equivalent). "As-a-deal score" = the first counter scored as if accepted (calibrated relationship charge where known).

# Variance: which first counters are coin flips, and what the current agent should expect

## (a) P08: does anything predict the mode? **No.**
| game | mode | r1 value | our body | sheets (pay d) | our claims | started* | other sessions +-2 min | its greeting |
|---|---|---:|---:|---|---|---|---:|---|
| a43d | low | 5.392 | 1367 ch | 45/14 | 3 idx | 14:22 | 3 | none |
| 1f27 | low | 5.392 | 1236 ch | 45/14 | 1 idx | 14:38 | 5 | "Many thanks ... great to hear" |
| ab47 | low | 5.392 | 1161 ch | 45/14 | 1 idx | 15:11 | 1 | none |
| cae4 | low | 5.338 | 1409 ch | 45/14/90 | fc, idx, qn | 16:23 | 2 | "Many thanks ... great to hear" |
| 586a | high | 5.512 | 1206 ch | 45/14 | 1 idx | 14:50 | 3 | "Thank you very much ... pleasure" |
| 9bfa | high | 5.512 | 1143 ch | 45/14 | 1 idx | 14:53 | 3 | "Many thanks ... great to hear" |
| 325d | high | 5.510 | 1288 ch | 45/14/30 | 1 idx | 15:05 | 3 | "Thank you very much ... pleasure" |
| 1363 | high | 5.456 | 1280 ch | 45/14/90 | fc, idx | 16:28 | 2 | "Many thanks ... great to hear" |
*session created_at, container clock. Reply delay 1 d and validity 30 d in all 8; back office "My call: counter" in all.
Body length, sheet count/order, claims, start time, parallel load, reply delay and back office do not separate the modes;
identical inputs (1f27/ab47 vs 586a/9bfa) split 2-2. The greeting is its own output and splits too. **It is drawn per session.**
One usable side fact: the headline is fixed per mode (EUR 5.41 or 5.51-5.53) **whatever payment term it picks**, so offering
90 d in round 1 (cae4, 1363 got its headline at 90 d) costs it ~0.05 in value: keep a 90-day sheet in round 1.

## (b) First counters per case (cases with >= 3 first counters)
| case | n | first-counter value range | identical inputs -> | coin flip? | spread (score pts) |
|---|---:|---|---|---|---:|
| P01 | 5 | 133.96-138.90 | 2 games same sheets, no data: 136.08 both | no | 0 |
| P02 | 19 | 368.42-370.72 | no data x5: 369.86/369.96/370.51/370.72; fc only x5: 369.03 or 369.77; **current recipe (fc + steel window + QN) x4: 368.42 all** | **yes, but not with the current recipe** | 13.7 / 9.5 / **0** |
| P03 | 14 | 427.28-429.42 | 3 groups (x3, x6, x2): identical every time | no | 0 |
| P04 | 3 | 4.877 every time | (inputs differ slightly) | no | 0 |
| P07 | 10 | 5.513-5.563 | 2 groups x3: identical | no (one 5.563 outlier with the same input as 5.523) | ~3 |
| **P08** | 8 | 5.338-5.512 | 4 games identical inputs: 5.392 x2, 5.512 x2 | **yes, 50/50** | **13.4** |
| P10 | 14 | 31.5-35.0 (set by lead time) | fc only x4: 31.9 or 32.0 | tiny | 0.8 |
| **P11** | 9 | 45.5-46.5 | current inputs x5: 46.0 x2, 46.5 x3 | **yes, ~40/60** | **8.4** |
| P18 | 10 | 5.20-5.60 | 2 groups x2: identical; values follow the data sent | no | 0 |

## (c) Expected live score per case, noidea_neel.py at 28a2791 (mean over the modes)
| case | expected | basis | best live | house |
|---|---:|---|---:|---:|
| P01 | ~0.85 | not played with this agent; deterministic counter, mirror; v2.7-v2.9 0.78-0.91 | 0.910 | ? |
| P02 | **0.85** | current recipe 2 of 2 at 0.847 (counter deterministic); 0.61 only with the contradicted QN (fixed) | 0.847 | 0.74 |
| P03 | **0.94** | 0.936 2 of 2, deterministic | 0.936 | 0.925 |
| P04 | ~0.83 | counter fixed at 4.877; final 0.81 (60 d) / 0.86 (90 d) - see P04_plan.md | 0.860 | ? |
| P05 | ~0.58 | RFQ fix ported, untested live with this agent (noidea 0.53-0.61) | 0.614 | ? |
| P07 | ~0.72 | deterministic counter; finals 0.65-0.75; untested with this agent | 0.753 | ? |
| P08 | **0.68** | low mode 0.73-0.78 / high mode 0.59-0.64, 50/50 | 0.732 | 0.752 |
| P10 | **0.69** | 4 recent games with the 31.5 counter: 0.674-0.702 | 0.702 | 0.69 |
| P11 | ~0.74 | 46.0 mode -> 0.71-0.79, 46.5 mode -> 0.71-0.77 (noidea v2.16 family mean 0.745); untested with this agent | 0.794 | ? |
| P18 | ~0.62 | counter follows the data; 0.54-0.68 in the last 4 games | 0.677 | ? |
| **mean** | **~0.75** | | **0.78** (best per case) | |

**Conclusions.** (1) Only P08 and P11 are true coin flips at round 1 (13 and 8 score points); nothing we send moves the draw, so judge
P08/P11 changes on >= 2 games or on the rounds AFTER round 1. (2) P02, P03, P04, P07 and P18 are deterministic for identical inputs:
there one live game is enough to judge a change. (3) Expected ~0.75 vs best-per-case 0.78: the gap is mostly the P08/P11 draws plus
the untested cases (P01, P05, P07, P11 with this agent) - those four need one game each.
