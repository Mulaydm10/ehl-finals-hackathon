# NoIdea agent: change log and experiment record

Agent: `tacto/starter-kit/arena_kit/agents/noidea.py` (`arena play case:Pxx --agent noidea`).
Offline tools (no practice quota): `src/eval/offline_eval.py` (simulated supplier on the 10 probed
cases, exact C_open/C_best from Neel's probes), `src/eval/replay_moves.py` (the real P07 supplier's
moves), `src/eval/calibrate.py` (best deal vs opening per case).

**The simulator is optimistic** (P01 sim 0.98 vs live 0.85; v1.1 P07 sim 0.81 vs live 0.68): use it to
rank versions, not to predict arena scores. It ignores arguments, tone and the relationship charge.

## Live results (practice arena)

| version | case | score | session | notes |
|---|---|---:|---|---|
| naive (kit) | P01 | 0.58 | a44d915880203878 | baseline |
| stock LLM + Qwen 9B | P01 | 0.00 | b04caaf8824a9871 | Qwen offered €142.50 > the ask of €138.55; instant "agreed" |
| v1 | P01 | **0.85** | e3e0b7be271e9371 | €135.70, Apr 2027, 14 d in 3 rounds; "we did not know that, a fair point" |
| probe (Neel) | 9 cases | 0–0.12 | see quota_log | walk-away probes for exact C_open/C_best |
| v1.1 | P07 | 0.68 | 00ae513af1091e9c | 24 m won (+0.48); price stalled at €5.52; volume question unanswered 3× |
| v1.2 | P07 | 0.69 | 33e48d99ea640a6a | anchor €4.94; supplier 5.56 → 5.56 → 5.52 → **final_offer 5.50** in round 4. All claims verified but "it does not change our calculation": single-part PO history is irrelevant to a kit price. Final reason: "please share the specific data or calculations you are basing [the kit target] on" → next: a kit-level calculation argument |

## Versions

### v1 (commit 3676484): code sets the terms, Qwen writes
- Search over every `term_options` combination, priced to a target supplier value, ranked by our
  total cost (incl. relationship charge); concession anchor = cost-justified change (EDA §3).
- Supplier estimate: cost floor from should-cost, cash rate from motives. Checked arguments from dataset C.
- Evidence: P01 0.85 live.

### v1.1 (commit 725c769): P07 lessons
- Cost floor = min(should-cost, current, quoted) × 0.94; floor only for stabilise/secure_supply.
- Every e-mail states the binding volume + term (the P07 supplier asked "Which volume can you commit to?" 3×).
- Reciprocal concession (never more per round than the supplier gave); 8 planned rounds (~25 s per live round).
- Sheets must differ in cost.
- Offline: mean 0.695 (responsive) / 0.694 (stubborn).

### v1.2 (this commit): Neel's playbooks + calibrated anchors (offline only, 0 games)
| change | source | offline effect |
|---|---|---|
| Anchor depth below the opening per goal/type (stabilise 3%, routine renewal 3%, quality 9%, capacity 14%, bundling 15%, RFQ 20%, raw material 22%) | `src/eval/calibrate.py` on Neel's probes: best deal is 0.3–2% below opening in stabilise cases, 13–22% in leverage/bundling/capacity | P05 0.32→0.76, P07 0.81→0.95, P08 0.37→0.88, P18 0.37→0.94 |
| **All 3 sheets within 1% of our best C** (the supplier may pick any) | offline eval P10: a 12-month sheet at equal supplier value cost us +33% and was picked | P10 0.31→0.97 |
| Never offer above the supplier's standing price | playbooks/_common.md §2, P01 stock-LLM 0.00 | guardrail |
| Each data ID cited once per case; new arguments in later rounds | _common §2, P01 replay ("we received a lot of material") | – (sim ignores args) |
| Better of the 6/12-month index windows per series | playbooks/price_increase.md (P02: 6 m) | – |
| No-cost-push arguments when the quote is below today's price (drivers < 3%, flat PO prices), all kit parts | P07 live trace: "our price follows our main cost drivers", we had cited nothing | – |
| Deal size vs our current business ("about €188,700 a year, ~5× our business with you") for needs-volume/bundle suppliers | Neel's P07 brief; P07 "a binding higher volume would help us" | – |
| RFQ: cite the best rival `offer:` once per bidder | playbooks/rfq.md | part of P05 gain |
| final_offer → one last non-price ask, then accept | _common §4 | – |
| Open book → ask for the cost breakdown; we pay late → promise reliable payment; quality → ask for the 8D | _common §3 | – |
| Qwen gets the type playbook's "goal / motive → lever / tone" sections | playbooks/*.md | Qwen 6–7 s per call, on-message |
- **Offline: mean 0.936 (responsive) / 0.944 (stubborn), up from 0.695 / 0.694.**
- P07 vs the real supplier's moves: if it holds at €5.52 whatever we do → 0.68 (ceiling); if it keeps
  giving €0.03 a round → 0.77. Beating 0.68 needs the supplier to move: that's what the volume answer,
  deal-size line and driver data are for. **Needs one live P07 game to validate.**
- Anchor depths are fitted on 9 cases (same generator as the hidden final, but different suppliers):
  watch for overfitting; prefer goal-level depths over case-specific ones.

## Open questions / next
- P01: Neel's score-1.0 package is Apr + 90 d, v1 took 14 d (cash-rate estimate 0.14 may be too high).
- RFQ round-robin is simple; Neel's auction mechanics (step targets down together) not yet in code.
- Index clauses still off (correct for P02/P08/P18 where the path is positive; may help when it's ≤ 0).
