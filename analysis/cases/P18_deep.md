STATUS: DONE (analysis, all 40 P18 games) + agent READY TO RUN, NOT RUN - 2026-10-11 ~03:30 CEST, cloud session, offline only
(0 arena sessions, no LLM). Agent: `analysis/agent_variants/noidea_p18_cross.py`. Check tool: `analysis/tools/p18_cross_check.py`.
Corrects `P18_lever.md` section 3 ("stay on 14 d"): after round 1, payment does not move its price.
UPDATE 2026-10-11, after the final (cloud, offline):
- **Live result:** `noidea_p18_cross.py` was run once by the local side (f2770f53c9ebd512, 0.677). The plan's key assumption
  failed: 90 d is priced. 4.87 @ 90 d drew 5.20 @ 90 d ("our standard is 30 days net"), so the guard went back to 30 d, and the
  game closed at 5.00 @ 30 d.
- **The "draws" are our wording:** the suppliers give the same reply to the same text. In all 57 groups of recorded games
  (every case) where our messages were byte-identical, the reply had the same price and status. So the "round-2 draw" below
  (0.10 or 0.20) came from our own wording, and the odds in section 6 count wordings, not runs.

# P18 deep: how Werdenfels prices, why Codacabana is one step lower, and the plan to cross 0.756

## 0. Short answer
- **Record:** Codacabana 0.75595 = EUR 4.90 @ 45 d, AS-14404 clause db0. Ours: 0.727 (0c968aae, 4.91 @ 14 d).
- **Payment term:** it matters only for its first counter (30 d -> 5.20, 45 d -> 5.30). After round 1 its cuts ignored our payment
  moves, and whole games on 14 d and on 45 d scored the same: 0.663 and 0.658. So "stay on 14 d" was wrong.
- **The lever:** keep our best round 1 (4.76 @ 30 d -> 5.20), then move to **90 days from round 2**. Every 30 days is worth +0.022
  score to us. At the same price, 90 d beats 14 d by +0.055 (5.00 @ 90 d = 0.721 vs 0.666 @ 14 d).
- **Why it can cross:** on 90 d any deal at or under 4.94 beats the record. In about 1 game in 5 its round-2 counter is 5.00 (a
  "soft draw"). Our three soft draws closed at 4.91, 4.94 and 4.94; on 90 d each of those beats 0.756.
- **Odds** (scripted Werdenfels weighted by the 40 games):

  | late payment | 90-day plan, per game | chance to beat |
  |---|---:|---:|
  | free | 0.725 | 18% |
  | charged | ~0.68 | 0% |
  | our current 14-day path | 0.663 | 0 of 10 |

- **Run (local side, one session each):**
  `cd tacto/starter-kit && uv run python ../../analysis/tools/play_variant.py case:P18 ../../analysis/agent_variants/noidea_p18_cross.py`
  Read its round-2 reply. At 5.10 or under on 90 d, payment is free: keep running (5 games ≈ 63%, 10 ≈ 86% for at least one
  beat). At 5.20 or more on 90 d, payment is priced: the agent drops back to 30 d itself. Then stop spending sessions on P18.

## 1. The record and the beat prices (scorer exact: all recorded P18 deals reproduce to the cent)
- Codacabana: EUR 54,823 saved = 4.90 @ 45 d db0, 24 or 36 m (the only exact match). Their other P18 deal (live feed, 21:50 CEST):
  45,653 saved = **5.20 @ 45 d db5 (0.6295)**. They play 45 d.

| price (24 m, db0) | 14 d | 30 d | 45 d | 60 d | 90 d |
|---|---:|---:|---:|---:|---:|
| 4.90 | 0.734 | 0.745 | 0.756 (= record) | 0.767 | 0.788 |
| 4.94 | 0.707 | 0.718 | 0.729 | 0.740 | **0.761** |
| 5.00 | 0.666 | 0.677 | 0.688 | 0.699 | 0.721 |
| 5.10 | 0.598 | 0.610 | 0.621 | 0.632 | 0.654 |
| **max price that beats, db0** | 4.86 | 4.88 | 4.89 | 4.91 | **4.94** |
| max price that beats, db5 | 4.97 | 4.99 | 5.00 | 5.02 | 5.05 |

