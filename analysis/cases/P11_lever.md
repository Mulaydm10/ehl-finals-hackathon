STATUS: DONE (task 21) - 2026-10-10 ~23:30, cloud session, offline only (0 arena sessions, no LLM calls). 40 P11 games read (all
datasets/runs + tools/replays/raw), every sheet, claim and trace reason. Variant: `analysis/agent_variants/noidea_p11.py`.

# P11: no lever reaches 0.81; one beats the 0.807 record on a low draw, and one lifts the high draw

## 1. Every negotiable term (arena_kit.total_cost; C_open 817578, C_best 722500)
P11 negotiates only **unit_price, ppm_commitment (300 / 800 / 1500 / 2500) and chargeback (0 / 150 / 300 / 500)**.
Payment (60 d), lead time, volume, contract and incoterm are `fixed_terms`; offering them is a 422 or an empty promise (rule 27).

| structure (ppm / EUR per complaint) | score at 44.90 | 44.95 | **45.00** | 45.50 | price for 0.807 / 0.81 | what it costs the supplier (evidence) | verdict |
|---|---:|---:|---:|---:|---|---|---|
| **300 / 0** (every deal) | **0.810** | **0.802** | **0.794** | 0.710 | **44.92** / 44.90 | - | price is the only lever |
| 300 / 150 | 0.818 | 0.809 | 0.801 | 0.717 | 44.96 / 44.95 | +1.00 / unit (29cbb6d6: 46.00 vs 47.00; 0d5bc007) | dead |
| 300 / 300 | 0.825 | 0.817 | 0.809 | 0.725 | 45.01 / 44.99 | ~+1.9 / unit; a EUR 300 sheet was never chosen (7 of 7) | dead |
| 300 / 500 (any ppm ≤ 1500: quality cost 0) | 0.833 | 0.824 | 0.816 | 0.732 | 45.05 / 45.04 | ~+3.2 / unit; "We cannot accept chargebacks" (1d97) | dead |
| 800 / 0 | 0.773 | 0.764 | 0.756 | 0.672 | 44.69 / 44.68 | finals 45.50 like 300 ppm (03a3, 29cb) | dead |
| 1500 / 0 | 0.720 | 0.712 | 0.703 | 0.620 | - | its alternative is -0.50 for 1500 / 2500 ppm; we lose 0.54 | dead (44.50 @ 1500 = 0.787) |

Why chargebacks are dead:
- **api.md:** "chargebacks at the defect rate it really has". Its real rate is about 6400 ppm, its opening commitment.
- **Cost:** EUR 150 costs it ~0.96 / unit but saves us only 0.045 / unit.
- **For ppm:** its relief price (-0.50 for 1500 ppm) roughly equals our cost (+0.54).

**(d) TakeTheMoneyAndRun's 0.807 = 44.92 @ 300 ppm / EUR 0 (0.8069).** This is the only cent-priced package that rounds to 0.807. 45.01 + EUR 300 would also score it, but that is dead. So at least one session had its floor at or under 44.92.

## 2. Its asks and floors - all 40 games (table of every ask within 1.2% of its standing price)

| draw | our ask | at our message | result |
|---|---|---:|---|
| low (45.00) | 44.60 / 44.70 / 44.80 / 44.90 | 4-6 | refused **13 of 13** (44.90 x4) |
| low | **44.95** | 4 (with its last facts) | **agreed 1 of 1** (eac20911, 0.802) |
| low | 44.95 | 5 (after a refused 44.90) | refused 3 of 3 (dbf5, 38c7, 1d97) |
| high (45.50) | 45.10 / 45.13 / 45.16 / 45.25 | 4 | agreed 5 of 10 (aced, b1f9, 7650 at 45.10; 7117 at 45.13; e647 at 45.25) |
| high | 44.98 - 45.45 | 5-7 | agreed 0 of 17 (only the sessions whose floor was high get here: a selection effect) |

- **Low draw.** Its floor sits between 44.90 and 45.00, drawn per session: ≤ 44.95 once (eac2), ≤ 44.92 once (TakeTheMoneyAndRun), > 44.90 4 of 4. The **0.81 target needs ≤ 44.90 at 300 / 0, so it is not reachable with any known lever.**
- **High draw.** 45.50 is NOT a floor. **77f61e47** held 45.50 ("our best price ... let's get this signed!") after POs + QNs. Our next e-mail carried the labour index (LCI-C) ALONE with a +0.24 step. The reply was "it's a tiny drop, but we can pass that on to you", and 45.00 (0.794): the only high draw that ever reached 45.00. 4d6c9a13 had the same shape: a hold at 45.50, then its own quote + a +0.20 step, then 45.00.
- **Every other game since v2.21** spent LCI-C at message 3, packed with the QNs or alone before any hold. The result was a HOLD 7 of 7 (11e2, 73c7, 605e, aced, b1f9, 7650, e647, f80f).

## 3. (b) What it wants, from its own words (every reply in every game)
| its line | count | can we trade it? |
|---|---|---|
| "Faster payment would help us more than anything" / "we can reflect it in the price" | every reply | no: payment_days is fixed at 60. We already give what we can (on-time payment, the late-payment admission), which it thanks us for in round 1 |
| "A binding higher volume would help us ... Which volume can you commit to?" | 76500e57, 881ddf0a | no: volume is fixed at 15900; we already confirm it as binding |
| "We cannot accept chargebacks" / "we just can't take on any extra financial risks" | 1d97, dbf5, 73c7 | it is its fear: never ask for a chargeback (see 1) |
| "Our margin and our limits stay internal" | every hold | - |

