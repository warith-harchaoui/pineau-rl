#!/bin/bash
# Deviation 12 (SIM_PROTOCOL.md): one worker over jobs_consolidation.txt, in order. Two copies may run (the two-worker
# limit): each job is claimed with an atomic mkdir lock, and finished jobs (output present) are skipped.
# Lines: "dose ALGO TASK SEED" (dose.py) or "train ALGO TASK SEED" (run.py, 1M steps for PPO, 200k otherwise).
# Deviation 14: every attempt keeps its own log (logs/<job>.attempt<N>.log, never overwritten) and adds one line to the
# append-only ledger logs/attempts.jsonl: job, attempt, start, end, exit code, SHA-256 of the output if there is one.
cd "$(dirname "$0")"
mkdir -p logs locks
ledger() {  # ledger <job> <attempt> <start> <exit code> <output>
  sha=$([ -f "$5" ] && shasum -a 256 "$5" | cut -d' ' -f1)
  printf '{"job": "%s", "attempt": %d, "start": "%s", "end": "%s", "exit": %d, "sha256": "%s"}\n' \
    "$1" "$2" "$3" "$(date '+%F %T')" "$4" "$sha" >> logs/attempts.jsonl
}
while read -r kind algo task seed; do
  if [ "$kind" = dose ]; then out="results/dose/$algo/$task/seed$seed.json"; else out="models/$algo/$task/seed$seed.zip"; fi
  [ -f "$out" ] && continue
  [ "$kind" = dose ] && [ ! -f "models/$algo/$task/seed$seed.zip" ] && continue  # model not trained yet: a later pass
  job="$kind-$algo-$task-$seed"
  mkdir "locks/$job" 2>/dev/null || continue
  for try in 1 2; do  # a crash is relaunched once (SIM_PROTOCOL.md); a stop by the watchdog leaves the lock for a restart
    n=$(( $(grep -c "\"job\": \"$job\"" logs/attempts.jsonl 2>/dev/null || true) + 1 ))
    start=$(date '+%F %T')
    if [ "$kind" = dose ]; then
      nice ./env/bin/python dose.py "$algo" "$task" "$seed" > "logs/$job.attempt$n.log" 2>&1
    else
      steps=200000; case "$algo" in ppo*) steps=1000000;; esac
      nice ./env/bin/python run.py "$algo" "$task" "$seed" "$steps" > "logs/$job.attempt$n.log" 2>&1
    fi
    code=$?
    ledger "$job" "$n" "$start" "$code" "$out"
    [ -f "$out" ] && break
    [ "$code" -ge 128 ] && break  # killed by a signal (watchdog, shutdown): not a crash, no automatic relaunch
  done
  [ -f "$out" ] || rmdir "locks/$job"
  echo "$(date '+%F %T') $kind $algo $task $seed $([ -f "$out" ] && echo done || echo FAILED)" >> logs/queue.out
done < jobs_consolidation.txt
echo "$(date '+%F %T') pass finished" >> logs/queue.out
