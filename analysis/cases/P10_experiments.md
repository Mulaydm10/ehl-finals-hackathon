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
| 10-11 07:00 | Run 2 | offline, gpt-6-astra (60 calls) | new noidea_p10r.py + P10_R.json (59c8 msgs 1-2 byte for byte, then 30.69 inside its 2% after the final); probe.py stop_on_template; mode_watch watch-only | agent branch checks ALL PASS; archived replay: only the post-final turn changes (4 of 11 games), 0 errors; fitted sim hold 0.7097 / agree 0.741742 / walk 0; Astra as the supplier: hold 40 of 40 for 30.69 ('my approval authority is not an additional discount allowance'), control 30.40: hold 9, walk 1 -> agreement NOT demonstrated; selected for the one hosted game, labelled speculative | analysis/offline_runs/2026-10-11_P10_run2_astra/ |

## Changelog
- **Run 1 (no agent change):**
  - New offline check `analysis/tools/p10_record_check.py`: exact marks, P10 trace statistics, every post-final e-mail in
    the archive, archived replay of noidea_p10.
  - General rule 127 added (docs/GENERAL_RULES.md): after a final, suppliers agreed only to sheets worth at least their
    final to them.
  - P10_R's hypothesis text corrected: P18's sub-offer agreements came in open rounds, not after a final.
- **Run 2:**
  - New `analysis/agent_variants/noidea_p10r.py`: the record-line price from the cost engine (30.69 on a 31.10 final),
    only inside 2% of the final and above our last ask; e-mail in code; then accept what stands; no move on an
    engine-template reply.
  - P10_R round 3 aligned to it and status-neutral.
  - `probe.py`: `stop_on_template`.
  - `mode_watch.py`: `--max-plays` defaults to 0 (watch only; the brief rules out playing the template window).
  - Defect found and fixed offline: on a fresh agent `self.sup` did not exist before `prepare()`, and main's crash guard
    then pushed again (30.07) on an open counter. The check now fails on any crash-guard firing.

