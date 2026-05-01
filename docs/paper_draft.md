# StatLeanAgent: Verifier-First Library Growth for Statistical Inference in Lean

## Abstract

StatLeanAgent is a human-guided, verifier-first system for building a Lean
library and proof-agent loop for statistical inference. The current prototype
targets a sparse formal domain: asymptotic statistics, empirical-process
interfaces, M/Z-estimation, causal IPW/AIPW bridges, influence-function
normality, and paper-quality estimator proof chains. The system combines a
curated `StatInference` Lean library, deterministic benchmark seeds, premise
retrieval metadata, Lean-labeled SFT/DPO/GRPO artifacts, and curator gates for
progressive lemma growth. The current checked-in build verifies 68/68 benchmark
seeds, has a passing concrete IPW/Hajek estimator proof chain, and records
artifact-backed ablation readiness for retrieval, SFT, DPO, process reward, and
curation.

## Core Claim

The contribution is infrastructure, not a claim that an LLM can already prove
arbitrary new statistical theorems autonomously. The verified claim is narrower:
given a human-designed statistical ontology and proof-carrying Lean interfaces,
the repository can produce auditable benchmark, training, curation, and
evaluation artifacts that support iterative Lean-grounded formalization.

## Contributions

1. `StatInference`: a Lean library layer for asymptotic bridges, finite-class
   uniform convergence, empirical-risk notation, estimator interfaces,
   M/Z-estimation routes, IPW/Hajek ratio linearization, AIPW product-rate
   remainders, and influence-function normality.

2. `StatInferBench`: a deterministic benchmark registry with train/dev/test
   splits, expected-premise metadata, theorem-hole tasks, and verifier reports.

3. Training artifact pipeline: checked-in SFT examples, DPO chosen/rejected
   pairs, and GRPO process-reward tasks grounded in Lean verifier output.

4. Curated library-growth loop: lemma proposals are blocked from promotion
   unless duplicate, import-minimality, non-vacuity, proof-cost, and semantic
   review gates are satisfied.

5. Paper-quality demonstration artifacts: held-out baseline report, concrete
   estimator proof-chain report, ablation-readiness report, and reproducibility
   bundle with hash-pinned artifacts and validation commands.

## System Architecture

The system is organized around a strict loop:

1. Human statistician selects theorem targets and approves definitions.
2. Formalization agents propose Lean theorem statements and proof skeletons.
3. Premise retrieval indexes `mathlib`-style local declarations in
   `StatInference`.
4. Prover agents generate proof attempts or theorem-hole completions.
5. The Lean verifier accepts, rejects, or diagnoses attempts.
6. Evaluation code records pass rates, rewards, premise recall, and failure
   categories.
7. Training data builders emit SFT/DPO/GRPO artifacts from verified traces.
8. Curator gates prevent unverified or vacuous lemma promotion.
9. The executable blueprint selects the next milestone during heartbeat loops.

## Current Evaluation Snapshot

The checked-in artifacts record the following current state:

- 68 seed benchmark tasks are materialized and verified.
- The seed-registry baseline accepts 68/68 current benchmark tasks.
- The held-out split report covers 2/2 held-out tasks with pass rate 1.0.
- The concrete IPW/Hajek estimator chain passes with 4/4 proof components.
- The training manifest contains 65 no-placeholder SFT examples, 65 DPO pairs,
  and 68 GRPO process-reward tasks.
- The curation reports contain 9/9 passing proposal, non-vacuity, and proof-cost
  gate checks, while three theorem-hole-derived candidates remain blocked from
  promotion because they require completed no-placeholder proofs.
- The ablation-readiness report records five ready system components:
  retrieval, SFT, DPO, process reward, and curation.

These numbers are seed-system readiness metrics. They are not a replacement for
future trained-model comparisons against external Lean provers.

## Reproducibility

Use the following commands from the repository root:

```bash
PYTHONPATH=src .venv/bin/python -m pytest
PYTHON=.venv/bin/python bash scripts/smoke.sh
lake build
PYTHONPATH=src .venv/bin/python -m statlean_agent.cli blueprint-status --blueprint config/statlean_blueprint.json
rg -n "\b(sorry|admit|unsafe)\b|^\s*axiom\b" StatInference -g '*.lean'
```

The final command is expected to return no matches and may therefore exit with
status 1. The checked-in reproducibility bundle records artifact hashes and the
same validation commands in `artifacts/evaluation/reproducibility-bundle.json`.

## Limitations

- The system currently proves a curated seed library and benchmark suite, not
  arbitrary textbook-scale statistical inference from first principles.
- Some theorem-hole tasks intentionally allow scoped placeholders as benchmark
  skeletons; these are excluded from no-placeholder SFT examples and blocked by
  curation gates.
- The current ablation artifact is a system-component readiness scaffold, not a
  trained-model ablation table.
- New statistical definitions still require human semantic review even when Lean
  accepts the code.

## Next Research Steps

1. Add external Lean prover baselines on `StatInferBench`.
2. Replace theorem-hole placeholders with promoted no-placeholder lemmas.
3. Expand empirical-process primitives toward bracketing, VC, and Donsker-style
   theorem families.
4. Run small-domain SFT and DPO adapters against the checked-in training
   manifest.
5. Add process-reward GRPO experiments only after verifier throughput and
   baseline comparisons are stable.
