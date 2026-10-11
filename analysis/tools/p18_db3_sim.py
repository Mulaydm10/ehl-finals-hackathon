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
    def __init__(self, soft, R, c3): self.soft, self.R, self.c3, self.k = soft, R, c3, 0
    def c(self, t):
        db = float((t.get("index_clause") or {}).get("deadband_pct") or 0)
        return 0.10 if db >= 5 else self.c3 if db >= 3 else 0.0
    def reply(self, sheets):
        self.k += 1; o = sheets[0]
        mk = lambda p, t: {"unit_price": round(p, 2), "payment_days": t["payment_days"], "contract_months": 24, "index_clause": t.get("index_clause") or CL[0]}
        if self.k == 1: return "open", [mk(5.20, {"payment_days": 30}), mk(5.30, {"payment_days": 30, "index_clause": CL[5]})]
        if any(t["unit_price"] - self.c(t) >= self.R - 1e-9 for t in sheets) and self.k >= 3:
            return "agreed", [max(sheets, key=lambda t: t["unit_price"] - self.c(t))]
        lad = {2: 5.00 if self.soft else 5.10}.get(self.k, 5.00)
        return ("final_offer" if self.k >= 4 else "open"), [mk(lad + self.c(o), o)]
def play(A, sup, opening, log):
    ag, thread = A(None), [dict(opening)]
    for n in range(1, 10):
        msg = ag.decide(CASE, {SID: [dict(x) for x in thread]})["message"]
        if msg.get("action"):
            sh = next(x for x in thread[-1]["term_sheets"] if x["term_sheet_id"] == msg["action"]["term_sheet_id"])
            log.append("US accept " + pcc.lab(sh["terms"])); return pcc.score(sh["terms"]), pcc.lab(sh["terms"])
        ours = [complete_offer(CASE, x["terms"]) for x in msg["term_sheets"]]
        log.append("US " + " | ".join(pcc.lab(o) for o in ours) + "   :: " + msg["body"].replace("\n", " / ")[:420])
        if thread[-1].get("status") == "final_offer": return 0.0, "pushed after final"
        status, sheets = sup.reply(ours)
        log.append(f"SUP {status} " + " | ".join(pcc.lab(t) for t in sheets))
        thread += [{**msg, "from": "buyer"}, {"from": "sales@70740", "status": status, "body": "Dear customer,", "claim_results": [],
                   "term_sheets": [{"term_sheet_id": f"offer:70740-{n}" + ("" if i == 0 else "-a"), "terms": t} for i, t in enumerate(sheets)]}]
    return 0.0, "ran out"
A = pcc.load(ROOT + "/analysis/agent_variants/noidea_p18_db3.py", "_db3sim").NoIdeaAgent
opening = next(m for m in pcc.games()[0]["threads"][SID]["messages"] if m.get("from") != "buyer")
for soft, R in ((False, 5.00), (True, 4.91), (True, 4.93)):
    for c3 in (0.0, 0.10):
        log = []; sc, deal = play(A, Sup(soft, R, c3), opening, log)
        print(f"soft={soft} R={R} c3={c3}: {sc:.4f} {deal}{'  BEATS 0.727' if sc > 0.7271 else ''}{'  BEATS RECORD' if sc > 0.75595 else ''}")
        if "-v" in sys.argv and c3 == 0.0: print("   " + "\n   ".join(log))
