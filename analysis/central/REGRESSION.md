STATUS: DONE (task 5) - 2026-10-10 evening, cloud session, offline only (no arena, no LLM).
Run on main at 1e48029 (v2.16b) + this branch. Commands (from tacto/starter-kit):
`uv run python ../../analysis/tools/variant_check.py ../../analysis/agent_variants/noidea_neel.py` (column "v1.5" = the
CURRENT arena_kit/agents/noidea.py, not v1.5) and `uv run python ../../analysis/tools/sim_selvbrunn.py <agent file>`.

# Regression check: noidea.py (main agent) vs noidea_neel.py (variant)

## 1. variant_check.py (3 simulated suppliers, 9 probed cases)
| case | Dhruv sim responsive | Dhruv sim stubborn | floor-stop (P04-calibrated) |
|---|---|---|---|
| P02 | 1.00 -> 1.00 | 0.98 -> **0.86** | 0.92 -> 0.92 |
| P03 | 0.96 -> 1.00 | 0.96 -> 0.99 | 0.96 -> 0.98 |
| P04 | 0.99 -> 1.00 | 0.99 -> 0.98 | 0.81 -> 0.86 |
| P05 | 0.76 -> 0.76 | 0.76 -> 0.76 | 0.76 -> **0.00** |
| P07 | 0.95 -> 0.94 | 0.96 -> **0.91** | 0.95 -> 0.97 |
| P08 | 0.92 -> **0.88** | 0.92 -> 0.90 | 0.99 -> 0.99 |
| P10 | 0.97 -> 0.97 | 0.97 -> 0.98 | 0.94 -> 0.97 |
| P11 | 0.97 -> 0.98 | 0.97 -> 0.98 | 0.99 -> **0.80** |
| P18 | 0.94 -> 0.94 | 0.94 -> 0.94 | 0.94 -> 0.94 |
| **mean** | 0.941 -> 0.941 | 0.940 -> **0.923** | 0.918 -> **0.827** |
P04 stress test: 25 near-live suppliers 0.844 -> 0.884 (better); **36 broad types 0.853 -> 0.804, worse in 7, min 0.52**.

## 2. sim_selvbrunn.py (P03 replay supplier, 3 scenarios)
| scenario | noidea.py | noidea_neel.py |
|---|---:|---:|
| base | 0.909 | **0.913** |
| kam_only (ignores the committee request) | **0.810** (9 rounds, ends 429.37 @ 14 d) | 0.906 |
| house (committee as low as the house) | 0.934 | **0.938** |

## 3. Cases that got worse, and why (diagnosed)
1. **P05 floor-stop 0.76 -> 0.00 (variant): it never closes.** It sends until the round limit and ends in a timeout
   (11 rounds; the main agent takes a deal in round 1). Risk on ANY supplier that stalls without saying final_offer:
   the variant needs an accept rule near the round limit / near its standing price.
2. **P11 floor-stop 0.99 -> 0.80 (variant): it keeps a EUR 500 chargeback** in its sheet, so the supplier prices it
   in (EUR 45.08 vs 43.83 at chargeback 0). The main agent has v2.16's "chargeback at its real defect rate / follow its
   best-priced structure"; the variant does not. Port that rule.
3. **Stubborn sim P02 0.98 -> 0.86, P07 0.96 -> 0.91, P08 0.92 -> 0.88 (variant):** the bigger mirror steps give value
   away when the supplier does NOT mirror (stubborn r = 0.10). Gate the 30% step on the mirror signal
   (`engine_rules.classify` = mirror), keep small steps otherwise.
4. **P04 broad types 0.853 -> 0.804 (variant):** near-close settles early against very patient suppliers (known since
   Update 1 of analysis/agent_variants/README.md).
5. **Main agent, P03 kam_only 0.81:** in round 4 noidea.py hops from 90 d to 60/45/30-day sheets (no data left), the KAM
   re-prices at 60 d and the game slides to EUR 429.37 @ 14 d in 9 rounds. The same structure hop that cost P02 0.30
   (model-read "refusal" / no-data fallback). The variant holds 90 d. Also: noidea.py never cites should-cost
   (cost:350020) on P03; the variant does (+EUR 0.79 per the P03 engine).

**Bottom line:** neither agent dominates. Before the final: (a) give the variant a close rule (fixes P05); (b) port v2.16's
chargeback rule into the variant (fixes P11); (c) gate big steps on the mirror signal; (d) in noidea.py, never leave the
structure the supplier priced when no new data is left (fixes P03 kam_only).
