STATUS: DONE (task 6) - 2026-10-10 evening, cloud session, offline only. Files: analysis/agent_variants/noidea_neel_cloud.py +
central_cloud.py (copies of main a2584de+ / e27b6f0; central_cloud.py is an unchanged copy, only the loader points at it).

# Regression fixes for noidea_neel.py (in the cloud copies; originals untouched)

Baseline re-run on current main first: P02 stubborn (now 1.00) and P08 responsive (now 0.93) were already fixed on main.

| # | fix (in noidea_neel_cloud.py) | cause, from the sim transcript | before -> after |
|---|---|---|---|
| 1 | RFQ: a bidder at `agreed` / `final_offer` is handled first, the cheapest of them (ported from noidea.py v2.9) | round-robin by message count answered the other bidders forever; the one that agreed at EUR 28.80 in round 1 was never accepted -> timeout after 11 rounds | P05 floor-stop **0.00 -> 0.76** |
| 2 | chargeback priced at the supplier's real scorecard ppm (x2 if cash-short) in `est["ppm"]` (ported from noidea.py v2.16) | without it chargebacks look free, the variant asked EUR 500 and the supplier priced it in (EUR 45.08 vs 43.83) | P11 floor-stop **0.80 -> 0.99** |
| 3 | alternative sheets within **0.3%** of our best C (was 1%): `ALT_BAND` | after fix 2, slot 2 became 800 ppm at the same price: same value to it, +EUR 4.7k to us, and the sim picked it | P11 responsive 0.93 (after fix 2) -> **0.97** |
| 4 | mirror step only while it answers in kind: from our 3rd ask, if its last step < 0.3x ours, back to the schedule | a non-mirroring supplier otherwise gets a 40%-of-gap step every round | no sim change (protects hidden suppliers); round 2 unchanged |
| 5 | near-close only within **0.5%** of its standing value (`CLOSE_GAP` 0.015 -> 0.005) | near-closing at 1-1.5% accepted stops that a few more small steps would have beaten | P04 live-calibrated **0.81 -> 0.86**, near-live 25 **0.844 -> 0.882**, broad 36 0.789 -> 0.805 |

