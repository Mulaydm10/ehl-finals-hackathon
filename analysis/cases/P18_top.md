# P18 - taking the top back from Codacabana (Parth, 2026-10-11 ~07:00)

**Goal:** beat 0.75595, Codacabana's 4.90 @ 45 d with the AS-14404 db0 clause. Our best is 0.727 (0c968aae, 4.91 @ 14 d db0).

**Sources:**
- all 67 recorded P18 games: `datasets/runs`, `tools/replays/raw`, back office;
- Neel's P18_deep / P18_lever / P18_experiments;
- the case file and the cost engine.

**Agent:** `analysis/agent_variants/noidea_p18_top.py`.
**Checks:** `analysis/tools/p18_top_check.py`, output in `analysis/offline_runs/2026-10-11_P18_top_offline/`.
**Live runner:** `tools/experiments/p18_top_run.py <variant>`.

## 1. How Werdenfels prices and agrees (67 games)
| fact | evidence |
|---|---|
| Its own counters never go under **5.00 db0 / 5.10 db5**, at 14, 30 or 45 days | 67 of 67 |
| Every price under 5.00 was it **agreeing to our ask**, always within 2% of its standing offer | 4.91 @ 14 d (0c968aae), 4.94 @ 14 d (a09d9536), 4.94 @ 30 d (6c2813ce); Codacabana's 4.90 @ 45 d = exactly 2.0%; doc:20260812-70740-M3 |
| Agreement needs our ask at or above a **hidden line** fixed for each conversation | the 0c968aae state accepted 4.91 and refused 4.90 / 4.89 / 4.86 and five db5 asks; the 6c2813ce state accepted 4.94 @ 30 d and refused 4.93 @ 30 d, 4.94 @ 45 d and 4.97 @ 14 d db5 |
| The line is measured **in its money**: db5 counts about 0.10, 45 days about -0.05 against 30 days, 14 days counts in some conversations and not in others | these values explain every reply in the 6c2813ce state (line 4.935 at 30 d) to the cent |
| A line under 5.00 exists only in **soft** conversations, where its round-2 counter is already 5.00 | 3 of 21 distinct round 2s after a 5.20 start; Neel's two new round 2s after 6c2813ce's msg 1: 0 of 2 |
| Softness is a **draw per conversation**: identical text gets the identical reply, any change re-rolls | 6c2813ce's msg 2 with only the ask changed (4.90 -> 4.88) drew 5.10, not 5.00 (cd68b78d) |

Why our two reproducible states cannot reach 0.756:
- **0c968aae state (14 d):** every beat on 14 days is more than 2% under its 5.00 / 5.10. Beat lines there are 4.86 db0 / 4.97 db5.
- **6c2813ce state (45 d):** its line, about 4.935 at 30 days in its money, is above the value of every beat sheet. The
  45-day db5 beat at 5.00 is worth 4.85 to it.

## 2. The beat sheets inside its 2% (24 m; exact scores)
| sheet | score | worth to it (line model) | inside 2% of |
|---|---:|---:|---|
| **5.00 @ 45 d db5** | **0.7618** | 4.85 | its 5.10 db5 (1.96%) and its 5.00 db0 |
| 4.97 @ 14 d db5 | 0.7593 | 4.87-4.97 (depends on the 14-day credit) | its 5.00 db0 only (2.5% under 5.10 db5) |
| 4.99 @ 30 d db5 | 0.7576 | 4.89-4.94 | its 5.00 db0 only |
| 4.89 @ 45 d db0 / 4.88 @ 30 d / 4.86 @ 14 d | 0.763 / 0.759 / 0.761 | - | none: more than 2% under 5.00 |

## 3. Plan (`noidea_p18_top.py`)
1. **msg 1:** 6c2813ce's, byte for byte. The arena answers it with 5.20 @ 45 d from its cache (5 of 5).
2. **msg 2:** a new opening every game (12 wordings, none ever sent), 4.88 @ 45 d db0 + forecast. This is a fresh soft/normal draw.
3. **msg 3:** the beat sheets inside its 2%, + labour index.
   - soft (it stands at 5.00): all three;
   - normal (it stands at 5.10): 5.00 @ 45 d db5 only.
4. **msg 4:**
   - after a soft hold: 5.02 db5 / 4.92 db0 @ 45 d (0.749 / 0.742, both over our 0.727);
   - after a normal counter: 5.10 @ 45 d db5 (0.696, its 5.00 floor in its money).
5. **Guards:** accept anything that beats 0.756 at once; propose back its own alternative if it beats; accept finals; accept
   what stands on an engine-template reply or if it is still open after msg 4.

## 4. Odds and stop rule
| step | rate |
|---|---|
| soft round 2 | ~1 in 6 |
| a soft line low enough for a beat sheet | ~1 in 4 |
| plus the normal-branch shot (5.00 db5 @ 45 against 5.10) | small, untested |
| **per game** | **~5%** |

- One game per variant, at most 12, stopping at the first beat.
- Every game is recorded and pushed.
- A game that does not beat changes nothing on the board (best score per case counts).

## 5. Live log (one game per variant; recorded in notes/quota_log.md and analysis/experiments/p18_top_results.jsonl)
| time | session | msg 2 variant | its round 2 | msg 3 | result |
|---|---|---|---|---|---|
| 07:06 | 1c767030bd2efdd2 | 0 | 5.10 (normal) | 5.00 @ 45 db5 (1.96% under its 5.10) | final at once 5.20 @ 45 d db5 -> **0.6295**. The normal-branch shot ends the game at its db5 price |
| 07:08 | 013521be77ea88e5 | 1 | 5.10 (normal) | 5.00 @ 45 db5 | final at once 5.20 @ 45 d db5 -> **0.6295** |
