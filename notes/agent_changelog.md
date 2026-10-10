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
| v1.7 / gpt-6-astra | P18 | 0.43 | 6833e98fbbe5ebdf | final_offer €5.40, 60 d, 24 m + AS-14404 db0 in round 3; its db5 alternative sheet was 0.485 (see "P18 live 1") |

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

### v1.3 (offline only, 0 games): kit calculation, supplier signals, Qwen fixes
| change | evidence | offline check |
|---|---|---|
| **Kit-level calculation** for bundles: kit at the supplier's own current prices + today's best price for parts it doesn't sell us yet ("the kit costs EUR 5.95; your EUR 5.74 is a 3.5% bundle discount for 5x our business") | P07 v1.2 live: part-level history "does not change our calculation… do not fully represent the cost structure of the complete bundled kit"; final message asked for "the specific data or calculations" | P07 €5.95 = Neel's hand calculation; P15 €5.56 |
| No part-level PO citations for kits; "kits" wording; cost breakdown "for the kit" | same | – |
| **Supplier-signal catalogue** `src/eval/signals.py` → `datasets/E_supplier_signals.json` (228 supplier sentences, 11 sessions/probes, 22 categories) | new signals found: prose_alternative, closed_book, term_conceded, nearing_close, acknowledges_our_move, absorb_pushback, eager_new_business | – |
| **Prose alternative → term sheet** ("Alternatively, from 1 January 2027: EUR …" is not binding; we put it in a sheet when it's within 1% of our ask or late in the game) | P01 live reason; playbooks/_common.md §4 | parses ISO and "1 January 2027" dates, payment days; no-op without one |
| **Qwen role fix**: "we" is always the buyer; supplier situation labelled as THEIRS; never reveal targets; drop sentences that do (`BAD_OPENING`) | `src/eval/qwen_bench.py` on 9 openings: 5/9 paragraphs wrote the supplier's restructuring/committee as "ours", one leaked "our target cost" | after the fix: 0/9 role errors, 0 leaks; latency mean 6.5 s, max 8.5 s |
- Offline eval unchanged at 0.936 / 0.944 (the simulator ignores text), as expected.
- Qwen still occasionally thanks for a "cost breakdown" it never sent; P03 "we acknowledge your price increase" is soft.

### v1.4: accept on final_offer (after a live failure)
- **P07 v1.3 live (c5d845883158676c): no deal, 0.12.** The kit calculation worked (best price yet, €5.40 vs €5.50
  in v1.2; it also stated "our internal cost breakdown… cannot be shared", "material accounts for about … of our cost").
  But at its `final_offer` our "final tweak" (same price, 90 d instead of 30 d) made it **walk away**.
- **Fix:** on `final_offer` accept if it keeps the must-haves and beats the alternative (and every other bidder).
  `final_tweak()` kept but unused. The playbook rule (_common.md §4 "one small final ask") is wrong for the
  arena: the brief says "final_offer: push further and it may walk" — **Neel: please update the playbook.**
- Simulator now makes a supplier walk when pushed after final_offer; it still can't reproduce this case
  (its supplier agrees before reaching final_offer), so offline means are unchanged (0.936 / 0.944).
- Lesson for testing: offline wins on text/signals need live checks; the simulator only covers price paths.
- Model comparison: the user ruled out the Antigravity proxy; Claude would need a real API key. Not tested.

- **P07 v1.4 live (0d480561d4703cde): 0.70**, accepted its final_offer €5.49 @ 90 d. The fix works.
- Across 4 P07 games the supplier's final lands at the same cash value (€5.40 @ 30 d ≈ €5.49–5.52 @ 90 d) whatever
  our anchor, arguments or pace: **the price path is no longer the bottleneck**. Reaching C_best (~€5.00) needs a
  lever we haven't pulled: e.g. 36 months instead of 24 (same C for us on a 2-year horizon, but security for it),
  or asking for its boss (approval ladder: a bigger move needs the committee). To explore, not proven.

- **P07 with gpt-6-astra (c819aac1445eb5d0): 0.70, identical to Qwen** (same moves, same final). Offline Astra writes
  better and faster (5.2 s, goal-fitting tone), but on this case the words didn't change the outcome. Points again
  at the levers (36 m, committee) rather than the prose.

### v1.5 (offline only): prefer the longer contract on cost ties
- `sheets_at` breaks cost ties by the longest `contract_months`. On P07's 2-year horizon 24 and 36 months cost us
  exactly the same (€327,204 at €5.49 / 90 d: a commitment beyond the horizon "neither costs nor earns"), but 36 m
  is more security for the supplier, whose final sat at ~€5.50 on 24 m in 4 live games (task A1).
- Offline: P07 round-1 sheets all 36 m; e-mail states "30,000 kits per year for 36 months"; eval unchanged
  0.936 / 0.944 (no regression on the other 9 cases; the tie-break only fires on equal cost).
- **Not measurable offline**: the arena's margin formula ignores contract length ("security, not cash") and the
  simulator only models cost. Whether the supplier moves below €5.49 for 36 m needs one live P07 game.

### v1.6 (offline): revert 36 m, only falling indices, forecast evidence
- **P07 v1.5 live (0f754b1368387b8e): 0.65, worse.** 36 months was priced higher (opened €5.60 vs €5.56, final €5.56 vs €5.49).
  One game (replies vary), but no sign of a reward → **tie-break reverted** (plain cost order, 24 m).
- **Our "no cost push" indices backfired:** citing drivers that ROSE < 3% got "Your figures confirm our case: that
  driver rose." → with no increase to fight, only indices that **fell or stayed flat** (bar 0%, was 3%).
- **New signal, volume evidence:** "please provide documentation supporting the binding volume… Which figures is
  that based on? Please send us the data" (rounds 2–4), and "your targeted savings would require a significantly
  higher volume commitment". → cite the latest positive **demand forecast** per part (`fc:` IDs, arena-checked on
  change_pct), top 2: P07 M16 bolt +15.3% (fc:360011@2026-09), nut +9.0% (fc:360012@2026-09).
