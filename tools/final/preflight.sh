# 09:00 pre-flight on the machine and network of the final (the brief asks for one case through the final setup).
#   bash tools/final/preflight.sh            (sandbox cases are free; P01 uses one practice session)
set -e
REPO=~/Dhruv/ehl-finals-hackathon
cd "$REPO/tacto/starter-kit"
set -a; . ./.env; . ./.env.openai; set +a
export LLM_PROVIDER=openai LLM_BASE_URL=https://api.openai.com/v1 LLM_MODEL=gpt-6-astra LLM_API_KEY="$OPENAI_API_KEY"
export NOIDEA_EXPERIMENTS="${NOIDEA_EXPERIMENTS-hidden}"
echo "== 0. version: $(git describe --tags --always) on branch $(git branch --show-current)"
R=$(git rev-parse --show-toplevel); AGENT="tacto/starter-kit/arena_kit analysis/agent_variants/central.py analysis/central/engine_rules.py datasets/G_lessons.json"
for t in final-v2 final-v1; do git -C "$R" rev-parse -q --verify "$t" >/dev/null && break; done   # the newest frozen version
if git -C "$R" diff --quiet "$t" -- $AGENT; then echo "   agent code = $t (frozen)"; else echo "!! agent code differs from $t:"; git -C "$R" diff --stat "$t" -- $AGENT | tail -6; fi
echo "== 1. key"; .venv/bin/arena me | head -12
echo "== 2. model"; .venv/bin/python -c "
from arena_kit.agents import llm_from_env
import time; t = time.time(); out = llm_from_env()('Answer with one word.', 'Say ok.'); print('model ok:', out.strip()[:20], f'{time.time() - t:.1f}s')"
echo "== 3. data: the Sunday release next to the package?"; ls -d data/release-sunday 2>/dev/null || echo "!! no release-sunday yet (run tools/sunday_release/rebuild.sh after 08:00)"
echo "== 4. tests + crash test"; .venv/bin/python -m pytest -q tests 2>&1 | tail -1
.venv/bin/python "$REPO/notes/analysis_v234/crash_test.py" 2>&1 | tail -1
mkdir -p "$REPO/logs"
for c in D01 D02 P01; do
  echo "== 5. $c through the final's agent"
  .venv/bin/arena play case:$c --agent noidea -v > "$REPO/logs/preflight-$c.log" 2>&1 || true
  grep -E '"score"|walk|timeout|failed|safe move|decision took|HTTP 5' "$REPO/logs/preflight-$c.log" | tail -5
done
echo "== done: every case above should show a score, no 'failed' / 'safe move' / 'decision took' lines"
