#!/bin/bash
# Runs every line of jobs2.txt, 8 at a time; skips runs whose final model already exists; logs one line per run.
cd "$(dirname "$0")"
mkdir -p logs
run_one() {
  set -- $1
  tag=$1; [ "${5:-}" = "--zoo" ] && tag="$1_zoo"; [ "${5:-}" = "--zoofix" ] && tag="$1_zoofix"
  [ -f "models/$tag/$2/seed$3.zip" ] && exit 0
  ./env/bin/python run.py "$@" > "logs/$tag-$2-$3.log" 2>&1 || ./env/bin/python run.py "$@" > "logs/$tag-$2-$3.retry.log" 2>&1
  tail -1 "logs/$tag-$2-$3.log"
}
export -f run_one
cat jobs2.txt | xargs -P 4 -I{} bash -c 'run_one "{}"' >> logs/done2.jsonl
echo ALL_DONE >> logs/done2.jsonl
