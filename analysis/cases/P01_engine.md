# P01 engine (Brandlhuber, sup:70110, price_increase, stabilise) - DONE 2026-10-10 evening, offline
Tool: `uv run python ../../analysis/tools/case_engine.py P01` (5 games). Value = cash value at its standard 30 d.

**a) Type: mirror, data-sensitive, patient.** Its step is ~0.45x ours without new data and >1x with data (8bdb: we +0.48 with
data, it -2.44). "We did not know that - a fair point" (6 reason lines: the data-naive owner). Only 1 final offer in 5 games
(our 5th message): it keeps moving if we do. Relationship charge: full cost ~EUR 129.95 (fitted on 8bdb at 8%).

**b) Cuts per data kind:** notice period (51 d letter vs 90 d contract) taken 2/3 - biggest first move; energy index
(PPI-D351, falling) taken 2/2; volume forecast taken 2/2; the alternative quote (dearer) "does not change" 1/1.

**c) Not yet cited (honest, checkable), ranked:**
1. Should-cost `cost:310010` EUR 132.64 vs its EUR 138.55 quote (4.3% above): should-cost was taken 9 of 9 elsewhere.
2. Its own quote `quote:7300001` EUR 126.53 of 3 Sep 2026, 8 days before the +9.5% letter (may be "irrelevant": not in refs).
3. Steel PPI-C241 -4.3% (idx:PPI-C241@2024-10, @2025-10), weight 0.26.
4. 7 quality notifications on this part in 12 months (qn:20004728, qn:20004837, ...); scorecard amber, 712 ppm.
5. Energy PPI-D351 -17.2% (2025-02 -> 2026-02) is a different window than the cited -3.7%; same series = likely "duplicate".

**d) Targets** (relationship included; cash rate 8% or 14% gives the same answer on 14 d):
best 0.91 = EUR 132.20, 14 d, Jan 2027. 0.9 needs <= EUR 132.34 (Jan, 14 d) or **<= EUR 134.79 (Apr 2027, 14 d)**; 1.0 at
EUR 130.66 (Apr, 14 d). 60/90 d only work if its cash rate is ~8% (unknown) - **14 d is the safe structure**. 1% price = 0.065.

**e) Plan:** one sheet, **effective 2027-04-01, 14 d** (the notice argument justifies April). Msg 1: notice period + should-cost
+ energy -3.7% (3 kinds). Msg 2: steel -4.3%. Msg 3: QNs. Msg 4+: forecast, own quote. Step 30% of the gap (it mirrors);
it rarely goes final, so close when it is within 0.3% of our ask after msg 5. Expected 0.92-0.95.
