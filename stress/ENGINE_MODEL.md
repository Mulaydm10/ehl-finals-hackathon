# How the arena's suppliers behave, measured from the archived games

Sources (raw data only): 386 archived real games `datasets/runs/*.json` (10 hosted practice cases:
P01 21, P02 38, P03 31, P04 27, P05 40, P07 35, P08 39, P10 49, P11 64, P18 42 games; 1,625 supplier
replies, 137 of them to timeouts), 169 back-office logs `tools/replays/backoffice/*.json`, the practice
case files, `tacto/data/facts.json` and `cost_drivers.csv`. Nothing from the agent, `docs/`, `notes/`
or `analysis/` was read.

Method: every supplier reply is converted into **value space** - what the term sheet is worth to the
supplier per unit in cash, with the arena's own `arena_kit.cost.supplier_value` (payment days at its
cash rate, units sold at the current price before the effective date, freight leg, tooling,
chargebacks) - and expressed as a fraction of the value of its opening quote. That makes replies on
different payment days / effective dates / lead times comparable. Standard terms per supplier were
read off the openings, the deals closed on standard terms and the sentences "Our standard Zahlungsziel
is N days net". With these standard terms `total_cost` reproduces the archived `c_open` of every
hosted case to the cent (e.g. P01 1,153,779.74, P07 391,027.40, P10 1,932,492.18).

## 1. The opening

The opening is fixed per case (identical in every archived game): P01 138.55 (= the letter's
`asked_price`, +9.5 %), P02 370.96 (+6.5 %), P03 438.21, P04 4.96 (+13 % on current), P05 36.00 /
31.50 at lead 52 / 38.50, P07 5.74 (-8.7 % vs current), P08 6.05, P10 32.20 at lead 54 and volume
19,890 (breaks the must-have), P11 47.00 at 6,400 ppm, P18 6.10. Some openings omit fields
(`missing_fields`, e.g. P01 payment days, P11 chargeback): those close on standard terms.
C_open = the cheapest opening that keeps the must-haves (P05: 70240's 31.50 at lead 52 breaks lead <= 42
and is skipped); if no opening keeps them (P10) the arena still uses them all.

## 2. Behaviour families (evidence)

**F1 Value-equivalent pricing of non-price terms.** The supplier answers the buyer's non-price terms
and moves the price so that its value stays on target ("Your requested terms change our costs").
Alternatives in the same reply differ by exactly that value:

| term | evidence (main vs alternative in the same reply) | implied rate |
|---|---|---|
| payment days | P02 372.52@90 vs 368.42@30; 369.52@30 vs 368.44@14 (47 pairs) | 6.5-6.7 % p.a. |
| | P03 431.67@90 vs 428.74@30 (32 pairs) | 4.1 % p.a. |
| | P04 4.94@90 vs 4.87@14; P07 5.55@90 vs 5.48@30; P08 5.53@90 vs 5.45@14 | 6.4-7.7 % p.a. |
| effective date | P01 136.4@2027-04-01 vs 133.8@2027-01-01: equal value once units before the date are valued at the current price | - |
| lead time | P05 70240 33.0@42 vs 31.5@52; P10 33.8@42 vs 31.9@54, 35.0@35 vs 32.0@54 | 0.48-0.50 % of price per day faster; slower gives nothing (70250 31.0@28 = 31.0@42) |
| volume | P03 431.95@4,580 vs 423.83@5,496 (+20 % volume) | 1.9 % cheaper (~0.1 % per 1 % volume) |
| contract length | P03 431.95@24 vs 429.40@36 months | 0.6 % per extra year |
| index clause | P08 5.20 with deadband 0 vs 5.31 with deadband 5; P18 5.20 vs 5.30 (104 pairs) | ~2 % of price between deadband 0 and 5 |
| ppm / chargeback | P11 46.5@300 ppm vs 46.0@800-2,500 ppm; 47.0@chargeback 150 vs 46.0@0 | +1.1 % for 300 ppm, +2.2 % for a 150 EUR chargeback |