- Offline: P07 round 1 = volume + kit calc + deal size + 2 forecasts, no rising index; eval unchanged 0.936 / 0.944.
- P07 so far (live): 0.68, 0.69, 0.12 (walked), **0.70**, 0.70 (Astra), 0.65 (36 m). Best = v1.4 on 24 m.

- **P07 v1.6 live (d67da0a2d2360134): 0.70**, final_offer €5.49 @ 90 d again. Forecast evidence verified and accepted,
  the "driver rose" pushback is gone, but the price didn't move.
- **Conclusion after 7 P07 games:** with our current approach this supplier's final converges on ~€5.49 @ 90 d
  (≈ C €327k, 0.70) regardless of anchor, arguments, model (Qwen/Astra), pace or contract length. The remaining gap
  to C_best (~€5.00) needs a lever we can't yet pull from the e-mail. Volume is fixed in P07 (it keeps asking
  "Which volume can you commit to? A binding higher volume would help us").
- Side finding: the deal-size line "around N times our current business with you" can't be backed by a checkable
  ID (spend isn't in facts.json), and the supplier asked 3x for "the exact figures behind" it. Candidate: drop the
  multiple, keep the € value (not done yet).
- **Decision: stop iterating on P07, test v1.6 on the other case types (task C).**

## Testing workflow (team rule from 2026-10-10 ~15:00)
1. **Offline trial on the Mac with Qwen**: `set -a; . ./.env; set +a; .venv/bin/python ../../src/eval/offline_eval.py --llm --show --only stubborn <cases>`
   (full agent incl. real e-mails vs our simulated supplier; 0 practice games). Read every e-mail.
2. **Offline trial with gpt-6-astra**: same command with `LLM_PROVIDER=openai LLM_BASE_URL=https://api.openai.com/v1 LLM_MODEL=gpt-6-astra LLM_API_KEY=$OPENAI_API_KEY` (key in `.env.openai`).
3. **Live** (1 practice game per case) only when 1 and 2 are clean.
The simulated supplier is **ours** (`src/eval/offline_eval.py`), built from Neel's probe data (real openings, exact
C_open/C_best). The arena's suppliers are hidden; Tacto's `arena-sim` is only a plumbing check.

### v1.7 (offline stage 1, Qwen): P05 / P10 / P11 trials
| case | issue found in the e-mails | fix |
|---|---|---|
| P05 (RFQ) | cited a rival offer that was **dearer** than the bidder's own price ("We have an offer at EUR 38.50" to a bidder at ~31.5) | cite a rival only if it's cheaper than this bidder's standing price (playbooks/rfq.md) |
| P10 (capacity) | cited labour +1.7% / rubber +3.2% as bare facts (P07: "your figures confirm our case: that driver rose") | a positive index is cited only against the ask: "…, well below the +7.7% you ask for." |
| P10 | Qwen: "Given **our need to secure full supply coverage**…" (urgency) | BAD_OPENING catches need/urgency phrases |
| P11 (quality) | Qwen offered "faster payment terms… propose a payment schedule" in 3/5 e-mails; payment is **not negotiable** in P11 | Qwen gets the NEGOTIABLE list; sentences about off-table levers (payment, contract length) are dropped |
- After the fixes: no off-table promises, no urgency, comparisons in place; offline scores P05 0.76, P10 0.98, P11 0.98;
  full eval unchanged 0.936 / 0.944; Qwen 5.8 s mean, 6.8 s max.
