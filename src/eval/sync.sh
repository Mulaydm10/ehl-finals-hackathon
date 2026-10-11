# commit + pull + push safely. usage: bash sync.sh "commit message"
cd ~/Dhruv/ehl-finals-hackathon || exit 1
markers() { git grep -l "^<<<<<<< \|^>>>>>>> " -- . ; }
if markers; then echo "MARKERS IN WORKTREE - nothing committed, fix them first"; exit 3; fi   # never commit markers
git add -A
git diff --cached --quiet || git commit -qm "$1

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
git pull --no-rebase -q --no-edit origin main
for p in $(git diff --name-only --diff-filter=U); do
  case "$p" in
    notes/quota_log.md|notes/sessions.txt|notes/agent_changelog.md|docs/GENERAL_RULES.md)
      sed -i "" -e "/^<<<<<<< /d" -e "/^=======$/d" -e "/^>>>>>>> /d" "$p" ;;           # logs: keep both sides
    datasets/runs/*|tools/replays/*) git checkout --theirs "$p" ;;                          # same session data
    analysis/central/claim_reactions.json) git checkout --theirs "$p"; tacto/starter-kit/.venv/bin/python analysis/tools/mine_claims.py >/dev/null 2>&1 ;;
    datasets/H_supplier_memory.json) git checkout --theirs "$p"; python3 src/eval/supplier_memory.py >/dev/null ;;
    *) echo "MANUAL CONFLICT: $p (merge left open - resolve, then rerun)"; exit 2 ;;
  esac
done
git add -A
if markers; then echo "MARKERS LEFT - not committing"; exit 3; fi
git diff --cached --quiet || git commit -qm "Merge origin/main

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
git push -q origin main && git fetch -q && echo "synced $(git rev-parse --short HEAD) = origin $(git rev-parse --short origin/main)"
