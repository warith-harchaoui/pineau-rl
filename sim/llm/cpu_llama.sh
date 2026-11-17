#!/bin/bash
# LLM_PROTOCOL.md, deviation 16 (e), outside the protocol: the Llama `random` run with random seed 4, which failed twice on
# the GPU, launched once on CPU (2 threads, as cpu.sh) after the CrossQ trainings of SIM deviation 12. Its results go
# to results/llama1_cpu/, which summary.py does not read: it enters no statistic.
cd "$(dirname "$0")"
export DEVICE=cpu OMP_NUM_THREADS=2 EVAL_EVERY=50 TOKENIZERS_PARALLELISM=false MICRO=2  # as night.sh for Llama
log() { echo "$(date '+%F %T') $*" >> logs/cpu_llama.out; }
until [ "$(ls ../models/crossq/*/seed1[0-9].zip 2>/dev/null | wc -l)" -ge 40 ]; do sleep 600; done
log "llama1 random 4 on CPU: start (single attempt)"
nice -n 19 ../env-llm/bin/python grpo.py unsloth/Llama-3.2-1B-Instruct llama1_cpu mul2 random 4 100 3e-6 > logs/llama1_cpu-random-4.log 2>&1
log "llama1 random 4 on CPU: $(tail -1 logs/llama1_cpu-random-4.log | cut -c1-160)"
