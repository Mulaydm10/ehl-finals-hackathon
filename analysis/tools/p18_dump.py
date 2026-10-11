"""P18: dump every recorded game turn by turn (our sheets, its sheets incl. alternatives, scores). Offline.
    cd tacto/starter-kit && .venv/Scripts/python.exe ../../analysis/tools/p18_dump.py [--alts]"""
import sys, importlib.util
from pathlib import Path
ROOT = str(Path(__file__).resolve().parents[2]).replace("\\", "/")
sys.path.insert(0, ROOT + "/analysis/tools")
spec = importlib.util.spec_from_file_location("pcc", ROOT + "/analysis/tools/p18_cross_check.py")
pcc = importlib.util.module_from_spec(spec); spec.loader.exec_module(pcc)
only_alts = "--alts" in sys.argv
for d in pcc.games():
    msgs = d["threads"][pcc.SID]["messages"]
    res = (d.get("detail") or {}).get("result") or {}
    deal = res.get("terms")
    has_alt = any(m.get("from") != "buyer" and len(m.get("term_sheets") or []) > 1 for m in msgs[1:])
    multi_buy = any(m.get("from") == "buyer" and len(m.get("term_sheets") or []) > 1 for m in msgs)
    if only_alts and not (has_alt or multi_buy):
        continue
    sid = d['session']['session_id']
    print(f"=== {sid} live {('%.4f' % pcc.score(deal)) if deal else 'no deal'} {pcc.lab(deal) if deal else ''}  end={d['session'].get('end_reason')}")
    for m in msgs[1:]:
        who = "US " if m.get("from") == "buyer" else "SUP"
        if m.get("action"):
            print(f"   {who} action {m['action']}")
            continue
        sheets = m.get("term_sheets") or []
        parts = []
        for x in sheets:
            t = x.get("terms", x)
            if t.get("unit_price") is None:
                parts.append("?"); continue
            parts.append(f"{pcc.lab(t)}/{t.get('contract_months')}m ({pcc.score(t):.3f})")
        st = m.get("status") or ""
        print(f"   {who} {st:12s} " + " | ".join(parts))
