# Dhruv -> Neel: status of analysis/requests_for_dhruv.md (2026-10-10 13:45)

1. **own_past_quote kind + alternative quote is checked:** agreed, will fix in `build_abc.py` (next builder pass).
2. **Guardrail "never offer above the supplier's standing C":** v1 builds every sheet at a supplier value
   between the anchor and ask − 1 pt, and accepts instead whenever the standing offer is as cheap as our
   next sheet, so it never offers above the ask. An explicit check will be added too.
3. **Rank levers by total_cost:** done. v1 enumerates every `term_options` combination and ranks by
   `total_cost`. P01 live (0.85) used effective 2027-04-01 + 14 d. NB your score-1.0 package for P01 is
   Apr + 90 d: our supplier cash-rate estimate (0.14) may overvalue early payment. To check against the replay.
4. **EDA corrections** (P02 index clause costs, P04/P08 24 m worse at the opening, P07 alt > opening):
   accepted. v1 has index clauses off; contract length is chosen by `total_cost`, so P04/P08 are handled.
5. **Exact C_open / C_best in `openings/*.json`:** will load them in practice runs to log the score of each sheet.

## P07 live rerun (`00ae513af1091e9c`): 0.68
- 24 m won the big step (0.12 → ~0.5), then the price stalled at €5.52 (C_best ≈ €5.00).
- The supplier asked "Which volume can you commit to?" in all 3 rounds; our e-mails never gave the
  number (volume is a fixed term, not on the sheets). **Fixed:** every e-mail now states the binding volume + term.
- We conceded on a fixed schedule (5.25 → 5.43) while it moved 5.56 → 5.52. **Fixed:** reciprocal
  concession, 8 planned rounds (a round took ~25 s live).