**F2 Price grid.** Counter prices are multiples of a supplier-specific grid (all non-agreed counters):
0.50 for P05 (all three) and P11; 0.10 for P01, P10, P18; 0.05 for P08; 0.01 for P02, P03, P04, P07.
Small concessions therefore round to zero: P18 holds (0.0 step) whenever the buyer moves 0.16-0.49 %,
and steps exactly one grid unit (1.64 %) when the buyer moves >= 1.1 %. An `agreed` reply takes the
buyer's exact price (129.11, 30.83, 26.60 ...).

**F3 First counter** (value change vs the opening, median, by number of verified claims in the
buyer's first e-mail; n in brackets):

| case | 0 verified | 1 | 2 | 3 |
|---|---|---|---|---|
| P01 | -1.85 % (7) | | -3.60 % (10) | -4.22 % (3) |
| P02 | -0.10 % (6) | -0.33 % (6) | -0.69 % (22) | -0.38 % (2) |
| P03 | -2.05 % (6) | -2.30 % (2) | -2.41 % (6) | -2.52 % (12) |
| P04 | -1.56 % (5) | -1.48 % (4) | -1.52 % (13) | -1.48 % (4) |
| P07 | -3.67 % (1) | -3.83 % (4) | -4.73 % (28) | -3.67 % (1) |
| P08 | | -9.83 % (6) | -11.57 % (10) | -14.18 % (22) |
| P10 | | -0.62 % (6) | -2.17 % (10) | -2.17 % (29) |
| P11 | | -1.06 % (23) | | -1.06 % (40) |
| P18 | | -11.72 % (2) | -9.96 % (2) | -13.36 % (37) |
| P05 70250 / 70210 | (RFQ) first counters -20 % / -15 % (median, all claims) | | | |

Read as a fraction of the room down to the lowest value ever conceded: P01 ~26 %, P02 ~5 %, P03 ~64 %,
P04 ~88 %, P07 ~40 %, P08 50-80 %, P10 ~10-45 %, P11 ~20 %, P18 55-70 %. Facts add ~0.15 % (P03) to
~2 % (P08) per verified claim; P04 and P11 ignore them on the first move.

**F4 Later steps: reciprocity with a cap; no move -> no concession.** Without new verified facts the
supplier's value step follows the buyer's value step: P01 0.25-0.75 % for buyer steps 0.34-1.97 %
(roughly 0.8 x the buyer step, capped near 0.6 %); P02 ~0.5 x (cap ~0.2 %); P07 0.5-0.8 x (cap
~1.2-1.4 %); P08 0.33-1.0 x (cap ~1.5 %); P03 and P04 hold at 0 once their first move used the room.
A buyer step of 0 with no new fact gave a 0 step every time it was observed (P01 r5, P18). With a new
verified fact the step roughly doubles or triples (P01 k=1: 0.57 % without, 2.23 % with one fact;
P02 0.09 % vs 0.34 %; P07 0.97 % vs 1.74 %; P08 1.03 % vs 2.95 %). Exception, RFQ (P05): suppliers kept
conceding on repeated identical buyer offers when rival offers were cited (26.5 -> 30.0 -> 27.5).

**F5 Verified data: checked by ID, typed, once per case.** `claim_results`: verified / contradicted
(unknown id or wrong figure) / irrelevant / duplicate (P01: a second citation of the same ids came
back `duplicate` x3). The reasons name the claim type ("index change", "should cost", "notice period",
"volume change", "price history", "contract terms") and say either "it holds and we took it into
account" or "it holds, but it does not change our calculation" (P10 volume change). Back office: a
cited cheaper rival quote triggers "I give half the step now and check the rest" followed next round
by "Checked: give the rest of the step" (44 / 43 occurrences).

**F6 Final offer.** First `final_offer` by reply number: P01 r4-5 (only 4 of 21 games - most agreed
earlier), P02 r4 (17) / r5 (11), P03 r3-5, P04 r2 (8) / r3 (11), P05 r2-5, P07 r4 (27 of 29), P08 r3
(31) / r4 (7), P10 r1 (12) / r2 (33), P11 r3-7, P18 r3 (11) / r4 (22). Early finals coincide with
little room (P10, P04). After a final offer: the buyer pushing with a lower sheet -> `walked_away`
in P04 1/1, P07 1/1, P08 1/1, P10 3/4 (+1 agreed); P05 2 walks vs 9 repeated finals; meeting the final
-> `agreed` (P18 3/3).

**F7 Walks.** 3 timeouts in a row end the thread (P01 2, P02 1, P05 several). Walking from an *open*
thread without timeouts is rare: P02 2/38 games (r4, buyer creeping up 0.6-0.9 EUR at a time), P04
1/27, P05 3 threads/40 games (r3), P18 1/42 - about 2 % of threads. A timeout repeats the standing
offer under a new id (median value step 0.00 over 84 P05 timeouts); one P05 supplier agreed to the
buyer's previous sheet on a timeout round.

**F8 Agreed.** A supplier agrees when the buyer's best sheet is worth at least its next target (P01:
standing 129.60, buyer 129.11 + a verified forecast -> agreed at 129.11). A first sheet above the
opening is agreed at once (P01 b04caaf8824a9871: 142.50 > 138.55).