1 cent = 0.0068 score; 30 days of payment = 0.022 score (≈ 3.2 cents).

## 2. All 40 games by path (normal mode unless marked)
| path | games | mean | best | ends |
|---|---:|---:|---:|---|
| **30 d -> 14 d** (4.76 @ 30 d, then 14 d) | 10 | **0.663** | 0.727 | 5.00 x6, 4.91, 4.94, 5.10, 5.20 db5 |
| 45 d throughout (main v2.34+) | 8 | 0.655 | 0.688 | 5.00 x4, 5.10 x4 |
| 45 d start, then 30 / 14 d | 5 | 0.665 (4 deals) | 0.718 | 4.94 @ 30 (6c2813ce), 5.00 @ 14 x2, 5.10 @ 30, walk (fe806698, empty repeat) |
| deep anchor 4.69 / 4.57 @ 30 d | 2 | 0.632 | 0.666 | 5.00, 5.10 |
| timeout before round 1 (Parth) | 2 | 0.632 | 0.666 | 5.00 (first counter 5.10), 5.10 |
| 14 d start, then 45 d (bf56d975) | 1 | 0.688 | | 5.00 @ 45 |
| 90 d + db5 from round 1 (probe c9b28881) | 1 | 0.598 | | 5.30 @ 90 db5 |
| 2-3 sheets in round 1, weaker facts (early) | 10 | 0.567 | 0.677 | 5.00-5.40 |
| template mode (3cb62cb9, 23:58) | 1 | 0.688 | | 5.00 @ 45 (5.20 -> 5.10 -> 5.00 -> final, like normal mode) |

## 3. How Werdenfels moves (40 games)
**3.1 First counter = round 1.** Our round-1 term matters here:

| our round 1 (one sheet, path + AS-14404 -8.5% + PPI-C2431 -2.3%) | its first counter |
|---|---|
| 4.76 @ 30 d, no clause | **5.20 x9, 5.30 x1** |
| 4.77 @ 45 d, no clause | 5.30 x8, 5.20 x3, 5.40 x2 |
| 4.69 / 4.57 @ 30 d | 5.30 x2 (deeper anchors draw the high counter) |
| 4.74 @ 14 d (bf56d975) | 5.20 |
| 4.77 @ 90 d db5 (c9b28881) | 5.50 db5 (= 5.40 db0) |
| 2-3 sheets, weaker facts | 5.20-5.60 |
After a timeout before round 1 it countered 5.20 (099a64a3) and 5.10 (b45bea53), but the final then came one round earlier, so there
was no net gain.

**3.2 Round 2: it cuts 0.10 or 0.20, and nothing we do sets which.**

| from | after a payment move | no payment move |
|---|---|---|
| 5.20 | -0.10 x9, **-0.20 x2** | -0.10 x2, **-0.20 x1** |
| 5.30 | -0.10 x2, -0.20 x3 | -0.10 x4, -0.20 x2 |
| 5.40 | | -0.10, -0.20, -0.30 |
- Our step (+0.08 to +0.24) did not change it either (cee66b66: +0.24 drew -0.10; 6a0a9bfd: +0.11 drew -0.20).
- 0c968aae / a09d9536 drew -0.20 and 193f7a36 / 4eec9023 / 19dbe142 drew -0.10 with the same moves. Those three ran in parallel at
  02:17 with differently worded e-mails and got identical prices (5.20 -> 5.10 -> 5.00 -> final 5.00). **The engine sets the price per
  session; the wording does not.** 0c968aae's e-mail even said "reduce our base price to €5.10" while its term sheet said 5.00.

**3.3 Round 3.**
- A step of **+0.05 or more drew its 0.10 cut in 17 of 17** games.
- Steps of +0.04 or less: cut 2 of 9, agreed at our ask 2 (0c968aae 4.91, ff6a6b20 5.00), held 4.
- A step of 0 ended with its final at once (ed9a881a).

**3.4 Round 4.**
- After a round-3 cut, our +0.01 to +0.03 step drew its final at the standing price in 16 of 16 games.
- An e-mail with no new fact and no move walked (fe806698).
- **It agreed at our ask** five times: 0c968aae 4.91 (r3), ff6a6b20 5.00 (r3), a09d9536 4.94 (r4, after a hold), 6c2813ce 4.94 @ 30 d
  (r4, after a hold), c4bcc22c 5.00 @ 14 d (r4, its offer 5.10 @ 45 d).

