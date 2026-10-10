# Playbook: capacity

A bottleneck supplier can't confirm our forecast (allocation, full order book). We must secure the volume
and lead time first. Typical negotiables: `unit_price`, `volume_per_year`, `contract_months`,
`lead_time_days`, sometimes `payment_days`. Practice: P09 (70220 machining, secure_supply, lead ≤ 42),
P10 (70410 seals, secure_supply, volume ≥ 22,230, no alternative).

## What the goal means here
- **secure_supply:** coverage of the full need and a healthy supplier first. Fallback risk is **25%** on
  uncovered need, late delivery costs **€1.8–2.4k per day**, the relationship charge is live (P10: sustainable
  margin 10%). Price comes last, but there's often a lot of it (P10: price 23% above should-cost).

## Prepare (code)
1. **Must-haves:** volume ≥ X or lead ≤ Y. Usually only one option qualifies (P10: only 23,400). The opening
   typically breaks it (P10 offered 19,890).
2. **Structure value:** P10 at the *opening price* with the right structure (23,400 / 24 m / lead 42) already
   scores **0.68**; today's price on that structure scores 0.86. Get the structure, then work on price.
3. **Months vs horizon:** with horizon 2 y and fallback +25%, 24–36 months is worth ~0.47 (P10).
4. **Lead time:** € per day × days beyond need (one-off in C). P10: lead 54 vs 42 = €28.8k (0.05). Lead 56
   costs ≈ €0.72/pc on P10's volume; trade it only for a bigger price cut.
5. **Should-cost margin:** if price ≫ should-cost (P10 +23%), there's room, but keep the supplier's margin
   ≥ sustainable (P10: don't go below ~€27 on a €24.31 cost).
6. Volume above need is paid in full; volume below need is bought at fallback +25%. Match the need.

## Opening move (round 1)
- Acknowledge its capacity situation; don't sound desperate (no "line down", no "no alternative").
- **Offer what it asked for**: a firm, binding, long commitment ("binding 36-month agreement for 23,400 pc a
  year = 70,200 pc", more than the 12-month commitment it asked for).
- Ask in the same breath for: full allocation of the need, lead ≤ need, price held.
- Arguments: should-cost (if price ≫ cost), the driver change (P10 +1.3% vs +7.7% asked), and the forecast
  (`fc:`) to explain why we need more than last year's call-offs. OTD only to justify lead-time guarantees.
- 3 sheets, all meeting the must-have:
  - **A:** 36 m, lead = need, lowest price.
  - **B:** 24 m, shorter lead, price nearer today's.
  - **C:** 36 m, longer lead (if allowed and not a must-have breach), lowest price (lead traded for price).

## Motive → lever (capacity specifics)
- **allocation by last year's call-offs:** show the forecast and commit firmly; allocation follows commitment.
- **"only against a binding 12-month commitment":** give 24–36 months. It's free security for it.
- **approval ladder:** price steps ≤ 2%; the commitment is the reason for the boss to approve.
- **cash-short** (if any): payment days (when negotiable) for price.
- **we pay late:** promise reliable payment.

## Concession path
- Never concede on the must-have or below 24 months. Trade lead time ↔ price, then price in €0.30–0.50 steps.
- Accept today's price on the full structure early if the supplier is stiff: it's already 0.86 on P10.

## When to accept
- As soon as must-haves + ≥ 24 m + lead ≤ need are on a standing sheet at ≤ today's price. Push price only while
  it keeps moving.
- By the last rounds accept any must-have-compliant, ≥ 24-month sheet. No deal = fallback +25% = score 0.

## When to walk away
- Never when there's no alternative (P10). With an alternative (P09 quote), only if it covers the need, meets
  lead and is cheaper in C.

## Tone
- Partner-like and steady; firm on volume, flexible on form. "We're ready to commit long-term; we need the
  full volume secured."
