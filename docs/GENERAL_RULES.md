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
