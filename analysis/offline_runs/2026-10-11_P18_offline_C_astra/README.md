# P18 offline run C (2026-10-11 ~05:12; no arena session, no LLM calls): acceptance-model audit over all 59 P18 games

Command: `cd tacto/starter-kit && .venv/Scripts/python.exe ../../analysis/tools/p18_accept_model.py` -> accept_model_audit.txt
(strictly local: reads datasets/runs and tools/replays/raw).

## Findings
- **0 of 8 acceptances were more than 2% (nominal) under its standing offer** (1.2%-1.96%; three were its own alternatives
  proposed back). Its 2% approval rule (doc:20260812-70740-M3) is real.
- **Payment and deadband count in its acceptance** (value model: db5/db3 -0.10; payment shorter than 30 d +0.10, longer -0.10):
  0c968aae accepted 4.91 @ 14 d (value 5.01) and refused 4.97-5.00 @ 14 d db5 (values 4.87-4.90) although 5.00 db5 is 0% under
  its 5.00 primary; 81b5c6de refused 4.94 @ 45 d (value 4.84) where 6c2813ce had accepted 4.94 @ 30 d (4.94).
- **Each conversation has its own floor (value terms):** 6c2813ce (4.91, 4.94]; ff6a6b20 <= 4.90; 0c968aae (4.97, 5.01];
  a09d9536 (5.01, 5.04]; c4bcc22c <= 5.10.
- Which price the 2% is measured on is not settled by the data: (a) its value, (b) the nominal price of its primary sheet,
  (c) its sheet with the same clause. In the 6c2813ce state (5.00 @ 45 d db0 + 5.10 db5): 4.97 @ 14 d db5 (value 4.97, 0.6% under
  its 5.00 primary) passes (a) and (b); 4.86 @ 14 d db0 (value 4.96, 2.8% nominal) passes only (a). Both clear that state's floor
  if 14 d is worth +0.10 to it (0c968aae: leaving 14 d "requires an adjustment"; c4bcc22c: 5.00 @ 14 d accepted against 5.10 @ 45 d).

## Decision for the record attempt (noidea_p18_pay14.py)
msg 3 in the 6c2813ce state = 4.97 @ 14 d db5 FIRST (passes 2 of 3 readings; 0.7593) + 4.86 @ 14 d db0 (0.7611); after a hold,
msg 4 = 5.00 @ 14 d db5 (value 5.00, 0% nominal under its primary; 0.7393) + 4.90 @ 14 d db0 (0.7339), with a new fact.
Estimated chance of a record: ~0.4 (the 2% reading and the 14-d credit in this conversation are the two unknowns).