**3.5 Deadband.** Its 5% deadband is always db0 + 0.10 (about 15 pairs). For us db5 is worth 0.108, so it is +0.008 net:
neutral. Switching to db5 mid-way counted as no move (a55d2e89).

**3.6 Its alternatives.** When we sent two payment terms, its alternative was the shorter term 0.10 cheaper (or db5 at the same
price): about +0.07/kg better for us than its primary.
- Its alternative cannot be accepted by its id: the arena returns 422, nothing happens and no round is used.
- Sending its own alternative back was **agreed 3 of 3** (a99d02eb, 06f8f4f5, c4599331). Main does not do this; it is switched off
  after walks on other suppliers.

## 4. The payment question, answered properly (corrects P18_lever.md section 3)
- **Inside one reply** its alternatives are 0.10 apart per payment step. That is what I measured before; the model writes those.
- **Round 1:** payment counts through the first counter (30 d -> 5.20 in 9 of 10; 45 d -> 5.30 in 8 of 13).
- **After round 1** its cuts ignored our payment moves (table 3.2). The one move to *longer* payment was not charged:
  bf56d975 went 5.20 @ 14 d -> 5.10 @ 45 d -> final 5.00 @ 45 d. Moves 45 -> 30 d got nothing extra either (1d818891, 6c2813ce).
- **Whole games:** 30 -> 14 d path 0.663 (10 games), 45-day start 0.658 (12 normal-mode deals).
- So after round 1, a longer payment term is free money for us: +0.022 per 30 days.
- **Not yet measured:** a move to 60 or 90 d after round 1. The only move to a longer term so far was 14 -> 45 d. The plan's
  round-2 reply measures it.

## 5. Why Codacabana is one step lower, and why our P18 scores fell
- **Soft draw:** its round-2 counter lands at 5.00 instead of 5.10 in about 1 game in 5 (0c968aae, a09d9536, 6c2813ce; 3 of 14 from
  5.20). Codacabana's 4.90 @ 45 d is that draw played on 45 d with asks under 4.90: 5.20 -> 5.00 -> 4.90 -> final.
- **Our soft draws were spent on short terms or with asks that were already high:**
  - 0c968aae / a09d9536 closed at 4.91 / 4.94 on 14 d (0.727 / 0.707).
  - 6c2813ce (02:17) had 5.00 @ 45 d after round 2, but our ask was already 4.90. Main then moved to 30 d and took 4.94 @ 30 d (0.718).
  - On 90 d, all three closes beat the record (4.91 -> 0.781, 4.94 -> 0.761).
- **"Why P18 fell"** (P18_lever.md section 9) was the draw, not the 45 d term. The two best games were the soft draws, and the
  paths average the same (section 2).

## 6. The plan to cross: `noidea_p18_cross.py` (gate case:P18; every other case = main untouched)
| our msg | sheet (24 m) | fact | expected reply |
|---:|---|---|---|
| 1 | **4.76 @ 30 d, no clause**: ed9a881a's words exactly | path + AS-14404 -8.5% + PPI-C2431 -2.3%, XLSX + committee | 5.20 @ 30 d (9 of 10) |
| 2 | **4.87 @ 90 d** with its db0 clause ("as your letter of 22 Sep proposed") | forecast | 5.10 @ 90 d, or 5.00 (soft) |
| 3 | **4.93 @ 90 d** (+0.06: draws the cut) | labour index -0.3% | 5.00, or soft: 4.90 / agrees 4.93 / holds |
| 4 | **4.94 @ 90 d** (the beat price) | AS-14404 -5.5% (2026-06 -> 09; never cited, its own clause series) | final 5.00, or agrees 4.94 |

**Rules:**
- **Accept early:** if its standing offer costs us no more than our next ask, take it.
- **Guard:** if its round-2 counter on 90 d is not under its first counter (90 d priced), rounds 3-4 go to 30 d with the same asks.
  If it answers on another term, the agent follows that term.
- **At its final_offer:** accept its primary. If the final carries a sheet cheaper for us by more than EUR 1,000, send that sheet
  back once.

