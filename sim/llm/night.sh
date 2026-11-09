#!/bin/bash
# GRPO at night only (LLM_PROTOCOL.md, Écart 8): 23:00 to 07:00, no run started after 06:00.
# Keeps the 4-core budget: the main simulation queue's JAX run is paused (SIGSTOP) while GRPO runs, then resumed.
# First run: the control (qwen05 random seed 1, the run that crashed) without OMP_NUM_THREADS. If it still hits NaN,
# the night stops there: the cause is then looked for in grpo.py before anything else.
cd "$(dirname "$0")"
export PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.35 PYTORCH_MPS_LOW_WATERMARK_RATIO=0.25 EVAL_EVERY=50 TOKENIZERS_PARALLELISM=false
log() { echo "$(date '+%F %T') $*" >> logs/night.out; }
hour() { date +%H | sed 's/^0//'; }
night() { [ "$(hour)" -ge 23 ] || [ "$(hour)" -lt 6 ]; }
main_pids() { pgrep -f "env/bin/python run.py (sac|crossq|ppo_sbx)"; }
pause_main() { for p in $(main_pids); do kill -STOP "$p"; done; log "paused main queue: $(main_pids | tr '\n' ' ')"; }
resume_main() { for p in $(main_pids); do kill -CONT "$p"; done; log "resumed main queue"; }
trap resume_main EXIT
done_run() { grep -q '"step": 100,.*pass1' "results/$1/mul2/$2/seed$3.jsonl" 2>/dev/null; }
one() {  # one <model> <tag> <reward> <seed> <micro>
  night || return 1
  done_run "$2" "$3" "$4" && return 0
  pause_main
  MICRO=$5 nice -n 19 ../env-llm/bin/python grpo.py "$1" "$2" mul2 "$3" "$4" 100 3e-6 > "logs/$2-$3-$4.log" 2>&1 &
  pid=$!
  while kill -0 $pid 2>/dev/null; do
    h=$(hour); if [ "$h" -ge 7 ] && [ "$h" -lt 23 ]; then kill $pid; log "07:00 reached, killed $2 $3 $4"; resume_main; return 1; fi
    sleep 60
  done
  resume_main
  log "$2 $3 $4: $(tail -1 "logs/$2-$3-$4.log" | cut -c1-160)"
}
all_runs() {  # returns 1 as soon as the night window closes
  one Qwen/Qwen2.5-0.5B-Instruct qwen05 random 1 8 || return 1
  done_run qwen05 random 1 || { log "control run failed again: NaN not explained by OMP_NUM_THREADS, stop"; exit 1; }
  for spec in "Qwen/Qwen2.5-0.5B-Instruct qwen05 8" "unsloth/Llama-3.2-1B-Instruct llama1 2"; do
    set -- $spec
    for seed in 0 1 2; do for reward in true random; do one "$1" "$2" "$reward" "$seed" "$3" || return 1; done; done
  done
}
while true; do
  until night; do sleep 300; done
  log "night window open"
  all_runs && { log ALL_DONE; exit 0; }
  log "night window closed"
  while night; do sleep 300; done
done
