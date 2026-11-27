#!/bin/bash
# GRPO rerun of LLM_PROTOCOL.md, deviation 20: grpo.py --c7, all on MPS, 10 seeds x 2 models x 2 rewards (40 runs),
# preceded by the pilot on the held-out split ALL[300:450]. Start (from anywhere):
#   nohup sim/llm/c7.sh > /dev/null 2>&1 &        progress: tail sim/llm/logs/c7.out
# It waits by itself until the GPU is free (no model loaded in Ollama, no Ollama runner), then works in the window:
#   WINDOW=night (default): 23:00 to 07:00, a run starts only if its expected duration ends before 07:00, and a run
#                still going at 07:00 is stopped and restarted from step 0 the next night (macOS corrupts MPS work
#                during interactive use: deviations 10 and 11);  WINDOW=any: around the clock (machine left alone).
# Each run is checked first (finished runs are skipped), so the script can be stopped and restarted at any time.
# A run that fails is retried once on a later pass; a second failure is reported as a result (deviation 20), never on CPU.
cd "$(dirname "$0")"
export DEVICE=mps PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.45 PYTORCH_MPS_LOW_WATERMARK_RATIO=0.3 TOKENIZERS_PARALLELISM=false \
       OMP_NUM_THREADS=${OMP_NUM_THREADS:-2} HF_HUB_OFFLINE=1  # 2 threads by default (SIM deviation 19); 4 from deviation 21
WINDOW=${WINDOW:-night}
SEEDS=${SEEDS:-0 1 2 3 4 5 6 7 8 9}
MIN_FREE_GB=${MIN_FREE_GB:-11}  # sim/watchdog.sh stops every job under 10 GB
log() { echo "$(date '+%F %T') $*" >> logs/c7.out; }
mins() { echo $((10#$(date +%H) * 60 + 10#$(date +%M))); }
# Expected minutes per run (deviation 20, from the MPS runs of deviations 13 and 14), with a margin of a quarter
budget() { case "$1 $2" in qwen05_c7*) echo 82;; "llama1_c7 true") echo 122;; *) echo 155;; esac; }
can_start() {  # can_start <minutes needed>
  [ "$WINDOW" = any ] && return 0
  local m; m=$(mins)
  if [ "$m" -ge 1380 ]; then m=$((m - 1440)); fi  # minutes relative to midnight, negative before it
  [ "$m" -ge -60 ] && [ $((m + $1)) -le 420 ]
}
in_window() { [ "$WINDOW" = any ] && return 0; local m; m=$(mins); [ "$m" -ge 1380 ] || [ "$m" -lt 420 ]; }
gpu_free() {  # the survey's local reader (study/gemma_reader.py) is not running and nothing is loaded in Ollama
  ! pgrep -f "python gemma_reader.py" > /dev/null && [ "$(ollama ps 2>/dev/null | tail -n +2 | grep -c .)" -eq 0 ] \
    && ! pgrep -f "ollama runner" > /dev/null
}
disk_ok() { [ "$(df -g . | awk 'NR==2 {print $4}')" -ge "$MIN_FREE_GB" ]; }
main_pids() { pgrep -f "env/bin/python (run|dose).py"; }  # the simulation jobs, paused while GRPO runs (as night.sh)
pause_main() { for p in $(main_pids); do kill -STOP "$p"; done; }
resume_main() { for p in $(main_pids); do kill -CONT "$p"; done; }
trap resume_main EXIT
wait_turn() {  # wait_turn <minutes needed>: until the window, the GPU and the disk allow a start
  local said=""
  until can_start "$1" && gpu_free && disk_ok; do
    [ -z "$said" ] && { log "waiting (window: $WINDOW, GPU free: $(gpu_free && echo yes || echo no), disk: $(df -g . | awk 'NR==2 {print $4}') GB)"; said=1; }
    sleep 300
  done
}
done_run() { grep -q '"step": 100,.*"pass1"' "results/$1/mul2/$2/seed$3.jsonl" 2>/dev/null; }
touch logs/c7.fails
fails() { awk -v k="FAIL $1 $2 $3" '$0 == k {n++} END {print n + 0}' logs/c7.fails; }
one() {  # one <model id> <tag> <reward> <seed> <micro>: 0 finished or given up, 1 stopped by the window
  done_run "$2" "$3" "$4" && return 0
  [ "$(fails "$2" "$3" "$4")" -ge 2 ] && return 0
  wait_turn "$(budget "$2" "$3")"
  pause_main
  log "$2 $3 $4: start"
  MICRO=$5 nice -n 10 ../env-llm/bin/python grpo.py "$1" "$2" mul2 "$3" "$4" 100 3e-6 --c7 > "logs/$2-$3-$4.log" 2>&1 &
  local pid=$!
  while kill -0 $pid 2>/dev/null; do
    if ! in_window; then kill $pid; wait $pid 2>/dev/null; resume_main; log "07:00 reached, stopped $2 $3 $4 (not a failure)"; return 1; fi
    sleep 60
  done
  resume_main
  if done_run "$2" "$3" "$4"; then log "$2 $3 $4: $(tail -1 "logs/$2-$3-$4.log" | cut -c1-200)"
  else echo "FAIL $2 $3 $4" >> logs/c7.fails; log "$2 $3 $4: FAILED ($(fails "$2" "$3" "$4")) $(tail -1 "logs/$2-$3-$4.log" | cut -c1-200)"; fi
  return 0
}
QWEN="Qwen/Qwen2.5-0.5B-Instruct qwen05_c7 8"; LLAMA="unsloth/Llama-3.2-1B-Instruct llama1_c7 2"  # MICRO as before
log "c7.sh started (window: $WINDOW, seeds: $SEEDS, threads: $OMP_NUM_THREADS)"
for spec in "$QWEN" "$LLAMA"; do  # the pilot on ALL[300:450], once per model, before any training
  set -- $spec
  [ -f "results/$2/pilot.json" ] && continue
  wait_turn 30; pause_main
  MICRO=$3 nice -n 10 ../env-llm/bin/python grpo.py "$1" "$2" mul2 true 0 0 3e-6 --pilot --c7 > "logs/$2-pilot.log" 2>&1 \
    && tail -1 "logs/$2-pilot.log" > "results/$2/pilot.json"
  resume_main; log "$2 pilot: $(tail -1 "logs/$2-pilot.log" | cut -c1-200)"
done
while true; do  # passes over every run, in balanced blocks: seed by seed, both models, both rewards
  for seed in $SEEDS; do for spec in "$QWEN" "$LLAMA"; do for reward in true random; do
    set -- $spec; one "$1" "$2" "$reward" "$seed" "$3"
  done; done; done
  left=0
  for seed in $SEEDS; do for tag in qwen05_c7 llama1_c7; do for reward in true random; do
    done_run $tag $reward "$seed" || [ "$(fails $tag $reward "$seed")" -ge 2 ] || left=$((left + 1))
  done; done; done
  [ "$left" -eq 0 ] && { log "ALL_DONE (failures reported as results: $(awk 'END {print NR}' logs/c7.fails) lines in logs/c7.fails)"; exit 0; }
  log "pass finished, $left runs left"
done
