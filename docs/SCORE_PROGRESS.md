# How the scores improved - night of 2026-10-10/11 (agent v2.34 -> v2.34i)

All runs: memory off (`NOIDEA_EXPERIMENTS=hidden`, as in the final), normal arena mode. Runs from the arena's
engine-template window (23:51-23:58) are left out - not comparable. Per-game sessions: `notes/quota_log.md`.

## 1. Run by run - average and worst case
| run | time | average (9 cases) | worst case | what was fixed after this run |
|---|---|---:|---:|---|
| loop 2 | 00:06 | 0.735 | **0.000** (P10) | server error caused a walk -> re-sync instead of blind retry |
| loop 3 | 00:21 | 0.823 | 0.621 (P18) | - |
| load test | 00:41 | 0.800 | 0.531 (P02) | supplier's alternative read as a "no" -> needs two real refusals |
| loop 4a | 00:49 | 0.762 | **0.000** (P18) | empty e-mail caused a walk -> every e-mail must move or add a fact |
| loop 4b | 00:55 | 0.826 | 0.688 (P18) | - |
| loop 5 | 01:33 | 0.827 (8 cases) | 0.688 (P18) | - |
| loop 6 | 01:40 | 0.825 | 0.621 (P18) | - |

The average settled at ~0.83 once the bugs were gone; the worst case rose from 0.000 to 0.62-0.69.

## 2. Case by case - first run tonight vs now
| case | first run tonight | now (latest runs) | best now | what made the difference |
|---|---:|---|---:|---|
| P01 | 0.959 | 0.999, 0.999, 0.999 | 0.999 | stopped repeating an uncheckable argument |
| P02 | 0.560 | 0.75, 0.83, 0.78 | **0.879** (team record) | one fact per e-mail; an alternative is not a refusal |
| P03 | 0.954 | 0.95, 0.99, 0.99 | **0.989** (record) | its counter revealed a 36-month alternative (a draw) |
| P04 | 0.815 | 0.82, 0.81, 0.82 | 0.860 | lottery among payment terms; no general fix possible |
| P07 | 0.773 | 0.81, 0.79, 0.75 | 0.812 | the supplier's reaction to our wording varies |
| P08 | 0.916 | 0.92, 0.92, 0.92 | 0.916 (= record) | stable |
| P10 | 0.000 | 0.70, 0.70, 0.71 | 0.710 | server-error fix; contract held for a round-2 trade |
| P11 | 0.794 | 0.79, 0.88, 0.88 | **0.877** | one new reason per e-mail for a cash-short supplier |
| P18 | 0.000 | 0.69, 0.69, 0.62 | 0.688 | no more empty e-mails, so no walk-away |
| **average** | **0.641** | **~0.83** | | |

"First run tonight" = each case's first normal-mode run (for P10 and P18 the run where the bug hit).

## 3. Compared with every team (practice board / per-case records, 01:35)
| | average per case | how it was achieved |
|---|---:|---|
| **our agent now** | **~0.83** | one run, memory off |
| best score any team reached on each case | 0.874 | best of many attempts (we hold 8 of 10 records) |
| next-best team (Codacabana) | 0.808 | best of many attempts |
| other top teams (pegasus, NightHunter, gLarPC, +=) | ~0.79 | best of many attempts |

Practice board: NoIdea #1 (88.0). The biggest gain is consistency: no case is lost any more, and a single run of the agent
beats the next-best team's best-of-many results.
