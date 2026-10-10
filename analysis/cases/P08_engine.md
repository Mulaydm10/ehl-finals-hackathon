STATUS: DONE (task 2, P08) - 2026-10-10 ~18:15 CEST, cloud session, offline only (0 arena sessions)
Data: all 7 P08 sessions (6 played + the probe; datasets/runs, tools/replays/raw, tools/replays/backoffice). total_cost reproduces all 5 deals to the cent.
Tool: `cd tacto/starter-kit && uv run python ../../analysis/tools/engine_dump.py P08 --rate 0.08 --reasons`

# P08 engine (Donautal, sup:70710, raw_material, leverage): how its price is set, and the plan to reach 0.75

Leverage case: **no relationship charge**, so there's no full-cost calibration. Its cash rate comes from its own sheet pairs
(below). Prices are EUR/kg. "db0-equivalent @ 45 d" = the price converted to AS-14404 db0 and 45-day payment, so every
sheet is comparable.

## 1. The engine in one table

| what | measured | evidence |
|---|---|---|
| **Final offer** | **always our 3rd message** (5 of 5 games that got there; validity 30 -> 7) | |
| **Index clause** | **mandatory for 24 months**: every sheet it sent from round 1 carries AS-14404 (db0 unless we asked for db5). "a 24-month agreement necessitates an AS-14404 index clause" | 6 of 6 games |
| **Deadband pricing** | db5 costs **+EUR 0.12/kg** vs db0 (0.024 per point), at equal payment. That is exactly what db5 saves us (EUR 0.118/kg at path +6%). **Deadband is neutral: take whatever it offers** | a43d R2 5.26 db0 / 5.38 db5; R3 5.21 / 5.33; 1f27 R1 |
| **Payment pricing** | its rate is about **8%** (7-8.5% from 3 primary/alternative pairs, cent rounding), the same as ours. **Payment days are neutral**; keep the 45 d it prefers ("to provide the most favorable base price, we propose the 45-day term") | 5.53@45 / 5.49@14; 5.50@45 / 5.46@14 (db5); 5.36@45 / 5.33@14 |
| **Hedge** | every alloy-index argument meets "That is not our reality: our AS-14404 is covered at fixed prices until March 2027" + "does not change our calculation" (5 of 5) | |
| **Round 1** (our 24 m clause-free asks ~4.70-4.73) | answer **5.41 @ 45 db0** (3 games) or **5.53 @ 45 db0** (2 games; 325d: 5.51 @ 30). Same sheets and same claim in all of them: variance, not wording | |
| **Round 2 depends on what we do with its clause** | **we stay clause-free: -0.15** (a43d, best game). We switch to db5 (its db0-equivalent): -0.15 (586a) / -0.06 (9bfa, + 14 d) / **0 "hold"** (1f27, db5 asks below its standing). We accept its db0: **-0.05** (ab47) / -0.09 (325d) | db0-equiv @ 45 d |
| **Round 3 (final)** | -0.03 to -0.06, with the volume forecast taken (3 of 4) | |
| **Walk-away** | once: we countered its final (v2.7 prose-alternative bug) -> "we withdraw" | 1f27 |
| **Asks for data** | "Which figures is that based on? Please send us the data." in round 2 of 5 games: we had nothing new to cite in round 2 | |
| **Open book?** | the dossier says open book, but it refused the breakdown in every game ("company policy") | |

**Data reactions (everything we ever cited in P08):**

| data | games | reaction | effect |
|---|---:|---|---|
| AS-14404 -0.3% (2026-03 -> 2026-09) | 6 | "does not change our calculation" + "not our reality" (hedged) | none |
| rising LCI-C +1.7% / PPI-C2431 +9.7% (a43d) | 1 | "We received a lot of material", "Your figures confirm our case" | none visible (a43d still the best game) |
| volume forecast `fc:370010@2026-09` +1.9% (round 3) | 4 | taken 3x; once "we require the actual data to verify this volume increase" | final step -0.04 to -0.06 |

## 2. Score map (24 months; 12 months can't compete: 0.75 would need EUR 4.69)

| score | db0 @ 45 d | db3 @ 45 d | db5 @ 45 d |
|---|---:|---:|---:|
| 1.0 (C_best) | 4.894 | 4.959 | 5.003 |
| **house 0.75** | **5.118** | 5.186 | 5.232 |
| 0.70 | 5.163 | 5.231 | 5.278 |
| ours 0.647 (a43d) | 5.210 | 5.279 | 5.326 |

**1 cent/kg = 0.011 score.** 36 months costs us the same as 24 months (2-year horizon), but it was priced higher in P07 and
P10, so don't. The house needed **EUR 0.09/kg (1.8%) below our best**, on any deadband.

