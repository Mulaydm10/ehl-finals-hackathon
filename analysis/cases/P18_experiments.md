# P18 experiment log and changelog (Neel; notes/agent_changelog.md is Dhruv's file and is not edited here)

| when (CEST) | run | type | agent / code | result | record |
|---|---|---|---|---|---|
| 10-11 04:50 | Run 1 | offline, gpt-6-astra | main, noidea_p18_cross, _soft v2, _replay (4.91) at aee97f3 | simulator 0.94 for all at msg 1 (not predictive: it accepts any sheet costing >= C_best); archived replay 0 errors; known hosted outcomes 0.677 / 0.677 / 0.727 | analysis/offline_runs/2026-10-11_P18_run1_astra/ |
| 10-11 05:10 | Run 2 | offline, gpt-6-astra | new noidea_p18_state45 (6c2813ce msg 1-2 verbatim, 4.93 -> 4.94 @ 45 d db0) | verbatim and branch checks pass after a fix; archived replay 42 games 0 errors; simulator 0.94 (not predictive) | analysis/offline_runs/2026-10-11_P18_run2_astra/ |
| - | Run 3 | hosted, one session | - | not executed: user said 'dont run on the arena' | - |

## Changelog
- **Run 1 (no code change):** the documented offline simulator is unfit for P18 (see the run README); the decision for the
  hosted run rests on the 58 recorded live games and the determinism of the replies.
- **Run 2:** new `noidea_p18_state45.py` (6c2813ce's 5.00 @ 45 d state; 4.93 then 4.94 @ 45 d = 0.7357 / 0.7289 if accepted).
  Defect found and fixed: the off-track handover to main re-cited facts and repeated our price; the plan now runs to msg 4.
  `noidea_p18_replay.py` default P18_MSG3 4.97/14/5 (refused live) -> 4.91/14/0 (accepted, 0.727).
- **Run 3:** not run (user instruction). Selected agent if a run is approved: noidea_p18_state45.py.
