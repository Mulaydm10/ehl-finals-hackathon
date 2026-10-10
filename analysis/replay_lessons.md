# Replay lessons (N4) - from all saved arena sessions

Source: `tools/replays/raw/` (25 sessions saved 2026-10-10; `tools/replays/save_sessions.py` adds new ones).
Sessions with real rounds: P01 x3, P04 x2, P07 x7, P10 x4. Quotes are the suppliers' own reasons.

| # | What happened | Evidence | Rule for the agent |
|---|---|---|---|
| 1 | **Falling data moves them, rising data backfires.** Energy −3.7% + notice period: "We did not know that - a fair point" and a price cut. Rising indices (+0.6%, +1.7%): "Your figures confirm our case: that driver rose." Part price history: "does not change our calculation" (kits). | P01 e3e0b7be271e9371; P04 d3050f951dc2c45b; P07 0f754b1368387b8e, 33e48d99ea640a6a | Cite only indices ≤ 0 % (variant). Don't cite part prices for kits. |
| 2 | **Re-citing an ID = `duplicate`** + "We received a lot of material". | P01 e3e0b7be271e9371 r2-r3 | Each ID once per case (v1.5 does this). |
| 3 | **Unanswered questions repeat every round:** "Which volume can you commit to?", "Which figures is that based on? Please send us the data.", "please provide a firm release schedule", "the data supporting your calculation that this represents five times our current business". | P07 x5, P04 x2 | Answer with an attachment (variant: monthly call-off schedule CSV); back every computed claim (e.g. "5x our business") with its calculation. |
| 4 | **The final lands on the same cash value whatever the path** (P07: €5.49-5.52 @ 90 d in 5 games, ~0.70; P04: ~€4.874-4.877 twice). | P07, P04 | The last points come from the *structure* the final lands on (cent grid, payment term), not from more rounds. |
| 5 | **Pushing after `final_offer` → walked away** (no deal, 0.12). | P07 c5d845883158676c | Accept on final_offer (v1.4+). |
| 6 | **A near-close asked 0.2% below its stop: refused ("we must maintain our price… final offer") and it went final on a worse term (0.81).** Its stop sits ~0.15% above the floor C_best implies. | P04 5f80eb75c793f352 | Close at most ~0.08% under its standing value, on the payment term where the cent grid favours us (variant). |
| 7 | **Capacity supplier: round-1 `final_offer` in all 4 games** when our first sheet was far below its zone; asking for a shorter lead than it can make = "technically unfeasible" + price premium; lead 56 at €31.90 was `agreed`. | P10 x4 (Dhruv) | Capacity cases: first sheet near its zone, lead time it can deliver; the structure (volume, months) is the win. |
| 8 | **It builds on one of our sheets:** "Building on your proposal for 30-day payment terms…". | P04, P07 | Every sheet we send must be one we're happy to have priced. |
| 9 | Should-cost cited where price > cost: "holds and we took it into account". Volume change (`fc:`): "took it into account" (P07) / "does not change our calculation" (P10). | P10 2d91214cf7693eff, P07 d67da0a2d2360134 | Use should-cost when the price is clearly above it. |
| 10 | Open-book suppliers still refuse the XLSX on the 2nd ask ("company policy"). | P04 | Ask once. |
