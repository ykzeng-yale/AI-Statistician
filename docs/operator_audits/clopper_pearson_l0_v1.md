# Clopper-Pearson L0 v1 operator audit

Date: 2026-08-26

Task: `clopper_pearson_binomial_interval_known_result`

Run:
`runs/main_worker_research_l0_clopper_pearson_20260826_v1_codex_harness_exact_haiku`

Runtime source head: `254a7aef345bc780bbe3d9fa71dbf32c6c49480d`

## Immutable disposition

This task received its one authorized product draw and one evaluator-only hidden
assessment. It is consumed at **0/1**. It must never be resumed, rerun, repaired,
hidden-evaluated again, rescored, or resampled.

All seven enabled model roles used exactly
`claude-haiku-4-5-20251001`. The topology records seven enabled Haiku roles, two
disabled formal roles with no model, policy status `OK`, and no Sonnet, Opus, or
automatic escalation.

The product runtime ended `BLOCKED` after 33 steps: 32 outer-graph iterations
and one same-owner continuation. The terminal classification was
`theory_developer_reported_gap`. The hidden full-task evaluator returned 0/1.
Formalization was not applicable and did not run.

## Component evidence

### Theory: failed

The accepted theory packet was
`theory_derivation:dcec30e6a486e1dc77a0ab46` with packet hash
`d884a5882e35736f488929483e6593b459b6691c600f62e0bdac052f0b7e7c6e`.
Its document manifest referenced mutable workspace files. Later TheoryDeveloper
work changed `clopper_pearson_theory.md`, so evaluator hydration correctly
failed closed on the document hash mismatch.

Operator inspection also confirms substantive mathematical defects in the final
document, independent of that lifecycle failure:

- lines 46-55 reverse both beta-binomial CDF identities;
- lines 91-96 use incorrect inversion inequalities and do not prove the coverage
  event bound;
- lines 121-125 reverse endpoint monotonicity in alpha and then state mutually
  inconsistent nesting directions.

The final TheoryDeveloper honestly stopped on a beta-binomial duality gap. Its
gap explanation still states a confused replacement identity, so it is gap
disclosure, not a mathematical correction.

The independent referee was not reliable. It declared the theory coherent,
called the incorrect identities correct, and described its numerical scratch in
the opposite direction from the active document. Automated referee acceptance
therefore receives no theory capability credit.

### Scientific code: failed

The evaluator attempted all 11 hidden algorithm checks against source hash
`1a7187842d7e0a6138de4c674632d45cc0e5870b01b8a9f42cf827461db00922`.
The scientific runner then failed to serialize nested NumPy boolean scalars, so
all check rows were recorded false and the bound-estimator invocation record was
lost. This is a genuine shared transport defect in the frozen evaluation path.

The transport defect does not make the candidate a pass. Operator inspection
confirms that the final estimator accepts undeclared extra request fields, while
the public ABI requires an exact closed three-field request object. An earlier
reviewed candidate rejected extra fields, but duplicate outer-lane regeneration
replaced it with the regressed source.

### Empirical: component pass only

The independent hidden empirical evaluator passed 8/8 checks over four frozen
scenarios and 16,213 exact estimator invocations. This is valid empirical
component evidence. Runtime did not reach a final accepted empirical state, and
required theory and scientific-code dimensions failed, so the component pass
does not complete the task.

### Formal: not applicable

No Formalizer, Lean, or kernel evidence was requested or executed. This neither
helps nor hurts the score.

## Harness diagnosis

The failure exposed four shared mechanism defects:

1. Accepted Theory manifests pointed at mutable workspace paths instead of
   content-addressed checkpoint files.
2. A stale top-level deferred-task manifest ID could overwrite the newer
   accepted identity in canonical `architect_context`.
3. Reviewer-to-source `REVISE` backedges were checked after unvisited-lane
   topology, allowing routine local revision to be bypassed.
4. Estimator-bound simulation normalized callback inputs but not the complete
   model-authored result before JSON serialization.

The same run also shows a capability problem that harness changes cannot solve:
the TheoryDeveloper and isolated referee did not reliably reason about a
standard distribution identity and coverage proof.

## Future-task correction

Commit `54e5ca52eca6192885a8a11775f7728997610ac7` changes only shared
future-task mechanisms:

- Theory manifests resolve to content-addressed file snapshots;
- canonical accepted context wins over stale deferred top-level IDs;
- a valid reviewer backedge returns directly to its exact source owner before
  outer topology continues;
- estimator-bound Python results receive the existing recursive JSON-native
  normalization before transport.

The source-owning model still receives raw observations and owns every theory or
source revision. No formula, statistical answer, Lean rule, content patch,
RepairAgent, model retry, task-family branch, second scheduler, or model-tier
escalation was added. These changes are future-task regression evidence only and
do not alter this task's score.

Verification for the mechanism commit: affected files 157/157; complete
repository 939/939 in 83.06 seconds; Python compile, Node syntax, diff hygiene,
architecture budget, model policy, and secret checks passed. The canonical
runtime is 24,986 lines and top-level production Python is 149,999 lines under
the unchanged limits.

## Frozen artifact hashes

- runtime manifest: `4bd55c15351e1e98236cd3795e7f9e31cb58aec3b818f1b69c001580fca4e3cb`
- runtime result: `4e7e2da35a7edabdeff4bcc4e6106cea13746790a462964fa4e95fb46d48010c`
- topology: `515402b2428a11d43248f6194b971231ed3b87a7c977a53adb90199e53df0392`
- progress: `6500b165fc5f9f3a42e390a63d573f12d47ae54bff98745605a72df01ba7d93f`
- hidden gold report: `75300d554434e0b54caa98bb3ea1a17d16db693ab0c67c7ca7653ccc781232b3`
- completion summary: `2967d4edec47cb17301c0428d004e752a4244f3351d2e54c7d2fd3e6d7bcb4be`
- failure summary: `1cf34513d7f60f71e2673ca0a01e13c15d395a9b4d0709f6e3e7b1b1af0dce3e`
- traces: `07233577cfcba64ddabe7e8741594c37d1a8963fc7d128640269a41ba61fbdae`
- handoffs: `5a459d0ce584e3a55ee0979ce9f43cb996b812dab79b4be476e028b111b755b1`
- observations: `f292f28226728f82ec7ed56293725b0b258e9e803944d04e52921ecd9d236a22`
- outer tool calls: `4b46d8f6f76155c75c85e59d723ab4fb176ad36169abcb49e941a5b777edf0d1`
- evidence ledger: `7db78d59ae02d410f3d6e2ec5ed61163778622355ccc5aac54f7abfeac7ac48c`
- source snapshot: `d50a076404a473281ba40760905b4d9e398619b0c01d93faed0bf22c8955f239`

The operator disposition is
`OPERATOR_CONFIRMED_CAPABILITY_AND_HARNESS_FAILURE`.
