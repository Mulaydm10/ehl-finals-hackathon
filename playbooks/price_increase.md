# Playbook: price_increase

A supplier announces +X% from a date. Typical negotiables: `unit_price`, `effective_date`, `payment_days`,
sometimes `index_clause` or `volume_per_year`. Practice: P01 (70110 foundry, stabilise), P02 (70510 motors,
stabilise), P13 (70230 machining, leverage), P17 (70550 boards, stabilise).

## What the goal means here
- **stabilise** (castings, electrical; A-class single source): relationship charge is live. Land near the
  **cost-justified change**, not below the supplier's floor. Fair, stable, explained. Time and terms > price.
- **leverage** (multi-source machined, raw material): push hard. Fallback risk is small (3%), the relationship
  isn't charged, an index clause is cheap (1% risk) when the path is ≤ 0. A credible walk-away if C_alt < C_open.
- **routine**: accept a fair step quickly; fight only if the ask is far above justification.

## Prepare (code)
1. **Justified change** = Σ cost_driver weight × index change (12 m and 6 m). Compare with the ask.
   History: suppliers settle **1–4 pts below their ask** (mean 2.5), close to the justified change.
   P01: ask +9.5% vs justified +2.3% (fight). P02: ask +6.5% vs +11.2% (12 m) but +4.6% (6 m): use 6 m.
   P17: ask = justified (don't fight the index; trade terms).
2. **Notice check:** letter `doc:` notice days vs contract `ctr:` (clause 3.1). If short, the announced date is
   invalid. **Read the clause precisely:** "90 days before the end of the calendar year" means a letter in
   September validly moves **1 January**, not the announced November date. The argument wins January, not April.
3. **Effective-date value:** units before the date are bought at the current price. P01: 2027-04-01 alone was
   **+0.72 score at the asked price**, worth more than any price cut. Compute it for every date option.
4. **Payment days:** +30 d = 0.67% of spend for us (8%). If the supplier is cash-short, faster payment is
   worth more to it than to us → trade days for price. If not, ask for 60–90 d and keep its headline price.
5. **Should-cost:** if the current price is already below should-cost (P01 −4.6%, P02 −7.1%, P17 −7.8%), the
   supplier is thin. **Don't cite should-cost** and don't push its cash value below cost + sustainable margin.
6. **Index clause (if negotiable):** check `index_paths`. P02 copper path +5% → the clause costs us 0.4–0.9
   score. Refuse unless it buys a larger price cut.

## Opening move (round 1)
- One line thanking it for the letter and acknowledging the cost pressure it names.
- **Strongest checked argument first**: the notice-period claim if short; else the index that moved *less*
  than its story (P01: electricity −3.7%; P02: copper 6-month +16% vs 12-month +47.7%).
- Then one labour or second driver index. Say in prose what the weighted drivers justify (+2.3% vs +9.5%).
- Ask for its cost breakdown if the dossier says open book.
- 3 term sheets (all below its standing price):
  - **A, cost-justified:** price = current × (1 + justified%), on the earliest *valid* date, 60 d.
  - **B, cash trade:** a bit lower price, faster payment (14–30 d). Use it when it wants faster payment.
  - **C, time trade:** a higher price (closer to its ask) but the **latest effective date** and/or longer
    payment. Lets a proud owner keep his headline number while we win on timing.

## Patterns that worked / failed (P01 replays)
- Verified notice + energy + labour data → "We did not know that, a fair point" and an immediate price cut
  (sessions `e3e0b7be271e9371` 0.85).
- Repeating the same claims in rounds 2–3 → `duplicate`, "we received a lot of material". Bring a **new**
  argument each round, or none.
- "We need a better price" with no data: it still conceded €1–3 per round (0.58). Patience works; data works faster.
- Offering more than its ask (stock LLM) → instant `agreed`, score 0.

## Motive → lever (price increase specifics)
- **data-naive owner** (70110, 70230): the driver indices disarm it. Explain them kindly ("we pulled the indices").
- **partnership pride** (70110): it once held the old price for a quarter → ask for the same now
  (effective date later), framed as mutual partnership.
- **pricing committee** (groups such as 70510): keep each step ≤ 2%. Note: P02's score-1 point was only
  −0.8 to −2.1% off the ask, so it's inside the KAM's authority. Don't trigger the committee for nothing.
- **hedged** supplier: rising-index stories don't hit its cost until the hedge ends → a later date or the
  current price until then.
- **below cost once** ("accepted below full cost to keep the volume"): fragile margin. Stabilise case → give
  it time/terms, not a deep price cut.

## Concession path
- Lead with the biggest non-price lever (date or payment), then price in shrinking steps (€ ≈ 1% → 0.7% → 0.5%).
- Target = cost-justified change; acceptable = no worse than **ask − 2.5 pts** on an equal-term basis.
- Each step must come with a reason or a trade ("for a 1 April start we can accept €X").

## When to accept
- C ≤ target, or `final_offer` and C < C_alt. In stabilise cases a deal at the cost-justified level with a later
  date usually scores 0.8–1.0. Don't burn rounds for the last 0.05.
- Before accepting: is the standing sheet's `effective_date` the one you wanted? Is payment what you think?

## When to walk away
- Only if C_alt < every acceptable C and the supplier has said `final_offer`. In practice cases the alternative
  was always dearer than the opening (P01, P02, P13): **don't walk**.

## Tone
- stabilise: warm, respectful, data-led, "partnership both ways". No threats.
- leverage: firm and factual; mention the alternative only if it's cheaper than the ask.
