# Exponential Rate MLE L0 v1 Operator Audit

## Disposition

The single frozen exact-Haiku product draw is **failed, consumed, and closed**.
AgentRuntime completed the intended non-formal research graph and returned `ACCEPTED`;
the canonical research evaluation was capability-ready and mode-conformant. Frozen
evaluator-only gold then rejected the full task. The ladder result is `0/1`, and the
task must not be rerun, resumed, repaired, or rescored.

Run directory:
`runs/main_worker_research_l0_exponential_rate_mle_20260821_v1_codex_harness_exact_haiku`

Immutable evidence hashes:

- Runtime manifest SHA-256: `2f3089ebc3907964835c30100da7509a962dd805e5703e1a439a88ebe7f2b826`
- Hidden-gold report SHA-256: `1ce19550ce812eaa6b8001fcd3ce8dc7508a1205337730300afee82bc45b6894`
- Runtime result SHA-256: `dab4e9b5f89a4c00e9132e957fcea399d873ea9b6d79805eecc494f17b1cf2dc`
- Runtime failure summary SHA-256: `24cb04a35027713ddc327549df51ae6eeb6939955b1649c1b2c05b34e73c0ac6`
- Runtime completion summary SHA-256: `ce3474e807b803b9aed8ce577faf3993e03254d3e772a851699e994c27f00dc3`
- Runtime traces SHA-256: `369535c9fbd5a4d22d54cdd1d43e13a16faf08172ba100fd93e8fde96a3c40f6`
- Runtime handoffs SHA-256: `a3a931a020f28f303c2c23f9831e4144848e8342995041f247ad3bc4938752c3`
- Runtime tool calls SHA-256: `98e55f5ec85c1f38d138279c3d901001b36e410252b92ec51050941482ec5014`
- Runtime observations SHA-256: `9ac6d881348f1eca869a3dfc8494e1603671d8e747f5f6e214b983817e6cb2bb`
- Runtime progress SHA-256: `35bf3ba467b396b6e88866e6088bb2d76dbc6425c92d27cf7b85aee9b5f90bbe`
- LLM topology SHA-256: `fed9e7c299c28607e9035b293f3dbff6c0463121d9383ea93c18ced0ec2ebf3c`
- Theory document SHA-256: `d03556ca640aa70c4588329a7bad289a35ee5bf44f1d0af063fe0ce9915960a7`
- Estimator source SHA-256: `e9601cecbaad54dda86e2ba3bb4cb389886847e3cfc9d01066c976359c19407b`
- Simulation source SHA-256: `1e4b89a4c03845f204893c602d3da1dae5d87a16b2f1c40134954f544444eb63`

Every enabled LLM role used `claude-haiku-4-5-20251001`. No enabled role used
Sonnet or Opus, and no automatic model escalation occurred. Formalization was
`not_applicable`; no Formalizer or Lean lane ran.

## Live Trajectory

The run completed in eleven outer traces and ten handoffs. TheoryDeveloper used its
persistent Markdown/LaTeX workspace, recovered from one exact local-edit error, and
explicitly committed a 9,552-byte theory document. The isolated preflight referee read
the document and used its scratchpad. Its first segment made real workspace progress
but failed to submit a valid terminal envelope; the same hash-bound reviewer workspace
continued once and then accepted. Architect planning was not regenerated.

AlgorithmEngineer submitted source that failed real sandbox execution, received the
raw observation in the same model session, rewrote the complete source, executed it
successfully, and explicitly committed the unchanged accepted hash. The independent
source reviewer accepted those exact bytes. The metric author and blinded reviewer
froze a protocol, and SimulationEngineer generated and executed one exact source. It
made 65,020 calls to the accepted estimator and passed all eight runtime metric
contracts. Critic then accepted the runtime candidate.

This is direct evidence for the intended Codex-shaped inner loop:

```text
same source-owning model -> tool -> raw observation -> source revision -> explicit commit
```

No RepairAgent, deterministic content patch, routine Architect error route, second
scheduler, or task-family formula rule was involved.

## Frozen Gold Result

The post-termination evaluator observed the exact accepted artifacts and produced no
runtime feedback. Generic theory-structure checks passed `7/7`, but the calibrated
semantic judge returned `FAIL`, so theory was not gold-validated. The algorithm harness
executed successfully and five of seven manifest-level acceptance checks passed. The
formula, schema, output-domain, permutation, and positive-rescaling checks passed; the
public invalid-request contract did not. Hidden empirical assessment passed all eight
checks over 15,000 estimator invocations.

The resulting dimension vector is:

- theory: runtime reviewed, hidden semantic `FAIL`;
- scientific code: executed and runtime reviewed, hidden acceptance failed;
- empirical: hidden `8/8` passed;
- formal: not applicable;
- unresolved gaps: runtime disclosure present;
- full task: failed.

## Model And Reviewer Defects

The active theory document correctly states the standardized target
`sqrt(n) (lambda_hat-lambda) / lambda => N(0,1)`, but its preceding display applies
the total-sample information `n/lambda^2` as though it were per-observation information
and claims
`sqrt(n) (lambda_hat-lambda) => N(0, lambda^2/n)`. A nondegenerate fixed-parameter
limit cannot retain this sample-size factor, and the two displays are not equivalent.
The structured handoff also labels the rate estimators and exact interval endpoints as
`O(1/n)` even though numerator and denominator scale together and the quantities are
`O(1)` under a fixed rate.

The independent preflight report reproduced the same total-versus-per-observation
information error and marked the asymptotic claim `PASS`. Critic relied on that accepted
review and again called the theory internally consistent. These are correlated model
judgment failures, not proof or evidence promotion by the runtime.

The accepted estimator validates numerical values only after coercing the sample with
`np.asarray(..., dtype=float)`. Consequently a boolean sample entry becomes `1.0` and
is accepted, despite the frozen public request clause explicitly requiring boolean
rejection. Its formulas, response schema, permutation behavior, positive-rescaling
behavior, and empirical behavior were otherwise accepted by the frozen evaluator.

## Harness Assessment

No shared harness defect was found in this trajectory. The source-owner loops exposed
real execution errors to the same model; explicit commit separated execution from
acceptance; independent reviewers received artifact-only context; confirmatory outcomes
remained blinded during authoring; hidden authority became visible only after runtime
termination; and formalization did not block a non-formal task. The frozen evaluator
correctly distinguished successful orchestration and simulation from full-task
correctness.

Adding an exponential formula rule, Python-boolean special case, another reviewer vote,
larger retry allowance, or outcome-informed prompt patch would overfit this consumed
task and obscure the actual result: exact Haiku authored and then independently
false-accepted a mathematical inconsistency and missed one explicit ABI edge case.
Production may use Sonnet, but all scored tests remain exact Haiku as required.

Therefore there is no post-run mechanism commit. This audit and the ladder update are
evidence bookkeeping only. The focused ladder/gold/source panel passed `61/61`, and the
full local suite passed `820/820` in 68.30 seconds. The task remains immutable at `0/1`,
and the scored ladder becomes `0/21`.
