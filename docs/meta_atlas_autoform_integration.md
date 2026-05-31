# Meta Atlas Lean and Autoform-Bot Integration

Latest integration audit: 2026-05-30.

The system now uses local mirrors of the user-owned forks as preferred sources,
with upstream Meta repositories as fallback acquisition/provenance references:

- Atlas Lean: `/Users/yukang/.codex/external/ykzeng-atlas-lean`
  - Remote: `https://github.com/ykzeng-yale/atlas-lean.git`
  - Commit: `c5a10f1a95de31e5476484c8bb3856ee7f164ea0`
- Autoform-Bot: `/Users/yukang/.codex/external/ykzeng-autoform-bot`
  - Remote: `https://github.com/ykzeng-yale/autoform-bot.git`
  - Commit: `f137da6cc9a60621d3b6aa0964e69443ba35903d`

## Atlas Lean Retrieval

Atlas is integrated as a retrieval/formal-source corpus, not as an imported Lean
dependency of the current proof bank. The formal-source index includes focused
subtrees that are directly useful for statistical theory development:

- `atlas_lean_high_dimensional_statistics`
- `atlas_lean_theory_of_probability`
- `atlas_lean_probabilistic_methods`
- `atlas_lean_analysis_foundations`
- `atlas_lean_fourier_analysis`
- `atlas_lean_functional_analysis`
- `atlas_lean_differential_analysis`
- `atlas_lean_projection_theory`

The latest formal-source audit indexed these Atlas declarations:

```text
atlas_lean_analysis_foundations: 127 declarations
atlas_lean_differential_analysis: 1470 declarations
atlas_lean_fourier_analysis: 350 declarations
atlas_lean_functional_analysis: 112 declarations
atlas_lean_high_dimensional_statistics: 1503 declarations
atlas_lean_probabilistic_methods: 1133 declarations
atlas_lean_projection_theory: 717 declarations
atlas_lean_theory_of_probability: 493 declarations
```

Retrieval smoke evidence:

```text
query=Atlas HighDimensionalStatistics IsSubGaussian mgf bound Bernstein concentration
top_hit=IsSubGaussian.mgf_bound
source=atlas_lean_high_dimensional_statistics

query=Atlas TheoryOfProbability CLT Lindeberg Feller Borel Cantelli weak convergence
top_hit=ProbabilityTheory.weakConvergence_iff_tendsto
source=atlas_lean_theory_of_probability

query=Atlas FourierAnalysis characteristic function Fourier transform weak convergence CLT finite measures
top_hit=FourierTransformMeasure.schwartz_weak_convergence_of_fourierTransform_tendsto
source=atlas_lean_fourier_analysis

query=Atlas differential analysis Frechet Taylor Sobolev Fourier Gaussian
top_hit=SobolevHilbert.sobolevFourierEquiv_map_I_smul
source=atlas_lean_differential_analysis

query=Atlas projection theory orthogonal projection large sieve grid projection geometric incidence
top_hit=LargeSieveSize.sum_modProjection_eq
source=atlas_lean_projection_theory
```

This gives the AI Statistician a larger local Lean search surface for
sub-Gaussian concentration, high-dimensional statistics, probability limit
theory, characteristic-function weak convergence, Hilbert/projection identities,
Taylor/Sobolev analysis, and geometric projection primitives while keeping
AXLE/Lean as the final verifier.

## Autoform-Bot Harness

Autoform-Bot is integrated as a harness adapter. The system records reusable
entrypoints for:

- statement extraction
- Lean compilation/evaluation checks
- dependency-graph evaluation
- Lean proof-checker wrappers
- Lean REPL/LSP tooling
- Lean proof-pattern/tactic skill documents
- multi-agent orchestration
- trace/visualization utilities

Current detected command templates:

```bash
python -m autoform.statement_extraction run --book-dir <book_dir> --output <book_dir>/targets.yaml
python -m autoform.bot.main run --config <config.yaml> --name <run_name>
python -m autoform.eval run --repo_dir <lean_repo> --code_dir <lean_source_dir> --task_file <targets.yaml> --book_dir <book_dir>
python -m autoform.visualizer.app --runs-dir <workspace> --port 8003
```

The real research-system audit gate `autoform_harness` now requires the local
harness to expose the statement extraction, Lean eval, dependency-graph eval,
proof-checker, Lean REPL/native-LSP, Lean skill-doc, and multi-agent bot
components.

The same check is exposed as a standalone command so the Autoform integration
can be validated without running the full research-system audit:

```bash
python -m ai_statistician.cli autoform-harness-audit --out runs/autoform_harness
```

Latest focused harness audit:

```text
ready=True
root=/Users/yukang/.codex/external/ykzeng-autoform-bot
commit=f137da6cc9a6
statement_extraction=True
lean_eval=True
dependency_graph_eval=True
proof_checker=True
lean_repl=True
native_lsp=True
lean_skill_docs=True
multi_agent_bot=True
visualizer=True
```

The AI Statistician now also writes concrete Autoform inputs from its own formal
gap queue:

