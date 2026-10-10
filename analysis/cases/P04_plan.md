STATUS: DONE (task 7, P04) - 2026-10-10 evening, cloud session, offline only.
Run: `cd tacto/starter-kit && uv run python ../../analysis/tools/offline_round.py P04 ../../analysis/agent_variants/noidea_neel.py`
(main agent at e27b6f0, no LLM: template wording; supplier = sim_floorstop, live-P04-calibrated: floor value 4.8667, stop 4.8740).

# P04 plan (Waelzlager-Zentrum Sued, floor-stop) - what the agent sends now, what's wrong, the minimal change

## What it sends now (sim result 0.81: deal EUR 4.91 @ 60 d, final at our msg 2 - the same as live 5f80eb75c793f352)
```
--- e-mail 1 refs ['idx:LCI-C@2025-10', 'idx:LCI-C@2026-01', 'po:4500014053-10', 'po:4500014120-10', 'po:4500014171-10', 'po:4500014280-10', 'po:4500014280-20', 'po:4500014329-10', 'po:4500014389-10', 'po:4500014467-10', 'qn:20004711', 'qn:20004732', 'qn:20004762', 'qn:20004857', 'qn:20004869', 'qn:20004968']
Dear Florian Gruber,

Thank you for your message.

1. Volume and term: we confirm a binding volume of 20,000 units per year for 24 months, 40,000 units in total.
2. Our proposal: option A: EUR 4.79 per unit, 14 days net, 24-month contract; option B: EUR 4.84 per unit, 60 days net, 24-month contract; option C: EUR 4.81 per unit, 30 days net, 24-month contract. Option A amounts to about EUR 191,600 over the term.
3. Basis: On 2026-09-20 you quoted us EUR 4.63 per unit for this part; your new quote is 7.1% above it. Labour cost index DE, manufacturing, seasonally and calendar adjusted (quarterly, carried to its three months) changed -0.3% from 2025-10 to 2026-01 (idx:LCI-C@2025-10, idx:LCI-C@2026-01). We raised quality notifications on this part over the past year (qn:20004711, qn:20004732, qn:20004762, qn:20004857, qn:20004869, qn:20004968). Our recent orders for Deep groove ball bearing 6306-2Z C3 were at 4.29, 4.39 per 1 (po:4500014329-10, po:4500014389-10, po:4500014467-10).
4. Next step: Please send us your cost breakdown for this part. All other terms as in your quote; on your written confirmation of one option we will issue the order.

Attached: our monthly call-off schedule for the full contract term.

Kind regards,
Purchasing, Hollerau Pumpenwerke

--- e-mail 2 refs []
Dear Florian Gruber,

Thank you for your message.

1. Volume and term: we confirm a binding volume of 20,000 units per year for 24 months, 40,000 units in total.
2. Our proposal: EUR 4.85 per unit, 60 days net, 24-month contract. This amounts to about EUR 194,000 over the term.
3. Next step: All other terms as in your quote; on your written confirmation of these terms we will issue the order.

Kind regards,
Purchasing, Hollerau Pumpenwerke
```

## What is wrong (against analysis/cases/P04_engine.md)
1. **Message 2 is wasted on a normal step** (EUR 4.85 @ 60 d = value 4.818, 1.2% under its stop). P04 goes final at our
   msg 2-3 and pins its value at 4.874-4.877 from its first counter: message 2 must be the one-cent close, not a step.
2. **Three payment terms in message 1** (14 / 60 / 30 d). It counters on our highest-price sheet (60 d), and on 60 d the
   cent grid lands badly at its stop: EUR 4.91 @ 60 d = 0.81. At the same stop, **90 d gives EUR 4.94 = 0.86** (the live best).
3. **Price-history sentence with two numbers** ("were at 4.29, 4.39") while `refs` carry 8 order lines (one at 4.29, seven at
   4.39). New rule (P02 f778b35c67ecd799): one number per claim sentence, or none. Say "were at EUR 4.39" and cite only 4.39 lines.
4. Fine as is: its own quote EUR 4.63 (20 Sep, valid 90 d) in words, QNs without a figure, one labour window, contract length
   (24 vs 36 m cost the same on the 2-year horizon).

## The cent grid (its floor 4.8667 vs its usual stop ~4.874, all contract lengths alike)
| payment | at its FLOOR | score | at its STOP | score |
|---|---:|---:|---:|---:|
| 14 d | EUR 4.85 | **0.99** | EUR 4.86 | 0.82 |
| 30 d | 4.87 | 0.94 | 4.88 | 0.77 |
| 60 d | 4.90 | **0.98** | 4.91 | 0.81 |
| 90 d | 4.94 | 0.86 | 4.94 | **0.86** |
So: 90 d is the safe landing at its stop; 14 d (or 60 d) is worth +0.13 only if the data moves it down to its floor.

## Minimal change (floor-stop / final at msg <= 3, e.g. engine_rules.classify == "floor_stop" or mined final_at_2/3)
- **Msg 1:** ONE sheet, **90 d**, 24 m, ask ~EUR 4.80, data as now (own quote in words, QNs no figure, labour, order prices
  "at EUR 4.39" only).
- **Msg 2 (= the close):** if its counter's value <= 4.870 (it moved to its floor: the data worked) -> one sheet **EUR 4.85 @ 14 d**
  (0.99); else -> one sheet at its own counter's value minus one cent on **90 d** (EUR 4.93 if it stands at 4.94). Never two
  near-closes (live P04: "we must maintain our price").
- **Msg 3 / final_offer:** accept its primary. Expected: 0.86 if it holds its stop; 0.94-0.99 if the own-quote / QN data takes
  it to its floor.
