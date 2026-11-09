#!/bin/bash
# E6 (SIM_PROTOCOL.md, Écart 5): the official RL Zoo pipeline, 10 seeds, once the TRPO queue (B1) is done.
# Two runs at a time, one thread each, so the 4-core budget holds alongside the main queue (one JAX run).
# (macOS xargs -I caps the command at 255 bytes, hence the two lanes of plain loops.)
cd "$(dirname "$0")"
until grep -q ALL_DONE logs/done3.jsonl 2>/dev/null; do sleep 300; done
echo "$(date '+%F %T') zoo_official: start"
lane() {
  for s in "$@"; do
    [ -f zoo_official/seed$s/ppo/Hopper-v4_1/Hopper-v4.zip ] && continue
    OMP_NUM_THREADS=1 nice -n 19 env-zoo/bin/python -m rl_zoo3.train --algo ppo --env Hopper-v4 --seed $s \
      -f zoo_official/seed$s --num-threads 1 --device cpu --eval-freq -1 > logs/zoo_official-$s.log 2>&1
    echo "$(date '+%F %T') seed $s exit $?"
  done
}
lane 0 2 4 6 8 & lane 1 3 5 7 9 & wait
echo "$(date '+%F %T') zoo_official: ALL_DONE"
