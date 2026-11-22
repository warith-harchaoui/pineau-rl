# Recompute every number of the document from the results committed in this repository.
#
#   make install    install the package src/pineau_rl (pyproject.toml) in PY, editable, with no other package:
#                   the dependencies come from envs/analysis.lock, nothing is downloaded
#   make analysis   rerun every analysis script of study/, sim/analysis/ and sim/llm/summary.py (rewrites their JSON)
#   make check      docs/check_numbers.py, article/check_article.py and paper/check_short.py: every key number of both
#                   documents, of the blog article and of the short paper against those JSON files
#   make test       the unit tests (tests/)
#   make lint       ruff and mypy on the package and the tests (needs ruff and mypy, which the locks leave out)
#   make verify     analysis + check + test, then git diff: the JSON files must come back byte for byte
#   make verify-head  the same in a fresh export of the last commit (safe while training runs write to sim/;
#                   the policies, Zoo runs and training logs are left out, since no analysis reads them)
#   make report     report/build.sh: the technical report in LaTeX (French and English), tables and figures from the JSON files
#   make figures    docs/figures/build.py (needs sprezzature-figures, rsvg-convert and the LLM environment)
#   make docs       docs/build.sh (needs md2star, pandoc and LuaLaTeX)
#
# PY is the analysis environment (envs/analysis.txt); PY_LLM the LLM one (envs/llm.txt). In CI: make verify PY=python
# The scripts import the package pineau_rl: every target finds it on PYTHONPATH (src/), installed or not.
# None of these targets trains anything. Training: sim/run.py, sim/drive.sh, sim/llm/grpo.py (see README.md).

PY     ?= $(CURDIR)/sim/env-an/bin/python
PY_LLM ?= $(CURDIR)/sim/env-llm/bin/python
NICE   ?= nice
export PYTHONPATH := $(CURDIR)/src$(if $(PYTHONPATH),:$(PYTHONPATH))

# In dependency order: extension_stats.json feeds robustness, title_filter_compare and trajectory.
STUDY := analyze analyze_final audit_stats agree_v2 extension_stats robustness title_filter title_filter_compare trajectory \
         survey_extra x8_stats q5_versions_stats r36_stats relecture_humaine/tirage35
SIM   := e1 e1_curve b1_trpo b1_script e2 e3 e4 e5 e6 e6_diag e7 e7_rank b3 dose e2_bonferroni e2_strict e7_test
# Deviations 12 and 20 of SIM_PROTOCOL.md: twenty seeds (_s20), the E4 replication on seeds 10 to 19 (_r10),
# PPO read at 200,000 steps like SAC and CrossQ (_equal, _equal_s20).
S20   := e2 e3 e5 e7 e7_rank b3 dose e2_bonferroni e2_strict e7_test
EQUAL := e2 b3 e2_bonferroni e2_strict
# Deviations 22 to 31 of SIM_PROTOCOL.md (21 November 2026): analyses of the data on disk, run after the lists above
# (they read e3.json, e3_s20.json, e5.json and e6_official.json).
POST  := e3_holm e1_grid e5_holdout rule_calibration b1_factor curves effect_sizes e6_speed
SIM12 := $(S20:%=%_s20) e4_r10 $(EQUAL:%=%_equal) $(EQUAL:%=%_equal_s20)

# Every JSON file the analysis rewrites. r36_project_pages.json and r36_quote_check.json need the PDFs (not in the
# repository): written by study/r36_pages.py and study/r36_check.py --json, read by r36_stats.py, not rewritten here.
# e6_official_eval.json needs the trained policies and env-zoo: not rewritten.
OUTPUTS := study/results_2026.json study/results_final.json study/audit_stats.json study/agree_v2.json \
           study/extension_stats.json study/robustness.json study/title_filter.json study/title_filter_compare.json \
           study/trajectory.json study/survey_extra.json study/x8_stats.json study/q5_versions.json \
           study/r36_stats.json \
           study/relecture_humaine/tirage35.json \
           $(SIM:%=sim/analysis/%.json) $(SIM12:%=sim/analysis/%.json) sim/analysis/e6_official.json \
           $(POST:%=sim/analysis/%.json) \
           sim/llm/results/summary.json sim/llm/results/gains.json sim/llm/results/extra.json \
           sim/llm/results/summary_5.json sim/llm/results/gains_5.json sim/llm/results/extra_5.json \
           sim/llm/results/logs_stats_5.json