- Simulator fix: offer IDs now look like the arena's (`offer:70210-1`, was `offer:sup:70210-1`).

### v1.7 stage 2 (offline, gpt-6-astra): P05 / P10 / P11
- Astra e-mails: shorter and firmer than Qwen; no off-table promises (P11 talks ppm + chargebacks only), no role
  errors, no urgency; latency mean 6.0 s, max 7.9 s (11 calls). Same offline scores: P05 0.76, P10 0.98, P11 0.98.
- **One issue: P10 round 3 answered in German** ("Wir sind bereit, verbindliche Jahresmengen…"), picking up the
  suppliers' German words. Fix: "Always write in English" in the prompt + drop paragraphs with ≥ 3 German function
  words (template opening instead). Re-run P10 with Astra: all 3 rounds English.
- Both offline stages are now clean for P05 / P10 / P11 → ready for stage 3 (live).
- Known offline weak spot: **P05 (RFQ) 0.76**; round-robin + rival citing, no auction mechanics yet (task D).

## P10 live (capacity, secure_supply, gpt-6-astra)
| version | score | session | what happened |
|---|---:|---|---|
| v1.7 | 0.46 | 675fc6b9c1c8c291 | we asked lead **35** (need is 42, same cost for us) → "technically unfeasible" → final_offer **€35.00 @ 35** in round 1, accepted. Its prose "Alternatively, with Lieferzeit … days: €…" ignored. "Your figures confirm our case: that driver rose" again (labour +1.7%, rubber +3.2%, even framed "well below the +7.7% you ask") |
| v1.8 | **0.65** | 2d91214cf7693eff | lead **42** → final_offer **€33.80 @ 42** (−€1.20); its prose alternative **€31.90 @ 56** proposed back verbatim → `agreed` → accepted. C €1,541,808 (price 1,492,920 + late delivery 33,600 + payment 9,953 + quality 5,335) |

### v1.8: learnings from P10 applied (offline Qwen + Astra clean, then live 0.46 → 0.65)
- **Supplier-friendly tie-break:** on equal cost to us, pick the option closest to the supplier's own opening terms
  (lead = our need, not faster; contract length near its offer). Replaces v1.5's "longer contract" rule.
- **Never cite an index that rose** (not even "well below your ask"): only indices that fell or stayed flat.
- **final_offer + a cheaper prose alternative → propose exactly that alternative once** ("We accept your
  alternative as you proposed it"), else accept the final. Live: it `agreed` to its own alternative.
- Prose parser: "Lieferzeit / lead time / delivery N days" = lead time, "Zahlungsziel / payment / net N days" = payment.
- Supplier reasons (v1.8): "A reduction in lead time to … days is incompatible with our current capacity
  utilization unless a significant premium is applied"; "Our Lieferzeit is … days" (its standard ≈ 54–56);
  forecast + delivery-record data "holds, but does not change our calculation"; should-cost "took it into account";
  "Our price reflects our costs; our calculation stays internal" (closed book).
- **Next idea (not done):** the supplier prices lead time below its standard steeply (€33.80 @ 42 vs €31.90 @ 56
  = €1.90/unit for 14 days). Our supplier model ignores that (`extra` = 0), so round 1 never offers a longer lead
  at a lower price. Model a lead-time premium in `supplier_value` (`extra` ≈ −k · (std_lead − lead) · price), so
  the optimizer sees the real trade. Capacity suppliers go final in round 1, so **round 1 must already be the
  right structure.**

### v2.0 (offline Qwen + Astra clean): dynamic agent - "the model proposes, code checks"
Code still does all maths and safety checks; at runtime the agent now reads, learns and chooses:
| part | what's new | check that stays in code |
|---|---|---|
| **Package parser** (`parse_packages`) | every offer in the supplier's e-mail, primary + alternatives, all fields (arena template: "a price of €31.90 per unit, Lieferzeit 54 days, …") | 65/65 offer e-mails in `datasets/F_supplier_emails.jsonl` (78 real e-mails, 22 sessions; the 12 misses are order confirmations without prices) |
| **In-negotiation learning** (`learn`, `premium`) | price premium per unit of lead time / contract length / volume from its own packages; offers are repriced with it | both live P10 games give the same **−€0.158 per unit per day of lead time**; baseline fixed at its opening terms |
| **Feasible snapping** (`snap_feasible`) | a lead time it states snaps UP to the next allowed option (its 54 → 56, never 42) | allowed options only |
| **Model reads + chooses + writes, one call per round** (`decide_with_model`) | notes (questions, refusals, wants) → its stated limits constrain later candidates; picks 1–3 of 8 pre-priced candidates and ≤ 3 verified arguments; writes the opening | candidates all within 1.5% of our best C, under its standing price, must-haves kept; indices validated; opening filtered (figures, leaks, off-table levers, German); any failure → deterministic path |
- Offline (simulated supplier now writes arena-format e-mails with a lead-time alternative at −0.158/day):
  deterministic mean 0.937 / 0.944 (no regression); Qwen dynamic P10 0.97 (15 s per call); **Astra dynamic P10 0.97,
  P07 0.98, P11 0.97, 6.2 s per call.** Astra read P10 as "wants … a longer lead time" and picked the lead-56 offer.
- Two bugs found and fixed offline: a moving premium baseline (price jumped 25.81 → 28.52); Qwen urgency
  ("we prioritize a reliable supply chain above all else") now filtered.
- Tools: `src/eval/collect_threads.py` (real e-mails), `src/eval/parse_test.py` (parser + learner on them).
| v2.0 live | P10 | **0.54** | afd996e3d4b14336 | round 1 still asked lead **42** (nothing learned yet) → "Accommodating this shorter lead time requires a premium, resulting in a unit price of €34.00" → **final_offer in round 1, no alternative this time** → accepted. Learning from round 2 comes too late: P10 goes final in round 1 in 3/3 games |

### v2.1 (offline): round-1 prior for the lead-time premium
- Prior: lead time below the supplier's own quoted lead costs it **0.49% of price per day** (P10 live ×2:
  −€0.158/day at €32.20), applied from round 1 when lead time is negotiable; learned values replace it.
