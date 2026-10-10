STATUS: index of every cloud-session learning (tasks 1-18), 2026-10-10 ~21:00. Offline only: 0 arena sessions, no paid LLM calls.
Branch `claude/wizardly-albattani-t7jmh3` (mirrored to `cloud/p02-p08-engine`). Agent copy: `analysis/agent_variants/noidea_neel_cloud.py`
+ `central_cloud.py` (= main `noidea_neel.py` + everything below). Each line points to the file with the evidence.

# What the cloud session learned, in one page

## A. How the supplier engines work (all cases)
| # | learning | evidence |
|---:|---|---|
| 1 | Five engine types: **mirror** (P01 P02 P07 P08 P18), **holder** (P03 P11: cuts per NEW verified data kind), **floor-stop** (P04), **one-shot** (P10: final in its 1st reply), **auction** (P05) | `ENGINES.md`, `cases/*_engine.md`; classifier `engine_rules.py` (87% at thread end) |
| 2 | **The final comes at a fixed message count of ours** (89% of 353 replies; P02 4, P07 4, P08 3, P18 3, P04 3, P10 1-2); holders count holds | `FINAL_TRIGGER.md` |
| 3 | It comes one message later when the gap is < 0.35% (it counters once more to close) or when our step there is far below its own (P08 0.18-0.19x: 5 of 6) | `FINAL_TRIGGER.md`, `cases/P08_loop3.md` |
| 4 | **First counters are per-session coin flips** on P08 (5.41 / 5.53, 50/50) and P11 (46.00 / 46.50): not fixable, judge changes on 2+ games or on later rounds | `VARIANCE.md` |
| 5 | **Budget suppliers** (P08): final = first counter - a fixed budget (low draw 0.208 ± 0.008 over 8 games, high 0.26-0.29), whatever data, steps, payment term, rounds or deferral. Only the first counter matters | `cases/P08_floor.md`, `P08_loop1-3.md` |
| 6 | The first counter can be **nominal on whichever sheet it picks**: lead with the longest payment term (P08: -0.054 in value, proven; the floor follows it) | `cases/P08_round2_payment.md`, `P08_floor.md` |
| 7 | **Round-2 cut = min(cap, share x gap)**: asking lower makes round 2 bigger but leaves less for later; deep anchors also ate P08's deferral | `cases/P08_loop3.md` |
| 8 | **The final is cent-rounded on OUR payment term**: at a fixed value floor the term decides the score (P08: 5.10 @ 14 = 0.7323 vs 5.15 @ 60 = 0.7329) | `cases/P08_loop3.md` |
| 9 | Supplier cash rate from same-round primary/alternative pairs at different payment days (P08: 6.5-8.7%) | `cases/P08_round2_payment.md` |
| 10 | Read the trace reasons: the supplier's own repeated lines tell its currency (P08: "anything else on your list" 21x) - but a stated currency did not move P08's budget (cross-sell measured 0 twice) | `cases/P08_floor.md`, `P08_loop1-2.md` |

## B. Mistakes and their fixes (all ported to main unless marked)
| # | learning | evidence |
|---:|---|---|
| 11 | **Every live mistake ranked by points lost**: pushing past a final ~1.1, department remarks ~1.0, early-game data gaps ~0.95, structure hops ~0.83 ... | `MISTAKES.md` |
| 12 | **Accept only the primary sheet**: the old code picked a refused '-a' alternative at 9 of 33 archived finals -> 422 -> walk | `MISTAKES.md` L1 |
| 13 | P10: never ask a lead time below its quote ("technically unfeasible", 0.46); credible anchor at today's price | `MISTAKES.md` L2, row 12 |
| 14 | P07 / P18: 24 m, not 36 m (36 m priced higher at P07); P08 hedged: 36 m (costs us nothing, headline 5.40 once) | `MISTAKES.md` L3, `P08_loop2.md` |
| 15 | Regression fixes: RFQ closing bidder first, chargeback at the real ppm, 0.3% alternative band, mirror gate, 0.5% near-close | `REGRESSION_FIX.md` |
| 16 | No thousands separators in any e-mail; one number per claim sentence; never call another payment term an increase | `P08_offline_review.md`, `P08_loop1.md` |

## C. P08 recipe in the agent (sim `analysis/tools/sim_donautal.py`, fitted to 18 games)
90-day first sheet (+1 cent) on 36 m, clause-free; 30% round-2 step at 60 d; deferral at 0.18x; normal step; accept the final's
primary. **New (task 18, not yet live):** floor-trade pair at our 4th message after a deferral: its own clause structure one cent
under its expected final, only when that beats every final in supplier memory (low draws). P(beat 0.7323) ≈ 21% per run if its floor is
hard, ~56% if soft. Details: `cases/P08_task18.md`.

## D. Tools
`analysis/tools/engine_dump.py`, `case_engine.py`, `final_trigger.py`, `test_engine_rules.py`, `replay_cmp_cloud.py` (old vs new agent
on real supplier messages), `sim_donautal.py` (P08 replay supplier, `--validate`).

## E. Cancelled
Task 17 (P03 own-quote-by-ID plan) was cancelled by the teammate session. Its commit 8114929 is reverted on this branch (a9a2dc4) and
never reached main. The idea itself stands if P03 is played again: its own quote:7300003 (412.74, 5 Sep) is the one data kind never
cited in 15 P03 games.
