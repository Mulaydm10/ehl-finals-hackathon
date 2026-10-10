# HANDOFF - read this first after a context reset (state at 2026-10-10 ~17:40)

EHL Munich 2026 hackathon, **Tacto Negotiation Arena** track, team **🃏 NoIdea** (Dhruv = user, Neel, Parth).
Live Final: **Sun 2026-10-11, code freeze 12:00**, 5 waves × 8 min, hidden suppliers, no human in the loop; top-10 pitch 13:00.

## Where things are
- **Repo (source of truth):** Mac mini `~/Dhruv/ehl-finals-hackathon` (`ssh macmini`), GitHub `Mulaydm10/ehl-finals-hackathon`
  (private), branch `main`. Laptop scratch copy for editing: `/tmp/claude-1000/-home-mulaydm10/<session>/scratchpad/repo`
  (NOT a git repo - always `cat` the Mac file into it before patching, then `scp` back).
- **Agent:** `tacto/starter-kit/arena_kit/agents/noidea.py` (current **v2.15**). Run: `cd tacto/starter-kit && source .venv/bin/activate`
  then `arena play case:Pxx --agent noidea -v`.
- **Model for the e-mails:** gpt-6-astra (OpenAI). Env: `set -a; . ./.env; . ./.env.openai; set +a; export LLM_PROVIDER=openai
  LLM_BASE_URL=https://api.openai.com/v1 LLM_MODEL=gpt-6-astra LLM_API_KEY=$OPENAI_API_KEY`. Default `.env` = local Qwen
  (`~/Dhruv/local-llm/serve-qwen`, port 8081). **Never use the Antigravity proxy.** Key in `.env.openai` (gitignored) - user must rotate after.

## Read these files (in this order)
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
- Heredocs over ssh break on apostrophes → write scripts locally and `scp` them (pattern used all session).
- User wants general improvements (no supplier-specific overfitting) + high scores.

## Best live score per hosted case (team, all versions)
| P01 | P02 | P03 | P04 | P05 | P07 | P08 | P10 | P11 | P18 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.91 | 0.51 | 0.93 | 0.86 | **0.61** | 0.75 | 0.65 | 0.66 | 0.67 | 0.67 |

## Last live results (recorded)
- v2.15: **P05 0.61 (new best, e9eaf87e62371fdf)**; **P02 0.20** (ef17b16a03f0225d) - supplier switched its primary to 30 d and made that its final; analyse vs the 0.48/0.51 games (they stayed on 90 d).
- Nothing is running now.

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
