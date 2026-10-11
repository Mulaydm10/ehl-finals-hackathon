#!/bin/bash
# WARNING (2026-10-11, live evidence): P18 answers an IDENTICAL conversation identically. Running a fixed-text agent N times
# repeats one game N times (5 sessions wasted at 04:10). Only use this with an agent whose messages change per game.
# USES ONE PRACTICE SESSION PER GAME. Usage: bash analysis/tools/p18_batch.sh <agent.py> [N]
# Run up to N live P18 games with the given agent, one after another; stop on a score above the record.
AGENT=$1; N=${2:-6}; SP="${TMPDIR:-/tmp}"; ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT/tacto/starter-kit"
for i in $(seq 1 $N); do
  LOG="$SP/p18_batch_$(date +%H%M%S)_$i.log"
  .venv/Scripts/python.exe "$ROOT/analysis/tools/play_variant.py" case:P18 "$AGENT" > "$LOG" 2>&1
  SID=$(grep -o "session [0-9a-f]*" "$LOG" | head -1 | cut -d' ' -f2)
  SC=$(grep '"score"' "$LOG" | grep -o "[0-9.]*" | head -1)
  MODE=$(grep -o "session -> [A-Za-z]* session\|-> SOFT session\|-> normal session" "$LOG" | head -1)
  PATH_=$(grep -o "open {'unit_price': [0-9.]*, 'payment_days': [0-9]*\|final_offer {'unit_price': [0-9.]*\|agreed {'unit_price': [0-9.]*" "$LOG" | grep -o "[0-9]\.[0-9]*" | tr '\n' ' ')
  echo "GAME $i $SID score=${SC:-ERR} ${MODE} prices: ${PATH_} log=$(basename $LOG)"
  if [ -z "$SC" ]; then echo "STOP: game $i had no score (see log)"; exit 1; fi
  if python -c "import sys; sys.exit(0 if float('$SC') > 0.75595 else 1)"; then echo "BEAT THE RECORD in game $i"; exit 0; fi
done
echo "BATCH DONE: $N games, no record"
