STATUS: DONE (task 7, P18) - 2026-10-10 evening, cloud session, offline only.
Run: `cd tacto/starter-kit && uv run python ../../analysis/tools/offline_round.py P18 ../../analysis/agent_variants/noidea_neel.py`
(main agent at e27b6f0, no LLM). The sim agrees in round 1 (0.94: its floor-stop supplier accepts anything above its floor),
so it only shows message 1. Live P18 answers 5.20-5.38 and goes final at our msg 3 (analysis/cases/P18_engine.md).

# P18 plan (Blankstahl Werdenfels, mirror) - what the agent sends now, what's wrong, the minimal change

## Message 1 as the agent sends it now
```
--- e-mail 1 refs ['fc:370010@2026-09', 'idx:AS-14404@2026-06', 'idx:AS-14404@2026-09', 'po:4500014022-10', 'po:4500014078-10', 'po:4500014140-10', 'po:4500014239-10', 'po:4500014287-10', 'po:4500014292-10', 'po:4500014355-10', 'po:4500014427-10']
Dear Franz Seidl,

Thank you for your message.

1. Volume and term: we confirm a binding volume of 23,700 units per year for 36 months, 71,100 units in total.
2. Our proposal: EUR 4.77 per unit, no price-adjustment clause, 45 days net, 36-month contract. This amounts to about EUR 339,147 over the term.
3. Basis: On 2026-09-09 you quoted us EUR 6.06 per unit for this part; your new quote is 0.7% above it. Our recent orders for Round bar 1.4404 dia 30 mm, peeled were at 5.26, 5.84 per 1 (po:4500014292-10, po:4500014355-10, po:4500014427-10). Alloy surcharge 1.4404, Isartal Edelstahlwerk (fictional mill, derived) changed -5.5% from 2026-06 to 2026-09 (idx:AS-14404@2026-06, idx:AS-14404@2026-09). Our demand forecast for this part is up +1.9% (fc:370010@2026-09).
4. Next step: Please send us your cost breakdown for this part. You told us that price changes above 2% need your pricing committee. Please put this proposal to your pricing committee: a binding 36-month agreement for 71,100 units, about EUR 339,147. On the committee's written confirmation we issue the order the same day, and we pay every invoice on the due date.

Attached: our monthly call-off schedule for the full contract term.

Kind regards,
Purchasing, Hollerau Pumpenwerke
```

## What is wrong (against analysis/cases/P18_engine.md and LEARNINGS 7b)
1. **"On 2026-09-09 you quoted us EUR 6.06 ...; your new quote is 0.7% above it."** That quote (quote:7200008) is ITS OWN
   quote and only 0.7% under its opening: the line anchors the talk at EUR 6.06 while we ask EUR 4.77. Only cite an own quote
   when it is clearly below its opening (>= 2%, as P04's EUR 4.63 vs 4.96); here drop it.
2. **Price-history sentence with two numbers** ("were at 5.26, 5.84") and 8 order lines in `refs`. The jump IS the argument
   (taken 9/9 live), but one number per sentence: "Our orders rose from EUR 5.26 in June (po:4500014022-10,
   po:4500014078-10)." + next sentence "Since July they are at EUR 5.84 (po:4500014292-10, po:4500014355-10,
   po:4500014427-10)." - two claims, one figure each (po claims check the orders, not a figure, so the risk is lower than
   P02's QN, but keep the rule).
3. **36-month contract.** P18's deals were all 24 m (its AS-14404 clause is "mandatory" on 24 m); 36 m was priced HIGHER on P07
   and P10, and costs us the same on the 2-year horizon. The committee rule ("committee suppliers keep the longest", from P03)
   should not apply here: use the horizon length (24 m).
4. Fine as is: one sheet; clause-free ask (it adds its clause, either deadband is neutral for us); AS-14404 -5.5% (2026-06 ->
   2026-09: recent, not hedged here, taken 6/6); forecast; committee line (no "full authority" signal from 70740).

## Minimal change, round by round (it mirrors 0.8-0.9x our step; final at our msg 3)
- **Msg 1:** one sheet EUR 4.77, 24 m, 45 d, no clause; price history as two one-number sentences; AS-14404 -5.5%; forecast.
  No own-quote line.
- **Msg 2:** step 40% of the gap (mirror rule) instead of the EUR 0.10 steps of the past games; new data: other parts' price
  jumps (all_parts_po: verified, never "duplicate" on P18) or 1 QN (qn:20004916, no figure).
- **Msg 3:** step 40% again (stay a near-close below its standing value) -> its final_offer -> accept its primary (db0 or db5).
- Expected: past games moved EUR 0.10 per round for our 0.10; with 40% steps the same 3 rounds should reach ~EUR 4.85-4.90
  (0.77-0.80) instead of 5.00 (0.68).
