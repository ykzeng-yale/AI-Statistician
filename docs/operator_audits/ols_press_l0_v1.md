# OLS PRESS L0 v1 operator audit

Date: 2026-08-26

Task: `ols_press_leave_one_out_known_result`

Run:
`runs/main_worker_research_l0_ols_press_20260826_v1_codex_harness_exact_haiku`

Runtime source head: `769054e214df0c875399db59e7addcdc6150d1dd`

## Immutable disposition

This task received its one authorized product draw and one evaluator-only hidden
assessment. It is consumed at **0/1**. It must never be resumed, rerun, repaired,
hidden-evaluated again, rescored, or resampled.

All seven enabled model roles used exactly
`claude-haiku-4-5-20251001`. The topology records seven enabled Haiku roles, two
disabled formal roles with empty models, policy status `OK`, and no Sonnet,
Opus, or automatic escalation.

The product runtime ended `BLOCKED` after seven outer traces and six handoffs.
The terminal classification was
`architect_metric_requirement_packet_validation_failed`. Research evaluation
and hidden full-task evaluation both returned 0/1. Formalization was not
applicable and did not run.

## Component evidence

### Theory: passed hidden authority

The accepted theory packet was
`theory_derivation:2060d4c2a11825ea8fa8c6cd` with packet hash
`516538ffe16745c261c8619d57f5a2b3a12433aab50e04c1c28314e075add189`.
Its one authoritative Markdown/LaTeX document has SHA-256
`590faeced50b8c5307edfacb8ab987980d3160ce08af049cbfde276851a1efef`
and document-set hash
`3a40085631a52e40e9b61ebd799565c9daae5288d37856df35c967a8d6447432`.
TheoryDeveloper used 11 same-session model/tool turns and two scratch
executions. Runtime did not author or patch its mathematics.

The isolated pre-execution referee read the exact document five times, ran two
model-authored scratch checks, wrote a 20,663-byte Markdown report with SHA-256
`118e8d8339b242eb2eeec1feea5a624641a1447d91ecc67e4e69fc5cf4fb3067`,
and returned `ACCEPT` with no findings. The evaluator-only mechanical authority
passed 7/7. The independently calibrated exact-Haiku semantic judge passed all
10/10 frozen claims after classifying 14/14 calibration cases correctly. This
is trustworthy theory component evidence, not Lean proof evidence.

### Scientific code: failed

The accepted algorithm handoff was
`accepted_algorithm_handoff:7a3c5b00f02c4826a92f` with hash
`38696aa3b4500ea210b0753e40932bac29b9865509fecf7519476462c8893292`.
The evaluated source hash was
`ec0b9cdca95d4e088e29a40769007d06c7444b3d37ed550062d36e2db94de63e`.
It passed eight of nine hidden algorithm checks over 22 exact estimator
invocations. The sole failed check was `algorithm-invalid-rejection`.

Operator inspection confirms the defect. The source converts request values
with `np.asarray(..., dtype=np.float64)`, so numeric strings and booleans can be
silently coerced despite the public closed contract. It also clips leverage at
one instead of rejecting a delete-one rank-deficient domain. These are model
source defects, not hidden-harness failures.

The independent code reviewer used three model-authored probes. Its first two
failed before exact target invocation because the reviewer violated the probe
ABI. Its third probe invoked the target eight times and passed 15 self-chosen
checks, but omitted coercible inputs and delete-one rank failure. It then
accepted the source. A successful broad numerical probe did not cover all
public edge cases.

### Empirical: hidden component pass only

The independent hidden empirical evaluator passed 11/11 frozen checks over
four random-design scenarios and 2,000 exact estimator invocations. It used
independent Gram-matrix full fits and brute-force delete-one refits. This is
valid empirical component evidence for admitted finite designs. Runtime never
reached an accepted metric protocol or generated simulation, so empirical
status is `hidden_gold_passed_runtime_not_accepted` and cannot complete the
task.

### Formal: not applicable

No Formalizer, Lean, or kernel evidence was requested or executed. This neither
helps nor hurts the score.

## Harness diagnosis

The metric author wrote a 10 KB external JSON protocol and received exact
validation feedback in the same session. After a rejected commit reported the
missing comma at line 164, the same Haiku model produced the correct local edit.
The client-tool loop had already switched to terminal-only mode, rejected that
edit, and allowed only another commit of the unchanged invalid hash. This is a
generic lifecycle defect: fresh terminal validation feedback was available,
but the source owner was denied the existing recovery action.

The code-review failure is different. Runtime did not need a Python rule for
strings, booleans, leverage, or OLS. The reviewer needed enough model-owned
probe attempts and an explicit instruction to compare its successful tests
against every public request, response, invariant, and edge-case clause before
acceptance.

## Future-task correction

Commit `ea907357214d7193e59e87405a8917cecda5849d` changes only shared
future-task mechanisms:

- a terminal commit rejected during the ordinary workspace budget can use one
  already-configured recovery turn for one same-owner edit before the reserved
  final commit;
- the code reviewer receives six model-owned probe opportunities instead of
  three and is prompted to audit complete public-contract coverage rather than
  infer coverage from a passing test count;
- redundant, unconsumed client-loop telemetry was removed so top-level
  production Python remains 149,999 lines under the unchanged architecture
  limit.

No task formula, expected answer, type-specific validator, source patch,
RepairAgent, new agent, second scheduler, automatic retry, model-tier
escalation, or Task 53 score change was added. The source-owning model still
receives raw execution or validation observations and owns every edit. These
changes are future-task regression evidence only.

Verification for the mechanism commit: focused cross-workspace and core panel
215/215; complete repository 942/942 in 78.19 seconds; Python compile, diff
hygiene, architecture budget, model policy, and secret checks passed.

## Frozen artifact hashes

- runtime manifest: `e4fa167a6972eb401978a7af5e5d8835b37df9bcea5cfb6c7da305d5168c6839`
- runtime result: `955461b69af848210ee7cb17855b36a4be550ee7343a21f9fade07913b31ad70`
- topology: `595bf120541ddf515f8780b7d09883cd244805115f295892c0aa8a947460d9df`
- progress: `434e2d6f33e5fbed058fc0a70e1f1efcf6748df05fefb0f0d9c91c67f9ceaa87`
- hidden gold report: `3ccb0b5b9fa5d0b2748b534d830c69945e05c6d2e62acabe8570b30ecf9dea22`
- completion summary: `a827f456195ae47ce241caa3107ab7d4763101a3eb7a18b13d3c6a5099695169`
- failure summary: `015130fdb8e0c3ad236749e593798f2cb07a38b3a0ea66dab5304bfdd6b46e66`
- traces: `3ea44cae40df90c253055b9320b5ef656eafb1ee3446c075930124115898edea`
- handoffs: `26119513a834724d589a35f5475fbc2c9f272396aa8bfea1bcb5085dfd61ed50`
- observations: `62643754deb11fcf597ad872d58052b596777fa4a3ad6853fa42d89ff7b6a73c`
- outer tool calls: `1e412130cf6927b4c2355fd3c718b1ab972a134aba181983f60397fc6647779b`
- evidence ledger: `07d54d668b01ee943967accdc785ef53d84dab28545d5ad47b4ecf44be8f6d38`
- source snapshot: `d50a076404a473281ba40760905b4d9e398619b0c01d93faed0bf22c8955f239`

The operator disposition is
`OPERATOR_CONFIRMED_COMPONENT_STRENGTH_AND_SHARED_HARNESS_FAILURE`.