- Offline: P10 round 1 now lead **56 @ €27.38** (was 42 @ €27.69); all 10 cases unchanged (0.937 / 0.944).
- P10 live so far: 0.46 (lead 35), 0.65 (lead 42 + its alternative), 0.54 (lead 42, no alternative). House agent 0.69.
| v2.1 live | P10 | 0.65 | 0bba4ffdf93afbe8 | round 1 lead **56 @ €27.38** (prior worked) → "We can revise our offer to €31.90 per unit to reflect the increased volume and extended contract duration… final offer" in round 1 → accepted. Same €31.90 @ 56 as game 21's alternative: **its floor at lead 56 is €31.90 in both games** |

### P10 status after 4 live games (house agent 0.69)
- Final offers: €35.00 @ 35, €33.80 @ 42 (+ alt €31.90 @ 54), €34.00 @ 42, €31.90 @ 56. It always goes **final in round 1**
  and always says its price reflects "the increased volume and extended contract duration".
- To beat 0.69 we need C ≤ €1,516,032 → **≤ €31.35 @ 56** or **≤ €32.07 @ 42** (about 2% below what it has ever given).
- Hypothesis to test next: the dossier says **approval_ladder** ("price changes above X% need the pricing committee") and
  Neel's capacity playbook says "price steps ≤ 2%". Our round-1 asks were 14–15% below its opening; a big ask may send
  it straight to the committee's final word. A **small first ask (≤ 2–3% below its opening, at lead 56)** might keep it
  in normal rounds where it concedes stepwise (as the approval-ladder supplier did in P07).

