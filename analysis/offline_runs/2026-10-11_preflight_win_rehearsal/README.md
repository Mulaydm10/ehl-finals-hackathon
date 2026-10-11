# Rehearsal on Neel's Windows laptop (2026-10-11 06:20-06:29 local): free pre-flight steps + sandbox D01/D02 - **D02 lost the better bidder to a timeout**

User: "we need to rehearse now. check the discord and do whatever is needed". The Discord could not be read from this session (no
access); the arena has no rehearsal set (`/v1/cases?set=` accepts practice, final, sandbox; final -> 403 "the final has not started;
its cases appear wave by wave"); `/v1/live` phase = build, submission_at 12:00+02:00. So this is the brief's own rehearsal, minus
the practice cases: tools/final/preflight.sh steps 1-5 with D01/D02 (sandbox, free), run with a Windows copy of the script
(same env: .env + .env.openai, NOIDEA_EXPERIMENTS=hidden, `arena play case:Dxx --agent noidea -v`). No practice session used.

| step | result |
|---|---|
| 0. agent code vs frozen tag | = **final-v2** (tacto/starter-kit/arena_kit, central.py, engine_rules.py, G_lessons.json unchanged) |
| 1. key (`arena me`) | ok - practice 426 used, 324 left of 750, resets 10:22 UTC |
| 2. model | openai / gpt-6-astra: "ok" in 4.1 s |
| 3. Sunday release | not yet (08:00) |
| 4. tests | 67 passed, 3 skipped; crash test not run here (notes/analysis_v234/crash_test.py has the Mac path ~/Dhruv/... hard-coded) |
| 5. D01 (sandbox) | **0.914** in 206 s (validated 0.87-0.91) |
| 5. D02 (sandbox RFQ) | **0.333** in 229 s (validated 0.52-0.58) - session e0bd42f0fb5aa051 |

## D02: why 0.333 - the better bidder (J1, 14.80 DAP) timed out and walked; we closed on C1 (15.40 EXW)
Timeline (logs/preflight-win-D02.log, local time):
- 06:25:57 our e-mail to J1 sent; 06:26:09 our e-mail to C1 sent (parallel sends, the kit's default).
- **06:26:50** J1's reply arrives: **final_offer 14.80 @ 14 d DAP**. The kit then fetches its quote attachment
  (`GET .../attachments/att:DEMO-J1-3-quote`), but the arena serves ONE call per session at a time, and C1's POST was still running.
- **06:27:53** C1's reply arrives (**104 s** after our send - the brief says "up to about a minute"); only now does J1's
  attachment GET go through. The loop takes C1 first (model call to 06:28:02), then J1's final at 06:28:02: **72 s after it
  arrived**, past its 60 s. The kit's `arrived[J1]` is stamped when the future completes (06:28:02), so the overdue check did not see it.
- 06:28:02 the agent's RFQ rule "J1 closed at 14.80 - showing it to C1 before accepting" sends to C1 again (reply 06:28:27).
- Meanwhile the arena ran a timeout round on J1 (`moves: [{"supplier_id": "sup:DEMO-J1", "move": {"type": "timeout"}}]`):
  J1 **walked** ("We are withdrawing from this negotiation. We need to plan our machines").
- 06:28:27 accept J1 offer:DEMO-J1-3 -> **422 "not a standing offer"**; accept C1 15.40 EXW -> C 195,137 = **0.333**.

## Why it matters for the Live Final
- Second time on D02 (24dc3b6c, notes/agent_changelog.md v2.34g: "a one-off under arena load"; A/B 3 + 3 games then had 0 timeouts).
  Under the final's load (every team, 10 cases at once) supplier replies are likely slower, so this is more likely, not less.
- It hits every multi-supplier case (RFQ / bundling): one slow reply blocks the session's other calls, and a bidder's FINAL that sits
  unanswered for 60 s is lost (walk), not just a timeout round.
- `ARENA_RFQ_SERIAL=1` would not have saved this game on its own: the agent's "show the final to the rival before accepting" step
  still sends to C1 and waits ~104 s while J1's final waits.

## Suggested fixes (for Dhruv - tacto/ is his; nothing changed here)
1. In `_play_threads`, stamp `arrived[sid]` from the reply's own arrival (before the attachment fetch), or fetch attachments only
   when no other call on the session is in flight, so the overdue/urgent logic sees a waiting final.
2. Agent RFQ rule: when a bidder's FINAL is in and it is our best C, accept it unless the rival's reply is already in; never start
   a new call to another bidder while a final waits (a final + 60 s = walk-away).
3. Re-run D02 3-5x on the Mac mini (free) after any change; rehearse the 10 hosted practice cases in parallel there (10 sessions).
