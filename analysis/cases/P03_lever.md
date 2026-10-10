STATUS: DONE (P03 deep lever analysis) - 2026-10-11 ~00:45, cloud session, offline only (0 arena sessions, no LLM calls).
Target: beat team "+=" 0.94449 (P03 record). Ready-to-run agent: `analysis/agent_variants/noidea_p03.py`, a subclass of
`noidea_neel.py`, the agent that holds our 0.9363.

# P03: beat "+=" with 431.21 @ 90 d or lower; the two data kinds we never sent are the only route

## 1. The board, decoded to the cent
- C_open is 4,246,314.02 and C_best is 3,909,043.10 in every P03 game.
- C_deal = C_open - EUR saved; the arena breakdown gives the structure.
- The supplier model below reproduces all 7 live relationship charges exactly (error 0.0).

| team | EUR saved | score | its deal (exact C match) |
|---|---:|---:|---|
| **"+=" (record)** | 318,549 | **0.94449** | **431.22 @ 90 d / 36 m** (24 m is the same; 428.19 @ 60 d also matches but is unlikely: its 60-d price runs 1.47 under its 90-d one) |
| NoIdea (us) | 315,776 | 0.93627 | 431.58 @ 90 d / 36 m (2483e389, 14ab701c) |
| pegasus | 315,385 | 0.93511 | 431.63 @ 90 d |
| Codacabana | 313,651 | 0.92997 | 431.85 @ 90 d (or 425.85 @ 30 d) |

**+= is 36 cents under us at the same structure: one more cut, the size of one data kind.**

Score at 90 d / 36 m / 4580 a year (C with the fitted relationship charge; 1 cent ≈ 0.00023):

| price | 431.67 | **431.58** | 431.40 | 431.30 | **431.22** | **431.21** | 431.10 | 431.00 | 430.50 | 430.00 | 428.49 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| score | 0.9342 | 0.9363 (us) | 0.9404 | 0.9427 | 0.9445 (+=) | **0.9447 (beats)** | 0.9472 | 0.9494 | 0.9603 | 0.9708 | 1.0000 |

## 2. The supplier, fitted exactly
- **Full cost EUR 395.30.** Its money is worth **6.10% / year** (sum of squared errors 0.0 over 7 deals).
- Its margin at 431.58 @ 90 d is 7.47%, against the 8% the case calls sustainable.
- Relationship charge = EUR 28,360 x soft(8 - margin) x 2 years. It is EUR 1,620 at 431.58 and rises as the price falls, but **a lower price always wins**: score 1.0 is reached at 428.49, a 6.8% margin.
- **Price ladder (15 games):** price = its 90-day stop 433.08, minus one cut per NEW verified data kind it takes. The cuts:

  | kind | cut (EUR) |
  |---|---:|
  | should-cost | 0.79 |
  | electronic components -2.27% | 0.48 |
  | forecast +10.3% | 0.14 |
  | copper -2.21% | 0.06-0.07 |
  | labour -0.26% | 0.02-0.03 |
  | OTD / quality / flat order run | 0 |
  | 2nd window of a series | duplicate |

  Together they take 433.08 down to 431.58.
- **Asks below its standing price** were never agreed (431.26-431.81: 0 of 9). Identical inputs give identical answers.
- **It goes final** at its reply to our 5th message.
- **Its words:** "frozen all price reductions until December 2027 ... We can talk about the terms instead - payment, volume or contract length"; "should you require a lower price, we invite you to propose shorter payment terms"; "A binding higher volume would help us".

