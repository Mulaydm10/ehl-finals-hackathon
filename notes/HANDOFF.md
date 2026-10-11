# HANDOFF - read this first after a context reset (state at 2026-10-11 ~00:05, agent v2.34b)

EHL Munich 2026 hackathon, **Tacto Negotiation Arena** track, team **🃏 NoIdea** (Dhruv = user, Neel, Parth).
Live Final: **Sun 2026-10-11, code freeze 12:00**, 5 waves × 8 min, hidden suppliers, no human in the loop; top-10 pitch 13:00.

## Where things are
- **Frozen: tag `final-v2` (`17b7f16`) is the final's agent** (= v1 + 2 stress-lab fixes); v1 behaviour via `NOIDEA_EXPERIMENTS=hidden,no_prem_std,no_hold_market_check` (tools/final/RUNBOOK.md).
- v2 work on the Mac: worktree `~/Dhruv/ehl-v2` (branch `v2`); run its code with `PYTHONPATH=~/Dhruv/ehl-v2/tacto/starter-kit` (the shared venv otherwise loads main = v1).
- **Repo (source of truth):** Mac mini `~/Dhruv/ehl-finals-hackathon` (`ssh macmini`), GitHub `Mulaydm10/ehl-finals-hackathon`
  (private), branch `main`. Laptop scratch copy for editing: `/tmp/claude-1000/-home-mulaydm10/<session>/scratchpad/repo`
  (NOT a git repo - always `cat` the Mac file into it before patching, then `scp` back).
- **Agent:** `tacto/starter-kit/arena_kit/agents/noidea.py` (current **v2.34b**; the final runs `--agent noidea` = noidea_rfq.NoIdeaAgent on top). Run: `cd tacto/starter-kit && source .venv/bin/activate`
  then `arena play case:Pxx --agent noidea -v`.
- **Model for the e-mails:** gpt-6-astra (OpenAI). Env: `set -a; . ./.env; . ./.env.openai; set +a; export LLM_PROVIDER=openai
  LLM_BASE_URL=https://api.openai.com/v1 LLM_MODEL=gpt-6-astra LLM_API_KEY=$OPENAI_API_KEY`. Default `.env` = local Qwen
  (`~/Dhruv/local-llm/serve-qwen`, port 8081). **Never use the Antigravity proxy.** Key in `.env.openai` (gitignored) - user must rotate after.

## Read these files (in this order)
000. **`docs/SCORE_PROGRESS.md` - how the scores improved (tables): ~0.83 per case in one run, memory off.**
00. **`docs/LESSONS.md` - how we work, the mistakes we made and fixed, rejected ideas. Read before changing the agent.**
0. **`docs/GENERAL_RULES.md` - every general rule (35) with its live evidence. Start here.**
1. `notes/agent_changelog.md` - EVERY version v1 → v2.15, each live result with session id, root causes, lessons. **Read the tail.**
2. `notes/quota_log.md` - every practice game (who, case, version, score, session). ~86 of 200 used; reset 2026-10-11 12:22.
3. `datasets/G_lessons.json` - lessons fed to the model each round (`principles` = playbook, `general`, per case type).
4. `docs/PLAYBOOK_REVIEW.md` - external playbook vs our agent (gaps: overfitting, injection, LOO validation).
5. `PLAN.md`, `notes/next_tasks.md`, `docs/EDA_FINDINGS.md` - plan, task list, data findings.
6. Teammates: Neel `analysis/` (central layer `analysis/agent_variants/central.py`, `analysis/central/LEARNINGS.md`,
   calibrated sims `analysis/tools/`), Parth (`analysis/cases/P06/P09/P12/P18.md`, `analysis/strategy_0.9.md`).

## Tools (all offline, no quota unless noted)
- `src/eval/offline_eval.py [--llm --show --only stubborn Pxx]` - our simulator (optimistic; misses behaviour like pace mirroring).
- `src/eval/archive_runs.py` - archives every arena game to `datasets/runs/<session>.json` (re-run after each game).
- `src/eval/compare_games.py sess:label …` - side-by-side of live games. `replay_walks.py` (P02), `replay_rfq.py` / `debug_rfq.py` (P05),
  `replay_finals.py`, `replay_p11_p08.py`, `inject_test.py` (prompt injection, must PASS), `signals.py`, `collect_threads.py`.
