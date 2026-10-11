"""Offline P10 arena (Parth, 2026-10-11): arena-sim's API with a Ravensteiner supplier fitted to the real games.

    cd tacto/starter-kit
    uv run python ../../tools/experiments/p10_offline.py ../../analysis/experiments/probes/P10_M.json [--mode template]
        [--seed 1] [--post-final hold|walk|accept|draw]

Runs tools/experiments/probe.py UNCHANGED against a local arena-sim server (127.0.0.1, its own key): the same messages,
branches and accept logic as live - no arena call, no quota, no live log (probe's logs go to a scratch folder).

The supplier (sup:70410) follows what 38 normal-mode P10 games showed (analysis/experiments/probes/P10_findings.md):
  round 1   32.00 for 23,400 / 24-36 m / lead 56, minus 0.30 if should-cost is taken and 0.20 if the price path is taken
            (31.50 with both, 31.70 should-cost only); index falls, forecast, OTD, ppm, news: marginal / shrugged.
            Lead 42 +2.30, lead 35 +3.50 (with an alternative at its 54 d). An ask under 28.50 = "unrealistic": final at once.
            Our ask >= its counter -> agreed at our ask (probe A, 31.56).
  round 2   final offer: step = min(0.8 x our move, k x gap left), k = 0.36 with a new taken fact else 0.27; a gap over
            4.45% or a move under 0.30 draws the token 0.10; 0.10 grid; the model's noise: one step less in 30% of draws.
  after     an ask at/above its final -> agreed; below: hidden acceptance floor (drawn), else walk / hold
  a final   (`--post-final`: no P10 data - cross-case small pushes: 4 holds, 1 move, 1 walk; single-supplier 6/11 walked).
  template  (`--mode template`, the 673ee890 window): round 1 = band end 31.00 + "Approve a further step?"; round 2 =
            the committee's approved step 0.30 plus 0.10 per new taken fact, final.
Score: the real yardsticks (C_open 1,932,492.18, C_best 1,328,926.89).
"""

import argparse
import json
import math
import random
import socket
import sys
import tempfile
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KIT = ROOT / "tacto" / "starter-kit"
sys.path[:0] = [str(KIT), str(ROOT / "tools" / "experiments")]
from arena_kit.cost import closing_terms, cost_breakdown, must_haves_ok, score, total_cost  # noqa: E402
from arena_kit.sim import Fail, Sim, create_app, structured  # noqa: E402

C_OPEN, C_BEST = 1932492.18, 1328926.89
OPENING = {"unit_price": 32.2, "lead_time_days": 54, "volume_per_year": 19890, "contract_months": 12}
OPENING_TEXT = ("Thank you for your enquiry. Please find our Angebot below. We offer a volume of 19890 pcs per year at a "
                "price of EUR 32.20 per unit. The requested contract term is 12 months, and our Lieferzeit is 54 days.")
STRONG = {"should_cost": 0.30, "price_history": 0.20}  # round-1 cuts of the facts it takes (31.50 with both)
LEAD_PREMIUM = {56: 0.0, 42: 2.30, 35: 3.50}


def grid(p, step=0.10):
    return round(round(p / step) * step, 2)


