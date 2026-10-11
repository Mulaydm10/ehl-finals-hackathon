"""Do SHORT later e-mails draw bigger steps? Per case, rounds 2+ (our priced e-mail -> its reply on the same structure):
the e-mail's length and whether it opens with a model-written paragraph, vs the supplier's cut (% of its price).
Normal-mode replies only (any model-written reason sentence); same number of verified facts compared."""
import json, glob, re, statistics, collections, sys
ENGINE = re.compile(r"^(We checked the |We value our cooperation|The contract term is reflected|Any further step needs|Our management has approved|"
                    r"Which volume can you|Our price reflects our costs|Our calculation is our property|Which figures is that based|"
                    r"Alternatively, with|A longer Zahlungsziel|.+ (rose|fell) … in twelve months|A Preisgleitklausel|Our price follows our main|"
                    r"Material accounts for about|Our margin and our limits|Our general terms and conditions|Without movement from your side|"
                    r"Our standard Zahlungsziel|Faster payment is welcome|We received a lot of material|We have already taken that|A binding higher volume)")
want = set(sys.argv[1:])
rows = collections.defaultdict(list)
for f in glob.glob("datasets/runs/*.json"):
    g = json.load(open(f))
    cid = (g.get("session") or {}).get("case_id") or ""
    if (want and cid.split(":")[-1] not in want) or len(g.get("threads") or {}) != 1:
        continue
    tr = ((g.get("detail") or {}).get("result") or {}).get("trace") or []
    last, nb = None, 0
    for i, t in enumerate(tr):
        mv = t["move"]
        if t["actor"] != "buyer":
            if (mv.get("terms") or {}).get("unit_price"):
                last = mv["terms"]
            continue
        if mv.get("type") != "message" or not mv.get("term_sheets"):
            continue
        nb += 1
        rep = next((x for x in tr[i + 1:] if x["actor"] != "buyer"), None)
        if nb < 2 or not rep or not last or not (rep["move"].get("terms") or {}).get("unit_price"):
            continue
        reasons = rep.get("reasons") or []
        if not reasons or all(ENGINE.match(r) for r in reasons):
            continue  # template / hold reply: not model mode
        new = rep["move"]["terms"]
        if any(new.get(k) != last.get(k) for k in new if k != "unit_price"):
            continue
        body = mv.get("body") or ""
        paras = [p for p in body.split("\n\n") if p.strip()]
        model_para = len(paras) >= 4  # Dear / model paragraph / our lines / propose / regards
        ver = sum(r.get("result") == "verified" for r in rep["move"].get("claim_results") or [])
        cut = 100 * (last["unit_price"] - new["unit_price"]) / last["unit_price"]
        rows[(cid, min(ver, 1), "long" if len(body) > 700 else "short")].append(cut)
for k in sorted(rows):
    xs = rows[k]
    print(f"{k[0]} facts={k[1]} {k[2]:5s} n={len(xs):3d} mean cut {statistics.mean(xs):.3f}%  median {statistics.median(xs):.3f}%")
