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

**Version.** The final runs `main` = tag **`final-v4`** (`a0c9ec5`). Lineage: `final-v1` -> `final-v2` (+2 stress-lab logic fixes) -> `final-v3` (+ last try before walking: when its final costs more than our alternative, one last sheet under the alternative goes out first - a free option; + close before the cap at max(90 s, 1.5 x slowest round + 15 s)) -> `final-v4` (+ RFQ clock: a bidder's final is never left waiting while we show it to a rival whose replies are too slow for its 60 s; reply times stamped before the attachment fetch). Evidence: stress 380 games v4 vs v2 2 better / 0 worse; tests 71 + 1 skip; crash 0; live 9 cases (v3) 0 warnings, same decisions as v2; D02 x3 0.569 / 0.579 / 0.579 (one game the clock saved: a 61 s rival reply); final rehearsal (kit arena-sim) 6 of 6 deals. **Back without git** (prefix to `bash tools/final/start_final.sh`): v3 behaviour `NOIDEA_EXPERIMENTS=hidden,no_rfq_clock`; v2 `NOIDEA_EXPERIMENTS=hidden,no_rfq_clock,no_last_try`; v1 `NOIDEA_EXPERIMENTS=hidden,no_rfq_clock,no_last_try,no_prem_std,no_hold_market_check`. Pre-flight step 0 names the frozen version the checked-out agent code matches; "!! agent code differs" means stop and check out the tag.
