# Bootstrap-mean L0 v1 operator audit

## Frozen authority

- Task: `nonparametric_bootstrap_mean_variance_known_result`
- Public reference: Bradley Efron, *Bootstrap Methods: Another Look at the
  Jackknife*, The Annals of Statistics 7(1), 1979, DOI
  `10.1214/aos/1176344552`
- Visible question SHA-256:
  `8de9eb8f3ce52fe93436a3db2b2f4239b8f7b490c72e795210ad9acfeb085d35`
- Visible question hash:
  `fadf0cad9f994bb6e594703f2ce5830384c9cebbaf96778d780b7f9f618c2dda`
- Evaluator descriptor:
  `7c1c5be3b4df99de1adb31d53dc74f244cceff8db988928bc81a7a952eb26bb0`
- Activation commit: `6034652636448eaf76bcd3eefe1b8fea00501130`
- Runtime code head: `799d777c0262d5e314e9524b5cd49b302811e147`
- Model for every enabled live role: `claude-haiku-4-5-20251001`
- Formal evidence: `not_applicable`

The public task and evaluator-only gold were calibrated, frozen, committed,
and pushed before the first product-model call. The task received exactly one
fresh model draw and one post-termination hidden evaluation. Its immutable
full-task score is `0/1`; it must not be rerun, resumed, repaired, or rescored.

## Runtime result

The canonical runtime terminated `BLOCKED` after ten outer traces, including
three Architect traces. It executed one generated algorithm and one generated
simulation. Research evaluation was `0/1` but mode-conformant; terminal
classification was `critic_scientific_rejected`. Formalizer correctly remained
inactive under task intent.

TheoryDeveloper used one persistent Markdown/LaTeX workspace for twelve
model/tool turns. It wrote two authoritative documents, ran two Python scratch
programs, and explicitly committed the checkpoint. The authoritative document
set hash is
`1565d83a47ce15b7d411cb0f64afeeabcb23db1ebfd92d2bf181db15bfc666b7`.

The isolated referee first wrote a blind reconstruction with SHA-256
`5e23385aeed2f1255db4e39271ff54c0587181a1df2e7ce343798d9cce980720`,
then inspected seven exact candidate-document ranges and revised the same
Markdown report. The accepted report SHA-256 is
`535a72db149e8be4bab053e852ae75f1bff635a7d770282be7633cc36629eb6d`.
This is the first disjoint live evidence that the blind-reconstruction
chronology introduced by `b9ece439` works end to end.

## Hidden evaluation

The immutable hidden result is `0/1`:

- theory structure: `7/7`;
- calibrated theory semantics: `7/7 SATISFIED` after `9/9` calibration;
- algorithm acceptance: `12/13`;
- exact empirical checks: `6/6`;
- runtime simulation contracts: `7/8`;
- unresolved-gap and runtime research completion: failed;
- formalization: `not_applicable`.

The accepted estimator source hash is
`b03836b16ea225486a727c0a1c445b1420b65ed801bfa14c6b9923976a12576f`.
Its statistical identities and every hidden empirical check were correct, but
the source calls `float(value)`. It therefore accepts a numeric string such as
`"2"`, contrary to the explicit public instruction not to coerce entries. The
algorithm reviewer nevertheless wrote "No silent coercions" and accepted the
source. This is a model-owned source-testing and review false positive, not a
reason for a runtime type patch or Python-specific coercion rule.

The generated simulation source hash is
`29873da94e34403e4f45065cd27a52e16d4e2498e6ae9938e2fd96f0f3899b16`.
It used exact `==` comparisons for floating variances after a location shift,
so `location_equivariant` failed while the other seven frozen contracts passed.
The source-owning session had seen only a blinded smoke-success observation and
committed after two turns; it never received this ordinary pre-confirmatory
diagnostic failure.

The simulation reviewer was nominally assigned the simulation artifact, but
its 220-line report was titled `est_bootstrap_mean_variance`, cited the upstream
estimator hash, and accepted the estimator rather than examining the current
simulation source. Its report SHA-256 is
`cace2ff3a3a1730a4302edf7987d7a79960f4929f589169d64f23e55856ee3ac`.
This is a current-target versus upstream-dependency focus defect at the review
boundary. It must be fixed by clearer exact artifact ownership, not by another
reviewer or a task-specific diagnostic.

## Shared conclusion

The Theory workspace and blind referee chronology worked. The scientific-code
failure localized two generic Codex-style lifecycle gaps: a source owner should
see raw exploratory execution diagnostics before explicitly committing exact
source bytes, and a reviewer must treat the current executed artifact as its
target while using upstream source only as dependency context.

Post-consumption commit
`26b8e12449aac0f4b6f031cf65896768ae7316ac` implements those shared boundaries
for future tasks. One source-owning Simulation session now receives a separate-
seed exploratory diagnostic, may revise, and explicitly commits. The exact
committed bytes then execute once on the blinded confirmatory cohort, whose
outcome is never returned for result-informed rewriting. The existing reviewer
prompt names the exact executed artifact as the target and the accepted
estimator as context only.

The change adds no agent, scheduler, retry, task formula, numeric detector,
source patch, or model escalation. `882/882` tests passed. This is future-task
mechanism evidence only and cannot change the bootstrap task's immutable `0/1`.
