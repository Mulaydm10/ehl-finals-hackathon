"""Scripted live probe of one single-supplier case: pre-written messages (numbers set in the design, no model),
fixed reactions, full archive. Costs ONE practice session per run. Built to test round-1 designs on P10.

    cd tacto/starter-kit
    uv run python ../../tools/experiments/probe.py ../../analysis/experiments/probes/P10_A.json [--dry-run]

Design (JSON):
  case        "P10"
  label       short name for the logs
  rounds      [{"body": str, "sheets": [{terms}], "refs": [ids]}]   round k's e-mail (k = 1, 2, ...)
  on_agreed   "accept" | "next"          next = send the next round instead of accepting (re-ask after agreed)
  on_open     "next" | "accept"          open = it countered without closing
  on_final    "accept" | "alternative" | "next"
              alternative = if one of its alternative sheets is cheaper for us, propose it back once
              ("We accept your alternative as you proposed it"), then accept; next = push on (it may walk)
When the rounds run out it accepts its standing (primary) sheet if the must-haves hold. The arena takes only
the primary sheet's id, so alternatives are always proposed back, never accepted by their '-a' id.
"""

import argparse
import base64
import datetime
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "tacto" / "starter-kit"), str(ROOT / "tools" / "experiments")]
import run_plan  # noqa: E402  (archive(), git_commit(), quota_left())

from arena_kit.cli import load_env  # noqa: E402
from arena_kit.client import ArenaClient  # noqa: E402
from arena_kit.cost import must_haves_ok, total_cost  # noqa: E402

ALT_BODY = "We accept your alternative as you proposed it; it is attached as a term sheet for your confirmation."


def terms_str(t, negotiable):
    return ", ".join(f"{k}={t.get(k)}" for k in negotiable)