**F9 Floors and C_best.** The lowest value ever conceded / implied by the archived C_best: P01 0.932,
P02 0.981, P03 0.968, P04 0.983, P07 ~0.87 (C_best; deals stopped at 0.909), P08 ~0.82-0.84, P10
0.953, P11 0.946, P18 0.807, P05 70250 ~0.69, 70210 ~0.76. Without data the floor is higher: P01
no-fact games ended at 0.965-0.970.

**F10 Supplier full cost (relationship term).** From the archived relationship charges (same every
game): full cost / opening value P01 0.9375 (opening margin 6.3 % vs sustainable 3 %), P02 0.9934
(0.7 % vs 0.5 %), P03 0.9079 (9.2 % vs 8 %); P10 deals never paid one (margin >= 10 %).

## 3. The simulator (`sim_supplier.py`)

Value function = F1 (supplier_value + `extras` for lead time, volume, ppm, + decision-only `security`
for contract months and index clause). Hidden parameters per supplier: `grid` (F2), `rate`,
`r_base` (reservation without data), `levers` {claim type: fraction of opening value} (F5/F9; the
absolute floor is `r_base - sum(levers)`), `lever_repeat`, `fact_pass`, `first_frac` (F3), `recip`
and `cap` (F4), `final_round` (F6), `p_walk_final`, `patience`, `insult`, `min_move`, `hazard` (F7),
`rival_follow`, `rival_premium` (F5), `lt_cost`, `vol_elast`, `ppm_cost`, `contract_bonus`, `ix_base`,
`ix_slope`, `max_payment_days` (veto), `ppm_real`, `full_cost_frac` (F10), `trust_penalty`
(contradicted data hardens it), `alt_std` (adds an alternative at its standard terms), `drivers` /
`strict_drivers` (an index series that is not a cost driver of the part is `irrelevant`).
A claim counts if its id exists in facts.json, the case facts or the session's offers (ids written in
the body count; 2 idx of one series = one claim, checked for the window and for the % in the sentence;
2-8 po of one part = one claim; doc + ctr = notice; at most 3 per e-mail).

## 4. Calibration (`calibrate.py`, `calibration_report.json`)

The real buyer e-mails of all 386 games were replayed through the simulator; games were split by id
hash into a fit half and a hold-out half; a random search (2,000 candidates per supplier) minimised
mean |value(sim) - value(real)| (% of opening) + 2 x status mismatch + (single-supplier) the C_best
gap. A thread is compared until one side ends (agreed / walked).

