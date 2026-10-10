STATUS: DONE (task 1, P02) - 2026-10-10 ~18:00 CEST, cloud session, offline only (0 arena sessions)
Data: all 14 P02 games (datasets/runs, tools/replays/raw, tools/replays/backoffice), calibrated supplier (full cost EUR 367.60, rate 6.6%).
Tool: `cd tacto/starter-kit && uv run python ../../analysis/tools/engine_dump.py P02 --rate 0.066 --reasons`

> **UPDATE (evening):** live game ee98266bedd37231 reached 0.824 (EUR 368.55 @ 90 d, value ~364.5) with steps of 30% of
> the gap. So ~367.8 was NOT a hard stop: it was where our small 0.6 steps ran out by the round-4 final. It mirrors bigger
> steps too (its step / ours: 0.5 without new data, ~1.0 with). See LEARNINGS section 7 and analysis/central/ENGINES.md.

# P02 engine (Nordmark, sup:70510): how its price is set, and the plan to reach 0.68+

All prices below are the supplier's **cash value per unit** ("value") unless marked: the price at its standard 30 days that
pays it the same, `supplier_value` at its calibrated 6.6%. At 90 days, headline price = value / 0.989.
The calibration reproduces all 5 real deal costs (90/45/30 d) to the cent.

## 1. The engine in one table

| what | measured | evidence |
|---|---|---|
| **Payment pricing** | priced at **exactly its 6.6%/yr cash rate**: EUR 0.068 per unit per day, **+EUR 4.10 for 90 d vs 30 d**. Neutral for it, but our money is worth 8%, so **90 d beats 30 d by +0.11 score at the same value** | primary 90 d vs its '-a' 30 d sheet have equal value to the cent in 12 messages (e.g. 373.13 @ 90 / 369.02 @ 30) |
| **Round-1 answer to our standard ask** (EUR 364.69 @ 90 d, value 360.68; 10 games sent exactly this) | no data taken: value **370.72** (a EUR 0.24 token move; 4 games), 3 others 369.86-370.51. Volume forecast taken: **369.77** (4 games) or **369.03** (2 games) | same ask, same claim, two discrete answers; wording does not explain the split (variance) |
| **Rounds 2-4** | with a taken claim it **mirrors our step 1:1 in value** (466f: 0.61 / 0.61 / 0.61 for our 0.61 each; af24: 0.89 for 0.89; 159d: 0.69 for 0.69). Without taken data only **~1/3** (6e75: 0.21 for our 0.60; c52d: 0.20 for 0.61) plus "Which figures is that based on? Please send us the data." | step table in the dump |
| **Stop** | lowest finals **367.79 / 367.86 / 367.93** = its full cost 367.60 + 0.05% margin. Never below full cost in 14 games. 3 games stopped at **369.45** = full cost at its 0.5% sustainable margin (3326 after our fast 1.1 steps: "the maximum concession available under these conditions"; dc1d / ef17 at 30 d: "our best possible price") | finals |
| **final_offer** | **always our 4th message** (9 of 9 games that got there; validity 30 -> 7 days). Its last step is small near the stop (0.07-0.34) | |
| **Walk-away** | only in round 4, twice: (a) it proposed "return to our standard 30-day payment term" in 3 e-mails in a row and we answered 90 d again (150f); (b) our remark about its departments (4d18). Plus 3 timeouts (manual game 94de) | |
| **Committee** | never involved: the back office shows the KAM alone in every game ("My call: counter", once "hold" when our value went down). Asked for it: "not applicable to this standard procedure" (159d); "as Key Account Manager, I hold the full authority" (6e75) | 9 back offices |
| **Index clause (CU-NOTATION)** | never tested live (our sheets were clause-free, it never offered one). **For us a clause can never reach 0.684**: best possible db0 0.27, db3 0.55, db5 0.735 (and only at a price 2.8% below its full cost) | grid with total_cost |
| **Our own 30-day switch** | the two 0.20 games (dc1d v2.13, ef17 v2.15) went to 30 d because **our round-3 sheets did**. Offline replay: when the model logs "refusal payment_days max 30" from its "we must maintain the 30-day term", every 90-day sheet is filtered out (our msgs become 360.44 / 360.92 / 361.40 @ 30 d = exactly the live game). It never refused 90 d; it priced it every round. Holding 90 d = ~0.49 instead of 0.196 | replay of ef17 with a stub model |

