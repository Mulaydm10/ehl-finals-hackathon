# Playbook: renewal

A framework contract expires; the supplier sends a renewal offer, often with a higher price and a short term.
Typical negotiables: `unit_price`, `payment_days`, `contract_months`, sometimes `volume_per_year`,
`index_clause`. Practice: P03 (70530 converters, stabilise, price frozen), P04 (70620 bearings, routine,
"not strategic"), P14 (70560 cables, stabilise, copper index), P19 (70640 C-parts, routine).

## What the goal means here
- **stabilise:** long, stable agreement at a fair price; relationship charge live (P03: sustainable margin 8%,
  €28k per point per year!). Don't squeeze below cost + margin. Terms and duration first.
- **routine:** small money. Tiny score span (P04: €23 = 0.01). Two good moves and close. 2–4 rounds.

## Prepare (code)
1. **Contract months vs horizon** (the decisive lever in most renewals). Year 2 of a 12-month deal is bought
   at `fallback × (1 + fallback_risk)`.
   - Deal price **below** that → 24/36 months is a big win (P03: **+0.60 score** at the asked price).
   - Deal price **above** that → 12 months is cheaper (P04: 24 m at the ask = −0.62). It flips at the
     fallback-with-risk price. Compute it.
   - 24 = 36 months for us when the horizon is 2 y; 36 is free extra security for the supplier, a cheap gift.
2. **Volume** = the need. Over-commit is paid (P03: 5,496 vs 4,580 = −1.2 score); under-commit buys the gap at
   the fallback price.
3. **Payment days**: 90 d is often worth more than a 1% price cut on small-span cases (P04: 90 d = +0.57).
4. **The renewal ask vs current price and the drivers.** Openings were +6.2% (P03), +13% (P04) on current.
   Drivers justified +3.7% (6 m, P03) and +0.8% (P04).
5. **Supplier floor:** C_best tells you its cash value floor. P04's was near its ask (≈ €4.87 vs €4.96): don't
   expect a big price move from a "list price" distributor; win on terms.
6. **Index clause** (P14 copper, path +5%): costs us. Same rule as everywhere: refuse or price it.

## Opening move (round 1)
- Answer its renewal e-mail: confirm our expected volume (it usually asks) and the duration we offer.
- **Lead with the commitment** (24–36 months at the full need). It's what renewals sell.
- One or two checked arguments: the 6-month driver change if lower than its ask; our PO prices (flat for
  years, P04/P07); its good quality (appreciation, e.g. 0 ppm at 70530).
- 3 term sheets, all at the full need:
  - **A:** longest term, moderate price (≈ current + justified), 60 d.
  - **B:** 24 m, lowest price, its standard payment.
  - **C:** 36 m, 90 d, a price closer to its ask (committee-safe).

## Motive → lever (renewal specifics)
- **price frozen / "no reductions this year"** (70530, 70420, 70570, 70630): the freeze is on going *below
  list*. An opening above list can still be argued back toward list. Never ask below list; win on months,
  payment, call-off flexibility.
- **"only multi-year volume agreements change prices"** (70620, 70440, 70630): offer 24–36 months, but check
  the flip price first (P04: only worth it below €4.935).
- **"not strategic" / reviewing small accounts** (70620, 70650): low leverage, slow replies. Simple, friendly,
  quick. Don't argue quality; it's looking for a reason to drop us.
- **pricing committee** (groups): steps ≤ 2%. P03's score-1 price was exactly −2.0% from the opening:
  inside one committee-free step **if** 24 m + 90 d are already agreed.
- **open book** (70620): ask for the calculation; negotiate on its elements.
- **hedged copper** (70560): the copper rise isn't in its cost yet → hold price, no clause.

## Concession path
- Lock duration first (it's free for the supplier: security, not cash), then payment, then price in
  ≤ 2% steps. Once duration is agreed, every € of price counts double on a 2-year horizon.
- Stabilise: stop at the cost-justified level; the relationship charge eats further cuts.

## When to accept
- routine: as soon as C ≤ target or after 2–3 rounds with a fair sheet. Don't spend rounds for 0.02.
- stabilise: 24+ months at ≤ the ask with 60–90 d already scores 0.7+ (P03); take it if the supplier says
  `final_offer`.
- **Check the duration on its standing sheet before accepting.** A 12-month sheet at a good price can score
  worse than a 24-month sheet at a higher price (P03, P07).

## When to walk away
- Only if C_alt < C of the best sheet you can get. P04 and P03 alternatives were worse than the openings: don't walk.

## Tone
- Cooperative, structured, process-aware. Groups: acknowledge their rules (freeze, committee) and ask for
  what fits inside them. Family firms: personal, appreciative.