| supplier | half | games | replies | mean value err | status mismatch | first-counter err | first counter real / sim | final round same | walks real / sim | C_best real / sim |
|---|---|---|---|---|---|---|---|---|---|---|
| P01 70110 | fit | 9 | 34 | 0.34 % | 6 % | 0.33 % | -3.59 / -3.62 % | 1/2 | 0/0 | 1,096,816 / 1,097,535 |
| | hold-out | 12 | 44 | 1.01 % | 23 % | 1.04 % | -3.47 / -3.62 % | 1/5 | 2/5 | |
| P02 70510 | fit | 24 | 97 | 0.19 % | 12 % | 0.17 % | -0.44 / -0.52 % | 8/20 | 2/0 | 2,235,514 / 2,235,531 |
| | hold-out | 14 | 59 | 0.12 % | 14 % | 0.11 % | -0.28 / -0.26 % | 6/12 | 1/3 | |
| P03 70530 | fit | 19 | 55 | 0.15 % | 15 % | 0.19 % | -1.33 / -1.51 % | 6/8 | 0/1 | 3,909,043 / 4,011,054 |
| | hold-out | 12 | 37 | 0.22 % | 30 % | 0.32 % | -1.09 / -1.51 % | 0/3 | 0/2 | |
| P04 70620 | fit | 11 | 30 | 0.16 % | 20 % | 0.17 % | -0.87 / -0.82 % | 5/10 | 0/1 | 196,529 / 196,421 |
| | hold-out | 16 | 39 | 0.11 % | 21 % | 0.14 % | -0.95 / -0.79 % | 8/13 | 2/1 | |
| P05 70210 | fit | 25 | 84 | 0.65 % | 16 % | 0.72 % | -14.9 / -16.3 % | 2/6 | 2/2 | (RFQ, no anchor) |
| | hold-out | 15 | 39 | 1.21 % | 26 % | 1.22 % | -14.9 / -16.3 % | 0/4 | 1/0 | |
| P05 70240 | fit | 25 | 84 | 0.41 % | 7 % | 0.47 % | -0.05 / -0.05 % | 1/5 | 3/1 | |
| | hold-out | 15 | 43 | 0.92 % | 7 % | 0.55 % | -0.05 / -0.05 % | 0/2 | 4/3 | |
| P05 70250 | fit | 25 | 66 | 0.76 % | 26 % | 0.94 % | -20.3 / -20.5 % | 3/11 | 1/1 | |
| | hold-out | 15 | 45 | 3.55 % | 29 % | 6.77 % | -5.9 / -20.5 % | 1/8 | 4/3 | |
| P07 70610 | fit | 18 | 71 | 0.44 % | 0 % | 0.38 % | -4.84 / -4.92 % | 17/17 | 1/1 | 299,241 / 298,853 |
| | hold-out | 17 | 59 | 0.78 % | 9 % | 0.65 % | -4.84 / -4.92 % | 9/14 | 0/0 | |
| P08 70710 | fit | 21 | 64 | 0.90 % | 8 % | 0.56 % | -8.42 / -9.43 % | 17/20 | 1/3 | 960,309 / 958,493 |
| | hold-out | 18 | 60 | 1.11 % | 20 % | 0.89 % | -6.71 / -8.05 % | 10/18 | 2/4 | |
| P10 70410 | fit | 25 | 43 | 0.17 % | 21 % | 0.17 % | -0.40 / -0.40 % | 15/22 | 2/0 | 1,328,927 / 1,569,274 |
| | hold-out | 24 | 43 | 0.33 % | 19 % | 0.37 % | -0.40 / -0.40 % | 17/23 | 2/0 | |
| P11 70140 | fit | 29 | 138 | 0.92 % | 15 % | 1.72 % | -1.06 / -3.19 % | 3/16 | 0/0 | 722,500 / 722,576 |
| | hold-out | 35 | 180 | 0.96 % | 11 % | 1.68 % | -1.06 / -3.19 % | 7/22 | 0/0 | |
| P18 70740 | fit | 22 | 77 | 0.96 % | 13 % | 1.17 % | -7.36 / -8.20 % | 12/21 | 0/0 | 222,651 / 221,512 |
| | hold-out | 20 | 73 | 1.09 % | 14 % | 1.20 % | -7.36 / -6.76 % | 10/18 | 1/0 | |

