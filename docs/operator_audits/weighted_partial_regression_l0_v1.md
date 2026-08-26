# Weighted partial regression L0 v1 operator audit

Date: 2026-08-26

## Immutable identity

- Task: `weighted_partial_regression_identity_known_result`
- Family: `weighted_partitioned_regression`
- Activation commit: `a1ca9c327ed7606795a562ab4f86cc46a9e12139`
- Activation-record commit: `c2c90d288cc4d31c6ddc4b5000145afb0e770ea5`
- Visible question SHA-256:
  `5817665b04593050333c8cef56213d721a6be134d7024340be8a3ac85af6d8da`
- Frozen estimator contract:
  `frozen_estimator_execution_contract:da5628f0e9a63c44ecbf`
- Gold manifest SHA-256:
  `7255132932bd1425c42406522b88b2f6d5f4709fac01b9a07b238cad3a4a1f75`
- Gold manifest stable hash:
  `ea05b9730623636d6f05a79efcac023fcacfbd8ced0300d5f2d86f42b8a0a627`
- Run:
  `runs/main_worker_research_l0_weighted_partial_regression_20260826_v1_codex_model_owned_referee_exact_haiku`
- Runtime model: exact `claude-haiku-4-5-20251001` for all seven enabled
  roles; no Sonnet, Opus, or automatic escalation
- Runtime result: `BLOCKED` after 20 outer traces
- Hidden full-task result: `0/1`
- Operator disposition: `OPERATOR_CONFIRMED_THEORY_AND_HARNESS_FAILURE`

The task received exactly one product draw and one post-runtime hidden
evaluation. Both are closed and immutable. It must not be resumed, rerun,
repaired, hidden-evaluated again, rescored, or resampled.

Immutable SHA-256 values:

- Runtime manifest:
  `07b83d385237bafc242cb851a1679fd0404d5b010e976b75bd98c4346f1398a1`
- Runtime result:
  `571a1d4b07bb43e48ab175ae6053d49abcc8e8befc982eb89a998bfda0316b01`
- Runtime model topology:
  `daccd1d8eba12e7f067067c76eeb7568def7f9d5d2ccd2a18308b4d9481b88c6`
- Runtime progress:
  `888e973280af95c3342ab882571f7cb358415913189c42c3e666975683f10fd8`
- Hidden gold report:
  `71ed3cb86ca48768a625f26345e75f615a20188bceca78837a543ad89b57cfb9`
- Theory derivation document:
  `0b500abc9f591a8af88aa621e37687c1e680e616de7c3a77e936a77ab8f354b3`
- Estimator implementation document:
  `1c0890f2cdbfaebe718724f27d8ad090f6f64f1b47264065c9569f26b5b7086f`
- Last executed Algorithm source:
  `6a61f9c3fe36801e38df68944ca37e9f95c53e93909eb1db905e55581943f752`
- Hidden mechanical theory result:
  `e9fb7016375a0a3e6614cba3cca508f4aee873052143c4d2a0fbf74e3054cca7`
- Hidden semantic theory result:
  `0a41194131f183c2b34c89c13d90df24c8d6131314eeea16085f50fbd46097be`

## Runtime result

The product run made 126 native client-tool model turns plus two direct
Architect calls. It executed 129 model-selected client tools, 12 outer runtime
tools, 20 outer traces, and 19 handoffs. Every enabled model call used exact
Haiku. Formalization was correctly `not_applicable` and never ran.

TheoryDeveloper used one document-backed workspace, wrote two Markdown/LaTeX
documents and compact handoffs, ran three exploratory scratch calculations,
and committed a checkpoint. The isolated theory referee searched and read the
documents, ran its own scratch calculations, and accepted. AlgorithmEngineer
then executed one source, received a `REVISE` verdict, and its first same-owner
revision ended at a checkpoint-boundary mismatch. Runtime continued the still
unvisited Simulation lane. Three Simulation candidates executed, and each
independent review requested revision. Architect later routed through a theory
revision, metric authoring, and a fresh Algorithm candidate.

The final Algorithm source executed successfully, but its reviewer used three
probe attempts without recording one successful exact-estimator invocation.
After the ordinary probe budget was exhausted, it submitted `ACCEPT`. The
validator correctly rejected that disposition, but the configured terminal
recovery budget was zero, so the same reviewer could not consume the validator
observation and submit `REVISE`. The task terminated as
`generated_code_semantic_review_packet_invalid`.

## Hidden evaluation

The accepted theory packet was
`theory_derivation:0963e78721799da49c407e0f`, hash
`552daf32e6fe9bde2aaaa6fb262c17ec02c437e22cf221f35d404a1e619ed716`.
Its two authoritative documents were hash-bound as one set, but the frozen
mechanical theory harness passed only four of five checks. The structured
estimator spec renamed the public immutable ID from
`est_weighted_partial_regression` to `est.weighted_partial_regression` even
though the implementation Markdown used the correct public ID.

The calibrated exact-Haiku semantic judge marked ten of eleven theory claims
`SATISFIED` and the conditional-mean-and-variance claim `VIOLATED`. The theory
document temporarily asserted both `M_A z = z` and a denominator of `z'Wz`, then
later corrected itself. Those false active steps remained in the authoritative
derivation. The runtime referee noticed the issue but called it presentational
and accepted, despite its own protocol stating that a correct final result does
not cancel a false intermediate claim.

No Algorithm handoff was independently accepted. Consequently the evaluator
did not run the hidden Algorithm or empirical harness, and neither dimension
receives capability credit. This is not evidence that the last source was
correct. Manual inspection found that it converts inputs with
`np.asarray(..., dtype=float)` before type rejection, so numeric strings and
booleans can be silently coerced contrary to the public closed-object contract.

## Harness findings

Two shared defects are separable from the model's substantive errors:

1. The model-visible frozen estimator contract reached Theory, Algorithm, and
   Simulation prompts, but the Theory handoff validator did not bind its exact
   estimator identity. Downstream source and probe identities therefore followed
   a model-renamed ID. Frozen task identity, ABI field names, and field order are
   harness authority; formulas and implementation remain model-owned.
2. GeneratedCodeSemanticReviewer promises same-session validation feedback, but
   the CLI configured zero rejected-disposition recovery turns. The validator
   behaved correctly; the lifecycle did not. One reserved same-model terminal
   correction is needed only after an actually rejected disposition. It is not
   an extra scientific iteration, repair agent, or source rewrite.

The false theory, coercing source, rejected reviews, and failed score remain
unchanged. Any post-run code change is future-task mechanism evidence only.

## Capability accounting

This is the fifty-first consumed scored task and remains `0/1`. Four of 51
tasks retain trustworthy full-task capability credit. The task retains scoped
evidence that document-backed theory, Python execution, model-selected probes,
and optional-formal routing operated, but receives no theory, scientific-code,
empirical, or full-task credit.
