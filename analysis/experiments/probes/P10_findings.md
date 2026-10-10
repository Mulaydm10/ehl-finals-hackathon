# P10 live probes (Parth, 2026-10-10 evening): what moves Ravensteiner

Scripted probes (`tools/experiments/probe.py`, no model, numbers fixed in `P10_*.json`), all 23,400/yr, lead 56.
Before: 11 games, all `final_offer` in round 1 at EUR 31.70-32.00 (best 0.663). House agent 0.69.

| probe | round 1 (ask, data) | its round 1 | round 2 (ask, move) | its round 2 | score | session |
|---|---|---|---|---|---:|---|
| A | 31.56 (2% under its 32.20), price history + should-cost | **agreed 31.56** | re-asks 30.93 / 30.31 / 29.89 | "agreed offer stands" 31.56 | 0.674 | e479da115f89e76a |
| B | **29.89** (price since 2024), PH + SC | **open 31.50** | 30.40, 36 m | final **31.20** | **0.702** | 991ff7c420b037fc |
| C | 29.89, PH + SC | open 31.50 | 30.90, 36 m, + ppm vs 300 commitment | final 31.30 | 0.694 | 7a9294b8466a475d |
| D | 28.94 (2023 price), PH + SC | open 31.50 | 29.09, 36 m | final 31.40 | 0.686 | e61c28186f958320 |
| E | 28.94, PH + SC + ppm (quality "does not change") | open 31.50 | 29.79, 36 m | final 31.40 | 0.686 | 0b29bc23bb8ed5e4 |

## What the engine does (P10)
1. **The round-1 final was ours.** Our agent's anchor EUR 27.38 is C_best's price at lead 56 (its floor) - "your target
   price is unrealistic" -> final at once. Any credible anchor (28.94-29.89) keeps it open; then it goes final in round 2.
2. **Round-1 counter = structure + data, not our anchor:** 31.50 with price history + should-cost (4/4, anchors 28.94 and
   29.89); 31.70 with should-cost alone. Each claim it "takes into account" ~ EUR -0.20. Quality (ppm vs its 300 ppm
   commitment): "does not change our calculation"; forecast and OTD: same (earlier games).
3. **Round-2 step <= 0.30, larger when our ask is reasonable** (anchor 29.89: steps 0.30/0.20; anchor 28.94: 0.10/0.10).
   "In exchange for this longer commitment" - 36 m is the move it names.
4. **An ask at or above its counter is agreed at our price** (back office: "My call: counter" -> "we agree"). After
   `agreed`, re-asks get "Our agreed offer stands" - no walk, no move.
5. No pricing-committee step appears in any back office, even for moves > 2%.

**Ceiling with this engine: ~EUR 31.20 = 0.70** (= round-1 counter 31.50 - one step). 0.90 needs EUR 28.66 at lead 56
(29.38 at lead 42); nothing seen moves it near that. Lead 42 costs a ~EUR 1.90 premium (> our EUR 0.72 late cost).

## After the agent change (same evening)
| game | what | its round 1 | its round 2 | score | session |
|---|---|---|---|---:|---|
| agent 2a53cb1 | credible anchor 29.57, flat price history (8 POs at 29.89) | open **31.70** (history "does not change") | final 31.50 | 0.679 | c283f47ddedd3b53 |
| agent 87653f3 | + history as a PATH (28.94 -> 29.89) | open **31.50** (path "taken") | final 31.30 | 0.694 | 53bab007f0218897 |
| probe F | anchor 30.50, path + should-cost, 36 m + 30.75 in round 2 | open 31.50 | final 31.30 | 0.694 | f6a3f82 commit |
- **A flat order history is shrugged off; the path to today's price is taken.** The agent now builds it from `facts.json`.
- The round-2 step (0.10-0.30) follows neither our anchor (28.94 -> 0.10, 29.57 -> 0.20, 29.89 -> 0.30, 30.50 -> 0.20) nor our
  step size; B's 0.30 looks like the top of its range. Not worth more sessions.
- **P10 result: 0.663 -> 0.694 with the agent (reliable), 0.702 best (probe B). 0.90 is not reachable with this engine.**

## For the agent (general rule, not P10-only)
- One-shot / capacity suppliers: anchor at a **credible** level (current price backed by the price history, never at
  the floor estimate), all strong data in round 1 (price history + should-cost), keep 36 m as the round-2 move, round-2
  ask ~1/3 of the gap above our anchor, accept its round-2 final.
