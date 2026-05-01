# Roadmap

## Current Green Baseline

The repository has a usable verifier-first baseline:

- Python tests pass locally through the repo virtualenv: `.venv/bin/pytest`.
- Lean builds locally with `lake build`.
- CI runs a strict Python smoke path and a Lean build path.
- `StatInference/` contains seed Lean modules for asymptotics, estimators,
  empirical process interfaces, causal interfaces, semiparametric interfaces,
  and benchmark-facing examples.
- `StatInferBench` has deterministic JSONL seed tasks with train/dev/test
  splits and CLI support for regeneration, rendering, listing, and verification.
- Retrieval is available through local premise indexing and deterministic
  premise search.
- Training manifest generation exists for SFT, DPO, and GRPO experiments.

This baseline is only green if Python tests, benchmark determinism checks, and
Lean build all pass. Do not promote documentation, code, or training artifacts
that describe an unverified state.

## Executable Blueprint

The detailed phase plan is machine-readable in
`config/statlean_blueprint.json`. Heartbeats and workers must query it with:

```bash
PYTHONPATH=src python -m statlean_agent.cli blueprint-status --blueprint config/statlean_blueprint.json
```

The current rule is: if repository health and CI are green, continue the first
non-`done` milestone in the first non-`done` phase. Monitoring alone is not
progress. Each loop should either patch a failure, implement the next milestone,
run the evaluation needed to promote it, or report a concrete blocker.

## Next Milestones

### 1. Harden `StatInference`

Keep the library no-`sorry` and no unreviewed axioms while expanding:

- mathlib-backed wrappers for convergence in probability and distribution;
- `op(1)` and `Op(1)` calculus;
- Slutsky and continuous mapping theorem wrappers;
- asymptotic linearity plus CLT implying asymptotic normality;
- first concrete estimator path, preferably Hajek/IPW ratio ATE under
  high-level overlap and unconfoundedness assumptions.

### 2. Grow `StatInferBench`

Move beyond seed projection tasks into theorem-hole, repair, proof-state, and
tactic tasks. Splits must be by theorem dependency, not random rows.

Track at minimum:

- pass@1, pass@8, pass@32;
- valid tactic rate;
- local `StatInference` lemma usage;
- unknown identifier rate;
- verifier calls per solved theorem;
- proof length;
- curation acceptance rate.

### 3. Improve Retrieval

Make retrieval useful enough that baseline provers can find local statistics
lemmas without hand-prompting.

Required work:

- index theorem names, types, modules, line numbers, tags, and dependencies;
- record which retrieved premises were used by successful proofs;
- evaluate retrieval-augmented proof search against whole-proof generation;
- prioritize retrieval and SFT before RL if models ignore local lemmas.

### 4. Make Training Manifests Auditable

The training path is SFT, then DPO, then GRPO. Do not start RL before benchmark
and curation gates exist.

Manifest requirements:

- SFT examples come from verified proof traces and adjacent mathlib probability
  tasks.
- DPO pairs use Lean-labeled accepted/rejected attempts.
- GRPO tasks use process rewards from Lean feedback.
- Every manifest records source benchmark hashes, verifier status, base model,
  and reward configuration.

### 5. Tighten CI And Heartbeats

Strict CI should fail on:

- Python test failures or smoke-script failures;
- Lean build failures;
- nondeterministic benchmark regeneration;
- schema-invalid benchmark, verifier, or training artifacts;
- new unapproved `sorry`, `admit`, `axiom`, or `unsafe` usage.

Heartbeat monitoring should report:

- agent id, worktree or branch, current task, changed files, and last validation;
- stale agents or worktrees;
- CI status, benchmark freshness, manifest freshness, and blocker notes;
- unexpected edits outside an agent's allowed paths.

### 6. Keep The System Human-Guided

Lean checks formal validity relative to definitions and assumptions. It does not
decide whether a statistical definition is useful, whether a theorem is
non-vacuous, or whether a training run should be trusted.

Humans must approve:

- target theorem selection;
- statistical assumptions and theorem strength;
- promotion of lemmas into `StatInference`;
- benchmark split policy and held-out sets;
- baseline comparisons and training launch decisions.

## 12-Month Ambition

By month 12, the system should have a no-`sorry` statistics library, a
paper-quality `StatInferBench`, retrieval-augmented prover baselines, and a
domain-adapted prover that improves over general Lean provers on held-out
statistical inference tasks.
