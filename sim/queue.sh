#!/bin/bash
# Deviation 12 (SIM_PROTOCOL.md): one worker over jobs_consolidation.txt, in order. Two copies may run (the two-worker
# limit): each job is claimed with an atomic mkdir lock, and finished jobs (output present) are skipped.
# Lines: "dose ALGO TASK SEED" (dose.py) or "train ALGO TASK SEED" (run.py, 1M steps for PPO, 200k otherwise).
cd "$(dirname "$0")"
mkdir -p logs locks
while read -r kind algo task seed; do
  if [ "$kind" = dose ]; then out="results/dose/$algo/$task/seed$seed.json"; else out="models/$algo/$task/seed$seed.zip"; fi
  [ -f "$out" ] && continue
  [ "$kind" = dose ] && [ ! -f "models/$algo/$task/seed$seed.zip" ] && continue  # model not trained yet: a later pass
  mkdir "locks/$kind-$algo-$task-$seed" 2>/dev/null || continue
  if [ "$kind" = dose ]; then
    nice ./env/bin/python dose.py "$algo" "$task" "$seed" > "logs/dose-$algo-$task-$seed.log" 2>&1
  else
    steps=200000; case "$algo" in ppo*) steps=1000000;; esac
    nice ./env/bin/python run.py "$algo" "$task" "$seed" "$steps" > "logs/$algo-$task-$seed.log" 2>&1 \
      || nice ./env/bin/python run.py "$algo" "$task" "$seed" "$steps" > "logs/$algo-$task-$seed.retry.log" 2>&1
  fi
  [ -f "$out" ] || rmdir "locks/$kind-$algo-$task-$seed"
  echo "$(date '+%F %T') $kind $algo $task $seed $([ -f "$out" ] && echo done || echo FAILED)" >> logs/queue.out
done < jobs_consolidation.txt
echo "$(date '+%F %T') pass finished" >> logs/queue.out
