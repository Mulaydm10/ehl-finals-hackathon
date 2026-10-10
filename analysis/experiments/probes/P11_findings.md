# P11 live probe (Parth, 2026-10-10 evening): Kalwisz holds at EUR 45.00

Probe `P11_A.json` (scripted, no model): rounds 1-2 as the best agent game, then ONE untried fact per round.
| round | our ask | new fact | arena result | its price |
|---|---:|---|---|---:|
| 1 | 42.77 | quality 2376 ppm, steel -4.3%, forecast +20% | verified x3, all "taken" | 46.00 |
| 2 | 43.77 | energy -17.1% | taken, "only a small part of our total cost" | 45.50 |
| 3 | 44.17 | QN mean **18558 ppm** (no separator) | **duplicate** - "already factored the quality issues" | 45.50 |
| 4 | 44.37 | its own quote EUR 45.15 (quote:7300011) | **irrelevant** - "does not concern this part or our company" | 45.00 ("like in that old quote") |
| 5 | 44.50 | labour -0.3% | taken - but held | 45.00 |
| 6 | 44.60 | price path 46.33 -> 45.15 | "does not change our calculation" | **final 45.00** |
Score 0.794 (= team best, 6b02 agent v2.16). Session in `results.jsonl` / quota log.

## What it means
- **EUR 45.00 is its behavioural floor:** 3 games stop at 45.00-45.13 whatever we cite. Every reply: "we cannot give up margin
  right now. Faster payment would help us more than anything" (dossier M1: "I cannot sign anything that lowers our margin").
  Payment is a fixed term in this case, so its one lever is closed. 0.90 needs EUR 44.35; not reachable with honest means
  (a prose promise of early payment would not bind - we don't do that).
- **Quality record counts once per case:** QN rows after the scorecard ppm claim = `duplicate`.
- **The earlier `contradicted` QN claims were a number-format bug:** we wrote "18,558 ppm", the arena (German) read 18.558.
  Fixed in `complaint_args()` (no thousands separator). General rule: no thousands separators in any checked figure.
- **Its own earlier quote is `irrelevant`** (only quotes in the case refs or our alternative count) - but the prose still
  moved it 45.50 -> 45.00.
- A downward price path (cuts at renewals) does nothing; an upward path is what P10 took.
