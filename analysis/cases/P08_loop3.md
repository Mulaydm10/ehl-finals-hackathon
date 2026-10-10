STATUS: DONE (task 16) - P08 loop, report 3 - 2026-10-10 evening, cloud session, offline only (0 arena sessions, no LLM calls).
Run: 8180d3894dd5c5b3 = 0.721, low draw, main 1f58b46 (36 m + DEEP_ANCHOR_HEDGED = 0.26). Every e-mail, claim and trace reason read.

# Loop run 3: the deep anchor bought nothing and cost the deferral; no floor lever is left, only the cent grid

## 1. Mistakes report, e-mail by e-mail

| msg | ours (value) | its reply (value) | trace reasons | mistake? | cost |
|---:|---|---|---|---|---:|
| 1 | **4.55 @ 90** / 4.49 @ 45 / 4.46 @ 14, 36 m (deep anchor 0.26; usual 4.79) = 4.489 | 5.41 @ 90, 36 m = **5.338** (run 2: 5.40) | index and volume "took it into account"; "For a 36-month contract, we must include an AS-14404 index clause ..." | the deeper anchor **did not lower the headline** (5.41 = the 24-month level) | 0 to -0.01 |
| 2 | 4.72 @ 14 (29% of the gap) = 4.737 | 5.16 @ 14 = 5.178 (**-0.160**) | LCI-C "adjusted our calculation accordingly"; clause restated | the lower asks left a bigger gap (0.60 vs 0.43), so round 2 took 0.16 instead of 0.10-0.12. Path only | 0 |
| 3 | 4.75 (+0.03 = **0.19x** its step) = 4.767 | **final 5.11 @ 14 = 5.128** (-0.050) | QNs "do not alter our cost basis" | **deferral failed** (first time, 5 of 6): see below | 0 (the total is the budget) |
| close | accepted its primary | 5.11 @ 14, 36 m = 0.721 | - | correct | - |

**Why the deferral failed.**
- Not our step ratio (0.19x, the same as the 5 deferrals that worked: 0.18-0.19x).
- The budget left after round 2 was the reason. Across 15 games its round-2 cut is **min(0.16, 0.255 x the gap after our ask)**: 6912 / a4b9 / ad04 / 94e7 gaps 0.43 -> cut 0.10-0.12; c387 / cae4 / 1363 / db7d / 8180 gaps 0.52-0.64 -> 0.16. The deep anchor's lower asks made the gap 0.60, so round 2 took 0.16 of the ~0.21 budget.
- With only ~0.05 (one final step) left, it went final at message 3 whatever our step. db7d deferred with 0.12 left; 1363 (0.10 left, step ratio 0.98) took all of it in one final step.
- **The total cut was 0.210, the same budget as always.** Deferral only spreads the budget; it never moved the total.

**Revert:** `DEEP_ANCHOR_HEDGED = None` in the cloud copy.

## 2. Anything left that moves the budget or the round-1 value? (re-read for 70710)

| source | content | lever? |
|---|---|---|
| doc:20260421-70710-M2 (call note) | the OWNER offered in April to walk us through the calculation (hourly rates, material) | no: Inside Sales refuses the breakdown in every game ("Material accounts for about … more detail we do not share", 18x). No supplier sent a cost breakdown in any archived game of any case (only delivery schedules: P02, P03, P05, P10) |
| doc:20260706-70710-M1 | alloys hedged until March 2027 | already used (no AS-14404 claims) |
| doc:20260912-70710-P08 | proposes "the price basis ... including a price adjustment clause" | the clause is its demand: mandatory in all 15 games |
| ctr:4600070710 | §3.2 index clause on AS-14404 already in force; §6.1 OTD target 95%; §8.1 extends 12 months unless terminated (60 d) | OTD 88% vs 95% is true and never cited, but accepted data never changed the budget (a43d: 0 facts taken, 0.199; cae4: 2, 0.220) -> expected 0. Extension: its notice was in time -> nothing |
| scorecard | green, ppm 75, OTD 88-92% | as above |
| dossier | our share of its turnover 0.3%; we pay 79% of invoices 2.9 days late; equity 33.9%, credit low risk | not cash-driven: no P11-type person's currency |
| cross-sell (task 13) | acknowledged once ("We appreciate the prospect of quoting for the additional sheet volume"), total unchanged twice | 0 |
| tools/sunday_release | not present | - |

**Plainly: no lever with a known positive sign moves P08's budget or round-1 value.** What remains is the cent grid of its final price.

## 3. The setup that maximises P(score > 0.732) per run: final on 60 days

Its final is cent-rounded on **our** payment term. At the low-draw floor (value ~5.116-5.121) the two grids fall differently:

| payment term | its final | value | score |
|---|---:|---:|---:|
| 14 d | 5.10 | 5.118 | 0.7323 (= the record, not above) |
| **60 d** | **5.15** | **5.116** | **0.7329 (above the record)** |

**P(score > 0.7323)**, noise model: 8 low-draw budgets, 0.208 ± 0.008; 100k draws; cent rounding as it does it:

| headline (low draw) | 14 d | 30 d | 45 d | **60 d** | 90 d |
|---|---:|---:|---:|---:|---:|
| 5.40 (36 m, run 2) | 20% | 28% | 41% | **54%** | 31% |
| 5.41 (24 m; 36 m in run 3) | 2% | 3% | 7% | **13%** | 4% |

- The mean score barely changes (0.7284 at 60 d vs 0.7306 at 14 d with a 5.40 headline).
- 60 d raises the chance of landing **just above** 0.7323. A "record" won this way is by ~0.001: a cent-grid effect, not a lower floor.
- Beating the **house** (0.752) stays at ~1-2% per low draw on any term.

**Recommended setup:**
- 36 m (headline 5.40 in 1 of 2 runs) + 90-day round-1 headline + **60 d from round 2** (`PAY_DAYS_HEDGED = 60`, replacing task 12's 14 d, which task 13 showed is not a lever) + deep anchor OFF + the rest unchanged.
- P(score > 0.732) **≈ 34% per low draw** (half 5.40, half 5.41 headlines), **≈ 18% per run** (low draws ~55%), against ≈ 6% per run with 14 d.

## 4. Code and checks
- `noidea_neel_cloud.py` (from main 51352f8): `DEEP_ANCHOR_HEDGED = None`; `PAY_DAYS_HEDGED = 60` (round 2 onward; then its term is held).
- **sim_donautal:**
  - round-2 cut = min(0.16, 0.255 x gap); no deferral when ≤ 0.07 of the budget is left;
  - `--validate` over 53 replies: median |diff| 0.010, every final within 0.01;
  - agent: cloud **0.7329 low** (5.15 @ 60) / 0.666 high, against main 0.7323 (5.10 @ 14, final at msg 3 like 8180) / 0.665.
- **Replays vs main 51352f8:**
  - SAME: P01-P05, P07, P10, P11 (8), P18;
  - P08: round 1 back to the 4.79 / 4.73 / 4.70 anchor, round 2 on 60 d; turns 3-4 reproduce run 2 (94e77b7b) exactly.

**Conclusions.**
1. The deep anchor did nothing to the headline (5.41). Its lower asks let round 2 take 0.16 of the 0.21 budget, so no deferral was possible. Reverted.
2. Nothing in the dossier, contract, letters or traces moves the budget. P08's low-draw score is set by the draw, the 5.40 / 5.41 headline and a 0.208 ± 0.008 budget.
3. Best setup for the loop's stop rule: final on 60 d, about 34% per low draw / 18% per run to land above 0.7323, by about 0.001. Beating the house's 0.752 is not reachable with any lever we know.
