STATUS: DONE (peer task: "what predicts or triggers P10's 31.00 first counter") - 2026-10-11, cloud session, offline only
(0 arena sessions, no LLM calls). Sources: all 30 P10 sessions (datasets/runs, tools/replays/raw), all 229 recorded sessions
of every case for the time check, notes/quota_log.md, notes/agent_changelog.md, tacto/brief. Tool: `analysis/tools/supplier_mode_scan.py`.

# P10: the 31.00 was not a lucky draw. The arena's supplier model was off and its engine answered by itself

## 1. The answer
| question | answer |
|---|---|
| What gave 31.00? | **The arena's engine-template mode.** Every session created 23:51:08-23:58:06 CEST on 10 Oct (7 of 7, six cases, incl. 673ee890) got replies made only of the engine's fixed sentences. No model-written sentence appeared. Before (23:46:02) and after (00:06) the replies were normal again |
| How do the modes price P10? | Template: **31.00** (1 of 1). Normal: **31.50 in 11 of 11** games whose round 1 had the price path + should-cost taken (with or without a third fact) |
| Did our e-mail cause it? | **No.** 67f3678f sent 673ee890's round 1 again: same sheet, refs, data sentences, committee sentence and subject. It drew 31.50 in normal mode. Only the model-written first paragraph differed, and in template mode no model reads it |
| Can we predict it? | **Not before round 1**: the opening is byte-identical in all 30 P10 sessions. **After round 1, yes**: engine sentences + a 4-day delay (normal mode: 2) |
| Can we trigger it? | **No.** It switched on and off for every case and every agent at once (an arena-side state). The only way to force it would be to make the arena's model fail. That attacks the organiser's service and shows in the replays. **Not built, not recommended** |
| Can 0.741 be beaten in normal mode? | **Not with any known lever.** It needs ≤ 30.69, i.e. 0.81 below the 31.50 first counter in the one e-mail before its final. The best measured step is 0.40 (59c899b9) |
| Plan | Keep `noidea_p10` (0.710 live in normal mode, 2 of 2: 59c899b9, 3c4aa1a6). Its round 2 (36-month move + labour index) is also what the engine's approval ladder rewards. A template-mode session is the only chance at > 0.741: estimate 30.40-30.60 (0.75-0.76, unmeasured) |

## 2. 673ee890 vs 67f3678f, field by field
| field | 673ee890 (0.741) | 67f3678f (0.694) |
|---|---|---|
| created | 23:58:02 CEST: v2.34b batch, 5 cases 4 s apart | 00:08: single run |
| its opening | 32.20 @ 54 d, 19,890, 12 m, delay 2 | **byte-identical** (as in all 30 P10 sessions) |
| our subject | "Re: Ravensteiner cuts the seal allocation" | same |
| our sheet | 29.57 / 23,400 / 36 m / 56 d | same |
| our refs | cost:340010, 3 POs, sc:70410@2026Q3 (same order) | same |
| our data + committee sentences | should-cost, path, OTD 79.5%, "please put this proposal to them" | identical |
| our first paragraph (model-written) | "You have linked additional capacity to binding commitment; ..." | "Your capacity updates link additional allocation directly to firm commitment ..." |
| its reply delay | **4 days** | 2 days |
| its reply wording | **engine template**: "We value our cooperation and have made a step towards you." "The contract term is reflected in the price." "**Any further step needs approval from our management.**" | **model**: "Given our current capacity constraints, we must maintain a firm position on pricing." + a "Legal Department" line |
| OTD claim | "it holds, but it does not change our calculation" | not mentioned |
| its counter | **31.00** | 31.50 |
| our round 2 | forecast (shrugged), ask 29.94 | labour index (taken), ask 30.11 |
| its final | "**Our management has approved a further step.**" 30.70 | "We have verified the minor decrease in the labor cost index" 31.30 |

## 3. The window (every recorded session, all cases)
| created (CEST, 10-11 Oct) | sessions | mode |
|---|---|---|
| up to 23:46:02 (incl. the v2.34 pass: P01, P02 407b3d1a, P03, P04, P11 x2) | 219 | normal (model-written replies) |
| **23:51:08-23:58:06** (P11 x2, P02 10b624c1, P07 216f49e9, P08 00e8923e, **P10 673ee890**, P18 3cb62cb9) | **7** | **template, every reply** |
| 00:06-00:18 (P10 a9e2c0e4, 67f3678f, 59c899b9) | 3 | normal |