**Full table after the fixes** (variant_check.py: noidea.py -> cloud copy):
P02 1.00/1.00/0.92 = | P03 1.00/0.99/0.98 = | P04 0.99/0.99/**0.86** | P05 0.76/0.76/**0.76** | P07 0.91/0.86/0.95 |
P08 0.93/0.96/0.99 | P10 0.97/0.98/0.97 | P11 **0.97/0.97/0.99** | P18 0.94/0.94/0.94. Means: responsive 0.940 (noidea 0.941),
stubborn 0.939 (0.940), floor-stop **0.929** (noidea 0.918; variant before 0.818).
sim_selvbrunn (P03): base 0.913 / kam_only 0.906 / house 0.938 - **unchanged**.

**Hard constraints checked** (offline decide on the probed openings, no LLM): round 1 is byte-identical to noidea_neel.py for
P02, P03, P04, P05, P07, P08, P10, P18 (P11 differs on purpose: chargeback EUR 0). P03 refs = cost:350020,
fc:350020@2026-09, idx:PPI-C2611@2025-01/@2025-10, committee sentence, one 90-day sheet. P02 refs = fc:350011@2026-09,
idx:PPI-C241@2024-10/@2025-10, qn:20004698, qn:20004826 (no figure), no committee sentence, one 90-day sheet.

## Not fixed (deliberately) - decide with a live game
- **P07 responsive 0.91 / stubborn 0.86 (noidea 0.95 / 0.96):** the mined "mirror" flag for case:P07 triggers the 40%-of-gap
  step in round 2 (EUR 4.94 -> 5.23, past its floor EUR 5.00, so the sim agrees at our price). It is the SAME rule that took
  P02 to 0.85, and live P07 does mirror (0.6x), so cutting it would also cut P02. The sims' suppliers don't mirror. The flag
  never fires for hidden suppliers (their case ids are new); there only the phrase / fix 4 apply.
- **P04 broad types with a stop 0.6% above the floor (6 of 36 at 0.52):** that sim supplier holds its stop but agrees to ANY
  ask at its floor, so noidea.py's 9-round creep wins. No live supplier did that (live P04 refused 0.2% below its stop).
- P10 responsive 0.974 -> 0.967: rounding-level, same structure.

## Diff (git diff --no-index, originals -> cloud copies)
```diff
diff --git a/analysis/agent_variants/noidea_neel.py b/analysis/agent_variants/noidea_neel_cloud.py
index 397ea12..4fd9d71 100644
--- a/analysis/agent_variants/noidea_neel.py
+++ b/analysis/agent_variants/noidea_neel_cloud.py
@@ -41,20 +41,21 @@ log = logging.getLogger("arena")
 
 
 def _central():
-    """analysis/agent_variants/central.py - the team's shared learnings (loaded by path: this file is loaded by path)."""
+    """analysis/agent_variants/central_cloud.py (cloud copy of central.py) - the team's shared learnings (loaded by path: this file is loaded by path)."""
     import importlib.util
     import sys
-    if "noidea_central" in sys.modules:
-        return sys.modules["noidea_central"]
-    spec = importlib.util.spec_from_file_location("noidea_central", Path(__file__).with_name("central.py"))
+    if "noidea_central_cloud" in sys.modules:
+        return sys.modules["noidea_central_cloud"]
+    spec = importlib.util.spec_from_file_location("noidea_central_cloud", Path(__file__).with_name("central_cloud.py"))
     mod = importlib.util.module_from_spec(spec)
-    sys.modules["noidea_central"] = mod
+    sys.modules["noidea_central_cloud"] = mod
     spec.loader.exec_module(mod)
     return mod
 
 
 central = _central()
 
+ALT_BAND = 1.003  # cloud fix #3: alternative sheets within 0.3% of our best C
 PLANNED_ROUNDS = 8  # P07 live: ~25 s per round, so an 8-minute wave fits ~12-15; keep a margin
 MIN_GAIN_PTS = 1.0  # never pay more than ask - 1 pt unless it is the last word
 CLOSE_STEP = 0.0008  # near-close: ask for 0.08% below its standing cash value. Live P04 5f80eb75c793f352: 0.2% below
@@ -75,7 +76,7 @@ LIMIT_HIT = re.compile(r"(?i)maximum (flexibility|extension)|within (our|my) (de
 # is also behavioural: its price did not move between its last two replies (see decide)
 EDGE_PLUS = 0.0004  # edge sheet: its approval threshold + 0.04% (P03: 2.04% beats the house agent, 2.00% scores 0.919)
 FREEZE_CUT = 0.01  # escalation under a price freeze: also offer its own structure 1% lower
-CLOSE_GAP = 0.015  # ...and our last ask is within 1.5% of its standing value (live P04: 1.0%)
+CLOSE_GAP = 0.005  # cloud fix #5 (was 0.015): near-close only within 0.5% of its standing value; a stop 0.6% above its floor is still worth creeping to (live P04: 1.0% gap)
 # How far below the opening quote to anchor (src/eval/calibrate.py: best deal vs opening, practice cases)
 ANCHOR_DEPTH = {"rfq": 0.20, "bundling": 0.15, "raw_material": 0.22, "capacity": 0.14, "quality": 0.09}
 ANCHOR_DEPTH_BY_GOAL = {"stabilise": 0.035,  # 0.03 in v1.5; 0.035 best offline for P02/P03 (3 sims; 0.04+ worse)
@@ -180,6 +181,13 @@ class NoIdeaAgent:
             if (cal := central.calibrated(case["case_id"], sid)):
                 full_cost, rate = cal["full_cost"], cal["interest_rate"]
             est = {"standard": std, "interest_rate": rate, "usual_rate": rate if cal else 0.08, "full_cost": full_cost}
+            # cloud fix (REGRESSION_FIX.md #2, ported from noidea.py v2.16): a chargeback is cash out at the defect rate it
+            # REALLY runs (scorecard ppm), x2 for a cash-short supplier; without this the sheet search treats chargebacks
+            # as free, asks the EUR 500 maximum and the supplier prices it in (P11 floor-stop sim 0.99 -> 0.80)
+            real_ppm = next((c["figure"] for c in self.claims if c["kind"] == "scorecard_ppm" and c["supplier"] == sid
+                             and c.get("figure")), None)
+            if real_ppm and "chargeback_eur_per_complaint" in case["negotiable"]:
+                est["ppm"] = real_ppm * (2.0 if "cash_short" in motives else 1.0)
             ask_pct = (open_terms["unit_price"] / cur - 1) * 100 if cur and open_terms.get("unit_price") else 0.0
             self._opening_price = open_terms.get("unit_price")
             self.sup[sid] = {"dossier": d, "std": std, "est": est, "justified": justified, "cur": cur, "calibrated": bool(cal),
@@ -352,7 +360,9 @@ class NoIdeaAgent:
         out = []
         # the supplier may pick ANY sheet we send: only offer ones we'd be glad to have accepted
         # (offline eval P10: a 12-month sheet at equal supplier value cost us +33% and got picked)
-        band = ranked[0][0] * 1.01 if ranked else 0
+        # cloud fix (REGRESSION_FIX.md #3): alternatives within 0.3% of our best C, not 1%. With chargebacks priced at the
+        # real defect rate, P11 filled slot 2 with 800 ppm at the same price: same value to it, +EUR 4.7k to us (0.98 -> 0.93)
+        band = ranked[0][0] * ALT_BAND if ranked else 0
         for c, t in ranked:  # 3 genuinely different options: same-cost duplicates waste a slot
             if c > band:
                 break
@@ -413,7 +423,13 @@ class NoIdeaAgent:
         step = min(scheduled - hist[-1], max(theirs, (limit - anchor) / (2 * PLANNED_ROUNDS)))
         # central: a mirroring supplier answers our step with its own - step a share of the remaining gap, but stay a
         # near-close below its standing value (the deal is its price; our ask only has to pull it down)
-        if sv and (central.mirror_supplier(case["case_id"]) or central.MIRROR.search(latest(events).get("body") or "")):
+        # cloud fix (REGRESSION_FIX.md #4): keep stepping big only while it answers in kind. From our 3rd ask on, if its
+        # last step was < 0.3x our last step (in value), it is not mirroring here: back to the schedule. Round 2 (the P02
+        # recipe) is unchanged; a non-mirroring supplier now costs at most one big step.
+        answered = True
+        if len(hist) >= 2 and len(sv) >= 2 and hist[-1] - hist[-2] > 1e-9:
+            answered = (sv[-2] - sv[-1]) >= 0.3 * (hist[-1] - hist[-2])
+        if sv and answered and (central.mirror_supplier(case["case_id"]) or central.MIRROR.search(latest(events).get("body") or "")):
             gap = sv[-1] - hist[-1]
             step = max(step, central.MIRROR_SHARE * gap)
             hist.append(min(limit, hist[-1] + max(0.0, min(step, gap - sv[-1] * CLOSE_STEP))))
@@ -429,6 +445,18 @@ class NoIdeaAgent:
         live = [s for s in live_threads(threads) if s in self.sup]
         # talk to the supplier whose thread is furthest behind (RFQ round-robin)
         sid = min(live, key=lambda s: sum(m.get("from") == "buyer" for m in threads[s]))
+        # cloud fix (REGRESSION_FIX.md #1, ported from noidea.py v2.9): in an RFQ a bidder that says agreed / final_offer
+        # is handled first, the cheapest of them - not whoever's turn it is (live P05 f8604d43d3fbf92f accepted the
+        # dearest bid; floor-stop sim P05 0.76 -> 0.00: an agreed bidder was never answered)
+        if len(live) > 1:
+            closing = [x for x in live if latest(threads[x]).get("status") in ("agreed", "final_offer")]
+            if closing:
+                cs = {x: self.best_sheet(case, x, threads[x]) for x in live}
+                cost = {x: total_cost(case, cs[x][1], self.sup[x]["std"], self.sup[x]["est"]) if cs[x][0] else math.inf
+                        for x in live}
+                best = min(closing, key=lambda x: cost[x])
+                if cost[best] <= min(cost.values()) + 1:
+                    sid = best
         events, s = threads[sid], self.sup[sid]
         sheet_id, terms = self.best_sheet(case, sid, events)
         status = latest(events).get("status")
```
