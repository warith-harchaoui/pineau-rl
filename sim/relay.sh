#!/bin/bash
# Switches the queues without killing a run: stops launching new jobs, waits for the runs in flight to end,
# then starts the main queue at P=1 (one JAX run, about 2 cores) and TRPO (B1) at P=2 (1 core each): 4 cores.
cd "$(dirname "$0")"
pkill -f "drive\.sh"; pkill -f "xargs -P"
while pgrep -f "env/bin/python run.py" > /dev/null; do sleep 60; done
echo "$(date '+%F %T') relay: in-flight runs done, starting P=1 main + P=2 TRPO"
P=1 nohup nice -n 19 ./drive.sh > logs-drive.out 2>&1 &
JOBS=jobs3.txt DONE=logs/done3.jsonl P=2 nohup nice -n 19 ./drive.sh > logs-drive3.out 2>&1 &
sleep 5
pgrep -f watchdog.sh > /dev/null || nohup ./watchdog.sh >> logs/watchdog.log 2>&1 &
