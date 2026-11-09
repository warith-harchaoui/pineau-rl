#!/bin/bash
# Every 20 min: stops drive.sh / drive2.sh if free disk < 10 GB or swap grew > 8 GB since start.
# Swap is measured as growth because macOS keeps stale swap from earlier runs.
cd "$(dirname "$0")"
swap_mb() { sysctl -n vm.swapusage | sed -E 's/.*used = ([0-9.]+)M.*/\1/' | cut -d. -f1; }
free_gb() { df -g / | awk 'NR==2{print $4}'; }
base=$(swap_mb)
echo "$(date '+%F %T') start swap_base=${base}M free=$(free_gb)G"
while pgrep -f "drive2?\.sh" > /dev/null; do
  f=$(free_gb); s=$(( $(swap_mb) - base ))
  echo "$(date '+%F %T') free=${f}G swap_growth=${s}M"
  if [ "$f" -lt 10 ] || [ "$s" -gt 8192 ]; then
    echo "$(date '+%F %T') STOP free=${f}G swap_growth=${s}M"
    pkill -f "drive2?\.sh"; pkill -f "xargs -P"; pkill -f "env/bin/python run.py"
    exit 1
  fi
  sleep 1200
done
echo "$(date '+%F %T') drivers finished"
