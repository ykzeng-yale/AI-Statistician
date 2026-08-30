# Statlib 4.33 Migration Audit

## Question

Can the canonical EmpericalProcessLEAN/StatInference foundation move from its
current Statlib pin to fetched Statlib `origin/main` without weakening local
Lean and kernel authority?

## Snapshots

The trusted project remains:

- EmpericalProcessLEAN `4cec7860c926feebd4cbcdaccedb63b2156972dd`;
- Lean `v4.30.0`;
- Mathlib `81343555dae873c8de2de2b27bbabf7bc4d8d97a`;
- Statlib `6575d611b5d32ef6013e9560d30b1a82a1972fb6`.

The isolated candidate used:

- fetched Statlib `origin/main` at
  `01d2a03770455f5c775bb25c57e7fbb8e1eaf8d8`;
- Lean `v4.33.0-rc2` declared by that snapshot;
- Mathlib `3ef2c2e23a8b5a46554fa771969b89287972b616` declared by that snapshot.

Only `lean-toolchain` and the Mathlib/Statlib revisions were changed in a
detached temporary EmpericalProcessLEAN worktree. No canonical source or pin
was edited.

## Results

`lake build Statlib` succeeded in the candidate environment with 2,825 jobs.
This establishes that the fetched Statlib snapshot and its declared toolchain
are internally buildable.

`lake build` for the combined StatInference project failed with 207 Lean error
lines and 41 failed required targets. Failures were distributed across
probability measures, probability theory, empirical processes, optimization,
matching, causal inference, estimators, experiments, and asymptotic statistics.
Representative incompatibilities included changed function/equivalence
elaboration, eta/definitional equality changes, removed declaration names,
and tactics that no longer closed their goals.

The failed required targets were:

- `StatInference.Matching.WDSM.FiniteCellShareRatioConvergence`
- `StatInference.Matching.PopulationSelectionDensityDesignCrossMoment`
- `StatInference.Matching.WDSM.SlutskyAlgebra`
- `StatInference.ProbabilityMeasure.InfiniteProduct`
- `StatInference.Matching.FiniteCellShareRatioConvergence`
- `StatInference.Matching.WDSM.BootstrapUniformResamplingLaw`
- `StatInference.Matching.WDSM.PopulationSelectionDensityDesignResidualOrthogonality`
- `StatInference.Matching.WDSM.PopulationSelectionDensityDesignQuadraticVariation`
- `StatInference.Matching.WDSM.PopulationSelectionDensityDesignCrossMoment`
- `StatInference.Matching.WDSM.TriangularMartingaleArrayConditionalCharacteristicFromFiltration`
- `StatInference.Matching.PopulationSelectionDensityDesignQuadraticVariation`
- `StatInference.Matching.SlutskyAlgebra`
- `StatInference.Matching.WDSM.FiniteCellIndicatorCLTInterfaces`
- `StatInference.ProbabilityTheory.ENNRealSeries`
- `StatInference.ProbabilityMeasure.ProductMeasure`
- `StatInference.ProbabilityMeasure.Rademacher`
- `StatInference.ProbabilityMeasure.GaussianMoments`
- `StatInference.Optimization.BrunnMinkowski`
- `StatInference.Optimization.OrthonormalCoordinateTransport`
- `StatInference.Optimization.BubeckEldanLogAffine`
- `StatInference.Optimization.ZerothOrderLowerBound`
- `StatInference.ProbabilityMeasure.KolmogorovExtension.RegularContent`
- `StatInference.EmpiricalProcess.OuterExpectation`
- `StatInference.ProbabilityTheory.BoundedSupremumBorelCantelli`
- `StatInference.ProbabilityMeasure.KolmogorovChentsov.Chaining`
- `StatInference.ProbabilityTheory.IndependentEventUnion`
- `StatInference.EmpiricalProcess.EllInfty`
- `StatInference.ProbabilityTheory.ConvergenceInProbabilityMetric`
- `StatInference.Experiments.TwoStageERM`
- `StatInference.Optimization.RelativePolarTransport`
- `StatInference.EmpiricalProcess.BrownianBridge`
- `StatInference.Optimization.EntropicDirectionalDerivatives`
- `StatInference.ProbabilityTheory.ExponentialMaxima`
- `StatInference.Optimization.SelfConcordancePolarization`
- `StatInference.AsymptoticStatistics.MaximumLikelihood`
- `StatInference.Optimization.Basic`
- `StatInference.AsymptoticStatistics.LocationEstimators`
- `StatInference.Estimator.ZEstimator`
- `StatInference.Causal.PotentialOutcomes`
- `StatInference.EmpiricalProcess.BracketingPrimitive`
- `StatInference.EmpiricalProcess.CoveringPrimitive`

After deleting the temporary worktree, `lake build` succeeded for the unchanged
canonical project with 9,843 jobs.

## Decision

Do not promote Statlib `01d2a037` into active proof authority. This would make
the Formalizer retrieve or emit declarations against a foundation on which the
combined project does not elaborate.

Keep the current Statlib pin as the only importable premise authority. The
newer upstream snapshot remains useful for literature-like discovery, API
comparison, and explicit port planning, but every candidate taken from it must
be labeled non-importable and re-elaborated in the active project before it can
be proof evidence.

Commit `506e5ed0` implements that boundary under the stable corpus identity
`statlib_upstream_discovery`; its exact commit/tree are included in Formalizer
tool-environment authorization while active-scoped retrieval still excludes it.

This is a compatibility result, not a reason to add 41 hand-written repairs or
Lean grammar rules to AI-Statistician. A future migration should be a dedicated
library port with whole-project compilation as its acceptance gate.

## Evidence Boundary

No model, evaluator, or product task was called. No theorem was proved, no
consumed task was changed, and capability credit remains unchanged at `7/113`;
development-panel exact Lean closure remains `0/2`.
