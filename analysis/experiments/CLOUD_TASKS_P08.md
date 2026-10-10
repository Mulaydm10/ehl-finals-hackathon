# Tasks for the cloud Claude (parth-94) - updated 2026-10-10 ~21:05 by the local side

Division of work: **you design, simulate and write the exact commands; Parth's local Claude runs them live and pushes the
results** (it has the key and the quota; you have neither - never call the arena). Branch `parth/n1-p06-p09-p12` only,
never push to main, `git pull --no-rebase` before every push. Code freeze Sun 12:00.

## DONE on the local side (read before planning - do not redo)
- **P08 solved by the agent: 0.916** (4ff01141bab9fea6; house 0.752, team best before 0.732). Path: round 1 5.25 @ 90 d ->
  5.02 @ 45 -> final 4.97 @ 45. Scripted probe A first: 0.912 (44afd13).
  What did it (all in noidea.py, gated, offline unchanged on the other 9 cases, 56 tests):
  1. `year_rise_path()`: a >= 3% rise over the last 12 months leads round 1 as a price PATH (5.17 -> 5.24 -> 5.43 -> 5.45,
     4 POs) -> "we took it into account", first counter 5.25 vs 5.40-5.42 in all 16 earlier games. Any supplier (not kits,
     not price_frozen); practice: changes P08 only (P18 already sends its jump, P03 is frozen).
  2. Hedged supplier (motive hedged_forward): no index claim and no cost calc on the hedged series; keep asking
     clause-free (never adopt its clause; accept its final); round 1 = all code sheets (90 d priced highest -> its counter
     on 90 d); later rounds open with one plain line instead of the model's paragraph.
- **P04: 0.874 is the ceiling, we hold it.** --main30 0.766 (30-day floor price 4.88), last-cent ask 4.93 @ 90 after its final
  -> walked, --probe (pay-on-time promise + one-cent-under sheets in open rounds) -> "our best possible proposal", walked after
  the repeated probe (62a17f4abde590c7). Stop P04.
- P07 0.812 (agent), P10 0.70, crash fix (19 QN IDs -> HTTP 500), weak-fact gating - see notes/agent_changelog.md.

## NOW: T1 - P05 (weakest hosted case, team best 0.61): a scripted plan I can run
P05 is the RFQ (3 bidders, rival quotes, 60 s per message per thread). Do for P05 what you did for P08:
engine notes from all P05 games (datasets/runs, tools/replays/*), what each bidder took, where the market stalls, and a
**scripted player** (like p04_record.py: fixed messages, `--sim` against your fitted model, archive + log, one live game
per variant, print every "after our msg" line). Use the local learnings: upward price paths are taken, weak facts hurt
moving suppliers, never push after a final, keep parallel sends (play.py RFQ loop). Put the exact commands and a decision
rule per outcome in `analysis/experiments/NEXT.md`.

## T2 - review the P08 rules for the Live Final (hidden suppliers)
Which hidden supplier profiles would trigger `hedged_forward` / `year_rise_path`, and could either hurt them? Write the
risks + a test (offline replay of P08/P18/P03 games through the current agent: sheets and claims per round) and keep it short.

## Rules
Offline only. One change per variant. Don't edit noidea.py for other cases without a gate and a test. Push to the branch.
