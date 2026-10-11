# NoIdea - a buyer agent for the Tacto Negotiation Arena (EHL Munich 2026)

Team **🃏 NoIdea**: Dhruv, Neel, Parth.

Our agent buys parts for Hollerau Pumpenwerke by e-mail from suppliers it has never met. **Code sets every number; the
language model reads the supplier's e-mail, chooses among offers code has already priced, and writes.** The final runs
`--agent noidea` (`tacto/starter-kit/arena_kit/agents/noidea_rfq.py`, an RFQ layer on top of `noidea.py`).

Commit the agent runs in the final: `<fill in at 12:00: git rev-parse HEAD>`

## Approach

**1. Preparation (before the first e-mail).** From the data package we build, offline and deterministically
(`src/datasets/build_abc.py`):
- a **dossier per supplier**: standard terms, scorecards, order and invoice history, contracts, news, and **motives** read
  from the documents (e.g. `cash_short`, `hedged_forward`, `price_frozen`, `wants_commitment`);
- a bank of **pre-verified arguments**, each with its data IDs and a ready sentence: index falls of the part's own cost drivers
  (the steepest window the arena checks), should-cost, order-price paths, demand forecasts, quality records, notice periods.
  Every claim is self-checked against `facts.json`; a claim the arena could contradict is never used.

**2. The numbers.** Every term sheet is priced by our exact total cost (price, payment interest, freight, lead time, quality,
index risk, relationship charge) and by a model of the supplier's side (its cash rate, real defect rate, the premiums it
reveals in its own counter-offers). The model can only pick among these sheets; it never writes a figure.

**3. How it decides what to offer.** General rules, each from live evidence (`docs/GENERAL_RULES.md`, 121 rules):
- open with the structure that is cheapest for us at the supplier's value; hold it - a supplier's *alternative* is not a
  refusal; adopt its term only when it refuses ours twice;
- **pace the facts**: round 1 carries the strongest facts (most suppliers price them all), later e-mails **one new fact each**
  (a second fact in the same e-mail moves no supplier); a cash-short supplier gets one reason per e-mail from round 1;
- concede by the supplier's engine read in-game (it mirrors our steps / it moves only for new facts / it stops at a fixed
  floor / it answers once), never backwards, and **never an e-mail without movement or a new fact**;
- tactics are honest only: true, checkable facts; naming the fear we remove (no chargebacks, on-time payment); our own
  late-payment record owned openly. No invented data, no prompt tricks - the arena checks every claim.

**4. When it closes or walks.** It accepts a final offer at once (pushing after a final makes suppliers walk), accepts an
agreement that meets its target, asks once just under a supplier's standing price when it stalls close to us, and takes the
best standing offer before a supplier walks. It walks only when no offer beats our alternative. In RFQs it anchors every
bidder on the market and shows the first agreement to the others once before accepting.

**5. Learning without memorising.** We validated the agent in a **hidden-supplier mode** (`NOIDEA_EXPERIMENTS=hidden`: no memory
of past games, no case-specific data) - the way it meets the final's suppliers. Over four full loops of every practice case
(9 cases in parallel, one process, under 4 minutes per wave) it averaged 0.82-0.83 with no crash or walk-away, set the team
record on P02 (0.879), and scored 0.87-0.91 on a sandbox case whose supplier is not in our data at all.

## Setup and run

Requirements: Python 3.12, [uv](https://docs.astral.sh/uv/). Environment variables (values in `tacto/starter-kit/.env`, never
committed): `ARENA_URL`, `ARENA_API_KEY`, `LLM_PROVIDER` (`openai`), `LLM_BASE_URL`, `LLM_MODEL` (we use `gpt-6-astra`),
`LLM_API_KEY`; optional `NOIDEA_EXPERIMENTS` (comma list; `hidden` = no memory).

```bash
cd tacto/starter-kit && uv sync
uv run arena data                                   # the data package (and the Sunday release once public)
cd ../.. && python3 src/datasets/build_abc.py --data tacto/data --out datasets   # dossiers + argument bank
cd tacto/starter-kit
uv run arena play case:P01 --agent noidea -v        # one practice case
uv run arena run --set final --agent noidea --parallel 10   # the Live Final
```
On the final machine we use `tools/sunday_release/rebuild.sh` (08:00 data release), `tools/final/preflight.sh` (09:00) and
`tools/final/start_final.sh` (before 12:00); steps in `tools/final/RUNBOOK.md`.

## Where things are
| path | what |
|---|---|
| `tacto/starter-kit/arena_kit/agents/noidea.py`, `noidea_rfq.py` | the agent |
| `tacto/starter-kit/arena_kit/play.py`, `client.py` | the kit's runner, with our fixes (server errors re-sync instead of a blind retry) |
| `datasets/` | dossiers, argument bank, lessons the model reads, archived games (`runs/`) |
| `docs/GENERAL_RULES.md` | every general rule with its live evidence |
| `notes/agent_changelog.md` | every version, every live game, why it changed |
| `analysis/` | teammates' engine analyses, per-case studies, simulators |
| `src/eval/`, `notes/analysis_v234/` | offline evaluation, replays, the crash test and the load test |
