"""P04: our cost and the agent's supplier-value model for its real finals per payment term; what the agent believes."""
import json, sys, logging, glob
from pathlib import Path
ROOT = Path.home() / "Dhruv/ehl-finals-hackathon"
sys.path.insert(0, str(ROOT / "tacto/starter-kit"))
logging.disable(logging.CRITICAL)
from arena_kit.agents.noidea_rfq import NoIdeaAgent
from arena_kit.agents.noidea import supplier_value
from arena_kit.cost import total_cost, complete_offer
case = next(c for c in json.loads((ROOT / "datasets/cases_practice.json").read_text()) if c["case_id"] == "case:P04")
g = max((json.loads(Path(f).read_text()) for f in glob.glob(str(ROOT / "datasets/runs/*.json"))
         if json.loads(Path(f).read_text()).get("session", {}).get("case_id") == "case:P04"), key=lambda g: g["session"].get("created_at") or 0)
threads = {sid: th["messages"][:1] for sid, th in g["threads"].items()}
a = NoIdeaAgent(); a.prepare(case, threads)
sid = next(iter(a.sup)); s = a.sup[sid]
print("est:", {k: v for k, v in s["est"].items() if k != "standard"}, "std:", s["std"])
print("buyer:", {k: case["buyer"].get(k) for k in ("reference_payment_days", "cost_of_capital_pct", "wacc", "interest_rate") if k in case["buyer"]})
c_open, c_best = 198846.33, 196529.32
for p, d in [(4.86, 14), (4.88, 30), (4.89, 45), (4.91, 60), (4.94, 90), (4.85, 14), (4.87, 30), (4.88, 45), (4.90, 60), (4.93, 90)]:
    t = complete_offer(case, {**s["open_terms"], "unit_price": p, "payment_days": d, "contract_months": 36})
    C = total_cost(case, t, s["std"], s["est"])
    print(f"{p:.2f} @ {d:2d} d: C {C:,.2f} score {(c_open - C) / (c_open - c_best):.3f}  supplier_value(agent) {supplier_value(case, t, s['est']):,.2f}")