## Behaviour across all games (src/eval/archive_runs.py, 24 games archived in datasets/runs/)
- **Every game is now archived in full** (both sides' e-mails, term sheets, statuses, trace with reasons):
  `datasets/runs/<session>.json`. Re-run `archive_runs.py` after each game (idempotent, no quota).
- **Each supplier follows its own script; our words barely change it.** P07's price path is near-identical across
  6 games and 5 agent versions (5.74 → 5.56 → 5.56 → 5.52 → 5.49/5.50, final in round 4 every time). Structure
  moves it (24 m, payment days), arguments mostly "hold, but do not change our calculation".
- **Patience differs per supplier**: P10 final in round 1 (4/4), P07 round 4 (6/6), P01 never final in 4–5 rounds
  (concedes €0.5–1.3/round), P04 (Neel) round 3.
- **Ask size alone does not trigger final_offer**: P07 asks 15%+ below → always open; P10 asks 8–15% → always final.
  The approval-ladder hypothesis is not supported (no small first ask tried on P10 yet).
- **What moved suppliers**: structure (P07 24 m; P10 lead 56 vs 35: €31.90 vs €35.00), data only on the data-naive P01
  owner ("a fair point"), and offering back its own prose alternatives (P10 agreed).
- Alternatives appear in most multi-round games (P07 1–4 per game, P10 2/4): free better terms.
- P10 floor seen twice: €31.90 @ 56, €33.80–34.00 @ 42. Beating 0.69 needs ≤ €31.35 @ 56.
- Note: Neel played P04 (d3050f951dc2c45b, 0.86); quota count now 24 of 200.
| v2.2 live | P10 | 0.65 | f0a505fc3669a3b9 | round 1 **36 m** @ lead 56 @ €27.38 → final_offer **€31.90 @ 56, 36 m** in round 1: identical to 24 m. Contract length beyond 24 m is not rewarded |

### v2.2: longer contract on ties for commitment-seeking suppliers (kept, neutral)
- Rule: capacity cases or `wants_commitment` / `capacity_tight` / `needs_multi_year` motives → on cost ties prefer the
  longer contract; others keep closest-to-its-terms (P07). Offline: P10 → 36 m, P07 stays 24 m, eval unchanged 0.937 / 0.944.
- Live P10: no effect (same €31.90 @ 56). Kept because it's free for us and harmless here; revisit if a live case shows harm.

### P10 conclusion after 5 live games (house agent 0.69, ours 0.65)
- Its final comes in round 1 every time, at a fixed price per structure: €35.00 @ 35, €33.80–34.00 @ 42, **€31.90 @ 54–56**
  (24 m or 36 m alike). Beating 0.69 needs ≤ €31.35 @ 56; none of anchor depth, lead time, contract length,
  arguments, model (Qwen/Astra) or dynamic reading moved it below €31.90.
- Untested: a small first ask (≤ 3% below its opening) to avoid the round-1 final; the cross-game data does not
  support the approval-ladder idea, so it's a long shot. **P10 parked at 0.65; next: untested case types (P05, P11, …).**

### v2.3 (offline): patience estimate, used for accept-readiness only
- Prior for the round of its final_offer (26 games): capacity 1, renewal 3, bundling/RFQ/raw material/quality 4,
  stabilise price increase 7 (leverage 4); capacity_tight / allocation / full order book / "not strategic" motives cap it at 2.
- Updated each round from warning signs: validity drops below the opening's (30 → 7 days at the P07/P10 finals),
  or its concession shrinks to < 40% of the previous one.
- **Pacing concessions to it HURT offline** (mean 0.937 → 0.869, P04 0.59): conceding faster just gives value to
  suppliers that would keep moving, and live finals didn't depend on our pace (P07 €5.49–5.50 in every version).
  → used only to be readier to accept near the expected final (within 0.3% of our ask). Offline back to 0.937 / 0.944.

### After a final_offer (src/eval/after_final.py, 13 finals in the archive)
- 11× accepted; 1× proposed its OWN prose alternative back verbatim → `agreed` (P10 2d91214cf7693eff, €31.90 @ 56);
  1× asked for something new (90 instead of 30 days at €5.40) → `walked_away` (P07 c5d845883158676c, 0.12).
- **Suppliers never concede after final_offer; pushing ends the deal.** Rule since v1.4: accept, or send back its own
  cheaper alternative. (Neel played a 2nd P04: 5f80eb75c793f352, accepted final €4.91.)

## P02 live (price_increase, stabilise, group supplier 70510, gpt-6-astra)
| version | score | session | what happened |
|---|---:|---|---|
| manual (web app) | 0 (walked) | 94dea31d90407b56 | 3 timeouts while writing by hand (60 s per message) → "We are withdrawing from this negotiation" |
| v2.3 | **0.48** | da8d0e3d77ce091c | we asked 90 d @ €364.69 → it took 90 d but **priced the financing**: €373.13 @ 90 d (alt €369.02 @ 30 d) → 373.13 → 372.50 → **final €372.15 @ 90 d in round 4** (prior said 7) |
- Its reasons: "extending payment terms to … days incurs financing costs that would necessitate a higher unit price";
  "Which figures is that based on? Please send us the data"; final: "**without additional verified data to substantiate
  your target price, our flexibility remains highly restricted**"; "our calculation stays internal".
- It charges ~€4.11/unit for 60 extra days (≈ 6.7 %/yr, below our 8%), so 90 d was still right (alt €369.02 @ 30 d = C
  €2.27 M vs our deal €2.26 M). Neel's score-1 package €368 @ 90 d needs ~€4 more.
- **We gave it no data on price**: only the forecast (our rule: never cite a rising index). Its opening e-mail states
  its OWN cost shares ("CU-NOTATION rose 47.7 % … 20 % of our cost; LCI-C 2.7 % … 20 %; PPI-C241 6.5 % … 14 %").
  **Next idea: a cost-justification calculation from its own shares × the 6-month index moves** (copper +16% over 6 m vs
  +47.7% over 12 m; Neel: 6-month driver mix ≈ +4.6% vs its +6.5% ask) - the calculation it asks for, like the kit calc.
- Web app: manual play can't meet 60 s per message → add a countdown + "Ask NoIdea then edit" flow.
- Patience prior for group/stabilise price increases is too high (7; this one went final in round 4).

### v2.4 (offline): own-cost-share calculation, negotiator personas + "Patrick Jane" reading, RAG, all sheets judged
| change | evidence | offline check |
|---|---|---|
| **Cost calculation from the supplier's OWN stated shares** ("X rose N% … is M% of our cost") × our 6- or 12-month index moves (arena-checked idx IDs) → "your cost increase comes to about +4.4%, not +6.5%"; the only argument in that round (3 claims); "That supports a price of about EUR …" only if ≤ our own ask | P02 live: "without additional verified data to substantiate your target price, our flexibility remains highly restricted" | fires on P02 (+4.4% vs +6.5%), P03, P04, P08, P18; not P10 (no shares stated) |
| **Personas**: Chris Voss (labels, calibrated how/what questions, never split the difference), Fisher & Ury (interests, objective criteria), **Patrick Jane** (one sharp, true observation from what its e-mail repeats/stresses/avoids, grounded only in its e-mail, signals or notes); stance per goal | user request; playbooks | Astra: "You have linked additional volume to a binding commitment; it sounds like confirmed demand… is what supports your capacity allocation… How can we structure that commitment so you can confirm the full volume?" |
| **RAG** into the model prompt: signals detected in its e-mail (25-pattern catalogue, with what works), our notes on this supplier verbatim ranked by overlap with its e-mail, lessons from our games by case type (`datasets/G_lessons.json`) | P10 retrieval: lead-time-premium signal, committee note, capacity e-mail, "final in round 1" lesson | Astra 8.3 s per call |
| Opening rules: never say the volume isn't binding, never describe/compare the sheets' terms (filtered too) | Astra P02 trial: "this proposal does not include a binding volume commitment"; "keeping your payment terms unchanged" (we asked 90 d) | – |
| "around N times our current business" dropped (keep the € value) | P07: 3 requests for "the exact figures behind" it | – |
| **Accept the cheapest of ALL its term sheets**, not `term_sheets[0]` (credit: **Parth**, P18 6833e98fbbe5ebdf) | 47 supplier messages in our archive carry '-a' alternative sheets | `src/eval/replay_finals.py` on 9 real finals: **+0.028 mean**, P10 game 20 0.470 → 0.656, P18 0.430 → 0.485, P04 +0.014 |
- Deterministic offline eval unchanged 0.937 / 0.944.
- Parth's branch `parth/n1-p06-p09-p12` (not merged yet): P06/P09/P12 deep dives; P18 live 0.43; v2.3 ideas (PO
  price-jump argument, contract-clause share vs its stated share, market line, committee request, plain-word sheets),
  P18 "the AS-14404 index clause is mandatory on 24 months". It edits noidea.py → needs a merge with v2.4.
