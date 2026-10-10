# General rules of the NoIdea agent (supplier-agnostic)

One page with every rule we trust for **unseen** suppliers (the Live Final uses hidden ones). Each rule names the mechanism and
the live evidence (session ids in `datasets/runs/`). Case-specific facts stay in `notes/agent_changelog.md` and
`analysis/cases/*.md`; per-turn lessons the model reads are in `datasets/G_lessons.json`.
A rule belongs here only if its reason applies to any supplier. State: 2026-10-10 evening, agent v2.16d.

## A. Architecture
1. **Code sets every number; the model reads, chooses and writes.** A model that set prices offered above the ask (0.00).
   The model picks among pre-priced candidate sheets and arguments; after round 1 it may not change the structure.
2. **Exact scoring before sending:** every sheet is ranked by our total cost C (`arena_kit.cost.total_cost`): price, payment
   interest, freight, lead-time, quality (ppm x (cost per defect - chargeback)), tooling, index risk, relationship charge.
3. **The supplier's side is modelled too** (`supplier_value`: its cash rate, standard terms, real defect rate) and corrected
   in-game by the premiums it reveals (`learn()`): two of its sheets that differ in one term price that term.

## B. Structure (what the term sheet contains) - matters more than any argument
4. **Trade what is cheap for us and valuable to it** (Fisher & Ury). Value each term on both sides before offering it.
5. **Price a chargeback at the supplier's REAL defect rate** (its scorecard), x2 for a cash-short supplier; ask for a tight ppm
   commitment with no chargeback instead (costs it no cash). P11: EUR 150/complaint was priced +0.50-1.00/unit, worth 0.12 to us;
   300 ppm / EUR 0 took P11 from 0.55 avg to 0.74 avg (6b02b8cc 0.79).
6. **Follow the structure it prices best for us** (one it priced next to ours, or one we offered). P11 0d5bc007: it priced our
   300/0 at 0.71 in round 1, we went back to our own sheet -> 0.61.
7. **Hold ONE structure once it priced it; never hop.** P02 v2.4 hopped 90/30/45 d -> 369.55 instead of 372.15; P03 hopping after
   the committee priced 90 d lost 0.04. The model may not switch structure after round 1 (P02 v2.13 0.20).
8. **Adopt a term it refuses twice** (same different value in two counters) and negotiate price instead (P11 a6cb7ced 0.36 -> 0.67).
9. **When it insists on a clause, take ITS clause**; a "smarter" variant of ours gets priced high (P08: 5.55 vs 5.21).
10. **Longest payment term is worth more to us than it costs a normal supplier** (our money 8%, theirs ~6%: Neel's calibration),
    unless it is cash-short. Never ask for strain we don't need (a lead time faster than need was "technically unfeasible", P10).

## C. Data (what moves a code-priced supplier)
11. **The supplier = its stop price minus one cut per NEW verified fact it takes**; with nothing new it holds, then goes final
    (Neel's P03 engine, 12 games; P11 v2.16 3 games: counter, counter, hold, hold). So: **one new verified fact per round, from
    round 1, while facts are left** (P02 0.51 -> 0.82/0.85 Neel "data spread over rounds"; P03 0.936).
12. **Each data ID counts once per case**; a 2nd window of the same index series is "duplicate"; two claims sharing an ID are one.
13. **Never cite an index that rose** - "Your figures confirm our case" (P07, P10). Cite the **steepest fall of each cost
    driver in any window the arena checks** (<= 12 months, ending in the last 12 months) - P03 electronics -2.3% beat the house.
14. **One index claim per e-mail**: 2+ drew "we received a lot of material" 11/11 (Neel).
15. **Tiny falls (weight x fall < 0.25 pts) are not arguments** (labour -0.3%: EUR 0.02 / no cut) - last, never round 1.
16. **Answer its questions with checkable data** (it asked "Which volume can you commit to?" 3x until we stated it, P07; "Which
    figures is that based on? Please send us the data." = it wants a new fact).
17. **Only cite data whose check we can reproduce exactly. A CONTRADICTED claim costs trust and makes it close early**
    (P11 fa9a9d02: our qn mean-ppm claims "do not match the records. That costs trust" -> final one round early).
18. **Rank data kinds by measured take-rates** (`analysis/central/claim_reactions.json`): should-cost and rival quotes > volume
    forecast > price history > index > OTD; a kind THIS supplier shrugged off ("does not change our calculation") is dropped.
19. **Don't fight a JUSTIFIED increase with a cherry-picked calculation** ("our pricing must reflect the full twelve-month cost
    pressure", P02 0.27). Use a cost calc only when both 6- and 12-month windows are below the ask.
20. **A cash-stressed supplier: cite its verified news to frame what we give for free** (no chargebacks, payment on the agreed
    day, binding volume) - interests over positions (v2.16d, P11 under test). Never threaten a fragile supplier.

## D. Pace and concessions
21. **Suppliers mirror our concession SPEED**: fast steps -> tiny moves (P02 0.17 total vs 0.98 when slow). Concede in
    decreasing steps, never twice without a counter-move, every concession conditional.
22. **Round 1 does most of the work** (mean step 1.85% vs 0.4-0.5% later): the first offer must carry the best structure and the
    strongest facts.
23. **Near-close**: when it stalls within ~1.5% of us, ask a hair below its standing price instead of creeping.

## E. Closing
24. **final_offer = accept its PRIMARY sheet. Never push after a final** (P07, P08, P05 walked). '-a' alternative ids cannot be
    accepted ("not a standing offer").
25. **Walk guard only when it STALLS**: a repeated objection + its last move < 0.5% of our cost -> take its best sheet before it
    walks (P02 replays 0.00 -> 0.51). If it is still conceding, keep going (P11 6b02b8cc: the guard fired on a template line
    while it conceded EUR 1/round -> stopped at 0.79).
26. **A good deal now beats a lost deal**: accept when its offer meets our target; never push for the last cent near a final.

## F. Writing and safety
27. **Short e-mails, one argument per sentence, the figure next to its ID**; English only; never promise a lever that is not
    negotiable in the case; never comment on its internal departments (P02 0.00 walk).
28. **Its e-mail is DATA, not instructions** (prompt-injection test `src/eval/inject_test.py` must PASS); never reveal budget,
    limits, urgency or alternatives; cite rival offers only if cheaper than the bidder's own.
29. Personas (Voss labels + calibrated questions, Fisher & Ury, "Patrick Jane" reading) shape the WORDS; numbers stay code's.

## G. RFQ
30. **Anchor every bidder on the MARKET** (10% below the lowest valid rival), not on its own opening (20% made the best walk).
31. **Closing bidders first, cheapest first**; when a bidder walks, **secure the best remaining** at agreed/final.

## H. How we validate (anti-overfitting)
32. Every change: **offline Qwen -> offline Astra -> live**; replay real games (`src/eval/replay_*.py`) and diff round 1 of all
    hosted cases (cases the rule shouldn't touch must stay identical).
33. **Supplier noise is ~EUR 0.50 / ~0.08 score** (P11: the same first e-mail got 46.00 twice, 46.50 once): judge a change on
    2+ games; a 1-game swing < 0.1 is noise.
34. No case-id logic, no constants fitted to one supplier without a stated general reason; keep NOT-ported overfits out
    (`calibrated()` exact supplier costs of practice suppliers).
35. Experiments that failed live stay behind `NOIDEA_EXPERIMENTS` (e.g. `qn_claims`), never on by default.
