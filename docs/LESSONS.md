# Lessons for the next optimisation round (read before changing the agent)

Distilled from the hidden-supplier loops of 2026-10-10/11 (v2.34 - v2.34h). Details and evidence:
`notes/agent_changelog.md`, rules 105-123 in `docs/GENERAL_RULES.md`.

## How to work
1. **Validate as if every supplier were new**: `NOIDEA_EXPERIMENTS=hidden` (no memory, no per-case data). Score that, not normal mode.
2. **Every change goes through the same gate**: round-1/2 dump of all hosted cases (`notes/analysis_v234/r1_dump.py`; only the
   intended cases may change) -> tests -> 19-case crash test (`crash_test.py`) -> replay of the failing game (`src/eval/gap_replay.py`)
   -> a full live loop of ALL cases in one parallel process (`load_test.py`). Keep a change only if it holds across cases.
3. **Separate the agent from the draw**: the same moves get different counters (supplier draws, our model-written wording).
   Judge on several games; compare the worst case per loop, not only the mean.
4. **One arena mode per comparison**: 23:51-23:58 on 10 Oct the arena answered in engine-template mode; two "new bests" came from
   that window. Check with `analysis/tools/supplier_mode_scan.py` before crediting anything.
5. **Find the mechanism in the trace** (the supplier's `reasons`, our refs per round, its sheets) before writing a rule. Key rules
   on what any case exposes (supplier labels in the dossier, terms, its replies) - never on a case id.

## Mistakes we made and the fix (do not repeat)
| mistake | symptom | fix |
|---|---|---|
| all facts in round 1 for a cash-short supplier | P11 stuck at 45.00 | one fact per e-mail for `cash_short` (v2.34) |
| two facts per later e-mail | P02 ran out of facts, empty e-mail, final on 30 d (0.56) | one fact per later e-mail, every supplier |
| an argument without data ids counted as "unused" forever | P01 sent no checkable fact from round 2 (0.959) | never repeat a sentence; id-less facts never fill a later slot |
| ask below our own previous ask | P02 "without movement from your side" -> final | monotone asks on the structure we hold |
| model read the supplier's ALTERNATIVE as a refusal | P02 hopped 90 d -> 30 d (0.531) | a limit counts only after two refusals by its primary sheet |
| near-close below our own ask + identical no-fact e-mail | P18 walked away (0.0) | never an empty repeat: an e-mail without a new fact always moves |
| blind retry after a 503 | stale counter landed after its final, P10 walked (0.0) | re-sync with the arena, decide again on its state |
| one "cited" set for the whole case | RFQ bidders after the first got no facts | facts tracked per supplier |
| case refs we have no value for were ignored | unseen RFQ bidder asked twice for "proof of volume" | cite the case's own ids without a figure |
| a wave case that cannot open was dropped | load test: P01 never started (429, 10 sessions per key) | runner retries until 90 s before the cap; nobody else uses the key |
| claimed bests without checking the arena mode | P07 0.825 / P10 0.741 were template-mode | rule 118 |
| trusted the log, not the sent e-mail | P10 "trade" A/B never traded (model path rebuilt the sheets) | check the arena trace; `trade_now` |
| testing a second version from another folder (git worktree) with the shared venv | the venv's editable install loads `arena_kit` from the MAIN checkout, so the "v2" run silently plays v1 | run v2 with `PYTHONPATH=<v2>/tacto/starter-kit`; check `arena_kit.__file__` first |
| a simulator failure taken at face value (RFQ bidders walk when pushed after a final) | the stress set said RFQ 0.19; the real P05 bidders stayed in 37 of 40 such pushes | before changing the agent for a simulator failure, measure that mechanism in the real games |
| a learned value measured from a field the opening left out | the slope is silently dropped (no baseline) | baseline = the first value the supplier itself stated; test with an opening that omits fields |

## Ideas tested and rejected (they helped one case and hurt another = overfitting)
- moving the payment term toward the supplier's standard in round 2 (`pay_trade`: P18 0.610 / 0.666 vs 0.688).
- holding the longer contract back for a round-2 trade (`trade_term`: P10 0.7019 x4 with and without).
- raw-material supplier on its standard payment term + shorter term as the trade (`budget_pay`: P18 0.666 x3 vs ~0.68) -
  it copied the best game's moves exactly; the supplier's replies vary, so the score did not follow.
- open on the supplier's standard payment term (P18 up, P04 / P07 down); normal suppliers' cash rate at 7% (moved six cases,
  not the target); lean later e-mails (no change in a same-mode A/B); contract term held for round 2 (unclear in the dump);
  round-1 hold / timeout before the first e-mail (Parth A/B: +0.04 on P02/P07/P18, P10 walked 2 of 2).
- Inconclusive, kept only where it was measured: the two-sheet choice framing for cash-short quality cases.
- `fc100` full cost = should-cost x 1.00 (agent estimate is 5-13% low vs real charges): stress 7 of 9 changed cases worse.
- `fc_ref97` / `fc_ref99` (full cost guessed high without a should-cost figure): unknown-supplier set 9 better / 12 worse, 99% worse overall.

## Checked late
- Lessons the model reads must be general: supplier recipes vs general principles A/B -> the general principles do at least
  as well (mean 0.783 vs 0.755); supplier-specific notes are keyed by supplier id + case type only.

- A dominated-action check needs no supplier model: compare each action with the offers the agent could see (never with
  replies still in flight). It found the one real RFQ bug the stress set held.

## Open questions (measured, not solved)
- Suppliers outside our data cost ~0.07 per case in the stress lab (spread over many lost facts and signals, worst through the
  relationship charge in stabilise cases). No single general fix found; the Sunday release's data for new suppliers matters.
- **Grid suppliers**: where the floor sits inside a 0.50 step differs by session (P11 agreed 45.10/45.25 at 45.50, refused
  44.95 at 45.00, agreed 44.45 at 44.50 once) - the first probe depth is untuned.
- **P18-type** suppliers price a longer payment term steeply (first counter 5.20 at 14/30 d, 5.30-5.50 at 45-90 d); P07 the
  opposite; nothing before round 1 tells them apart.
- **RFQ without facts** tops out early (sandbox D02 ~0.58); with the package's facts it should do better - not measured.

## Results at the end of the loops (hidden mode, normal arena mode, 9 cases in parallel)
L4b 0.826, L5 0.84 (8 cases), L6 0.825; no crash or walk since v2.34f. Records across all teams: we hold 8 of 10.
