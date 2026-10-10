"""Compare an agent variant with Dhruv's agent on every offline check we have. No arena sessions, no LLM.

    cd tacto/starter-kit && uv run python ../../analysis/tools/variant_check.py ../../analysis/agent_variants/noidea_neel.py

1. Dhruv's simulated supplier (src/eval/offline_eval.py), responsive r=0.30 and stubborn r=0.10, 9 probed cases.
2. The floor-stop supplier calibrated on the live P04 game (sim_floorstop.py), all 9 cases.
3. P04 stress test: 25 supplier settings near the live one, and 36 broad ones.
"""

import itertools
import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(ROOT / "src/eval"))
logging.disable(logging.CRITICAL)
import offline_eval as oe  # noqa: E402
from sim_floorstop import load_agent, run  # noqa: E402

CASES = ["P02", "P03", "P04", "P05", "P07", "P08", "P10", "P11", "P18"]


def main(variant):
    orig, mine = load_agent(None), load_agent(variant)
    cases = {c["case_id"][5:]: c for c in json.loads((ROOT / "datasets/cases_practice.json").read_text(encoding="utf-8"))}
    probes = {c: json.loads((ROOT / f"analysis/cases/openings/{c}.json").read_text(encoding="utf-8")) for c in CASES}
    tot = [0.0] * 6
    print("case | Dhruv sim responsive | Dhruv sim stubborn | floor-stop (live-calibrated)   [v1.5 -> variant]")
    for cid in CASES:
        pr, r = probes[cid], probes[cid]["result"]
        a = [oe.simulate(A, cases[cid], pr["threads"], r["c_open"], r["c_best"], rr)[0] for A in (orig, mine) for rr in (0.3, 0.1)]
        f = [run(A, cases[cid], pr["threads"], r["c_open"], r["c_best"])[0] for A in (orig, mine)]
        for i, v in enumerate(a + f):
            tot[i] += v
        flag = " <-- worse" if a[2] < a[0] - 0.005 or a[3] < a[1] - 0.005 or f[1] < f[0] - 0.005 else ""
        print(f"{cid}  | {a[0]:.2f} -> {a[2]:.2f} | {a[1]:.2f} -> {a[3]:.2f} | {f[0]:.2f} -> {f[1]:.2f}{flag}")
    n = len(CASES)
    print(f"MEAN | {tot[0]/n:.3f} -> {tot[2]/n:.3f} | {tot[1]/n:.3f} -> {tot[3]/n:.3f} | {tot[4]/n:.3f} -> {tot[5]/n:.3f}")
    pr, r = probes["P04"], probes["P04"]["result"]
    go = lambda A, **kw: run(A, cases["P04"], pr["threads"], r["c_open"], r["c_best"], **kw)[0]  # noqa: E731
    near = list(itertools.product([0.4, 0.5, 0.54, 0.6, 0.7], [0.0010, 0.00125, 0.0015, 0.00175, 0.002], [1]))
    wide = list(itertools.product([0.3, 0.54, 0.8], [0.0005, 0.0015, 0.003, 0.006], [0, 1, 2]))
    for name, g in (("near the live supplier", near), ("36 broad supplier types", wide)):
        b = [go(orig, r=x, markup=y, patience=z) for x, y, z in g]
        m = [go(mine, r=x, markup=y, patience=z) for x, y, z in g]
        print(f"P04 {name}: v1.5 mean {sum(b)/len(b):.3f}, >=0.93 in {sum(v >= 0.93 for v in b)}/{len(g)}  ->  "
              f"variant mean {sum(m)/len(m):.3f}, >=0.93 in {sum(v >= 0.93 for v in m)}/{len(g)}, min {min(m):.2f}, "
              f"worse in {sum(x < y - 1e-9 for x, y in zip(m, b))}")
    print(f"P04 live-calibrated: v1.5 {go(orig):.2f} (live was 0.86) -> variant {go(mine):.2f}")


if __name__ == "__main__":
    main(sys.argv[1])
