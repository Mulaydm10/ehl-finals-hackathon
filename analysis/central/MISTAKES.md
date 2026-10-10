STATUS: DONE (task 11, step 1) - 2026-10-10 evening, cloud session, offline only (0 arena sessions, no LLM calls).
Sources: every archived game (datasets/runs, tools/replays/raw, backoffice; all cases, all agent versions, teammates' too),
agent_changelog.md, quota_log.md, GENERAL_RULES.md, LEARNINGS.md, REGRESSION*.md, VARIANCE.md, FINAL_TRIGGER.md, ENGINES.md.
"main" = `analysis/agent_variants/noidea_neel.py` at d488bf0. "cloud" = `noidea_neel_cloud.py` on this branch (main + the fixes below).
Points: per game, from paired games or the exact cost model. Score per 1% of price: P08 0.011, P18 0.0065, P07 0.0065, P04 0.17, P11 0.0017.
"est." = estimate.

# Every mistake we made, ranked by points lost

## A. Latent defects still in main (found by feeding archived games through the agent offline)

| # | case | mistake | evidence | loss | status |
|---|---|---|---|---:|---|
| **L1** | P04, P10, P18 (any supplier whose alternative is cheaper) | at final_offer / agreed, `best_sheet` picked the cheapest sheet **including its '-a' alternative**. The arena refuses '-a' ids (422, P05 d9af85e0); `play.recover_close` strips the id; the stripped sheet is still the cheapest -> `sheet_id` None -> the final_offer branch **walks** | old code picks '-a' at **9 of 33** archived finals with 2+ sheets: P04 d3050f95 (0.86), P10 2d91214c, 675fc6b9, P18 a99d02eb (0.62), 06f8f4f5, 6833e98f. All 112 archived deals were on the primary | the whole deal (0.4-0.9) in ~1 of 4 such finals | **FIXED in cloud**: `best_sheet` accepts only primary ids; alternatives still reach us via `prose_alternative` |
| **L2** | P10 (capacity) | round 1 asked **lead 35** (need 42; its quote 54): `supplier_value` has no lead-time premium, so 35 tied and won | 675fc6b9: "technically unfeasible", final 35.00 @ 35 = 0.46 | 0.19-0.24 | **FIXED in cloud**: capacity-tight suppliers never get a lead below their quote (now 56) |
| **L3** | P07, P18 | `approval_ladder` -> longest contract -> **36 m** | P07 0f754b13: 36 m priced higher, 0.65 vs 0.695-0.70 at 24 m; P18 raw material = P08 logic (36 m buys nothing on a 2-year horizon) | P07 ~0.045 | **FIXED in cloud** for bundling / raw material (P10 capacity keeps 36 m: Parth's 0.70 probes were 36 m; P03 keeps it) |
| L4 | P05 (RFQ) | rival citation could name a DEARER bid ("38.50" to a bidder at 36.00) | 993222d5: "does not change our calculation" x2 | part of row 13 | **FIXED in cloud**: cite a rival only if it is cheaper than this bidder |
| L5 | P08 (minor) | "stay on its structure" falls back to our top sheet when its structure is not in our top 3 (P08 replays: 90 -> 60 / 45 d) | neutral: payment days ±0.005 at equal value | ~0 | not fixed (neutral) |

## B. Mistakes from live play, ranked by points lost (status in cloud)

| # | case | mistake | sessions | n | points lost | status |
|---|---|---|---|---:|---:|---|
| 1 | P07, P08, P05 | **pushed after final_offer -> it walked** | P07 c5d84588 (0.70 -> 0.12), P08 1f27ac1b (~0.48 est.), P05 d9af85e0 | 3 | **~1.1** | FIXED (accept at final; and L1 closed the way back to it) |
| 2 | P02 | **remark about its departments / repeated objection -> walk** | 4d18bd11, 150fb1c1 (~0.50 each) | 2 | **~1.0** | FIXED in cloud: prompt rule "never comment on their departments, colleagues or internal processes"; 0 walks in Neel's 7 P02 games |
| 3 | P02, P03 | early games: no checkable data in round 1, empty rounds ("Which figures is that based on?"), committee asked after "I hold full authority", 3 payment sheets -> KAM stopped at its 2% on 60 d | P02 6e7579c3 (0.22); P03 fef482f4, 78f03f1c (0.86), 1db1ce07, ff7b0d58, 32c6fd97 (0.90) | 6 | **~0.95** | FIXED (should-cost vs quote, latest forecast, steepest falling window, fillers, full-authority check, one sheet to the committee) |
| 4 | P02, P03, P04 | **structure hops** (payment days changed after it priced one) | P02 159def0f, dc1d4fd8, ef17b16a (30-day finals, ~0.30 each); P03 47a88b4d (0.04); P04 5f80eb75 (0.05) | 5 | **~0.83** | FIXED (code sets sheets, holds its structure) |
| 5 | P08 | round 2: **took its clause or asked db5** (-0.05 to -0.09, or a hold) instead of clause-free (-0.15 to -0.17) | ab473a1c, 325d6e71, 586a9adf, 9bfa8610, 1f27ac1b | 5 | ~0.56 (est.) | FIXED (no index clause in our sheets) |
| 6 | P11 | chargeback locked or priced as free; left the 300 ppm / EUR 0 structure it had priced | a6cb7ced (0.31), 0d5bc007 (0.10), 29cbb6d6 (~0.08) | 3 | ~0.50 | FIXED (chargeback at real ppm, ALT_BAND 0.3%) |
| 7 | P02 | **small steps against a mirroring supplier** | de6192e3 (0.657), a1e2a4ac (0.669) vs 0.847 | 2 | ~0.37 | FIXED (MIRROR_SHARE 0.40 + MIRROR_GATE) |
| 8 | P10 | asked a lead time below need / below its quote | 675fc6b9 (35: 0.46), afd996e3 (42: 0.54) | 2 | ~0.35 | **FIXED in cloud** (L2) |
| 9 | P02, P11 | **contradicted claims**: four numbers in one QN sentence; "18,558" read as 18.558 | f778b35c (0.61 vs 0.85), fa9a9d02 (~0.08) | 2 | 0.32 | FIXED (figure-free QNs, one number per claim sentence, no thousands separators) |
| 10 | P08 | cited the hedged AS-14404 ("not our reality"); no 90-day round-1 sheet | 1f27, 325d, 586a, 9bfa, ab47, a43d | 6 | ~0.30 (est.) | FIXED (hedged series excluded; 90-day headline guaranteed) |
| 11 | P05 | accepted the dearest bid / not the closing bidder | f8604d43 (0.22), 993222d5 (0.03) | 2 | 0.25 | FIXED (closing bidder first) |
| 12 | P10 | **deep anchor -> round-1 final at 31.90-32.00** instead of 31.20-31.56 after a credible ask | b9e67662, 396a494d, 582e0e73, f0a505fc, 0bba4ffd | 5 | ~0.25 (0.03-0.06 each) | **FIXED in cloud**: capacity-tight anchor = today's price (29.89, Parth's probe B = 0.702) |
| 13 | P05 | anchor on the bidder's own opening, not the market; dearer rival cited | 993222d5, 26c6afc9, 798c7367 (0.53 vs 0.61) | 3 | 0.24 | PARTLY (dearer rival fixed, L4); market anchor not in Neel's agent (Dhruv's noidea.py has the 10% market anchor, 0.61) |
| 14 | P02 | cherry-picked 6-month cost window ("full twelve-month cost pressure") | c52de025 (0.27 vs 0.48) | 1 | 0.21 | FIXED |
| 15 | P18 | offered the clause (it took db3 and froze); cited PPI +9.7% ("confirm our case") | bf73ee39 (0.44 vs 0.62) | 1 | 0.18 | FIXED |
| 16 | P11 | MESOs + premium extrapolated beyond the priced range -> accepted in round 2 | f5157e0d (0.54) | 1 | 0.17 | FIXED (Dhruv v2.16j; not in Neel's agent at all) |
| 17 | P04 | near-close 0.2% refused; landed on 60 d (0.81) not 90 d (0.86); 3 payment sheets in msg 1 | 5f80eb75 | 1 | 0.05 (+0.09 per P04_plan) | PARTLY (CLOSE_STEP 0.08%); one-90-day-sheet recipe NOT in code |
| 18 | P11 | grid probe + own late-payment admission not in Neel's agent | b1f94bfe 0.777 / 858230b 0.794 vs 0.71 | - | ~0.05 per game (est.) | NOT FIXED in Neel's agent (Dhruv's noidea.py v2.18 has it) |
| 19 | P03 | stale forecast / outdated index window / data ran out | d1bfa5a9, 27e05be0, 3091eac9, 2e4bf89a | 4 | 0.05 | FIXED |
| 20 | P11 | accepted an OPEN offer with facts left | 352bdb04 | 1 | ≤0.06 (est.) | FIXED |
| 21 | P08 | final at our 3rd message with a normal step (no deferral) | 9 of 10 games | - | ~0.05 per game | FIXED (deferral 0.18x: live 2 of 2 deferred, db7d315a, 6912fd89) |
| 22 | all | rising index cited ("confirm our case"); 2+ index claims ("a lot of material"); empty rounds | a43d77c0, d3050f95, 0f754b13, 675fc6b9, bf73ee39, c52de025, e3e0b7be, cae4b621 | 8 | ~0 separable | FIXED |
| 23 | P01 | model priced above its ask (pre-agent) | b04caaf8 | 1 | 0.85 | FIXED (code sets numbers, cap at its price) |
| 24 | P05, P02 | timeouts / stale ids (422) -> bidders walked | d88810ba, d9af85e0, 94dea31d | 3 | ~0.6 | PARTLY: play.py resync + parallel sends (kit); Neel's agent has no `focus` |
| 25 | P08 | first counter is a per-session coin flip (5.34-5.39 vs 5.46-5.51) | 5 of 11 high | - | ~0.13 per high game | NOT FIXABLE |
| 26 | P11 | first counter coin flip (46.00 vs 46.50) | 7 of 10 high | - | ~0.08 per high game | NOT FIXABLE |

## C. Not fixed, worth > 0.01, and the fix

| mistake | fix | why not done here |
|---|---|---|
| 13 P05 market anchor | anchor at min(own opening, market low x 0.90); keep 2 bidders alive | RFQ logic lives in Dhruv's noidea.py (0.61); Neel's agent is not the RFQ player |
| 17 P04 recipe | floor-stop supplier: one 90-day sheet in msg 1, near-close at msg 2 (P04_plan.md, +0.05-0.09) | needs a floor-stop detector in Neel's agent (engine_rules.classify) - untested; P04 is deterministic, so 1 live game decides |
| 18 P11 grid probe / late-pay | port `price_grid` + `own_late_pay` from noidea.py v2.18 | large port; Dhruv's agent already plays P11 at 0.78-0.79 |

**Replays** (`replay_cmp_cloud.py noidea_neel.py noidea_neel_cloud.py`, every archived game, 68 threads):
- **SAME**: all P01, P02 (13), P03 (13), P04, P05, P11 (8 incl. the latest b1f94bfe) and P08 c387 / cae4 / 1363 / db7d.
- **Changed by design**:
  - P07 and P18: 24 m instead of 36 m (P18 a99d02eb: the contract length is the only change);
  - P10: lead 56 and anchor 29.89 in round 1;
  - P08 a43d: round 2 on its primary's 45/60 d structure instead of the alternative's 14 d.
- The L1 walk can't be replayed (it needs the arena's 422). Checked directly instead: at the 9 finals, `best_sheet` now returns the primary.
- P08 sim is unchanged: 0.792 low / 0.666 high.

**Conclusions.**
1. The two big losses are fixed: pushing past a final (~1.1) and P02 department remarks (~1.0). But main still has a hidden walk (L1): at 9 of 33 past finals it would accept a refused '-a' sheet and then walk.
2. Cloud fixes for main to port: L1 primary-only accept, P10 lead/anchor, 24 m for P07/P18, cheaper-rival-only, and the departments prompt line. P02, P03 and P11 replays are SAME.
3. Not fixable: the P08 and P11 first-counter coin flips (~0.13 and ~0.08 per high draw).
