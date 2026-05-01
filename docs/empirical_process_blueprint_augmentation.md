# Empirical Process Blueprint Augmentation

This note refines the current progressive blueprint against the textbook route
from Vapnik's statistical learning theory and van der Vaart--Wellner's weak
convergence and empirical-process theory.  It is intentionally additive: active
P10.M1 work is touching `StatInference/EmpiricalProcess/Complexity.lean`,
`src/statlean_agent/benchmarks.py`, and `benchmarks/seeds.jsonl`, so this file
does not modify those paths.

## Goal Clarification

The long-term target is not to reimplement mathlib's measure theory, topology,
or probability foundations.  The target is a self-contained downstream
`StatInference` empirical-process and theoretical-ML layer:

```text
mathlib probability/topology/measure theory
  -> StatInference primitive statistical definitions
  -> finite sample and asymptotic empirical-process theorems
  -> GC/Donsker/ERM/M/Z-estimator master theorems
  -> concrete learning and statistical-inference applications
```

"Self-contained" means that `StatInference` should not assume empirical-process
conclusions as black-box certificate fields when those conclusions are the
theorem being claimed.  It is acceptable to assume mathematically meaningful
primitive conditions such as iid sampling, measurability, bounded envelope,
finite bracketing number, finite VC dimension, entropy integrability, or
stochastic equicontinuity hypotheses.

## Current Blueprint Interpretation

The current P0-P9 route is useful, but some phase names are stronger than the
implemented mathematics:

- `P2 Empirical Process And GC Library` should be interpreted as
  "empirical-process interfaces, deterministic ERM/GC handoffs, and
  proof-carrying certificate scaffolds."  It is not a full bottom-up
  formalization of the GC/Donsker theory in van der Vaart--Wellner Part 2.
- `P9 Empirical-process expansion targets` scoped bracketing, VC-subgraph, and
  Donsker interfaces.  These are proof-carrying handoff points, not primitive
  constructor theorems.
- `P10` should become the transition from scaffolded interfaces to
  textbook-derived theorem families.  It should not stop at adding benchmark
  seeds for certificate projections.

## Textbook Dependency Map

Vapnik's route is the learning-theory route:

```text
risk functional and empirical risk
  -> ERM consistency
  -> uniform one-sided convergence
  -> VC entropy/capacity
  -> distribution-independent bounds and SRM
```

van der Vaart--Wellner's route is the empirical-process route:

```text
outer probability and weak convergence
  -> empirical measures/processes indexed by function classes
  -> symmetrization and maximal inequalities
  -> GC via bracketing or uniform entropy
  -> Donsker via bracketing or uniform entropy
  -> VC/VC-subgraph/entropy examples and permanence
  -> M-estimators, Z-estimators, delta method, bootstrap
```

The correct formalization strategy is to build a theorem atlas and dependency
DAG, then formalize vertical slices.  It is not efficient to formalize every
textbook theorem sequentially.

## Proposed Blueprint Augmentation

### P10: Interface-To-Theorem Transition

Keep P10 focused on converting P9 interfaces into benchmarked theorem targets.
Extend it with explicit artifact gates:

- textbook theorem atlas rows for bracketing GC, VC/VC-subgraph entropy, and
  Donsker routes;
- non-vacuity witnesses for each active interface family;
- benchmark seeds tied to interface-family tags;
- checked-in verification and evaluation artifacts regenerated after task-count
  changes;
- blueprint status promoted only after tests, smoke, and `lake build`.

Suggested milestones:

- `P10.M1`: Bracketing GC benchmark seeds and non-vacuity witness.
- `P10.M2`: VC-subgraph benchmark seeds and combinatorial obligation stubs.
- `P10.M3`: Donsker bridge seeds and asymptotic-normality handoff.
- `P10.M4`: Textbook theorem atlas and dependency graph for empirical-process
  routes.
- `P10.M5`: External prover evaluation slice on the new empirical-process
  tasks.

### P11: Primitive Empirical Sample Model

Build the real probabilistic substrate currently abstracted away by deterministic
`empiricalRisk : Nat -> Index -> Real` fields:

- finite sample vectors `Fin n -> Observation`;
- empirical average and empirical measure wrappers over mathlib product
  measures;
- iid coordinate projections and product-measure wrappers;
- measurable and integrable function-class assumptions;
- one-function LLN/concentration wrappers based on mathlib where available.

Promotion gate: at least one concrete sample-space example proves a non-vacuous
empirical-average convergence or concentration statement without new axioms.

