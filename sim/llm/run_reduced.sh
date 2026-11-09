#!/bin/bash
# Reduced GRPO (plan option a): one run at a time, 100 steps, seeds 0-2, true vs random reward, lr 3e-6.
# MPS memory capped; a guard kills the current run if free disk < 10 GB or swap grows > 4 GB.
cd "$(dirname "$0")"
export PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.35 PYTORCH_MPS_LOW_WATERMARK_RATIO=0.25 EVAL_EVERY=50
swap_mb() { sysctl -n vm.swapusage | sed -E 's/.*used = ([0-9.]+)M.*/\1/' | cut -d. -f1; }
free_gb() { df -g / | awk 'NR==2{print $4}'; }
base=$(swap_mb)
for spec in "Qwen/Qwen2.5-0.5B-Instruct qwen05" "unsloth/Llama-3.2-1B-Instruct llama1"; do
  set -- $spec; model=$1; tag=$2
  for seed in 0 1 2; do for reward in true random; do
    f="results/$tag/mul2/$reward/seed$seed.jsonl"
    grep -q '"step": 100,.*pass1' "$f" 2>/dev/null && continue
    ../env-llm/bin/python grpo.py "$model" "$tag" mul2 "$reward" "$seed" 100 3e-6 > "logs/$tag-$reward-$seed.log" 2>&1 &
    pid=$!
    while kill -0 $pid 2>/dev/null; do
      f_=$(free_gb); s_=$(( $(swap_mb) - base ))
      if [ "$f_" -lt 10 ] || [ "$s_" -gt 4096 ]; then
        echo "$(date '+%F %T') STOP $tag $reward $seed free=${f_}G swap_growth=${s_}M"; kill $pid; exit 1
      fi
      sleep 60
    done
    echo "$(date '+%F %T') $(tail -1 logs/$tag-$reward-$seed.log)"
  done; done
done
echo ALL_DONE