class P10Sim(Sim):
    def __init__(self, case, facts, mode="normal", seed=0, post_final="draw"):
        super().__init__({case["case_id"]: case}, facts, "sim", no_clock=False)
        self.mode, self.rng, self.post_final = mode, random.Random(seed), post_final
        self.noise = self.rng.random() < 0.30  # the model's sample: one grid step less in round 2
        u = self.rng.random()  # hidden acceptance floor under its final (no P10 data: assumed 15% of sessions)
        self.slack = self.rng.uniform(0.005, 0.018) if u < 0.15 else 0.0

    # -- claims: group the cited ids into the arena's claim kinds, max 3 per e-mail, one per kind ------------
    def _claims(self, s, msg):
        ids = list(dict.fromkeys((msg.get("refs") or []) + __import__("re").findall(
            r"\b(?:idx|quote|offer|sc|qn|po|cost|fc|news|doc|ctr):[\w.:@#/-]*\w", msg.get("body") or "")))
        kinds = {}
        for ref in ids:
            pre = ref.split(":", 1)[0]
            kind = {"po": "price_history", "cost": "should_cost", "fc": "volume_change", "news": "news",
                    "sc": "delivery_record", "qn": "quality_record", "quote": "rival_quote", "offer": "rival_quote"
                    }.get(pre)
            if pre == "idx":
                kind = "index_change:" + ref.split(":", 1)[1].split("@")[0]
            if kind:
                kinds.setdefault(kind, []).append(ref)
        out = []
        for kind, refs in list(kinds.items())[:3]:
            known = all(r in self.facts for r in refs)
            dup = kind in s["used"]
            out.append((kind, "contradicted" if not known else "duplicate" if dup else "verified"))
            if known:
                s["used"].add(kind)
        return out

    def _taken(self, kind):
        return kind in STRONG or kind.startswith("index_change")  # index falls are taken but marginal

    # -- the supplier ----------------------------------------------------------------------------------------
    def _answer(self, s, th, msg, sheets):
        claims = self._claims(s, msg)
        results = [{"index": i, "result": r} for i, (_, r) in enumerate(claims)]
        new_taken = [k for k, r in claims if r == "verified" and self._taken(k)]
        reasons = [f"We checked the {k.split(':')[0].replace('_', ' ')} data you cited; "
                   + ("it holds and we took it into account." if self._taken(k) else
                      "it holds, but it does not change our calculation.") for k, r in claims if r == "verified"]
        best = max(sheets, key=lambda t: t["unit_price"]) if sheets else None
        st = th.setdefault("p10", {"taken": set(), "ask": None, "c1": None, "final": None})
        st["taken"] |= set(new_taken)
        r = th["round"]

        def reply(status, terms, extra, files=("quote.pdf",)):
            m = self._mail(s, th, status, terms, " ".join(reasons + extra), list(files))
            m["claim_results"] = results
            s["trace"].append({"round": r, "actor": f"sup:{th['key']}", "move": structured(m, r),
                               "reasons": reasons + extra})
            return m

        if best is None:  # no term sheet: P10 goes final at its standing price (1e65e7ad, 26336719)
            return reply("final_offer", th["stated"], ["Without movement from your side we cannot move either."])
        terms = {k: best[k] for k in ("unit_price", "lead_time_days", "volume_per_year", "contract_months")}
        ask = best["unit_price"]

        if th["status"] == "final_offer":  # a message after its final
            fin = st["final"]
            if ask >= fin - 1e-9:
                return reply("agreed", terms, ["We accept the terms as outlined in your term sheet."])
            floor = round(fin * (1 - self.slack), 2)
            mode = self.post_final
            if mode == "draw":
                mode = "accept" if ask >= floor and self.slack else self.rng.choices(["hold", "walk"], [0.75, 0.25])[0]
            if mode == "accept" and ask >= round(fin * 0.98, 2):  # forced: the 2%-authority supplier accepts within 2%
                return reply("agreed", terms, ["Within my own authority I can confirm this."])
            if mode == "draw" and ask >= floor and self.slack:
                return reply("agreed", terms, ["Within my own authority I can confirm this."])
            if mode == "walk" or (fin - ask) / fin > 0.04:
                th["closed"] = "walked_away"
                return reply("walked_away", th["stated"], ["We end our negotiation here."], files=())
            return reply("final_offer", th["stated"], ["Our final offer stands."])

        lead = terms["lead_time_days"]
        base = 32.00 + LEAD_PREMIUM.get(lead, 0.0) + (0.20 if terms["volume_per_year"] < 23400 else 0.0) \
            + (0.20 if terms["contract_months"] < 24 else 0.0)
        if r == 1:
            if self.mode == "template":
                counter = 31.00 + LEAD_PREMIUM.get(lead, 0.0)
                extra = ["We value our cooperation and have made a step towards you.",
                         "Any further step needs approval from our management."]
                s.setdefault("backoffice", []).append("Segment Manager -> Pricing Committee: Approve a further step?")
            else:
                counter = grid(base - sum(STRONG[k] for k in st["taken"] if k in STRONG))
                extra = ["We acknowledge the increased volume and extended contract term, which permit a price adjustment."]
            st["c1"] = counter
            if ask >= counter:
                st["ask"] = ask
                return reply("agreed", terms, ["We accept your proposed terms."])
            if ask < 28.50:  # unrealistic anchor: final at once at its counter (27.38 games: 31.70 / 31.90 / 32.00)
                st["final"] = counter
                return reply("final_offer", {**terms, "unit_price": st["final"]}, ["Your target price is unrealistic."])
            st["ask"] = ask
            return reply("open", {**terms, "unit_price": counter}, extra)

        # round 2 (and any later open round): its final
        c1, prev = th["stated"]["unit_price"], st["ask"] or ask
        move, gap = ask - prev, c1 - ask
        if self.mode == "template":
            step = 0.30 + 0.10 * len(new_taken)
            extra = ["Our management has approved a further step."]
        else:
            k = 0.36 if new_taken else 0.27
            step = 0.10 if (gap / c1 > 0.0445 or move < 0.30) else min(0.8 * move, k * gap)
            if self.noise and step > 0.15:
                step -= 0.10
            extra = ["In exchange for this longer commitment, we revise our price."]
        price = max(grid(c1 - step), round(ask, 2))
        st["ask"] = ask
        if ask >= price - 1e-9:
            return reply("agreed", terms, ["We accept the terms as outlined in your term sheet."])
        st["final"] = price
        return reply("final_offer", {**terms, "unit_price": price},
                     extra + ["This is our final offer (letztes Angebot). Please decide."])

    def open(self, team, case_id):
        out = super().open(team, case_id)
        s = self.sessions[out["session_id"]]
        sup, th = next(iter(s["threads"].items()))
        standard = {k: v for k, v in OPENING.items() if k != "unit_price"}
        standard.update(ppm_commitment=300, chargeback_eur_per_complaint=0.0)  # its quote PDF's standard terms
        th.update(opening=OPENING["unit_price"], standard=standard, messages=[], n=0)
        self._mail(s, th, "open", dict(OPENING), OPENING_TEXT, ["quote.pdf"])
        out["threads"] = {sup: list(th["messages"])}
        out["opening"] = {sup: structured(th["messages"][0], 0)}
        return out

    def _end(self, s, reason, sup):
        super()._end(s, reason, sup)
        r = s["result"]
        r["c_open"], r["c_best"] = C_OPEN, C_BEST
        r["score"] = score(C_OPEN, r["c_deal"], C_BEST) if r.get("deal") and r.get("must_haves_ok") else 0.0


