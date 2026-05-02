# Empirical Process Blueprint Augmentation

This note refines the current progressive blueprint against the textbook route
from Vapnik's statistical learning theory and van der Vaart--Wellner's weak
convergence and empirical-process theory.  P10 is now complete: bracketing,
VC-subgraph, and Donsker interfaces have benchmark evidence, and P10.M5 records
the external-prover evaluation slice that future model adapters must target.

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
- `P10` completed the transition from scaffolded interfaces to benchmarked
  empirical-process theorem targets: bracketing, finite L1 bracketing,
  VC-subgraph obligations, Donsker normality handoff, and an external-prover
  evaluation slice are all tracked in artifacts.
- `P11` starts the textbook-grounded promotion step: every next theorem target
  should be source-linked to VdV&W or Vapnik text, mapped to current Lean
  declarations, and marked with semantic risks before formalization.

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

Completed milestones:

- `P10.M1`: Bracketing GC benchmark seeds and non-vacuity witness.
- `P10.M2`: VdV&W finite-bracketing GC deterministic core.
- `P10.M3`: VC-subgraph benchmark seeds and combinatorial obligation stubs.
- `P10.M4`: Donsker bridge seeds and asymptotic-normality handoff.
- `P10.M5`: External prover evaluation slice on the new empirical-process
  tasks.

### P11: Textbook-Grounded Theorem Promotion

Before building more primitive probability infrastructure, create an auditable
theorem atlas from the local VdV&W markdown/PDF sources:

- source-linked theorem rows for finite bracketing GC, VC/VC-subgraph examples,
  maximal inequalities, and Donsker constructor routes;
- mapping from textbook statements to existing `StatInference` declarations and
  benchmark seeds;
- missing Lean primitives and mathlib dependencies;
- semantic-risk notes for hidden measurability, separability, outer-probability,
  tightness, and envelope assumptions;
- AXLE extraction/checking tasks recorded only as auxiliary evidence, with local
  Lake remaining the acceptance authority.

Promotion gate: every theorem-statement candidate must include a textbook source
reference, current Lean dependency map, non-vacuity plan, and explicit list of
assumptions that are still abstract.

### P12: Primitive Empirical Sample Model

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

### P13: Self-Contained Finite-Class GC

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

### P14: Bracketing GC Route

Formalize the van der Vaart--Wellner bracketing route:

- bracket objects `[l, u]` with pointwise membership;
- `L1(P)` bracket width;
- bracketing number and finite bracketing assumptions;
- finite-bracket approximation theorem;
- finite bracketing number for every epsilon implies GC;
- classical CDF indicator-cell example as a non-vacuity/application target.

This should be prioritized before full VC/Donsker because the GC bracketing
proof is elementary relative to the other routes: finite approximation plus LLN.

### P15: Uniform Entropy, Symmetrization, And Maximal Inequalities

Build the route needed for uniform covering-number GC and later Donsker:

- Rademacher signs and ghost samples;
- symmetrization for expectations and probabilities;
- finite/maximal inequalities needed by the textbook proofs;
- uniform entropy wrappers over mathlib covering-number APIs;
- covering-number GC constructor theorem.

This phase is allowed to reuse existing mathlib concentration, covering, and
weak convergence primitives, but should expose `StatInference`-level APIs that
match empirical-process textbook statements.

### P16: VC And VC-Subgraph Route

Build the combinatorial capacity layer:

- set-class shattering and growth functions;
- VC index/dimension wrappers;
- Sauer-style growth bound;
- indicator-class covering/entropy consequences;
- VC-subgraph class definitions for real-valued functions;
- GC constructor theorem for bounded/measurable VC-subgraph classes.

Promotion gate: include concrete examples such as intervals/cells or threshold
sets, not only abstract VC assumptions.

### P17: Donsker Route

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

### P18: Downstream Statistical Inference Applications

Connect the empirical-process layer to the statistics layer:

