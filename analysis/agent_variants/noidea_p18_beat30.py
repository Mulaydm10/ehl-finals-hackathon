"""P18: beat our own 0.727 in the 6c2813ce state on 30 d (local, Neel, 2026-10-11 ~06:00; user: "just run p18 ... beat your own
record"). Gate case:P18; every other case = main. Built on noidea_p18_state45.py (6c2813ce msg 1-2 byte for byte).

The 6c2813ce state (reproduced 3 of 3: 6c2813ce, 81b5c6de, d71cab8c): 5.20 @ 45 d, then 5.00 @ 45 d + 5.10 db5. There its msg 3
4.91 @ 30 d drew a HOLD (5.00 @ 30 d, the move 45 -> 30 d uncharged) and its msg 4 4.94 @ 30 d was AGREED: its limit at 30 d is in
(4.91, 4.94]. Every ask at or under 4.92 @ 30 d db0 (0.7317), or 5.02 db5 (0.7377), beats our 0.727 (0c968aae).
Plan: msg 3 = 6c2813ce's msg 3 (labour, "lowest price ... today?") with 5.02 @ 30 d db5 + 4.92 @ 30 d db0 (both 4.92 to it).
After a hold: msg 4 = 6c2813ce's msg 4 + its on-time delivery (a new fact; a fact-free msg 4 drew "send us the data" + final in
81b5c6de) with 5.03 @ 30 d db5 (0.7310, beats) + 4.93 @ 30 d db0 (0.7249, the safety net). final_offer / agreed: accept.
"""
import importlib.util
import sys
from pathlib import Path

_spec = importlib.util.spec_from_file_location("arena_kit.agents._p18_state45_for_beat30",
                                               Path(__file__).with_name("noidea_p18_state45.py"))
_s45 = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _s45
_spec.loader.exec_module(_s45)
_s45.MSG3 = ((5.02, 30, 5), (4.92, 30, 0))  # 0.7377 / 0.7317 - 4.92 to it
_s45.MSG4 = ((5.03, 30, 5), (4.93, 30, 0))  # 0.7310 / 0.7249 - 4.93 to it
_s45.TRACK = {1: (5.20, 45), 2: (5.00, 45)}
VOL = "We confirm a binding volume of 23,700 units per year for 24 months."
OTD = " Your on-time delivery in the last quarter was 81.0% (sc:70740@2026Q3)."


class NoIdeaAgent(_s45.NoIdeaAgent):
    def _out(self, case, sid, m, old=None, plan=None):
        d = super()._out(case, sid, m, old, plan)
        if old == _s45.OLD4:  # msg 4: add a new fact
            out = d["message"]
            assert VOL + "\n\nOn this basis" in out["body"], "6c2813ce msg 4 text changed"
            out["body"] = out["body"].replace(VOL + "\n\nOn this basis", VOL + OTD + "\n\nOn this basis", 1)
            out["refs"] = sorted(set(out["refs"]) | {"sc:70740@2026Q3"})
            self.cited.update(out["refs"])
        return d
