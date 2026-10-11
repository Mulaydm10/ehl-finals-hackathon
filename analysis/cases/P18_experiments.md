# P18 experiment log and changelog (Neel; notes/agent_changelog.md is Dhruv's file and is not edited here)

| when (CEST) | run | type | agent / code | result | record |
|---|---|---|---|---|---|
| 10-11 04:36 | Run 1 | offline, gpt-6-astra | main, noidea_p18_cross, _soft v2, _replay (4.91) at aee97f3 | simulator 0.94 for all at msg 1 (not predictive: it accepts any sheet costing >= C_best); archived replay 0 errors; known hosted outcomes 0.677 / 0.677 / 0.727 | analysis/offline_runs/2026-10-11_P18_run1_astra/ |
| 10-11 04:43 | Run 2 | offline, gpt-6-astra | new noidea_p18_state45 (6c2813ce msg 1-2 verbatim, 4.93 -> 4.94 @ 45 d db0) | verbatim and branch checks pass after a fix; archived replay 42 games 0 errors; simulator 0.94 (not predictive) | analysis/offline_runs/2026-10-11_P18_run2_astra/ |
| - | Run 3 | hosted, one session | - | not executed: user said 'dont run on the arena' | - |
| 10-11 04:50 | offline A | offline (Astra configured, 0 calls) | candidate scoring + archived replay of state45 / replay | C (6c2813ce state, db5 + db0 pairs) ranks first: 0.742 / 0.736 at msg 3; record not reachable from any reproducible state | analysis/offline_runs/2026-10-11_P18_offline_A_astra/ |
| 10-11 04:51 | offline B | offline (Astra configured, 0 calls) | noidea_p18_state45 v2 on main e67addb | all branch checks pass; byte-equal msgs 1-2; archived replay 42 games 0 errors; selected for the live game | analysis/offline_runs/2026-10-11_P18_offline_B_astra/ |
| 10-11 04:52 | LIVE | hosted, 1 session | noidea_p18_state45 v2 | 81b5c6de3be181e5: state reproduced; hold at msg 3; final 5.00 @ 45 d at msg 4 ('absolute limit for these terms') = **0.688** | tools/replays/raw/P18_81b5c6de3be181e5.json, analysis/offline_runs/2026-10-11_P18_live_81b5c6de/ |
| 10-11 05:12 | offline C | offline (no LLM) | acceptance-model audit over 59 games | 0 of 8 acceptances > 2% nominal under its offer; payment and deadband count in acceptance; per-conversation floors; record design: 4.97 @ 14 d db5 first | analysis/offline_runs/2026-10-11_P18_offline_C_astra/ |

## Changelog
- **Run 1 (no code change):** the documented offline simulator is unfit for P18 (see the run README); the decision for the
  hosted run rests on the 58 recorded live games and the determinism of the replies.
- **Run 2:** new `noidea_p18_state45.py` (6c2813ce's 5.00 @ 45 d state; 4.93 then 4.94 @ 45 d = 0.7357 / 0.7289 if accepted).
  Defect found and fixed: the off-track handover to main re-cited facts and repeated our price; the plan now runs to msg 4.
  `noidea_p18_replay.py` default P18_MSG3 4.97/14/5 (refused live) -> 4.91/14/0 (accepted, 0.727).
- **Run 3:** not run (user instruction). Selected agent if a run is approved: noidea_p18_state45.py.
- **Offline A:** mistakes audit (9 items) and exact candidate scores; decision: build state45 v2 (db5 + db0 at the same value per message).
- **Offline B:** state45 v2 (db5 + db0 pairs, value-based guard) verified against the new main (final-v2); selected for the live game.
- **Live 81b5c6de (0.688):** at 45 d its acceptance limit is 5.00; 4.94 was accepted on 30 d in the same state (6c2813ce). It
  values payment days steeply in acceptance. Lesson: in a reproduced state keep the structure the supplier ACCEPTED at, not the
  one it countered on; and never send a later e-mail without a new fact.
