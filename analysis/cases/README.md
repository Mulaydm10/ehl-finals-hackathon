# Per-case deep dives (N1)

C_open / C_best / C_alt are **exact** (arena results of one probe session per case: open, save the
openings, walk away; see `openings/<case>.json`, `tools/probe_open.py`). P01 from our earlier sessions.
Score = (C_open − C) / (C_open − C_best). Tools: `analysis/tools/case_dump.py` (raw data),
`case_levers.py` (€ per lever, price per score), `sheets.py` (score any term sheet).

| case | type | goal | supplier | C_open | C_best | 0.01 score = | biggest lever | score-1.0 package |
|---|---|---|---|---:|---:|---:|---|---|
| [P01](P01.md) | price_increase | stabilise | 70110 | 1,153,780 | 1,096,816 | €570 | effective 2027-04-01 (+0.72) | €138.20 Apr 90 d · €133.65 Jan 60 d |
| [P02](P02.md) | price_increase | stabilise | 70510 | 2,282,867 | 2,235,514 | €474 | 90 d (+0.64), −1% (+0.48); index clause **costs** | €368 @ 90 d, no clause |
| [P03](P03.md) | renewal | stabilise | 70530 | 4,246,314 | 3,909,043 | €3,373 | 24 months (+0.60) | €429.40, 24 m, 90 d, 4,580 |
| [P04](P04.md) | renewal | routine | 70620 | 198,846 | 196,529 | €23 | 90 d (+0.57); 24 m **costs** above €4.935 | €4.93, 24 m, 90 d |
| [P05](P05.md) | rfq | leverage | 70210/70240/70250 | 305,545 | 223,424 | €821 | price (auction); lead ≤ 42 must-have | ≈ €26.5, lead ≤ 35 |
| [P07](P07.md) | bundling | routine | 70610 | 391,027 | 299,241 | €918 | 24 months (+0.48); alt beats opening | €5.00/kit, 36 m, 90 d |
| [P08](P08.md) | raw_material | leverage | 70710 | 1,135,887 | 960,309 | €1,756 | price; 24 m only below €5.89 | €5.10, 24 m, 90 d, no clause |
| [P10](P10.md) | capacity | secure_supply | 70410 | 1,932,492 | 1,328,927 | €6,036 | volume 23,400 (must) + 24 m (+0.47) | €28.10, 23,400, 24 m, lead 42 |
| [P11](P11.md) | quality | quality_first | 70140 | 817,578 | 722,500 | €951 | ppm ≤ 1,500 (must), then price | €43.50 @ 800 ppm, €0 chargeback |
| [P18](P18.md) | raw_material | leverage | 70740 | 295,173 | 222,651 | €725 | price; 24 m | €4.75, 24 m, 90 d, no clause |

**Non-hosted cases (no probe: lever € values exact, C_open / C_best estimated, see each file):**

| case | type | goal | supplier | C_alt | 0.01 score ≈ | biggest lever | target package |
|---|---|---|---|---:|---:|---|---|
| [P06](P06.md) | rfq | stabilise | 70120 / 70150 | none (no deal = 0) | ~€1.3k | price; 14 d pay for cash-short Tarsevi near its floor; tooling 0 | ≤ €200, 0 tooling, lead ≤ 56 |
| [P09](P09.md) | capacity | secure_supply | 70220 | 310,669 | ~€640 | volume 15,600 (+€20k/step), lead 28 (€1,800/day); 1% price = €1.9k | €15.80–16.02, 15,600, lead 28 |
| [P12](P12.md) | quality | quality_first | 70310 | 906,877 | ~€830 | price (1% = €9k); whole quality term ≤ €5.5k | €97.00, ppm 800, chargeback 150, lead 23 |

Cross-case lessons:
- **Contract length vs horizon** decides many cases: with horizon 2 y, a 12-month deal leaves year 2 at the fallback price
  (+ fallback risk). It's a big win when fallback > deal price (P03, P07, P10), and a **loss** when fallback < price (P04, P08 at the opening).
- **Index clauses cost us whenever `index_paths` is positive** (P02 CU +5%, P08/P18 AS +6%). Only accept for a price cut ≥ the clause's € cost.
- **Effective date** (P01) and **payment days** are worth more than they look; compute, don't guess.
- C_best ⇒ the supplier's cash floor; in leverage cases it's far below today's price (P05 −27%, P18 −20%, P08 −8%).
- **Chargeback ≥ cost_per_defect zeroes the quality term** (P12: €300 ≥ €275), so ppm stops mattering in C. Without a ppm must-have, quality data is leverage for price.
- **Relationship charge flips the cash lever near a supplier's floor** (P06, P09): for a cash-short supplier, paying in 14 d can beat a lower price at 60 d.
- **Price at should-cost + sustainable margin = no price room** (P09: €16.02 vs €15.40 at a 4% margin): win on volume and lead instead.
