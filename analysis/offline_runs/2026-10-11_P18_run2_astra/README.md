# P18 Run 2 - offline, gpt-6-astra: the 45-day soft-state candidate (2026-10-11 04:43; no arena session)

**Model:** gpt-6-astra (tacto/starter-kit/.env.openai). Qwen not used (user: "use astra everywhere"; the local server is unreachable).
**Arena:** no session. The planned Run 3 (one hosted P18 session) was NOT executed: the user said "dont run on the arena".

## What Run 1 taught and how it shaped Run 2
Run 1 showed that the documented simulator cannot rank P18 strategies (it accepts 4.76 at message 1). It also showed that every
existing P18 agent's hosted outcome is already known, because Werdenfels answers identical conversations identically:

| candidate | what it does | known hosted outcome | can it beat 0.727? |
|---|---|---|---|
| noidea_p18_cross | 4.76 @ 30 d, then 90 d from msg 2 | 90 d charged +0.10 (f2770f53), guard back to 30 d, final 5.00 @ 30 d = **0.677** | no |
| noidea_p18_soft v2 | 4.87 @ 30 d (+ asks for its db5 price), beat sheets if round 2 = 5.00 | 5.00 + 5.10 db5 at round 2 but floor 5.00, final 5.00 @ 30 d = **0.677** (x6, identical) | no |
| noidea_p18_replay | 0c968aae msg 1-2 verbatim, msg 3 set by P18_MSG3 | 4.91 @ 14 d accepted = **0.727** (a tie); every lower ask drew its final | no (tie at best) |
| **noidea_p18_state45 (new)** | 6c2813ce msg 1-2 verbatim -> its 5.00 @ 45 d state; msg 3 4.93 @ 45 d, msg 4 4.94 @ 45 d | not played | **yes: 0.7357 / 0.7289 if accepted; else 0.688** |

So Run 2 tests the only recorded state where a <2% ask scores above 0.727 on the structure the supplier already holds.

## Why the 6c2813ce state
- After 6c2813ce's msg 1-2 the supplier stood at 5.00 @ 45 d db0 (+5.10 db5). Its msg 3 (4.91 @ 30 d) drew a HOLD, not a final;
  its msg 4 (4.94 @ 30 d) was AGREED. Its floor at 30 d is in (4.91, 4.94].
- It did not credit the move 45 -> 30 d, and 45-d openings ended at the same 5.00 floor as 30-d ones, so 45 d looks free there.
  If so, 4.93 @ 45 d is accepted when the floor is <= 4.93 (about 2 in 3) and 4.94 @ 45 d always. If it values 15 days at its
  8% cash rate (+0.0167), 4.94 @ 45 d passes only for a floor <= 4.923 (about 4 in 10). Both asks are inside its 2% authority
  (1.4% / 1.2% under 5.00), never a step back (4.90 -> 4.93 -> 4.94), on its own clause and term.
- The record (0.75595) is NOT reachable in this state: 45 d db0 needs <= 4.89 = 2.2% under 5.00.

## Checks (all offline)
| check | result | file |
|---|---|---|
| msgs 1-2 vs 6c2813ce | byte for byte equal (subject, body, sheets, refs); msg 3 = its msg 3 with only the proposal changed | state45_check_v2.txt |
| branches after msg 3 | agreed -> accept; hold 5.00 -> msg 4 4.94 @ 45 d -> agreed / final -> accept; final -> accept its primary; counter 4.92 -> accept | state45_check_v2.txt |
| **defect found (v1)** | the off-track handover to main re-cited msg 1's order prices and repeated our price (4.93 after 4.93; 4.77 after 4.77), the empty-repeat pattern that made it walk in fe806698. **Fixed:** the plan runs through msg 4 whatever it answers, never repeats or steps back; main only from msg 5 | state45_check_v1_defect.txt (2 Astra calls, 9.4 s mean) |
| off track (counter 4.95; first counter 5.30) | 4.94 @ 45 d (+0.01); msg 2 4.90 @ 45 d + forecast | state45_check_v2.txt |
| archived replay (42 games) | 0 errors | archived_replay_state45.txt |
| documented simulator + Astra | 0.94 at msg 1 (not predictive, as in Run 1); 0 Astra calls (P18 rounds are code-written) | sim_noidea_p18_state45.txt |

Exact scores (arena cost model): 4.93 @ 45 d db0 0.7357; 4.94 @ 45 d 0.7289; fallback 5.00 @ 45 d 0.6883; record line 4.89 @ 45 d
0.7627; our best 4.91 @ 14 d 0.7271.

## Code changes in Run 2
- new `analysis/agent_variants/noidea_p18_state45.py` (with the off-track fix above);
- `noidea_p18_replay.py`: stale default P18_MSG3 4.97/14/5 (refused live) -> 4.91/14/0 (the only accepted msg 3, 0.727);
- new `analysis/tools/p18_state45_check.py`.

## Selected agent for a hosted run (not executed)
`noidea_p18_state45.py`: the only candidate with a realistic chance above 0.727 (estimated 40-100% for 0.729-0.736), and no
chance at the record. The expected improvement is small (+0.002 to +0.009). It stays unplayed until the user asks for an arena run.
