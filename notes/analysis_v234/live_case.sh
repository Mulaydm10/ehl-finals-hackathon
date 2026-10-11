# usage: bash live_case.sh <case e.g. P07> <experiments> <tag>   -> /tmp/v216/<case>_<tag>.log  (the final's agent: --agent noidea)
. /tmp/astra_env.sh
source .venv/bin/activate
export NOIDEA_EXPERIMENTS="$2"
arena play case:$1 --agent noidea -v > /tmp/v216/$1_$3.log 2>&1
echo DONE >> /tmp/v216/$1_$3.log
