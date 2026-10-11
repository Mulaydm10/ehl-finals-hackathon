# P10 record investigation - experiment log and changelog (Parth; notes/agent_changelog.md is Dhruv's file, not edited here)

Brief: "P10 Record-Breaking Investigation - Ravensteiner".
- Sequence: Run 1 offline Qwen -> Run 2 offline Astra -> exactly ONE hosted P10 session.
- Marks:
  - repeatable normal-mode best 0.7097 (31.10 @ 56 d / 36 m / 23,400);
  - historical high 0.740961 (30.70, engine-template window, 673ee890);
  - beat it at <= 30.69 @ 56 d (0.741742).

| when (CEST) | run | type | agent / code | result | record |
|---|---|---|---|---|---|
| 10-11 06:30 | Run 1 | offline; Qwen requested, unreachable (0 LLM calls) | noidea_p10.py / P10_M.json at 44e6f47; new analysis/tools/p10_record_check.py | archived replay byte-equal (turns 1-2); fitted sim 31.10-31.20; documented sim 0.80 at msg 1 (unfit); exact marks verified; the current path stops at 31.10 (first counter pinned at 31.50 in 40/41, final at msg 2 in 39/39, largest cut there 0.40); strongest untested lever = one step inside its 2% authority after its final (30.69), odds low | analysis/offline_runs/2026-10-11_P10_run1_qwen/ |

## Changelog
- **Run 1 (no agent change):**
  - New offline check `analysis/tools/p10_record_check.py`: exact marks, P10 trace statistics, every post-final e-mail in
    the archive, archived replay of noidea_p10.
  - General rule 127 added (docs/GENERAL_RULES.md): after a final, suppliers agreed only to sheets worth at least their
    final to them.
  - P10_R's hypothesis text corrected: P18's sub-offer agreements came in open rounds, not after a final.
