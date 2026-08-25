# Fixed-design ridge bias-variance L0 audit

Date: 2026-08-25

Task: `fixed_design_ridge_bias_variance_known_result`

Public reference: A. E. Hoerl and R. W. Kennard, "Ridge Regression:
Biased Estimation for Nonorthogonal Problems," Technometrics 12 (1970),
55-67, DOI `10.1080/00401706.1970.10488634`.

## Frozen authority

- Visible task: `benchmarks/research_l0_ridge_bias_variance_questions_20260825.json`
- Visible file SHA-256: `e4bd8b5aa706565321a36036700d15e19eb4a63f9bc189cc0be54e65048041ff`
- Visible question hash: `cf1ea140b28c6a0579266e95e5510cb0099be39e7c00118c888d4586bc77ab46`
- Estimator contract: `frozen_estimator_execution_contract:19dbc5b7091fc69827e8`
- Evaluator-only manifest SHA-256: `6f977e367f5c110f9960767718f8e8c38af16501a5d797e8432cb3b15c4bb800`
- Gold descriptor hash: `a46c2e1edcddb7495baa80188ffc312085c491af94568a780b372c67de5a75bc`
- Visible activation commit: `bf599f4b19ae45bc0ebe8e0b707360188b64c721`

The visible task and external evaluator authority were frozen, calibrated, and
the visible commit was pushed to both canonical refs before the first product
model call.

Mechanical calibration before activation recorded:

- reference algorithm checks: 7/7;
- generic incorrect implementations rejected: 4/4;
- reference empirical DGPs: 2/2;
- reference estimator identity checks: 10,000;
- hidden Theory structure checks: 7/7;
- exact-Haiku semantic calibration cases: 12/12;
- exact-Haiku reference claims: 9/9 satisfied.

Calibration is evaluator-authority evidence, not product capability evidence.

## Single fresh draw

Run:
`runs/main_worker_research_l0_ridge_bias_variance_20260825_v1_codex_checkpoint_exact_haiku`

- Runtime model for every enabled role: `claude-haiku-4-5-20251001`
- Product model calls: 26
- Outer iterations: 6
- Terminal status: `BLOCKED`
- Failure classification: `generated_code_semantic_review_packet_invalid`
- Formalization: not applicable and not invoked
- Full-task result: 0/1
- Research ladder after consumption: 0/29

The TheoryDeveloper used its durable Markdown workspace for 12 model/tool turns.
It produced a 206-line derivation with SHA-256
`4301d0e2d265968925c39d1b1ee9e3b4a106668d294e403fda804022d1b5dc1a`.
The isolated Theory referee used 10 model/tool turns, wrote a 281-line Markdown
report with SHA-256
`fdc6a5b4c598004f8003ffb30ae5ff5dedc40ddd8a35956a7b22f21328627e13`,
and accepted the checkpoint for downstream diagnostic execution.

Post-termination hidden theory evaluation observed:

- structural and lineage checks: 7/7;
- semantic claims satisfied: 8/9;
- semantic candidate status: `INCONCLUSIVE`;
- combined hidden theory acceptance: false.

AlgorithmEngineer then used two native model/tool turns. Its 202-line generated
Python source had SHA-256
`f84a9e96b6b8b26e642eda9cd6cccb128b33f5ef446e99dfe4a49c72098d5691`.
The isolated scientific sandbox loaded NumPy and SciPy, executed the source, and
reported all visible smoke invariants passing. That is execution evidence only;
the source was not independently accepted.

## Measured blocker

GeneratedCodeSemanticReviewer made one provider-native structured-output call.
Its substantive verdict was `ACCEPT`, but five entries in
`source_revision_assessment.evidence_refs` were human-readable descriptions
rather than pointers into the supplied evidence document. Runtime correctly
rejected the envelope. The old single-shot transport then blocked the entire
task instead of returning those exact validation observations to the same
reviewer context.

Because no independently accepted algorithm handoff existed:

- hidden algorithm execution was not attempted;
- generated confirmatory simulation was not attempted;
- hidden empirical execution was not attempted;
- Critic did not produce the required unresolved-gap disclosure.

The evaluator therefore records 0/1. A visible sandbox pass cannot substitute
for independent semantic review or hidden scientific evaluation.

## Shared correction

For future disjoint tasks, GeneratedCodeSemanticReviewer now submits through the
existing native client-tool loop. Runtime-invalid pointer or lineage fields are
returned as `is_error: true` observations to the same isolated reviewer session,
matching the OpenAI Codex distinction between model-actionable tool failures and
fatal harness failures. The model may submit one corrected complete judgment;
repeated invalid submission still fails closed.

This change does not edit review content, generate source, invoke Architect,
add a repair agent, add task-specific ridge logic, expose hidden gold, or create
a second scheduler. This consumed task will never be rerun, resumed, repaired,
or rescored.

## Artifact hashes

- Runtime manifest: `7171637d73300aebfedcfc2c9335e84153d6286a5313eb20c5fa768038088b55`
- Hidden gold report: `08e38e9ed9a8f3eb7e4729cad8760befc237fd443fd8e2e6e45f23b55ffca9c2`
- Completion summary: `6771e6e29d42fc6942d3dec03e22f57d9bdac850c02f33650d5f47217745055f`
- Failure summary: `9bee7e3a62d76120e725fcb40044e02ca2f2b591faeaedf43933a33cab47ba6b`
- Model topology: `99b7b0da0f5a6546ed6d43065633a5be470ec016fa37b49edc199a74e59c49b1`
- Progress log: `d1405ea9a23bd762cc76aa537d5d64f3989e4a4f70b895bc4cc542baf1580d65`
- Runtime traces: `6a1f48dd6debfa88650e1d7e3a18f70c1f24609422712a22a842f0a36c89710f`
- Task handoffs: `7f68e33767c9d3475372546682e81da436301a60a9fa75653f1db2dfa9e0774d`
- Runtime observations: `16d968805b23d8f3e5fe1568ddefd9c326ecc9bd305b799aac7402abc01441e3`
- Runtime result: `6013b3688a74f55d7b3f4dab807a3afe3187ece72adc3f9c75eb744be74c41a9`
