# Central layer: what all our games, agents and simulators taught us (Neel, 2026-10-10)

One place for the team's learnings, so every agent version starts from the same facts. Sources: 54 archived live
games (`datasets/runs/`, `tools/replays/raw/`, incl. the supplier **back offices** via Parth's
`tools/replays/fetch_backoffice.py`), Dhruv's changelog (`notes/agent_changelog.md` v1.2–v2.8), Parth's
`analysis/strategy_0.9.md`, Neel's `analysis/replay_lessons.md` / `analysis/run_audit.md`, and the simulators
(`src/eval/offline_eval.py`, `analysis/tools/sim_floorstop.py`, new `analysis/tools/sim_selvbrunn.py`).
Code: `analysis/agent_variants/central.py` (read by `noidea_neel.py`). Data: `analysis/central/*.json`.

## 1. Exact scoring: we can now compute the arena's score of any deal before sending it
Stabilise / secure_supply cases charge `relationship_eur_per_point × soft(8 − margin) × years`, and every deal's
`cost_breakdown` shows that charge. Two deals on different payment terms pin the supplier's **hidden full cost and
cash rate**. `analysis/tools/calibrate_suppliers.py` fits them for every case with such deals:

| case | supplier | full cost | its cash rate | fit |
|---|---|---:|---:|---|
| P02 | Nordmark (70510) | EUR 367.60 (quote 370.96!) | 6.6% | all 4 deals to the cent |
| P03 | Selvbrunn (70530) | EUR 395.30 | 6.1% | all 4 deals to the cent |

Consequences:
- The agent's old guard "never ask below its full cost" (a 0.94 × price guess) was wrong both ways. With P02's real
  full cost it pinned our ask at EUR 369.51 = 0.51; EUR 364 @ 60 d scores 0.96 **with** the charge. With a
  calibrated supplier, rank sheets by the exact charge instead of guarding.
- Our money is worth 8%, theirs 6.1–6.6%: **the longest payment term is always worth more to us than it costs them.**
- P03 house agent 0.9249 = **EUR 432.06 @ 90 d** (or 429.08 @ 60 d). `analysis/tools/p03_calib.py` prints the grid.

## 2. Which data moves a supplier (54 games, `analysis/tools/mine_claims.py` → `claim_reactions.json`)
| data kind | "took it into account" | "does not change our calculation" / "confirms our case" |
|---|---:|---:|
| should-cost (vs its **quote**) | 2 / 2 | 0 |
| rival quote | 3 / 4 | 1 |
| volume forecast (`fc`, a rise) | 12 / 19 | 7 |
| price history (`po`) | 4 / 9 | 5 (P03: 2 of 2 no effect) |
| index change | 4 / 13 | **7× "Your figures confirm our case"** (rising), 2 no effect |
| delivery record (OTD) | 0 / 1 | 1 |
- **26 replies asked "Which figures is that based on? Please send us the data."** All 6 of our P03 round-1 e-mails had
  **no checkable claim** (every driver rose, and nothing else was ranked), so every P03 game started with that question.
- **When every standard window rose, search all checkable windows (≤ 12 months, ending in the last 12 months) for the
  steepest fall of a cost driver** - P03: −2.3% on its main driver took the committee from 432.15 to 431.67 (0.923 → 0.934).
- Never cite a rising index. All 11 "We received a lot of material" (padding) replies came after e-mails with two or
  more index claims; three claims of *different* kinds never drew it (P10, P18).
- Should-cost was ranked against **today's** price (P03: 2.4% → never cited), not against the **quote** (8.7% above).
- Data that is taken moves price a little (P03: −EUR 0.14 per claim at the committee level, Dhruv 8c2816f2d571b367);
  in P18 / P05 it moved a lot. "Verified is not convincing" (api.md): its own economics decide how far.

## 3. How the supplier bots decide (rules confirmed live)
1. **Round 1 does most of the work** (mean price step 1.85% vs 0.4–0.5% later, 107 steps).
2. **Approval ladder:** the sales person stops at the threshold *in its own cash terms* (P03: EUR 431.61 @ 60 d =
   2.00% below the quote at its 6.1% rate, 6 of 6 games). Only the committee goes further: P03 433.08 @ 90 d (3×),
   432.94 @ 90 d with one taken claim. The back office shows the routing: sales person → Credit Control (payment)
   / Legal (contract). **Ask for the committee in round 1** on one structure; Dhruv's v2.7 did and got the
   committee-level 90-day price in round 1.