Overall: replies are reproduced within ~0.1-1.2 % of the opening value on held-out games for 11 of
12 suppliers; statuses agree on 70-93 % of replies; the C_best anchor is matched within 0.1 % for
P01, P02, P04, P07, P08, P11, P18.

**Where the simulator is weak (honest list):**
- **Timing of the final offer** is the weakest family: same first-final round in only 1/5 (P01),
  6/12 (P02), 0/3 (P03), 1/8 (P05 70250), 7/22 (P11) held-out threads. The real trigger is not a fixed
  reply count; it looks state-dependent (little room left, or an LLM judgement). The sim uses
  `final_round` OR room < 0.2 % of opening.
- **P11 (quality)**: the sim's first counter is a grid step too generous (-3.2 % vs -1.1 %); the
  real supplier moves one 0.50 step at a time and links price to ppm/chargeback in ways a single
  linear `ppm_cost` does not capture.
- **P05 70250**: one fit-half/hold-out split makes its hold-out error large (3.5 %) - its first
  counter depends on rival offers being cited, and the hold-out half has games where it hardly moved
  (median -5.9 %). RFQ rival dynamics ("half now, rest next round") are modelled crudely; the real
  RFQ suppliers also concede on repeated identical buyer offers, which the sim only does when a rival
  offer id is cited.
- **P10 / P03 C_best**: the sim's C_best is 18 % (P10) and 2.6 % (P03) above the real one - the real
  suppliers accept volume / contract-length packages (P10: 23,400 pcs for 24-36 months) far below
  anything conceded in the archive; the volume/contract value (`vol_elast`, `contract_bonus`) is fitted
  only from replies, and no archived game reached those packages.
