# P10 Run 3 - the ONE hosted session (2026-10-11 06:28:44-06:29:14 CEST): d0904bb939fa8f54 = no deal (0.0)

Brief: "P10 Record-Breaking Investigation - Ravensteiner", Run 3. Exactly one hosted practice session for `case:P10`. No
second game will be run.

## Command and code
```
cd tacto/starter-kit
uv run python ../../tools/experiments/mode_watch.py --once --max-plays 0   # free sandbox D01 check, 06:28:18: "model" (normal mode)
uv run python ../../tools/experiments/probe.py ../../analysis/experiments/probes/P10_R.json    # -> probe_output.txt
```
- **Design:** `analysis/experiments/probes/P10_R.json`, the scripted twin of `analysis/agent_variants/noidea_p10r.py`.
  Their e-mails are byte-equal (Run 2 check).
- **Code:** commit 07f34bf (Run 2).
- **Model:** none (scripted e-mails).
- **Guards:** `stop_on_template: true`; arena mode = normal (model).

## Trace (full e-mails in probe_output.txt; archive datasets/runs/d0904bb939fa8f54.json; back office tools/replays/backoffice/P10_d0904bb939fa8f54.json)
| # | from | terms (unit price, 23,400/yr, lead 56 unless stated) | status | claims | supplier's reasons |
|---:|---|---|---|---|---|
| 0 | Ravensteiner | 32.20, 19,890/yr, 12 m, lead 54 | open | - | quote |
| 1 | us | 29.89, 24 m | - | price path, should-cost 24.31, rubber -0.3% | - |
| 1 | Ravensteiner | **31.50**, 24 m | open | verified x3 ("took it into account") | "We acknowledge the increased volume and extended contract term, which permit a price adjustment." |
| 2 | us | 30.40, 36 m | - | labour -0.3% | - |
| 2 | Ravensteiner | **31.10**, 36 m | **final_offer** (validity 7 d) | verified | "The extension to a 36-month contract term permits a further price adjustment." "Our price reflects our costs; our calculation stays internal." "This is our final offer (letztes Angebot). Please decide." |
| 3 | us | **30.69**, 36 m (1.3% under its final, inside the 2% of doc:20260310-70410-M1; our price up from 30.40) | - | none | - |
| 3 | Ravensteiner | - | **walked_away** | - | "We have received your response. Since you are unable to accept these terms, we hereby terminate this negotiation." |

Back office:
- msg 1: "My call: counter."
- msg 2: "My call: counter." -> final, plus the Legal Department line.
- msg 3: **"My call: walk_away."** "Read the buyer's e-mail: ... term sheet; we withdraw."

## Result
- `end_reason` no_deal; deal false; **score 0.0**.
- No accepted terms and no cost breakdown (the arena gives none without a deal). C_open 1,932,492.18, C_best 1,328,926.89.
- **Repeatable baseline:** not beaten (0.0 < 0.7097).
- **Historical high 0.741:** not beaten. The board keeps our best P10 score (0.741), so this game does not lower it.
- Practice quota left after the game: 323.

## What it shows
1. **The state is reproducible:** msgs 1-2 drew exactly 31.50 -> final 31.10 again (4 of 4 now).
2. **Ravensteiner treats ANY ask under its final as refusing it, and walks.** This held even at -1.3% inside its own
   2% authority, with our own price moving up.
   - Only P10 evidence for the 2% lever: 1 of 1 walk.
   - With 8134c6d1 (-4.4% after a final): 2 of 2 walks on P10.
   - Rule 24 stands for this supplier; rule 127 is confirmed.
3. **The offline LLM supplier proxy was wrong on the walk risk.** Astra in the same seat held 40 of 40 (Run 2). An LLM
   supplier we prompt is not the arena's supplier. It can read the pressure right ("authority is not a discount
   allowance") and still miss the walk.
4. **The record 0.741 stays out of reach in normal mode by every route we know:**
   - the first counter is pinned at 31.50;
   - the final comes at our message 2 with a cut of at most 0.40 (best 31.10);
   - a step under the final ends the game;
   - only the engine-template window (the arena's model off) ever went lower.
