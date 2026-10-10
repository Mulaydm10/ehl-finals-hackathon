# General rules of the NoIdea agent (supplier-agnostic)

One page with every rule we trust for **unseen** suppliers (the Live Final uses hidden ones). Each rule names the mechanism and
the live evidence (session ids in `datasets/runs/`). Case-specific facts stay in `notes/agent_changelog.md` and
`analysis/cases/*.md`; per-turn lessons the model reads are in `datasets/G_lessons.json`.
A rule belongs here only if its reason applies to any supplier. State: 2026-10-10 ~18:40, agent v2.16g; section I = teammates' learnings (Neel, Parth, cloud sessions).

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
15. **Tiny falls (weight x fall < 0.25 pts) are weak on PRICE-CONTINUOUS suppliers (P03: EUR 0.02) - but on a GRID supplier a taken tiny fall is a full step (P11 labour -0.3%% -> -0.50, 77f61e47)** (labour -0.3%: EUR 0.02 / no cut) - last, never round 1.
16. **Answer its questions with checkable data** (it asked "Which volume can you commit to?" 3x until we stated it, P07; "Which
    figures is that based on? Please send us the data." = it wants a new fact).
17. **Only cite data whose check we can reproduce exactly. A CONTRADICTED claim costs trust and makes it close early**
    (P11 fa9a9d02: our qn mean-ppm claims "do not match the records. That costs trust" -> final one round early).
18. **Rank data kinds by measured take-rates** (`analysis/central/claim_reactions.json`): should-cost and rival quotes > volume
    forecast > price history > index > OTD; a kind THIS supplier shrugged off ("does not change our calculation") is dropped.
19. **Don't fight a JUSTIFIED increase with a cherry-picked calculation** ("our pricing must reflect the full twelve-month cost
    pressure", P02 0.27). Use a cost calc only when both 6- and 12-month windows are below the ask.
20. **A cash-stressed supplier: cite its verified news to frame what we give for free** (no chargebacks, payment on the agreed
    day, binding volume)? Tested live: "holds, but does not change our calculation" + counts as material (P11 7117d351) -
    OFF (`news_frame`). Never threaten a fragile supplier either.

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

## I. Teammates' learnings (all branches + commits reviewed 2026-10-10 18:30; merged into main)
Sources: Neel `analysis/central/LEARNINGS.md` 1-8, `analysis/central/ENGINES.md`, `analysis/cases/*_engine.md`,
`analysis/central/REGRESSION.md` (cloud review of our agent vs Neel's variant); Parth `tools/experiments/`, `analysis/cases/P*.md`,
`analysis/strategy_0.9.md`, play.py RFQ fixes.
36. **Know the supplier's ENGINE and play it** (ENGINES.md, 10 hosted cases): **mirror** 5/10 (its step follows ours), **holder**
    2/10 (cuts only for new verified facts), **floor-stop** 1 (pinned after its first counter: only the cent grid + near-close),
    **one-shot** 1 (final at message 1: everything in message 1), **auction** 1 (RFQ: rival offers move bidders).
    Live classifier `analysis/central/engine_rules.py` (87% right at thread end; "unknown" after one reply). Our gate for
    "mirror": its words ("in response to your step") or classifier + a cut after an e-mail of ours with no new fact.
37. **Holder: pack facts (2 per later round) before its fixed final; mirror: spread (1 per round) and step bigger.**
    Neel P02 (mirror): 30%-of-gap steps 0.67 -> 0.82, the path then follows a fixed schedule to the cent (0.847 x2).
    Our P11 (holder): 2 facts in a round cut EUR 1.00 (3x), 1 fact 0.50. The 30% step is OFF until live-tested beyond P02
    (offline it cost P04/P08 against non-mirroring sims) - `mirror_step`.
38. **Suppliers go final at a fixed message count** (P02 4th-5th, P08 3rd, P10 1st, P11 4th-5th): time the data to land before it.
39. **One number per claim sentence, the checked figure, no thousands separator** (Neel P02 f778b35c: 4 numbers in a QN sentence,
    the arena checked the wrong one -> contradicted -> -0.24). **Quality notifications without a figure** (the data's own value
    is checked) - P11 answered "already looked at those ... don't change our calculation" but still cut 0.50.
40. **Facts it shrugged off are last-round fillers, never dropped and never round 1** - no round goes out empty ("Which figures
    is that based on?" + final came after an empty round, P08 and P11).
41. **"I hold full authority" -> never mention a committee** (P02 said it every round). Escalation only where it signals one.
42. **Hedged series** (motive hedged_forward, "covered at fixed prices until ..."): never cite them - "That is not our reality".
43. **A falling cost-driver index was taken in every case where we cited one** (P01, P02 x3, P03 x4, P18); a rising index of the
    same kind earlier ("confirms our case") does not block a FALLING one.
44. **The supplier's own recent quote** (P01, P04, P08, P11) and **order-price history** were never cited in most cases -
    check them; cite its own quote in words when it is above our target.
45. **One-shot suppliers (P10)**: a small ask + price history + should-cost in message 1 -> agreed in round 1 at 31.56 = 0.674,
    P10 best (Parth probe A, 7eba122).
46. **RFQ loop (Parth fcfdb78)**: no wait before accepting, urgent-first, resync stale offer ids; answer every bidder within its own
    60 s (parallel sends).
47. **Exact supplier calibration** (Neel: full cost + cash rate pinned by two deals) is practice-supplier knowledge - useful to
    understand engines, NOT ported (it would overfit the hidden final).
48. **A learned premium holds only over the range the supplier priced** - never extrapolate (P11 f5157e0d: a 300-vs-1500 ppm
    slope extrapolated to 6,400 ppm made every sheet unaffordable -> forced accept 0.54). `premium()` clamps.
49. **MESOs (several equal-value sheets in round 1) are unproven**: one game better (0d5b), one worse (f5157e0d - it priced the
    loosest variant). Off (`meso`). Never vary the payment term across sheets (P02/P03).
50. **One near-close ask (-0.75%) before taking an OPEN offer** costs nothing: it agreed once (7117d351), held twice.
51. **Some suppliers draw their mode per session** (cloud VARIANCE.md): P08 50/50 (13 score pts), P11 ~40/60 (8 pts) - identical
    inputs split; nothing we send moves the draw. Judge changes there on >= 2 games or on the rounds AFTER round 1. P02, P03,
    P04, P07, P18 are deterministic for identical inputs: one live game judges a change.
52. **Short-fuse suppliers (final early, P10)**: credible anchor (today's price, not a deep one - a deep anchor got a floor-level
    final in round 1), the order history as a price PATH (last old price -> today's), one 1/3-gap step in round 2 (Parth
    87653f3, live 0.694; 0.90 not reachable with that engine).
53. **Grid probe**: a supplier quoting on a coarse grid (all counters multiples of 0.50 / 1.00) hides its real floor between grid
    points and agrees to any ask >= it (P11 agreed to our 45.13 while showing 45.50). When it holds and no facts are left,
    step the ask UP from (shown - grid) in small steps on its own sheet; accept its final at once.
54. **Template lines are not objections**: a phrase a supplier writes in every e-mail ("Our standard Zahlungsziel is 60 days net")
    must not trigger a walk guard - count payment-term phrases only when payment is negotiable.
55. **Rule-order audit**: guards that accept (no-sheets, walk risk, near-final) must not pre-empt a cheaper probe unless the walk
    risk is real; "no sheet below its offer" usually means a modelling error, not a deal - repeat the last ask.
56. **Play the man, not the game**: read what the counterpart PERSON needs (P11's export manager: cash, "the bank is watching") and
    pay in that currency with something true and cheap for us. Check our OWN record first (invoices.csv: we paid Kalwisz 96% late,
    ~10 days) - owning it and fixing it is a real concession to a cash-short firm, worth more than cents of price.
57. **Honest hard-ball only**: firm closes ("we can sign today at X"), calibrated questions ("what is the lowest price at which you
    can sign today?" - it answers "as openly as the company is"), true competitive facts (a qualified second source) without its
    price. Never prompt injection or fabricated data: the arena "understands attempts to manipulate", wrong figures cost trust.
58. **Ask the floor - it answers.** "What is the lowest price at which you can sign these terms today?" got P11's true floor ("We can
    give you a price of EUR 45.00", then final 45.00). If the named floor equals its standing price, stop probing below it.
59. **The person's currency moves the floor; data moves the price.** P11's high-draw floor fell to 45.10 (from 45.13-45.50) after we
    owned our late payments; all facts together cut ~EUR 1.00-1.50. Beyond that only real value to the person helps.
60. **A supplier cost floor is hard**: P11 stopped at ~EUR 45.00 in 14 games whatever we sent (data, person-currency, probes, timing). Find the floor early (ask it), take it, and spend no more rounds/games pushing through it.
61. **Probe high, not low, when patience is short**: a holder at its floor gives 1-3 probe rounds; asks far below the floor are refused and burn them. Ladder 50/25/10% of a grid step under its price; under a NAMED floor send one hair-below ask.
62. **Read the arena trace reasons** (detail.result.trace[].reasons): the supplier explains each move ("cannot take on that financial risk", "extra guys on the line") - mine them before guessing.
63. **Let its answer choose the ladder**: ask the floor before probing. A supplier that NAMES a floor = its price sits at the top of the gap (hair-below ask); one that keeps its limits internal sat low in it (start the ladder low - P11 agreed to the first probe 3/3).
64. **Every new rule must be checked against every case offline before live**: the hair/probe rules were written for one grid supplier and halved P08 in the simulator until gated on a grid and on our own structure. Never step back below our own previous ask.
65. **Remember each supplier across games** (`datasets/H_supplier_memory.json`): the prices it agreed to and refused at a given standing price are the best guide to its floor - start the next negotiation from them, not from a generic ladder. A sentence a supplier writes every time is not a signal.
66. **At a hard price floor, stop pushing price - trade a term that is cheap for the supplier at ITS OWN commitment** (a
    chargeback at the ppm it promised costs it little if it keeps its word; frame it that way), next to a hair-under-the-floor sheet.

## J. Teammates' learnings, round 2 (all commits since 18:55 reviewed 2026-10-10 ~20:40; branches merged at 50d0513)
Sources: Neel `analysis/central/LEARNINGS.md` 8b-9 (his request 13: "add them to GENERAL_RULES"), `MISTAKES.md` (every live
mistake ranked by points lost), `FINAL_TRIGGER.md` (353 replies), `P08_*.md`; Parth's commits (gap steps, weak facts, QN
crash fix, price path, P04 ceiling, P07/P10/P18 probes).
67. **Know when it goes final**: suppliers go final at a fixed message count of ours (89% of 353 replies; P02 4, P07 4, P08 3,
    P18 3, P04 3, P10 1-2); a holder (P11) counts its HOLDS instead (final after 1-3 holds). Plan every fact and probe before it.
68. **Budget suppliers: final = first counter - a fixed budget** (P08: -0.21 low / -0.27 high whatever we do after round 1).
    Test it by comparing total cuts across games; if it holds, only the FIRST counter matters - spend effort on round 1.
69. **The first counter can be nominal on whichever sheet it picks** (P08 answered 5.41 on our 45-d AND 90-d sheet): lead with
    the sheet worth least to it at equal nominal price - the longest payment term (-0.054 value, proven).
70. **A small step at its final message postpones the final one round** (P08 5 of 6 at 0.18x its last step) - spreads the
    budget, fails when less than one final step of budget is left.
71. **The final is cent-rounded on OUR payment term**: at a fixed value floor pick the term whose cent grid lands lowest
    (P08 5.15 @ 60 d = 0.7329 vs 5.10 @ 14 d = 0.7323).
72. **Mirror suppliers: bigger steps** (30% of the gap to its standing) - P07 0.75 -> **0.81** (Parth gap_steps); NOT for
    patient suppliers (patience prior >= 5: P01/P02 concede on their own, offline 0.99 -> 0.88), cash-short holders (P11),
    hedged (P08: -0.20 -> 0.53) or price-frozen (P03).
73. **Weak facts (QNs, tiny index falls, fillers) only for a supplier that HOLDS - but never at the price of an EMPTY round (rule 40 wins: P11 3cc43596 empty round 3 -> final at msg 3)** - a supplier that is moving answers them with
    the fact's tiny value instead of mirroring our step (P07 0.812 lean vs 0.792 with QN / labour in round 2). On a grid holder
    send the pending fact WITH the probe in the same e-mail (conflict found when merging - rule 61 needs its round).
74. **QNs only when its quality is a problem** (last scorecard amber/red, or a quality case): a green supplier answered "we take
    them seriously ... they do not alter" and cut less all game (P07).
75. **Big claims can crash the arena** (HTTP 500 on a 19-ID QN claim, P07 x2): <= 8 IDs per claim, one part; on a 5xx resend once
    without data IDs.
76. **Order history as a PATH** (last old price -> today's), ignoring one-order blips - taken where the flat run is shrugged off.
77. **Credible anchor for one-shot / capacity suppliers** (P10): round 1 near today's price stays open (7/7) and finals 31.20-31.56;
    a deep anchor got a round-1 final at 31.90-32.00. Never ask a lead time below need or below its quote ("technically unfeasible").
78. **Floor-stop suppliers (P04)**: whole-cent grid -> ceiling 0.874 (4.89 @ 45 d; 30-d floor 4.88); one longest-payment sheet in
    message 1, near-close at message 2 (P04_plan.md; NOT yet in our agent).
79. **Biggest live losses, never again** (MISTAKES.md, points lost): pushing after final_offer ~1.1; remarks about its departments /
    walk after repeated objection ~1.0; structure hops ~0.83; empty / data-less rounds ~0.6; small steps against a mirror ~0.37;
    contradicted claims 0.32. Coin-flip first counters (P08 50/50, P11 40/60) are NOT fixable - judge on 2+ games.
80. **At a named / remembered hard floor, offer two sheets: the floor with a cheap-for-it term, and a hair under the floor**:
    P11 eac20911 agreed to 44.95 (0.8019, first above 0.80) - the hair sheet, delivered in the same e-mail as its last facts.

## K. P08 win (Parth 0.912, beats the house 0.752) and the latest teammate lessons (reviewed 2026-10-10 ~20:55)
81. **Its own rising price path leads round 1**: when our orders with it rose >= 3% in 12 months (P08: 5.17 -> 5.45 in 9 months),
    cite the order history as a PATH first - "the rise is already in our price". P08's first counter fell 5.41 -> 5.25 and, on a
    budget supplier, the final followed (d0708ed1038995d1 = **0.912**; Neel's best was 0.732). Code: Parth 544b5cd.
82. **Never name an acceptable price or "the current level" in the opening** - it anchors the supplier's floor upward
    (P08 81ee4b1e: +0.08 floor, total cut only -0.13, 0.633).
83. **Its own earlier quote, by ID, is the one P03 fact never cited** (quote:7300003, EUR 412.74, 5 Sep) - untested lever.
84. **Never ask again after its final - reconfirmed**: P04 last-cent ask 4.93 @ 90 d after its final -> walked, 0.000 (39d795e).
85. **The floor trade (rule 66) generalises**: Neel ported it to P08 (its own clause structure one cent under the expected final,
    gated by supplier memory to low draws).
86. **Words matter where the numbers are equal: name the fear you remove, never accuse.** P11 (28 games, same data and sheet):
    openings that told the cash-short owner "no penalties / no chargebacks" drew the low first counter 7 of 9 vs 7 of 19;
    "prove your reliability" / "earn our confidence" / "documented complaints" leaned high. Put the reassurance in code, not luck.
87. **Floor-stop suppliers stop at a fixed price per term: choose the TERM from memory** (P04: 45 d = 0.874 vs 14 d = 0.815, the
    same supplier); then one ask one cent under its usual final BEFORE its final (free: refused -> its final). Agent 0.82 -> 0.874.
88. **Check the spec before inventing a lever**: prices are EUR with 2 decimals (api.md) - a floor between two cents is out of reach.
    P04: 0.874 is the ceiling; the agent reaches it every time (5 of 5) once the TERM is chosen from memory.
89. **Memory lookups must compare numbers as numbers** (the arena sends 45.0 where we stored 45) - a silent mismatch disabled a rule.
90. **Never drop a checkable fact because a calculation already covers its series**: a falling window has its own IDs and is
    the strongest fact for a data-naive owner (P01: iron & steel -4.3% in round 1 -> first counter 133.40 vs 136.40, deal 0.9987).
91. **Budget / short-fuse suppliers: load round 1 with every strong fact** (2 index claims of different series allowed there):
    P18 first counter 5.20 vs 5.40 with history only; a supplier that values fast payment cuts a whole step for 14 d (0.707).
92. **A term the supplier values buys a step as a TRADE, not as an opening**: P18 cut 0.20 when we moved to 14 d in round 2
    (0.727), but answered the same nominal 5.20 when 14 d came in round 1 (0.688). Open on its terms, trade the term later.

## L. RFQ (Neel noidea_p05 0.755, Parth's scripted 0.82, record 0.924)
93. **Give every bidder data on the RFQ part itself** (cost drivers of the part, not of the bidder's catalogue): "Which figures
    is that based on?" was answered for the first time - 70210 "you did your homework", first counter 36.00 -> 30.50.
94. **Cite the cheapest rival offer at any lead time**, not only offers meeting our must-haves ("I give half the step now").
95. **Hold RFQ asks low and show the first agreement to the others once before accepting** - the auction ratchet
    (70250 agreed 30.25 -> shown -> 70210 agreed 28.57 @ 14 d). Never a walk-guard accept while another bidder is live.
96. **Extreme anchors make bidders walk** (Parth run 3: 21.00 -> both walked, 0.381): anchor ~10% under the market low.
97. **RFQ asks ~10% under the market low** (6% left money: a bidder agreed to our own ask; 10% -> 0.824; 12% and below risk walks
    and slow rounds). Multi-bidder rounds run close to the 60-s reply limit - one timeout cost 0.06.
98. **RFQ asks ~12% under the market low** (live P05 curve: 6% 0.755, 10% 0.81, 12% 0.871, 15% 0.865; an extreme anchor walks).
99. **In an RFQ the highest opener can have the lowest floor** (P05 Fuchsreiter: opens 38.50, agrees 26.75; the low opener's floor
    ~27.4). Judge bidders by how far they MOVE once they move, not by their opening.
100. **A round without our move can unlock a holder** (Parth P05 0.950): it answers "without movement from your side we cannot
    move either", then - after our deep ask + the lowest rival - "we need to clarify this internally" and its line drops about
    one step per round; it agrees to our standing ask once that is above its line. Make ONE move after the clarification.
    A late reply counts as "our last offer repeated" (three in a row end the thread) - prefer a no-price note to a timeout.

## M. From the top-scoring runs of the whole team (docs/TOP_RUNS_LEARNINGS.md, src/eval/top_runs.py)
101. **Round 1 = every strong verified fact the case offers** (falling indices, forecast, should-cost, price path, notice
     breach): top games had more round-1 facts in 7 of 9 bilateral cases and a bigger first cut.
102. **One sheet in round 1** (top games of 7 cases), the term chosen by the supplier's currency (90 d / 14 d / grid term).
103. **The best deals close with the supplier agreeing to our ask** after it holds - keep a standing ask just under its line.
104. **One more round while it still moves or facts are left** - the top games ran a round longer on P02, P03, P04, P11.

## N. Fact pacing by supplier (v2.34, all archived traces)
105. **After round 1 one e-mail earns about one fact's worth**: a 2nd fact in the same later e-mail cut no more than one (P11
     0.88% vs 0.92% per message, n=21 / 77; P07 1.26% vs 1.26%; P03 0.01% vs 0.06%). Later e-mails carry one new fact (mirrors
     always; other holders still up to 2 - untested either way).
106. **Round 1 prices several facts - except at a cash-short supplier.** First counter by verified round-1 facts: P01 137.4 (0)
     -> 133.4-134.3 (2-3), P02 374.5 / 373.6 / 372.8 (0 / 1 / 2), P03 432.9 / 432.3 / 431.8 (1 / 2 / 3), P10 31.9 (1) / 31.5
     (2-3): load round 1 (rule 101). A CASH-SHORT supplier ("it does not squeeze its margin") cuts ONE step per e-mail however
     much it is shown: P11, the same five levers - four in round 1 -> 45.00-45.50 (38 games); one per e-mail -> 44.45-44.50
     (4 of 4, both first-counter draws). Round 1 there = the one fact behind our structure (its quality record for a ppm
     commitment), then one strong fact per e-mail.
107. **A lever that earns its own cut travels with the WEAKEST remaining fact** (P11 round 2: late-payment admission + energy
     1.03 pts -> 45.00; steel 1.11 pts alone in round 3 -> 44.50). Never spend two strong reasons in one capped e-mail.
108. **Plan the levers for the productive rounds**: P11 cut only at our messages 2-4 (0 of 35 replies from message 5 on). A fact
     held past its final is lost: one strong fact per productive round, weak ones after.
109. **Validate as if every supplier were new**: `NOIDEA_EXPERIMENTS=hidden` switches off supplier memory and per-case reactions
     (the final's suppliers are new). The gap between hidden and normal play is what the agent memorised, not learned.
110. **One fact per later e-mail holds for EVERY supplier, not only mirrors** (v2.34b): P02 hidden with 2 per e-mail ran out of
     facts by round 3 -> empty e-mail -> its final on a worse term (0.56); one per e-mail -> 0.809 (best 0.847 did the same).
111. **A floor-stop supplier without memory is a cent-rounding lottery** (P04: 14 d 0.815 / 30 d 0.766 / 45 d 0.874 / 60 d 0.810 /
     90 d 0.860, the same floor). No pre-game rule picks 45 d; recalibrating the supplier's cash rate moved six other cases and not
     P04 (rejected). Accept the lottery; memory helps only if a supplier comes back.
112. **The first counter of P11 is mostly a draw** (46.00 / 46.50; 45.50 in 3 games): wording labels and the payment promise do
     not separate the draws over 51 games. What we control is the rest: one held fact = one step, from either draw.
113. **Never send an argument twice; after round 1 an argument without data IDs never takes the round's fact slot** (P01
     hidden: an id-less cost calc repeated every round, 0 checkable facts, "please provide the specific data", 0.959 vs 0.9997).
114. **Concessions are monotone**: on the structure we hold, never ask below our own previous ask - a step back reads as taking a
     concession back ("Without movement from your side we cannot move either" -> its final, P02).
115. **A server error is not a reason to resend**: a 503 on our e-mail + a blind retry landed a round late, after the supplier's
     final, and it walked (P10 0.0). Re-sync with the arena and decide on what the thread says now.
116. **The agent must never crash a case**: one exception = no deal. Every decision path ends in a safe move; crash-test every
     known case structure (19 practice cases, 9 never hosted) before the final.
117. **The supplier reads our exact words** (identical text -> identical counter; identical moves with different paragraphs ->
     different counters, P07 5.44-5.56). For an unseen supplier this is noise: judge changes on several games, not one.
118. **Check the arena's MODE before crediting a change** (Neel): in engine-template mode (its model off, 23:51-23:58 on
     10 Oct) every reply is fixed engine sentences and results differ (P10 31.00 vs 31.50). Two of our "new bests" came from
     that window. A/B only within one mode; `analysis/tools/supplier_mode_scan.py` tells them apart.
119. **A supplier's ALTERNATIVE is not a refusal** (P02 0.531): never let a model's reading of its e-mail hard-filter our
     structure; a term counts as refused only when its PRIMARY sheet moved away from ours twice (rule 8), then we adopt it for good.
120. **An instant agreement to our first ask means the anchor left room** (P03: agreed at once 3 of 3 = 0.954; the one game where
     it countered went to 0.989 via its own 36-month alternative). Look for the term the supplier pays for in its counters.
121. **Never send an e-mail without movement or a new fact** (P18 walked on one; P02 went final after one). If no fact is left,
     move a real step toward its price; never repeat our last ask word for word.
122. **In an RFQ every bidder is its own negotiation**: a fact told to one bidder is new to the others - track what EACH
     supplier has seen (P05: one bidder never got a fact under a case-wide set).
123. **Cite the case's own evidence even without its value**: a forecast / should-cost id the case lists can be cited without a
     figure - the arena checks it against its own data (never contradicted; D02 +0.05 in 6 of 6 games). An unanswered "send us
     proof of the volume" is a lost step.
