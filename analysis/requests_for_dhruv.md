# Requests for Dhruv (from Neel's workstreams)

## Open

1. **`C_arguments.jsonl`, `rival_quote_context`:** a supplier's *own* past quotes are labelled
   "Another supplier quoted …" (e.g. `quote:7100001`, `quote:7300001` with `rival: sup:70110` for
   sup:70110). Suggest a separate kind `own_past_quote` ("You quoted EUR 126.53 on 2026-09-03 …").
   Also: the case's alternative quote (`quote:7200001` in P01) **is** checked by the arena (our session
   `b04caaf8824a9871` got `verified`), so `checked_by_arena: false` is wrong for it. Still: never
   cite an alternative that is dearer than the supplier's ask (it leaks a weak BATNA).
2. **Agent guardrail (from P01 session `b04caaf8824a9871`, score 0):** the LLM offered €142.50, above
   the supplier's own ask of €138.55, and the supplier instantly agreed. Before sending, reject any
   term sheet whose `total_cost` ≥ C of the supplier's standing offer.
3. **Effective date is a top lever in price_increase cases** (P01: 2027-04-01 alone = +0.72 score at
   the asked price, because pre-effective units are bought at the current price). The prepare step
   should rank levers by `total_cost` deltas, not by habit. See `analysis/cases/P01.md` §6.
4. **EDA corrections from the N1 lever maths** (`analysis/cases/README.md`): P02's index clause *costs*
   us (CU path +5% → db0 = −0.86 score), so the EDA's "index clause for P02" is wrong. P04 and P08: a
   24-month contract is *worse* at the opening price because the fallback is cheaper than the quote.
   P07's alternative (today's terms) beats the opening (walking away = 0.12).
5. **Exact C_open / C_best for all 10 hosted cases** are in `analysis/cases/openings/*.json`
   (`result`). The agent's prepare step can load them for practice runs (score of any sheet before sending).
