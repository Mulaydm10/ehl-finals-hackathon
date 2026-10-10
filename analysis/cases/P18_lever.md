STATUS: PARTIAL - HANDOFF (cloud credits almost out) - 2026-10-11, cloud session, offline only (0 arena sessions, no LLM).
Done: record decoded, scorer exact, payment-day pricing measured, levers ranked. NOT done: agent `noidea_p18.py`, sim, replays -
the local side takes over from §6.

# P18 (Werdenfels): the record is 4.90 @ 45 d; Werdenfels charges ~EUR 0.10/kg per 30 days of payment, 3x what it is worth to us - stay on 14 d

## 1. The record, decoded (C_open 295,173.23, C_best 222,651.27; scorer reproduces all 19 live P18 deals to the cent)
| team | EUR saved | score | deal (only exact C match) |
|---|---:|---:|---|
| **Codacabana** | 54,823 | **0.75595** | **4.90 @ 45 d, AS-14404 clause db0**, 24 or 36 m (C 240,350.39) |
| NoIdea (0c968aae, Dhruv v2.28) | 52,729 | 0.72708 | 4.91 @ 14 d, db0, 24 m |

P18 is `leverage`: no relationship charge, so the score is our own cost only (price, payment interest at 8% vs 60 d, clause).

## 2. What beats it (24 m; max price with score > 0.75595)
| clause | 14 d | 30 d | 45 d | 60 d | 90 d |
|---|---:|---:|---:|---:|---:|
| db0 (its default) | 4.86 | 4.88 | 4.89 | 4.91 | 4.94 |
| db3 | 4.93 | 4.94 | 4.96 | 4.98 | 5.01 |
| db5 | 4.97 | 4.99 | 5.00 | 5.02 | 5.05 |
| no clause | 5.01 | 5.03 | 5.05 | 5.07 | 5.10 |

