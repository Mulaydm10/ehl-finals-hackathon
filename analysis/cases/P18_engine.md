# P18 engine (Blankstahl Werdenfels, sup:70740, raw_material, leverage) - DONE 2026-10-10 evening, offline
Tool: `case_engine.py P18` (11 games). Same part as P08, other supplier.

**a) Type: mirror (0.8-0.9x our step), short patience.** It moves EUR 0.10 per round when we move 0.10 (4e24: 5.20 ->
5.10 -> final 5.00; 6d61, a99d alike). Final at our msg 3 (7 of 10). AS-14404 clause mandatory on 24 m; its db5
alternative costs the same as db0 for us. Not hedged (unlike P08).

**b) Data:** price history (the July 5.26 -> 5.84 index step) taken 9/9; falling index taken 6/6; forecast 6 taken / 3 no.
A rising PPI-C2431 inside a cost calc drew "confirm our case".

**c) Not yet cited, ranked:** 1. **Alloy AS-14404 -8.5% (idx:AS-14404@2024-11, idx:AS-14404@2025-10)**, weight 0.43 -
this supplier is not hedged and took falling indices 6/6. 2. 1 quality notification (qn:20004916). 3. Labour -0.3%.
(Rival `quote:7300008` EUR 5.45 is above our deal now - useless.)

**d) Targets** (24 m, 30 d, AS db0): best 0.677 = EUR 5.00. **0.75 = EUR 4.893, 0.8 = EUR 4.817, 0.9 = EUR 4.670.** 1% = 0.034.

**e) Plan:** 24 m, clause-free asks (it adds its clause; accept either deadband). Msg 1: price history + AS -8.5% +
forecast. Msg 2: other parts' price jumps (all_parts_po). Steps 30% of the gap instead of 0.10 (mirror rule: P02 0.67 ->
0.82 with it). Accept its msg-3 final. Expected 0.72-0.76.
