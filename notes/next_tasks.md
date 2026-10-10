# Next tasks: focus list (2026-10-10 ~14:50)

State: agent **v1.4** (`--agent noidea`). Live: P01 **0.85**, P07 **0.70** (best of 4). Offline mean 0.94
(simulator, optimistic). Practice games: **22 of 200** (resets Sun 12:22). History: `notes/agent_changelog.md`,
`notes/quota_log.md`. Owners: **D** = Dhruv (+ Claude), **N** = Neel (+ Claude).

## A. Close the P07 gap (0.70 → toward 1.0) (D)
The supplier's final lands at the same cash value (~€5.45–5.50 @ 90 d) whatever our anchor, arguments or
pace. C_best ≈ €5.00. Untested levers, one live game each, offline-check first:
1. **36 months** instead of 24: same C for us on a 2-year horizon, more security for it. ~~tested live: 0.65, priced higher → reverted (v1.6)~~
2b. ~~Volume evidence~~: v1.6 live 0.70, forecasts verified but final still 5.49. **P07 parked at 0.70 (7 games); move to task C.**
2. **Bring in its boss / committee** (approval_ladder: changes > 2% need the pricing committee):
   explicitly ask for a bundle price above the KAM's authority, with the strategic reason.
3. **Hold longer** before its final: smaller concessions (we reach €5.08 by round 4).
4. ~~Astra vs Qwen~~: tested, no difference on P07 (both 0.70).

## B. Model decision for the final (D)
- Offline benchmark (9 openings): **gpt-6-astra** 5.2 s mean / 0 role errors / tone fits the goal, vs Qwen
  6.5 s / 0 errors after the fix but generic. Live P07 with Astra (game 17, c819aac1445eb5d0): **0.70, identical to Qwen** (same supplier moves). Prose quality didn't move this supplier.
- Next: a **parallel-load test** (10 sessions at once, as in a Live Final wave), offline: latency, rate
  limits, errors. Then decide: Astra for the final, Qwen as fallback (`LLM failed → plain opening` already in code).
- Security: the OpenAI key is in the chat transcript → **rotate after the hackathon**. Lives only in
  `tacto/starter-kit/.env.openai` (gitignored, 600).
- No Antigravity proxy (user decision).

## C. Test v1.4 on every case type live (D) - workflow: Qwen offline → Astra offline → live
P05/P10/P11: stage 1 (Qwen) done, 4 bugs fixed (v1.7); stage 2 (Astra) done, 1 fix (English only). **Ready for live.** P10 live: 0.46 (v1.7) → **0.65 (v1.8)** with Astra. v2.0 dynamic live 0.54 (final in round 1, no alt). v2.1 offline: round-1 prior → lead 56 @ €27.38. Target: beat the house agent 0.69.
Only P01 (price_increase) and P07 (bundling) have been played by our agent. Still unplayed:
P02 P03 (stabilise), P04 (routine renewal), **P05 (RFQ)**, P08 P18 (raw material), **P10 (capacity)**,
P11 (quality). ~8 games. Order: P05, P10, P11 first (most different from what we've tested).

## D. Agent features still missing (D)
- **RFQ auction mechanics** (playbooks/rfq.md): step all bidders' targets down together, cite the
  leader's `offer:` to the trailing bidders each round. Today it's simple round-robin.
- **Index clauses**: still off. Right when `index_paths` > 0 (P02, P08, P18); could help when ≤ 0.
- **Signal reactions** not yet in code: closed_book (stop asking for a breakdown; P07 v1.3 said
  "cannot be shared"), term_conceded (lock it), nearing_close (accept sooner), eager_new_business (push).
- **P01 check**: Neel's score-1.0 package is Apr + 90 d; we took 14 d. Is our cash-rate estimate (0.14)
  too high for 70110?
- Builder: `own_past_quote` claim kind; the case's alternative quote IS arena-checked (Neel's request 1).

## E. Live Final readiness (D, N review)
- `arena run --set final --agent noidea --parallel 10`: test the runner end to end against the sandbox
  (`case:D01`, `case:D02`) and the wave cap (the kit's `closing_move` closes before the cap).
- Robustness: Qwen/Astra down → plain opening (done); arena 409/429 handling (kit); logging to a file.
- Mac never sleeps during the final; power; network. Pre-flight at Sun 09:00 (one practice case).
- **Sunday 08:00 release**: `uv run arena data`, rebuild A/B/C (`src/datasets/build_abc.py`), run
  Neel's diff tool (N5), check for new templates → MOTIVES.
- Hidden cases carry `facts` (e.g. new letters) inside the case file: make sure the agent reads
  `case["facts"]` (claims, trigger docs not in the package, kit memos).

## F. Neel's open items (N)
- **Fix playbooks/_common.md §4**: on final_offer accept, no extra asks (P07 v1.3 walked away). See notes/dhruv_replies.md.
- N2 supplier economics (cost floor, cash rate per supplier) → feeds our cash-rate estimate (D-P01 check).
- N4 replay collector + `datasets/D_episodes.jsonl` (our sessions: `notes/sessions.txt`) + replay lessons.
- N5 Sunday-release diff tool.
- N1 for the 9 non-hosted cases (P06 P09 P12–P17 P19) = our hidden-case stand-ins.

## G. Submission and pitch (both, Sun before 12:00 / 13:00)
- Repo → **public** before submission (now private); README: how to run, approach; final **commit hash**.
- ehl.gg: repo, commit hash, short description, slides (`tacto/brief/submission.md`).
- Pitch (top 10, 5 + 2 min): pick one replay to walk through. Candidates: P01 0.85 ("we did not know that,
  a fair point"), P07's story (0.12 → 0.70: 24 m, volume answer, kit calc, accept-on-final).
  Expect: "Why did your agent write that? Would it work on a real supplier? What did it learn and from where?"
- **Entire**: `entire login` on the Mac + import the repo on entire.io (only you can); sessions on the
  laptop aren't captured.
