# Real AXLE Validation

Latest real proof-bank validation: 2026-05-29.

Runtime used:

```bash
PYTHONPATH=/Users/yukang/AI\ Statistician \
/Users/yukang/LeanProjects/LeanPractice/.venv/bin/python \
  -m ai_statistician.cli proof-audit --real-lean \
  --out runs/proof_audit_real_full_41
```

Result:

```text
verified=41/41
kernel=41/41
verifier=axle.verify_proof
strength=axle_lean_kernel
```

This is the current evidence that the registered proof bank is not only
mock-checked: all 41 registered Mathlib-backed obligations were accepted by
AXLE/Lean-kernel verification in the real external runtime.

Latest real research-system validation: 2026-05-29.

Runtime used:

```bash
PYTHONPATH=/Users/yukang/AI\ Statistician \
/Users/yukang/LeanProjects/LeanPractice/.venv/bin/python \
  -m ai_statistician.cli research-system-audit --real-lean \
  --runs 20 --out runs/research_system_real_lean_autoform_targets
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
proofs_verified=41/41
proofs_kernel_verified=41/41
proof_verification_strength=axle_lean_kernel
research_traces_ok=10/10
formal_gaps=20
formalized_gaps=20
autoform_targets=20/20
formal_source_graph_symbols=69308
formal_source_graph_edges=1361304
verifier_cache_hits=286
verifier_cache_misses=41
verifier_cache_size=41
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
