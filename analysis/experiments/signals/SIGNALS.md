# What the conversations teach the agent - signals mined from 189 practice games (Parth, 2026-10-11)
`tools/experiments/mine_signals.py` -> `replies.csv` (1,225 supplier answers: status, prices, both sides' moves, claim
results, text markers). Rerun it after new games; the numbers below are from 2026-10-11.

| signal (its words) | what follows | evidence | use in the agent |
|---|---|---|---|
| "We need to clarify this internally - we will come back to you on price" (half a step for a much lower rival) | the next answer brings "the rest of the step" **whatever we do** | 41 of 41; its next cut 1.68 when we moved vs 1.62 when we sent nothing (P05 only - an RFQ mechanism) | don't spend a concession in that round; if the next answer is likely its final (it gave the half step in its round >= 2), make that round's ask a probe just over its new line (P05: 27.50 -> 26.60 agreed, 26.55 refused = 3.3-3.5 % under its counter; after a round-1 half step the next answer was open at 6-7 % under) |
| it agrees at **our** price below its own last counter | its counters sit on a grid rounded up; its line is inside the grid cell | 22 agreements in P05, P07, P10, P11, P18 (offsets 0.03-1.90) | before taking an OPEN counter, one probe under it (the grid probe does this for holders; RFQ threads lack it) |
| price grid of its counters | 0.50 (P05, P11), 0.10 (P10, P18), 0.05 (P01), cents (P02-P04, P07, P08) | per case | probe depth = a share of the grid step |
| "took it into account" on our data | a cut in 88 % of answers, mean 1.78 | n=239 | lead with the data it takes; one new fact per round (P11: facts spread over rounds = one 0.50 step each, 0.8019 -> 0.885) |
| "it holds, but it does not change our calculation" | mean cut 0.007 | n=57 | stop citing data to that supplier (P04: data in round 2 brought its final a round earlier) |
| walk-aways | after its final_offer, after timeouts, after a repeated or tiny move | 21 walks | never push after final; never repeat an ask after a hold; no tiny moves |
| round of its first final_offer | P10 1-2, P04 2-3, P05/P08/P18 3-4, P02/P07 4, P03/P01 5, P11 4-7 | 120 threads | the levers (facts, rival, probe) must be in before round 3 |
| **one timeout (its patience drops)** | it concedes faster and goes final sooner, LOWER | P05: first counter 28.00 / 27.50 after a round-1 timeout vs 30.00 after a no-price note (fff61af1) and 30.50 with no hold; final 27.00 (or 26.60 agreed) vs 27.50 / 28.00. P11: held path ended at 44.45 vs 44.50 | candidate agent switch (round-1 hold) - needs an A/B on other cases before the final: it costs ~65 s of the wave and a patience step |
| a no-price question in round 1 | answered, quote moves a little (38.50 -> 38.00 + "Which figures?") but **no patience drop** | P05 fff61af1 | not a substitute for the timeout |

Rounds do not score: practice ranks the best score per case, and in the final fewer rounds win a tie. More rounds help
only when each one carries a new lever (a fact, a rival, a probe); a supplier without a new reason holds and goes final.
