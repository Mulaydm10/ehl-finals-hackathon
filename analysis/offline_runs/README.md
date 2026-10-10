# Offline runs with an LLM (no arena sessions, 0 practice quota)

`analysis/tools/offline_astra.py` runs the NoIdea agent (v1.5, `ef489c6`) **with gpt-6-astra writing the
opening paragraphs** against Dhruv's simulated supplier (`src/eval/offline_eval.simulate`: real opening
quote from the probes, exact C_open / C_best). Responsive supplier r = 0.30, stubborn r = 0.10.
Full e-mails and term sheets: `<case>_gpt-6-astra.json`. Run on Neel's Windows laptop, 2026-10-10.

**Caveat:** the simulator is optimistic (P01 sim 0.98 vs live 0.85): it ignores arguments, tone and the
relationship charge. Use it to spot bugs and rank versions, not as a score forecast.

| case | supplier | sim score | rounds | Astra calls | Astra time |
|---|---|---:|---:|---:|---:|
| P02 | responsive | 0.94 | 5 | 5 | 32 s (6.4 s/call) |
| P02 | stubborn | 0.98 | 6 | 6 | 36 s |
| P03 | responsive | 0.96 | 1 | 1 | 3 s |
| P03 | stubborn | 0.96 | 1 | 1 | 4 s |
| P04 | responsive | 1.00 | 2 | 2 | 9 s |
| P04 | stubborn | 0.98 | 6 | 6 | 38 s |

Mean 0.97. 0 LLM errors; every call well inside the 60 s per-message limit.

## What's right
- P03: **36 months, volume 4,580 (= need)**: the two big levers (+0.60). P04: **36 months at €4.79–4.90**,
  below the €4.935 flip price, so the long contract is correct here. P02: **no index clause** (path +5% costs us).
- Astra's paragraphs fit the motives: approval authority (P02, P03), price freeze → terms (P03), open book →
  "send your cost calculation in XLSX" (P04). Tone is polite and partnership-minded.

## Issues found (for Dhruv)
1. **P02 cites a rising index against itself:** round 1 cites `PPI-C241` **+6.2%** (steel, 6 m). That supports
   the supplier's increase. Better: copper 6 m **+16.0%** (vs its 12 m +47.7%) and labour +1.7%
   (`analysis/cases/P02.md` §7). Claim selection should skip indices whose change ≥ the asked/justified %.
2. **Language switch:** P02 round 2 (responsive), Astra wrote its paragraph **in German** ("Uns ist an einer
   partnerschaftlichen Lösung gelegen…") while the rest of the e-mail is English. Add "Write in English" to
   the system prompt, or detect and fall back to the plain opening.
3. **Windows encoding bug:** the supplier name shows as `WÃ¤lzlager-Zentrum SÃ¼d` in P04. `NoIdeaAgent.__init__`
   reads `A_dossiers.json` / `C_arguments.jsonl` with `read_text()` without `encoding="utf-8"`. Fine on macOS,
   garbled on Windows. **Matters if the final runs on a Windows machine.**
4. **P03 anchor = target:** the first sheets already score 0.96 (sim agrees instantly). Against the real
   supplier there's no room left to concede, and the sim ignores P03's relationship charge (8% sustainable
   margin, €28k/pt): at full cost ≈ should-cost the brief estimates ~0.83 at €429. Consider anchoring ~1–2% lower.
5. **P02 payment days:** all sheets trade 14/30/45 d; none offers 60/90 d. Nordmark (group, credit 147) is not
   cash-short, so 90 d at a higher headline price is the committee-friendly trade (brief: 90 d = +0.64).
   Equal C for us, but it may land better with a group.
6. Cosmetic: the body lists `index_clause None` and raw field names; better as words ("no price-adjustment clause").
