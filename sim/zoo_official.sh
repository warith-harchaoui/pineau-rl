#!/bin/bash
# E6 (SIM_PROTOCOL.md, Écart 5): the official RL Zoo pipeline, 10 seeds, once the TRPO queue (B1) is done.
# Two runs at a time, one thread each, so the 4-core budget holds alongside the main queue (one JAX run).
cd "$(dirname "$0")"
until grep -q ALL_DONE logs/done3.jsonl 2>/dev/null; do sleep 300; done
echo "$(date '+%F %T') zoo_official: start"
seq 0 9 | OMP_NUM_THREADS=1 xargs -P 2 -I{} sh -c '
  [ -f zoo_official/seed{}/ppo/Hopper-v4_1/Hopper-v4.zip ] && exit 0
  nice -n 19 env-zoo/bin/python -m rl_zoo3.train --algo ppo --env Hopper-v4 --seed {} -f zoo_official/seed{} \
    --num-threads 1 --device cpu --eval-freq -1 > logs/zoo_official-{}.log 2>&1
  echo "$(date "+%F %T") seed {} exit $?"'
echo "$(date '+%F %T') zoo_official: ALL_DONE"
