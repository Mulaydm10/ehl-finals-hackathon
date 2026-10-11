"""P18: beat Codacabana's 0.756 (local, Neel, 2026-10-11 ~06:15; user: "read the highest score holder's deal and just make a
better deal than them. run offline 2 times and then run on the arena"). Gate case:P18; every other case = main.

The record holder's deal (P18_lever.md 1, live feed 2026-10-10T22:58:07Z): Codacabana EUR 4.90 @ 45 d, AS-14404 clause db0, 24 m
(C 240,350.39, 0.75595), normal mode. They play 45 d throughout (their other P18 deal: 5.20 @ 45 d db5). Werdenfels values that
deal at 4.90 db0. A better deal at the same value to it: **5.00 @ 45 d db5 (0.7618)**, it prices db5 at exactly +0.10 (15 pairs);
or **4.89 @ 45 d db0 (0.7627)**. The term space is only price x clause (none/db0/db3/db5) x days x months (24 = 36 m in C), so
there is no other structure that beats it at an equal or better value to Werdenfels.

What is new vs noidea_p18_open45 (0.621, 2493f26f): round 1 is no longer a draw. msg 1 = 6c2813ce's msg 1 byte for byte, which
drew 5.20 @ 45 d in 4 of 4 sessions (6c2813ce, 81b5c6de, d71cab8c, aaf4f9c6). msg 2 is open45's NEW msg 2
(6c2813ce's paragraph + forecast + the 5% deadband request, 4.84 @ 45 d db0), so round 2 and the conversation's limit are a fresh
draw from the 5.20 state (5.00 at round 2 in about 1 of 5 from 5.20; 6c2813ce's own msg 2 leads to a known limit > 4.94 @ 45 d).
msgs 3-4 = open45: the record sheets, then hold them if it cut under 5.00, else 5.02 db5 / 4.92 db0 (0.7486 / 0.7424 > our 0.727).
"""
import importlib.util
import logging
import sys
from pathlib import Path

from arena_kit.play import latest

_spec = importlib.util.spec_from_file_location("arena_kit.agents._p18_open45_for_coda",
                                               Path(__file__).with_name("noidea_p18_open45.py"))
_o45 = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _o45
_spec.loader.exec_module(_o45)
_s45 = _o45._s45
RECORD = _o45.RECORD

log = logging.getLogger("arena")


class NoIdeaAgent(_o45.NoIdeaAgent):
    def _decide(self, case, threads):
        if case["case_id"] in _s45._soft._cross.P18_CASES:
            if case["case_id"] != self.case_id:
                self.prepare(case, threads)
            sid = next((x for x in case["suppliers"] if x in self.sup), None)
            events = threads.get(sid) or []
            k = sum(m.get("from") == "buyer" and bool(m.get("term_sheets")) for m in events)
            if events and k == 0 and latest(events).get("status") == "open":
                if self._msgs is None:
                    _s45.NoIdeaAgent._msgs = _s45._src()
                log.info("%s P18 coda msg 1: 6c2813ce verbatim (4.77 @ 45 d, no clause)", sid)
                return self._out(case, sid, self._msgs[0])
        return super()._decide(case, threads)