### v2.3 (Parth, offline only, 0 games): P18 round-1 arguments + plain-word sheets
| change | evidence | offline check |
|---|---|---|
| `po_prices` also cited when the price **jumped ≥ 3%** in the PO history, not only when there's no increase | P18: July index step 5.26 → 5.84 (+11%) was never cited (ask +4.5%) | P18 e-mail now cites it |
| `price_story()`: if the current contract's index clause passes a series on at more than the cost share **the supplier itself states** in its quote ("… is 38 % of our cost"), say so with the clause ID | P18 `ctr:4600070740#3.2` 80% vs 38%; 5 of 10 practice openings state cost shares | fires on P18 only |
| market line in prose: cheapest **recent** (≥ 2026-07) rival quote below the standing price; not in RFQs / stabilise / secure_supply | P18: €5.45 (70710, `quote:7300008`); prose only, past quotes may not be checked as data of this case | fires on P18 only |
| `approval_ladder` motive → round 1: "please put this proposal to your pricing committee" | P18 M3, P02, P03 dossiers | P02, P03, P18 |
| term sheets in plain words ("EUR 4.77 per unit, 90 days payment, 24 months, no index clause") instead of field names | every e-mail printed "index_clause None" | all cases |
- Offline unchanged: mean **0.937 / 0.944**, 31 tests pass, no new lint errors. **Needs one live P18 game** (plan: analysis/cases/P18.md §8).