- Web app to chat with the suppliers by hand: `src/ui/chat_app.py` (localhost:8765 via `ssh -N -L 8765:127.0.0.1:8765 macmini`).
  Manual play times out (60 s per message) - use "Ask NoIdea".

## Workflow rules (from the user)
- Every change: **offline Qwen trial → offline Astra trial → live**. Record everything; **after each turn commit + push to main**
  (changelog, quota log, sessions, archive). Keep general learnings in `G_lessons.json` and memory.
- Merge teammates' work keeping both sides; **never `git pull --rebase` over a merge commit** (use `git pull --no-rebase`).
- After a merge ALWAYS check `git diff --name-only --diff-filter=U` before any commit (a `commit -a` once committed conflict markers, fixed in 4c2f71d).
- Heredocs over ssh break on apostrophes → write scripts locally and `scp` them (pattern used all session).
- User wants general improvements (no supplier-specific overfitting) + high scores.

## Best live score per hosted case (team, all versions)
| P01 | P02 | P03 | P04 | P05 | P07 | P08 | P10 | P11 | P18 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **1.00** (v2.34 hidden 0.9997) | **0.879** (v2.34e HIDDEN, normal mode, 9b8414c1) | **0.963** (Neel; hidden 0.954) | **0.874** (ceiling; hidden 0.815) | **0.965** (Parth scripted; agent 0.87) | **0.812** (Parth; our 0.825 was ENGINE-TEMPLATE mode, normal 0.77-0.79) | **0.916** (Parth; hidden 0.781) | **0.710** normal (Neel; 0.741 ENGINE-TEMPLATE mode 673ee890; ours normal 0.702) | **0.885** (Parth scripted; agent 0.80, hidden 0.79) | **0.727** (v2.28; hidden 0.688) |

**Single-agent hidden pass (memory off, v2.34b):** see changelog tail. Validation mode: `NOIDEA_EXPERIMENTS=hidden`.

## Last live results (recorded)
- v2.15: **P05 0.61 (new best, e9eaf87e62371fdf)**; **P02 0.20** (ef17b16a03f0225d) - supplier switched its primary to 30 d and made that its final; analyse vs the 0.48/0.51 games (they stayed on 90 d).
- Nothing is running now.

## State 20:45 (agent v2.21b, all branches merged at 50d0513, rules 1-79 in docs/GENERAL_RULES.md)
- Read GENERAL_RULES.md (sections I-J = teammates), analysis/central/MISTAKES.md, FINAL_TRIGGER.md, ENGINES.md, VARIANCE.md.
- New since 19:05: supplier memory (datasets/H_supplier_memory.json, rebuilt by src/eval/after_game.sh after EVERY game),
  grid probe + floor trade (P11), late-payment admission, Parth gap steps (P07 0.81) + weak facts after a hold, safe sync
  (src/eval/sync.sh - use it, it refuses to commit conflict markers).
- P11: floor EUR 45.00 is hard (0/9 asks below accepted); best 0.7935; the floor trade (45.00 + EUR 300 chargeback = 0.809) is
  untested live. P04 recipe (one longest-payment sheet, near-close msg 2; Parth 0.874) NOT in our agent yet.
- Next: one live pass of all hosted cases on v2.21b (quota ~49 left before the 12:22 reset); then P04 recipe.

