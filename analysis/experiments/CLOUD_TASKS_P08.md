# Tasks for the cloud Claude (parth-94): P08 - beat the house 0.752 (team best 0.732)

Division of work: **you design, simulate and write the exact commands; Parth's local Claude only runs them live and pushes
the results** (it has the key and the quota; you have neither - never call the arena). Work on branch
`parth/n1-p06-p09-p12` only, never push to main, `git pull --no-rebase` before every push. Code freeze Sun 12:00.

## What the local side learned today (use it)
- **Price history counts only as a PATH.** P10: flat [29.89 x 8] -> "does not change our calculation"; the path
  [28.94, 29.89, 29.89] -> "we took it into account" (5/5, first counter 31.70 -> 31.50). P18 jump 5.26 -> 5.84: taken.
  Downward paths (P11): no effect. `noidea.price_path()` builds it from facts.json.
- **Weak facts hurt a supplier that is moving** (P07 deterministic A/B: lean 0.812 x2; + QN or labour -0.3% in round 2 ->
  0.792). Quality complaints to a GREEN supplier (P08 is green, 75 ppm) cost concessions. Now gated in noidea.
- **Its own old quote = `irrelevant`** in code (P04 quote:7200019, P11 quote:7300011) - but P11's prose then moved 45.50 -> 45.00
  ("like in that old quote").
- **Suppliers here are deterministic for identical messages** (P07 probe A twice: same prices to the cent) - except where a
  per-session draw exists (P08 low/high). So one game per variant is informative on the low draw.
- **Gap steps (30%) are excluded for hedged suppliers** (P08 89259de630143206: +0.20 step -> -0.06, final round 3, 0.528).
- Crash fixed: one claim with 19 QN IDs -> arena HTTP 500 -> abandoned case. Max 8 IDs, one part.

## T1 (now): `tools/experiments/p08_record.py` - a scripted P08 player like `p04_record.py`
- Fixed plan per message (prices from code, no model), `--sim` against your `analysis/tools/sim_donautal.py`, archive + log like
  p04_record (run_plan.archive / measure / results.jsonl / quota_log). Flags for variants, one variant per live game.
- **Base = the best low-draw path** (cae4b621695f8161 / c387 / 6912: clause-free, 24 m, 90 d main sheet, the steps they used),
  round 1 data = PPI-C2431 -2.3% + forecast +1.9% + **NEW: upward price path**:
  "Our orders for this bar rose from EUR 5.17 to EUR 5.45 within nine months (po:4500013278-10, po:4500013392-10,
  po:4500013795-10, po:4500014455-10)." (prices 5.17 / 5.24 / 5.43 / 5.45). No QN (green supplier).
- Variants to wire: `--quote` (round 2: its own 10-Sep quote "EUR 5.45, valid 90 days, material covered until March 2027"
  quote:7300008, as prose with the ID), `--m36` (36 months), `--nopath` (control = base without the path).
- Print the same table as p04_record (every "after our msg" line) and the R1 value (db0-equivalent @ 45 d) so the effect
  of round-1 data is visible on its own.
- Write `analysis/experiments/NEXT.md`: the exact commands in order and a decision rule for each outcome
  (e.g. "R1 low draw < 5.40 -> path works, run --quote next; R1 = 5.41 -> path no effect, run --m36"). Keep it short.

## T2 (after each game I push): update the model and NEXT.md
I push `datasets/runs/<session>.json`, `tools/replays/backoffice/P08_<session>.json`, `analysis/experiments/results.jsonl`,
`notes/quota_log.md` after every game. Refit the floor model (R1 value, budget, draw), append one line per game to
`analysis/cases/P08_floor.md`, and rewrite NEXT.md with the next single command.

## T3 (when a variant beats 0.752, or lowers the low-draw R1 value by >= 0.03): port it into the agent
Gate it on the supplier type that showed it (hedged_forward / raw_material leverage, not P08-only), add a test, keep
`offline_eval` and `ruff` counts unchanged, and put the live check command in NEXT.md.

## Rules
Offline only (no arena, no quota). One change per variant. Never cite AS-14404 windows (hedged: "not our reality"), rising
indices, or QNs to P08. Never push after its final_offer. Don't edit noidea.py logic for other cases without a gate.
