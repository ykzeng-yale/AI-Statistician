# Real AXLE Validation

Latest real proof-bank validation: 2026-05-29.

Runtime used:

```bash
PYTHONPATH=/Users/yukang/AI\ Statistician \
/Users/yukang/LeanProjects/LeanPractice/.venv/bin/python \
  -m ai_statistician.cli proof-audit --real-lean \
  --out runs/proof_audit_real_full_45
```

Result:

```text
verified=45/45
kernel=45/45
verifier=axle.verify_proof
strength=axle_lean_kernel
```

This is the current evidence that the registered proof bank is not only
mock-checked: all 45 registered Mathlib-backed obligations were accepted by
AXLE/Lean-kernel verification in the real external runtime.

Latest real research-system validation: 2026-05-29.

Runtime used:

```bash
PYTHONPATH=/Users/yukang/AI\ Statistician \
/Users/yukang/LeanProjects/LeanPractice/.venv/bin/python \
  -m ai_statistician.cli research-system-audit --real-lean \
  --runs 20 --out runs/research_system_real_lean_45_aipw_cancel_bridge
```

Result:

```text
all_gates_passed=True
autoform_harness=True
autoform_target_export=True
sources=19/19
frontier_supported=60/60
frontier_precision=60/60
frontier_backlog=0/0
frontier_smoke=23/23
proofs_verified=45/45
proofs_kernel_verified=45/45
proof_verification_strength=axle_lean_kernel
research_traces_ok=10/10
formal_gaps=20
formalized_gaps=20
autoform_targets=20/20
formal_source_graph_symbols=69330
formal_source_graph_edges=1361926
verifier_cache_hits=294
verifier_cache_misses=45
verifier_cache_size=45
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
