# after every live game: archive it, rebuild the supplier memory and the claim-reaction table (the agent reads both)
cd ~/Dhruv/ehl-finals-hackathon/tacto/starter-kit && set -a && . ./.env && set +a
.venv/bin/python ../../src/eval/archive_runs.py > /dev/null 2>&1
cd ../.. && python3 src/eval/supplier_memory.py > /dev/null && tacto/starter-kit/.venv/bin/python analysis/tools/mine_claims.py > /dev/null 2>&1
echo "memory + reactions rebuilt"
