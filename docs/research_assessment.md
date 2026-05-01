# Research Assessment

This project is viable because several prerequisites have matured, but the statistical inference layer remains open.

## Ready Foundations

Mathlib now has substantial probability infrastructure:

- `Mathlib.Probability.CentralLimitTheorem`
- `Mathlib.MeasureTheory.Function.ConvergenceInDistribution`
- probability kernels and conditional kernels;
- independence and conditional independence;
- martingale and process files;
- CDF and distribution infrastructure.

Recent formalization projects adjacent to this repo include:

- Statistical Learning Theory in Lean 4: Empirical Processes from Scratch;
- Lean formalization of Rademacher complexity and Dudley entropy integral;
- FormalML, a subgoal-completion benchmark for ML theory;
- Lean formalizations of RL convergence.

These validate that Lean can support probability-heavy ML theory.

## Missing Layer

Classical statistical inference is still sparse:

- M-estimation;
- Z-estimation;
- asymptotic linearity;
- influence functions;
- semiparametric efficiency;
- bootstrap;
- IPW, AIPW, TMLE-style estimators;
- matching estimators;
- survival inference;
- general empirical-process theorem interfaces for inference.

The gap is not only proof search. The hard part is ontology: definitions, assumptions, measurability, topology, non-vacuity, and reusable theorem boundaries.

## Agent Tooling Readiness

Useful components:

- LeanDojo/ReProver: retrieval-augmented proving baseline.
- LeanDojo-v2: newer tracing, SFT, GRPO, and Pantograph-based proving scaffold.
- Pantograph/PyPantograph: interactive Lean proof-state execution.
- Kimina Lean Server: high-throughput verification for RL pipelines.
- DeepSeek-Prover-V2 and Kimina models: strong Lean proof proposal models.
- Mathesis: useful ideas for natural-language-to-Lean autoformalization.
- LeanAgent and LEGO-Prover: useful design references for lifelong learning and growing libraries.

Main risks:

- Lean version drift;
- mathlib dependency churn;
- verifier throughput bottlenecks;
- statement misformalization;
- models ignoring local statistical lemmas;
- generation of true but useless helper lemmas;
- vacuous theorem statements.

## Strategic Conclusion

The direction is a go if framed as a 6 to 12 month research infrastructure project:

```text
formal statistics library + benchmark + verifier-guided multi-agent prover
```

It is not ready for a fully autonomous statistician that reads arbitrary papers and proves everything from first principles.

