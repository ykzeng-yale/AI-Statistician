# Real AXLE Validation

Latest real proof-bank validation: 2026-05-30.

Runtime used:

```bash
PYTHONPATH=/Users/yukang/AI\ Statistician \
/Users/yukang/LeanProjects/LeanPractice/.venv/bin/python \
  -m ai_statistician.cli proof-audit --real-lean \
  --out runs/proof_audit_real_full_53
```

Result:

```text
verified=53/53
kernel=53/53
verifier=axle.verify_proof
strength=axle_lean_kernel
```

This is the current evidence that the registered proof bank is not only
mock-checked: all 53 registered Mathlib-backed obligations were accepted by
AXLE/Lean-kernel verification in the real external runtime.

Latest real research-system validation: 2026-05-30.

Runtime used:

```bash
PYTHONPATH=/Users/yukang/AI\ Statistician \
/Users/yukang/LeanProjects/LeanPractice/.venv/bin/python \
  -m ai_statistician.cli research-system-audit --real-lean \
  --runs 20 --out runs/research_system_real_lean_54_doob_probability_bridge
```

Result:

```text
all_gates_passed=True
autoform_harness=True
autoform_target_export=True
sources=23/23
frontier_supported=60/60
frontier_precision=60/60
frontier_backlog=0/0
frontier_smoke=23/23
proofs_verified=53/53
proofs_kernel_verified=53/53
proof_verification_strength=axle_lean_kernel
research_traces_ok=10/10
formal_gaps=20
formalized_gaps=20
autoform_targets=20/20
formal_source_graph_symbols=74972
formal_source_graph_edges=1475530
verifier_cache_hits=310
verifier_cache_misses=53
verifier_cache_size=53
```

The research-system run proves that `--real-lean` now flows through the actual
open-question workflow, not only the standalone proof-bank audit. It verifies
all currently registered Mathlib-backed proof obligations with AXLE, runs the
frontier smoke benchmark with one selected question per supported class, indexes
the Meta Atlas Lean mirror through the formal-source graph, detects reusable
Autoform-Bot harness entrypoints, exports all current formal-gap skeletons as
Autoform-compatible target YAML/book artifacts, writes research traces whose
proved subclaims are marked `kernel_verified=true`, and still leaves frontier
theorem claims as explicit formal gaps.

The additional 42nd obligation is
`independent_null_event_family_inter_probability`, a finite-family event
independence bridge proving
`μ (⋂ i ∈ I, A i) = ∏ i ∈ I, μ (A i)` from Mathlib's `iIndepSet.meas_biInter`.
It upgrades the `independent_null_pvalues` BH/FDR formalization primitive from
source-only grounding to a proof-bank-backed bridge while still leaving the full
BH step-up FDR theorem as an explicit formal gap.

The 43rd obligation is
`independent_null_event_family_compl_inter_probability`, proving
`μ (⋂ i ∈ I, (A i)ᶜ) = ∏ i ∈ I, μ (A i)ᶜ` from `iIndepSet_iff` and generated
singleton sigma-algebra measurability. The formalization-target audit now ranks
this complement bridge first for `independent_null_pvalues`, with both
intersection and complement-intersection product obligations available as
bridge candidates.

The 44th obligation is `finite_horizon_evalue_markov_type1_control`, proving a
finite-horizon e-value exceedance control theorem by combining Mathlib Markov
tails with a finite union allocation. It raises
`proof_bank_expansion_bridge_ready` from 6 to 8: `eprocess_type1_control`,
`nonnegative_supermartingale`, and `ville_inequality` now rank this theorem as
their next verified bridge. This remains a finite-horizon Markov/union bridge,
not a proof of optional stopping or full Ville inequality.

The 45th obligation is `aipw_score_expectation_target_of_aug_cancel`, proving
that an AIPW-style score has expectation `psi` when its contrast has expectation
`psi` and treated/control augmentation expectations cancel. It raises
`proof_bank_expansion_bridge_ready` from 8 to 10: `conditional_mean_residual_zero`
and `nuisance_correctness_cases` now rank this theorem as their next verified
bridge. This remains finite expectation algebra, not a proof of conditional
expectation residual identities or full double robustness.

The 46th obligation is `aipw_score_integrable_of_components`, proving that an
AIPW-style score is integrable when its contrast and augmentation components
are integrable. It raises `proof_bank_expansion_bridge_ready` from 10 to 11:
`integrability_of_score_terms` now ranks this theorem as its verified bridge.
This remains an integrability side-condition theorem, not a nuisance-rate or
asymptotic-normality proof.

