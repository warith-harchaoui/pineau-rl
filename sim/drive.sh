#!/bin/bash
# Runs every line of $JOBS (default jobs.txt), logging to $DONE (default logs/done.jsonl), P at a time (default 4); skips runs whose final model already exists; logs one line per run.
cd "$(dirname "$0")"
mkdir -p logs
run_one() {
  set -- $1
  tag=$1; [ "${5:-}" = "--zoo" ] && tag="$1_zoo"
  [ -f "models/$tag/$2/seed$3.zip" ] && exit 0
  ./env/bin/python run.py "$@" > "logs/$tag-$2-$3.log" 2>&1 || ./env/bin/python run.py "$@" > "logs/$tag-$2-$3.retry.log" 2>&1
  tail -1 "logs/$tag-$2-$3.log"
}
export -f run_one
cat "${JOBS:-jobs.txt}" | xargs -P "${P:-4}" -I{} bash -c 'run_one "{}"' >> "${DONE:-logs/done.jsonl}"
echo ALL_DONE >> "${DONE:-logs/done.jsonl}"