def free_port():
    with socket.socket() as so:
        so.bind(("127.0.0.1", 0))
        return so.getsockname()[1]


def run(design, mode="normal", seed=0, post_final="draw", quiet=False):
    import httpx
    import uvicorn

    import probe

    case = next(c for c in json.loads((ROOT / "datasets" / "cases_practice.json").read_text(encoding="utf-8"))
                if c["case_id"] == "case:P10")
    facts = json.loads((ROOT / "tacto" / "data" / "facts.json").read_text(encoding="utf-8"))
    sim = P10Sim(case, facts, mode, seed, post_final)
    port = free_port()
    server = uvicorn.Server(uvicorn.Config(create_app(sim), host="127.0.0.1", port=port, log_level="warning"))
    th = threading.Thread(target=server.run, daemon=True)
    th.start()
    while not server.started:
        time.sleep(0.05)
    base = f"http://127.0.0.1:{port}"
    key = httpx.post(f"{base}/v1/register", json={"event_code": "sim", "team_name": f"offline{seed}"}).json()["api_key"]

    from arena_kit.client import ArenaClient

    scratch = Path(tempfile.mkdtemp(prefix="p10_offline_"))
    (scratch / "notes").mkdir()
    (scratch / "analysis" / "experiments" / "probes").mkdir(parents=True)
    probe.ROOT = scratch  # probe's quota_log / results.jsonl go to the scratch folder, never the live logs
    probe.load_env = lambda *a, **k: None
    probe.ArenaClient = lambda *a, **k: ArenaClient(base_url=base, api_key=key)
    probe.run_plan.archive = lambda *a, **k: None
    probe.run_plan.quota_left = lambda *a, **k: "offline"
    probe.run_plan.git_commit = lambda *a, **k: "offline"
    assert base.startswith("http://127.0.0.1:"), "offline runs must never reach the arena"
    try:
        result = probe.main([str(design)])
    finally:
        server.should_exit = True
    return result, sim


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("design")
    ap.add_argument("--mode", default="normal", choices=["normal", "template"])
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--post-final", default="draw", choices=["draw", "hold", "walk", "accept"])
    a = ap.parse_args()
    result, sim = run(a.design, a.mode, a.seed, a.post_final)
    print(f"\nOFFLINE ({a.mode}, seed {a.seed}, post-final {a.post_final}, noise {sim.noise}, slack {sim.slack:.3f}): "
          f"score {result.get('score')} deal {result.get('deal')} price {(result.get('terms') or {}).get('unit_price')}")


if __name__ == "__main__":
    main()