- **Walks**: walk-from-open is under-identified (about 10 events). `patience`/`insult`/`min_move` and
  "no buyer move -> patience -1" are assumptions from the brief ("it gives nothing without a move from
  you"), not measured; the hold-out shows both missed and extra walks (P01 2 real vs 5 sim).
- **Words do not matter** in the sim: tone, questions, urgency leaks, threats, appreciation, documents
  (cost-breakdown XLSX, 8D, delivery schedules) and the LLM's free judgement ("identical messages need
  not get identical replies") are not modelled. Bodies are short templates with true hints
  ("Faster payment is welcome ..." when its cash rate >= 9 %).
- Fact relevance is approximate: existence, supplier/part match, idx window and the % next to the ids;
  quote/cost figures are not checked.
- The 9 never-hosted practice cases (P06, P09, P12-P17, P19) have no traces: their standard terms,
  openings (letter `asked_price` where one exists, else current price x a draw) and behaviour come
  from the pooled ranges.

## 5. The stress set (`gen_cases.py`, `cases/`)

190 cases = 19 practice templates x 10 variants (seed 20261011), same parts, suppliers, refs, buyer
block, negotiable fields and options. Hosted templates: opening price x U(0.96, 1.05). Each supplier
draws an archetype: `mirror` 44 % (fitted parameters, jittered: rates/fractions x lognormal(0.35),
room x U(0.6, 1.6), levers x U(0.5, 1.6), final round -1..+2, mild walk rules), and the "strangers"
`boulware`, `conceder`, `data_driven` (small base room, 3-5 big levers), `cash_short` (rate 12-24 %),
`walker` (patience 1-3, hazard 5-15 %), `monopolist` (room <= 1 %, levers ~0, early final), ~9-10 %
each. Non-hosted templates draw from pooled ranges (grid by price, rate 3-12 %, base room 0.5-12 %,
levers 0.2-2 % per type with p = 0.4, first_frac 0.05-0.9, recip 0.2-1.2, cap 0.2-3 %, final round
2-7, p_walk_final 0.4-1.0, patience 2-6, lead-time premium 0.2-0.8 %/day, ...). Supplier full cost
from F10 (hosted, +-1.5 points) or 0-6 points above the sustainable margin. `_hidden` holds all of it
plus c_open, c_best, c_alt and the best package.

## 6. Walk rules recalibrated (walk model 2, `cases_v2/`)

`walk_stats.py` measures the walk-relevant events in the real replies (`walk_stats.json`); `walk_check.py`
replays every real buyer e-mail through the simulator with the `mirror` walk parameters of walk model 1
(stress/cases) and walk model 2 (stress/cases_v2) and counts the same events (`walk_check.json`).
`stress/cases/` is unchanged (`gen_cases.py --walk-model 1 --out stress/cases` regenerates it byte for byte, and
the v1 report reproduces with the current simulator); `cases_v2/` uses the same seed and the same draws except the
walk parameters, which come from their own random stream.

| rule | real games | sim replay, model 1 | sim replay, model 2 | stress run v1 (cases) | stress run v1_c2 (cases_v2) |
|---|---|---|---|---|---|
| RFQ: push past a final offer -> walk | 2 / 40 pushes (34 had no sheet; 4 sheets 0.06-2.8 % below -> no walk; 6.5 % and 13.2 % below -> walked, both game d9af85e000ab3d4d) | 2 / 35 | 1 / 35 | 14 / 16 pushes | 11 / 19 pushes |
| single: push past a final -> walk / agreed / repeated | 6 / 4 / 1 of 11 (meets final -> agreed 1/1; within 1.6 %: 1 / 3 / 1; 1.7-6.4 % below: 4 / 0 / 0) | 18 / 6 / 8 of 32 | 16 / 10 / 2 of 28 | no pushes | no pushes |
| open-thread walk (no timeouts) per thread | 7 / 466 = 1.5 % (single 4/346, RFQ 3/120; all at reply 3-4) | 1 / 466 = 0.2 % | 6 / 466 = 1.3 % | 18 / 220 = 8.2 % (16 patience, 2 hazard) | 3 / 220 = 1.4 % (hazard) |
| no-move e-mail -> walk | 2 / 93 (both a first no-move; streak 2 -> final 10/17, streak 3 -> final 6/6) | patience -1 each | no patience effect; streak 2 -> final with p 0.45-0.75, streak 3 -> final | | |
| "insulting" offer (best value > 5 % below the lowest value ever conceded) -> walk | 0 / 253 (0 / 78 at 10 %, 0 / 38 at 15 %) | patience -1 below r_min x (1 - 8-15 %) | removed | | |
| contradicted data -> walk | 0 / 3 | patience -1 | removed (price hardening `trust_penalty` kept) | | |
| 3 timeouts in a row | ends the thread (arena rule) | same | same | | |

Walk model 2 parameters (`gen_cases.walk_v2`):
- per-reply hazard from the 3rd reply on: single 4/541 = 0.74 %, RFQ 3/71 = 4.2 % (the replies at risk in the
  archive); mirror x U(0.6, 1.4), strangers x U(0.5, 2.0), walker x U(1.6, 2.0), so at most about 2x the real rate;
- RFQ push: walk chance ramps from 0 at `rfq_gap0` (~2.8 %, the deepest real push that did not walk) to
  `p_walk_final_rfq` at `rfq_gap1` (~13 %, the deepest real push, which walked); no sheet -> the final is repeated;
- single push: within `small_gap` (~1.6 %) agreed with p 0.45-0.75 / walk 0.1-0.3 / else repeated; further below
  -> walk with p 0.85-1.0 (mirror);
- open-thread patience no longer reacts to insults, slow or no moves, or contradicted data.

Remaining caveat: the agent's RFQ pushes past a final are deep - median 14 % below the bidder's final value
(3.5-27 %) - deeper than every real push except the two that walked, so most of them still walk (11 / 19). The
real evidence for deep pushes is 2 events in one game. Sensitivity: with a flat 5 % walk chance per RFQ push
(depth ignored) the RFQ mean score is the same (0.213), because the walked bidders were not the ones the
agent's deals depended on - the RFQ shortfall is the price of the deals, not the walks.
