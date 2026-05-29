# AI Statistician

Production-oriented AI statistician system with three auditable pieces:

- formal Lean proof obligations for estimator facts,
- vetted estimator implementations,
- Monte Carlo simulation feedback with persisted traces.

The old interview/demo exploration is archived in `Preliminary Attempt/`. The
new code lives in `ai_statistician/`.

## Quick Start

```bash
python3 -m ai_statistician.cli list
python3 -m ai_statistician.cli demo --runs 300 --out runs/smoke
python3 -m ai_statistician.cli demo --question-file examples/questions.json --runs 300 --out runs/external
python3 -m ai_statistician.cli demo --question-file examples/partial_questions.json --runs 300 --out runs/partial
python3 -m ai_statistician.cli trace-audit --run-dir runs/partial --out runs/trace_audit_partial
python3 -m ai_statistician.cli eval --question-file examples/questions.json --n-seeds 3 --runs 300 --out runs/eval_external
python3 -m ai_statistician.cli proof-audit --out runs/proof_audit
python3 -m ai_statistician.cli intake-audit --out runs/intake_audit
python3 -m ai_statistician.cli retrieval-audit --out runs/retrieval_audit
python3 -m ai_statistician.cli retrieval-audit --loogle --out runs/retrieval_audit_loogle
python3 -m ai_statistician.cli formal-source-audit --out runs/formal_source_index
python3 -m ai_statistician.cli algorithm-audit --out runs/algorithm_audit
python3 -m ai_statistician.cli research-algorithm-audit --out runs/research_algorithm_audit
python3 -m ai_statistician.cli research-intake-audit --out runs/research_intake_audit
python3 -m ai_statistician.cli research-knowledge-audit --out runs/research_knowledge_audit
python3 -m ai_statistician.cli frontier-coverage-audit --out runs/frontier_coverage_audit
python3 -m ai_statistician.cli frontier-precision-audit --out runs/frontier_precision_audit
python3 -m ai_statistician.cli frontier-backlog-audit --out runs/frontier_backlog_audit
python3 -m ai_statistician.cli frontier-smoke-benchmark --runs 60 --out runs/frontier_smoke_benchmark
python3 -m ai_statistician.cli doctor --out runs/doctor
python3 -m ai_statistician.cli capability-audit --out runs/capability_audit
python3 -m ai_statistician.cli research-capability-audit --out runs/research_capability_audit
python3 -m ai_statistician.cli prover-component-audit --out runs/prover_component_audit
python3 -m ai_statistician.cli system-audit --include-partial-examples --runs 300 --out runs/system_audit
python3 -m ai_statistician.cli release-bundle --include-partial-examples --runs 300 --out runs/release_bundle
python3 -m ai_statistician.cli research-benchmark --runs 100 --out runs/research_benchmark
python3 -m ai_statistician.cli research-benchmark --question-file examples/research_paper_abstracts.md --runs 100 --out runs/research_paper_benchmark
python3 -m ai_statistician.cli research-eval --n-seeds 3 --runs 80 --out runs/research_eval
python3 -m ai_statistician.cli research-trace-audit --run-dir runs/research_benchmark --out runs/research_trace_audit
python3 -m ai_statistician.cli research-gap-audit --run-dir runs/research_benchmark --out runs/research_gap_backlog
python3 -m ai_statistician.cli formalization-target-audit --run-dir runs/research_benchmark --out runs/formalization_target_audit
python3 -m ai_statistician.cli research-system-audit --runs 100 --out runs/research_system_audit
```

`research-knowledge-audit` also writes a source inventory under
`source_inventory/`, checking that the local paper/prover/Lean resources used by
the lab are present and contain usable artifacts: AI-for-math paper logs,
Mathlib Probability/MeasureTheory, local StatInference, lean-stat-learning-theory,
the vendored EmpericalProcessLEAN main snapshot in
`legacy_sources/emperical_process_lean/`, the vendored legacy AI-Statistician
source pool in `legacy_sources/ai_statistician/`, and OpenProver. These
vendored Lean/stat source pools are not the active runtime; they are registered
as retrieval, proof-bank expansion, benchmark, and training material.
Every research trace now also carries `paper_sources`: ranked local hits from
the 60-paper frontier benchmark and the AI-for-math paper log. Frontier
benchmark records deliberately mark `expected_theoretical_results` and
`evaluation_prompt` as withheld fields and do not use them for retrieval, so
paper grounding does not leak benchmark answers into theory planning.
Simulation traces also carry an auditable `stress_tests` ledger: every stress
scenario extracted at problem-intake time is copied onto each simulation row
with compact numeric diagnostics (`covered`, `stress_flag`, `primary_value`,
`threshold`). This does not claim a separate theorem proof for each stress
scenario; it ensures the trace can prove which declared stress checks were
exercised by the simulation layer.

