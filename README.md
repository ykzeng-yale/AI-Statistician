# AI-Statistician

AI-Statistician is a Lean-grounded multi-agent system for statistical theoretical development. The goal is to build a formal Lean library, benchmark, and training loop for modern statistical inference: asymptotic linearity, empirical process arguments, M/Z-estimation, influence functions, causal estimators, and theoretical machine learning.

This repository starts from the current practical reality: Lean/mathlib has strong probability foundations, but statistical inference abstractions are still sparse. The system is therefore designed to grow a curated downstream library rather than letting models invent unreviewed axioms.

## Mission

Build a verifier-first AI system that can:

- translate textbook or paper-level statistical claims into Lean theorem skeletons;
- retrieve relevant mathlib and local `StatInference` lemmas;
- decompose hard theorems into reusable sublemmas;
- prove those sublemmas with Lean feedback;
- curate useful verified lemmas into a growing statistics library;
- train domain-adapted proof models from successful and failed proof traces.

## Current Status

Initial scaffold:

- Lean seed library under `StatInference/`;
- Python orchestration package under `src/statlean_agent/`;
- 14-agent registry for formalization, proving, curation, benchmarking, and training;
- worktree manager for isolated agent branches;
- reward and curation contracts for Lean-verified proof attempts;
- project docs for architecture, roadmap, research assessment, benchmark design, and training plan.

## Quick Start

Install Python tooling:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

If Lean and Lake are installed:

```bash
lake exe cache get
lake build
```

List the configured agents:

```bash
statlean list-agents
```

Create and inspect the seed benchmark database:

```bash
statlean seed-benchmarks --output benchmarks/seeds.jsonl
statlean list-benchmarks --input benchmarks/seeds.jsonl
statlean render-task erm_oracle_ineq_seed --input benchmarks/seeds.jsonl
```

Verify seed tasks if Lean and Lake are installed:

```bash
statlean verify-benchmarks \
  --input benchmarks/seeds.jsonl \
  --output artifacts/verification/reports.jsonl
```

Build a local premise index and training manifest:

```bash
statlean index-premises --root . --output artifacts/premise_index/local.jsonl
statlean search-premises "oracle excess risk" --index artifacts/premise_index/local.jsonl
statlean build-training-manifest \
  --benchmarks benchmarks/seeds.jsonl \
  --output artifacts/training/manifest.json
```

Preview a worktree assignment:

```bash
statlean assign-worktree --agent formalization --base main --dry-run
```

## Architecture

The system uses more than 10 specialized agents. The initial registry includes:

1. Problem Ingest Agent
2. Formalization Agent
3. Library Cartographer Agent
4. Proof Planner Agent
5. Tactic Synthesizer Agent
6. Whole-Proof Generator Agent
7. Verifier Agent
8. Error Repair Agent
9. Lemma Miner Agent
10. Library Curator Agent
11. Benchmark Generator Agent
12. Reward and Evaluation Agent
13. Trainer Agent
14. Worktree Steward Agent

Each code-writing agent gets an isolated git worktree and branch. Curated changes are merged only after Lean verification, test validation, and statistical meaning checks.

## First Milestones

1. Build the base `StatInference` Lean library and keep it no-`sorry`.
2. Formalize statistics-facing wrappers over mathlib convergence and CLT tools.
3. Prove the first reusable oracle inequality for ERM from uniform deviation.
4. Add the core interface for asymptotic linearity plus CLT implying asymptotic normality.
5. Build `StatInferBench` from extracted theorem holes and proof states.
6. Run baseline provers before training any local model.
7. Train with SFT, then DPO, then process-reward GRPO using Lean verifier feedback.

## Non-Negotiable Safety Rules

- No unreviewed new axioms.
- No accepted `sorry`, `admit`, or unsafe placeholder.
- No theorem statement weakening to make a proof easier.
- Every promoted statistics lemma must be non-vacuous and semantically meaningful.
- Lean verification is necessary but not sufficient: statistical definitions require human review.
