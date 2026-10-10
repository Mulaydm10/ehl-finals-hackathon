"""Supplier memory: what every supplier did in ALL our archived games, per term structure (no quota).

    python3 src/eval/supplier_memory.py          # rebuild datasets/H_supplier_memory.json after each game

The agent reads it at the start of a game (NoIdeaAgent.prepare -> s["memory"]): the prices it AGREED to when we asked
(its real floor is at or below them), the asks it refused while holding, its final offers, the floors it named, and
which kinds of data it took or shrugged off. Rebuilt from datasets/runs/*.json, so it grows with every game - also
across the waves of a final if suppliers repeat.
"""
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "datasets" / "H_supplier_memory.json"
CHECKED = re.compile(r"(?i)we checked the (.+?) data you cited; it holds(,| and)(?: but)? (it does not change|we took it)")
NAMED = re.compile(r"(?i)(?:can give you|best we can do|absolute bottom line|bottom line|as low as we can go|lowest (?:price )?"
                   r"(?:we|i) can|meet you at)[^.€]{0,40}(?:€|eur\s?)\s?(\d+[.,]\d{2})|(?:€|eur\s?)\s?(\d+[.,]\d{2})[^.]{0,30}"
                   r"(?:is (?:really )?our (?:absolute )?(?:bottom line|final|best))")


def key(terms):
    return "|".join(f"{k}={terms[k]}" for k in sorted(terms) if k != "unit_price")


def main():
    mem = defaultdict(lambda: {"games": 0, "scores": [], "structures": defaultdict(lambda: {
        "agreed_to_our_ask": [], "refused_asks": [], "finals": [], "named_floors": []}), "took": defaultdict(int),
        "shrugged": defaultdict(int)})
    for f in sorted((ROOT / "datasets/runs").glob("*.json")):
        g = json.loads(f.read_text())
        if len(g.get("threads", {})) != 1:
            continue  # RFQs: several bidders, keep it simple
        sid, th = next(iter(g["threads"].items()))
        ms = th.get("messages") or []
        m = mem[sid]
        m["games"] += 1
        sc = ((g.get("detail") or {}).get("result") or {}).get("score")
        if sc is not None:
            m["scores"].append(round(sc, 3))
        last_ask, prev_std = None, None
        for x in ms:
            sheets = x.get("term_sheets") or []
            t = (sheets[0].get("terms") or {}) if sheets else {}
            if x.get("from") == "buyer":
                last_ask = t if t.get("unit_price") is not None else last_ask
                continue
            body = x.get("body") or ""
            for kind, _, verdict in CHECKED.findall(body):
                (m["took"] if verdict.startswith("we took") else m["shrugged"])[kind.lower()] += 1
            if t.get("unit_price") is None:
                continue
            st = m["structures"][key(t)]
            p = t["unit_price"]
            if x.get("status") == "agreed" and last_ask and abs(last_ask.get("unit_price", -1) - p) < 0.005 \
                    and key(last_ask) == key(t):
                st["agreed_to_our_ask"].append([p, prev_std])  # [price it agreed to, its standing before]
            elif last_ask and prev_std is not None and abs(p - prev_std) < 0.005 and key(last_ask) == key(t) \
                    and last_ask.get("unit_price", 1e9) < p:
                st["refused_asks"].append([last_ask["unit_price"], p])  # [our ask, the standing it held]
            if x.get("status") == "final_offer":
                st["finals"].append(p)
            for a, b in NAMED.findall(body):
                v = float((a or b).replace(",", "."))
                if abs(v - p) < 0.005:
                    st["named_floors"].append(v)
            prev_std = p
    out = {}
    for sid, m in mem.items():
        out[sid] = {"games": m["games"], "scores": m["scores"], "took": dict(m["took"]), "shrugged": dict(m["shrugged"]),
                    "structures": {k: {kk: sorted({tuple(x) if isinstance(x, list) else x for x in vv}) for kk, vv in v.items()}
                                   for k, v in m["structures"].items()
                                   if any(v.values())}}
    OUT.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print(f"{OUT.name}: {len(out)} suppliers")
    for sid in sorted(out):
        best = {k: v for k, v in out[sid]["structures"].items() if v["agreed_to_our_ask"] or v["named_floors"]}
        if best:
            print(" ", sid, out[sid]["games"], "games", json.dumps(best)[:300])


if __name__ == "__main__":
    main()