**Data reactions (everything we ever cited in P02):**

| data | games | reaction | cut |
|---|---:|---|---|
| volume forecast `fc:350011@2026-09` +11.9% | 9 | "it holds and we took it into account" / "economies of scale" (9 of 9) | R1: EUR 0.95 or 1.69 below the token answer; R2: 1.20 (x4) or 1.92 (x1), then 1:1 mirroring |
| 3 rising index windows (CU +16%, LCI +1.7%, PPI-C241 +6.2%, 6-month calc) | 1 (c52d) | verified, but "We received a lot of material", "Your figures confirm our case", "our pricing must reflect the full twelve-month cost pressure" | **none** (370.72, same as no data), then 1/3 mirroring -> 0.27 |
| no claim at all | 4 | "Which figures is that based on? Please send us the data." | token 0.24, then 1/3 mirroring |

## 2. What the house (0.74) and the board-best (0.684) must have been

No clause can reach either score (above), so both were **clause-free**. Price for each score (calibrated, relationship charge included):

| score | @ 90 d | @ 60 d | @ 30 d | cash value | vs its full cost |
|---|---:|---:|---:|---:|---:|
| 1.0 (C_best) | 365.79 | - | - | 361.77 | -1.6% |
| **house 0.74** | **369.54** | 367.50 | 365.48 | **365.48** | **-0.58%** |
| **board-best 0.684** | **370.16** | 368.11 | 366.09 | **366.09** | **-0.41%** |
| ours 0.507 (af24) | 371.88 | 369.82 | 367.79 | 367.79 | +0.05% |

Value -> score at 90 d: 368.06 = 0.48, 367.40 = 0.55, 367.00 = 0.59, 366.50 = 0.64, 366.09 = 0.68, 365.48 = 0.74, 365.00 = 0.78.

**So the house got EUR 2.31 and the board-best EUR 1.70 more value than our best, both below its full cost.** Its KAM stop
(~367.8) is the wall; the price path is not. Since the committee is closed and payment and clause cannot do it, the most
likely lever is **more taken data kinds**. That is the P03 engine: each new verified kind lowers the stop. In P02 we have
only ever had one taken kind, the forecast. Without it, finals were 369.7-370.1; with it, 367.8-368.4. A single kind was
worth about EUR 2 at the final.

## 3. Honest, checkable facts we have NOT cited yet (ranked by expected cut)

Expected cut: P03's measured rule (about EUR 0.5 x driver weight x fall%) as the floor. P02 rewarded the forecast much
more than P03 did (0.95-1.9 vs 0.14), so the upside may be larger. All are untested in P02.

| # | fact (sentence to send) | kind | expected cut | risk |
|---|---|---|---|---|
| 1 | "Producer prices for basic iron and steel changed -4.3% from 2024-10 to 2025-10 (idx:PPI-C241@2024-10, idx:PPI-C241@2025-10)." (weight 0.16; its own stated share 14%) | index, falling | >= EUR 0.34 | ends 2025-10 = the earliest end the arena still counts (2025-09 = "outdated" in P03). Older window: it may answer "full twelve-month cost pressure". One index claim per e-mail |
| 2 | "We had two supplier-caused quality notifications on this motor in the last 12 months: leakage at test (qn:20004698) and a wrong material certificate (qn:20004826)." | quality record | unknown, likely small (P03 0 ppm ~ 0; elsewhere 3 of 3 taken) | **do not** state a ppm for its whole supply: its scorecard is green (273 ppm); say lots/notifications only |
| 3 | "Labour cost index DE (manufacturing) changed -0.3% from 2025-10 to 2026-01 (idx:LCI-C@2025-10, idx:LCI-C@2026-01)." (weight 0.21) | index, falling | ~EUR 0.03 | low |
| 4 | "Copper notation changed -2.2% from 2026-01 to 2026-03 (idx:CU-NOTATION@2026-01, idx:CU-NOTATION@2026-03)." (weight 0.20) | index, falling | ~EUR 0.22 | **highest risk**: copper is its own +47.7% case; a 2-month dip reads as cherry-picking (c52d: "full twelve-month cost pressure"). Only last, only if 1 was taken |
| 5 | "Our orders for this motor were at EUR 348.32 throughout (po:4500014350-20, po:4500014413-10, po:4500014474-10)." | price history | ~0 (P03 2/2 "does not change our calculation") | low; filler only |

