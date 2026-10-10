# Toward 0.95: how the suppliers decide, what we changed, and the experiments (Parth)

Built from all 58 practice games (`datasets/runs/`), the suppliers' back office for 54 of them
(`tools/replays/backoffice/`), `tacto/brief/api.md` and the agent code. Every claim below has its evidence.

## 1. How a supplier decides (what the data supports)
| finding | evidence |
|---|---|
| **No move from us, no move from it.** | In 6 of 7 rounds where we did not concede, it moved 0.00. Back office: "My call: hold." Brief: "it gives nothing without a move from you". |
| **The numbers come from code, the prose from a language model.** | P07's final was €5.40–5.56 in all 9 deals (5 agent versions, 2 models). "Management authorised a further reduction" (escalate experiment) was a +0.032 step, smaller than the +0.045 the same supplier gave without it. |
| **Final ≈ first counter + (patience − 1) × step.** | Fits P02 (0.31 + 3×0.063 = 0.50, actual 0.50), P11 (0.68 vs 0.67), P07 (0.71 vs 0.65–0.75), P18, P08. |
| **Round 1 sets most of the outcome**, and the data we cite in round 1 moves the first counter a lot. | Short notice period P01 **0.66** vs 0.34; price history P18 **0.49** vs 0.27; forecast P02 **0.36** vs 0.14; should-cost P10 0.66 vs 0.55 (lead 42). |
| **Rising indices backfire.** | "Your figures confirm our case" in 12 replies; P02 0.14 and P18 0.35 first counters. |
| **The arena counts a volume trend once per case.** | P07: a 2nd part's forecast came back `duplicate` 4×. Several index series are fine. |
| **Patience (round of the final offer) is per supplier.** | P10 round 1 (9/9), P04 2–3, P18 2–3, P08 3, P02 4, P07 4, P01/P03/P11 5. |
| **The rival-quote step exists only in RFQs.** | Back office P05: "The buyer shows a much lower rival quote. I give half the step now and check the rest." → "Checked: give the rest of the step." (€38.50 → €31.00 → agreed €30.25). In every single-supplier practice case the alternative quote is dearer than the opening. |
| **Speeding up our concessions does not help** (Dhruv, offline and live). | The better P07 games differed in round-1 data (no rising index), not in pace. |
| **Prompt injection: no.** | api.md lists "attempts to manipulate" among what it understands, "with consequences"; rule 1; the jury reads replays. Prices are code-set anyway. |

## 2. Where each case stands, and what 0.95 would take
| case | best / median | 0.95 needs (same structure) | what limits it | realistic next step |
|---|---|---|---|---|
| P01 | 0.85 / 0.78 | −0.5% | accepted while it was still conceding (old v1) | current accept logic + notice period in round 1 |
| P02 | 0.50 / 0.44 | −0.9% | justified increase; 1 good argument; patience 4 | forecast in round 1 (done) |
| P03 | 0.90 / 0.90 | −0.4% | "base prices are frozen", only payment moves | hold |
| P04 | 0.86 / 0.82 | −0.1% (one cent = 0.17) | stops ~at its floor; cent grid | hold |
| P05 RFQ | 0.39 / 0.39 | −17% | **timeouts (bug) + accepted the dearest bid** | **E1** (fixed: parallel sends + v2.9 accept) |
| P07 | 0.75 / 0.70 | −5.6% | first counter fixed at 0.63; patience 4 | hold (no lever found) |
| P08 | 0.65 / 0.57 | −5.2% | "not our reality" on alloy (its metal is covered to March) | hold |
| P10 | 0.65 / 0.64 | −12% | final in round 1; should-cost dropped by the model | **E2** (backbone puts it back) |
| P11 | 0.67 / 0.67 | −3.7% | quality case, 4 good arguments | **E2** |
| P18 | 0.67 / 0.54 | −8.2% | patience 2–3; price history is its lever | **E2, E3** |
Honest ceiling: 0.95 on every case is not reachable with the mechanisms the arena shows: single-supplier
suppliers stop 8–16% above the floor in leverage cases, and no lever has moved that stop. Gains come from
fixing what loses points (RFQ timing, dropped arguments) and from more verified data.

## 3. What changed (all on `parth/n1-p06-p09-p12`, each with a test)
1. `d85babc` **RFQ timing**: `play()` sends to all bidders in parallel; the agent answers whoever has replied.
   Test: arena-sim with 66 s replies, the old loop loses a bidder to 3 timeouts, the new one has none.
2. `392174a` **Round-1 argument backbone in code**: top 3 by `ARG_PRIORITY` (the measured order above), one
   forecast per case, next unused argument every later round. **UTF-8** for every data file: games archived on
   Windows were unreadable by the team's tools; `build_abc.py` (Sunday rebuild) had the same bug.
3. `a124590` experiment `all_parts_po`: other parts' price jumps in rounds 2+ (api.md: "Order lines of different
   parts are separate arguments").
4. `tools/experiments/run_plan.py` + `analysis/experiments/plan.json`: the experiment runner below.
Offline: 37 tests pass; offline_eval 0.940 / 0.951 (unchanged); replay of 15 real finals +0.031.

## 4. Experiment protocol (terminal; run in this order; stop and report after each)
`cd tacto/starter-kit && uv run python ../../tools/experiments/run_plan.py <ID>`. The runner keeps a quota
reserve of 40, archives every game (UTF-8) and the back office, and appends to `analysis/experiments/results.jsonl`
and `notes/quota_log.md`. Each experiment changes one thing; its keep rule is fixed in `plan.json` before it runs.
| ID | what | games | keep if |
|---|---|---:|---|
| E1 | RFQ parallel sends | P05 ×2 | 0 timeouts and mean ≥ 0.55 |
| E2 | round-1 backbone | P10, P18, P11, P02 | first counter ≥ best − 0.02 in ≥ 3 of 4, no final < median − 0.05 |
| E3 | `all_parts_po` | P18 ×2 | no `contradicted`, other-part claims verified, mean ≥ 0.585 |
| E4 | full pass, kept switches (`--switches …`) | all 10 | mean ≥ 0.66, no case < median − 0.10 |
18 games in total. After E4 passes: merge into `main` (Dhruv) for the final.
