STATUS: DONE (task 19, incl. the update) - 2026-10-10 evening, cloud session, offline only (0 arena sessions, no LLM calls).
Runs: 81ee4b1e4096514b = 0.633 (low draw, main 0bb9fad, round 2 on 60 d). Teammate's **d0708ed1038995d1 = 0.912** (low draw, beat the house:
order-history price path in round 1). Agent: `noidea_neel_cloud.py` / `central_cloud.py` = main f9c48d9 (P03 `OWN_QUOTE_ID` kept) + below.

# P08: the round-1 price path moves the FIRST counter - the lever the budget model said to look for

## 1. Run 81ee (brief)

| msg | ours | its reply (value) | reasons | mistake | cost |
|---:|---|---|---|---|---:|
| 1 | 4.79 @ 90 first, 36 m, clause-free; own quote in words, cross-sell, forecast, PPI | 5.41 @ 90 = 5.338 | "Building on your preference for 14-day payment terms" | none (but no price path: see 2) | the whole gap to 0.912 |
| 2 | **4.94 @ 60** (30%); opening "**We require pricing no higher than the current level**" | 5.34 @ 60 = 5.304 (**-0.033**; gap rule says -0.11) | "Accommodating your requested 60-day payment terms" | round 2 on 60 d and/or an opening naming an acceptable level (the current 5.45) | **-0.08** (floor 5.205 vs 5.12-5.14) |
| 3-4 | deferral, then normal step; floor trade gated off (correct) | 5.255 open, final 5.24 @ 60 = 5.205 | QNs / order history shrugged off | none | 0 |

Fixed: `PAY_DAYS_HEDGED = None` (round 2 back on 14 d: 6 low draws, totals 0.20-0.22) and the prompt rule "never name a price level we could
accept". The two causes are confounded (n = 1); both are blocked.

## 2. The price path (d0708ed1 = 0.912)

| | flat history (every earlier game) | **price path (d0708ed1)** |
|---|---|---|
| round-1 sentence | "Our recent orders ... were at 5.43, 5.45" (8 POs, msg 4) | "**Our orders for this bar rose from EUR 5.17 to EUR 5.45 within nine months (po:4500013278-10, po:4500013392-10, po:4500013795-10, po:4500014455-10).**" |
| its reaction | "does not change our calculation" (6 of 6) | "**it holds and we took it into account**" (round 1, with PPI and forecast also taken) |
| first counter (low draw) | 5.41 / 5.42 @ 90 = 5.338-5.348 | **5.25 @ 90 = 5.180** |
| total cut | 0.199-0.220 | 0.222 (**the budget model holds**) |
| final | 5.10-5.12 @ 14 (record 0.7323) | **4.94 @ 14 = 0.912** |

- The POs: the last order at the low price (5.17, 2025-12-08), the first at each later level (5.24 2026-01-05, 5.43 2026-04-07) and the latest
  (5.45, 2026-09-24). The one-order blip at 5.21 (2025-12-23) is left out. The arena read all four prices ([5.17, 5.24, 5.43, 5.45]): verified.
- **My task-18 table was wrong:** "order history is flat (5.43-5.45): no path". The flat run is only the last 8 orders; the 12-month window holds
  the rise. Dhruv's `noidea.py` has `price_path()`, but in another wording ("were at X until ..., at Y since ...") and only for short-fuse suppliers
  or the experiment `price_path_all`.

**Ported:** `central_cloud.rising_price_path()` builds the exact live sentence form from facts.json (PO window 12 months, blips dropped,
≤ 8 IDs, "this bar" / "this part"). The agent puts it first in round 1 for hedged raw-material suppliers (`PRICE_PATH_HEDGED`; P08 only
among the practice cases) and drops the flat run. Round 1 now carries path + forecast + PPI (3 checked claims, like d0708ed1).
Kept unchanged: 36 m, cross-sell, deferral, floor trade. d0708ed1 had 24 m and no cross-sell; both measured ~0 earlier.

## 3. Does a rising path exist elsewhere, and was it ever cited?

| case | supplier engine | rising path within 12 months | ever cited as a rise? | candidate? |
|---|---|---|---|---|
| **P08** | budget (first counter) | 5.17 -> 5.45, +5.4% | only in d0708ed1 (8 games cited the flat 5.43 / 5.45) | **ported** |
| P18 (same bar, 70740) | mirror | 5.26 -> 5.84 in three months, +11.0% | **yes, round 1 in 13 games** (Parth/Dhruv) | already in use |
| P10 | one-shot | 28.94 -> 29.89 | yes, round 1 (Parth's price path, taken 5/5) | already in use |
| **P04** | floor-stop (pinned to its first counter; 1 cent = 0.17) | 4.29 -> 4.39, +2.3% | never | **strongest next candidate**: same mechanism as P08 (the first counter is everything) - untested |
| P03 | holder (one cut per new kind) | 400.19 -> 412.74, +3.1% | never as a rise (flat 412.74 x8: "does not change" 2/2) | candidate: a path may be "taken" where the flat run was not -> one more cut; untested |
| P02 | mirror | 344.08 -> 348.32, +1.2% | never | weak (small rise) |
| P11, P01, P05, P07 | - | none | - | - |

Not ported to P02 / P03 / P04 here (their replays must stay SAME); the function is general, so enabling it is one gate.

## 4. Checks
- **sim_donautal** (19 games): `PATH_SHIFT = 0.16` (low-draw headline 5.41 -> 5.25 when round 1 cites the rising path).
  - `--validate` over 64 replies: median |diff| 0.010.
  - d0708ed1 round 1 is exact; its final is within 0.01 (4.95 vs 4.94).

| agent | low draw | high draw |
|---|---:|---:|
| main f9c48d9 (60 d, no path) | 0.644 | 0.677 |
| **cloud (path + 14 d)** | **0.901** | 0.856 (high-draw path shift assumed = low; untested) |

- **Replays vs main f9c48d9:**
  - SAME: P01-P05 (P03 13, own-quote change kept), P07, P10, P11 (8), P18 (5).
  - P08: 13 threads change. Round 1 adds the path (4 PO IDs) and round 2 goes 60 -> 14 d.
  - d0708ed1 replay: turn 1 = the live round-1 data (path + PPI + forecast) on 36 m instead of 24 m.

**Conclusions.**
1. 81ee lost 0.08 in round 2 (60 d and/or naming "the current level"). Both are fixed: 14 d plus a prompt rule.
2. The budget model holds (d0708ed1 total 0.222). The lever it pointed to, the first counter, was moved by a verified rising PRICE PATH of our own orders: 5.41 -> 5.25 = 0.912. Ported as round 1's first claim for P08-type suppliers; sim 0.901 on a low draw.
3. Same idea for other first-counter suppliers: P04 (floor-stop, never cited, 1 cent = 0.17) is the strongest next test, P03 a possible extra cut; P18 and P10 already use it.