## State 19:05 (v2.16j, all teammate branches merged at b0b53d5)
- **Read `docs/GENERAL_RULES.md` (52 rules incl. teammates' section I) and `analysis/central/ENGINES.md` + `VARIANCE.md`.**
- P11: 10 games on v2.16.x, median 0.71, best 0.79; round-1 counter is a per-session coin flip (46.00 / 46.50) -> stop spending
  P11 games. Kept general fixes: chargeback at real ppm, follow best-priced structure, holder packs 2 facts / mirror spreads 1,
  fillers, no early accept with facts left, one near-close ask, premium clamp (bug), figure-free QNs. Off (experiments):
  `mirror_step`, `meso`, `news_frame`, `qn_claims`.
- Next: one full pass of the hosted cases on the merged agent (expected ~0.75 mean, cloud VARIANCE.md), P01/P05/P07 untested.

## v2.16 (P11 focus, 18:00-18:10)
- P11 0.67 -> **0.79** live: chargebacks priced at the real defect rate, follow its best-priced structure (300 ppm / EUR 0), Neel's falling-window claims, one index per e-mail, late price history. v2.16b: walk guard only when it stalls (it fired on a template line while P11 was conceding EUR 1/round). Details: changelog tail.

## Merged
- 2026-10-10 ~18:00: Parth branch parth/n1-p06-p09-p12 merged into main (be018e9): E1 experiments, round-1 argument backbone, UTF-8, parallel RFQ sends + RFQ focus choices; v2.15 walk guard kept. 37 tests pass, offline mean 0.94. Nothing running.

## (old) RUNNING note
- v2.15 live: P02 finished **0.20** (ef17b16a03f0225d, analyse it) and **P05** (`/tmp/v215/P05.log`). Get scores with
  `grep '"score"' /tmp/v215/P0*.log`, then `archive_runs.py`, append to `notes/agent_changelog.md` + `notes/quota_log.md` +
  `notes/sessions.txt`, commit, push.

## Current focus / next steps
1. **P02 (weakest, highly variable 0.00–0.51):** what works = hold ONE structure (90 d), short e-mails, 0–1 IDs, no attachment,
   small slow steps, never comment on its departments, take its best sheet when it repeats an objection (walk guard v2.13).
2. **P05 (RFQ):** v2.15 = 10% market anchor, secure best remaining on a walk, primary-sheet-only accept. C_best ≈ €26.50; bids stall ~€31.
3. Then: re-run the full hosted set once on the final version; Live Final readiness (runner `arena run --set final --agent noidea
   --parallel 10`, Sunday 08:00 data refresh + rebuild datasets, Mac must not sleep), submission (repo public, README, commit hash, slides).

## The most important general learnings (details in the changelog)
- Code sets every number; the model reads/chooses/writes (a model setting prices offered above the ask → 0.00).
- Suppliers react to STRUCTURE and **mirror our concession speed**; arguments mostly "hold but don't change" prices.
- **Never push after final_offer**; accept its **primary** sheet ('-a' ids are refused by the arena).
- Never cite an index that rose; don't fight a justified increase with a cherry-picked window; take its clause if it insists;
  adopt a term it refuses repeatedly; never comment on its internal departments; repeated objection → take its best offer.

## NEXT STEPS (2026-10-11 ~00:40, after loop 3 of the hidden single-agent pass)
1. 08:00 CEST: `bash tools/sunday_release/rebuild.sh` (backup, arena data, merge release, rebuild A/B/C, tests + crash test + round-1 diff; rollback line printed). Commit + push.
2. 09:00 pre-flight: `NOIDEA_EXPERIMENTS= arena run --set practice --agent noidea --parallel 10` (load test: 60-s limit, 503 handling).
3. Open idea (NOT built): payment terms are near-ties in our model (P18/P04/P08/P07 within 0.05-0.12% of C); P18 opened at its
   standard 30 d scored 0.700 mean (n=3) vs 0.51-0.65 at 45 d. Candidate tie-break: open on the suppliers standard term, keep
## NEXT STEPS (2026-10-11 ~00:40, after loop 3 of the hidden single-agent pass)
1. 08:00 CEST: `bash tools/sunday_release/rebuild.sh` (backup, arena data, merge release, rebuild A/B/C, tests + crash test + round-1 diff; rollback line printed). Commit + push.
2. 09:00 pre-flight: `arena run --set practice --agent noidea --parallel 10` (load test: 60-s limit, 503 handling).
3. Open idea (NOT built): payment terms are near-ties in our model (P18/P04/P08/P07 within 0.05-0.12% of C); P18 opened at the
   supplier standard 30 d scored 0.700 mean (n=3) vs 0.51-0.65 at 45 d. Candidate tie-break: open on the standard term, keep the
   shorter term as a round-2 trade (P18 0c968aae, P10 Neel). Needs an A/B in NORMAL mode before any default change.
4. Hidden-mode pass L3 (all normal mode): P01 0.999, P02 0.818, P03 0.954, P04 0.815, P07 0.792, P08 0.916, P10 0.702, P11 0.794, P18 0.621 = mean 0.823.
5. 12:00 freeze: start `arena run --set final --agent noidea --parallel 10` before 12:00.
