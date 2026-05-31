# Real Lean Kernel Validation

Latest current proof-bank validation: 2026-05-31.

Runtime used:

```bash
python3 -m ai_statistician.cli proof-audit \
  --local-lean \
  --out runs/proof_audit_local_lean_current
```

Result:

```text
verified=92/92
kernel=92/92
verifier=local.lake_env_lean
strength=local_lean_kernel_batch
proof_bank_fingerprint=d3163e108d374e2cd15a3d56c894299055c678e2295490758cbd108cf9631de8
```

This is the current evidence that the registered proof bank is not only
mock-checked: all 92 registered Mathlib-backed obligations were accepted by a
real Lean kernel check through the local Lake/Mathlib runtime. AXLE remains the
preferred remote verifier for release bundles when its Python package and API
runtime are available; the local Lean backend is the offline kernel-equivalent
fallback used for this latest full-bank proof audit.

Latest remote AXLE proof-bank validation: 2026-05-30.

```bash
PYTHONPATH=/Users/yukang/AI\ Statistician \
/Users/yukang/LeanProjects/LeanPractice/.venv/bin/python \
  -m ai_statistician.cli proof-audit --real-lean \
  --out runs/proof_audit_real_full_54
```

```text
verified=54/54
kernel=54/54
verifier=axle.verify_proof
strength=axle_lean_kernel
```

That remote AXLE run predates the newest proof-bank additions. The current
88-obligation proof bank has full local Lean kernel evidence above; run the
same `proof-audit --real-lean` command again from an AXLE-ready runtime to
refresh remote AXLE evidence for all 88 obligations.

Latest real research-system validation: 2026-05-30.

Runtime used:

