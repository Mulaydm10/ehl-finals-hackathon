"""P18 cross check - offline, no arena, no LLM (complete=None -> template wording).

    cd tacto/starter-kit && uv run python ../../analysis/tools/p18_cross_check.py [--replay] [--scenarios]

--replay     feeds every recorded P18 game (datasets/runs) to analysis/agent_variants/noidea_p18_cross.py and prints, turn by turn,
             what it would send next to the live supplier messages (the live game diverges after our first different move).
--odds       weights the scenarios by how often each draw happened (P1_W, CUT2_W, SOFT_CLOSE_W) for 90 and 60 days.
--scenarios  plays the agent against a scripted Werdenfels built from the 40 recorded games (analysis/cases/P18_deep.md):
             first counter 5.10 / 5.20 / 5.30 on 30 d; round-2 cut 0.10 (normal) or 0.20 (soft draw); our payment change after
             round 1 free or priced (+0.10 / +0.20 on 90 d); round 3 cuts 0.10 when we step >= 0.05, else holds or agrees
             (the 0c968aae / a09d9536 closes); at our 4th message it goes final at its standing price unless the scenario agrees.
             Every deal is scored with the arena's cost model (reproduces all recorded P18 deals to the cent).
"""
import importlib.util
import json
import logging
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tacto/starter-kit"))
logging.disable(logging.CRITICAL)
from arena_kit.cost import complete_offer, total_cost  # noqa: E402

CASE = next(c for c in json.loads((ROOT / "datasets/cases_practice.json").read_text(encoding="utf-8"))
            if c["case_id"] == "case:P18")
STD = {"payment_days": 30, "contract_months": 12, "volume_per_year": 23700, "ppm_commitment": 70, "lead_time_days": 14,
       "incoterm": "DAP", "effective_date": "2027-01-01", "index_clause": None, "tooling_eur": 0}
EST = {"standard": STD, "interest_rate": 0.07, "full_cost": 4.5}
C_OPEN, C_BEST, RECORD = 295173.23, 222651.27, 0.75595
SID = "sup:70740"
CLAUSE = {db: {"series": "AS-14404", "material_share": 0.45, "deadband_pct": db, "base_month": "2026-08"} for db in (0, 3, 5)}


def score(t):
    return (C_OPEN - total_cost(CASE, complete_offer(CASE, t), STD, EST)) / (C_OPEN - C_BEST)


