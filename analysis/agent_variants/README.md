# Agent variants (Neel)

`noidea_neel.py` = Dhruv's `noidea.py` v1.5 (`ef489c6`) plus the lessons from the live P04 game
(`d3050f951dc2c45b`, 0.86). Dhruv's file is unchanged; merge what you like.

## What went wrong live on P04 (0.86)
| round | we offered (cash value to it) | it answered (cash value) |
|---|---|---|
| 1 | €4.79–4.84 (≈ 4.81) | €4.91 @ 60 d (4.877) |
| 2 | €4.80–4.88 (≈ 4.82) | €4.94 @ 90 d (4.874), moved only 5% of the gap |
| 3 | €4.81–4.89 (≈ 4.83), still ~1% below it | **final_offer** €4.94 @ 90 d → we accepted: 0.86 |

Its floor (from C_best) is a cash value of **€4.8667**. It stopped 0.15% above it. Asking for just one cent less on
the right payment term would have scored 0.94–0.99: €4.85 @ 14 d (0.99), €4.90 @ 60 d (0.98), €4.87 @ 30 d (0.94).
At 90 d the cent grid lands badly (€4.93 is below its floor, €4.94 = 0.86). **On P04 one cent = 0.17 score.**

## Changes
1. **Near-close** (`value_target`, `decide`, `sheets_at`): when the supplier **stalls** and we're within 1.5% of
   it, ask for **0.2% below its standing cash value**, price each structure **up** to the next cent, and send only
   the sheet(s) cheapest for us (it may pick any sheet we send). If that's no better than its standing sheet,
   accept. Stall = its last move as a share of the gap to our ask fell below ⅓ of its previous share (or < 2%);
   a big move *up* (structure switch) is not a stall. Constants: `CLOSE_STEP 0.002`, `STALL_DROP 1/3`,
   `STALL_MIN 0.02`, `STALL_NOISE 0.10`, `CLOSE_GAP 0.015`.
2. **Only cite indices that fell or stayed flat** (`rank_args`). Live P04: bearings +0.6% and labour +1.7% →
   *"Your figures confirm our case: that driver rose… That does not change our position."* (also P02 offline:
   steel +6.2% cited against us).
3. **Cost breakdown asked once:** the `open_book` lever goes to the LLM only in round 1, and the code's own
   question is skipped if the LLM already asked. Live P04: the 2nd ask got "company policy, we do not share…".
4. **UTF-8 file reads** (Windows garbled "WÃ¤lzlager"), **"Write in English only."** (Astra wrote German once).
5. `_repo()` finds the repo by looking upward for `datasets/A_dossiers.json` (works from either folder).

## Evidence (offline, 0 arena sessions) - `analysis/tools/variant_check.py`
New simulator `analysis/tools/sim_floorstop.py`, calibrated on the live P04 game. It reproduces it round by
round with v1.5 (€4.91 @ 60 → €4.94 @ 90 → final → **0.86**).

| check | v1.5 | variant |
|---|---:|---:|
| P04, live-calibrated supplier | 0.86 | **0.98** |
| P04, 25 suppliers near the live one: mean / share ≥ 0.93 / min | 0.889 / 7 of 25 / 0.81 | **0.982 / 25 of 25 / 0.98** |
| P04, 36 broad supplier types: mean / share ≥ 0.93 | 0.815 / 12 | 0.823 / 14 |
| 9 cases, offline_eval responsive (mean) | 0.931 | 0.931 |
| 9 cases, offline_eval stubborn (mean) | 0.939 | 0.939 |
| 9 cases, floor-stop sim (mean) | 0.822 | 0.836 |
| P04 with gpt-6-astra writing, calibrated supplier | – | **0.98** (€4.90 @ 60 d, 36 m) |

No case is worse in any of the three simulators. **Known weakness:** against a *very patient* supplier (it
holds its stop 2 extra rounds while we creep up), near-close settles 0.2% above its floor where v1.5's creep
reaches it (worse in 5 of 36 broad types, e.g. 0.99 → 0.94). Real suppliers so far (P04, P07) said
`final_offer` soon after stalling, so near-close fits them.

**Risk to watch:** change 2 removes all *rising* index claims. P01's 0.85 game cited labour +2.7% together with
the notice period and energy −3.7%; with the variant P01 would cite notice + energy only. Untested live.

