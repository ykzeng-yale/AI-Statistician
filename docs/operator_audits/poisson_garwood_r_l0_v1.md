# Poisson-Garwood R L0 v1 operator audit

## Frozen authority

- Task: `poisson_garwood_rate_interval_r_known_result`
- Public source: F. Garwood (1936), *Fiducial Limits for the Poisson
  Distribution*, DOI `10.1093/biomet/28.3-4.437`
- Visible question SHA-256:
  `7d44c1145c8b821301a65da0f644a51776200d419d26669b4e7bfdfc17042d8d`
- Evaluator descriptor:
  `f6c1ca29ca9be25ccd97e0a5030286640e21d00e041f55dce8ac6bcfc45fcdf1`
- Activation commit: `158bb602cb5719ee611baad6865a16c70243f8e1`
- Model for every enabled live role: `claude-haiku-4-5-20251001`
- Formal evidence: `not_applicable`

The visible task and evaluator-only gold were calibrated, frozen, and pushed
before the first product-model call. Gold remained outside the repository,
runtime RAG, and model workspaces. The task was consumed exactly once. It must
not be rerun, resumed, repaired, or rescored.

## Runtime result

The canonical runtime terminated `ACCEPTED` after ten outer traces. Product
research evaluation was complete, mode-conformant, and ready. Every enabled
role used exact Haiku; Formalizer and the Lean lane were inactive.

TheoryDeveloper used one persistent workspace for 13 model turns and committed
two authoritative Markdown/LaTeX documents totaling 287 lines and 12,409 bytes.
The isolated preflight referee accepted them. Hidden mechanical theory checks
passed `7/7`, and the calibrated paragraph-grounded semantic judge passed all
eight claims after `12/12` calibration.

AlgorithmEngineer stayed in one source-owning session. Its first R submission
was rejected because the declared entrypoint did not match the executable
source; the raw error returned to the same model. Its next complete source ran
under WebR, and the model committed the exact observed hash. The accepted R
source used the required `run_estimator(request)` ABI and the final algorithm
and simulation sources were independently reviewed. SimulationEngineer then
authored R source, invoked the accepted estimator mechanically, and ran 10,000
confirmatory replicates per selected protocol. Runtime metric contracts passed
`8/8`; the isolated simulation reviewer accepted; Critic returned `ACCEPT`.

This is integrated evidence that the same canonical product path can develop
Markdown theory, generate and revise R, execute WebR, bind an R estimator into
an R simulation, and keep formalization nonblocking. There was no Python
substitution, RepairAgent, source patch, second scheduler, task formula, model
tier escalation, or post-runtime scientific fallback.

## Hidden evaluation

The immutable full-task result is `0/1`:

- theory structure: `7/7`;
- calibrated theory semantics: `8/8 SATISFIED`;
- algorithm checks: `8/10` across 35 estimator invocations;
- empirical checks: `6/6` across 105 estimator invocations;
- required failing dimension: `scientific_code`;
- formalization: `not_applicable`.

The hidden algorithm formula, output schema, endpoint ordering, zero-count
boundary, exposure scaling, confidence nesting, count monotonicity, and numeric
accuracy checks all passed. The failed atomic result was
`invalid_requests_rejected`; the other failed row was its aggregate
`all_contract_checks_passed` parent.

## Scope defect

Static inspection of the exact accepted source and the frozen hidden harness
isolates the failure. The R estimator rejects the visible contract's missing,
logical, fractional, negative, nonfinite, nonscalar, and out-of-range inputs.
It accepts a request containing the three valid fields plus one unexpected
field. The hidden harness scored that extra-field case as invalid.

The frozen visible Poisson contract never said that the request object was
closed or that extra fields must be rejected. Unlike earlier ladder tasks, its
description also omitted an "exactly these fields" requirement. Therefore the
score remains the precommitted `0/1`, but this specific failure is not evidence
that Haiku violated the public ABI. Runtime reviewers and Critic were correct
to assess the visible contract; the operator made the benchmark-freeze error.

For future disjoint tasks, hidden invalid cases are audited atomically against
explicit public clauses before activation. Aggregate checks may summarize
those cases but cannot add behavior. No product prompt, runtime parser,
hardcoded rejection rule, additional model turn, or repair route is added, and
this consumed task receives no new draw or score change.
