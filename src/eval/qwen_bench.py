"""Qwen opening-paragraph benchmark: latency, how much survives the no-figures filter, samples."""
import json, logging, re, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tacto/starter-kit"))
logging.basicConfig(level=logging.WARNING)
from arena_kit.agents.noidea import NoIdeaAgent, SYSTEM
from arena_kit.agents.llm import llm_from_env
raw_complete = llm_from_env()
log = []
def complete(system, user):
    t = time.time(); out = raw_complete(system, user); log.append((time.time() - t, out)); return out
cs = {c["case_id"][5:]: c for c in json.loads((ROOT / "datasets/cases_practice.json").read_text())}
a = NoIdeaAgent(complete)
for f in sorted((ROOT / "analysis/cases/openings").glob("*.json")):
    th = {k: list(v) for k, v in json.loads(f.read_text())["threads"].items()}
    a.case_id = None
    m = a.decide(cs[f.stem], th)["message"]
    secs, out = log[-1]
    sents = [x for x in re.split(r"(?<=[.!?])\s+", " ".join(out.split())) if x]
    kept = [x for x in sents if not any(ch.isdigit() for ch in x)]
    print(f"{f.stem}: {secs:4.1f}s  sentences {len(sents)} kept {len(kept)}  | {m['body'].split(chr(10)*2)[1][:230]}")
t = [x for x, _ in log]
print(f"\nlatency mean {sum(t)/len(t):.1f}s max {max(t):.1f}s over {len(t)} calls")
