# summary of running/finished live logs matching a pattern: bash mon.sh 'v234'
for f in /tmp/v216/*$1*.log; do
  sess=$(grep -o "sessions/[0-9a-f]\{16\}" "$f" | head -1 | cut -d/ -f2)
  last=$(grep -E "sup:[0-9]+ (open|final_offer|agreed|walked_away|no_bid)" "$f" | tail -1 | cut -c1-140)
  sc=$(grep -iE "score[^s]" "$f" | tail -1 | cut -c1-160)
  done=$(tail -1 "$f" | grep -c DONE)
  echo "$(basename $f .log) [$sess] done=$done | $last | $sc"
done