### P12: Self-Contained Finite-Class GC

This is the first bottom-up empirical-process vertical slice:

```text
single-function LLN/concentration
  -> finite union over a finite function class
  -> uniform deviation over the class
  -> finite-class GC
  -> ERM consistency/high-probability bound
```

This phase replaces the current finite-class certificate interface with a
constructor theorem from primitive finite-class assumptions.

### P13: Bracketing GC Route

Formalize the van der Vaart--Wellner bracketing route:

- bracket objects `[l, u]` with pointwise membership;
- `L1(P)` bracket width;
- bracketing number and finite bracketing assumptions;
- finite-bracket approximation theorem;
- finite bracketing number for every epsilon implies GC;
- classical CDF indicator-cell example as a non-vacuity/application target.

This should be prioritized before full VC/Donsker because the GC bracketing
proof is elementary relative to the other routes: finite approximation plus LLN.

### P14: Uniform Entropy, Symmetrization, And Maximal Inequalities

Build the route needed for uniform covering-number GC and later Donsker:

- Rademacher signs and ghost samples;
- symmetrization for expectations and probabilities;
- finite/maximal inequalities needed by the textbook proofs;
- uniform entropy wrappers over mathlib covering-number APIs;
- covering-number GC constructor theorem.

This phase is allowed to reuse existing mathlib concentration, covering, and
weak convergence primitives, but should expose `StatInference`-level APIs that
match empirical-process textbook statements.

### P15: VC And VC-Subgraph Route

Build the combinatorial capacity layer:

- set-class shattering and growth functions;
- VC index/dimension wrappers;
- Sauer-style growth bound;
- indicator-class covering/entropy consequences;
- VC-subgraph class definitions for real-valued functions;
- GC constructor theorem for bounded/measurable VC-subgraph classes.

Promotion gate: include concrete examples such as intervals/cells or threshold
sets, not only abstract VC assumptions.

### P16: Donsker Route

Treat full Donsker theory as a later, deeper layer:

- empirical process as a random element in a bounded-function space;
- finite-dimensional convergence wrappers;
- asymptotic tightness/equicontinuity interfaces;
- bracketing and uniform-entropy Donsker constructor theorems;
- permanence results for Lipschitz transforms, products, unions, and convex
  hulls where feasible;
- finite-class Donsker as the first concrete theorem.

This phase should not block GC/ERM progress.  Donsker is harder because it
requires weak convergence in function spaces, tightness, and measurability
management.

### P17: Downstream Statistical Inference Applications

Connect the empirical-process layer to the statistics layer:

- ERM consistency from one-sided/two-sided uniform convergence;
- M-estimator argmin consistency and rate routes;
- Z-estimator linearization and stochastic equicontinuity;
- functional delta method applications;
- bootstrap targets;
- causal/IPW/AIPW examples using the real GC/Donsker constructors rather than
  only abstract bridge fields.

## Parallel Workstreams

The following can run while another agent works on P10.M1 bracketing code, with
low conflict risk:

1. Textbook theorem atlas extraction in `docs/` or `artifacts/research/`.
2. Mathlib API audit for iid samples, product measures, LLN, concentration,
   covering numbers, weak convergence, and `Lp` norms.
3. Design notes for `P11` primitive empirical sample model.
4. Benchmark taxonomy updates that do not edit `benchmarks/seeds.jsonl` until
   the current task-count drift is resolved.
5. New theorem-statement drafts in documentation, not Lean source, for
   bracketing GC and finite-class GC constructor theorems.

Avoid touching these paths until current P10.M1 edits are synchronized:

- `StatInference/EmpiricalProcess/Complexity.lean`
- `src/statlean_agent/benchmarks.py`
- `benchmarks/seeds.jsonl`
- checked-in benchmark/evaluation artifacts affected by seed count

## Immediate Promotion Checklist For Active P10.M1

The current working tree appears to have partial P10.M1 progress.  Before
promoting it:

- regenerate verification reports and benchmark/evaluation artifacts for the
  current seed count;
- regenerate `artifacts/evaluation/empirical-process-targets.json` so the
  bracketing row records `ready_for_lemma_targets`;
- update tests that still expect bracketing to need a seed;
- update the blueprint evidence for P10.M1;
- fix Lean lint warnings in `Complexity.lean`;
- rerun `.venv/bin/pytest`, `PYTHON=.venv/bin/python bash scripts/smoke.sh`, and
  `lake build`.

