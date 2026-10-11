# Live Final runbook - Sunday 2026-10-11 (team NoIdea)

Everything runs on the **Mac mini** (`ssh macmini`, repo `~/Dhruv/ehl-finals-hackathon`). Keys live only in the git-ignored
`tacto/starter-kit/.env` (arena) and `.env.openai` (model).

| time | step | command | done when |
|---|---|---|---|
| 08:00+ | Sunday data release: backup, download, merge, rebuild datasets, tests, crash test | `bash tools/sunday_release/rebuild.sh` | "self_check ... 0 bad", tests pass, crashes 0; then `bash src/eval/sync.sh "sunday release"` |
| 09:00 | Pre-flight on the final machine (key, model, sandbox D01/D02 + one practice case) | `bash tools/final/preflight.sh` | every case shows a score; no failed / safe move / slow-decision lines |
| 11:00 | Submission on ehl.gg: repo the jury can open (it is private now), README (how to run), approach text, slides, **commit hash** | `git rev-parse HEAD` | - |
| 11:30 | Checklist (tacto/brief/submission.md): `arena me` works; release downloaded; model credits; Mac on power, no sleep | - | - |
| **before 12:00** | **Start the runner and leave it running** | `bash tools/final/start_final.sh` | log shows "wave 1 started" after 12:00 |
| 12:00-~13:00 | Watch the log only: `tail -f logs/final-*.log` | - | 5 waves closed |

## Rules during the final (from the brief)
- **Nobody else uses the team key during the final** - no practice or sandbox games from any laptop: the arena allows 10 open
  sessions per key, and a wave case that cannot open would score 0. (The runner now retries a case that cannot open yet until
  90 s before its wave cap, and keeps polling through transient errors - but do not rely on it.)
- **No pushes after 12:00** (the organisers check the top 10). Do not run `src/eval/sync.sh`, `after_game.sh` or any commit.
- The agent must not read `/v1/events`, `/screen`, `/leaderboard`, `/results` - ours never does (checked: agent, kit runner,
  archive tool). Humans may look at the board in a browser; never feed it to the agent.
- If the runner crashes or the Mac restarts: `bash tools/final/start_final.sh` again - it resumes its sessions.
- Default configuration = what the hidden-supplier loops validated (`NOIDEA_EXPERIMENTS=hidden`). With memory instead:
  `NOIDEA_EXPERIMENTS= bash tools/final/start_final.sh` (only helps if a practice supplier comes back; untested in that mode).

## What the agent was validated on (hidden mode, normal arena mode, 2026-10-11 00:00-01:20)
Mean 0.82-0.83 over 9 practice cases, 9 in parallel in one process in under 4 minutes (wave cap 8), 0 crashes / walks since
v2.34f; P02 0.879 = team record; sandbox (suppliers not in our data) D01 0.87-0.91, D02 RFQ 0.52-0.56.
After the final: revoke the OpenAI key that was pasted in chat on Saturday.

**Version.** The final runs `main` = tag **`final-v2`** (`17b7f16`) = `final-v1` + two logic fixes found by the blind stress lab (RFQ high-opener take checks the live market; learned term slopes kept when the opening omits that term). Evidence: 380 simulated games 2 better / 0 worse; live 9 cases in parallel 0.820, 0 warnings (v1 0.823, same decisions on single-supplier cases); D02 0.579 x2. **Back to v1 behaviour without git:** `NOIDEA_EXPERIMENTS=hidden,no_prem_std,no_hold_market_check bash tools/final/start_final.sh` (identical to v1 on all 380 games). Pre-flight step 0 names the frozen version the checked-out agent code matches; "!! agent code differs" means stop and check out the tag.
