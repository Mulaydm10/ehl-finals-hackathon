# What the top-scoring runs have in common (all team games, 2026-10-10 ~23:00)

Tool: `src/eval/top_runs.py` (every archived game with a result; per case the games within 0.02 of the case best vs the rest).

| case | games | best | round-1 facts top / rest | first cut top / rest | top games closed by |
|---|---:|---:|---|---|---|
| P01 | 8 | 1.000 | 5 / 0 (notice period, index, forecast) | 1.6% / 0.9% | it agreed to our ask |
| P02 | 21 | 0.847 | 3 / 1 (index + forecast) | - | its final, one more round |
| P03 | 15 | 0.936 | 4 / 0 (should-cost + forecast 5/5) | = | 90 d, one sheet |
| P04 | 14 | 0.874 | 1 / 0 | = | it agreed to our ask 5/8 |
| P05 | 35 | 0.965 | 0 (hold path) | - | it agreed to our ask |
| P07 | 19 | 0.812 | 3 / 3 (index + forecast 5/5) | 3.7% / 3.1% | one sheet, 90 d |
| P08 | 23 | 0.916 | 7 / 3 (price path) | 13.2% / 10.6% | its final |
| P10 | 19 | 0.702 | 4 / 1 (should-cost + price path 6/6) | 2.2% / 0.8% | its final |
| P11 | 43 | 0.802 | 4 / 4 (index + forecast + scorecard 13/13) | 2.1% / 1.1% | its final / agreed |
| P18 | 16 | 0.727 | 12 / 9 (2 indices + price path) | 14.8% / 12.3% | it agreed to our ask |

## The principles (every case, not one supplier)
1. **Round 1 carries every strong verified fact the case offers** - falling cost indices, the volume forecast, should-cost,
   the price PATH, a notice-period breach. Top games had 1-8 more facts in round 1 in 7 of 9 bilateral cases, and a bigger
   first cut. Most suppliers decide most of the price in their first counter.
2. **One sheet in round 1** in the top games of P02, P03, P04, P07, P10, P11, P18 (the rest sent 2-3): commit to one structure.
3. **The payment term follows the supplier's currency**: 90 d where our money is worth more than theirs (P02, P03, P07),
   14 d for suppliers that reward fast cash (P01, P18, P05), the cent-grid term at a floor-stop (P04 45 d).
4. **The best deals are the supplier AGREEING TO OUR ASK** (P01, P04, P05, P18): keep a standing ask just under its line
   after it holds, instead of taking its final at once.
5. **One more round while it still moves or facts are left** (top games ran one round longer on P02, P03, P04, P11).
6. **RFQ is different**: no facts and no price in round 1 to the high opener (hold path), then a deep ask + the lowest rival.
