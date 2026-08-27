# Uniform spacings Dirichlet L0 v1 operator audit

Date: 2026-08-27

## Immutable identity

- Task: `uniform_spacings_dirichlet_known_result`
- Family: `order_statistics_uniform_spacings`
- Visible-question commit: `139772781eca0b7acbb0809aa0b6434645b70d88`
- Authority-binding commit: `855641ced4205b5f8fb97c03f3cc18bb993986a4`
- Activation-seal and run head: `c19816e141713c2f388ef4365fb2ea7bd9aa7123`
- Run:
  `runs/main_worker_research_l0_uniform_spacings_20260827_v1_codex_workspace_exact_haiku`
- Runtime model: exact `claude-haiku-4-5-20251001` for all seven enabled
  roles; no Sonnet, Opus, or automatic escalation
- Runtime result: `BLOCKED` after seven outer traces
- Frozen full-task result: `0/1`
- Trustworthy capability result: `0/1`
- Operator disposition: `OPERATOR_INVALIDATED_ACTIVE_THEORY`
- Future-task shared mechanism commit:
  `24de629178cb2c8214dcefe5c553ef1015378052`

The task received exactly one product draw and one post-runtime hidden
evaluation. It is closed and immutable. It must not be resumed, rerun, repaired,
hidden-evaluated again, rescored, or resampled. Hidden findings did not enter the
runtime context or generate revision feedback.

Immutable SHA-256 values:

- Visible question: `4a856b1684b5dfdfa0f0e723f70aa21b21cae19988e79a69e66272ed9170f53d`
- Runtime manifest: `23ec810f89f98dc022a659cb695d5710ccf384601f6afacf21ff6b7c51599f5d`
- Runtime result: `0a1d91dd90e8758b9f3b09cfca8844c7495e7e57b3a32894fa98650689c5fa61`
- Runtime completion summary: `7c9a1bd1bab17e850e4eca3f0dbf9b5de05fce6868e0859f0f96448b6e83fced`
- Runtime failure summary: `c4a9b97c31fef0fa26aac5803a0b19f0ea6e8e89a6c7864440037dc6f8fd4b27`
- Runtime model topology: `a68c729fa3df7633510d69d14e1480fce1106a51db4b8615e120b12fd034f37b`
- Post-runtime gold evaluation: `5b32eef288cd9a6f0cc68fb67dfd655e32f0b63ee1f9d64c37029ceca2df5687`
- Theory document: `e68e331670668f79eeb42e3ee435d30602dc54f6135d9ee40410ea681cd8ab09`
- Estimator document: `9551476d1443a5290e5c0f61818cc876ee935b0ba846cb4300608d453725945a`
- Theory client-tool session: `42427b7b10feb266a87f3a34c6d4c4d4e82a3962e21e7b1d8eaf662db9ef3fda`
- Theory-referee report: `a270e56cccaeb115d4a047583d7d71b20b985a713820c639dc1c1ee06c880440`
- Theory-referee session: `e898395d99a8e90efa6074be582c74ac8431000ee226c396a31dd66317da44af`
- Metric protocol: `5c10548c98010043a47fc2873ab68b8d253228e9f2c787bea6982e2dae13f589`
- Metric client-tool session: `4900cafc99b14ffafac97b712c17c655c0fb0e2b598798faaabe4bf0d51d8e4c`
- Algorithm client-tool session: `c1104b21660945f6017f26642965dd3c92a2e0f9bd378db82f894c37c776598a`

## Runtime result

The canonical AgentRuntime executed seven outer traces: three Architect traces,
one retrieval trace, one TheoryDeveloper trace, one AlgorithmEngineer trace, and
one independent generated-code review trace. It recorded six handoffs, eight
observations, five outer tool calls, one executed generated-code artifact, and no
executed generated simulation.

One persistent Theory owner used 17 model turns and 17 model-selected tools. It
wrote two authoritative Markdown documents, made three exact local edits, read
the current documents, ran three Python scratch calculations, wrote the compact
handoff, and committed one checkpoint. An isolated referee used 11 model turns
and 12 tools, read the hash-bound documents, ran three scratch calculations, and
returned `ACCEPT`.

The Algorithm owner used seven model turns. It submitted four complete source
versions and committed one exact source. The independent reviewer first authored
two invalid optional probes. Their raw failures stayed in the same reviewer
session, the reviewer corrected its own probe, and the third probe succeeded
before `ACCEPT`. This directly exercises the desired Codex-shaped loop:

`model edit -> environment result -> same model revision -> independent acceptance`.

The accepted source has exact source hash
`9a202316a22863bfa742429fe140fd34ba89e44d5eba59cd506b8cf609eb7f14`.
Its accepted handoff is `accepted_algorithm_handoff:e489dec62fb74bd8fe63`
with hash
`f4a67db0786560567ed9a6bc7f18e33e1e602cbf9aa9c568302bd3cb99da148d`.

The metric source owner then used 11 model turns and 11 selected tools. It wrote
a 15,076-character protocol with eight rows, committed it, received exact
validation errors, and remained in the same session. Every lower and upper bound
was a quoted numeric string instead of a JSON number. Its first local correction
matched eight repeated literals and was rejected because the old exact editor
required a unique occurrence. Subsequent attempts to regenerate large sections
were truncated by the provider. The final unchanged commit failed closed with
`architect_metric_requirement_candidate_authority_invalid`.