Outside the window, only 2 single replies in 222 sessions were full engine renders (P11 3d85f139 round 1 at 18:56;
P05 37c25dfb sup:70250 round 1 at 22:27). The rest of those sessions were normal. So the fallback also happens rarely on
single replies, not only in the window.

## 4. What the engine does when it answers alone
- **Its own step**: "We value our cooperation and have made a step towards you" (round 1 in P07, P08, P10, P11, P18 template games).
- **The approval ladder** (the brief: "bigger moves need the boss's approval"):
  - the reply says "Any further step needs approval from our management" and takes **2 days longer** (P10: 4 instead of 2; P02: 3 instead of 1 in 20 of 20);
  - the next e-mail draws "**Our management has approved a further step**": P10 -0.30 (on a shrugged fact), P02 -2.01 (-0.54%);
  - both approved steps followed an e-mail where we raised our ask (P10 29.57 -> 29.94; P02 364.69 -> 365.31).
- **Not better everywhere**:

  | case | template-mode result | best in normal mode |
  |---|---|---|
  | P10 | 0.741 | 0.710 |
  | P07 | 0.825 | 0.812 |
  | P02 | 0.809 | 0.847 |
  | P18 | 0.688 | 0.727 |
  | P08 | 0.781 | 0.916 |
  | P11 | 46.50 first counter, 3 of 3 (the high one) | 46.00 in 13 of 43 games on the usual opener |

  The model in normal mode departs from the engine's figure in both directions: firmer on P10 (+0.50), sometimes softer on P11 (-0.50).

## 5. Warning for main (v2.34b) - now settled by the 00:06-00:10 normal-mode pass
P02 0.56 -> 0.81, P07 0.825 and P10 0.741 were credited to v2.34b (one fact per later e-mail). All three came in the template
window. Dhruv's next pass (v2.34d, 00:06-00:10, every reply model-written) separates the two:

| case | template window (23:58) | normal mode (00:06-00:10) | verdict |
|---|---:|---:|---|
| P02 | 0.809 | **0.828** (b09861f7) | the fact-pacing fix is real |
| P07 | 0.825 | **0.773** (88c1d97f) | 0.825 was the window, not the agent |
| P10 | 0.741 | 0.694-0.710 (main, noidea_p10) | 0.741 was the window |
| P08 | 0.781 | 0.916 (2bfced14) | the window was worse here |
| P18 | 0.688 | 0.621 (77b16b90) | - |

Check: `python3 analysis/tools/supplier_mode_scan.py` (reads UTF-8; on Windows the default cp1252 made 673ee890 read as
"model"). A session that ends in a walk-away or a hold is not "mixed": those replies are now ignored.

## 6. P10 in normal mode: what the data says next
| finding | evidence |
|---|---|
| Round 1 stops at 31.50 after two taken facts | 31.50 with 2 taken (991f, a2e3, 7a92, e61c, 8134), 3 taken (a9e2, 59c8, 3c4a: rubber index "took it into account") or + OTD/ppm (67f3, 0b29) |
| So round 1's third fact is wasted | the rubber index changed nothing in round 1 (a9e2, 59c8) |
| Stacked round 2 is the biggest step | 59c8 and 3c4a: 36-m move + labour index, ask 30.40 -> 31.10 (-0.40), 2 of 2; the move alone -0.10 to -0.30; labour alone -0.20 |
| **Untested tweak** | round 1 = path + should-cost only; round 2 = the 36-m move + labour **and** rubber index. Best case about 30.90 (0.725). Risk: v2.34's finding that a 2nd fact in a later e-mail usually adds nothing (P11, P07, P03). It cannot reach 0.741 either |

## 7. How to read a P10 game while it runs
- First reply has "We value our cooperation and have made a step towards you" or "Any further step needs approval from our
  management", and a 4-day delay: **template mode**. Send `noidea_p10`'s round 2 as is: a move + a new taken fact, and our
  ask raised from round 1. Expect the approved step on top.
- First reply has model wording ("capacity constraints", "firm position", "manufacturing realities") and a 2-day delay:
  **normal mode**. `noidea_p10` round 2 -> about 31.10 (0.710).
- Scan any batch afterwards: `python3 analysis/tools/supplier_mode_scan.py P10`.
