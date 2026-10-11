# P10 Run 1 - offline, Qwen requested (2026-10-11 06:05-06:15 CEST; 0 arena sessions, 0 LLM calls)

Brief: "P10 Record-Breaking Investigation - Ravensteiner", Run 1. Goal: the baseline, why it stops, the strongest untested lever.

## Provider
- **Qwen (requested): not reachable.** The documented Qwen server is Dhruv's Mac (MLX, `~/Dhruv/local-llm/serve-qwen`, port
  8081; notes/HANDOFF.md). From this laptop `curl http://localhost:8081/v1/models` -> exit 7, connection refused
  (`qwen_check.txt`). The P18 runs recorded the same.
- **It does not change P10's e-mails:** `noidea_p10.py` writes its P10 e-mails in code. The documented offline evaluator
  with `--llm` made **0 LLM calls** on P10 (`offline_eval_P10.txt`), so Qwen and Astra would send byte-identical messages.

## Commands (all local; none opens a session)
```
cd tacto/starter-kit
curl -s -m 3 http://localhost:8081/v1/models                                   # -> qwen_check.txt
LLM_PROVIDER=openai LLM_BASE_URL=http://localhost:8081/v1 LLM_MODEL=qwen3.5-9b LLM_API_KEY=none \
  uv run python ../../src/eval/offline_eval.py --llm --show --agent-file ../../analysis/agent_variants/noidea_p10.py P10
uv run python ../../src/eval/offline_eval.py --show --agent-file ../../analysis/agent_variants/noidea_p10.py P10
                                                                                # both -> offline_eval_P10.txt
uv run python ../../tools/experiments/p10_offline.py ../../analysis/experiments/probes/P10_M.json --seed 1|2|3
                                                                                # -> p10_offline_baseline.txt
uv run python ../../analysis/tools/p10_record_check.py                          # -> record_check.txt
```
Offline checks:
- `offline_eval.py` has no arena client.
- `p10_offline.py` runs `probe.py` with its client replaced by a 127.0.0.1 arena-sim and asserts that address before it starts.
- `p10_record_check.py` reads local files only.

## Agent, design, code
- Agent: `analysis/agent_variants/noidea_p10.py` (main, merged into this branch at 44e6f47). Its scripted twin is
  `analysis/experiments/probes/P10_M.json`, the 59c899b9 e-mails byte for byte.
- New: `analysis/tools/p10_record_check.py`.

| msg | sheet (23,400/yr, lead 56) | claims (all verified live) | live answer (59c899b9, 3c4aa1a6, 3a968d38) |
|---:|---|---|---|
| 1 | 29.89, 24 m | price path 28.94 -> 29.89 (po:4500010364-10, po:4500010407-10, po:4500014436-10); should-cost 24.31 (cost:340010); rubber PPI-C2219 -0.3% 2026-01 -> 02 | open 31.50 |
| 2 | 30.40, 36 m | labour LCI-C -0.3% 2025-10 -> 2026-01 | final 31.10 |
| - | accept its final | | **0.7097** (3 of 3) |

