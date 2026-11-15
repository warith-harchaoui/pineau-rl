#!/bin/bash
# Every hour (SIM_PROTOCOL.md, deviation 15): how many cores the other programs of the machine leave free, and how many
# of them this project may use, up to MAX_CORES (8). One training run (run.py, dose.py) is single-threaded: one core;
# the GRPO run on CPU (cpu.sh) takes two. Above the current number of workers, new workers (worker.sh) start; below it,
# nothing is stopped: workers.max is lowered and each worker leaves after its current job (worker.sh reads it).
# Free cores = cores - CPU of the other processes (ps %cpu, summed) - a margin of one core. Decisions: logs/scale.log.
cd "$(dirname "$0")"
MAX_CORES=${MAX_CORES:-8}
NCPU=$(sysctl -n hw.ncpu)
log() { echo "$(date '+%F %T') $*" >> logs/scale.log; }
while true; do
  ours=$(pgrep -f "env/bin/python (run|dose).py|grpo.py|queue.sh|worker.sh|cpu.sh|scale.sh|watchdog.sh" | tr '\n' ',' | sed 's/,$//')
  other=$(ps -axo pid=,pcpu= | awk -v ours=",$ours," 'index(ours, "," $1 ",") == 0 { s += $2 } END { printf "%d", s / 100 }')
  grpo=$(pgrep -f "grpo.py" > /dev/null && echo 2 || echo 0)
  free=$(( NCPU - other - 1 ))
  budget=$(( free < MAX_CORES ? free : MAX_CORES ))
  target=$(( budget - grpo )); [ "$target" -lt 1 ] && target=1
  workers=$(pgrep -f "/bin/bash ./(queue|worker).sh" | wc -l | tr -d ' ')
  echo "$target" > workers.max
  started=0
  while [ "$workers" -lt "$target" ] && pgrep -f watchdog.sh > /dev/null; do  # never more work without the watchdog
    nohup ./worker.sh >> logs/worker.nohup 2>&1 &
    workers=$((workers + 1)); started=$((started + 1)); sleep 2
  done
  log "cores=$NCPU other=$other free=$free grpo=$grpo budget=$budget workers.max=$target started=$started"
  sleep 3600
done
