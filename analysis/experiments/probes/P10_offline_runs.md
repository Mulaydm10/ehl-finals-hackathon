# P10 offline runs (Parth, 2026-10-11) - `tools/experiments/p10_offline.py`

Offline arena = the kit's arena-sim API on 127.0.0.1 with a Ravensteiner supplier fitted to the 38 normal-mode P10 games
(rules in the script's docstring); `probe.py` runs UNCHANGED against it (same messages, branches, accept logic), its logs
go to a scratch folder, no arena call, no quota. Each run: what it tested, the result, the lesson.

| # | design | mode / draw | rounds (its replies) | result | lesson |
|---:|---|---|---|---|---|
| 1 | P10_M (59c899b9's e-mails) | normal, seed 1 (noise drawn) | 31.50 -> final 31.20 | 0.7019 (C 1,508,829.60 = live to the cent) | The offline arena reproduces the live mechanics and the score exactly. The design lands on 31.10 or one grid step higher (31.20) depending on the model's sample; live, these exact e-mails drew 31.10 three times out of three, and every reworded variant (K, P, L) drew 31.20. Lesson: keep 59c899b9's two e-mails byte for byte. |
| 2 | P10_R (59c8 + one step to 30.69 after its final) | normal, seed 2, post-final "accept" | 31.50 -> final 31.10 -> 30.69 sent -> "Our final offer stands" 31.10 (new id offer:70410-3) | 0.7097 | The hold branch works end to end: after a hold the script accepts the NEW standing id (the old final id is stale), so a hold costs nothing against the baseline. Found a simulator bug, not a script bug: the forced "accept" draw only accepted under a drawn hidden floor; fixed to mean "accepts any ask within 2% of its final" (the 2%-authority hypothesis) for run 3. |
