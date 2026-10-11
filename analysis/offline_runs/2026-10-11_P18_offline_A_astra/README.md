# P18 offline run A (2026-10-11 ~05:30, gpt-6-astra configured; no arena session): mistakes audit + candidate scoring

**Commands** (strictly local):
    cd tacto/starter-kit
    .venv/Scripts/python.exe ../../analysis/tools/p18_candidates.py                      -> candidates_exact_scores.txt
    .venv/Scripts/python.exe ../../analysis/tools/p18_replay_agents.py replay noidea_p18_state45 noidea_p18_replay
                                                                                        -> archived_replay_finalists.txt (0 errors)
    set -a && . ./.env.openai && set +a
    P18_MSG3=5.01/14/5 .venv/Scripts/python.exe ../../src/eval/offline_eval.py --agent-file <agent> --llm --show P18
                                                                                        -> sim_*.txt (0.94 at msg 1, 0 Astra calls)
The documented simulator cannot rank P18 (it accepts any sheet costing >= C_best, Run 1); the P18 agents write their messages in
code, so Astra is not called. The ranking below rests on the 58 recorded live games.

## Mistakes so far on P18 and their fixes (all live-evidenced; analysis/cases/P18_lever.md 12-21)
| # | mistake | cost | fix (in code or rule) |
|---|---|---|---|
| 1 | assumed a longer payment term after round 1 is free (cloud cross plan, 90 d; then 45 d) | f2770f53 0.677, d602e35b 0.599 | never move payment longer after round 1 (charged +0.10 each time) |
| 2 | assumed db3 is cheap (bf73ee39, one game) | d602e35b 0.599 | db3 = db5 price; never db3 (db5 is worth more to us) |
| 3 | ran a fixed-text agent 6 times: identical conversations get identical replies | 5 sessions wasted | p18_batch.sh warning; one changed input per live game |
| 4 | asked 4.86 after our own 4.87 (a step back) | 152d666e 0.666 | every agent guards against repeating or undercutting our last ask |
| 5 | asked outside its 2% authority / under its floor in the 0c968aae state (4.89, 4.90, 4.97-5.00 db5) | 4 sessions | the acceptance rule is measured: < 2% under its db0 offer, above the conversation's floor |
| 6 | switched 14 d -> 30 d in a state where it had credited 14 d | b354bd04 0.610 | never change the structure it has priced |
| 7 | handing a replayed conversation to main mid-way: main re-cites facts and repeats our price | caught offline (Run 2) | state45 owns its plan to msg 4 |
| 8 | offline runs left uncommitted | - | tools in analysis/tools, outputs in analysis/offline_runs, committed per run |
| 9 | trusted offline sims built on unverified assumptions (harvest alternatives, soft floors) | ~6 sessions | rank candidates on the live record; sims only catch bugs |

## Candidates for the one live run (exact scores, arena cost model; candidates_exact_scores.txt)
| candidate | best outcome | needs | P(> 0.727) (judgement) | record possible? |
|---|---|---|---|---|
| A: 0c968aae state, 5.01 @ 14 d db5 | 0.7327 | its db5 price exactly 0.10 (floor there: 4.90-4.91, known) | ~0.6-0.75, one shot | no |
| B: 6c2813ce state, 4.93 then 4.94 @ 45 d db0 | 0.7357 / 0.7289 | floor (30-d terms, in (4.91, 4.94]) and 45 d not credited | ~0.5-0.85, two shots | no |
| **C: B with db5 at the same value in the same message** | **0.7420** / 0.7357, then 0.7354 / 0.7289 | as B; the db5 sheet pays +0.0057 when it takes that one | as B (the db0 sheet is the backup in the same e-mail) | no |
| D: a fresh conversation for the record | 0.76 | a floor <= 4.90 (never in 58 games), or 60 d uncharged | ~0.01-0.03 | yes, but very unlikely |

**Record (0.75595):** not reachable from any reproducible state. Each record line needs either an ask >= 2% under its 5.00 (outside
its authority) or a floor <= 4.90, which no conversation of ours reached (lowest: 4.90-4.91 in 0c968aae).
**Decision:** build C (noidea_p18_state45 v2) and verify it in offline run B before the single live game.