Best path seen: round 1 at 5.41, clause-free in round 2 (-0.15), final -0.05 = 5.21. Repeating that path, plus a cut from
the data we never sent (below), is the route to 0.75.

## 3. Honest, checkable facts we have NOT cited yet (ranked)

| # | fact (sentence to send) | kind | why it should land | risk |
|---|---|---|---|---|
| 1 | "On 10 September you quoted us EUR 5.45 for this bar, valid 90 days, 'material covered until March 2027; price valid accordingly' (quote:7300008)." | own recent quote | its own price 20 days before the EUR 6.05 opening, still valid; same hedge it cites against us; rival-quote-type data was taken 14 of 18 times elsewhere | not in the case refs, so the arena may mark it "irrelevant" (no trust cost; only "contradicted" costs). The prose works either way |
| 2 | "Our orders over the last year were at EUR 5.43-5.45 (po:4500014305-10, po:4500014391-10, po:4500014455-10)." | price history | flat price while its alloy cost is hedged; never cited in P08; price history was P18's strongest argument on the same part | P03: "does not change our calculation" 2/2 |
| 3 | "Producer prices for cold drawing changed -2.3% from 2026-06 to 2026-08 (idx:PPI-C2431@2026-06, idx:PPI-C2431@2026-08)." (weight 0.36) | index, falling, **not hedged** | answers its own defence "our base price must still account for the increases in our other cost drivers" (325d R2); the latest data months | its 12-month is +12.3%, so it may read as cherry-picking. Only ONE index claim per e-mail |
| 4 | "We had seven supplier-caused quality notifications on this bar in the last 12 months (qn:20004725, qn:20004878, qn:20004922)." (+ 4 more: qn:20004895, 20004940, 20004951, 20005016) | quality record | true, recent, all recharged; a different kind from 1-3 | its scorecard is green (75 ppm): don't claim a bad ppm rate; give no figure (the arena then takes its own) |
| 5 | volume forecast `fc:370010@2026-09` +1.9% | volume | taken 3 of 4 | already used (round 3); move it to round 1 |

**Never cite:** any AS-14404 window (hedged: -8.5% / -7.5% windows exist but meet "not our reality" 5 of 5); PPI-C2431
12-month +12.3%; LCI-C (weight 0.03); the alternative `quote:7200008` EUR 6.06 (dearer); 70740's old EUR 5.41
(`quote:7100065`, May 2025, and 70740 is the P18 supplier); OTD 88% / scorecard ppm (green); notice (the contract's 60 d
is met). No should-cost exists for this part.

## 4. Plan, round by round (3 messages, then its final)

**Structure: ONE main sheet, 24 months, 45 days, clause-free ask in rounds 1-2** (the only game that held clause-free got the
biggest round-2 cut). Expect its clause on every counter. That's fine: at the final, accept its primary whatever the
deadband (neutral for us). Never 12 or 36 m, never a payment switch, never push after the final.

| our msg | ask (24 m, 45 d, no clause) | data (3 different kinds max; one index claim max) | expected answer (db0 @ 45 d) |
|---|---|---|---|
| 1 | EUR 4.73 (as now) | own quote EUR 5.45 (#1) + price history 5.43-5.45 (#2) + volume forecast (#5) | 5.41 or 5.53 so far; #1/#2 aim to lower that first counter |
| 2 | +EUR 0.10-0.11 (a43d: 4.84) | cold drawing -2.3% (#3); one line: "We prefer a fixed price; if a clause is required, start it after your cover ends in March 2027" | -0.15 (a43d) |
| 3 | +EUR 0.10-0.15 | quality notifications (#4) | **final_offer** (-0.03 to -0.06 + data): accept its primary |

- Our ask stays below its counter all the way (a43d: 4.73 / 4.84 / 4.99 vs 5.41 / 5.26 / 5.21). Never offer above its
  standing price.
- Don't switch to db5 asks below its standing price: that drew "hold" (1f27).
- Realistic outcome: a43d's path again = 0.65; plus EUR 0.05-0.10 from the uncited data = **0.70-0.76**. If round 1
  lands on 5.53 instead of 5.41, expect ~0.5-0.6.

## 5. General points for the agent (not P08-specific)

- Leverage cases with a hedged supplier: drop every index claim on the hedged series (5 of 5 "not our reality"). The
  dossier motive `hedged_forward` says which series.
- A supplier's own recent quote for the same part (in `quotes.csv`, often with a remark) is the strongest honest anchor we
  never use. `C_arguments.jsonl` files it as `rival_quote_context` with "Another supplier quoted", which is wrong for its
  own quotes (see `analysis/requests_for_dhruv.md` #1, `own_past_quote`).
- Have one new data kind ready for EVERY round. Both P02 and P08 asked "Which figures is that based on?" in round 2,
  when we had nothing new.