The 47th obligation is `filtration_mono_measurable_set`, proving that if an
event is measurable with respect to an earlier sigma-algebra in a filtration,
then it remains measurable at any later index. It is a direct wrapper around
Mathlib's `Filtration.mono`. The formalization-target audit now ranks it as the
verified bridge for the `filtration` primitive and as an additional bridge
candidate for `stopping_time` and `ville_inequality`; this raises
`proof_bank_expansion_bridge_ready` from 11 to 12. This remains a structural
filtration measurability theorem, not a proof of optional stopping or full
Ville inequality.

The 48th obligation is `stopping_time_le_event_measurable`, proving the
defining stopping-time event measurability theorem
`IsStoppingTime ℱ τ -> MeasurableSet[ℱ i] {ω | τ ω ≤ i}` from Mathlib's
`IsStoppingTime.measurableSet_le`. It is now wired into the
`sequential_anytime_inference` theorem goal and the provable-subclaim registry
as a real stopping-time bridge. This remains a measurability primitive, not a
proof of optional-stopping validity, nonnegative-supermartingale maximal
inequalities, or full Ville inequality.

The 49th obligation is `submartingale_expected_stopped_value_mono`, a direct
wrapper around Mathlib's `Submartingale.expected_stoppedValue_mono`. It proves
the forward optional-stopping expectation monotonicity theorem for bounded
stopping times of a submartingale:
`τ ≤ π -> (∀ ω, π ω ≤ N) -> μ[stoppedValue f τ] ≤ μ[stoppedValue f π]`.
The formalization-target audit now lists it as a ranked bridge candidate for
`stopping_time`, `ville_inequality`, `filtration`, and
`nonnegative_supermartingale`, and the local-source retriever aligns those gaps
with the StatInference theorem family around
`durrett2019_theorem_4_4_1_submartingale_expected_stoppedValue_mono`. This is a
real optional-stopping theorem bridge; it still does not construct e-processes
or prove Ville's inequality end to end.

The 50th obligation is `submartingale_stopped_process`, a direct wrapper around
Mathlib's `Submartingale.stoppedProcess`. It proves that stopping a real-valued
submartingale at a stopping time preserves the submartingale property. The
formalization-target audit now includes it among ranked bridge candidates for
`stopping_time`, `ville_inequality`, `filtration`, `nonnegative_supermartingale`,
and `eprocess_type1_control`, and aligns those targets with the local
StatInference Durrett 4.2.9 stopped-submartingale theorem family. This is a real
stopped-process preservation theorem; it still does not prove Ville's maximal
inequality or construct a valid e-process end to end.

The 51st obligation is `submartingale_doob_maximal_ineq`, a direct wrapper
around Mathlib's finite-horizon Doob maximal inequality `maximal_ineq` for
nonnegative real-valued submartingales. It proves a running-maximum tail bridge
of the form
`ε * μ {sup_{k≤n} f_k ≥ ε} ≤ ENNReal.ofReal (∫_{sup_{k≤n} f_k ≥ ε} f_n dμ)`.
The sequential-anytime theorem plan now cites it beside the stopped-process and
optional-stopping bridges, so `nonnegative_supermartingale`,
`ville_inequality`, and `eprocess_type1_control` have a real AXLE-verified
maximal-inequality subclaim. This still does not construct an e-process or
prove anytime type-I control end to end.

The 52nd obligation is `submartingale_doob_maximal_budget`, a budgeted
corollary of the same Mathlib maximal inequality. It proves that a terminal
integral budget over the running-maximum event transfers to a
threshold-weighted probability budget:
`ENNReal.ofReal (∫_{sup f ≥ ε} f_n dμ) ≤ ε * α ->
ε * μ {sup f ≥ ε} ≤ ε * α`. The sequential-anytime theorem plan now has both a
raw maximal-inequality bridge and a budgeted tail-control bridge.

The 53rd obligation is `submartingale_doob_maximal_probability_bound`, the
post-Doob cancellation step. It assumes the threshold is nonzero and proves
`μ {sup f ≥ ε} ≤ α` from the same terminal integral budget by combining
`maximal_ineq`, `le_trans`, and Mathlib's `ENNReal.mul_le_mul_iff_right`.
This closes the algebraic division step toward Ville-style type-I control.
The remaining formal gaps are the e-process construction and the proof that
the terminal budget assumption holds for the constructed process.

Important boundary:

- These are finite, reusable Mathlib-backed estimator/probability/statistical
  subclaims.
- The 60/60 frontier benchmark coverage is routing + scoped surrogate support,
  not a claim that every frontier paper's full theorem has been formalized.
- This does not prove full frontier asymptotic theorem goals such as CLT,
  semiparametric efficiency, Donsker conditions, BH FDR, Ville inequality,
  Davis-Kahan recovery, or Hill/Weissman asymptotics end to end.
- `runs/` artifacts stay local and are not committed; regenerate with the
  command above when auditing a release.
