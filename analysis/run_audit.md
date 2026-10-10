# Audit of all saved arena negotiations (33 real negotiations, 8 cases; 2026-10-10 ~16:40)

Script: `analysis/tools/run_audit.py --house` (offline, reads `tools/replays/raw/`). House = Tacto's reference agent (`/v1/live`).

| case | house | our best | gap | games | what happened |
|---|---:|---:|---:|---:|---|
| P01 | 0.966 | 0.853 | −0.11 | 3 | best game used verified notice + energy data; 9 `duplicate` claims; one game offered €142.50 above its ask (0.00) |
| P02 | 0.740 | 0.476 | −0.26 | 4 | supplier plateaus at 0.29-0.51 then `final_offer`; committee/authority signals; rising data backfired once |
| P03 | 0.925 | 0.900 | −0.03 | 5 | stops at €431.61 / 60 d (0.87); escalation → €433.08 / 90 d (0.90) every time |
| P04 | 0.860 | 0.860 | 0.00 | 2 | final at its stop; near-close asked too much once (0.81) |
| P07 | 0.782 | 0.728 | −0.05 | 8 | final lands at ~0.70 in 7 games; it asks for volume/data every round, never answered with data; 1 walk-away after pushing a final |
| P08 | 0.752 | 0.647 | −0.11 | 1 | rising data backfired; breakdown refused |
| P10 | 0.686 | 0.647 | −0.04 | 6 | **`final_offer` in round 1 in all 6 games**; one game accepted the worse of its two sheets (0.47 vs 0.66) |
| P18 | 0.386 | 0.618 | +0.23 | 4 | beats house; one game accepted the db0-clause sheet while a db5 sheet scored more (0.43 vs 0.49) |

## Mistakes, by cost
1. **Accepted the first sheet, not the best one in the same e-mail** (v1.x `standing()` reads `term_sheets[0]` only):
   P10 `675fc6b9c1c8c291` took €35.00 / lead 35 (0.47) while `offer:70410-1-a` €32.00 / lead 54 stood next to it
   (0.66): **−0.19**. P18 `6833e98fbbe5ebdf` took the db0 index clause (0.43) over the db5 sheet `-3-a` (0.49): **−0.06**.
   Suppliers sent 2 sheets in 14 of 33 games. Fixed in `noidea_neel.py` (`best_sheet`); **not yet in `noidea.py`**.
2. **Changing the structure after the supplier moved our way**: P03 `47a88b4d0bb75ce3` held €433.08 / 90 d (0.906),
   we asked for 60/45/30 d, it reverted to 0.868 final. P04 `5f80eb75c793f352` 0.86 → 0.81 the same way. Fixed in variant.
3. **Offering above the supplier's own price**: P01 `b04caaf8824a9871` €142.50 vs ask €138.55 → 0.00 (stock LLM agent).
4. **Pushing after `final_offer`**: P07 `c5d845883158676c` asked 90 d at its final price → walked, 0.12. Fixed (v1.4+).
5. **Questions left unanswered** - "Which volume can you commit to?" / "Which figures is that based on? Please send us
   the data" in **17 of 33** games each; P07's final stuck at ~0.70 in 7 games while it kept asking for the data
   behind "5x our business" and a release schedule. Variant attaches a call-off CSV; computed claims still lack data.
6. **Rising data cited** ("Your figures confirm our case") in 8 games; **re-cited IDs / padding** ("lot of material")
   in 12 games. Variant cites only falling/flat indices, each ID once.
7. **Cost breakdown asked again after a refusal**: 11 games. Variant asks once.
8. **Letting the supplier end the game**: in 28 of 33 games the last supplier status was `final_offer` and we
   accepted it; 10+ of those plateaued well below the house (P02 0.29-0.51). We have no move that reopens a
   plateau except escalation (P03: +0.04, works).
9. **P10 opening triggers an immediate final** (6 of 6): our first sheet asks lead 35/42 or a price far below its zone
   ("technically unfeasible", "requires a premium"); it answers `final_offer` at once and the case is over in 1-2 rounds.
10. Not a mistake but worth knowing: 0 timeouts in 33 games; the 60 s limit is not an issue.
