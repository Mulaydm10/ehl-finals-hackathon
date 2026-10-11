STATUS: index of every cloud-session learning (tasks 1-21 + P03/P04/P10 deep studies + P10 draw + P03 v2 + P18 deep), updated 2026-10-11. Offline only: 0 arena sessions, no paid LLM calls.
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
| 4b | **Some "draws" are the arena's mode, not chance.** When its supplier model is off, the engine answers alone in fixed sentences ("We value our cooperation and have made a step towards you", "Any further step needs approval from our management") and prices by its own rule. All 7 sessions created 23:51-23:58 CEST on 10 Oct; 2 single replies in the other 222. P10: 31.00 in that mode vs 31.50 in 11 of 11 normal games (same e-mail: 673ee890 vs 67f3678f); P11: 46.50 in 3 of 3. Not triggerable by wording (openings are byte-identical in every session); visible in the first reply. Its approval ladder: that reply takes 2 days longer, the next e-mail draws "Our management has approved a further step" (P10 -0.30, P02 -0.54%). Judge agent changes only on normal-mode games: the 00:06 rerun kept P02 (0.828) but not P07 (0.825 -> 0.773) or P10 (0.741 -> 0.71) | `cases/P10_draw.md`, `tools/supplier_mode_scan.py` |
| 5 | **Budget suppliers** (P08): final = first counter - a fixed budget (low draw 0.208 ± 0.008 over 8 games, high 0.26-0.29), whatever data, steps, payment term, rounds or deferral. Only the first counter matters | `cases/P08_floor.md`, `P08_loop1-3.md` |
| 6 | The first counter can be **nominal on whichever sheet it picks**: lead with the longest payment term (P08: -0.054 in value, proven; the floor follows it) | `cases/P08_round2_payment.md`, `P08_floor.md` |
| 7 | **Round-2 cut = min(cap, share x gap)**: asking lower makes round 2 bigger but leaves less for later; deep anchors also ate P08's deferral | `cases/P08_loop3.md` |
| 8 | **The final is cent-rounded on OUR payment term**: at a fixed value floor the term decides the score (P08: 5.10 @ 14 = 0.7323 vs 5.15 @ 60 = 0.7329) | `cases/P08_loop3.md` |
| 9 | Supplier cash rate from same-round primary/alternative pairs at different payment days (P08: 6.5-8.7%) | `cases/P08_round2_payment.md` |
| 9b | **The first counter moves with a verified rising PRICE PATH of our own orders** (P08: "Our orders for this bar rose from EUR 5.17 to EUR 5.45 within nine months (4 PO IDs)" -> "took it into account", headline 5.41 -> 5.25, final 4.94 @ 14 = **0.912**, beat the house; teammate's d0708ed1). The flat last-8-orders run had been shrugged off 6 of 6. Next candidates: P04 (+2.3%), P03 (+3.1%) | `cases/P08_run81ee.md`; `central_cloud.rising_price_path()` |
| 9c | Round 2 on 60 d (low draw, with an opening that named "the current level" as acceptable) raised P08's floor by 0.08 (81ee 0.633): stay on 14 d; never name an acceptable price level | `cases/P08_run81ee.md` |
| 10 | Read the trace reasons: the supplier's own repeated lines tell its currency (P08: "anything else on your list" 21x) - but a stated currency did not move P08's budget (cross-sell measured 0 twice) | `cases/P08_floor.md`, `P08_loop1-2.md` |
| 10b | **Short-fuse suppliers (final at our 1st-2nd message): stack one MOVE and one NEW taken fact in the e-mail that draws its final.** Round 1: anchor at today's price (an "unrealistic" anchor ends it at once), the two strongest facts it takes, and hold the structure move back (P10: 24 m, not 36 m). Facts beyond two did not lower P10's first counter (31.50 with 2 or 3 taken), so keep spare facts for the last e-mail. Last e-mail: the move + a new taken fact + an ask well under its counter. Live P10 59c899b9 and 3c4aa1a6: 31.50 -> 31.10 (-0.40, 2 of 2), vs the move alone -0.10 to -0.30 and a fact alone -0.20. Never send shrugged kinds (P10 forecast 0 of 11) | `cases/P10_deep.md` §9, `cases/P10_draw.md` §6, `agent_variants/noidea_p10.py` |
| 10c | **A holder agrees at OUR ask when the ask is at or above its line: keep every ask at least EUR 0.60 (~0.15%) under its standing price.** P03 main v2.34-v2.34d asked 430.81 with should-cost + electronics + path in round 1 and was agreed at once, 3 of 3 (0.954; its line was ~0.26 lower). The gap also stops the near-close / accept rules from closing while unused data is left | `cases/P03_deep.md` §3, `tools/sim_selvbrunn_ladder.py` |
| 10d | **Cite a quote only when it is in the case's refs (or the case's own facts).** 7 of 7: the one quote ever "verified" was in its case refs (P01 quote:7200001, the case's alternative); all 6 outside the refs came back "irrelevant" ("does not pertain to this case"), own quotes (P03, P04 x3, P11) and a rival's (P03 quote:7100051, live 45943af6). Orders, indices, should-cost and forecasts outside the refs are verified as usual | `cases/P03_deep.md` §6, §10 |

## B. Mistakes and their fixes (all ported to main unless marked)
| # | learning | evidence |
|---:|---|---|
| 11 | **Every live mistake ranked by points lost**: pushing past a final ~1.1, department remarks ~1.0, early-game data gaps ~0.95, structure hops ~0.83 ... | `MISTAKES.md` |
| 12 | **Accept only the primary sheet**: the old code picked a refused '-a' alternative at 9 of 33 archived finals -> 422 -> walk | `MISTAKES.md` L1 |
| 13 | P10: never ask a lead time below its quote ("technically unfeasible", 0.46); credible anchor at today's price | `MISTAKES.md` L2, row 12 |
| 14 | P07 / P18: 24 m, not 36 m (36 m priced higher at P07); P08 hedged: 36 m (costs us nothing, headline 5.40 once) | `MISTAKES.md` L3, `P08_loop2.md` |
| 15 | Regression fixes: RFQ closing bidder first, chargeback at the real ppm, 0.3% alternative band, mirror gate, 0.5% near-close | `REGRESSION_FIX.md` |
| 16 | No thousands separators in any e-mail; one number per claim sentence; never call another payment term an increase | `P08_offline_review.md`, `P08_loop1.md` |

## C. P08 recipe in the agent (task 19: + round-1 price path, round 2 back on 14 d; sim 0.901 low) (sim `analysis/tools/sim_donautal.py`, fitted to 18 games)
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

## F. Since task 19 (P11, P03, P04 deep studies)
| # | learning | evidence |
|---:|---|---|
| 17 | **Decode a record from the board's EUR saved**: C_deal = C_open - saved; scan price x term for an exact C match (P03 "+=" = 431.22 @ 90 d; P04 makeAnother.md = 4.89 @ 45 d; P11 TakeTheMoneyAndRun = 44.92) | `cases/P03_lever.md`, `P04_deep.md`, `P11_beat807.md` |
| 18 | **The arena's relationship charge reveals the supplier's full cost and cash rate exactly** (P03: 395.30, 6.10%, 7 deals to the cent) | `cases/P03_lever.md` |
| 19 | **Our rising ORDER PRICE PATH is the biggest cut a committee supplier gives** (P03: 431.67 -> 430.41 in one round, live 0.9633 beats "+=" 0.944); its own quote by ID was read as a rival quote ("irrelevant") | `cases/P03_lever.md` §6 |
| 20 | **C_best = the deal at the supplier's floor**: no deal in any case ever crossed it (P01 got within EUR 0.01). So F = value of the C_best price on the term worth most to it | `cases/P04_deep.md` §3 |
| 21 | **Cent-grid ceiling proof** (P04): cash rate from its own two-sheet quotes (≤ 7.69%) + C_best floor -> no whole-cent deal above 0.8737; the record can only be tied | `tools/p04_floor_fit.py` |
| 22 | **Never hop payment terms after a floor-stop supplier's first counter** (P04 1992e28a: one hop = one cent = -0.17); after a refused probe take its standing sheet | `cases/P04_deep.md` §5 |
| 23 | P11 high draw: holding the labour index back to its first hold did not repeat 77f6's cut (0 of 2 live: 23cf3ecd, b450b035; 1 of 3 overall) | `cases/P11_lever.md` |
| 24 | **Short-fuse suppliers cut once per MOVE and once per NEW taken fact, then go final at our 2nd message: keep one move (36 m) and one unused verified fact for round 2 together.** P10: Codacabana's record 0.71 = 31.10 @ 56 d, one 10-cent step under our 31.20. Plan stacks the 36-m move with the labour index (never combined) and adds the rubber index fall in round 1. **Live 59c899b9: -0.40 stacked = 31.10 (0.710), the biggest round-2 step on P10; now rule 10b** | `cases/P10_deep.md`, `agent_variants/noidea_p10.py`, `experiments/probes/P10_G.json` |
| 25 | **P10's 31.00 (record 673ee890, 0.741) came from the engine-template window (rule 4b), not from its e-mail.** In normal mode 0.741 needs ≤ 30.69 = -0.81 in one e-mail; the best measured is -0.40, so it cannot be beaten there with known levers. Keep `noidea_p10`; its round 2 is also what the approval ladder rewards (template-mode estimate 30.40-30.60, unmeasured) | `cases/P10_draw.md` |
| 26 | **P03: "+=" retook the record at 0.97350 = 429.87 @ 90 d, set at 23:54 CEST inside the template window (rule 4b).** Normal mode is a deterministic ladder (433.08 @ 90 d minus one cut per new taken kind); every measured kind ends at 430.32-430.35 (0.9635-0.9642), 0.46-0.49 short. `noidea_p03` v2: v1's measured order, asks EUR 0.60 under its line (rule 10c), and the one kind never sent, the second source's Feb 2025 benchmark quote (quote:7100051, EUR 429.18), in the 5th e-mail. Beats "+=" only if that quote is worth >= 0.47. **Live 45943af6: 0.96394 = 430.33, as simulated to the cent; the quote was "irrelevant" (rule 10d) - P03 stopped, "+=" stands** | `cases/P03_deep.md`, `agent_variants/noidea_p03.py`, `tools/sim_selvbrunn_ladder.py` |
| 27 | **A supplier's alternatives are not its price list.** Inside one reply Werdenfels puts 0.10 between payment terms. After round 1 its cuts ignored our payment moves: from 5.20 it cut 0.20 in 2 of 11 games with a move and 1 of 3 without. 14-day and 45-day games scored the same (0.663 vs 0.658). Payment counts only through the first counter (30 d -> 5.20 in 9 of 10, 45 d -> 5.30 in 8 of 13) | `cases/P18_deep.md` sections 3-4 |
| 28 | **P18 plan to cross 0.756 (not run):** round 1 of our best game (4.76 @ 30 d), then 90 days from round 2 with asks 4.87 / 4.93 / 4.94. On 90 d any close at or under 4.94 beats, which covers all three soft-draw closes we had (4.91, 4.94, 4.94). Odds: 0.725 a game and 18% to beat if 90 d stays free; 0.67-0.68 with no beat if it is charged (a guard falls back to 30 d) | `agent_variants/noidea_p18_cross.py`, `tools/p18_cross_check.py` |
