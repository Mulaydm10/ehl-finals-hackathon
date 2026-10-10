# Playbook: raw_material

A raw-material supplier proposes a new price basis, usually with a surcharge/index clause. Typical
negotiables: `unit_price`, `index_clause` (series, share, deadband 0/3/5%), `payment_days`,
`contract_months`. Practice: P08 (70710 1.4404 bar, hedged), P16 (70720, PPI-C241 clause),
P18 (70740 same bar, small account). All **leverage**.

## What the goal means here
- **leverage:** push price hard. Fallback risk 3%, index risk 1%, no relationship charge. C_best sat far below
  today's price (P08 −8%, P18 −20%): these suppliers have room.

## Prepare (code)
1. **Index path sign decides the clause.** `index_paths` > 0 (P08/P18 AS-14404 +6%, P16 PPI-C241 +3%) → any
   clause costs us ≈ material_share × (path − deadband + index_risk) × spend. Rule of thumb (45% share,
   +6% path): db0 ≈ 3.2% of price, db3 ≈ 1.8%, **db5 ≈ 0.9%**. Accept a clause only for a price cut at least that
   big. If the path is ≤ 0, the clause *helps* us (we get the fall): then ask for it.
2. **Contract months vs fallback:** with horizon 2 y, longer is better only below
   `fallback × (1 + fallback_risk)` (P08: €5.89; P18: €6.31). At openings above it, 12 m looks better;
   at target prices, 24 m wins. Compute at the target, not the opening.
3. **Current price vs opening:** openings were +11% (P08) and +4.5% on a price that had *already* risen 11% via
   the old clause in July (P18).
4. **The supplier's own recent quote/price** (P08 `quote:7300008` at today's €5.45, "material covered until
   March 2027") is the anchor.
5. Drivers: alloy surcharge AS-14404 +5.9% (12 m) but **−0.3% (6 m)**; cold drawing +12.3% / +9.7%.
   The 6-month alloy series is the best checked argument: the series *they* propose is flat.

## Opening move (round 1)
- Accept the *idea* of a fair price basis; reject the increase with data:
  1. AS-14404 6-month change (−0.3%), the clause series is flat.
  2. Our recent PO prices for the part (what it has been charging).
  3. Hedge (if any) in prose, its own words: "covered at fixed prices until March 2027", so no cost increase
     before April.
- Ask for the cost breakdown (open-book suppliers: 70710, 70740).
- 3 sheets, all 24 months:
  - **A:** low price, 60 d, no clause.
  - **B:** slightly higher price, 90 d, no clause.
  - **C:** lowest price **with a db5 clause** (gives it the protection it asked for, priced in).

## Motive → lever (raw material specifics)
- **hedged** (70710, 70730): its costs don't follow the index until the hedge ends → price at today's level
  at least until then; any clause should start after the hedge.
- **proposes a clause** (70720 PPI-C, 70740 AS-1.4404): it values risk transfer → sell the clause for a lower
  base price and a deadband ≥ 3–5%. Never a clause *and* a higher base.
- **open book:** ask for its calculation; challenge the material line with the index.
- **reviewing small accounts** (70740): frame a bigger, longer commitment rather than threats.
- **dual source** (80/20 split between 70710 and 70740): the split is our competition lever: "we're reviewing
  the share". Use it once, calmly, if it won't move. Don't cite the other supplier's IDs.
- **pricing committee:** ≤ 2% steps after the opening anchor.

## Concession path
- Price in steps of ~2–3% from a low anchor (P18: 4.65 → 4.80 → 4.95 → 5.10 → 5.25), holding 24 m and no
  clause. Offer db5 as a late trade if it insists on a clause.

## When to accept
- C ≤ target, or `final_offer` at or below today's price on 24 m (P08 0.54–0.58, P18 0.51).
- Before accepting, check the standing sheet's `index_clause`: a clause slipped in can cost 0.03–0.10.

## When to walk away
- Only if C_alt < best C. Practice alternatives (another bar supplier's quote) were dearer than the openings: don't walk.

## Tone
- Firm, factual, unhurried; it's a commodity negotiation. Appreciate good quality (ppm 30–75) and OTD where true.
