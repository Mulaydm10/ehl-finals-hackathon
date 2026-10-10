# P05 engine (RFQ: 70210 Dralveck, 70240 Hrvelec, 70250 Fuchsreiter; leverage) - DONE 2026-10-10 evening, offline
Tool: `case_engine.py P05` (10 sessions). Must-have: lead <= 42.

**a) Type: auction / rival-quote responders.** Each bidder reacts to a cited cheaper rival offer: rival quote taken 24 of 30
("I give half the step now and check the rest" -> next round the rest). 70250 (free capacity, needs volume) drops fastest
(38.50 -> 31.00 -> agreed 30.36-30.94 to OUR price); 70210 goes final at 30.00-31.50; 70240 (full order book) sits at
32.1-33.2 and is the first to walk. Lead-time strain priced (42 reason lines). Walks: when our ask is far below every rival
(20% market anchor) and after counters on finals.

**b) Data:** only rival offers matter. Should-cost EUR 36.87 is ABOVE every quote - never cite.

**c) Not yet cited:** nothing material (no index drivers, no quotes for the part). The lever is the auction itself.

**d) Targets** (14 d, lead 28): best 0.614 = EUR 30.00. **0.75 = EUR 28.68, 0.9 = EUR 27.23, 1.0 = EUR 26.25.** 1% = 0.031.

**e) Plan:** every round, cite the CURRENT cheapest rival offer (`offer:` id) to each other bidder; ask 5-10% under that
market low (not 20%: walks). Keep at least 2 bidders alive; parallel sends (no timeouts). When 70250 "agrees" to our price,
do not accept at once if a round is left: re-cite its price to 70210 one more time, then take the cheapest. Expected 0.68-0.75.
