# Native Agentic Scientist HC0 Development Observation

Prospective 2026-10-15 condition requested by the user to understand the actual
Sakana v3 modules before further adaptation. Not an official publication study,
blind discovery, complete research-E2E test, or rerun of any consumed evaluation.

- Upstream: unmodified `2b8aa39285c35aaca3b0e06dd121061ef8a2d854`.
- Public task: `benchmarks/research_l0_questions_20260814.json`, question
  `heteroskedastic_covariance_known_result`; the entire exposed question is copied.
- Coding host: OpenCode 1.18.29 through Headless
  `93cd9b06b85f848af1308c41e018991b33907c5e`, installed locally for this condition.
- Model: existing local Qwen3-4B-Instruct-2507 Q4_K_M; deployment asset hashes and
  server arguments from the recorded October 3 deployment, with fresh seed
  2026101506. Context 131072, one slot, temperature 0.7, top-p 0.8, top-k 20,
  min-p 0; host output limit 16384. These are configured values, not captured
  per-request wire settings; see the qualification limit in the final record.
  No cloud provider or credential is configured.
- Phase: native `agsci investigate`, stock idea and execution prompts, one idea
  cycle, at most two official candidate evaluations, upstream two idea-generation
  attempts and default idea/run timeouts. Paper, GPU and container mode disabled.
  This phase does not claim sealed isolation or a complete publication workflow.
- Fresh HOME and memory; no previous solutions, evaluator bank or archived
  held-out material supplied. Native execution is local and is not an OS sandbox.
- Seed: an explicit unimplemented callable, not an operator-authored answer.
- Public scorer: six deterministic generated full-rank designs compared with
  statsmodels 0.14.6 OLS HC0. Scores count implementation agreement, never proof,
  assumption sufficiency, scientific originality or simulation validity.
- Operator review after termination describes actual theory/code/simulation
  artifacts and module behavior. It is AI-assisted qualitative analysis, not a
  new independently calibrated gold grade. Preserve all logs and unsuccessful
  outputs; do not edit model source, repair packets or retry for a passing score.

The task adapter below only stages the existing public brief and the upstream
file interface. It does not change production code or the upstream controller.
This observation informs a module-by-module comparison with the statistical
integration. It does not establish a live comparison of that custom profile;
such an arm needs its own declared, matched condition. One draw cannot estimate
efficacy or separate host/model/harness effects.

## Pre-Inference Environment Correction

The first launch exited 2: both upstream idea-launch attempts failed on macOS
Bash 3's missing `mapfile`, before Headless or any model request. Keep its
`results/` directory unchanged. GNU Bash 5.3 was built locally from the official
`https://ftp.gnu.org/gnu/bash/bash-5.3.tar.gz`, SHA-256
`0d5cd86965f869a26cf64f4b71be7b96f90a3ba8b3d74e27e8e9d9d5550f31ba`.
The next invocation uses that executable through PATH and fresh `results_bash5/`.
No upstream or candidate source, question, model setting or criterion changed.
The original upstream NumPy 2.4.2 and SciPy 1.17.1 versions were restored after
preparation briefly installed older pins; statsmodels 0.14.6 is the added public
reference dependency. No inference occurred during either installation.

## Prospective Prompt-Delivery Contrast

The Bash-5 run reached the model but both idea attempts stopped without tool use
or required files. Each requested the content of `idea_prompt.md`. Post-run host
inspection reports `toolcall=true` and enabled read/write/edit tools; it does not
prove exact wire-level tool receipt. Upstream passes only a file-reference sentence
to OpenCode, while it passes a prompt file directly for Claude/Codex/Gemini.
Pinned Headless already supports reading that file for OpenCode as well.

A fresh developmental contrast keeps the stock scientific prompts, question,
evaluator, model, seed and opportunity limits. Its only upstream change is adding
`opencode` to `agent_streams_prompt_file`, in a separate local checkout. It uses
a fresh HOME, task and memory at `/private/tmp/ai-statistician-v3-hc0-inline-20261015`.
The canonical submodule stays unchanged. This is explicitly **transport-adapted
v3**, not unmodified v3, our complete statistical integration or a successful
retry of the previous result. Its outcomes remain separate; no output is patched.

Preparation:

```sh
.venv/bin/python benchmarks/agentic_scientist_hc0_20261015/prepare.py \
  --destination /private/tmp/ai-statistician-v3-hc0-20261015
```

The live working directory is outside this repository so the stock host does not
inherit our project AGENTS.md. It is retained at the above path and copied to
`runs/agentic_scientist_live_20261015/` after termination for durable records.
Final outcomes are in [observed_results.json](observed_results.json) and the
[module/scientific interpretation](analysis.md). No candidate evaluation or
complete research result was produced. Existing scientific records and their
scores are unchanged. The owned local model server has been stopped.

The executed stock command, from the pinned upstream directory, was:

```sh
.venv/bin/agsci investigate \
  agent.name=opencode agent.model=local-qwen/Qwen3-4B-Instruct-2507 \
  paths.task_dir=/private/tmp/ai-statistician-v3-hc0-20261015/task \
  paths.results_dir=/private/tmp/ai-statistician-v3-hc0-20261015/results_bash5 \
  execution.max_idea_cycles=1 execution.max_program_evals_per_attempt=2 \
  container.enabled=false paper.enabled=false run_id=hc0_native_stock_bash5_20261015
```

It ran with an empty inherited environment plus fresh task HOME, LANG, local
Bash/Node/Headless/Python PATH, `HEADLESS_BIN`, `TASK_PYTHON` and
`AGENTIC_TEMP_ROOT=/private/tmp`. For the contrast, the patched temporary checkout
used `.venv/bin/python -m src.agsci.main investigate`, the separate inline task
and result roots, and `run_id=hc0_native_inline_20261015`. These are historical
commands, not instructions to resume or overwrite their consumed directories.
