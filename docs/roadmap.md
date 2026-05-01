# Roadmap

## Phase 0: Repository and Toolchain

Target: 1 to 2 weeks.

Deliverables:

- Lake project pinned to Lean/mathlib.
- Python package with typed contracts and CLI.
- CI for Python tests and optional Lean build.
- Agent registry with at least 12 roles.
- Worktree strategy for code-writing agents.

Go/no-go:

- `pytest` passes.
- `statlean list-agents` works.
- `lake build` works on a machine with Lean and mathlib cache.

## Phase 1: Seed Lean Library

Target: month 1.

Deliverables:

- `StatInference.Asymptotics.Basic`
- `StatInference.Asymptotics.Op`
- `StatInference.Asymptotics.AsymptoticNormal`
- `StatInference.Estimator.Basic`
- `StatInference.Estimator.AsymptoticLinear`
- first deterministic ERM oracle inequality.

Go/no-go:

- no `sorry`;
- no unreviewed axioms;
- no theorem statement that hides the target conclusion in assumptions.

## Phase 2: Asymptotic Inference Backbone

Target: months 2 to 3.

Deliverables:

- mathlib-backed wrappers for convergence in probability and distribution;
- `op(1)` and `Op(1)` calculus;
- Slutsky and continuous mapping theorem wrappers;
- concrete bridge from asymptotic linearity plus CLT to asymptotic normality.

Initial statistical theorem:

```text
asymptotic linearity + CLT + negligible remainder
=> asymptotic normality
```

## Phase 3: First Concrete Estimator

Target: months 3 to 4.

Recommended target: Hajeck/IPW ratio estimator for ATE under high-level assumptions.

Deliverables:

- potential outcome interface;
- overlap and unconfoundedness assumption interfaces;
- ratio linearization lemma;
- empirical average notation;
- influence-function statement;
- asymptotic normality theorem under abstract CLT conditions.

## Phase 4: StatInferBench

Target: months 4 to 5.

Deliverables:

- JSONL benchmark format;
- theorem-hole tasks;
- repair tasks;
- proof-state/tactic tasks;
- train/dev/test split by theorem dependency, not just random split.

Metrics:

- pass@1, pass@8, pass@32;
- valid tactic rate;
- local lemma usage;
- unknown identifier rate;
- verifier calls per solved theorem;
- proof length;
- curation acceptance rate.

## Phase 5: Baseline Evaluation

Target: month 5.

Baselines:

- DeepSeek-Prover-V2 7B;
- Kimina prover models;
- ReProver/LeanDojo baseline;
- whole-proof generation without retrieval;
- retrieval-augmented proof search.

Decision criterion:

- If baseline models cannot use local `StatInference` lemmas, prioritize retrieval and SFT before RL.

## Phase 6: Domain Training

Target: months 5 to 6.

Training order:

1. SFT on local proof traces and adjacent mathlib probability proofs.
2. DPO on Lean-labeled good/bad attempts.
3. GRPO with process rewards from Lean.

Do not start RL before the benchmark and curation gates exist.

## 12-Month Ambition

By month 12, the system should support:

- asymptotic normality for sample mean style examples;
- an abstract M-estimation or Z-estimation consistency theorem;
- an IPW/AIPW theorem under high-level assumptions;
- a first `StatInferBench` paper-quality benchmark;
- a domain-adapted prover that improves over general Lean provers on held-out statistical inference tasks.

