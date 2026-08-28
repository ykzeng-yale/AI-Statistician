# Task 84 Operator Audit: Karlin-Rubin MLR and UMP Theory

## Immutable disposition

- Task: `karlin_rubin_mlr_ump_known_result`
- Frozen product code HEAD: `96ece9c0005b2fdc860c8929e54d8504df8a0acf`
- Run: `runs/main_worker_research_l0_karlin_rubin_mlr_ump_20260828_v1_codex_direct_theory_exact_haiku`
- Product runtime status: `ACCEPTED`
- Frozen automated full-task result: `0/1`
- Operator trustworthy full-task result: `0/1`
- Trusted aggregate after consumption: `4/84`
- Runtime model for every enabled role: `claude-haiku-4-5-20251001`
- Formalization: not applicable and not executed

This draw, its sole post-runtime hidden evaluation, and all source artifacts are
consumed and immutable. They must not be rerun, resumed, repaired, reevaluated,
rescored, resampled, or used as hidden feedback for the Task 84 source owners.

## Execution evidence

Frozen theory-only intent started directly in TheoryDeveloper without an
Architect planning call. The canonical graph used three outer nodes:

1. one TheoryDeveloper workspace with 18 model turns and 18 model-selected tools;
2. one isolated artifact-grounded theory preflight with 13 model turns and 13
   model-selected tools;
3. one terminal Critic workspace with 26 model turns and 25 model-selected tools.

The runtime labels the preflight node as owned by `ArchitectCoordinator`, but its
handoff states that AgentRuntime compiled the frozen route without another model
call. There was no Architect plan, scientific-code, Simulation, source-replication,
Formalizer, Lean, or kernel lane. All 57 product calls used exact Haiku. The theory
owner produced one 343-line authoritative Markdown/LaTeX document and explicitly
committed a hash-bound checkpoint.

Runtime research evaluation was `1/1` and mode-conformant. Hidden mechanics passed
`7/7`, while calibrated hidden semantics failed the complete candidate with `7/8`
claims satisfied. The violated claim was the required comparison with every
level-alpha competitor at every fixed alternative, so full-task theory did not
pass.

Key immutable hashes:

- Runtime manifest: `5570b65e22c83dacdd7ab2b7f1124fe10bdcd3455c8b21fc2bc18a3af55ce393`
- Runtime result: `fa3c2febf8609c2ef614fdfc304e0bb2e01c8bd7521e5d545adb2879a24f97fd`
- Gold evaluation: `67c9db8f43a0ca489f003fd601209e1a9f1f8b34bad87b80ba266370c245fb19`
- Theory document: `dceaed73969d88656f24c0b2a99ce52c01f263663f19c0ac0e1402f341b42fd8`
- Independent review: `a5fa0a3841226482a6c264f2c309b259c3368be6f9246491f6f5cbb83abec13a`
- Runtime progress: `1b7fe97be360a6d843abc6a67c9af063151a8867b3b31113b76a3dca433dc712`
- Runtime LLM topology: `05f09241e6612431fe1687ee6bcc55c419eab0917f19fcfebe3623502c5efcf6`

## Mathematical audit

The theorem is true under the frozen assumptions, but the active derivation does
not prove it.

1. The load-bearing Neyman-Pearson identification is invalid. The document says
   that, because a likelihood ratio is nondecreasing in `T`, its equality region
   is `{T=c'}` and the most-powerful test must have randomization only at that
   single value. A nondecreasing likelihood ratio may be flat on an interval, so
   the equality region can contain many `T` values. Neyman-Pearson permits arbitrary
   allocation on that entire equality region subject to the null-size constraint.

2. The document then claims that two upper-tail tests with null size alpha must
   have identical threshold and randomization because the quantile is unique.
   That is false in distributions with support gaps and is not enough to identify
   a particular Neyman-Pearson test on a flat likelihood-ratio region. The correct
   argument directly proves

   ```text
   (phi - psi) (h(T) - h(c)) >= 0
   ```

   on the lower tail, boundary, and upper tail, then combines it with
   `E_theta0(phi-psi) >= 0`. No such arbitrary-competitor sign argument appears in
   the active document.

3. The covariance proof contains a separate active equality error. For arbitrary
   `theta_2 > theta_1`, covariance gives

   ```text
   E_theta2 phi >= E_theta1 phi,
   ```

   but the document writes `E_theta1 phi = alpha`. Exact alpha holds only at
   `theta_1=theta_0`. The surrounding covariance calculation contains the pieces
   needed for monotonicity, but the stated equation is false.

4. An earlier attempted proof asserts that `h(c) >= 1`, discovers that no
   contradiction follows, and remains in the authoritative document beside the
   replacement argument. It is narrated as reconsideration but is not separated
   into a visibly rejected calculation as the public task requested.

The quantile existence and atom-randomization construction, correct covariance
identity, composite-null direction, theorem statement, and nonuniqueness/two-sided/
necessity scope are otherwise recognizable. They are component-quality mathematics,
not a completed proof of the requested UMP result.

## Referee and Critic audit

The isolated referee false-accepted the exact defects above. It repeated the false
`E_theta1 phi = alpha` step, asserted that the quantile pair is unique, treated a
flat likelihood-ratio equality region as a single boundary point, and still called
all proofs sound. Its numerical normal-family probes establish behavior in one
strict-LR example and cannot validate the general flat-region argument.

The terminal Critic read the theory and review artifacts repeatedly and made the
same false acceptance. It cited scratch execution as support while correctly
labeling it exploratory, but did not challenge the general proof that those probes
could not test. Product `ACCEPTED` is therefore orchestration completion, not
trustworthy theory capability.

## Harness conclusion

The intended Codex-shaped harness executed correctly:

- frozen single-lane intent bypassed routine Architect planning;
- one Theory model session owned Markdown/LaTeX, reads, exact edits, scratch, and
  checkpoint;
- raw observations returned to that same session;
- independent review and Critic used separate artifact-bound sessions;
- hidden authority remained outside runtime and failed the false-accepted result;
- formalization remained nonblocking because it was not applicable.

This draw diagnoses exact-Haiku mathematical judgment and independent-review
reliability. It does not justify a Karlin-Rubin formula, a likelihood-ratio parser,
another reviewer vote, a repair worker, extra turns, a retry, a scheduler, a model
escalation, or a Codex runtime dependency. No shared product mechanism change is
made from this consumed result.
