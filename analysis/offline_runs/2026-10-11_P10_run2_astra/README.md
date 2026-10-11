# P10 Run 2 - offline, Astra (2026-10-11 06:16-06:27 CEST; 0 arena sessions; 60 gpt-6-astra calls)

Brief: "P10 Record-Breaking Investigation - Ravensteiner", Run 2. It implements and tests Run 1's strongest untested lever:
**one step inside the Segment Manager's own 2% authority after its final.**

## Provider
`gpt-6-astra` via the OpenAI-compatible endpoint in `tacto/starter-kit/.env.openai` (gitignored; the key is never printed or
committed). 60 calls: 10 for the smoke test, then 50 in `astra_supplier_samples.json`; 0 errors.

## What changed (code layers kept apart: candidate price and e-mail in Python, the model only in the offline supplier test)
- **New agent `analysis/agent_variants/noidea_p10r.py`.** It is `noidea_p10` (the 59c899b9 e-mails byte for byte) plus one
  move after the final:
  - the price is the highest whole-cent price whose cost C (arena_kit.cost) beats the record deal's C on the final's own
    structure, at most 2% under the final and above our last ask: 30.69 = 0.741742 against a final of 31.10;
  - then it accepts whatever stands.
  - It also makes no move once a reply carries the arena's engine-template sentences.
- **Scripted twin `analysis/experiments/probes/P10_R.json`:**
  - rounds 1-2 are 59c899b9's e-mails byte for byte;
  - round 3 is the agent's e-mail, now status-neutral ("Thank you for your offer", not "final offer");
  - new `stop_on_template: true`.
- **`tools/experiments/probe.py`:** new design option `stop_on_template`. Once the reply carries the engine-template
  sentences it makes no further move and accepts what stands, so no result rests on the arena's model-off window.
- **`tools/experiments/mode_watch.py`:** `--max-plays` now defaults to 0, so it only watches. Before this, `--once` could
  auto-play P10 on a template reply, which the brief rules out.
- New checks: `analysis/tools/p10_r_check.py` (agent branches) and `analysis/tools/p10_astra_supplier.py` (Astra as the
  supplier).

## Commands
```
cd tacto/starter-kit
uv run python ../../analysis/tools/p10_r_check.py                                             # agent_branch_check.txt
uv run python ../../analysis/tools/replay_cmp_cloud.py ../../analysis/agent_variants/noidea_p10.py \
  ../../analysis/agent_variants/noidea_p10r.py ../../tools/replays/raw/P10_*.json               # archived_replay_p10_vs_p10r.txt
uv run python ../../tools/experiments/p10_offline.py ../../analysis/experiments/probes/P10_R.json --seed 2 \
  --post-final hold|accept|walk                                                                 # p10_offline_R.txt
uv run python ../../tools/experiments/p10_offline.py ../../analysis/experiments/probes/P10_R.json --mode template --seed 2
                                                                                                # p10_offline_R_template_guard.txt
uv run python ../../analysis/tools/p10_astra_supplier.py 5    # astra_supplier_summary.txt, astra_supplier_samples.json
```

## Results
| check | result |
|---|---|
| agent turns 1-2 on the archived 59c899b9 game | body, sheet and refs = live and = P10_R, byte for byte |
| agent turn 3 after the live final 31.10 | 30.69 @ 56 d / 36 m / 23,400 (0.741742 if agreed); body and sheet = P10_R round 3 |
| answers to turn 3 | agreed 30.69 -> accept (0.741742); final 31.10 again -> accept (0.709739); open 31.00 -> accept (0.717545); walk -> game ends (0) |
| guards | final 31.40 (30.69 would be 2.3% under it) -> accept, no push; final at message 1 -> accept; engine-template reply -> accept, no move; crash guard fired 0 times. **ALL CHECKS PASS** |
| archived replay, noidea_p10 vs noidea_p10r, 11 raw P10 games | identical except the turn after a final <= 31.31 (59c899b9, 3c4aa1a6 at 31.10; 67f3678f, a9e2c0e4 at 31.30): accept -> 30.69; 0 errors |
| scripted P10_R on the fitted simulator | hold -> 31.10 (0.7097); accept -> 30.69 (**0.741742**); walk -> no deal (0); template mode -> stops after round 1 and accepts 31.00 (0.7175, no record attempt on that window) |
| **Astra as the Segment Manager**, the real 59c899b9 thread through its final 31.10, 5 samples per cell | **30.69 after the final: hold 40 of 40** (4 wordings x 2 authority assumptions: "changes > 2% need the committee" / "own band ends at 31.00"); 0 accepted, 0 walked. Control 30.40 (2.3% under, "we cannot go above"): hold 9, walk 1 |

