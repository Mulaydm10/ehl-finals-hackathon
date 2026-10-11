# P18 offline runs, 2026-10-11 (Neel, local; no arena sessions, no LLM)

Re-run at ~04:40 from the committed tools so every offline check of the night is on record (the first runs were made from a
scratchpad and not committed - a gap in our commit-every-run rule, closed here). Live games: notes/quota_log.md and
analysis/cases/P18_lever.md sections 12-19.

| file | what | tool |
|---|---|---|
| beat_lines.txt | highest price that beats 0.75595 per payment term and clause, from the arena cost model | `analysis/tools/p18_replay_agents.py lines` |
| all_games_table.txt | all 58 P18 games: round-1 sheet and data, its price path, score (tonight's raw files have no start time: "?") | `p18_replay_agents.py games` |
| replay_all_agents_over_all_games.txt | every recorded game fed to noidea_p18_cross / _harvest / _soft (v2) / _db3 / _replay: what each would send, turn by turn; no errors | `p18_replay_agents.py replay` |
| cloud_cross_check_scenarios_odds.txt | the cloud's scripted Werdenfels and odds for noidea_p18_cross (before live; 90 d turned out to be charged) | `p18_cross_check.py --scenarios --odds` |
| p18_dump_all_games.txt / p18_dump_alternatives.txt | every game turn by turn with all sheets incl. its alternatives and their scores | `p18_dump.py [--alts]` |
| sim_harvest_agent.txt | harvest agent vs a scripted supplier that writes 60-d / db5 alternatives (never below the cloud agent; live: no alternative came) | `p18_harvest_sim.py -v` |
| sim_soft_agent_v2.txt | soft agent v2 vs a hidden-floor supplier (beats when the floor <= 4.89; live: the floors were higher) | `p18_soft_sim.py [-v]` |
| sim_db3_agent.txt | 45 d + db3 agent if db3 / 45 d were free (0.732) or charged (0.666); live: charged (0.599) | `p18_db3_sim.py -v` |

The scripted suppliers were built from the recorded games and were wrong where it mattered (payment charged, db3 = db5, floors
higher, replies deterministic): use them to catch bugs, not to forecast scores.
