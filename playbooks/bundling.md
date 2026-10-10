# Playbook: bundling

We move several parts (a kit) from several suppliers to one, for one kit price. Typical negotiables:
`unit_price` (per kit), `payment_days`, `contract_months`. Practice: P07 (70610 fastener kit, routine),
P15 (70430 seal kit, routine). The alternative is usually **today's terms continuing** (`current_contract`).

## What the goal means here
- **routine:** fewer suppliers, less process cost. But the span can be large (P07: €91.8k, C_best 13%
  below the opening): bundling volume buys real price. Aim for a quick but well-priced deal.

## Prepare (code)
1. **Today's kit cost** from the memo's quantities × current prices × quotas. It should equal
   `current_unit_price` (P07: €6.29 ✓). Also compute the kit at **this supplier's own list prices** for the
   parts it already sells (P07: ≈ €5.95, with the part it doesn't sell at the other supplier's price).
2. **The bundle's size for it:** kit spend per year vs what we buy from it today (P07: ~€170k vs ~€40k,
   **4×**). That's the argument.
3. **Contract length vs horizon** (decisive): with horizon 2 y and a 12-month offer, year 2 is at the fallback
   (+risk). P07: 24 months = **+0.48**; at 12 months no realistic price scores well. Check the flip price.
4. **The alternative may beat the opening** (P07: walking away = 0.12 because today's 24-month terms beat a
   12-month offer). Know the price at which a deal beats walking.
5. Drivers (fasteners +1.7%, labour +2.7%) and price history (flat for 3 years at P07) show no cost push.

## Opening move (round 1)
- Positive framing: "we're choosing one partner for the whole kit": volume, years, fewer deliveries.
- State kit volume and the duration we offer (24–36 months).
- Arguments: the flat driver index; our PO prices for its parts (flat since 2023); forecast growth for the
  parts it doesn't supply yet (`fc:` of that part).
- 3 term sheets, all 24–36 months:
  - **A:** 36 m, lowest price, 60 d.
  - **B:** 24 m, low price, its standard payment.
  - **C:** 36 m, 90 d, a slightly higher price.

## Motive → lever (bundling specifics)
- **needs volume / second shift idle:** the kit fills it. Ask for the bundle discount explicitly.
- **"we want one supplier for the kit" (our memo):** the bundle is our gift; price it.
- **approval ladder:** a 10–15% bundle price needs the boss. That's fine. Give a strategic reason
  (single source, multi-year volume) so it escalates *for* us.
- **open book** (70430): ask for the cost breakdown per component.
- Don't let it carve out a component it doesn't stock: the kit must be complete or the deal isn't a bundle.

## Concession path
- Hold 24–36 months non-negotiable (it's the whole value). Trade payment 90 → 60 → 45 d as sweeteners while
  price moves down in ~2% steps.
- P07 ladder: €4.95 → 5.10 → 5.20 → 5.35 (scores 1.0 → 0.91 → 0.86 → 0.76 on 24–36 m).

## When to accept
- Any 24–36-month sheet that reaches target, or `final_offer` above the walk-away line. Routine: ≤ 4–5 rounds.
- **Never accept 12 months** unless its C beats walking (P07: only below ~€5.38).

## When to walk away
- When the best standing C > C_alt (today's terms). Walking is legitimate here: say "then we keep today's
  arrangement" as a calm, credible fallback once it stalls above that line.

## Tone
- Positive, growth-oriented, simple. No threats needed; the volume is the leverage.
