STATUS: DONE (task 15) - P08 loop, report 2 - 2026-10-10 evening, cloud session, offline only (0 arena sessions, no LLM calls).
Run: 94e77b7b71359f60 = 0.721, low draw, main 078e9a5 (36-month sheets). Every e-mail, claim and trace reason read.

# Loop run 2: 36 m answered one cent lower; no other cost; the record is now a coin we can win by luck

## 1. Mistakes report, e-mail by e-mail

| msg | ours | its reply (value) | trace reasons | mistake? | cost |
|---:|---|---|---|---|---:|
| 1 | 4.79 @ 90 / 4.73 @ 45 / 4.70 @ 14, **36 m**, clause-free; own quote; cross-sell; forecast +1.9%; PPI-C2431 -2.3% | **5.40 @ 90** db0 **36 m** = 5.328 (24 m low draws: 5.41 x5, 5.42 x1) | "**For a 36-month contract**, we must include the AS-14404 index clause ... in exchange for this and the 14-day payment term, we can offer €…"; "**We appreciate the prospect of quoting for the additional sheet volume**" (cross-sell acknowledged for the first time); index "took it into account"; XLSX refused | none. It accepted 36 m and answered 1 cent lower | 0 |
| 2 | 4.88 @ 14, 36 m (30% step), LCI-C | 5.21 @ 14 = 5.229 (-0.099) | LCI-C "factored it into our calculation"; "a 36-month contract requires the AS-14404 index clause" | none. The model-written opening no longer misreads its sheet (prompt rule) | 0 |
| 3 | 4.90 (0.18x), 7 QNs | 5.16 @ 14 = 5.178 open (-0.050), **deferral 5 of 5** | QNs "do not impact our current cost structure" | none | 0 |
| 4 | 4.98 (normal step), order history | **final 5.11 @ 14 = 5.128** (-0.050) | order history "does not impact our current pricing" | none | 0 |
| close | accepted its primary | 5.11 @ 14, db0, **36 m** = 0.721 | - | correct; 36 m scores the same as 24 m | - |

- Total cut **-0.200** (5.328 -> 5.128): the same budget.
- What 36 m drew in its text: only the clause requirement restated ("a 36-month contract requires the AS-14404 index clause"). No premium, no objection, no hold.

## 2. Is 36 m worth keeping? Yes

- **The headline.** 5.40 against 5.41 / 5.41 / 5.41 / 5.41 / 5.41 / 5.42 on all 6 earlier low draws (24 m). One sample, but not seen once in 6 tries
  at 24 m. It costs us nothing (24 and 36 m score the same at equal price).
- **Why one cent matters: it moves the record into reach.** The final nominal price is cent-rounded. The record 0.7323 is 5.10 @ 14; anything
  above it needs **5.09 @ 14**, i.e. a final value < 5.113.

| round-1 headline (low draw) | needs budget > | P(beat record 0.732) | P(beat house 0.752: 5.08 @ 14) |
|---|---:|---:|---:|
| 5.42 @ 90 | 0.235 | 0.1% | 0% |
| 5.41 @ 90 (24 m) | 0.225 | **2.5%** (0 of 7 empirical budgets) | 0.1% |
| **5.40 @ 90 (36 m)** | 0.215 | **21%** (2 of 7 empirical budgets: 0.217, 0.220) | 2.4% |

Budget = 0.208 ± 0.0086 (7 low draws: 0.217, 0.200, 0.199, 0.210, 0.200, 0.210, 0.220). Normal model, 200k draws, cent rounding as the supplier does it.
Data accepted does not explain the spread (a43d: 0 facts accepted, 0.199; cae4: 2, 0.220), so the budget behaves like noise.

**Luck has a real chance:** a pure re-run of the current agent beats 0.732 in about **21% of low draws**, so **~10% per game** (the draw
is ~50/50; a high draw cannot beat it). Beating the house by luck: ~2.4% of low draws, ~1% per game.

## 3. Next lever, by expected value

| lever | gain if it works | evidence of its sign | risk | EV per game |
|---|---|---|---|---|
| **re-run the current agent (36 m kept)** | record in ~21% of low draws | measured (budget spread) | none | **P(record) ~10%**; mean 0.72 low / 0.665 high |
| deeper round-1 anchor (`DEEP_ANCHOR_HEDGED`, e.g. 0.26; all 14 games used ~0.22) | if its first counter follows our anchor the way mirror steps do (pooled fit: 0.08 of the extra gap): ~-0.02 value = +0.02 score, which lifts P(record) to ~60% | **unknown**: P02 / P08 first counters never followed inputs; P10's first answer got WORSE with a deep anchor (rule 52) | a hold or walk is not seen in P08 at 22%, but P05 walked at a 20% market gap | ~0 ± 0.02 |
| ask the floor / hair-below | ≤ 0.01 (its floor is reached at msg 3-4 anyway; P11's named floor = real floor) | P11 | a hair ask needs its clause structure | ~0 |
| cross-sell | 0 (measured twice, acknowledged in run 2) | measured | none | 0 (kept) |
| 12 m, deadband, payment term, data mix, step pattern | 0 / negative (P08_floor.md) | measured | - | 0 |

**Recommendation: re-run unchanged (36 m on).** No untested lever has a known positive sign. Each re-run is a ~10% shot at the record
(21% on a low draw) at no cost. If the loop prefers information over luck, flip `DEEP_ANCHOR_HEDGED = 0.26` for one run: it is the only
round-1 lever left, the round-1 headline settles it at once, and it is reverted if the headline is above 5.40.

## 4. In the code / checks
- `noidea_neel_cloud.py` (from main after run 2, db1c6de): unchanged behaviour; the new switch `DEEP_ANCHOR_HEDGED = None` is OFF.
- **Replays vs main:** SAME in all 77 threads (P01-P05, P07, P08 incl. 94e77b7b, P10, P11, P18).
- **sim_donautal:** budget 0.208, 36-month shift 0.01. `--validate` over 50 replies: median |diff| 0.010. Agent run: low 0.7323 (5.10 @ 14 = the record exactly), high 0.665.

**Conclusions.**
1. Run 2 lost nothing. 36 m was accepted at 5.40 (one cent below every 24-month low draw) and is kept.
2. That cent makes the record reachable by luck: P(beat 0.732) = 21% per low draw (~10% per game), against 2.5% at 24 m. Beating the house needs a real floor lever (~1% by luck).
3. Next: re-run as is; optional one-run test of the deeper anchor (switch ready, off).
