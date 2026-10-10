# Requests for Dhruv (from Neel's workstreams)

## Open

1. **`C_arguments.jsonl`, `rival_quote_context`:** a supplier's *own* past quotes are labelled
   "Another supplier quoted …" (e.g. `quote:7100001`, `quote:7300001` with `rival: sup:70110` for
   sup:70110). Suggest a separate kind `own_past_quote` ("You quoted EUR 126.53 on 2026-09-03 …").
   Also: the case's alternative quote (`quote:7200001` in P01) **is** checked by the arena (our session
   `b04caaf8824a9871` got `verified`), so `checked_by_arena: false` is wrong for it. Still: never
   cite an alternative that is dearer than the supplier's ask (it leaks a weak BATNA).
2. **Agent guardrail (from P01 session `b04caaf8824a9871`, score 0):** the LLM offered €142.50, above
   the supplier's own ask of €138.55, and the supplier instantly agreed. Before sending, reject any
   term sheet whose `total_cost` ≥ C of the supplier's standing offer.
3. **Effective date is a top lever in price_increase cases** (P01: 2027-04-01 alone = +0.72 score at
   the asked price, because pre-effective units are bought at the current price). The prepare step
   should rank levers by `total_cost` deltas, not by habit. See `analysis/cases/P01.md` §6.
4. **EDA corrections from the N1 lever maths** (`analysis/cases/README.md`): P02's index clause *costs*
   us (CU path +5% → db0 = −0.86 score), so the EDA's "index clause for P02" is wrong. P04 and P08: a
   24-month contract is *worse* at the opening price because the fallback is cheaper than the quote.
   P07's alternative (today's terms) beats the opening (walking away = 0.12).
5. **Exact C_open / C_best for all 10 hosted cases** are in `analysis/cases/openings/*.json`
   (`result`). The agent's prepare step can load them for practice runs (score of any sheet before sending).
6. **Playbooks (N3) are in `playbooks/`**: one per arena `type` plus `playbooks/_common.md` (signals,
   claim rules, motive → lever table, closing rules). Please **prepend `_common.md`** to
   `playbooks/<type>.md` in the prompt (together ≤ ~160 lines). For a hidden case whose type mixes
   with an unfamiliar goal, `_common.md` §1 (lever ranking by total_cost) is the part that generalises.

## From Parth (P18 offline check, v1.7 on main 6750e76; P18 live test is Parth's, P10 stays with Dhruv)

7. **P18: the strongest argument is never sent.** `arguments()` adds `po_prices` only when `ask_pct <= 0`.
   In P18 (ask +4.5%) the price history *is* the case: the July index step took €5.26 → €5.84 (+11%), more
   than the full 12-month driver change (+7.0%) (analysis/cases/P18.md §4). Suggest: for `raw_material` (or
   whenever the last PO price jump > the justified change), add the `po_prices` sentence with a prose line
   "the July step was +11% against a +7% driver change". Offline e-mail today cites AS-14404 −0.3%, LCI +1.7%, fc +1.9% only.
8. **Every e-mail prints raw field names** (`write()`, `offers`): "…term sheets (unit_price 4.77, index_clause
   None, payment_days 45, contract_months 24; …)". Suggest plain words: "€4.77/kg, 45 days, 24 months, no index clause".
9. **Two analysis findings for the agent logic** (analysis/cases/P06.md, P09.md, P12.md):
   - a chargeback ≥ `cost_per_defect` sets the quality term to 0, so ppm stops mattering in C (P12: €300 ≥ €275).
     The sheet search already prices this, but the LLM/prose shouldn't spend price on ppm promises then;
   - near a cash-short supplier's floor in stabilise/secure_supply cases, **shorter payment can beat a lower price**
     because the relationship charge falls (P06). Only if the cash-rate / full-cost estimates feed the sheet ranking.
- Offline P18: 0.94 (both modes) but the simulator accepts message 1 (our €4.77 sheet already costs ≥ C_best), so
  it only checks the anchor, which matches Neel's brief (€4.65–4.75, 24 m, no clause). Needs one live game.

## From Neel

