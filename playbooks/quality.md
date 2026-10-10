# Playbook: quality

A supplier with a red scorecard; our escalation letter asks for an improvement plan, quality commitments
and cost recovery. Typical negotiables: `ppm_commitment` {300, 800, 1500, 2500}, `chargeback_eur_per_complaint`
{0, 150, 300, 500}, `unit_price`, sometimes `lead_time_days`. Practice: P11 (70140 brackets, PL foundry,
cash-short, ppm ≤ 1,500 must-have, payment fixed 60 d), P12 (70310 sheet metal, we are 11% of its turnover,
lead options, alternative = current contract).

## What the goal means here
- **quality_first:** defects and late deliveries cost more than a few cents of price. **Cost per defect is
  large** (P11 €450). No relationship charge, but these suppliers are often fragile (restructuring, cash).

## Prepare (code)
1. **Must-have ppm** (P11 ≤ 1,500). The opening may ignore it entirely (P11 opened at **6,400 ppm**). Fix first.
2. **Quality cost** = volume × ppm/1e6 × (cost_per_defect − chargeback). Chargeback ≥ cost_per_defect → 0.
3. **Chargeback efficiency:** a chargeback costs the supplier chargeback × its *real* ppm per unit and saves
   us chargeback × *committed* ppm. When real ppm > committed (always for red suppliers), **a chargeback
   costs it more than it saves us** (P11: €500 at 1,500 ppm saves us €0.68/pc, costs it ~€1.19/pc). It'll
   price that in. → With cash-short suppliers prefer **price cuts over chargebacks**.
4. **A tighter ppm commitment without a chargeback** costs it no cash and is worth up to
   (1,500 − 300) × 1e-6 × €450 = €0.54/pc to us (P11). Credible targets: one step below its real ppm
   (2,376 → 800 with an 8D plan); 300 is a stretch.
5. Price vs current and drivers: P11 opened +4.1% vs +2.3% justified; history shows it *cuts* at renewals.
   C_best was −4.3% vs today's price.
6. **Lead time** options (P12): € per day beyond need; quality cases still pay for lateness.

## Opening move (round 1)
- Reference our escalation letter; the scorecard numbers are facts (cite **one** `sc:` claim per message;
  the same ID twice is `duplicate`: ppm first, OTD in a later round).
- Ask for the **8D report** and a binding ppm commitment ≤ the must-have.
- Show the business upside: volume growth (`fc:` +20% at P11) for a supplier that fixes quality.
- 3 sheets, all within the must-have:
  - **A:** ppm 800, chargeback 0, price below today's.
  - **B:** ppm 300, small chargeback (€150), price near today's.
  - **C:** ppm 1,500, chargeback 0, lowest price.

## Motive → lever (quality specifics)
- **cash-short / restructuring / "cannot sign anything that lowers our margin"** (70140): no big chargebacks;
  offer what helps its cash that we *can* give: **reliable on-time payment** (we're late on 93%), and
  faster payment if `payment_days` is negotiable. Price cut + realistic ppm commitment.
- **we are a large share of its turnover** (70310 11%): strong leverage; its survival needs our volume.
- **wants commitment**: volume and duration as the reward for a ppm commitment.
- **escalation**: firm, documented, not personal. The data speaks.

## Concession path
- Round 1 fixes ppm ≤ must-have (non-negotiable). Then price: small steps up from a low anchor
  (P11: 43.0 → 43.5 → 44.0 → 44.5 → today's 45.15). Use a €150 chargeback only as a sweetener for a tighter ppm.
- Don't trade ppm above the must-have for any price.

## When to accept
- Must-have met, C ≤ target; or `final_offer` at ≤ today's price within the must-have (P11: 0.68).
- **Read the standing sheet's ppm and chargeback before accepting**: a ppm over the must-have scores 0.

## When to walk away
- If C_alt < best compliant C. P11's alternative (70190, €53.56 + tooling) was far dearer: don't walk.
  P12's alternative is the current contract: compare carefully; walking is real there if it won't commit.

## Tone
- Firm on quality, respectful and constructive on money. One clear message per round. No humiliation:
  a red supplier in restructuring that panics may walk.