## 3. Every lever, with what it is worth if it works
| # | lever | score if it works | evidence | risk | verdict |
|---:|---|---:|---|---|---|
| 1 | **Our order PRICE PATH by ID** (round 2): "Our orders for this part rose from EUR 400.19 to EUR 412.74 within nine months (po:4500013355-10, po:4500014465-10)" | **≥ 0.9447 if it cuts ≥ 0.37** | the same claim form was **taken** by P08 (d0708ed1: "we took it into account", 0.912), P18 and P10. P03 only ever got the FLAT order run ("does not change", 0). Dhruv's `year_rise_path` skips price-frozen suppliers, so it was **never sent to P03** | shrugged as "price history" -> 0, no trust cost (true, 2 IDs, 2 order prices) | **IN THE AGENT** |
| 2 | **Its own quote by ID** (round 3): quote:7300003 EUR 412.74, 5 Sep 2026, valid 30 days (still valid on 30 Sep), "Prices as per current list" | same | a kind never cited in 15 games (task 17, never played) | "irrelevant" (not in the case refs) -> 0, no trust cost | **IN THE AGENT** |
| 3 | 1 + 2 together | 0.947-0.96 if both cut 0.2-0.5 | - | - | the experiment |
| 4 | payment 90 d (max) | in use | its price drops only 1.47 per 30 days; for us 30 days are worth 2.87 | - | keep 90 d |
| 5 | shorter payment for a lower price ("we invite you to propose shorter payment terms") | ≤ 0.86 | 60 d: 430.20 = 0.90; 30 d: 428.74 = 0.86 | - | never |
| 6 | volume 5496 ("a binding higher volume would help") | 0.0 | we would buy 20% over need | - | never |
| 7 | 24 vs 36 months | equal for us (horizon 2 y) | 36 m "approved by management" every game | - | keep 36 m |
| 8 | bigger index windows | 0 | every series is already at its largest allowed fall (PPI-C2611 -2.27%, CU -2.21%, LCI -0.26%; a window ending before 2025-10 is "outdated", d1bf) | - | done |
| 9 | ask below its standing / a deeper anchor | 0 | 0 of 9 asks below its price agreed; committee prices are data-driven | - | no |
| 10 | quality 0 ppm, OTD 84.6 vs 95%, old QNs, rival quote 466.99, notice period | 0 or negative | measured 0 / outdated / dearer / notice in time | - | no |
| 11 | cross-sell part:350021 (we buy it from 70540; its should-cost 692.92 vs its 2024 quote 672.00) | 0 | not a term; P08 cross-sell 0 twice | - | no |

**What "+=" most likely did:** one more cut of 0.36 at the same structure. That is the size of one taken data kind; electronic components gave 0.48. Levers 1 and 2 are the only honest, checkable kinds P03 has not seen from us.

## 4. The experiment: `noidea_p03.py`
| our msg | refs | expected its price @ 90 d / 36 m |
|---:|---|---|
| 1 | should-cost, forecast +10.3%, electronic components -2.3% (unchanged) | 431.67 (3 of 3) |
| 2 | **price path 400.19 -> 412.74** (2 POs) | 431.67 - cut A |
| 3 | **quote:7300003** (412.74) | - cut B |
| 4 | copper -2.2% | -0.07 |
| 5 | labour -0.3% | -0.02, then its final at our 5th message (accept its primary) |

**Outcomes:**
- **Neither kind taken:** final 431.58 = 0.9363. A tie with our record: never worse, same kinds as before.
- **A + B ≥ 0.37:** **≥ 0.9447, beats "+=".**
- **Each 0.10 more:** +0.023.

**Switches** (top of `noidea_p03.py`):
- `PRICE_PATH_P03 = True`;
- `OWN_QUOTE_AFTER_PATH = True`;
- `P03_CASES = {"case:P03"}`.

Gate: every other case runs `noidea_neel.py` unchanged.

**Run (local):** play P03 with `analysis/agent_variants/noidea_p03.py`, the same way `noidea_neel.py` is played.

## 5. Checks
- **Replays** `replay_cmp_cloud.py noidea_neel.py -> noidea_p03.py`, 14 P03 games:
  - **every price and structure is identical in every turn**; only the claim order changes;
  - in the record games (2483e389, 14ab701c):
    - round 1 is the same;
    - round 2 is the path (was the own quote);
    - round 3 is the own quote (was copper);
    - round 4 is copper;
    - round 5 is labour (14ab: was the flat order run).
  - One old 60-d game (1db1ce07, a path the agent no longer takes) also cites the flat run with the path. That is one repeated PO ID = "duplicate", no cost.
- **Other cases:** P01, P02, P04, P07, P08, P10, P11, P18 (63 threads) all SAME.
- **Supplier model:** the 7 live relationship charges are reproduced to the cent. Score at 431.67 / 431.58 = 0.93418 / 0.93627, exactly the live scores.
- **Not testable offline:** whether the supplier takes the two new kinds (no LLM / arena). The decision is one live game.

**Decision rule after the game:**
- Path "taken" (a cut in round 2): keep it; tell Dhruv that `year_rise_path` should not skip price-frozen suppliers.
- Both shrugged: P03 stays at 0.9363 and "+=" keeps the record. Their 0.36 then came from something not in our data, such as wording.