**Offline checks:**
- `p18_cross_check.py --replay`: all 40 recorded games ran without errors.
  - Round 1 is identical to ed9a881a, and round 2 is 4.87 @ 90 d.
  - On recorded replies, rounds 3-4 follow the term it answered on.
  - It sent the cheaper alternative back on the three finals that carried one: 6833e98f (5.40 @ 30 d db5, about +0.05 over the
    primary it accepted), 06f8f4f5 and c4599331.

**Scenarios** (`--scenarios`, scripted Werdenfels):

| late payment | normal draw (5.20 -> 5.10) | soft draw (5.20 -> 5.00) | first counter 5.30 |
|---|---|---|---|
| free | 5.00 @ 90 = 0.721 | 4.93 / 4.94 @ 90 = 0.768 / 0.761 **beat** | 5.00-5.10 @ 90 = 0.654-0.721 |
| +0.10 on 90 d | guard -> 5.00 @ 30 = 0.677 | 5.00 / 5.10 @ 90 = 0.721 / 0.654 | 0.54-0.65 |
| +0.20 on 90 d | guard -> 5.00 @ 30 = 0.677 | guard -> 4.93 / 4.94 @ 30 = 0.725 / 0.718 | 0.54-0.68 |

**Odds** (`--odds`). Weights from the games: first counter 5.20 9/10; soft cut 0.2 from 5.20 and 0.45 from 5.30; soft-draw close
agree / hold-then-agree / cut 0.3 / 0.5 / 0.2.

| plan | late payment free | +0.10 | +0.20 |
|---|---|---|---|
| **90 d** | **0.725, 18% to beat** | 0.674, 0% | 0.682, 0% |
| 60 d (set `PAY = 60`) | 0.702, 9% | 0.668, 0% | 0.670, 0% |
| our 30 -> 14 d path (recorded) | 0.663, 0 of 10 | | |

**Why 90 d and not 60 d:**
- On 60 d only 4.91 or less beats, so the 4.94 closes would not count. On 90 d all three soft closes count.
- 90 d is also +0.022 more in every other game.

**What could go wrong:**
- It may price 90 d after round 1 (never measured). Then the guard returns to 30 d (0.674-0.682, still above 0.663).
- It may refuse 90 d. Then the agent follows its term.
- An open-ended round 5 goes to main (monotone from 4.94).

## 7. Other levers checked (do not spend sessions on them)
| lever | result |
|---|---|
| 36-month move (fd5b66b1) | 0 ("our lowest possible price of EUR 5.20") |
| its contract's clause value 5.74 (a55d2e89) | 0 (first counter 5.20 as without) |
| deeper opening 4.69 / 4.57 (6a0a9bfd, cee66b66) | first counter 5.30 both times: worse |
| late-payment admission + on-time promise, account value (cee66b66) | 0 |
| timeout before round 1 (b45bea53, 099a64a3) | 5.10 once, but the final came a round earlier: 0 net |
| db5 switch mid-way (a55d2e89) | counted as no move |
| 70710's quote 5.45 / its own 2025 quote 5.41 | outside the case refs -> "irrelevant" (rule 10d) |
| index facts after round 1 | "it holds, but it does not change our calculation" when round 1 already had indices |

**Untried, small:**
- **On-time delivery:** sc:70740@2026Q3 shows 81.0% against our 95% target. It is in P18's own case refs but was never cited on
  P18; on P03 and P10 it changed nothing (3 of 3). Switch `OTD_FACT`.
- **The owner's open-book offer** (doc:20260904-70740-M1): context only, no check. Werdenfels never sent the XLSX in 40 games.

## 8. Files
- `analysis/agent_variants/noidea_p18_cross.py`. Switches: `PAY` (90; 60 is the cautious setting), `OTD_FACT` (False),
  `HARVEST_EUR` (1000).
- `analysis/tools/p18_cross_check.py`, run as `cd tacto/starter-kit && uv run python ../../analysis/tools/p18_cross_check.py
  [--replay] [--scenarios] [--odds]`.
- After each live game, record:
  - its round-2 counter on 90 d;
  - whether it agreed;
  - the final, with the session id, in `P18_lever.md`.