def show_reply(reply, negotiable):
    sheets = reply.get("term_sheets") or []
    print(f"  <- {reply.get('status')}  "
          + " | ".join(f"{s.get('term_sheet_id')}: {terms_str(s['terms'], negotiable)}" for s in sheets))
    print(f"     claim results: {[c.get('result') for c in reply.get('claim_results') or []]}  "
          f"signals: {reply.get('signals')}")
    print("     " + (reply.get("body") or "").replace("\n", "\n     "))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("design")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    design = json.loads(Path(args.design).read_text(encoding="utf-8"))
    cid = f"case:{design['case']}"
    print(f"probe {design['label']} on {cid}: {len(design['rounds'])} round(s); "
          f"on_agreed={design.get('on_agreed', 'accept')} on_open={design.get('on_open', 'next')} "
          f"on_final={design.get('on_final', 'alternative')}")
    for k, r in enumerate(design["rounds"], 1):
        print(f"\n[round {k}] sheets {[s for s in r['sheets']]} refs {r.get('refs', [])}\n{r['body']}")
    if args.dry_run:
        return None

    kit = ROOT / "tacto" / "starter-kit"
    load_env(str(kit / ".env"))
    client = ArenaClient()
    case = next(c for c in client.cases("practice") if c["case_id"] == cid)
    neg = case["negotiable"]
    opened = client.open_session(cid)
    sid = opened["session_id"]
    sup = next(iter(opened["threads"]))
    first = next(m for m in opened["threads"][sup] if m.get("from") != "buyer")
    subject = "Re: " + (first.get("subject") or "your offer").replace("Quote from ", "").split(": ", 1)[-1]
    print(f"\nsession {sid}  supplier {sup}")
    show_reply(first, neg)

    def send(msg):
        print(f"\n  -> {[terms_str(s['terms'], neg) for s in msg.get('term_sheets') or []] or msg.get('action')}")
        reply = client.send_message(sid, sup, msg)
        if "result" in reply:
            return reply
        show_reply(reply, neg)
        return reply

    def accept(reply):
        primary = (reply.get("term_sheets") or [{}])[0]
        full = {**case.get("fixed_terms", {}), **(primary.get("terms") or {})}
        if not primary.get("term_sheet_id") or not must_haves_ok(case, full, {}):
            print("  standing sheet breaks a must-have or is missing: walking away")
            return client.send_message(sid, sup, {"action": {"type": "walk_away"}})
        return client.send_message(sid, sup, {"action": {"type": "accept", "term_sheet_id": primary["term_sheet_id"]}})

    def cost(t):
        return total_cost(case, {**case.get("fixed_terms", {}), "ppm_commitment": 300, **t})

    reply, result, ask = first, None, None
    for k, r in enumerate(design["rounds"], 1):
        sheets = [dict(t) for t in r.get("sheets", [])]
        if "step_frac" in r and ask is not None:  # move a share of the gap to its standing price
            theirs = ((reply.get("term_sheets") or [{}])[0].get("terms") or {}).get("unit_price")
            if theirs:
                ask = round(ask + r["step_frac"] * (theirs - ask), 2)
                for t in sheets:
                    t["unit_price"] = ask
        elif sheets:
            ask = sheets[0]["unit_price"]
        body = r["body"].replace("{price}", f"{ask:.2f}" if ask is not None else "")
        msg = {"subject": subject, "body": body, "term_sheets": [{"terms": t} for t in sheets],
               "refs": r.get("refs", [])}
        if r.get("attachments"):  # [{"name", "type": "csv"|"md"|"json", "text"}] - the arena reads md/csv/json
            msg["attachments"] = [{"name": a["name"], "type": a["type"],
                                   "content_b64": base64.b64encode(a["text"].encode("utf-8")).decode("ascii")}
                                  for a in r["attachments"]]
        reply = send(msg)
        if "result" in reply:
            result = reply["result"]
            break
        status, last = reply.get("status"), k == len(design["rounds"])
        if status == "agreed":
            if design.get("on_agreed", "accept") == "next" and not last:
                continue
            result = accept(reply).get("result")
            break
        if status == "final_offer":
            mode = design.get("on_final", "alternative")
            if mode == "next" and not last:
                continue
            sheets = reply.get("term_sheets") or []
            if mode == "alternative" and len(sheets) > 1:
                best = min(sheets[1:], key=lambda s: cost(s["terms"]))
                if cost(best["terms"]) < cost(sheets[0]["terms"]) - 1:
                    alt = {k2: best["terms"][k2] for k2 in neg}
                    reply = send({"subject": subject, "body": f"Dear Sir or Madam,\n\n{ALT_BODY}\n\nKind regards,\n"
                                  "Purchasing, Hollerau Pumpenwerke", "term_sheets": [{"terms": alt}], "refs": []})
                    if "result" in reply:
                        result = reply["result"]
                        break
            result = accept(reply).get("result")
            break
        if status == "open" and (design.get("on_open", "next") == "accept" or last):
            result = accept(reply).get("result")
            break
        if status in ("walked_away", "no_bid"):
            break
    if result is None:
        result = client.session(sid).get("result") or {}
    print(f"\nRESULT deal={result.get('deal')} score={result.get('score')} c_deal={result.get('c_deal')} "
          f"terms={terms_str(result.get('terms') or {}, neg)}")
    run_plan.archive(client, sid, cid)
    when = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    sc = result.get("score")
    with (ROOT / "notes" / "quota_log.md").open("a", encoding="utf-8") as f:
        f.write(f"| {when} | Parth | {design['case']} | probe {design['label']} (scripted, no model) | "
                f"{sc if sc is None else round(sc, 3)} ({terms_str(result.get('terms') or {}, neg)}) | {sid} |\n")
    out = ROOT / "analysis" / "experiments" / "probes" / "results.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"time": when, "label": design["label"], "case": design["case"], "session": sid,
                            "score": sc, "deal": result.get("deal"), "terms": result.get("terms"),
                            "commit": run_plan.git_commit()}, ensure_ascii=False) + "\n")
    print(f"quota left: {run_plan.quota_left(client)}")
    return result


if __name__ == "__main__":
    main()
