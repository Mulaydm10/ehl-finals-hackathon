import sys, importlib.util, logging
from pathlib import Path
ROOT = str(Path(__file__).resolve().parents[2]).replace("\\", "/")
sys.path.insert(0, ROOT + "/tacto/starter-kit")
spec = importlib.util.spec_from_file_location("pcc", ROOT + "/analysis/tools/p18_cross_check.py")
pcc = importlib.util.module_from_spec(spec); spec.loader.exec_module(pcc)
logging.disable(logging.CRITICAL)
from arena_kit.cost import complete_offer
CASE, SID = pcc.CASE, pcc.SID

class W2(pcc.Werdenfels):
    def __init__(self, *a, alt="a", **kw):
        super().__init__(*a, **kw); self.alt = alt
    def reply2(self, sheets):
        status, t = self.reply(sheets[0])
        if status != "agreed" and len(sheets) > 1 and self.alt:
            o = sheets[1]
            if self.alt == "a":
                alt = {**t, "unit_price": round(t["unit_price"] - 0.10, 2), "payment_days": o["payment_days"]}
            else:
                alt = {**t, "payment_days": o["payment_days"], "index_clause": pcc.CLAUSE[5]}
            return status, [t, alt]
        return status, [t]

def same(a, b):
    return abs(a["unit_price"] - b["unit_price"]) < 1e-9 and a.get("payment_days") == b.get("payment_days") and \
        abs(pcc.eq0(a) - pcc.eq0(b)) < 1e-9

def play(Agent, sup, opening):
    ag, thread, log = Agent(None), [dict(opening)], []
    for n in range(1, 10):
        msg = ag.decide(CASE, {SID: [dict(x) for x in thread]})["message"]
        if msg.get("action"):
            if msg["action"]["type"] != "accept":
                return 0.0, msg["action"]["type"], log
            sh = next(x for x in thread[-1]["term_sheets"] if x["term_sheet_id"] == msg["action"]["term_sheet_id"])
            log.append("US accept " + pcc.lab(sh["terms"]))
            return pcc.score(sh["terms"]), pcc.lab(sh["terms"]), log
        ours = [complete_offer(CASE, x["terms"]) for x in msg["term_sheets"]]
        log.append("US " + " | ".join(pcc.lab(o) for o in ours))
        last = thread[-1]
        own = [x["terms"] for x in last.get("term_sheets") or []]
        if len(ours) == 1 and any(same(ours[0], o) for o in own[1:]):
            status, sheets = "agreed", [ours[0]]          # its own alternative proposed back
        elif last.get("status") == "final_offer":
            return 0.0, "pushed after final_offer", log
        else:
            status, sheets = sup.reply2(ours)
        log.append(f"SUP {status} " + " | ".join(pcc.lab(t) for t in sheets))
        thread += [{**msg, "from": "buyer"}, {"from": "sales@70740", "status": status, "body": "Dear customer,",
                   "claim_results": [], "term_sheets": [{"term_sheet_id": f"offer:70740-{n}" + ("" if i == 0 else "-a"),
                                                          "terms": t} for i, t in enumerate(sheets)]}]
    return 0.0, "ran out", log

cross = pcc.load(ROOT + "/analysis/agent_variants/noidea_p18_cross.py", "_c1").NoIdeaAgent
harv = pcc.load(ROOT + "/analysis/agent_variants/noidea_p18_harvest.py", "_h1").NoIdeaAgent
opening = next(m for m in pcc.games()[0]["threads"][SID]["messages"] if m.get("from") != "buyer")
verbose = "-v" in sys.argv
print(f"{'charge':>6} {'P1':>5} {'cut2':>5} {'close':<12} {'alt':<4} {'cross':>7} {'harvest':>8}  harvest deal")
for pay in (0.0, 0.10, 0.20):
    for p1, cut2 in ((5.20, 0.10), (5.20, 0.20), (5.30, 0.10), (5.30, 0.20)):
        for close in ("step", "agree3", "hold_agree4"):
            for alt in ("a", "b", None):
                sc, endc, _ = play(cross, W2(p1, cut2, pay, close, alt=alt), opening)
                sh, endh, log = play(harv, W2(p1, cut2, pay, close, alt=alt), opening)
                flag = "  BEATS" if sh > pcc.RECORD else ""
                print(f"{pay:>6.2f} {p1:>5.2f} {cut2:>5.2f} {close:<12} {str(alt):<4} {sc:>7.4f} {sh:>8.4f}  {endh}{flag}")
                if verbose and pay == 0.0 and p1 == 5.20:
                    print("      " + " / ".join(log))
