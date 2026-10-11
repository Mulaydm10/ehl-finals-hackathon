# Sunday 08:00 - one command: download, back up, merge the release into tacto/data, rebuild the datasets, check.
#   bash tools/sunday_release/rebuild.sh            (from anywhere; repo on the Mac)
# Roll back: printed at the end (restore the backup folder).
set -e
REPO=~/Dhruv/ehl-finals-hackathon
cd "$REPO/tacto/starter-kit"
set -a; . ./.env; set +a
STAMP=$(date +%Y%m%d-%H%M)
BK="$REPO/backups/pre-release-$STAMP"
mkdir -p "$BK"
cp -R "$REPO/tacto/data" "$BK/tacto-data"
cp -R "$REPO/datasets" "$BK/datasets"
echo "== 1. backup -> $BK"
echo "== 2. download (arena data)"
.venv/bin/arena data --out data
ls -la data/ data/release-sunday 2>/dev/null | head -40
if [ ! -d data/release-sunday ]; then echo "!! no release-sunday folder yet - is it public? (arena data prints the time)"; exit 2; fi
echo "== 3. merge (dry run first)"
python3 "$REPO/tools/sunday_release/merge_release.py" data/release-sunday "$REPO/tacto/data" --dry
python3 "$REPO/tools/sunday_release/merge_release.py" data/release-sunday "$REPO/tacto/data"
echo "== 4. round-1 dump BEFORE the rebuild (old datasets)"
NOIDEA_EXPERIMENTS=hidden .venv/bin/python "$REPO/notes/analysis_v234/r1_dump.py" > /tmp/r1_pre_release.txt 2>&1 || true
echo "== 5. rebuild datasets A/B/C"
cd "$REPO"
python3 src/datasets/build_abc.py --data tacto/data --out datasets
python3 -c "import json; r=json.load(open('datasets/build_report.json')); print('suppliers', r['suppliers'], 'claims', r['claims'], 'self_check', r['self_check']['ok'], 'ok /', r['self_check']['bad'], 'bad'); assert r['self_check']['bad'] == 0, r['self_check']['problems'][:5]"
echo "== 6. tests + crash test (all 19 practice cases, hidden mode) + round-1 diff"
cd "$REPO/tacto/starter-kit"
.venv/bin/python -m pytest -q tests 2>&1 | tail -2
NOIDEA_EXPERIMENTS=hidden .venv/bin/python "$REPO/notes/analysis_v234/crash_test.py" 2>&1 | tail -3
NOIDEA_EXPERIMENTS=hidden .venv/bin/python "$REPO/notes/analysis_v234/r1_dump.py" > /tmp/r1_post_release.txt 2>&1 || true
diff /tmp/r1_pre_release.txt /tmp/r1_post_release.txt | head -60 || true
echo "== done. Roll back with:  rm -rf $REPO/tacto/data $REPO/datasets && cp -R $BK/tacto-data $REPO/tacto/data && cp -R $BK/datasets $REPO/datasets"