## How to run it live (needs a decision; uses practice quota)
`analysis/tools/play_variant.py case:Pxx analysis/agent_variants/noidea_neel.py` runs it with the kit's own
`play()` loop (1 practice session; saves the session to `tools/replays/raw/` and logs it). For the final, Dhruv
merges what he wants into `noidea.py` (or adds `--agent-file` to `arena play`).

## Update 2 (after live P04 run 5f80eb75c793f352 = 0.81, and P03 offline runs)
- Live P04 with the 0.2% near-close: **0.81**. It refused €4.85 @ 14 d / €4.90 @ 60 d ("we must maintain our price")
  and went final on €4.91 @ 60 d. Its stop sits ~0.15% above the C_best floor → `CLOSE_STEP` now **0.08%**
  (offline: closes on €4.89 @ 45 d = its own standing value on a better term, 0.874).
- Accept rule "within 0.05% of our ask" no longer fires in a closing round (it pre-empted the close).
- **Committee tie-break** (`approval_ladder` / `price_frozen`): among sheets within `TIE_BAND` 0.01% of our best
  cost, lead with the smallest headline cut. 0.015% / 0.05% made P02 worse (0.94 → 0.86), 0.01% made it better.
- **Call-off schedule CSV** attached in round 1 and whenever it asks for volumes / a release schedule.
- **Offers in words** ("option A: EUR 427.92 per unit, 60 days net, 36-month contract, 4,580 units per year").
- `variant_check.py`: no case worse than v1.5 in any simulator; P02 0.94 → 0.98 / 0.93 → 0.96.
- Lessons from all saved sessions: `analysis/replay_lessons.md`.

## Update 3: German business style + anchor (P03 final offline run)
Source: negotiationacademy.com "How to negotiate with Germans" (the ZEIT article could not be fetched: blocked
for the fetch tool, HTTP 403, not in the Internet Archive). Applied:
- **Prompt:** 1-2 sentences, get to the point, direct and specific, no hedging / flattery / small talk / jokes /
  emotional appeals ("facts over emotions"); acknowledge their approval rules plainly.
- **Agenda:** numbered e-mail: 1. volume and term (incl. total units), 2. our proposal in words + total value of
  option A over the term (specific, measurable), 3. basis (arguments), 4. next step ("All other terms as in your
  quote; on your written confirmation of one option we will issue the order": no details left open).
- **Formal address by full name** from its signature ("Dear Birgit Mayrhofer"; general German business convention,
  not from the article; no Ms/Mr guessed from a name).
- **Stabilise anchor 3.0% → 3.5%** below the opening: P03 0.96 → 1.00 in all three simulators, P02 0.94 → 1.00 /
  0.93 → 0.96; 4-5% was worse. Regression check: no case worse than v1.5 anywhere.
- **Bug fixed:** `say()` formatted every field at once; a date (P01 `effective_date`) crashed the e-mail.

| P03 offline | run 1 (before) | run 2 | final run |
|---|---|---|---|
| deal | €426.49 / 45 d / 36 m | €427.92 / 60 d / 36 m | €426.61 / 60 d / 36 m |
| sim score | 0.96 (round 1) | 0.96 (round 1) | **1.00** (round 2) |
| with relationship charge (full cost €390-403) | 0.83-0.96 | 0.83-0.96 | **0.83-1.00** |

## Update 4: central layer (`central.py`, `analysis/central/LEARNINGS.md`)
Shared learnings from 54 live games + Dhruv's and Parth's notes + the simulators, read by `noidea_neel.py`:
- **Calibrated supplier** (`analysis/tools/calibrate_suppliers.py`): hidden full cost and cash rate fitted on the
  relationship charge of real deals (P02 EUR 367.60 / 6.6%, P03 EUR 395.30 / 6.1%, both exact to the cent). With it,
  the "never below its full cost" guard is skipped (it pinned P02 at 0.51) and sheets rank by the exact charge.
- **Data that suppliers take into account** (`analysis/tools/mine_claims.py`): should-cost vs its *quote* and a
  rising volume forecast are now cited in round 1. Kinds this supplier already shrugged off (P03: price history) are
  dropped, and rising indices are never cited.
- **Approval ladder:** one structure to the committee in round 1, then stay on the structure it priced.
- P03 replay supplier `analysis/tools/sim_selvbrunn.py` (rules from the 7 live games): 0.913 base, 0.906 if it
  ignores the round-1 committee request, 0.938 if the committee goes as low as the house agent's deal.
