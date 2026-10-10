"""Final rehearsal under load: ONE process (shared client + rate limiter, like `arena run --set final`), the given practice
cases in parallel, each with a wave cap (default 8 min; the kit closes 90 s before it). Logs per case: rounds, slowest
decision, timeouts, result. Uses practice quota (one session per case).
    cd tacto/starter-kit && set -a && . ./.env && . ./.env.openai && set +a && LLM_PROVIDER=openai LLM_MODEL=gpt-6-astra \
      NOIDEA_EXPERIMENTS=hidden .venv/bin/python load_test.py P01 P02 P03 P04 P07 P08 P10 P11 P18"""
import logging, re, sys, time, json, threading
from concurrent.futures import ThreadPoolExecutor
from arena_kit import ArenaClient
from arena_kit.cli import agent_factory
from arena_kit.play import RemoteTable, play

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(threadName)s %(message)s", datefmt="%H:%M:%S")
for n in ("httpx", "openai", "httpcore"):
    logging.getLogger(n).setLevel(logging.WARNING)
slow = []


class Watch(logging.Handler):  # collect the kit's own warnings: slow decisions, timeouts, re-syncs, failures
    def emit(self, record):
        msg = record.getMessage()
        if re.search(r"decision took|missed|timeout|re-sync|HTTP 5|failed|safe move|Traceback", msg):
            slow.append(f"{record.threadName}: {msg[:200]}")


logging.getLogger("arena").addHandler(Watch())
cases = ["case:" + c for c in sys.argv[1:]]
cap_s = 8 * 60
client = ArenaClient()
new_agent = agent_factory("noidea", None)
t0 = time.time()
cap = t0 + cap_s


def one(cid):
    threading.current_thread().name = cid.split(":")[1]
    start = time.time()
    try:
        r = play(RemoteTable(client), cid, new_agent(), deadline=cap)
        return cid, r, time.time() - start
    except Exception as e:
        logging.getLogger("arena").exception("%s failed", cid)
        return cid, e, time.time() - start


with ThreadPoolExecutor(max_workers=min(10, len(cases))) as pool:
    out = list(pool.map(one, cases))
print("\n==== LOAD TEST: %d cases in parallel, cap %ds, wall %.0fs" % (len(cases), cap_s, time.time() - t0))
for cid, r, took in out:
    if isinstance(r, Exception):
        print(f"{cid}: EXCEPTION {r!r} after {took:.0f}s")
    else:
        print(f"{cid}: score {r.get('score')} deal {r.get('deal')} in {took:.0f}s")
print("---- warnings (%d):" % len(slow))
for s in slow[:60]:
    print("  ", s)
print("practice left:", client.practice_remaining)
