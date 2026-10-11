# Overfitting audit of the final's agent (2026-10-11 ~02:40)

Question: did chasing high practice scores overfit the agent? Answer: **not in its code, partly in its tuned values and
(until tonight) in the lessons the model reads; our 0.83 is an in-sample number.**

## 1. Code - clean
- Token-level scan of everything the final runs (`noidea.py`, `noidea_rfq.py`, `play.py`, `client.py`, and the shared
  `analysis/agent_variants/central.py`, `analysis/central/engine_rules.py`): **no case, supplier or part id and no fixed price in
  code** (only in comments / docstrings as evidence).
- Every number in an e-mail is computed at runtime from the case's own data (cost model, supplier model, data-derived facts).
- Teammates' case-specific drivers and variants (scripted P05 0.965, P11 0.885, noidea_p03/p04/p10...) are NOT in `--agent noidea`.

## 2. Runtime data
| data | per case / supplier? | in the final |
|---|---|---|
| supplier memory `H_supplier_memory.json` | per supplier id | off in hidden mode (the validated default of `start_final.sh`) |
| claim reactions `claim_reactions.json` | `by_case` per case id + `by_kind` over all games | `by_case` never matches a new case id; hidden mode ignores it |
| lessons the model reads `G_lessons.json` | 7 recipes named ONE practice supplier (e.g. "P10 goes final in round 1... floor EUR 31.90") | **fixed**: rewritten as general mechanisms; the originals moved to `by_supplier` - shown only when that exact supplier id comes back in the same case type, never in hidden mode |
| dossiers / argument bank | built from the data package for all 46 suppliers | general (data, not memory) |
The model cannot put a number in an e-mail (sentences with digits are dropped) and only chooses among sheets code priced.

## 3. Fitted on few suppliers (a real risk)
- ~25 constants tuned on one or two practice suppliers each: anchor depth and patience per case type, hair / near-close / grid
  probe sizes (P11, P04), RFQ market depth (P05), mirror step share (P02 / P07). The mechanisms are general; the values may not
  suit another supplier of the same type.
- Default rules whose live evidence is ONE supplier: one fact per e-mail + choice framing for cash-short suppliers (P11),
  two index claims in round 1 for raw material (P18 / P08), hedged-supplier rules (P08), price-frozen rules (P03).
- Seven ideas were rejected or withdrawn tonight because they helped one case and hurt another, or did nothing (LESSONS.md).

## 4. Evaluation - mostly in-sample
We tuned and tested on the same 9 practice suppliers, so **~0.83 is optimistic for new suppliers**. Out-of-sample evidence
so far: sandbox D01 (supplier not in our data) 0.87-0.91; sandbox D02 RFQ 0.52-0.60 (no facts available); the 19-case crash test
(9 never-played cases) for robustness only. Expect somewhat lower on Sunday's suppliers (a guess, not measured).

## 5. How we know a supplier is "the same"
The arena gives every supplier a fixed id in every case (`sup:70140` is always the P11 foundry). Supplier-specific knowledge is
keyed by that id (and, for lessons, also the case type), so it applies only to an exact match; everything else gets general rules.

## 6. Do the general principles hold without the supplier recipes? (live A/B, same window)
| case | old recipes | general principles |
|---|---:|---:|
| P02 | 0.740 | **0.767** |
| P07 | **0.792** | 0.786 |
| P10 | 0.694 | **0.702** |
| P11 | 0.794 | **0.877** |
| mean | 0.755 | **0.783** |

The general principles do at least as well - generalising did not dilute the score.
