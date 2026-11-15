#!/bin/bash
# Every 20 min: stops the launchers and their runs (GRPO included) if free disk < MIN_FREE_GB (default 10) or swap grew > 8 GB since start.
# Swap is measured as growth because macOS keeps stale swap from earlier runs.
cd "$(dirname "$0")"
swap_mb() { sysctl -n vm.swapusage | sed -E 's/.*used = ([0-9.]+)M.*/\1/' | cut -d. -f1; }
free_gb() { df -g / | awk 'NR==2{print $4}'; }
base=$(swap_mb)
echo "$(date '+%F %T') start swap_base=${base}M free=$(free_gb)G"
while pgrep -f "(drive2?|queue)\.sh" > /dev/null; do
  f=$(free_gb); s=$(( $(swap_mb) - base ))
  echo "$(date '+%F %T') free=${f}G swap_growth=${s}M"
  if [ "$f" -lt "${MIN_FREE_GB:-10}" ] || [ "$s" -gt 8192 ]; then
    echo "$(date '+%F %T') STOP free=${f}G swap_growth=${s}M"
    pkill -f "(drive2?|queue|cpu)\.sh"; pkill -f "xargs -P"; pkill -f "env/bin/python (run|dose).py"; pkill -f "grpo.py"
    for l in locks/*; do  # deviation 14: every job stopped here goes to the ledger, and its lock is freed for a restart
      [ -d "$l" ] || continue; j=${l#locks/}
      case "$j" in dose-*) o="results/dose/$(echo "$j" | cut -d- -f2)/$(echo "$j" | cut -d- -f3-4)/seed${j##*-}.json";;
                   *) o="models/$(echo "$j" | cut -d- -f2)/$(echo "$j" | cut -d- -f3-4)/seed${j##*-}.zip";; esac
      [ -f "$o" ] && continue
      printf '{"job": "%s", "end": "%s", "stopped_by": "watchdog", "free_gb": %d, "swap_growth_mb": %d}\n' \
        "$j" "$(date '+%F %T')" "$f" "$s" >> logs/attempts.jsonl
      rmdir "$l"
    done
    exit 1
  fi
  sleep 1200
done
echo "$(date '+%F %T') drivers finished"
