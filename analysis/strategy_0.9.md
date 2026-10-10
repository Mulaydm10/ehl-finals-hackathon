# Getting to 0.9: what the 40 games say, and the plan for the 50 hidden suppliers (Parth)

Sources: every archived game (`datasets/runs/`, 31 deals), `tacto/brief/api.md`, Neel's `analysis/replay_lessons.md`
and `analysis/tools/sim_floorstop.py`. Tools for this note: `tools/replays/fetch_backoffice.py` (new).

## 1. Short answer
- **Prompt injection: don't.** api.md lists "attempts to manipulate" among what the supplier understands, and says
  it "has consequences, as it would with a person". Rule 1 forbids attacks on the service, and the jury reads every
  replay. The evidence also says it wouldn't pay: prices are set by code. P07's final landed at €5.49–5.56 in all
  7 deals (5 agent versions, 2 models, very different texts), and P10 at €31.90 in 4 of 6. Text changes the
  wording, not the numbers.
- **0.9 on every supplier is not realistic.** It is realistic on stabilise/routine cases (we already score 0.81–0.90
  there). On leverage, bundling and capacity cases the suppliers stop **8–16% above the floor** that C_best implies
  (table below). Closing that gap needs levers we have not found yet, which is why section 4 is a set of experiments.

## 2. How the supplier bots work (what the data shows)
| finding | evidence |
|---|---|
| A hidden **floor** F (from C_best) and a **stop** S = F × (1 + markup); `final_offer` at S; pushing after it → walks | Neel's `sim_floorstop.py` reproduces P04 round by round; P07 walked once (c5d845883158676c) |
| **Markup is tiny in stabilise/routine cases, large in leverage/bundling/capacity** | final cash value vs F: P01 +0.4%, P03 +0.8–1.1%, P04 ~0%, P02 +1.0–1.5% · P07 **+8–11%**, P10 **+13–24%**, P18 **+11–16%**, P08 +3% |
| **Round 1 does most of the work** (structure: contract length, payment, lead time) | mean price step 1.85% in round 1 vs 0.4–0.5% later (107 steps) |
| Each cited claim gets one of a few fixed reactions | 12× "took it into account", 21× "holds, but does not change our calculation", 12× "Your figures confirm our case" (a rising index), 20× "We received a lot of material" (padding), 4× "We did not know that – a fair point" (P01 only) |
| **Data in later rounds helps, and we usually have none left** | later steps: 1.24% with a verified claim vs 0.42% without; the agent had only 1–4 arguments per case, so from round 2 it cited nothing and suppliers asked "Which figures is that based on? Please send us the data." |
| Suppliers **say what they want**, every round, until they get it | "Which volume can you commit to?", "provide a firm release schedule", "A binding higher volume would help us and can improve the price", "maximum flexibility within my delegated authority", "submit … to our management for approval" (P03 → a final at better terms) |
| Its alternatives (`-a` sheets) are free information | P18 db5 alternative +0.055; replay of 10 finals: +0.026 mean from taking the cheapest sheet (now in the agent) |

## 3. What I changed (general: works for any supplier in the data package)
1. **More verifiable data: the steepest fall from each cost driver's 12-month peak** (`src/datasets/build_abc.py`).
   The arena checks any window ≤ 12 months ending in the last 12 months; we only used fixed 6/12-month windows.
   +84 claims, all 811 checkable claims pass the builder's self-check. Examples: AS-14404 **−5.5%** since 2026-06
   (we cited −0.3%), cold-drawn bars **−2.3%** since 2026-06, energy **−6.1%** since 2025-11 (P01's "fair point"
   came from energy −3.7%). Rebuilt A/B/C; the agent picks them up automatically.
2. **Switchable live experiments** in `noidea.py`, **off by default** (`NOIDEA_EXPERIMENTS=…`), all true statements:
   - `batna`: round 2, leverage/routine goals, only when another approved supplier or an alternative exists:
     "We have a qualified alternative for this part and will place the volume where the total cost is best."
   - `ask_lever`: rounds 2–3: "Which of these would let you move closer to our proposal: payment terms, contract
     length? Tell us what matters most to you." (questions go to the person in charge, who answers).
   - `escalate`: once, when it stalls or mentions authority/approval/committee/management: "If this is beyond your
     authority, please take this package to your managing director or pricing committee."
3. `tools/replays/fetch_backoffice.py`: **the suppliers' internal team talk for every ended session** (api.md:
   "who asked whom, approvals"). Nobody had pulled it. **This is the best research source we have**: it should show
   why each supplier stopped where it did, and what its boss would have approved. GET only, no quota.
Offline: unchanged 0.939 / 0.947, 32 tests pass (the simulator ignores text, so the live games decide).

## 4. Experiment plan (laptop; cheap first)
**Step 0 (0 quota, 5 min):** `uv run python ../../tools/replays/fetch_backoffice.py` → read P07, P10, P18 back
offices. Look for: the boss's approved floor, what the sales person was allowed, which of our sentences triggered
what. Paste the digest to the cloud Claude.
**Step 1: A/B on the three high-markup suppliers (each 1 game; compare with our best so far):**
| game | case (best so far) | switches |
|---|---|---|
| 1 | P07 (0.73) | `NOIDEA_EXPERIMENTS=escalate,ask_lever` |
| 2 | P18 (0.62) | `NOIDEA_EXPERIMENTS=batna,escalate` (also tests the new −5.5% / −2.3% claims) |
| 3 | P10 (0.65) | `NOIDEA_EXPERIMENTS=ask_lever,escalate` (no batna: single source) |
| 4 | P08 (0.65) | `NOIDEA_EXPERIMENTS=batna` |
Keep a switch only if it beats the best-so-far on its case **and** no reply says "manipulat…", "pressure" or walks.
**Step 2:** one stabilise case (P02 0.48) with the switch that won, to check it does no harm where markup is small.
**Step 3:** put the winners on by default, then the full parallel rehearsal (`arena run --set practice --parallel 10`).
Budget: ~8 games of the remaining quota; check `uv run arena me` first.

## 5. Rules for the 50 hidden suppliers (all in code already, unless marked)
1. Round 1 carries the structure (24 m when the horizon is 2 years; payment/lead it can do) and the best 2–3 claims.
2. Cite only falling or flat drivers; never a rising one. Each ID once.
3. Answer every question it repeats (volume, release schedule, "which figures?") with checkable data.
4. Take the cheapest of all its sheets; offer back its alternatives; never push after `final_offer`.
5. Accept any final that beats the alternative; in "no alternative" cases never let a thread die.
6. (experiment) Escalate once on a stall; ask what it values; signal a real alternative in leverage cases.