```bash
PYTHONPATH=/Users/yukang/AI\ Statistician \
/Users/yukang/LeanProjects/LeanPractice/.venv/bin/python \
  -m ai_statistician.cli research-system-audit --real-lean \
  --runs 20 --out runs/research_system_real_lean_55_supermartingale_optional_stopping
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
proofs_verified=54/54
proofs_kernel_verified=54/54
proof_verification_strength=axle_lean_kernel
research_traces_ok=10/10
formal_gaps=20
formalized_gaps=20
autoform_targets=20/20
formal_source_graph_symbols=74972
formal_source_graph_edges=1475530
verifier_cache_hits=312
verifier_cache_misses=54
verifier_cache_size=54
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
`psi` and treated/control augmentation expectations cancel.
`nuisance_correctness_cases` ranks this theorem as a verified algebraic bridge,
while `conditional_mean_residual_zero` is now served by the direct centered
residual theorem below. This remains finite expectation algebra, not a proof of
conditional expectation residual identities or full double robustness.

The 46th obligation is `conditional_mean_residual_zero_of_mean_eq`, proving the
direct centered-residual fact `E[Y - m] = 0` when `E[Y] = m`. It is now the
first-ranked bridge for `conditional_mean_residual_zero` and
`exogeneity_moment_condition`. This proves the finite expectation step used
after a conditional-expectation argument has reduced the problem to an ordinary
mean equality; it still does not prove conditional expectation residual
identities themselves.

The 47th obligation is `condexp_integral_eq_integral_real`, proving that the
integral of a real conditional expectation equals the original integral. This
is the Mathlib `integral_condExp` bridge for law-of-total-expectation,
`conditional_expectation`, `iterated_expectation`, and exogeneity theorem
skeletons. It is a reusable conditional-expectation integration rule, not a
proof of any model-specific conditional exchangeability assumption.

The added tower-property bridge is `condexp_tower_of_sub_sigma_real`, proving
that for nested sigma-fields `m1 <= m2 <= mΩ`, conditioning a real random
variable on `m2` and then on `m1` is almost everywhere the same as conditioning
directly on `m1`. It wraps Mathlib's `condExp_condExp_of_le` and gives
iterated-expectation, filtration/martingale, causal-identification, and
exogeneity theorem skeletons a direct kernel-verified bridge for staged
conditioning, while still assuming the nested sigma-field hypotheses.

The 48th obligation is `conditional_mean_residual_zero_of_condExp_ae_eq`,
promoted from the local StatInference conditional-mean integral bridge. It
proves that if `E[outcome | scoreSigma]` is almost everywhere equal to a
score-space version, then the centered residual has population integral zero.
The proof uses Mathlib's `integral_condExp`, `integral_congr_ae`, and
`integral_sub`. This is the direct bridge for AIPW residual orthogonality and
exogeneity moment conditions, while still assuming the conditional-expectation
equality premise rather than proving nuisance correctness.

The 49th obligation is `aipw_score_expectation_target_of_zero_aug`, proving
that an AIPW-style score has expectation `psi` when the contrast term has
expectation `psi` and both augmentation residual terms have mean zero. It now
depends on the conditional-expectation residual bridge above, making the AIPW
roadmap's residual-zero dependency explicit.

The 50th obligation is `aipw_score_integrable_of_components`, proving that an
AIPW-style score is integrable when its contrast and augmentation components
are integrable. It raises `proof_bank_expansion_bridge_ready` from 10 to 11:
`integrability_of_score_terms` now ranks this theorem as its verified bridge.
This remains an integrability side-condition theorem, not a nuisance-rate or
asymptotic-normality proof.

The 51st obligation is `filtration_mono_measurable_set`, proving that if an
event is measurable with respect to an earlier sigma-algebra in a filtration,
then it remains measurable at any later index. It is a direct wrapper around
Mathlib's `Filtration.mono`. The formalization-target audit now ranks it as the
verified bridge for the `filtration` primitive and as an additional bridge
candidate for `stopping_time` and `ville_inequality`; this raises
`proof_bank_expansion_bridge_ready` from 11 to 12. This remains a structural
filtration measurability theorem, not a proof of optional stopping or full
Ville inequality.

The 52nd obligation is `stopping_time_le_event_measurable`, proving the
defining stopping-time event measurability theorem
`IsStoppingTime ℱ τ -> MeasurableSet[ℱ i] {ω | τ ω ≤ i}` from Mathlib's
`IsStoppingTime.measurableSet_le`. It is now wired into the
`sequential_anytime_inference` theorem goal and the provable-subclaim registry
as a real stopping-time bridge. This remains a measurability primitive, not a
proof of optional-stopping validity, nonnegative-supermartingale maximal
inequalities, or full Ville inequality.

The 53rd obligation is `submartingale_expected_stopped_value_mono`, a direct
wrapper around Mathlib's `Submartingale.expected_stoppedValue_mono`. It proves
the forward optional-stopping expectation monotonicity theorem for bounded
stopping times of a submartingale:
`τ ≤ π -> (∀ ω, π ω ≤ N) -> μ[stoppedValue f τ] ≤ μ[stoppedValue f π]`.
The formalization-target audit now lists it as a ranked bridge candidate for
`stopping_time`, `ville_inequality`, `filtration`, and
`nonnegative_supermartingale`, and the local-source retriever aligns those gaps
with a real kernel-checked Mathlib theorem.

The screening/selection bridge family adds four local-kernel verified proof-bank
obligations:

- `screening_statistic_concentration`
- `signal_margin_implies_active_selection`
- `inactive_coordinate_union_bound`
- `selection_accuracy_lower_bound_from_support_events`

These obligations are intentionally finite-sample event-algebra and margin
bridges. They do not prove a full high-dimensional selection theorem, but they
turn the frontier theory-revision queue's screening obligations into verified
proof-bank bridge targets before the remaining model-specific concentration and
signal-separation assumptions are formalized.
with the StatInference theorem family around
`durrett2019_theorem_4_4_1_submartingale_expected_stoppedValue_mono`. This is a
real optional-stopping theorem bridge; it still does not construct e-processes
or prove Ville's inequality end to end.

The 54th obligation is `submartingale_stopped_process`, a direct wrapper around
Mathlib's `Submartingale.stoppedProcess`. It proves that stopping a real-valued
submartingale at a stopping time preserves the submartingale property. The
formalization-target audit now includes it among ranked bridge candidates for
`stopping_time`, `ville_inequality`, `filtration`, `nonnegative_supermartingale`,
and `eprocess_type1_control`, and aligns those targets with the local
StatInference Durrett 4.2.9 stopped-submartingale theorem family. This is a real
stopped-process preservation theorem; it still does not prove Ville's maximal
inequality or construct a valid e-process end to end.

The sequential martingale block also includes
`supermartingale_expected_stopped_value_antimono`, a bounded optional-stopping
expectation theorem for real-valued supermartingales. For stopping times
`τ ≤ π` with bounded `π`, it proves `μ[stoppedValue f π] ≤ μ[stoppedValue f τ]`
using Mathlib's `Supermartingale.setIntegral_le` and stopped-value
decomposition. This is the direct expectation-budget primitive needed by
nonnegative-supermartingale/e-process theorem skeletons.

The Doob bridge `submartingale_doob_maximal_ineq` is a direct wrapper
around Mathlib's finite-horizon Doob maximal inequality `maximal_ineq` for
nonnegative real-valued submartingales. It proves a running-maximum tail bridge
of the form
`ε * μ {sup_{k≤n} f_k ≥ ε} ≤ ENNReal.ofReal (∫_{sup_{k≤n} f_k ≥ ε} f_n dμ)`.
The sequential-anytime theorem plan now cites it beside the stopped-process and
optional-stopping bridges, so `nonnegative_supermartingale`,
`ville_inequality`, and `eprocess_type1_control` have a real AXLE-verified
maximal-inequality subclaim. This still does not construct an e-process or
prove anytime type-I control end to end.

The budget bridge `submartingale_doob_maximal_budget` is a budgeted
corollary of the same Mathlib maximal inequality. It proves that a terminal
integral budget over the running-maximum event transfers to a
threshold-weighted probability budget:
`ENNReal.ofReal (∫_{sup f ≥ ε} f_n dμ) ≤ ε * α ->
ε * μ {sup f ≥ ε} ≤ ε * α`. The sequential-anytime theorem plan now has both a
raw maximal-inequality bridge and a budgeted tail-control bridge.

The probability-bound bridge `submartingale_doob_maximal_probability_bound` is the
post-Doob cancellation step. It assumes the threshold is nonzero and proves
`μ {sup f ≥ ε} ≤ α` from the same terminal integral budget by combining
`maximal_ineq`, `le_trans`, and Mathlib's `ENNReal.mul_le_mul_iff_right`.
This closes the algebraic division step toward Ville-style type-I control.
The remaining formal gaps are the e-process construction and the proof that
the terminal budget assumption holds for the constructed process.

The martingale-convergence bridge `submartingale_ae_tendsto_limit_process`
wraps Mathlib's `Submartingale.ae_tendsto_limitProcess`. It proves that an
L1-bounded real-valued submartingale converges almost everywhere to the
filtration `limitProcess`. The right-censored survival/Kaplan-Meier roadmap now
uses it as a kernel-checked convergence primitive for Nelson-Aalen and survival
martingale skeletons, while still leaving the martingale CLT, Greenwood
variance consistency, and product-limit delta method as formal gaps.

The robust-mean block now includes `median_of_means_failure_union_control`, a
finite block-event union bridge. It proves that a median-of-means failure event
contained in the finite union of bad block events has probability bounded by
the sum of the bad-block budgets. This is a real verified bridge from
block-level Chebyshev control toward MoM theorem skeletons; it still does not
prove the binomial majority tail or the sharp sub-Gaussian MoM deviation
theorem.

The design-based variance block now includes
`neyman_variance_conservative_algebra`. It proves that if exact randomization
variance is an observable Neyman bound minus a nonnegative treatment-effect
variance term, then the observable bound is conservative. This is a real
verified algebra bridge for Neyman-style variance traces; it still does not
prove complete randomization, finite-population potential-outcome
identification, or the randomization variance decomposition end to end.

The same design-based block now includes `finite_population_ate_mean_difference`.
It proves the deterministic finite-population potential-outcome identity that
the mean of unit-level effects `Y(1)-Y(0)` equals the treated potential-outcome
mean minus the control potential-outcome mean. This is a real verified target
algebra bridge; it still does not prove complete-randomization assignment or
randomization-unbiasedness of the observed difference-in-means estimator.

The design-based block also includes
`complete_randomization_uniform_assignment_mass`. It proves that Mathlib's
uniform PMF on a finite nonempty assignment space gives each assignment mass
`1/card`. This is a real verified distribution bridge for complete-randomization
traces; it still does not prove fixed-treated-count combinatorics,
randomization-unbiasedness, or the design-based covariance formula.

The conformal-rank block now includes `uniform_rank_pmf_mass`. It proves that
Mathlib's uniform PMF on a finite nonempty rank space `Fin n` gives each rank
mass `1/n`. This is a real verified PMF bridge for rank-uniformity traces; it
still does not prove that exchangeable nonconformity scores induce a uniform
rank, nor the full order-statistic conformal coverage theorem.

The BH/FDR block now includes `bh_threshold_grid_mono`. It proves that the
Benjamini-Hochberg threshold grid `q*k/m` is monotone in the rank index `k`
whenever the nominal level `q` is nonnegative. This is a real verified algebraic
bridge for ordered-p-value and step-up fixed-point traces; it still does not
prove BH self-consistency, p-value independence, or the full FDR control theorem.

The causal ATE block now includes `potential_outcome_observed_consistency`. It
proves the deterministic consistency identity for a binary observed outcome:
treated units reveal `Y(1)` and control units reveal `Y(0)` by construction.
This is a real verified bridge for the potential-outcome consistency primitive;
it still does not prove conditional exchangeability, positivity, identification,
or AIPW double robustness.

The same causal block now includes `propensity_score_ne_zero_of_lower_bound`. It
proves that a propensity score bounded below by a strictly positive constant is
nonzero, providing the denominator-safety step needed by inverse-propensity and
AIPW algebra. It still does not prove overlap as a model assumption,
conditional exchangeability, identification, or double robustness.

The next causal bridge is `propensity_weight_mul_cancel_of_lower_bound`. It
uses the same strict lower-bound assumption to prove the inverse-weight
identity `p⁻¹ * p = 1` via Mathlib's `inv_mul_cancel₀`. This gives
`propensity_weight_identity` and AIPW/IPW score algebra a kernel-checked bridge,
while still leaving conditional exchangeability, nuisance correctness,
identification, and double robustness as explicit formal gaps.

The latest sequential/product-process bridge is
`event_indicator_product_integral_eq_inter`. It proves that the integral of the
product of two event indicators equals the measure of the intersection, using
Mathlib's `Set.inter_indicator_one` and `integral_indicator_one`. This gives
`adapted_product_process`, `bernoulli_likelihood_ratio`, and
`conditional_expectation_product_step` a kernel-checked algebraic bridge while
leaving the full Bernoulli likelihood-ratio martingale theorem as a formal gap.

The next sequential/product-process bridge is
`independent_event_indicator_product_lintegral_eq_mul`. It proves that for two
independent measurable events, the lintegral of the product of their ENNReal
event indicators factors as `μ A * μ B`, using Mathlib's
`Set.inter_indicator_one`, `lintegral_indicator_one`, and
`IndepSet.measure_inter_eq_mul`. This gives
`independent_bernoulli_sequence`, `adapted_product_process`,
`bernoulli_likelihood_ratio`, `conditional_expectation_product_step`, and
`martingale_definition` a stronger kernel-checked product bridge. It still does
not prove conditional-expectation preservation or the full likelihood-ratio
martingale theorem end to end.

The first direct conditional-expectation bridge for the same sequential lane is
`independent_event_indicator_condExp_filtration_eq_prob`. It wraps Mathlib's
Borel-Cantelli support lemma
`iIndepSet.condExp_indicator_filtrationOfSet_ae_eq`, proving that in an
independent sequence of measurable events, the conditional expectation of a
future event indicator given the filtration generated by past events is almost
everywhere the future event probability. This materially improves the
`conditional_expectation_product_step` and Bernoulli martingale skeletons, while
still leaving the full likelihood-ratio product-process martingale theorem as a
formal gap.

The general real-valued conditional-expectation bridge is
`independent_real_condExp_natural_eq_mean`. It wraps
`iIndepFun.condExp_natural_ae_eq_of_lt`, proving that for an independent
real-valued stochastic sequence, the conditional expectation of a future
variable given the natural filtration generated by the past sequence is almost
everywhere its mean. This gives `sample_moment_lln`, `iid_empirical_mean_clt`,
`exogeneity_moment_condition`, `conditional_expectation`, and
`martingale_definition` a kernel-checked starting point. It still does not
prove LLN or asymptotic normality end to end.

The first registered full asymptotic limit theorem bridge is
`iid_real_clt_tendsto_distribution`. It wraps Mathlib's one-dimensional central
limit theorem `tendstoInDistribution_inv_sqrt_mul_sum_sub`, proving convergence
in distribution of the centered sqrt(n)-scaled iid real partial sum to the
Gaussian law with matching variance. This gives `iid_empirical_mean_clt`,
`multivariate_score_clt`, `wald_interval_slutsky`, and
`influence_function_variance` a real kernel-checked CLT starting point. It is
still univariate and does not prove multivariate score CLTs, sandwich
variance consistency, or a problem-specific estimator asymptotic-normality
theorem end to end.

Two additional asymptotic transport bridges are now registered:
`tendsto_in_distribution_continuous_mapping` wraps Mathlib's
`TendstoInDistribution.continuous_comp`, and
`slutsky_add_negligible_zero_real` wraps
`TendstoInDistribution.add_of_tendstoInMeasure_const` for real-valued
statistics plus a remainder converging to zero in probability. These make
`slutsky_theorem`, `matrix_inverse_continuous_mapping`,
`tail_quantile_continuous_mapping`, `product_limit_delta_method`,
`rank_uncertainty_functional_delta_method`, and
`wald_interval_slutsky` bridge-ready. They still assume the continuity or
negligible-remainder premises rather than proving problem-specific
linearization, variance consistency, or empirical-process remainder bounds.

Important boundary:

- These are finite, reusable Mathlib-backed estimator/probability/statistical
  subclaims.
- The 60/60 frontier benchmark coverage is routing + scoped surrogate support,
  not a claim that every frontier paper's full theorem has been formalized.
- This does not prove full frontier asymptotic theorem goals such as
  multivariate CLT, semiparametric efficiency, Donsker conditions, BH FDR,
  Ville inequality, Davis-Kahan recovery, or Hill/Weissman asymptotics end to
  end.
- `runs/` artifacts stay local and are not committed; regenerate with the
  command above when auditing a release.
