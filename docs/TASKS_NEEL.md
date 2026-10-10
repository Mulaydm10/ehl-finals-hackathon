# Tasks for Neel (and Neel's Claude)

> **For Neel's Claude:** you're working in the `ehl-finals-hackathon` repo for the Tacto
> Negotiation Arena. Read `PLAN.md`, `docs/EDA_FINDINGS.md`, `tacto/brief/brief.md` and
> `tacto/brief/api.md` first. **Only write inside your folders:** `analysis/`, `playbooks/`,
> `tools/replays/`, `tools/sunday_release/`, `datasets/D_episodes.jsonl`. Don't edit `src/`,
> `datasets/A_*|B_*|C_*|dossiers/` or `tacto/` (Dhruv's agent and builder live there). If you need a
> change there, write it in `analysis/requests_for_dhruv.md`. `git pull --rebase` before every push.
> Use **at most 80 practice sessions per 24 h** and log each in `notes/quota_log.md`.

Setup: `cd tacto/starter-kit && uv sync --all-extras`, put `ARENA_API_KEY` (ask Dhruv, never commit
it) in `tacto/starter-kit/.env`, then `uv run arena me`. Rebuild the datasets any time with
`python3 src/datasets/build_abc.py`. Practice case files: `datasets/cases_practice.json`.
`arena_kit.total_cost(case, terms, standard, supplier)` computes C exactly; use it everywhere instead
of hand maths.

---

## N1. Per-case deep dives: all 19 practice cases → `analysis/cases/<Pxx>.md`

For each case in `datasets/cases_practice.json` (start with the 10 hosted: P01 P02 P03 P04 P05 P07
P08 P10 P11 P18; the 9 non-hosted are the stand-ins for hidden cases), go through the data package
in this order and write a one-page brief:

1. **Case file:** type, goal, need, horizon, negotiable fields + `term_options`, fixed terms,
   must-haves, alternative (and its C), every `buyer` rate.
2. **Trigger:** read `trigger_doc` in `tacto/data/correspondence/`. Ask %, ask price, effective date,
   notice days vs the contract's (`contract_clauses.csv` clause 3.1).
3. **Supplier dossier:** read `datasets/dossiers/<sup>.md` (motives, scorecards, intel, all notes),
   then go deeper than it. Check every row for the supplier and part in `price_conditions`,
   `negotiation_history`, `po_lines` (price history, `stale_condition` lines), `invoices` (how late we
   pay), `quality_notifications`, `quotes`/`rfqs`, `forecasts`/`forecast_lines` (forecast changes =
   `fc:` claims), `spend_cube`, `sourcing` (single source? tooling owner?), `news`.
4. **Cost justification:** the part's `cost_drivers` × index changes over the last 12 and 6 months
   (`index_values.csv`) → the justified change. Compare with the ask.
5. **Should-cost:** `should_cost.csv` vs current price → margin room. Is the supplier already below cost?
6. **€ per lever** for this case (use `total_cost`): 1% price, ±15/30 payment days, each
   `effective_date` option, each `contract_months` option, volume, index clause on/off, ppm/chargeback.
7. **Recommendation:** target terms, walk-away point (vs the alternative's C), the best 3 citable
   arguments (from `datasets/C_arguments.jsonl`, with exact sentences), what NOT to argue (e.g.
   hedged suppliers), tone, and 3 term sheets for the first e-mail.

Template header for each file: `case | type | goal | supplier(s) | C_open est | C_alt | target C | score if target hit`.

## N2. Supplier economics model → `analysis/supplier_economics/suppliers.csv` + `README.md`

The relationship charge and supplier acceptance both depend on the **supplier's** margin:
`(value − full_cost) / value`, where value counts payment timing "at what money is worth to it now"
(more for cash-short suppliers). Read "Cost and score" in `tacto/brief/api.md` and
`arena_kit.cost.supplier_value`. For each of the 46 detailed suppliers, estimate:

| column | how |
|---|---|
| `supplier_id`, `part_id` | |
| `full_cost_est`, `full_cost_low`, `full_cost_high` | should-cost (±5–15%, German base; adjust for CZ/PL/HU/TR/CN), else back out from history: prices that came with "accepted below full cost" are ≤ cost |
| `current_margin_est_pct` | (current price − full_cost) / price |
| `cash_rate_est` | what money is worth to it: high for the cash-short (Liquidity notes, credit index ≥ 300, credit_watch/downgrade news, equity < 20%, wants faster payment), else about the buyer's 8% |
| `floor_price_est` | lowest price it can accept at each payment_days option (14/30/45/60/90) |
| `price_room_pct` | current price vs floor |
| `best_trade` | e.g. "−2% price for 30→14 days" when cash_rate ≫ 8% |
| `confidence`, `evidence_ids` | |

Validate it against practice replays (N4): when a supplier says "below our cost" or walks away,
was our offer under your floor?

## N3. Playbooks per case type → `playbooks/<type>.md`

One per arena `type`: `price_increase`, `renewal`, `rfq`, `bundling`, `raw_material`, `capacity`,
`quality`. Each holds: what the goal (stabilise / secure_supply / quality_first / leverage /
routine) implies for the cost weights; the opening move; 3 term-sheet patterns; which motives
(EDA section 5) call for which levers; signals and how to respond (`final_offer`, `agreed`, boss
joining, reply delay, `contradicted` claims); when to accept; when to walk away; tone. Each one
**≤ 150 lines**, because they go into the LLM prompt. Base them on EDA sections 1–5 and the N1 briefs,
then refine with replay lessons (N4).

## N4. Replay collector + episode dataset (D) → `tools/replays/`, `datasets/D_episodes.jsonl`

1. Write `tools/replays/collect.py`: after a session, `GET /v1/sessions/{sid}` (the trace with the
   supplier's reasons, claim results, cost_breakdown, score) → append one JSON line per **message**
   to `datasets/D_episodes.jsonl`:
   `{case_id, type, goal, supplier, round, our_email{subject, body, term_sheets, refs}, reply{status, terms, claim_results, signals}, reasons, final_score, cost_breakdown}`.
2. Collect every session either of us plays (Dhruv's runs log their session IDs to
   `notes/sessions.txt`; read it, don't write it).
3. **Probe experiments** (≤ 40 sessions, the sandbox first: `case:D01`, `case:D02`): how do suppliers
   react to (a) payment-for-price trades, (b) index evidence vs data-naive owners, (c) tone, polite
   vs firm, (d) 1 vs 3 term sheets, (e) threats of the alternative, (f) asking for a cost breakdown,
   (g) pushing after `final_offer`?
4. Write `analysis/replay_lessons.md`: what moved suppliers and what backfired, with the session
   IDs. Pick the **best 1–2 e-mails per case type** as few-shot examples (`"fewshot": true` in D).

## N5. Sunday release tool → `tools/sunday_release/diff.py`

Sunday 08:00 the arena publishes new news, letters and a memo (`uv run arena data`). Write a script
that downloads the release next to the package, diffs it against v1 (new IDs in `facts.json`, new
rows per table, new correspondence), prints a summary of **which suppliers changed and how**, and
flags new templates that `MOTIVES` in `src/datasets/build_abc.py` doesn't cover (write those into
`analysis/requests_for_dhruv.md`). Test it on Saturday by diffing v1 against itself plus a fake extra file.

---

**Order:** N1 for the 10 hosted cases → N3 → N2 → N4 (needs Dhruv's agent v1 for real episodes;
probes can start now) → N5 Saturday evening → N1 for the 9 non-hosted cases.