.PHONY: all install analysis analysis-study analysis-sim hyperparams analysis-suite analysis-llm check test lint verify verify-head figures docs report clean

all: verify

install:
	$(PY) -m pip install --no-deps --no-build-isolation -e .

analysis: analysis-study analysis-sim analysis-llm

analysis-study:
	@cd study && for s in $(STUDY); do echo "study/$$s.py"; $(NICE) $(PY) $$s.py > /dev/null || exit 1; done

analysis-sim:
	@cd sim && for s in $(SIM); do echo "sim/analysis/$$s.py"; $(NICE) $(PY) analysis/$$s.py > /dev/null || exit 1; done
	@echo "sim/analysis/e6_official.py stats"; cd sim && $(NICE) $(PY) analysis/e6_official.py stats > /dev/null
	@cd sim && for s in $(S20); do echo "sim/analysis/$$s.py, twenty seeds"; SEEDS=0:20 SUFFIX=_s20 $(NICE) $(PY) analysis/$$s.py > /dev/null || exit 1; done
	@echo "sim/analysis/e4.py, seeds 10 to 19"; cd sim && SEEDS=10:20 SUFFIX=_r10 $(NICE) $(PY) analysis/e4.py > /dev/null
	@cd sim && for s in $(EQUAL); do echo "sim/analysis/$$s.py, equal budget"; BUDGET=equal SUFFIX=_equal $(NICE) $(PY) analysis/$$s.py > /dev/null || exit 1; \
	  BUDGET=equal SEEDS=0:20 SUFFIX=_equal_s20 $(NICE) $(PY) analysis/$$s.py > /dev/null || exit 1; done
	@cd sim && for s in $(POST); do echo "sim/analysis/$$s.py"; $(NICE) $(PY) analysis/$$s.py > /dev/null || exit 1; done

# Deviation 28: the hyperparameters, read from the libraries of the training environment (sim/env), not in verify.
# Deviations 32 to 34: the experiments of 21 November (queue sim/jobs_suite.txt); run once their trainings are finished.
# Deviation 33 (a, b): e6_enjoy.py and e6_hub.py need env-zoo and the policies; their JSON files are not rewritten here.
PY_TRAIN ?= $(CURDIR)/sim/env/bin/python
SUITE := c6_determinism e6_gamma c2
hyperparams:
	cd sim && $(PY_TRAIN) analysis/hyperparams.py > /dev/null

analysis-suite:
	@cd sim && for s in $(SUITE); do echo "sim/analysis/$$s.py"; $(NICE) $(PY) analysis/$$s.py > /dev/null || exit 1; done

# summary.py reads every finished run under sim/llm/results/, so a run finished after the last commit enters it.
analysis-llm:
	@echo "sim/llm/summary.py"; cd sim/llm && $(NICE) $(PY) summary.py > /dev/null
	@echo "sim/llm/summary.py, five seeds (deviations 14 and 16)"; cd sim/llm && SEEDS=0:5 SUFFIX=_5 $(NICE) $(PY) summary.py > /dev/null
	@echo "sim/llm/logs_stats.py (deviation 19)"; cd sim/llm && $(NICE) $(PY) logs_stats.py > /dev/null

check:
	cd docs && $(PY) check_numbers.py
	cd article && $(PY) check_article.py
	cd paper && $(PY) check_short.py

test:
	$(PY) -m pytest -q -p no:cacheprovider tests

lint:
	ruff check src tests
	mypy

verify: analysis check test
	@git diff --stat --exit-code -- $(OUTPUTS) && echo "Every JSON file regenerated byte for byte."

verify-head:
	@d=$$(mktemp -d) && git archive HEAD -- . ':(exclude)sim/models' ':(exclude)sim/zoo_official' ':(exclude)sim/logs' \
	  | tar -x -C "$$d" && cd "$$d" && git init -q && git add -A && \
	  git -c user.name=verify -c user.email=verify@localhost commit -qm HEAD && \
	  echo "Fresh export of HEAD in $$d" && \
	  $(MAKE) --no-print-directory -f "$(CURDIR)/Makefile" -C "$$d" verify PY="$(PY)" NICE="$(NICE)"

figures:
	cd docs/figures && $(PY_LLM) build.py

docs: check
	cd docs && ./build.sh

report:
	cd report && PY=$(PY) ./build.sh

clean:
	rm -rf docs/build study/__pycache__ sim/analysis/__pycache__ tests/__pycache__ src/pineau_rl/__pycache__ src/*.egg-info build