## 4. (c) The first counter (46.00 low / 46.50 high)
- Identical round-1 data in 28 games; only wording correlated (rule 86).
- Since the code reassurance line (v2.22) the draws split 3 low / 3 high.
- Round-1 data never moved it. Nothing new to try here.

## 5. Candidate levers
| # | lever | score if it works | evidence | risk |
|---|---|---|---|---|
| 1 | chargeback EUR 150-500 at 45.00 | 0.801-0.816 | it prices EUR 150 at +1.00 / unit; EUR 300 sheets never chosen 7 of 7 | dead |
| 2 | ppm relief (800 / 1500) | ≤ 0.787 | its relief = our cost | dead |
| 3 | payment / volume | - | fixed terms | dead (422 / rule 27) |
| 4 | **low draw: ONE shot at 44.91** at its floor (alone), then 44.95, then its final | **0.8086** (> 0.807 record) / 0.802 / 0.794 | TakeTheMoneyAndRun got ≤ 44.92; eac2 got 44.95; 44.90 refused 4 of 4 | ~0 (refused -> 44.95 -> its final; the 44.90 + chargeback pair it replaces never worked) |
| 5 | **high draw: LCI-C held back until its first hold, then sent alone with a +0.25 step** | 0.794 (45.00), then the 44.91 shot | 77f61e47 (1 of 1); 4d6c9a13 the same shape with another fact | gives up message 4's 45.10 probe (agreed 3 of 6 at 45.10, 0.777); if it holds, our 45.10 comes one message later |
| 6 | its own quote:7300011 (EUR 45.15, 13 Sep) as a 2nd held-back fact for the high draw | 0.794 | 4d6c cut 45.50 -> 45.00 after it | that quote was at **10-day payment**; it replied "we expect you to pay faster like in that old quote". Honest only if the 10 days are named. Not in the experiment |

## 6. ONE recommended live experiment: `noidea_p11.py` (levers 4 + 5, one rule: "the labour fact waits for its first hold")
- **Messages 1-3 as main.** LCI-C is removed from the claim pool until the supplier holds, so message 3 carries the QNs / POs, as in 77f6. The model path draws from the same pool.
- **Message after its first hold:** LCI-C **alone**, plus:
  - at its known floor (low draw, 45.00): **44.91 alone**;
  - above it (high draw, 45.50): **our last ask + 0.25** (44.26).
- **Next message:**
  - after the shot: main's floor round 2, which is **44.95**;
  - after a cut to 45.00: the **44.91** shot;
  - after a high-draw hold: main's memory probe **45.10**.
- **Its final:** accepted, as always.
- **Gate:** `case:P11` only. The shot fires only on our cheapest remembered structure (300 / 0).

| draw | expected path | outcomes | EV (main v2.27) |
|---|---|---|---|
| low (~1 in 3) | 46.00 -> 45.00 -> hold -> **44.91 + LCI-C** -> 44.95 -> final | **0.8086** (~15%) / 0.802 (~20%) / 0.794 | **~0.798** (0.795) |
| high (~2 in 3) | 46.50 -> 45.50 -> hold -> **44.26 + LCI-C** -> 45.00 (77f6) or hold -> 44.91 or 45.10 | 0.794-0.809 if it cuts / 0.777 / 0.710 | **~0.76** (0.75) if the cut repeats half the time |
| per game | | P(> 0.807) ≈ 6%; **P(> 0.81) ≈ 0** | ~0.775 (0.765) |

**Decision rule after one game:**
- Low draw: 44.91 agreed means the P11 record; otherwise we get 0.802 or 0.794, as main does.
- High draw: its answer to message 4 decides. **45.00 means lever 5 is confirmed** (2 of 2 + this): keep it. A hold at 45.50 means it is refuted: high draws go back to main's message-4 probe.

## 7. Checks
- **Replays** `replay_cmp_cloud.py` main v2.27 -> noidea_p11 (39 P11 games):
  - turns 1-3 are SAME in all games;
  - the intended turn changes as planned:
    - low draws since v2.21 (eac2, dbf5, 38c7, 1d97, 7285, 3fa2, 37ea, 74cc): turn 4 [44.90, 45.00 + 300] -> **[44.91] + LCI-C**;
    - high draws (73c7, 605e, 11e2, aced, b1f9, 7650, e647, 77f6): turn 4 45.10 -> **44.26 + LCI-C** (77f6 live: 44.25 + LCI-C);
  - SAME in full: 3cc4, 6b02, fa9a, 8cdb;
  - in old games that never held before turn 4, LCI-C just waits (same price).
  - The code-only replay already sends LCI-C at turn 4; only the live model path packed it into message 3, which the pool change stops.
- **Other cases:** P01, P02, P03, P04, P07, P08, P10, P18 (70 threads) all SAME (case gate).
- **Offline run** (`offline_round.py P11`, P04-calibrated sim): runs clean. The sim never holds, so the new branch does not fire.
- **Not tested offline:** the model-written e-mails (no paid LLM). The pool change is code, and the model picks only from that pool.
