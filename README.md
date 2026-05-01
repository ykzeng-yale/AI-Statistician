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

Current green baseline:

- `.venv/bin/pytest` passes the current Python suite;
- `lake build` completes for the Lean library;
- strict CI runs Python smoke checks and a Lean build;
- no accepted `sorry`, `admit`, `axiom`, or unsafe placeholder is part of the
  baseline;
- seed `StatInference` modules cover asymptotics, estimators, empirical-process
  interfaces, causal interfaces, semiparametric interfaces, and benchmark
  examples;
- `StatInferBench` has deterministic JSONL seed tasks with train/dev/test
  splits and CLI support for rendering, listing, and verification;
- local premise retrieval supports indexing and deterministic search over Lean
  declarations;
- SFT/DPO/GRPO manifest generation exists for auditable training experiments;
- 14-agent registry for formalization, proving, curation, benchmarking, and training;
- worktree manager for isolated agent branches.

## Quick Start

Install Python tooling:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

Run the stricter local smoke path used by CI:

```bash
bash scripts/smoke.sh
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

Build the paper reproducibility bundle:

```bash
statlean reproducibility-bundle \
  --repo-root . \
  --blueprint config/statlean_blueprint.json \
  --paper-draft docs/paper_draft.md \
  --output artifacts/evaluation/reproducibility-bundle.json
```

Prepare post-P8 external prover baselines:

```bash
statlean external-baseline-plan \
  --benchmarks benchmarks/seeds.jsonl \
  --split test \
  --output artifacts/evaluation/external-baseline-plan.json
```

Ingest available external baseline results:

```bash
statlean external-baseline-results \
  --benchmarks benchmarks/seeds.jsonl \
  --plan artifacts/evaluation/external-baseline-plan.json \
  --output artifacts/evaluation/external-baseline-results.json
```

Build the theorem-hole no-placeholder promotion queue:

```bash
statlean theorem-hole-promotion-queue \
  --benchmarks benchmarks/seeds.jsonl \
  --output artifacts/curation/theorem-hole-promotion-queue.json
```

Preview a worktree assignment:

```bash
statlean assign-worktree --agent formalization --base main --dry-run
```

## Architecture

The system uses more than 10 specialized agents. They are coordination roles,
not autonomous authorities: agents propose artifacts, while Lean, tests, CI,
and human reviewers decide what is accepted.

The registry includes:

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

## Next Milestones

The initial P0-P8 build blueprint is complete. Post-P8 work is tracked in P9;
external baseline planning, theorem-hole proof promotion, and baseline result
ingestion are complete. The next loop is empirical-process expansion targets.

1. Harden the no-`sorry` `StatInference` library around convergence wrappers, `op(1)`/`Op(1)` calculus, asymptotic normality, and first concrete estimators.
2. Grow `StatInferBench` from seed tasks into theorem-hole, repair, proof-state, and tactic tasks with dependency-based splits.
3. Improve retrieval so baseline provers reliably use local `StatInference` lemmas.
4. Keep SFT/DPO/GRPO manifests auditable: every example, pair, and reward task must cite source benchmark and verifier artifacts.
5. Tighten strict CI around Python smoke checks, Lean builds, deterministic benchmark regeneration, schema validation, and forbidden-token scans.
6. Add heartbeat monitoring for agent id, worktree, touched files, last validation, stale branches, CI status, and blockers.
7. Keep the project human-guided: people choose theorem targets, validate statistical assumptions, approve curation, and decide when training runs are scientifically justified.

## Non-Negotiable Safety Rules

- No unreviewed new axioms.
- No accepted `sorry`, `admit`, or unsafe placeholder.
- No theorem statement weakening to make a proof easier.
- Every promoted statistics lemma must be non-vacuous and semantically meaningful.
- Lean verification is necessary but not sufficient: statistical definitions require human review.
- CI and heartbeat failures are blockers, not warnings to route around.