SimulationEngineer and the terminal Critic therefore did not run. Research
evaluation was `0/1` complete and `1/1` mode-conformant. Formalization was
correctly not applicable, and the Formalizer did not run.

## Hidden evaluation

The evaluator-only gate ran once after AgentRuntime terminated. It generated no
runtime feedback.

- Mechanical Theory checks passed `7/7`.
- The exact-Haiku semantic judge passed its first and only `10/10` calibration,
  then marked only one of eight candidate claims satisfied and seven violated.
- The accepted Python source passed all `11/11` closed ABI checks.
- The evaluator-only empirical harness passed all `9/9` checks across 12,000
  estimator invocations.
- Runtime never accepted a metric protocol or executed confirmatory simulation,
  so the hidden empirical pass is component evidence, not runtime empirical
  completion.

The full task remained `0/1`. Its required Theory, empirical-runtime,
unresolved-gap, and overall-research-loop dimensions failed.

## Mathematical audit

The final formulas do not rescue the active derivation.

1. Theory line 9 defines `D_i = U_(i) - U_(i-1)` starting at `i=0`, which uses
   undefined `U_(-1)`, and runs through `n+1`, implying the wrong number of
   components. Lines 13-15 then claim `n+1` spacings while summing through
   `n+1`.
2. Lines 33-36 define `D_0=U_(1)`, then apply
   `D_i=U_(i)-U_(i-1)` starting at `i=1`, duplicating the first gap, and finally
   redefine `D_n=1-U_(n)`. The inverse map on line 41 corresponds to a different,
   correct indexing, so the displayed forward and inverse maps disagree.
3. Line 43 calls the support an `(n+1)`-dimensional simplex, while line 46 calls
   it an `n`-dimensional surface. The task required a precise reference measure.
   The free-coordinate Lebesgue density is `n!`; induced Hausdorff measure on the
   embedded simplex carries a coordinate-volume factor. The document conflates
   these measures.
4. Lines 85-194 repeatedly assert the false `(n+1)!` Dirichlet density and offer
   several false measure-based resolutions. Lines 202-213 finally recover `n!`,
   but the earlier equations remain active and are never removed or delimited as
   rejected scratch work.
5. The marginal Beta law, mean, variance, covariance, dependence explanation,
   and `n=1` final formulas are correct. They do not establish a valid derivation
   from the contradictory definitions and change-of-variables argument.

The referee report demonstrates the same failure mode. It quotes the invalid
spacing definition and calls it correct, supplies a telescoping sum for a
different definition, calls the contradictory simplex dimension correct, and
describes the active factorial errors as a sound self-correction. Its scratch
work checked familiar final formulas rather than the disputed intermediate
definitions and measure transformation.

This is the second disjoint known-result task, after orthogonal Lasso, where an
isolated referee accepted familiar final mathematics while false intermediate
derivations remained authoritative.

## Shared harness correction

The official OpenAI Codex checkout was rechecked at
`57e2edc6e97474448f1fb634224471448bc09d40`. The applicable principle remains a
scoped source-owner loop with external files, raw tool observations, stable tools,
and compact hash-bound handoffs. Codex core, App Server, Responses transport,
thread storage, Guardian, and its scheduler remain excluded because they would
create a second conversation and orchestration owner.

Commit `24de6291` applies two future-task-only corrections:

1. Theory author and independent-referee prompts now define Markdown authority
   explicitly: every unmarked paragraph and equation remains active. Narrative
   chronology or a later correction cannot revoke false text; it must be removed,
   rewritten, or clearly delimited as `REJECTED` or `SCRATCH` with no active
   dependency.
2. The existing model-owned exact editor accepts an optional positive
   `expected_occurrences`. Runtime verifies the exact count before replacing all
   nonoverlapping matches atomically. The metric prompt uses an actual numeric
   example and states that numeric-looking strings are invalid.

This adds no spacing formula, Dirichlet rule, mathematical parser, output patch,
RepairAgent, extra reviewer, Architect route, retry scheduler, provider, model
escalation, or task-specific branch. Runtime still does not decide whether a
derivation or metric is scientifically correct.

The count-checked editor fixes the observed source-edit ergonomics; it does not
make the current metric JSON ABI ideal. A trivial known-result task still
produced a 22,359-character authoring prompt and a 15,076-character eight-row
document despite an explicit request for the smallest nonredundant portfolio.
Future architecture work should reduce this to a compact model-owned evaluator
or metric envelope inside the Simulation workspace, with independent pre-outcome
review, rather than adding more condition fields or repair layers.

The focused Theory, metric, client-loop, and Lean edit panel passed `168/168`.
The complete repository passed `960/960` in 78.45 seconds. Compile-all, JSON,
diff, and changed-file secret hygiene passed. Ruff was unavailable in the pinned
environment and is not claimed.

## Capability accounting

This is the sixtieth consumed scored task. It is `0/1`; four of 60 tasks retain
trustworthy full-task capability credit. The run demonstrates a real persistent
Markdown/LaTeX Theory workspace, direct Python execution, same-owner coding and
probe correction, isolated review, immutable hidden evaluation, and correct
non-formal task routing. It does not demonstrate a valid reviewed derivation, an
accepted runtime metric, confirmatory runtime simulation, terminal Critic
acceptance, or formal proof.