## 3. The open question: how much does Werdenfels charge for longer payment?
**About EUR 0.10/kg for every ~30 days** (≈2% a month, ~24%/yr implied; its standard is 30 d; "A longer Zahlungsziel costs us
interest; that is priced in"). For us 30 days are worth only ~EUR 0.033/kg (8%/yr), so each extra 30 days costs us ~EUR 0.067/kg net
(~0.045 score). **Stay on 14 d.**

| evidence (same reply, two sheets, or same data in round 1) | result |
|---|---|
| 14 d vs 45 d, same reply (c4599331 r1+r2, 92616dfb r1+r2, 9d4d288e r1) | 14 d **0.10 cheaper**, 4 of 4 (r1 pairs via db5 = db0 + 0.10) |
| 14 d vs 30 d, same reply (06f8f4f5 r3, 928a3878 r2; 06f8 r2) | 14 d 0.10 cheaper 2 of 3 (equal once) |
| 60 d vs 30 d (6833e98f r2, r3) | 60 d **0.10 dearer** (2 of 2) |
| 90 d vs 45 d (6833e98f r1) | 90 d 0.10 dearer |
| round-1 counter, best data (AS-14404 2024-11, PPI-C2431 2026-06, price path) | 30 d: 5.20 (2 of 2); 45 d: 5.30 (3), 5.40 (1); 14 d: 5.20 (1) |
| round 2 switch 30 -> 14 d (+ forecast) | 5.20 -> 5.00 (0c968aae, a09d9536) vs 5.20 -> 5.10 when staying at 45 d (3cb62cb9) |

So in its own terms the record's 4.90 @ 45 d ≈ **4.80 @ 14 d**: Codacabana's session ended about one grid step below ours.
Longer payment beats 14 d only if Werdenfels charges < EUR 0.033/kg per 30 days - never seen.

**Clause:** its db5 alternative is always db0 + EUR 0.10 at the same payment (~15 pairs). db5 saves us 2.25% (~0.11/kg), so
**db5 at +0.10 is ~0.01/kg better: take it when offered.** It never accepted no clause on 24 m (21 of 21 games).

## 4. How it moves (21 games)
- Opening 6.10 @ 30 d / 12 m, no clause. It counters on a **EUR 0.10 grid**, always with the AS-14404 clause.
- **Round 1**: 5.20 with the best three facts (AS-14404 -8.5% 2024-11 -> 2025-10, PPI-C2431 2026-06, our price path
  5.26 -> 5.84); 5.30-5.60 with weaker data. Same e-mail can draw 5.20/5.30/5.40 (per-session draw).
- **Mirror**: ~EUR 0.10 per round when we step ~0.10 (0.20 when we step ~0.19 or switch to 14 d); final at our 3rd-4th message.
- It sometimes **agrees at our ask** when we are within ~0.09 of its offer (0c968aae 4.91 vs 5.00; a09d9536 4.94), sometimes not
  (a665044e 4.96 vs 5.00 -> final 5.00).
- **Never send an identical e-mail without a new fact**: fe806698 walked away (0.0). v2.34f fixed this in main.

## 5. Levers ranked (to reach <= 4.86 @ 14 d db0, or <= 4.97 db5)
| # | lever | cost to us | evidence | status |
|---:|---|---|---|---|
| 1 | 14-day payment from round 2 | 0.69% vs 45 d (~0.034/kg) | it gives ~0.10/kg | in main (v2.28) |
| 2 | **36-month move held back for round 3, stacked with a new fact** (rule 10b) | none (horizon 2 y: C identical) | P10 rewarded the move -0.10 to -0.30; Werdenfels "focus on customers with volume" (M2, M4, M5). **Never tried on P18** | untested, best new idea |
| 3 | take db5 when offered at +0.10 | - | +0.01/kg | free |
| 4 | lower round-1 anchor | risk: "unrealistic" | mirror meeting point ≈ (P1 + 0.9 x A1) / 1.9: A1 4.76 -> ~4.94; 4.50 -> ~4.82 | untested |
| 5 | QN qn:20004916, other parts' price jumps | - | verified elsewhere; ~0 beyond the mirror | weak |
| - | 70710's quote 5.45 (quote:7300008) | - | outside the case refs -> "irrelevant" (rule 10d) | don't |
| - | 90 / 60 / 45 d | costs ~0.067/kg per 30 d net | §3 | don't |

## 6. Suggested plan for the local side (not built)
1. msg 1 @ 30 d / 24 m, ask 4.76, facts: AS-14404 -8.5% (2024-11 -> 2025-10), PPI-C2431 (2026-06 window), price path -> expect 5.20.
2. msg 2 @ **14 d**, + forecast, ask ~4.87 -> expect 5.00 (2 of 2).
3. msg 3: **36 months** (71,100 kg) + labour index, ask ~4.80 (stay ≥ 0.10 under its offer) -> hope 4.80-4.90.
4. Accept its final; if it offers db5 at +0.10, take db5. Expected: 4.90 @ 14 d (0.733) without the move cut; 4.80 (0.80) if
   the move cuts like on P10. Beats the record only if the 36-month move (or a lucky agree-at-ask) gives one extra grid step.
Tools: exact scorer = `total_cost(case, complete_offer(case, terms), std, est)` (no relationship charge on P18).

## 7. Live (local, 2026-10-11 01:09, fd5b66b1c9f06fc0, `analysis/agent_variants/noidea_p18.py`): **0.621 - the 36-month move is worth 0 on Werdenfels**
| our msg | sheet | its answer |
|---:|---|---|
| 1 | main: ONE sheet 4.77 @ 45 d / 24 m (the model picked 1 of 3) + AS-14404, PPI-C2431, price path (3 verified) | 5.30 @ 45 d (the high round-1 draw) |
| 2 | 4.85 @ 45 d (main's 4.93 shifted -0.08), forecast (shrugged) | 5.20 @ 45 d (-0.10) |
| 3 | **36 m** + labour index, ask 4.89 @ 45 d (the beat price on 45 d) | **5.20 held**: "We can extend the contract term to 36 months at our lowest possible price of EUR 5.20" |
| 4 | main 5.07 | final 5.10 @ 45 d -> accepted, 0.621 |
- **36-month move: 0** on P18 (unlike P10's -0.10 to -0.30). Werdenfels prices contract length in already ("continuity ... already
  reflected").
- **Main missed the 14-day switch** here (it stayed on its 45-d primary); in 0c968aae the switch to 14 d in round 2 was worth -0.20.
- A smaller round-2 step (+0.08) drew a smaller mirror step (-0.10).
- Next design (not run): main's round 1, round 2 = 14 d at an ask <= 4.84 (so a 4.86 ask stays monotone), round 3 = labour
  index at 4.86 @ 14 d - it agreed at our ask 4.91 in 0c968aae (line <= 4.91); 4.86 needs its line 5 cents lower.