**Never cite:** should-cost `cost:350011` EUR 374.95 (above its quote, so it supports the supplier); notice period (109 d >= 90 d,
verified for the supplier); the alternative `quote:7200002` EUR 421.06 (dearer, leaks a weak BATNA); its own old
`quote:7100044` EUR 381.47; a 2nd forecast ID (`duplicate`); any rising window; the 6/12-month cost calculation (c52d);
OTD 90.4% (0 of 2 taken anywhere; use it as appreciation without the ID).

## 4. Plan, round by round (one structure, one sheet, data every round)

**Structure for all 4 messages: ONE sheet, 90 days, no index clause.** Never 30/45/60 d, never a second sheet. No
attachment, no committee line (it says it has full authority), short e-mail, no remarks about its departments.

| our msg | ask (headline @ 90 d) | value step | data (one new kind each, max one index claim per e-mail) | expected answer (value) |
|---|---|---|---|---|
| 1 | EUR 364.69 (as now) | - | forecast `fc:350011@2026-09` + steel window (#1) + QN quality record (#2): three DIFFERENT kinds (mixed kinds never drew "a lot of material") | 369.0-369.8 with the forecast alone; each extra taken kind is a further cut (P03: -0.3 to -0.5) |
| 2 | + EUR 0.6-0.9 | +0.6-0.9 | labour window (#3) | 1:1 mirror + cut |
| 3 | + EUR 0.6-0.9 | +0.6-0.9 | copper window (#4) only if #1 was "taken into account"; else price history (#5) | 1:1 mirror + cut |
| 4 | + EUR 0.5 | +0.5 | none left | **final_offer** -> accept its primary sheet |

- **Steps <= EUR 0.9.** 1.1 steps made it stop at 369.45 ("maximum concession available"). Never step backwards in value
  (lower price at shorter payment = a value cut for it = "hold").
- **If it pushes "return to our standard 30-day term" in two e-mails in a row**: one line, "We prefer to keep 90 days and
  will pay reliably on the agreed day", and the v2.13 walk guard (take its standing 90-day sheet if within 1.5%).
- **Accept** only its primary sheet at `final_offer` / `agreed`; never push after the final.
- Realistic outcome: P03-sized cuts (~EUR 0.6 for the three new kinds) -> final ~367.2 = **~0.57**. If P02 rewards each kind
  like the forecast (~EUR 1) -> 365.8-366.5 = **0.64-0.71**. Holding 90 d alone protects ~0.49.

## 5. Two agent fixes this points to (for the local session)

1. **A stated preference is not a refusal.** Ignore a model-read limit on a field when the supplier's own standing sheets
   still carry our value (P02: its primary was 90 d in every round while it wrote "we must maintain the 30-day term").
   That limit caused both 0.20 games (replay above).
2. **Kind-name mismatch:** `noidea.py` names its forecast claims `forecast`, but `central.take_rate` and
   `claim_reactions.json` call them `volume_change`, so the forecast gets the 0.30 default instead of 0.76 (2.5 on P02 /
   P03 / P18 as a proven kind). On P18, round 1 now sends two index claims and drops the forecast. One alias in
   `take_rate` fixes it.
