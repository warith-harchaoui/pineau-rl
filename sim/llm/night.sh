#!/bin/bash
# GRPO at night only (LLM_PROTOCOL.md, Écart 8): 23:00 to 07:00, no run started after 06:00.
# Keeps the 4-core budget: the main simulation queue's JAX run is paused (SIGSTOP) while GRPO runs, then resumed.
# The NaN came from GPU work cut short by macOS (LLM_PROTOCOL.md, écart 10): grpo.py now recomputes a corrupted update.
# A run that still fails is retried the next night; two failures of the same run are reported as a result.
cd "$(dirname "$0")"
export PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.45 PYTORCH_MPS_LOW_WATERMARK_RATIO=0.3 EVAL_EVERY=50 TOKENIZERS_PARALLELISM=false
log() { echo "$(date '+%F %T') $*" >> logs/night.out; }
hour() { date +%H | sed 's/^0//'; }
night() { [ "$(hour)" -ge 23 ] || [ "$(hour)" -lt 6 ]; }
main_pids() { pgrep -f "env/bin/python (run|dose).py"; }  # every simulation job (deviation 12)
pause_main() { for p in $(main_pids); do kill -STOP "$p"; done; log "paused main queue: $(main_pids | tr '\n' ' ')"; }
resume_main() { for p in $(main_pids); do kill -CONT "$p"; done; log "resumed main queue"; }
trap resume_main EXIT
done_run() { grep -q '"step": 100,.*pass1' "results/$1/mul2/$2/seed$3.jsonl" 2>/dev/null; }
batt() { pmset -g batt | grep -o '[0-9]*%' | head -1 | tr -d %; }
one() {  # one <model> <tag> <reward> <seed> <micro>
  night || return 1
  [ "$(batt)" -ge "${MIN_BATT:-55}" ] || { log "battery $(batt)% below ${MIN_BATT:-55}%: no GPU run tonight"; return 1; }
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
  for spec in "unsloth/Llama-3.2-1B-Instruct llama1 2"; do  # the Qwen runs go on CPU (cpu.sh, écart 11)
    set -- $spec
    for seed in ${SEEDS:-0 1 2}; do for reward in true random; do one "$1" "$2" "$reward" "$seed" "$3" || return 1; done; done
  done
}
all_done() {  # every run of this launcher reached step 100 (a crashed or stopped run returns from one() too)
  for seed in ${SEEDS:-0 1 2}; do for reward in true random; do done_run llama1 "$reward" "$seed" || return 1; done; done
}
tries=${TRIES:-0}  # nights already failed by an unfinished run (a relaunch passes TRIES=1)
while true; do
  until night; do sleep 300; done
  log "night window open"
  if all_runs; then
    all_done && { log ALL_DONE; exit 0; }
    tries=$((tries + 1)); log "pass finished with unfinished runs ($tries)"
    [ "$tries" -ge 2 ] && { log "GAVE_UP: a run failed on two nights, reported as a result"; exit 1; }
  fi
  log "night window closed"
  while night; do sleep 300; done
done