`formal-source-audit` goes one step deeper: it indexes local Lean declarations
from Mathlib Probability/MeasureTheory plus the local StatInference,
EmpiricalProcessLEAN, and lean-stat-learning-theory checkouts, then runs
theorem-mining queries such as finite-sum variance, Bonferroni/finite union
bound, Chebyshev tails, CLT, Borel-Cantelli, conditional expectation,
sub-Gaussian learning, empirical-process, and Godambe/bootstrap search. This is
the proof-bank expansion tool: before adding a new obligation, run it to find
existing declarations to reuse instead of re-proving from scratch.
The local declaration index now stores compressed theorem-shape features
alongside raw text: binder counts, premise heads, conclusion head, left/right
equality heads, and major symbols. Search therefore uses Lean-aware structure
such as `IndepFun -> variance = sum` instead of only grep-style token overlap.
Formal gaps also persist `primitive_formal_source_hits`, so each missing
primitive such as `slutsky_theorem`, `davis_kahan_sin_theta`, or
`regular_variation` gets its own local Lean/StatInference candidate list rather
than relying only on a broad theorem-goal query.
`formalization-target-audit` then aggregates those primitive-level hits into a
ranked theorem-development queue: each row lists the missing primitive, gaps it
unlocks, local candidate declarations, supporting proof obligations, and a
suggested next proof-bank/library step. It also classifies each target's
`bridge_readiness` so the lab can distinguish primitives that can start from
existing AXLE-verified proof-bank bridges from primitives that need fresh source
search or library design.
`formal-source-audit` now defaults to a persistent SQLite FTS + Lean-shape
reranking backend and writes `formal_source_index.sqlite` next to the audit
manifest, so repeated search and interactive theorem mining can query the local
corpus without rescanning every Lean file in Python.
The production research benchmark can use the same backend: by default
`research-benchmark` writes `formal_source_index.sqlite` in its output
directory and uses that SQLite FTS + Lean-shape reranker when attaching local
Lean/StatInference candidates to formal-gap skeletons. Use
`--formal-source-backend memory` only for tiny fixture runs.
Research traces additionally require source grounding for each normalized
problem class: the primary statistical-method card must be present, along with
at least one local Lean/stat formal source and one retrieval/search-system
source.

Real AXLE proof verification:

```bash
python3 -m ai_statistician.cli doctor --out runs/doctor
/Users/yukang/LeanProjects/LeanPractice/.venv/bin/python \
  -m ai_statistician.cli demo --real-lean --runs 300 --out runs/axle
/Users/yukang/LeanProjects/LeanPractice/.venv/bin/python \
  -m ai_statistician.cli proof-audit --real-lean --out runs/proof_audit_axle
/Users/yukang/LeanProjects/LeanPractice/.venv/bin/python \
  -m ai_statistician.cli theory-intake --question-file examples/llm_theory_questions.json --llm-theory
/Users/yukang/LeanProjects/LeanPractice/.venv/bin/python \
  -m ai_statistician.cli system-audit --real-lean --runs 200 --seeds 20260528 20260529 --out runs/system_audit_axle
/Users/yukang/LeanProjects/LeanPractice/.venv/bin/python \
  -m ai_statistician.cli release-bundle --real-lean --include-partial-examples --runs 200 --seeds 20260528 20260529 --out runs/release_bundle_axle
/Users/yukang/LeanProjects/LeanPractice/.venv/bin/python \
  -m ai_statistician.cli research-benchmark --real-lean --runs 60 --out runs/research_benchmark_axle
/Users/yukang/LeanProjects/LeanPractice/.venv/bin/python \
  -m ai_statistician.cli research-eval --real-lean --runs 40 --seeds 20260528 20260529 --out runs/research_eval_axle
/Users/yukang/LeanProjects/LeanPractice/.venv/bin/python \
  -m ai_statistician.cli research-system-audit --real-lean --runs 60 --out runs/research_system_audit_axle
```

Check `doctor` first. It reports `real_lean_ready` and concrete
`real_lean_blockers`; an AXLE key alone is not enough if the active Python
runtime cannot import the `axle` package. Use `python -m pip install -e
'.[proof]'` in the runtime that will launch `--real-lean`.

`proof-audit` writes both human-auditable proof artifacts and future training
data: `proof_audit_manifest.json`, exported Lean files, `proof_attempts.jsonl`,
and `proof_attempt_log_manifest.json`. The JSONL rows are proof-level verifier
attempts. Positive rows include the checked proof body as `supervision_target`;
failed rows preserve verifier errors, `first_error`, retrieval context, and
reward `0.0` for future repair/value-model data. Every proof row records
`verification_strength` and `kernel_verified`: offline mock checks are useful
for regression gates, but only `--real-lean` AXLE rows with
`kernel_verified=true` are Lean-kernel proof evidence. Capability audits mark
the proof-bank path ready only when the latest real audit covers the full
registered proof bank, not just a selected smoke subset. This is not
tactic-state tracing yet.
Convert those checked attempts into whole-proof SFT prompt/completion data with:

