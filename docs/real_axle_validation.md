# Real AXLE Validation

Latest real proof-bank validation: 2026-05-29.

Runtime used:

```bash
PYTHONPATH=/Users/yukang/AI\ Statistician \
/Users/yukang/LeanProjects/LeanPractice/.venv/bin/python \
  -m ai_statistician.cli proof-audit --real-lean \
  --out runs/proof_audit_real_full_31
```

Result:

```text
verified=31/31
kernel=31/31
verifier=axle.verify_proof
strength=axle_lean_kernel
```

This is the current evidence that the registered proof bank is not only
mock-checked: all 31 registered Mathlib-backed obligations were accepted by
AXLE/Lean-kernel verification in the real external runtime.

Latest real research-system validation: 2026-05-29.

Runtime used:

```bash
PYTHONPATH=/Users/yukang/AI\ Statistician \
/Users/yukang/LeanProjects/LeanPractice/.venv/bin/python \
  -m ai_statistician.cli research-system-audit --real-lean \
  --runs 20 --out runs/research_system_real_lean_cached_31
```

Result:

```text
all_gates_passed=True
proofs_verified=31/31
proofs_kernel_verified=31/31
proof_verification_strength=axle_lean_kernel
research_traces_ok=10/10
proved_research_subclaims=62
kernel_verified_research_subclaims=62
mock_verified_research_subclaims=0
formal_gaps=20
verifier_cache_hits=158
verifier_cache_misses=31
verifier_cache_size=31
```

The research-system run proves that `--real-lean` now flows through the actual
open-question workflow, not only the standalone proof-bank audit. It verifies
available registered subclaims with AXLE, writes research traces whose proved
subclaims are marked `kernel_verified=true`, and still leaves frontier theorem
claims as explicit formal gaps.

Important boundary:

- These are finite, reusable Mathlib-backed estimator/probability/statistical
  subclaims.
- This does not prove full frontier asymptotic theorem goals such as CLT,
  semiparametric efficiency, Donsker conditions, BH FDR, Ville inequality,
  Davis-Kahan recovery, or Hill/Weissman asymptotics end to end.
- `runs/` artifacts stay local and are not committed; regenerate with the
  command above when auditing a release.