### P18 live 1 (Parth, v1.7 / gpt-6-astra, session 6833e98fbbe5ebdf): 0.43
Played on v1.7 (`64fd00b`): v2.3 was pushed while the game ran, so v2.3 is still **untested live**.
| round | supplier sheet (primary / alternative) | C primary / alt | score primary / alt |
|---|---|---:|---:|
| 0 open | €6.10, 30 d, 12 m, no clause | 295,173 | 0.000 |
| 1 open | €5.60, 90 d, AS db0 / €5.60, 45 d, AS db5 | 272,032 / 268,714 | 0.319 / 0.365 |
| 2 open | €5.50, 60 d, AS db0 / €5.50, 30 d, AS db5 | 268,912 / 264,784 | 0.362 / 0.419 |
| 3 final_offer | €5.40, 60 d, AS db0 / €5.40, 30 d, AS db5 | **264,023** (accepted) / 259,970 | **0.430** / 0.485 |
(all 24 m; C from `arena_kit.cost.total_cost`, reproduces the arena's c_deal to the cent)
- **The cheaper alternative sheet was left on the table: +0.055 (€4,053).** `standing()` (play.py) is always
  `term_sheets[0]`; `decide()` accepts that ID. The db5 alternative came as its own term sheet with an ID
  (`offer:70740-3-a`), not as prose, so `prose_alternative()` doesn't help. Suggest: at `agreed` / `final_offer`,
  accept the cheapest-for-us sheet among `term_sheets` (and price alternatives in `c_stand` every round).
  Untested: whether the arena accepts an alternative's ID (it lists both sheets again in the order confirmation).
- **Index clause is a hard requirement on 24 m**: "We cannot accept a fixed price for a 24-month term; the AS-14404
  index clause is mandatory" (round 2). All our sheets were clause-free, so it re-added db0 to every primary sheet.
  Supports P18.md §8 "next lever": offer db5 ourselves (≈ €0.04/kg) in exchange for a base-price step.
- Claim results: our round-1 claims all **verified** (AS-14404 −0.3%, LCI-C +1.7%, forecast +1.9%); nothing
  contradicted. Rounds 2–3 cited nothing (refs empty), so no checks. Its own claims (AS +5.9%, LCI +2.7%,
  PPI-C2431 +12.3%) were answered with "That remains." each time.
- It refused the XLSX cost breakdown 3× ("proprietary"), even though the dossier has an open-book motive; the
  writer asked every round. It asked "Which figures is that based on? Please send us the data." (round 2,
  after our message cited nothing) and "Which volume can you commit to?" in the final.
- Price path €6.10 → 5.60 → 5.50 → 5.40 (final in round 3), still above P18.md's floor (€5.45 no clause = 0.51).
- e-mails still say "23,700 units" (P18 is kg). v1.7 printed raw field names; v2.3 fixes that.

### v2.4 (Parth, local): accept the cheapest of the supplier's sheets, not only the standing one
| change | evidence | offline check |
|---|---|---|
| `best_sheet()`: accept / price (`c_stand`, `best_standing`) the cheapest sheet in the supplier's message that keeps the must-haves, by its own id | P18 live 1: `offer:70740-3-a` 0.485 vs accepted `offer:70740-3` 0.430 | replay of the live final: accepts `offer:70740-3-a` |
| play.py: a `422` on accepting an alternative's id (the brief says accept takes the *standing* sheet; arena-sim only knows `offer_id`) clears that id, keeps its terms and decides again | 422 = "nothing happens, no round is used" (api.md) | new test `test_an_alternative_the_arena_refuses_is_kept_without_its_id` |
| `refused_alternative()`: such a sheet is proposed back once at `final_offer` ("We accept your alternative as you proposed it"), the v1.8 prose-alternative path | P10 live: its own alternative came back `agreed` | replay: proposes €5.40 / 30 d / AS db5 (C 259,970) |
- Offline unchanged: mean **0.937 / 0.944** (the offline supplier never sends alternatives), 32 tests pass, ruff clean on the changed lines.

### Merge with Parth + P02 live on v2.4 (Astra) → v2.5 fixes
- **Merged** `parth/n1-p06-p09-p12` into main (7435c91), both feature sets kept: his price story (PO price jump,
  contract-clause share vs its stated share, market line, committee request), plain-word sheets, `refused_alternative`
  + play.py 422 fallback, tests; our best_sheet (with C), cost calc, personas + RAG, patience. Tests 32 passed.
- **P02 v2.4 live (159def0f5e514b40): 0.34** (v2.3 was 0.48). The model (a) chose **no argument in round 1**, so the
  cost calculation built for this supplier was never sent (only restated later), and (b) **hopped the structure**
  90 → 30 → 45 days; the supplier priced every hop (374.84 @ 90, 369.52 @ 30, 369.85 @ 45) → final €369.55 @ 45 d.
  Its '-a' sheets were also there (370.71 @ 30, 368.44 @ 14).
- **v2.5 fixes:** (1) **required round-1 argument**: the cost calc (or a short-notice claim) always goes in round 1,
  the model can only add; (2) **stable structure**: after round 1 our main sheet keeps its non-price terms unless
  another structure is ≥ 1% cheaper for us. Offline Astra P02: cost calc in round 1, 90 d in every round
  (364.69 → 367.26). Offline eval **0.939 / 0.947** (was 0.937 / 0.944). Lesson: **the model may choose, but the
  strategy's backbone (strongest argument, structure) must be fixed in code.**
- **P02 v2.5 live (c52de0252df56877): 0.27.** Cost calc now in round 1 and 90 d held every round, but: "Your figures
  confirm our case: that driver rose. We have reviewed your calculations based on six-month index movements; however,
  **our pricing must reflect the full twelve-month cost pressure**"; it then only moved €374.84 → 373.85 @ 90 d
  (pricing 90-day financing all along). P02 live so far: 0.48 (v2.3, no price argument), 0.34 (v2.4), 0.27 (v2.5).
- **Root cause = our own EDA lesson ignored**: P02's increase IS justified over 12 months (copper +47.7%); its own
  shares give +11% over 12 m > its +6.5% ask. The 6-month window was cherry-picked, and the calc cited 3 rising indices.
- **v2.6 fix:** cost calc only when BOTH the 6- and 12-month totals are below its ask. Now fires on P04 and P08 only
  (not P02, P03, P18, P10). Tests 32 passed; offline 0.939 / 0.947. P02 falls back to the v2.3-style behaviour (0.48).
- Lesson (into G_lessons): **a justified increase is not fought with numbers; trade terms instead (payment, date).**

## Parallel live run, v2.6 + gpt-6-astra, 4 cases at once (16:22, no timeouts / model failures under load)
| case | score | previous best | session | deal / note |
|---|---:|---:|---|---|
| P07 | **0.73** | 0.70 | 8f088ea83d5e5ca8 | **new best P07**: 5.52 @ 30 → 5.52 @ 90 → 5.48 → final **€5.44 @ 90 d**, 24 m |
| P08 | **0.65** | first live | a43d77c01405cba4 | 5.41 → 5.26 → final **€5.21 @ 45 d, 24 m + AS-14404 clause db0** (it added the clause itself, like P18); accepted as cheapest by C |
| P02 | 0.44 | 0.48 | d0c627ec43ba1f5d | v2.6 fix worked (0.27 → 0.44): no cherry-picked calc; 373.88 → 372.45 @ 90 d |
| P10 | 0.64 | 0.65 | b9e6766299dada92 | final in round 1 again: €32.00 @ 56, 36 m (its floor ~€31.90) |
- Mean of the 4: **0.61**. The full v2.6 stack (structure + dynamic + personas/RAG + Parth's features) ran 4 sessions in
  parallel on the Mac + Astra without timeouts: the Live Final shape works.

### v2.7 (offline): index-clause lever + no checked rises inside the cost calc
- **Clause lever**: `index_clause` options are part of the search; once the supplier adds a clause to every sheet
  unasked (P08/P18: always after round 0, 8/8 games incl. teammates') → `clause_required`; the deadband premium is
  learned from its own sheets (P08: €5.26 @ db0 vs €5.38 @ db5, same 45 d → **€0.024/kg per deadband point**; P18 alike)
  and `total_cost` picks the deadband cheapest for us. Replay of the real P08 game: after its clause the agent offers
  db5 at €4.80–5.07. **Honest finding:** at its own deadband prices db0/db3/db5 are worth ~the same to us
  (0.647 / 0.644 / 0.643): the €31k clause cost in P08 was mostly unavoidable once it insisted.
- **Cost calc cites IDs only for indices that fell/stayed flat**; rising ones in plain text (P08 v2.6: "Your figures
  confirm our case: that driver rose"). P08 refs now: AS-14404 only.
- Tests 32 passed; offline 0.939 / 0.947; Astra P08 trial clean (10.3 s per call).
