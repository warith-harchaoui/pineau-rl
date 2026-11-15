#!/bin/bash
# The remaining Qwen runs on CPU (LLM_PROTOCOL.md, écart 11): during the day, macOS corrupts GPU work for good, and the
# same step on CPU is clean. One run at a time, 2 threads, lowest priority: the second of the two workers.
cd "$(dirname "$0")"
export DEVICE=cpu OMP_NUM_THREADS=2 EVAL_EVERY=50 TOKENIZERS_PARALLELISM=false MICRO=8
log() { echo "$(date '+%F %T') $*" >> logs/cpu.out; }
done_run() { grep -q '"step": 100,.*pass1' "results/$1/mul2/$2/seed$3.jsonl" 2>/dev/null; }
IFS=, read -r -a SPEC_LIST <<< "${SPECS:-random 1,random 2,true 2}"  # deviation 14: SPECS="true 3,random 3,..."
for spec in "${SPEC_LIST[@]}"; do
  set -- $spec
  done_run qwen05 "$1" "$2" && continue
  for attempt in 1 2; do
    log "qwen05 $1 $2: start (attempt $attempt)"
    nice -n 19 ../env-llm/bin/python grpo.py Qwen/Qwen2.5-0.5B-Instruct qwen05 mul2 "$1" "$2" 100 3e-6 > "logs/qwen05-$1-$2.log" 2>&1
    log "qwen05 $1 $2: $(tail -1 "logs/qwen05-$1-$2.log" | cut -c1-160)"
    done_run qwen05 "$1" "$2" && break
  done
done
log ALL_DONE