## Results
| tool | result | what it says |
|---|---|---|
| documented `offline_eval.py` (Dhruv's simulated supplier), with and without the Qwen setting | 0.80 at message 1, both supplier types | **not predictive.** It agrees to any sheet that costs at least C_best; live, this message draws 31.50 |
| fitted P10 simulator `p10_offline.py`, P10_M | 31.20 (0.7019) at seeds 1 and 3; 31.10 (0.7097) at seed 2 | the simulator draws one grid step less in 30% of games; live, these exact e-mails gave 31.10 every time |
| archived replay of `noidea_p10.py` on 59c899b9 (no LLM) | turns 1-2: body, sheet and refs SAME | the current agent sends the best-known path byte for byte |
| exact cost engine (`record_check.txt` A) | 31.10 = 0.709739; record 30.70 = 0.740961; **30.69 = 0.741742** | at lead 56 only <= 30.69 beats 0.741; at lead 42 or 35, <= 31.41; 24 and 36 months cost the same |

## Why the current strategy stops at 31.10 (`record_check.txt` B, C; 56 traced P10 games)
1. **Two messages only.** It goes final at our second message in 39 of 39 normal-mode games.
2. **The first counter is pinned.** 31.50 in 40 of 41 normal-mode games where should-cost and the price path were taken.
   A third taken fact never lowered it: rubber index x7, forecast x2, OTD x1.
3. **The final cuts at most 0.40.** Finals at message 2 were 31.10 x7, 31.20 x16, 31.30 x8, 31.40 x6, 31.50 x2. The record
   needs 30.69: a cut of 0.81 in that one message, twice the largest ever seen.
4. **0.741 came from the arena's engine-template window** (673ee890, the only template game; analysis/cases/P10_draw.md):
   - round 1: Segment Manager -> Pricing Committee, "band ends at ..., buyer at ..."; open at 31.00;
   - round 2: "Approved: you may go further" -> 30.70.
   - Zero escalations in normal mode across all 194 back-office logs, all cases.
5. **The structure is already optimal.** Lead 56 / 36 m / 23,400.
   - Lead 42 needs <= 31.41, but it prices 42 d at 33.80-34.00.
   - Its own 54 d (its quote; not a term option, never sent in 393 games, may be refused with a 422) saves EUR 4,800
     (<= 30.80 beats). But its 54-d alternatives were 31.90/32.00 against 31.70 at 56 d with the same facts: about +0.20, net
     worse than 56.
6. **Every strong fact is spent.**
   - The part has two cost drivers (cost_drivers.csv: PPI-C2219 w 0.14, LCI-C w 0.28), each with one falling window. Both
     are used.
   - Should-cost and price path are used.
   - Left over: OTD, forecast, news (shrugged 1/1, 11/11, 1/1); quality (scorecard ppm shrugged in round 1, "we meet the
     agreed quality targets"); 7 QNs on the part in 12 months, but the scorecards are green (rule 74: QNs only for an
     amber/red supplier).
   - The notice claim needs a letter with notice days; doc:20260918-70410-P10 has none, so it is not checkable.

## The five levers (brief C)
| # | lever | status | evidence |
|---:|---|---|---|
| 1 | unused verified evidence (QNs, notice/capacity docs) | partially tested, not supported | quality kind shrugged (0b29bc23 r1) / no extra cut (7a9294b8 r2: 31.30); green supplier; the letter carries no notice days |
| 2 | round-1 argument combinations | tested | 31.50 with 2, 3 or 4 facts of any mix (40/41); 31.70 with should-cost alone; 31.90-32.00 with shrugged facts only |
| 3 | timing of the 36-month concession | tested | move + new fact in message 2: 31.10 in 5 of 12 (best path); without the move, 31.10 in 2 of 19 |
| 4 | response strategy (message 2 ask; after the final) | message 2 tested; **after the final untested on P10** | message-2 asks 29.09-31.12 all drew finals of 31.10-31.40. After a final (all cases): agreed 4 of 4 when our sheet was worth >= its final to it (its own alternative or a payment trade); walked 3 of 3 when it was worse off; 1 tiny push (-0.1%, P05) drew a counter |
| 5 | term-sheet economics | tested (cost engine) | 56 d / 24-36 m / 23,400 is optimal; 54 d unproven and likely priced +0.20; 12 m scores 0.117 |

## Strongest new mechanism to test next (Run 2)
**One step inside the Segment Manager's own 2% authority after its final.** In the reproducible 59c899b9 state (final 31.10),
ask 30.69 @ 56 d / 36 m:
- 1.3% under the final, so inside the 2% the Segment Manager may give without the committee (doc:20260310-70410-M1);
- our own price moves up 0.29 (from 30.40), not backwards;
- **0.741742 if agreed.**

Why it is the strongest untested lever:
- It is the only lever whose mechanism, the Segment Manager's own authority, exists in normal mode.
- In this state four facts were taken plus the 36-month move, against two taken facts in the template game whose band ended
  at 31.00. Its own band may reach below 31.00 here.

**Honest odds: low.**
- No supplier in our data agreed after a final to a sheet worth less to it than its final (0 of 4 agreements). Every such
  push walked or was countered.
- The P18 acceptances under its offer (4.91 / 4.94) all came in OPEN rounds, not after a final.
- A walk scores 0 for that game only; the board keeps 0.741.
