import sys, importlib.util, logging
from pathlib import Path
ROOT = str(Path(__file__).resolve().parents[2]).replace("\\", "/")
sys.path.insert(0, ROOT + "/tacto/starter-kit")
spec = importlib.util.spec_from_file_location("pcc", ROOT + "/analysis/tools/p18_cross_check.py")
pcc = importlib.util.module_from_spec(spec); spec.loader.exec_module(pcc)
logging.disable(logging.CRITICAL)
from arena_kit.cost import complete_offer
CASE, SID, CL = pcc.CASE, pcc.SID, pcc.CLAUSE

class Sup:
    """soft: round-2 primary 5.00 (+db5 alt 5.10), else 5.10; R = acceptance floor in its value terms;
    c3 = its price of db3; rate = its payment valuation per year (0 = ignores payment); counters charge 90 d +0.10."""
    def __init__(self, soft, R, c3, rate):
        self.soft, self.R, self.c3, self.rate, self.k = soft, R, c3, rate, 0
    def V(self, t):
        db = float((t.get("index_clause") or {}).get("deadband_pct") or 0)
        c = 0.10 if db >= 5 else self.c3 if db >= 3 else 0.0
        return t["unit_price"] - c - self.rate * (t["payment_days"] - 30) / 360 * t["unit_price"]
    def reply(self, sheets):
        self.k += 1
        mk = lambda p, d=30, db=0: {"unit_price": p, "payment_days": d, "contract_months": 24, "index_clause": CL[db]}
        if self.k == 1:
            return "open", [mk(5.20), mk(5.30, 30, 5)]
        if self.k == 2:
            d = sheets[0]["payment_days"]; ch = 0.10 if d >= 60 else 0.0
            return ("open", [mk(round(5.00 + ch, 2), d), mk(round(5.10 + ch, 2), d, 5)]) if self.soft else ("open", [mk(round(5.10 + ch, 2), d)])
        ok = [t for t in sheets if self.V(t) >= self.R - 1e-9]
        if ok:
            return "agreed", [max(ok, key=self.V)]
        floor = 5.00 if self.soft or self.k >= 3 else 5.10
        return ("final_offer" if self.k >= 4 else "open"), [mk(floor)]

def same(a, b):
    return abs(a["unit_price"] - b["unit_price"]) < 1e-9 and a.get("payment_days") == b.get("payment_days") and \
        (a.get("index_clause") or {}).get("deadband_pct") == (b.get("index_clause") or {}).get("deadband_pct")

def play(Agent, sup, opening, log=None):
    ag, thread = Agent(None), [dict(opening)]
    for n in range(1, 10):
        msg = ag.decide(CASE, {SID: [dict(x) for x in thread]})["message"]
        if msg.get("action"):
            sh = next(x for x in thread[-1]["term_sheets"] if x["term_sheet_id"] == msg["action"]["term_sheet_id"])
            if log is not None: log.append("US accept " + pcc.lab(sh["terms"]))
            return pcc.score(sh["terms"]), pcc.lab(sh["terms"])
        ours = [complete_offer(CASE, x["terms"]) for x in msg["term_sheets"]]
        if log is not None: log.append("US " + " | ".join(pcc.lab(o) for o in ours)); log.append("   " + msg["body"].replace("\n", " / ")[:700])
        last = thread[-1]
        if last.get("status") == "final_offer":
            if len(ours) == 1 and any(same(ours[0], x["terms"]) for x in last["term_sheets"]):
                status, sheets = "agreed", [ours[0]]
            else:
                return 0.0, "pushed after final"
        else:
            status, sheets = sup.reply(ours)
        if log is not None: log.append(f"SUP {status} " + " | ".join(pcc.lab(t) for t in sheets))
        thread += [{**msg, "from": "buyer"}, {"from": "sales@70740", "status": status, "body": "Dear customer,", "claim_results": [],
                   "term_sheets": [{"term_sheet_id": f"offer:70740-{n}" + ("" if i == 0 else "-a"), "terms": t} for i, t in enumerate(sheets)]}]
    return 0.0, "ran out"

A = pcc.load(ROOT + "/analysis/agent_variants/noidea_p18_soft.py", "_soft_sim").NoIdeaAgent
opening = next(m for m in pcc.games()[0]["threads"][SID]["messages"] if m.get("from") != "buyer")
if "-v" in sys.argv:
    for soft, R in ((True, 4.93), (False, 5.00)):
        log = []
        print("=====", "SOFT R=4.93 c3=0 rate=0.08" if soft else "NORMAL", play(A, Sup(soft, R, 0.0, 0.08), opening, log))
        print("\n".join(log))
    sys.exit()
print(f"{'soft':5} {'R':>5} {'c3':>6} {'rate':>5}  score  deal")
for soft in (True, False):
    for R in ((4.86, 4.88, 4.89, 4.90, 4.92, 4.94, 4.96) if soft else (5.00,)):
        for c3 in (0.0, 0.05, 0.0675, 0.10):
            for rate in (0.0, 0.08):
                sc, deal = play(A, Sup(soft, R, c3, rate), opening)
                print(f"{str(soft):5} {R:>5.2f} {c3:>6.4f} {rate:>5.2f}  {sc:.4f} {deal}{'  BEAT' if sc > 0.75595 else ''}")