```bash
python3 -m ai_statistician.cli proof-training-export \
  --attempt-log runs/proof_audit/proof_attempts.jsonl \
  --out runs/proof_training_export
```
Then evaluate the no-training nearest-neighbor proof-memory baseline:

```bash
python3 -m ai_statistician.cli proof-policy-baseline \
  --train-jsonl runs/proof_training_export/proof_sft_train.jsonl \
  --validation-jsonl runs/proof_training_export/proof_sft_validation.jsonl \
  --out runs/proof_policy_baseline
```

Read [docs/production_design.md](/Users/yukang/AI%20Statistician/docs/production_design.md) for the architecture and the exact honesty boundary.
Read [docs/real_axle_validation.md](/Users/yukang/AI%20Statistician/docs/real_axle_validation.md) for the latest full proof-bank AXLE validation summary.

## Honest Capability Boundary

The production core verifies registered Mathlib-backed proof obligations and
simulates vetted estimator implementations. The new `research-benchmark` command
is the first AI Statistical Theory Lab layer: it turns open, paper-style
questions into structured problem specs with extraction evidence, creates
theory plans, proves available subclaims, marks frontier theorem pieces as
`FORMAL_GAP`, exports Lean-facing theorem skeletons for those gaps under
`formal_gaps/`, records the missing Lean/stat primitives needed to turn each
skeleton into a theorem, attaches retrieved local Lean/StatInference declaration
candidates to each formal gap, and runs problem-specific simulations.
The proof bank now includes a genuine finite-sample estimator theorem,
`finite_sample_mean_unbiased`: the arithmetic mean over `Fin n` is unbiased
whenever every component estimator is integrable and unbiased for the same
target. This is still finite-sample expectation algebra, not a CLT or efficiency
theorem, but it is a real estimator definition plus Lean proof rather than a
placeholder theorem statement.
It also includes `finite_sample_mean_variance_indep`: for pairwise independent
L2 component estimators indexed by `Fin n`, the variance of the arithmetic
sample mean is the sum of component variances divided by `n^2`. This closes the
previous `finite_sample_mean_variance` primitive gap for registered
finite-sample mean traces while still leaving CLT/asymptotic normality as a
separate frontier gap.
It also includes `finite_sample_mean_chebyshev_indep`, a composed
nonasymptotic guarantee proving that an unbiased pairwise-independent
finite-sample mean has absolute-error probability bounded by the proved
finite-sample variance identity divided by `c^2`.
It also includes `affine_estimator_expectation`, proving the expectation of
an affine/shrinkage estimator `a*X+b` is `a*E[X]+b`; this is the formal bridge
used by the Bayesian normal-conjugate posterior-mean trace.
It also includes `affine_estimator_variance`, proving that the variance of
`a*X+b` is `a^2 Var(X)` for L2 estimators; this supports posterior shrinkage,
linear-smoother SE, and bias-adjusted ranking uncertainty traces.
It also includes `mean2_estimator_variance_indep`, a finite-sample performance
identity proving that the variance of an average of two independent L2
estimators is `(Var(X)+Var(Y))/4`.
It also includes `estimator_error_chebyshev`, a nonasymptotic error-probability
bound for any finite-second-moment estimator with known mean.
It also includes `block_estimator_chebyshev_bound`, the same Mathlib-backed
Chebyshev ingredient exposed as a block-estimator bridge for robust
median-of-means traces. This proves the block failure probability ingredient
only; the binomial median amplification and full robust sub-Gaussian deviation
theorem remain explicit formal gaps.
Another composed guarantee is `mean2_estimator_chebyshev_indep`, which derives
an explicit Chebyshev error bound for the average of two independent unbiased L2
estimators using both the expectation and variance proof ingredients. Composed
obligations now carry machine-readable `depends_on` edges, and the proof/trace
audits validate that those edges point to registered proof-bank obligations.
It also includes `finite_event_indicator_mean_unbiased`, a finite-sample
sample-proportion theorem proving that the mean of event indicators is unbiased
for the common event probability.
It also includes `finite_union_bound`, a Bonferroni-style finite union bound
using Mathlib's `measure_biUnion_finset_le`; conformal, BH/FDR, and
finite-horizon anytime-valid traces can now point to an AXLE-verified union
probability subclaim instead of leaving all event-control algebra as an
unstructured formal gap.
It also includes `finite_horizon_type1_union_control`, a finite monitoring
horizon type-I control bridge: if each monitored rejection event has mass at
most its allocated `α_i`, then the probability of any rejection is at most the
sum of those budgets. This supports sequential-testing traces while still
leaving Ville's inequality and full anytime supermartingale validity as formal
gaps.
It also includes `event_probability_mono`, the measure monotonicity fact
`A ⊆ B -> μ(A) ≤ μ(B)`, which is a reusable subclaim for bad-event containment
arguments in conformal coverage, BH/FDR decompositions, and anytime-valid error
control.
It also includes `independent_event_inter_probability`, proving
`μ(A ∩ B) = μ(A) * μ(B)` from Mathlib's `IndepSet` event-independence
interface; BH/FDR and sequential likelihood-ratio traces can now cite a real
AXLE-verified independence algebra subclaim instead of treating independence as
only informal prose.
It also includes `first_borel_cantelli_limsup_zero`, a first Borel-Cantelli
lemma wrapper proving that summable bad-event probabilities imply the limsup
bad-event has measure zero. This gives sequential and extreme-tail traces a
real AXLE-verified repeated-event control subclaim.
It also includes `second_borel_cantelli_limsup_one`, the independent-event
recurrence counterpart: independent measurable events with divergent total
probability occur infinitely often with probability one. Extreme-tail traces
can now cite both Borel-Cantelli directions as verified formal subclaims.
It also includes `adapted_hitting_after_is_stopping_time`, proving that the
first hitting time of a measurable set by an adapted discrete process is a
stopping time. This is a concrete verified primitive for optional-stopping and
e-process traces.
For private/noised inference, the proof bank now also contains
`noised_estimator_unbiased`, `noised_estimator_variance_indep`, and
`noised_estimator_chebyshev_indep`: real AXLE-verified Lean obligations showing
that independent mean-zero additive noise preserves unbiasedness, adds variance,
and yields a Chebyshev error bound with `Var(X)+Var(Z)`. This is still not a
proof of epsilon-delta DP calibration, but it is a formal bridge for the
sampling-plus-privacy-noise estimator error decomposition used by the DP trace.
`research-eval` repeats that workflow across multiple seeds and writes aggregate
diagnostics, so benchmark claims are stability claims rather than one-off demos.
The trace audit also checks that every extracted diagnostic is backed by a
concrete simulation metric, allowing deliberate aliases such as
`se_calibration -> se_ratio`. It also checks theorem-goal coverage: every
candidate procedure's theorem goal must be defined in the trace and represented
downstream by either a proved subclaim or a formal gap skeleton.
Theorem goals can now also carry explicit `proof_obligations`, so a frontier
gap can point to the exact AXLE-verified subclaims that already support part of
the argument. The current templates use this for causal AIPW expectation
linearity, conformal probability complements, survival event indicators, robust
mean Chebyshev/Markov steps, design-based variance algebra, BH/anytime
probability inequalities, PCA variance positivity, extreme-tail probability
facts, nonparametric sieve regression error bounds, and DP private-mean noise
decomposition. For example, the private mean error-decomposition gap links to
the three noised-estimator obligations above while still keeping DP calibration
and composition as unproved formal gaps.
The frontier layer now includes narrow differential-privacy, nonparametric
regression, Bayesian posterior-calibration, and measurement-bias ranking
classes: recent DP accountant/private-learning prompts route to a
Gaussian-mechanism clipped-mean baseline, DNN/P-spline nonparametric prompts
route to a polynomial-sieve pointwise inference baseline,
predictive-distribution-to-prior prompts route to a normal-conjugate posterior
calibration baseline, and educational-assessment measurement-bias prompts route
to a bias-adjusted country-ranking baseline. Full DP calibration, composition,
DNN approximation, subsampling U-statistic, adaptive tuning theory, posterior
coherence, nonconjugate posterior calibration, IRT measurement-invariance
identifiability, and rank-functional asymptotics remain explicit formal gaps.

It is not yet a fully autonomous system that invents arbitrary new estimators and
proves CLTs, efficiency bounds, or full JASA/AOAS paper theorems in Lean.
The gap backlog is therefore a library-construction plan, not just a list of
unproved claims.

Research capability audit:

```bash
python3 -m ai_statistician.cli research-capability-audit \
  --out runs/research_capability_audit
```

This is the direct answer to "have we achieved the full target?" It maps the
AI Statistical Theory Lab goal to concrete evidence rows. The current scaffold
is expected to pass `all_current_release_requirements_met=true`, while
`goal_complete=false` remains intentional: full Lean proofs of new frontier
asymptotic/statistical theorems and arbitrary JASA/AOAS coverage are still
roadmap items, not achieved capabilities.
