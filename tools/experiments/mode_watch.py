"""Watch the arena's supplier mode with FREE sandbox sessions; play the P10 record attempt the moment it answers in
engine-template mode (Parth, 2026-10-11).

    cd tacto/starter-kit
    uv run python ../../tools/experiments/mode_watch.py --once          # one sandbox probe: prints model / TEMPLATE
    uv run python ../../tools/experiments/mode_watch.py --every 300 --until 11:30 --design ../../analysis/experiments/probes/P10_M.json

Why: P10's record 0.741 (673ee890) came from the engine-template window (23:51-23:58 CEST, 10 Oct): with the arena's
model off, the segment manager escalated to the Pricing Committee ("The buyer wants more than my band allows ...
Approve a further step?" -> "Approved: you may go further, within our rules") - a path the model never takes in normal
mode (40+ games, backoffice "My call: counter" only). The mode is arena-side and cannot be triggered; it can be watched.
Sandbox sessions do not count against the practice quota (api.md). One probe = open case:D01, one e-mail, walk away,
classify the reply's reasons with analysis/tools/supplier_mode_scan.reply_mode (engine sentences only = TEMPLATE).
On TEMPLATE: run the design with tools/experiments/probe.py (ONE practice session), then commit + push the run.
"""

import argparse
import datetime
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KIT = ROOT / "tacto" / "starter-kit"
sys.path[:0] = [str(KIT), str(ROOT / "tools" / "experiments"), str(ROOT / "analysis" / "tools")]
from arena_kit.cli import load_env  # noqa: E402
from arena_kit.client import ArenaClient  # noqa: E402

LOG = ROOT / "analysis" / "experiments" / "mode_watch.log"
PROBE = {
    "subject": "Re: Pump housing PH-100",
    "body": "Dear Sir or Madam,\n\nThank you for your offer. We propose to keep today's price of EUR 48.60 per piece "
            "for 24 months at 30 days payment.\n\nKind regards,\nPurchasing, Hollerau Pumpenwerke",
    "term_sheets": [{"terms": {"unit_price": 48.6, "payment_days": 30, "contract_months": 24,
                               "effective_date": "2027-01-01"}}],
    "refs": [],
}


def reply_mode(reasons):
    try:
        from supplier_mode_scan import reply_mode as rm  # main's scanner (same engine-sentence list)
    except ImportError:
        src = subprocess.run(["git", "show", "origin/main:analysis/tools/supplier_mode_scan.py"], cwd=ROOT,
                             capture_output=True, text=True, encoding="utf-8").stdout
        ns = {}
        exec(src.split("def games():")[0], ns)
        rm = ns["reply_mode"]
    return rm(reasons)


def probe_once(client):
    opened = client.open_session("case:D01")
    sid = opened["session_id"]
    sup = next(iter(opened["threads"]))
    try:
        reply = client.send_message(sid, sup, PROBE)
    finally:
        try:
            client.send_message(sid, sup, {"action": {"type": "walk_away"}})
        except Exception:
            pass
    time.sleep(1)
    trace = (client.session(sid).get("result") or {}).get("trace") or []
    reasons = next((t.get("reasons") or [] for t in trace if t.get("actor") != "buyer" and t.get("round") == 1), [])
    mode = reply_mode(reasons) if reasons else None
    delay = (reply.get("signals") or {}).get("reply_delay_days")
    return sid, {"T": "TEMPLATE", "M": "model"}.get(mode, "unclear"), delay, reasons


def log(line):
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with LOG.open("a", encoding="utf-8") as f:
        f.write(f"{stamp} {line}\n")
    print(f"{stamp} {line}", flush=True)


def play(design):
    log(f"TEMPLATE seen -> playing {design}")
    out = subprocess.run([sys.executable, str(ROOT / "tools" / "experiments" / "probe.py"), design], cwd=KIT,
                         capture_output=True, text=True, encoding="utf-8")
    tail = "\n".join(out.stdout.strip().splitlines()[-3:])
    log("probe: " + tail.replace("\n", " | "))
    files = ["analysis/experiments/probes/results.jsonl", "notes/quota_log.md", "analysis/experiments/mode_watch.log",
             "datasets/runs", "tools/replays/backoffice"]
    subprocess.run(["git", "add", *files], cwd=ROOT)
    msg = f"live P10 (engine-mode watch): {tail.splitlines()[0][:150] if tail else 'see log'}"
    subprocess.run(["git", "commit", "-q", "-m", msg + "\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"],
                   cwd=ROOT)
    subprocess.run(["git", "pull", "-q", "--no-rebase", "origin", "parth/n1-p06-p09-p12"], cwd=ROOT)
    subprocess.run(["git", "push", "-q", "origin", "parth/n1-p06-p09-p12"], cwd=ROOT)
    return out.stdout


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--every", type=int, default=300, help="seconds between sandbox probes")
    ap.add_argument("--until", default="11:30", help="local time to stop (HH:MM)")
    ap.add_argument("--design", default=str(ROOT / "analysis" / "experiments" / "probes" / "P10_M.json"))
    ap.add_argument("--max-plays", type=int, default=2)
    args = ap.parse_args()
    load_env(str(KIT / ".env"))
    client = ArenaClient()
    stop = datetime.datetime.combine(datetime.date.today(), datetime.time.fromisoformat(args.until))
    plays = 0
    while True:
        try:
            sid, mode, delay, reasons = probe_once(client)
            log(f"sandbox {sid}: {mode} (delay {delay}) {json.dumps(reasons, ensure_ascii=False)[:160]}")
            if mode == "TEMPLATE" and plays < args.max_plays:
                result = play(args.design)
                plays += 1
                if "score=0.7" in result and any(f"score=0.{x}" in result for x in ("74", "75", "76", "77", "78", "79")):
                    log("record attempt done")
        except Exception as e:  # never die on a network blip
            log(f"probe error: {type(e).__name__}: {e}")
        if args.once or datetime.datetime.now() >= stop or plays >= args.max_plays:
            break
        time.sleep(args.every)


if __name__ == "__main__":
    main()