def load(path, name="_p18_cross_check"):
    spec = importlib.util.spec_from_file_location(f"arena_kit.agents.{name}", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def games():
    out = []
    for f in sorted((ROOT / "datasets/runs").glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        if (d.get("session") or {}).get("case_id") == "case:P18" and SID in (d.get("threads") or {}):
            out.append(d)
    return sorted(out, key=lambda d: d["session"].get("created_at") or 0)


def lab(t):
    ic = t.get("index_clause")
    return f"{t['unit_price']:.2f}@{t.get('payment_days')}d" + ("" if ic is None else f"/db{int(float(ic.get('deadband_pct') or 0))}")


def ask_of(msg):
    if msg.get("action"):
        return msg["action"]["type"]
    return " | ".join(lab(x.get("terms", x)) for x in msg.get("term_sheets") or []) + f"  refs {sorted(msg.get('refs') or [])[:3]}"


def replay(Agent):
    for d in games():
        msgs = d["threads"][SID]["messages"]
        res = (d.get("detail") or {}).get("result") or {}
        deal = res.get("terms")
        print(f"=== {d['session']['session_id']}  live {('%.4f' % score(deal)) if deal else 'no deal'}")
        ag = Agent(None)
        for i, m in enumerate(msgs):
            if m.get("from") != "buyer":
                continue
            try:
                out = ag.decide(CASE, {SID: [dict(x) for x in msgs[:i]]})["message"]
            except Exception as e:  # noqa: BLE001
                out = {"action": {"type": f"ERR {type(e).__name__}: {e}"}}
            live = m.get("action", {}).get("type") if m.get("action") else " | ".join(lab(x["terms"]) for x in m.get("term_sheets") or [])
            print(f"  turn {sum(x.get('from') == 'buyer' for x in msgs[:i]) + 1}: live {live:<28} cross {ask_of(out)}")


# ---- scripted Werdenfels -------------------------------------------------------------------------------------------------
def eq0(t):
    db = float((t.get("index_clause") or {}).get("deadband_pct") or 0)
    return t["unit_price"] - (0.10 if db >= 5 else 0.05 if db >= 3 else 0.0)


class Werdenfels:
    """p1: first counter on 30 d; cut2: round-2 cut; pay: extra price for 90 d after round 1 (0 = free); close: 'step' (round 3
    cuts 0.10 on a step >= 0.05, else holds; final at msg 4 = hold), 'agree3' (agrees at our 3rd ask within 0.10 of its offer,
    0c968aae), 'hold_agree4' (holds at msg 3, agrees at our 4th ask within 0.06, a09d9536)."""

    def __init__(self, p1=5.20, cut2=0.10, pay=0.0, close="step", pay60=None):
        self.p1, self.cut2, self.pay, self.close = p1, cut2, pay, close
        self.pay60 = pay / 2 if pay60 is None else pay60
        self.k, self.base, self.last_ask = 0, None, None

    def charge(self, days):
        return self.pay if days >= 90 else self.pay60 if days >= 60 else 0.0

    def reply(self, ours):
        """ours: our single sheet (terms). Returns (status, sheet terms)."""
        self.k += 1
        days, db = ours.get("payment_days"), float((ours.get("index_clause") or {}).get("deadband_pct") or 0)
        a = eq0(ours) if ours.get("index_clause") else ours["unit_price"]
        step = None if self.last_ask is None else round(a - self.last_ask, 4)
        self.last_ask = a
        if self.k == 1:
            self.base = self.p1
        elif self.k == 2:
            self.base = round(self.base - self.cut2, 2)
        elif self.k == 3:
            line = self.base + self.charge(days)  # what it asks on OUR payment term
            if self.close == "agree3" and a >= line - 0.10 + 0.0001 - 1e-9 and a < line:
                return "agreed", dict(ours)
            if self.close == "hold_agree4" or (step is not None and step < 0.05 - 1e-9):
                pass  # hold
            else:
                self.base = round(self.base - 0.10, 2)
        else:
            if self.close == "hold_agree4" and self.base + self.charge(days) - a <= 0.06 + 1e-9:
                return "agreed", dict(ours)
        price = round(self.base + (self.charge(days) if self.k >= 2 else 0.0) + (0.10 if db >= 5 else 0.05 if db >= 3 else 0.0), 2)
        terms = {"unit_price": price, "payment_days": days, "contract_months": ours.get("contract_months", 24),
                 "index_clause": ours.get("index_clause") or CLAUSE[0]}
        if a >= price - 1e-9:
            return "agreed", dict(ours)
        return ("final_offer" if self.k >= 4 else "open"), terms


def play(Agent, sup, opening):
    ag, thread = Agent(None), [dict(opening)]
    for n in range(1, 9):
        msg = ag.decide(CASE, {SID: [dict(x) for x in thread]})["message"]
        if msg.get("action"):
            if msg["action"]["type"] != "accept":
                return 0.0, msg["action"]["type"], n
            sh = next(x for x in thread[-1]["term_sheets"] if x["term_sheet_id"] == msg["action"]["term_sheet_id"])
            return score(sh["terms"]), lab(sh["terms"]), n
        ours = msg["term_sheets"][0]["terms"]
        if thread[-1].get("status") == "final_offer" and not any(
                abs(ours["unit_price"] - x["terms"]["unit_price"]) < 1e-9 and ours.get("payment_days") == x["terms"].get("payment_days")
                for x in thread[-1]["term_sheets"]):
            return 0.0, "pushed after final_offer", n
        status, t = sup.reply(complete_offer(CASE, ours))
        thread += [{**msg, "from": "buyer"},
                   {"from": "sales@70740", "status": status, "body": "Dear customer,", "claim_results": [],
                    "term_sheets": [{"term_sheet_id": f"offer:70740-{n}", "terms": t}]}]
    return 0.0, "ran out", n


def scenarios(Agent):
    opening = next(m for m in games()[0]["threads"][SID]["messages"] if m.get("from") != "buyer")
    rows = []
    for pay in (0.0, 0.10, 0.20):
        for p1, cut2 in ((5.20, 0.10), (5.20, 0.20), (5.30, 0.10), (5.30, 0.20), (5.10, 0.10)):
            for close in ("step", "agree3", "hold_agree4"):
                s, end, n = play(Agent, Werdenfels(p1, cut2, pay, close), opening)
                rows.append((pay, p1, cut2, close, s, end, n))
    print(f"{'90 d charge':>11} {'P1':>5} {'cut2':>5} {'close':<12} {'score':>7}  deal")
    for pay, p1, cut2, close, s, end, n in rows:
        print(f"{pay:>11.2f} {p1:>5.2f} {cut2:>5.2f} {close:<12} {s:>7.4f}  {end} ({n} msgs){'  BEATS' if s > RECORD else ''}")
    return rows


# how often each draw happened in the recorded games (P18_deep.md section 3)
P1_W = {5.20: 9 / 10, 5.30: 1 / 10}  # first counter after the 4.76 @ 30 d round 1 (10 games; the 5.10 came after a timeout)
CUT2_W = {5.20: {0.10: 0.8, 0.20: 0.2}, 5.30: {0.10: 0.55, 0.20: 0.45}, 5.10: {0.10: 1.0}}  # round-2 cut by first counter
SOFT_CLOSE_W = {"agree3": 0.3, "hold_agree4": 0.5, "step": 0.2}  # after a 5.00 round-2 counter: 0c968aae / a09d9536, 6c2813ce / unseen


def odds():
    opening = next(m for m in games()[0]["threads"][SID]["messages"] if m.get("from") != "buyer")
    print(f"{'pay':>4} {'late charge':>11} {'E[score]':>9} {'P(beat)':>8}")
    for pay in (90, 60):
        mod = load(ROOT / "analysis/agent_variants/noidea_p18_cross.py", f"_p18_cross_{pay}")
        mod.PAY = pay
        for charge in (0.0, 0.10, 0.20):
            e = pb = 0.0
            for p1, w1 in P1_W.items():
                for cut2, w2 in CUT2_W[p1].items():
                    soft = round(p1 - cut2, 2) <= 5.00
                    for close, w3 in (SOFT_CLOSE_W.items() if soft else (("step", 1.0),)):
                        sc, _, _ = play(mod.NoIdeaAgent, Werdenfels(p1, cut2, charge if pay == 90 else 0.0, close,
                                                                    pay60=charge / 2 if pay == 60 else None), opening)
                        w = w1 * w2 * w3
                        e += w * sc
                        pb += w * (sc > RECORD)
            print(f"{pay:>4} {charge:>11.2f} {e:>9.4f} {pb:>8.1%}")


if __name__ == "__main__":
    args = set(sys.argv[1:]) or {"--replay", "--scenarios", "--odds"}
    A = load(ROOT / "analysis/agent_variants/noidea_p18_cross.py").NoIdeaAgent
    if "--replay" in args:
        replay(A)
    if "--scenarios" in args:
        scenarios(A)
    if "--odds" in args:
        odds()
