# Playbook: rfq

2–3 suppliers quote for a (often new) part in parallel threads. Accepting one ends the case. Typical
negotiables: `unit_price`, `payment_days`, `lead_time_days`, sometimes `tooling_eur`. Contract months and
volume are usually fixed. Practice: P05 (machined shaft, 70210 / 70240 / 70250, leverage, no alternative),
P06 (castings, 70120 / 70150, stabilise, tooling negotiable, no alternative).

## What the goal means here
- **leverage:** a real auction. In P05, C_best was **26% below the cheapest valid opening and 28% below
  should-cost**: at least one bidder has a very low floor. Price is almost everything (−€1 = 0.10 score;
  payment and lead are worth ~0.02–0.05).
- **stabilise** (P06): still competitive, but the winner must stay healthy (relationship charge on the
  awarded supplier). Don't drive a cash-short bidder below cost + margin.

## Prepare (code)
1. **Valid openings only.** A quote that breaks a must-have (P05: 70240's lead 52 vs ≤ 42) doesn't count
   for C_open, but its *price* is the best anchor you have. Ask it to fix the must-have.
2. **No alternative = no deal scores 0.** Never end without a deal; never let a bidder sense that.
3. Per bidder: motives, capacity (free capacity vs fully booked), cash (equity, payment e-mails), quality
   (ppm/OTD), country cost base. Rank who has the lowest floor:
   free capacity + cash need + "reference customer" (70250) > idle shift + data-naive (70210) > full order
   book (70240, cheap price but slow and unreliable).
4. **Lead-time cost:** € per day beyond the need. Know which lead options are free.
5. **Tooling (if negotiable):** paying tooling up front costs us the € once; to a cash-short supplier
   up-front cash is worth more → trade tooling payment for unit price when the unit saving × volume ×
   years > tooling €.
6. Quality: ppm differences are usually small € (P05: €0.5–1.3k), so don't over-weight them in leverage cases.

## Opening move (round 1, to every bidder at once)
- Same core message to all: firm volume × months, start date, "we're deciding this round of quotes".
- **Rival offers are checked facts.** Cite the best competing `offer:<id>` with its price to the *other*
  bidders ("We have an offer at EUR 31.50 per piece (offer:…)"). It counts once per bidder; citing reveals it.
- To the cheapest bidder that breaks a must-have: "your price works if you meet lead ≤ 42; the contract
  is the binding commitment you asked for".
- Per-bidder sweeteners from their motives: faster payment (cash), volume for idle capacity, reliable
  payment (overdue invoices), reference customer.
- 3 sheets per bidder, all below the best valid competing C. Vary payment and lead, not just price.

## Running the auction (rounds 2+)
- Every round, recompute the leader by **C**, not price (payment, lead, tooling and quality differ).
- Tell each trailing bidder, with a fresh rival `offer:` ID, what it must beat. Don't lie: claims are checked.
- Step targets down together (e.g. €29 → €27.5 → €26.5). Bidders that stop moving and say `final_offer`
  are out of room.
- Keep at least one **valid** offer standing at all times (must-haves met).
- Don't show the leader its rivals' worse prices; only cite better ones.

## Motive → lever (RFQ specifics)
- **free capacity / looking for customers / second shift idle:** the strongest price mover. Offer the full
  volume for the contract term.
- **wants faster payment / low equity:** 14–30 d for a lower price; costs us ~1% for 46 days.
- **full order book / "only against a binding commitment":** a fixed 24-month contract *is* that commitment.
  It'll be slow and expensive on lead; use it as the price anchor.
- **we pay late (overdue invoices):** promise reliable payment. Free.
- **values us as a reference:** appreciation, mention the new series.

## When to accept
- When the two best bidders have stopped moving (`final_offer`, or the same price twice), accept the
  lowest-C valid sheet. By round 7–8 at the latest (all threads run in parallel in the wave's 8 minutes).
- Accepting ends **all** threads: double-check must-haves and the standard terms (quote PDF) of the
  winner's missing fields.

## When to walk away
- Never in a no-alternative RFQ. With an alternative, only if every valid sheet is dearer than C_alt.

## Tone
- Businesslike and competitive, never hostile: these are future suppliers. Warm with bidders that value us.