3. **Stay on the structure it priced.** Hopping payment terms after its committee priced one lost 0.04 (P03
   47a88b4d0bb75ce3: 433.08 @ 90 d → we asked 60/45/30 d → final 431.61 @ 60 d).
4. **final_offer = accept.** Pushing after it: P07 walked (0.12), P08 walked (0.00).
5. **Take the cheapest of all its sheets** incl. `-a` alternatives (+0.03 mean on 15 real finals).
6. **Text moves words, not numbers** (Parth: P07 final at EUR 5.49–5.56 in 7 deals across 5 versions and 2
   models). No prompt injection: api.md says manipulation "has consequences", and the jury reads every replay.
7. Price-freeze suppliers ("frozen until December 2027") still trade on terms: "We can talk about the terms
   instead - payment, volume or contract length." Volume above need costs us more than any discount (P03: 5,496/yr
   = +EUR 0.8M).

## 4. Simulators: what they can and cannot tell us
- They ignore text, data and the relationship charge, so they cannot rank e-mails or claims. Use them for the
  number logic (no hopping, near-close, accept on final), and the calibrated scorer (§1) for the true value.
- `sim_floorstop.py` (live-P04-calibrated) reproduced P04 round by round. `sim_selvbrunn.py` replays P03's real
  rules (2% sales stop, committee price, claim effect, final after 3 holds).
- Today's regression check (`variant_check.py`, 3 simulators × 9 cases): mean 0.941 / 0.945 / 0.825 vs
  Dhruv's v2.8 0.937 / 0.943 / 0.813. The flags on P04/P08/P10/P11 are the same as before these changes.

## 5. P03 (Selvbrunn) in one table
| what we did (7 live games) | its answer | score |
|---|---|---:|
| 3 sheets 60/45/30 d, no data, 36 m (×6, ours) | sales 431.61 @ 60 d, then holds | 0.862 |
| … + escalation to the committee on 90 d (×3) | 433.08–433.09 @ 90 d | 0.8996–0.8998 |
| 1 sheet 90 d / 24 m, volume forecast, committee asked in round 1 (Dhruv v2.7) | 432.94 @ 90 d | 0.903 |
| central layer: 1 sheet 90 d / 36 m, should-cost + volume forecast, committee in round 1, stay at 90 d (27e05be06bb4181f) | committee 432.15 @ 90 d (429.22 @ 30 d) | 0.9228 |
| … + on-time delivery 84.6% as a 3rd claim (3091eac920857dc0) | "does not change our calculation"; 432.15 again | 0.9228 |
| **… + electronic components −2.3% (2025-01 → 2025-10) instead of OTD (2e4bf89ac2967a45)** | **431.67 @ 90 d** | **0.9342 - beats the house** |
| June forecast +23.3% instead of September's +10.3%, index window ending 2025-09 (d1bfa5a91489432b) | index "irrelevant - outdated timeframe"; 432.54 → 432.49 | 0.9146 |
| **proven round 1, then one NEW index series per round: copper −2.2%, labour −0.3% (2483e3891d076863)** | **431.67 → 431.60 → 431.58** | **0.9363 - best** |
| … + quality record 0 ppm in round 2 (14ab701cbfba6767) | 431.61 → 431.58, then "without new data … we cannot adjust" | 0.9363 |
| house agent | – | 0.9249 (= 432.06 @ 90 d) |

**The committee is deterministic:** the same claims gave exactly the same price twice (432.15). Each piece of data
it takes into account lowers its price; data it shrugs off changes nothing. What beat the house was the **steepest
fall of its main cost driver in any window the arena checks** (`central.falling_window_claims`): all 6- and 12-month
windows rose, but electronic components (44% of cost) fell −2.3% from Jan to Oct 2025 → −EUR 0.48.

## 6. The P03 engine, fully measured (12 live games)
**Price = the sales person's stop (EUR 430.15 @ 30 d = 433.08 @ 90 d) − one cut per NEW verified data kind it takes.**
Text, anchor depth, our moves (20-92% of the gap) and committee requests change nothing on their own; it says so:
"As no new verified data or increased volume commitment has been provided, we cannot adjust our calculation further."

