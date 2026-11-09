#!/bin/bash
cd "$(dirname "$0")"
for lr in 3e-6 1e-5 3e-5; do
  EVAL_EVERY=60 ../env-llm/bin/python grpo.py Qwen/Qwen2.5-0.5B-Instruct qwen05_pilot_$lr mul2 true 9 60 $lr 2>&1 | grep '"done"'
  EVAL_EVERY=60 ../env-llm/bin/python grpo.py unsloth/Llama-3.2-1B-Instruct llama1_pilot_$lr mul2 true 9 60 $lr 2>&1 | grep '"done"'
done
