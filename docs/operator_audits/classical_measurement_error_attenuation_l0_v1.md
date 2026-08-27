# Classical measurement-error attenuation L0 v1 operator audit

## Immutable evaluation boundary

- Task: `classical_measurement_error_attenuation_known_result`.
- Product draw: exactly one fresh `research_eval` run using
  `claude-haiku-4-5-20251001` for every enabled model role.
- Runtime status: `BLOCKED` after ten outer-graph iterations.
- Runtime research evaluation: `0/1`; mode conformance: `1/1`.
- Hidden evaluation: exactly one evaluator-only pass after runtime termination,
  with full-task result `0/1`.
- Formalization: not applicable and not executed.
- The run must never be resumed, rerun, repaired, hidden-evaluated again,
  rescored, or resampled.

Run directory:
`runs/main_worker_research_l0_measurement_error_attenuation_20260827_v1_codex_workspace_exact_haiku`.
The runtime head was
`43b97dbf940ef2789675b7c83dbf8fce5267d03a`. The runtime manifest SHA-256 is
`52befe0bb5b4fa6ead7f4b30242185dfb8ebdc5f209d0157546913a2f627d968`,
the runtime-result SHA-256 is
`c0aae56ff1d35e812aebce3049c90d3e9a91ccc64e9c9467c60d58b89bfa1ef5`,
and the hidden-evaluation SHA-256 is
`3a00bd04ae31d49e30b1dd21866c570a8f4478483ce8e4be156d01a92a3ed699`.
Hidden authority generated no runtime feedback.

## Theory result

TheoryDeveloper used one persistent Markdown/LaTeX workspace containing
`theory_derivation.md` and `estimator_implementation.md`. It correctly derived
the population attenuation factor, identified and corrected the slope using
known measurement-error variance, derived the sample formulas, and covered
zero-error, sign, translation, scaling, and nonpositive-denominator behavior.

Frozen authority passed all `7/7` mechanical checks. The exact-Haiku semantic
judge passed all eleven calibration cases and all eight candidate claims in one
integrated candidate call. The theory packet hash is
`7ea67c9f1cdc4506e7796f50234d1d744de28f5dba93b0d822e27ad1af75489b`,
the document-set hash is
`3736f29444fbf7fc60e0f7fafb48a49a8a77bcb9067c79624b1409d6d27407e4`,
and the two file SHA-256 values are
`43d21687b3c05ae185e94798484b41390a29ece65807ed464395d7a6ea18ce0a`
and
`b91eec1e9fc43b0e30b76e0648798f3ccd9d699421ad928ad9a218bafc3ad4b5`.
This draw supports the current document-authoritative Theory workspace; it does
not justify another Theory packet layer.

## Scientific-code result

The model-authored estimator computed the six requested statistics correctly,
but added an unsupported rejection at source lines 73-75:

```text
if np.allclose(Y, Y[0]):
    raise ValueError("outcome is constant; covariance is zero")
```

The closed public contract permits zero sample covariance, zero naive slope,
and zero corrected slope. The independent reviewer nevertheless asserted that
constant-outcome rejection was required and accepted the artifact. Its three
model-authored probes all failed before invoking the target estimator, so they
provided no boundary evidence.

The hidden algorithm harness reached the constant-outcome edge first, terminated
with that `ValueError`, recorded `0/15`, and made zero accepted-estimator
invocations. The evaluated stable source hash is
`1917042dfbf8294a6d6eccbbf11b25d79bc801a0a51c93bb60774f99e69087bf`;
the exact file SHA-256 is
`47d0f3846ce405bf16b444e3b08d16553b14ba5c9585ad70c60fc37349aed891`.
No constant-outcome rule or measurement-error repair belongs in runtime. The
general lesson is that a reviewer may not invent stricter rejection behavior
than the supplied question, theory, and closed interface support.

## Simulation collaboration result

Runtime had a hash-bound accepted Algorithm handoff, but both exploratory
Simulation manifests recorded empty `required_estimator_ids`, empty
`available_upstream_estimator_ids`, no bound source hashes, and an empty handoff
receipt. The Simulation workspace reimplemented the estimator instead of calling
the accepted Algorithm artifact. Thus its exploratory checks could not expose
the accepted estimator's constant-outcome error and were not valid cross-workspace
integration evidence.

The first Simulation review correctly noticed the upstream constant-outcome
restriction and seed/replicate issues. After the source revised seed handling,
the second review explicitly said that all blocking defects were absent and the
artifact was semantically fit. It nevertheless placed one low, nonblocking
`replicates` documentation note in structured `findings`, forcing `REVISE` and
exhausting the source lineage. The revised source already documented that
`replicates` was not used for exploratory checks.

The hidden empirical component independently passed `11/11` over 16,000
accepted-estimator invocations. That is evaluator-only component evidence. The
runtime did not accept confirmatory empirical evidence or unresolved-gap
disclosure, so the empirical and overall task dimensions remain failed.

## Shared future correction

Commit `464cba39753ff2959e5d0f2c08491c982745cc60` makes one existing handoff
available to exploratory Simulation whenever it validates. Early Simulation is
still allowed when no Algorithm artifact exists, and confirmatory Simulation
still fails closed without one. Existing estimator binding then requires the
model-authored Simulation source to select and invoke accepted exact source.

The semantic-review prompt now defines structured findings as active defects
that make the current artifact unfit for downstream use. Nonblocking observations
stay in the model-authored Markdown review. It also tells the reviewer not to
invent unsupported rejection conditions. The model still chooses checks,
probes, semantic fitness, findings, and source changes; runtime adds no severity
route or content repair.

This is selective reuse of the official Codex harness boundary: preserve
explicit artifact context across a specialist handoff, keep tool observations in
the same source-owning session, and use a compact typed envelope around
model-authored work. It adds no measurement-error formula, constant-outcome
special case, source patch, RepairAgent, retry, extra reviewer, task-family route,
provider, model escalation, Codex App Server, or second scheduler. The complete
repository passed `985/985`; production Python is 149,993 lines. Task 66 was not
rerun, resumed, repaired, hidden-evaluated again, rescored, or resampled.

## Disposition

`CODE_CONTRACT_FAILED_SIMULATION_HANDOFF_AND_REVIEW_BLOCKED`

The task receives `0/1` trusted full-task capability credit. Aggregate
trustworthy capability remains `4/66`, and exact development theorem closure
remains `0/2`.
