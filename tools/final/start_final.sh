# Start the Live Final runner. Run it on the Mac mini BEFORE 12:00 and leave it running (no human in the loop after).
#   bash tools/final/start_final.sh
# Default = the configuration validated in the hidden-supplier loops (NOIDEA_EXPERIMENTS=hidden: no supplier memory,
# no per-case reaction data). To run WITH memory instead:  NOIDEA_EXPERIMENTS= bash tools/final/start_final.sh
# If it crashes or the Mac restarts: run this script again - the kit's runner picks up the sessions it had started.
set -e
REPO=~/Dhruv/ehl-finals-hackathon
cd "$REPO/tacto/starter-kit"
set -a; . ./.env; . ./.env.openai; set +a
export LLM_PROVIDER=openai LLM_BASE_URL=https://api.openai.com/v1 LLM_MODEL=gpt-6-astra LLM_API_KEY="$OPENAI_API_KEY"
export NOIDEA_EXPERIMENTS="${NOIDEA_EXPERIMENTS-hidden}"
mkdir -p "$REPO/logs"
LOG="$REPO/logs/final-$(date +%Y%m%d-%H%M%S).log"
echo "$(date) commit $(git -C "$REPO" rev-parse HEAD) experiments=[$NOIDEA_EXPERIMENTS] model=$LLM_MODEL" | tee "$LOG"
nohup caffeinate -dims .venv/bin/arena run --set final --agent noidea --parallel 10 -v >> "$LOG" 2>&1 &
echo "runner pid $! - follow it with:  tail -f $LOG"