```bash
python -m ai_statistician.cli autoform-target-export \
  --run-dir runs/research_benchmark \
  --out runs/autoform_targets
```

That command emits:

- `autoform_targets.yaml`: Autoform-Bot `FormalizationTarget` records.
- `autoform_book/formal_gap_statements.md`: book-style descriptions of each
  statistical theorem-development target.
- `autoform_targets_manifest.json`: audit/provenance, command templates, and
  target fingerprint.

This is still a formalization handoff, not a proof claim: the exported targets
preserve `FORMAL_GAP` and placeholder-assumption boundaries.

## Provenance Boundary

The system uses the user-owned mirrors fully for local search, proof planning,
and Autoform handoff. The source inventory still records provenance and default
export policy explicitly:

- `atlas_lean_*`: `retrieval_only_no_training_export`
- `autoform_bot_harness`: `integration_reference_no_training_export`

Training exporters do not serialize external declaration payloads by default;
retrieval/search and Autoform routing use the local mirrors directly. For an
owner-authorized training export, set
`AI_STATISTICIAN_INCLUDE_EXTERNAL_TRAINING_SOURCES=1`.

## Latest Validation

Current local Lean kernel proof-bank audit plus latest cached system audit:

```bash
python3 -m ai_statistician.cli proof-audit \
  --local-lean \
  --out runs/proof_audit_local_lean_current

python3 -m ai_statistician.cli research-system-audit \
  --runs 25 \
  --out runs/test_research_system_audit
```

Result:

```text
proof_bank_kernel=69/69
proof_verifier=local.lake_env_lean
proof_strength=local_lean_kernel_batch
system_all_gates_passed=True
system_elapsed_latest=122.1s
sources=23/23
frontier_supported=60/60
frontier_smoke=23/23
formalized_gaps=20/20
missing_primitives=97
```

Focused Atlas/Autoform source audit:

```text
formal_source_audit: sources=15 declarations=44000 queries=27/27 backend=sqlite_fts_hybrid
formal_source_graph_audit: declarations=44000 symbols=74968 edges=1475474 queries=11/11
autoform_harness_audit: ready_for_integration=True
source_inventory: 23/23 all_ok=True
```

The same audit now reports `proof_bank_expansion_bridge_ready=12`.
`independent_null_pvalues` is backed by the verified
`independent_null_event_family_inter_probability` and
`independent_null_event_family_compl_inter_probability` obligations. The
sequential primitives `eprocess_type1_control`, `nonnegative_supermartingale`,
and `ville_inequality` now rank `finite_horizon_evalue_markov_type1_control`
as their verified finite-horizon Markov/union bridge while preserving optional
stopping and full Ville as formal gaps. The AIPW primitives
`conditional_mean_residual_zero` and `nuisance_correctness_cases` now rank
`aipw_score_expectation_target_of_aug_cancel` as their verified algebraic bridge
while preserving conditional-expectation residual identities and full double
robustness as formal gaps. `integrability_of_score_terms` now ranks
`aipw_score_integrable_of_components` as its verified integrability bridge.
The `filtration` primitive now ranks `filtration_mono_measurable_set` as its
verified bridge, and `stopping_time` / `ville_inequality` also list it as a
candidate bridge while preserving optional stopping and full Ville as formal
gaps. The proof bank now also includes
`stopping_time_le_event_measurable`, a direct wrapper around Mathlib's
`IsStoppingTime.measurableSet_le`, and the sequential-anytime theorem plan cites
it as the verified stopping-time event measurability primitive. It also now
includes `submartingale_expected_stopped_value_mono`, a wrapper around Mathlib's
`Submartingale.expected_stoppedValue_mono`; the formal-source/graph queue aligns
this bridge with the local StatInference Durrett 4.4.1 optional-stopping theorem
family while preserving e-process construction and full Ville as formal gaps.
The stopped-process bridge `submartingale_stopped_process` is also verified via
Mathlib's `Submartingale.stoppedProcess`, and the graph queue aligns it with the
local StatInference Durrett 4.2.9 stopped-submartingale theorem family.
The supermartingale bridge `supermartingale_expected_stopped_value_antimono`
adds the reversed bounded optional-stopping expectation budget for
supermartingales. This gives Autoform targets a direct e-process/Ville
primitive instead of forcing them to reconstruct it from the submartingale
optional-stopping proof.
The Doob bridge `submartingale_doob_maximal_ineq` is now verified via Mathlib's
finite-horizon `maximal_ineq`, so the sequential-anytime Autoform target queue
contains a real maximal-inequality subclaim before the remaining full
Ville/e-process construction gaps.
The budgeted bridge `submartingale_doob_maximal_budget` is also verified, so
the Autoform target queue can hand off a sharper formal gap: construct the
e-process and prove the terminal budget rather than rediscovering Doob's
maximal inequality.
The probability-bound bridge `submartingale_doob_maximal_probability_bound`
then cancels the nonzero threshold using Mathlib's
`ENNReal.mul_le_mul_iff_right`, so Autoform targets no longer need to spend
search budget on the post-Doob algebraic division step.