- ERM consistency from one-sided/two-sided uniform convergence;
- M-estimator argmin consistency and rate routes;
- Z-estimator linearization and stochastic equicontinuity;
- functional delta method applications;
- bootstrap targets;
- causal/IPW/AIPW examples using the real GC/Donsker constructors rather than
  only abstract bridge fields.

## P11.M1 Status Update

`P11.M1` is complete as a source-linked audit artifact, not as a theorem
completion claim.  The checked-in inventory at
`artifacts/research/vdvw-theorem-inventory.json` records seven VdV&W theorem
cards across bracketing, VC-subgraph, and Donsker targets.  Every row maps a
local markdown anchor to current Lean declarations, benchmark seeds, missing
definitions, semantic risks, and next actions.

The inventory deliberately marks every row as
`blocked_pending_primitives_or_review`.  This prevents bridge/certificate
interfaces from being treated as exact textbook formalizations before the
primitive definitions and semantic assumptions are present.

## P11.M2 Status Update

`P11.M2` is complete as a statement-candidate artifact, not as an exact theorem
formalization.  The checked-in artifact at
`artifacts/research/vdvw-bracketing-gc-statement-candidates.json` records three
tracks for VdV&W Theorem 2.4.1:

- the compiled dependency-minimal bridge already represented by
  `L1BracketingSequenceRoute.toGlivenkoCantelliClass`;
- the next primitive `L1(P)` bracketing-number constructor target;
- the exact outer-almost-sure textbook target, still blocked by missing
  outer-probability and empirical-measure semantics.

Every candidate records source anchors, target Lean names, proof obligations,
benchmark seeds, local Lake hooks, optional AXLE hooks, semantic risks, and a
promotion gate.

## P11.M3 Status Update

`P11.M3` is complete as a proof-obligation artifact, not as any VC or Donsker
theorem-completion claim.  The checked-in artifact at
`artifacts/research/vdvw-vc-donsker-proof-obligations.json` records five guarded
tracks:

- VC set-class entropy for VdV&W Theorem 2.6.4;
- VC-subgraph envelope-scaled entropy for Theorem 2.6.7;
- uniform-entropy Donsker for Theorem 2.5.2;
- bracketing Donsker for Theorem 2.5.6;
- VC-subgraph Donsker with pre-Gaussian and weak-tail assumptions for
  Theorem 2.6.8.

The main guardrail is explicit: GC certificates, VC entropy obligations, and
Donsker weak-convergence evidence are different layers and must not be collapsed
into one certificate.

## Parallel Workstreams

The following can run while another agent works on P12 primitive empirical
process semantics,
with low conflict risk:

1. Textbook theorem atlas extraction in `docs/` or `artifacts/research/`.
2. Mathlib API audit for iid samples, product measures, LLN, concentration,
   covering numbers, weak convergence, and `Lp` norms.
3. Design notes for `P12` primitive empirical sample model.
4. Benchmark taxonomy updates that do not edit `benchmarks/seeds.jsonl` until
   the current task-count drift is resolved.
5. New theorem-statement drafts in documentation, not Lean source, for
   bracketing GC and finite-class GC constructor theorems.

Avoid touching these paths until current P12.M1 edits are synchronized:

- `StatInference/EmpiricalProcess/Complexity.lean`
- `src/statlean_agent/benchmarks.py`
- `benchmarks/seeds.jsonl`
- checked-in benchmark/evaluation artifacts affected by seed count

## Immediate Promotion Checklist For Active P12.M1

Before promoting P12.M1:

- design checked-in primitive empirical sample and outer-convergence semantics;
- map VdV&W GC/Donsker theorem-card gaps to concrete Lean API signatures;
- specify theorem-hole seeds for empirical measure, outer supremum norm,
  outer probability, iid sample model, and endpoint SLLN handoff;
- keep all files in English and avoid committing local textbook assets or API
  secrets;
- rerun `.venv/bin/pytest`, `PYTHON=.venv/bin/python bash scripts/smoke.sh`, and
  `lake build`.