| data (cited once per case) | cut per unit | note |
|---|---:|---|
| should-cost EUR 403.21 vs its EUR 438.21 quote | 0.79 | only one ID |
| electronic components −2.27% (2025-01 → 2025-10), 42% of its cost | 0.48 | ≈ 0.5 × weight × fall% |
| volume forecast +10.3% (latest) | 0.14 | the June +23.3% snapshot did worse; a 2nd fc ID = "duplicate" |
| copper −2.21% (2026-01 → 2026-03), 5% | 0.07 | later rounds count too |
| labour −0.26%, 16% | 0.02 | |
| quality record 0 ppm | ~0 | |
| on-time delivery 84.6%, price history | 0 | "does not change our calculation" |
| a 2nd window of a series already cited | 0 | "duplicate" / "already taken" |
| a window ending ≥ 12 months before the data's last month (2026-09) | 0 | "irrelevant - outdated timeframe" |
| more volume (5,496 / yr) | – | can never pay: best possible score −1.15 |

All of it used: **EUR 431.58 @ 90 d = 0.936**, above the house (0.925). 0.95 needs EUR 430.90, another EUR 0.68, and no
data kind is left that this supplier takes into account. General rule for any supplier: **cite every verified, honest
fact it takes, one new kind (or index series) per message, from round 1, and keep the rounds going while data is
left**; it is the only thing a code-priced supplier rewards.

## 7. P02 (Nordmark): 0.507 -> 0.824 in 3 live games (house 0.74, best of all teams 0.721)
A different engine from P03: Nordmark **mirrors our steps** ("In response to your step, we are prepared to reduce",
"We expect a significant step towards our position") and cuts for each NEW verified fact; it goes final when a round
brings no new data ("it lacks new verifiable data").

| game | change | its price @ 90 d by round | score |
|---|---|---|---:|
| de6192e39dd86084 | central layer: volume + steel index −4.3% + quality (no effect); copper; labour; then no data | 372.52, 371.45, 370.85, final 370.45 | 0.657 |
| a1e2a4acb73dd3e9 | data spread one per round, order-price history last, no committee line | 372.52, 371.52, 370.92, final 370.32 | 0.669 |
| **ee98266bedd37231** | **+ mirror rule: step 30% of the remaining gap** (€3.17 instead of €0.76) | **372.52, 370.85, 369.45, final 368.55** | **0.824** |

Rules now in `central.py` (general, from per-case signals mined by `mine_claims.py`):
- **Spread the data:** keep one new fact for each of the next 3 rounds; send 1 per later round.
- **Mirroring supplier** (signal in its replies): step 30% of the remaining gap, staying a near-close below its price.
  The deal is ITS price, so a bigger step from us costs nothing and buys a bigger one.
- **"I hold full authority"** (P02 said it in every round): never mention a committee.
- "Confirm our case" (a rising index) does not block a *falling* index of the same kind; a falling cost-driver index was
  taken in every case where we cited one (P01, P02 x3, P03 x4, P18).
Round 4 said "our best effort ... without requiring management escalation", so escalation may be the next lever.

### 7b. P02, three more live games (552fb056e31d24d1, 8d4c4d5d7dff80bb: 0.847 each)
- **Nordmark follows a fixed concession schedule once our steps are big enough.** With 30% steps, with 40% steps plus
  a 5% deeper anchor, and with 2 extra data rounds, its path was the same to the cent: 372.52, 370.85, 369.45, 368.55,
  final 368.25 (5th message). Small steps (EUR 0.76) bought less (cuts 1.00 / 0.60 / 0.60). Step size matters up to a
  cap; the anchor does not (the split-the-difference model was wrong).
- **It goes final at a fixed message count** (4th or 5th) whatever data the later rounds carry ("our service levels
  remain within acceptable parameters" for on-time delivery, "past prices do not reflect our current cost structure" for
  order history). Later rounds still cut, but on its schedule.
- So the floor it approaches (~EUR 368.0 @ 90 d) is what to lower, as on P03, with data it takes **early**. Next test:
  quality notifications on the part (never cited in any game).
- Cloud session (analysis/central/ENGINES.md, analysis/cases/*_engine.md): engine type per case. 5 of 10 suppliers
  mirror, 2 hold, 1 floor-stop, 1 one-shot, 1 auction. QNs and the supplier's own recent quote were never cited.
