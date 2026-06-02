# External Lean Source Reuse Audit

Date: 2026-06-01.

Purpose: identify open-source Lean codebases in statistics, probability,
analysis, calculus, and ML theory that can reduce AI-Statistician formal
primitive debt through local retrieval and proof-bank mining.

## Integrated Local Retrieval Sources

These repositories are cloned under `/Users/yukang/.codex/external` and wired
into `research_source_inventory.py`, `research_knowledge.py`, and formal-source
audit queries.

| Source ID | Upstream | License | Local path | Use |
| --- | --- | --- | --- | --- |
| `formal_slt` | `https://github.com/Robby955/FormalSLT` | MIT | `/Users/yukang/.codex/external/FormalSLT/FormalSLT` | Finite-sample SLT, Rademacher, PAC/VC, ERM, Azuma, stability, Dudley/chaining |
| `lean_rademacher` | `https://github.com/auto-res/lean-rademacher` | MIT | `/Users/yukang/.codex/external/lean-rademacher/FoML` | Rademacher complexity, McDiarmid, Massart, Dudley entropy, linear predictors |
| `lean_machine_learning_lml` | `https://github.com/LeanMachineLearning/LML` | Apache-2.0 | `/Users/yukang/.codex/external/LeanMachineLearning-LML/LeanMachineLearning` | Stochastic bandits, regret, UCB, explore-then-commit, algorithm theorem structure |
| `brownian_motion_lean` | `https://github.com/RemyDegenne/brownian-motion` | Apache-2.0 | `/Users/yukang/.codex/external/brownian-motion/BrownianMotion` | Brownian motion, Gaussian processes, Kolmogorov-Chentsov, stochastic-process theorem shapes |
| `kolmogorov_extension_lean` | `https://github.com/RemyDegenne/kolmogorov_extension4` | Apache-2.0 | `/Users/yukang/.codex/external/kolmogorov_extension4/KolmogorovExtension4` | Kolmogorov extension theorem, projective measure families, compact systems |
| `scilean_calculus` | `https://github.com/lecopivo/SciLean` | Apache-2.0 | `/Users/yukang/.codex/external/SciLean/SciLean` | Calculus, gradients, Jacobians, probabilistic derivatives, optimization, Gaussian examples |

`brownian_motion_lean` and `scilean_calculus` are retrieval-only and excluded
from training export by default because they contain WIP/sorry-heavy regions.
They are still useful for theorem shapes, definitions, and search context.

## Smoke Evidence

The new source-only index found 6,986 declarations:

- `formal_slt`: 731 declarations
- `lean_rademacher`: 280 declarations
- `lean_machine_learning_lml`: 561 declarations
- `brownian_motion_lean`: 1,055 declarations
- `kolmogorov_extension_lean`: 46 declarations
- `scilean_calculus`: 4,313 declarations

Representative retrieval hits:

- FormalSLT query retrieved `FormalSLT.AlgorithmicStability.*generalizationGap*`.
- Lean Rademacher query retrieved `RademacherComplexity_eq` and
  `dudley_entropy_integral_bound`.
- LML query retrieved `Bandits.ucbAlgorithm` and UCB/regret lemmas.
- Brownian query retrieved `IsGaussianProcess.isPreBrownian_of_covariance` and
  `isKolmogorovProcess_brownian`.
- Kolmogorov query retrieved projective-family content lemmas.
- SciLean query retrieved Gaussian/calculus declarations.

## Deferred Candidates

- `https://github.com/njuyxw/FormalML`: useful as a proof-search/evaluation
  benchmark for ML/probability/optimization subgoals, but GitHub did not report
  a repository license. Keep it out of source inventory until license and
  intended reuse policy are clear.
- `https://github.com/lean-dojo/LeanCopilot`: proof-search infrastructure, not
  domain theorem source. Consider separately when improving prover automation.
- `https://github.com/ulamai/ulamai`: prover/formalizer infrastructure with no
  GitHub license metadata at audit time. Treat as design/reference only unless
  license is clarified.

## Next Reuse Step

Run primitive-source coverage against the current missing formal primitives and
classify each unsupported primitive as:

- `direct_wrapper_possible`
- `bridge_lemma_needed`
- `source_only_not_importable`
- `no_source_found`

By default this is a fast prioritization pass: it skips external searches for
primitives that already have proof-bank or local declaration support, and
records how many external queries were performed or skipped. For exhaustive
external-source discovery, run the formal-source retrieval benchmark/ablation
suites with the active `lean_rag` dependency graph DB.

The best first proof-bank mining targets are:

- Rademacher/uniform-deviation primitives from `formal_slt` and
  `lean_rademacher`.
- PAC/VC and bounded-difference bridges from `formal_slt`.
- Gaussian process/Kolmogorov-Chentsov theorem shapes from
  `brownian_motion_lean`.
- Projective-family measure-construction bridges from
  `kolmogorov_extension_lean`.
- Differentiability/gradient/optimization theorem shapes from `scilean_calculus`
  when estimator or algorithm derivations need calculus context.