10. **Offline Astra runs on P02 / P03 / P04 (0 quota)**: sim mean 0.97, 0 LLM errors, ~6 s per Astra call.
   Six issues incl. a P02 claim that cites rising steel (+6.2%) against us, a German paragraph from Astra,
   and a **Windows UTF-8 bug** in `NoIdeaAgent.__init__` (`read_text()` without encoding). Details:
   `analysis/offline_runs/README.md`.
11. **P04 live 0.86 → offline 0.98: near-close + 3 fixes**, in `analysis/agent_variants/noidea_neel.py`
   (your v1.5 copy; your file untouched). It reached €4.94 @ 90 d and stalled 0.15% above its floor; one cent lower
   on 14 / 60 / 30 d scores 0.99 / 0.98 / 0.94. Near-close + only falling indices + cost breakdown once + UTF-8 /
   English. New live-calibrated simulator `analysis/tools/sim_floorstop.py` (reproduces the live game), comparison
   `analysis/tools/variant_check.py`: no case worse in any simulator. Please review, then merge or add
   `--agent-file` to `arena play`. Details: `analysis/agent_variants/README.md`.
12. **Central layer** (`analysis/agent_variants/central.py`, `analysis/central/LEARNINGS.md`), worth porting to
   `noidea.py`: (a) calibrated supplier full cost / cash rate from deal breakdowns (P02 full cost EUR 367.60, almost
   its quote, so a full-cost guard caps us at ~0.5); (b) cite should-cost against the **quote**, not today's price;
   (c) never send round 1 without a checkable claim (26 "Which figures is that based on?" replies); (d) on an approval
   ladder, stay on the structure the committee priced. Your v2.7 P03 game (volume forecast + committee in round 1)
   is our best P03 at 0.903.

## 13. (Neel, 2026-10-10 evening) Add the P08-loop general rules to docs/GENERAL_RULES.md
analysis/central/LEARNINGS.md §9 has six rules from 17 P08 games (budget suppliers: final = first counter - fixed
budget; nominal first counter, so lead with the longest payment term; small step at the final message postpones it one
round; the final is cent-rounded on our payment term; round-2 cut = min(cap, share x gap); levers measured at 0). Please
add them to docs/GENERAL_RULES.md (I don't write in docs/). Rules 1, 2 and 4 are the general ones. Your v2.20 supplier
memory could detect a budget supplier from its total cut across games.

## 14. (Neel, 2026-10-10 22:55) Let `year_rise_path` run for price-frozen suppliers too (P03 0.963)
Live 722dee8e68a4836c (`analysis/agent_variants/noidea_p03.py`): the rising order PRICE PATH ("Our orders for this part
rose from EUR 400.19 to EUR 412.74 within nine months (po:4500013355-10, po:4500014465-10)") was taken by Selvbrunn's
committee in round 2: 431.67 -> 430.41, the biggest cut P03 has ever given. The final 430.36 @ 90 d = 0.963 beats "+=" 0.944.
Your `year_rise_path` skips price-frozen suppliers, so the main agent never sends it to P03. Its own quote by ID
(quote:7300003) came back "irrelevant" (read as a rival quote): leave it out. Details: analysis/cases/P03_lever.md §6.

## 15. (Neel, 2026-10-11 01:30) P18 regression in v2.34+: the round-1 term choice opens at 45 d and never switches to 14 d
All 26 P18 games (analysis/cases/P18_lever.md section 9): v2.27/v2.28 opened with ONE sheet @ 30 d and switched to 14 d in round 2
(4.76 -> 4.87, +0.11) -> 5.20 -> 5.00 -> agreed 4.91 / 4.94 = **0.727 / 0.707**. v2.34+ sends three sheets led by 45 d, its primary
goes to 45 d and stays there: **0.62-0.69 in 7 games**. Werdenfels prices payment at ~EUR 0.10/kg per 30 days (~24%/yr, 3x our 8%),
so for a supplier whose two-sheet quotes show payment priced above our rate, open at its standard term and move to 14 d in round 2
with a full step (>= +0.11 here: smaller steps drew one grid step less, 3 of 3). Never hold our ask in its final-trigger round:
"it gives nothing without a move" (ed9a881a: hold + new fact -> its final at once).