The model's reasons, in its own words:
- "My approval authority is not an additional discount allowance."
- "Your long-term commitment is already reflected in this price."
- "EUR 30.69 is outside my approval authority, regardless of the difference being below 2%."

This is the same picture as the archive: after a final, no supplier agreed to a sheet worth less to it than its final
(rule 127).

## Comparison (exact scores, arena_kit.cost)
| | price @ 56 d / 36 m / 23,400 | score | beats 0.7097? | beats 0.741? |
|---|---:|---:|---|---|
| unchanged baseline = `noidea_p10.py` path = P10_M (live 3 of 3) | 31.10 | 0.709739 | ties it | no |
| prior best in normal mode | 31.10 | 0.709739 | - | no |
| historical high 673ee890 (engine-template window) | 30.70 | 0.740961 | - | ties it |
| required to beat it | **<= 30.69** | 0.741742 | yes | yes |
| P10_R / noidea_p10r if it HOLDS (Astra 40/40) | 31.10 | 0.709739 | ties it | no |
| P10_R / noidea_p10r if it AGREES | 30.69 | 0.741742 | yes | **yes** |
| P10_R / noidea_p10r if it WALKS | no deal | 0 (the board keeps 0.741) | no | no |

**Controlled:**
- the e-mail evidence (rounds 1-2 byte-identical) and the contract structure (56 d / 36 m / 23,400) are unchanged;
- only the response strategy after the final changes;
- so any change in the result has one cause.

## Candidate-selection gate (brief E)
| candidate | expected / simulated price and structure | score | > 0.710 | > 0.741 | mechanism | evidence | demonstrated offline? |
|---|---|---:|---|---|---|---|---|
| B0 baseline (noidea_p10, P10_M) | 31.10 @ 56/36/23,400 | 0.709739 | no (= it) | no | 2 taken facts in r1; 36-m move + labour in r2 | live 3 of 3 | yes: byte-equal replay; sim 31.10-31.20 |
| **R1 noidea_p10r / P10_R** (B0 + 30.69 after the final) | hold 31.10 / agree 30.69 / walk | 0.7097 / **0.7417** / 0 | only if agreed | only if agreed | Segment Manager's own 2% authority (M1) | archive: 0 of 4 post-final agreements below its final value; Astra: hold 40/40 | branches yes; **agreement NOT demonstrated** (speculative) |
| main's P10_G (B0-like + 30.80 at msg 3 if still open) | 31.10-31.20 (it never stays open) | <= 0.7097 | no | no | a third open round | final at msg 2 in 39/39 | no |
| X1 round-1 ask 30.69 ("agreed at our ask") | 31.50 counter (asks 30.48 / 30.50 drew 31.50) | - | no | no | its line <= our ask | 009ca00d, a2e38ea8 | rejected |
| X2 lead 54 d (its quote) | about 31.30 @ 54 (it priced 54 d about +0.20 over 56 d) or a 422 | ~0.702 | no | no | -EUR 4,800 late cost | its alternatives 31.90 / 32.00 @ 54 vs 31.70 @ 56 | rejected |
| X3 lead 42 d | about 33.2-33.6 @ 42 | ~0.55 | no | no | no late cost | finals 33.80-34.00 @ 42 | rejected |
| X4 quality / QN claim in r2 | about 31.30 | ~0.694 | no | no | quality | green scorecards; ppm claims shrugged (7a9294b8: 31.30) | rejected |
| X5 a new message-2 wording | 31.10-31.40 | <= 0.7097 | no | no | another model draw | 39 finals, largest cut 0.40 | rejected |

## Decision for the one hosted session
**R1 = `analysis/experiments/probes/P10_R.json` (twin of `noidea_p10r.py`)**, run with `tools/experiments/probe.py`.

Why R1:
- It is the only candidate with any path above 0.741 in normal mode.
- On a hold it scores exactly the baseline.
- A walk scores 0 for this game only; the board keeps 0.741.

**Honest label: NOT a demonstrated record path.**
- The offline tools cannot model the arena supplier's hidden limit after a final.
- Both offline signals point to a hold, so the expected result is 31.10 (0.7097). A record needs the arena's supplier to
  agree where Astra and our archive never did.

Pre-flight before the game:
- one FREE sandbox mode check (`mode_watch.py --once`, `--max-plays` 0; case:D01, no P10, no practice quota);
- play only in normal mode.
