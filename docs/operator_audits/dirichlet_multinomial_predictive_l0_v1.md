# Task110 Operator Audit: Dirichlet-Multinomial Prediction

Date: 2026-08-30

## Immutable Evaluation Boundary

Task110 is the sole consumed exact-Haiku draw for
`dirichlet_multinomial_posterior_predictive_known_result`. The visible question was
frozen at commit `c098167a`; hidden authority was qualified and the public
preactivation ledger was pushed at `89265b6d` before the first product-model call.

The product run, one post-runtime hidden assessment, all workspaces, and all outputs
are immutable. They must never be rerun, resumed, repaired, reevaluated, rescored,
resampled, manually patched, exposed to a source owner, or model-escalated. This audit
does not feed observations back into the consumed runtime.

## Result

- Runtime status: `ACCEPTED` after 14 steps, comprising 13 outer iterations and one
  same-owner source continuation.
- Full hidden task: failed, 0/1.
- Trusted capability credit: 0/1; aggregate remains 7/110.
- Formalization: not applicable; Formalizer correctly did not run.
- Model: `claude-haiku-4-5-20251001` only. No Sonnet or Opus call ran.
- Product calls: 78 total, comprising one Architect structured-output call and 77
  retained client-tool turns. The retained loops executed 83 tools and returned four
  raw tool errors to their current owners.
- Hidden assessment: one invocation and two exact-Haiku semantic calls; no runtime
  feedback was generated.

## What Worked

The canonical harness exercised the intended research graph without a repair agent or
second scheduler:

- TheoryDeveloper authored a 401-line Markdown/LaTeX document, used scratch
  calculations, and explicitly committed a hash-bound checkpoint.
- The independent theory referee inspected the exact document in a clean context,
  wrote a 351-line Markdown report, and accepted the theory.
- AlgorithmEngineer authored and executed exact Python source. The first independent
  source review returned three concrete findings to the same source-owning workspace.
- That exact Algorithm session resumed, made two model-authored edits, reran the
  current bytes, and explicitly committed the revised source.
- A second isolated source review read the current hash-bound source and ran an
  executable nine-invocation probe before accepting it.
- SimulationEngineer authored exploratory and confirmatory source, consumed the
  accepted estimator by hash, and completed the frozen product-side experiment.
- Independent Simulation-source reviews and the final Critic ran through their native
  retained tool loops.
- Runtime correctly treated formalization as not applicable and reported a complete
  non-formal research loop.

These are real harness and component observations. They do not establish full-task
correctness.

## Theory Findings

The hidden authority passed all seven mechanical checks. Its calibrated semantic judge
marked all eight claims satisfied in two exact-Haiku calls. Operator inspection found
no material contradiction requiring rejection of that result.

The document gives a coherent conjugate derivation of the posterior concentration,
Dirichlet-multinomial predictive mass, mean, full covariance, overdispersion factor,
fixed-total conservation, permutation equivariance, single-trial reduction, and
concentration limit. It also distinguishes posterior uncertainty from conditional
multinomial sampling variation and states finite-task scope limitations.

This task therefore supplies positive evidence for the persistent Markdown/LaTeX
Theory workspace and isolated review, not for arbitrary frontier-theory discovery.

## Scientific-Code Findings

The estimator's posterior-predictive mathematics is correct. Hidden valid-domain,
response, determinism, nonmutation, transformation, and exact-reference behavior
passed, and all 13 hidden empirical checks passed over three frozen designs.

The exact source nevertheless violates the visible closed request ABI:

1. It reads declared fields with `request.get(...)` but never requires the request key
   set to equal the three declared fields, so an extra request field is accepted.
2. It accepts a `prior_concentration` element below the public lower bound 0.05 as long
   as it is positive.
3. It does not enforce the public per-element upper bound 10000.
4. It requires at least two categories but does not enforce the public maximum length
   of ten.

The hidden Algorithm authority consequently passed only 8/10 aggregate checks despite
60 exact estimator invocations. No task-specific output was patched.

## Reviewer Findings

The first reviewer correctly identified floating-count coercion, floating future-size
coercion, and conversion-before-validation. The same source owner fixed those observed
defects.

The second reviewer then overfit its audit to those prior findings. Its probe exercised
eight malformed requests and one valid request, but omitted several other visible
contract boundaries. More seriously, its report claimed that the `.get()` pattern
rejects extra fields; that inference is the opposite of the source behavior. It also
claimed all public ranges were enforced while omitting the visible 0.05 lower bound,
10000 per-element upper bound, and length-ten ceiling.

The model-owned probe, real execution, current-source read, and immutable review report
all worked. The substantive falsification judgment did not.

## Critic And Evidence Findings

CriticEvaluator requested `ACCEPT`, and the runtime completion contract accepted the
research loop because all product-visible evidence requirements were satisfied. That
is a correct statement about orchestration completion, not hidden correctness.

The post-runtime evaluator remained independent and failed the scientific-code
dimension. Theory, empirical, unresolved-gap, and overall runtime-loop dimensions
passed; source replication, formalization, and novelty were not applicable. The
full-task gate therefore returned 0/1 and generated no runtime feedback.

## Shared Future-Task Change

Commit `9597b52d44a80e36ed541d0dc49035c83c3cbbb2` changes only the existing future-task
reviewer loop. After a reviewer-authored exact-source probe, its raw result and the
unchanged frozen executable contract return together as the newest observation in the
same model context. The model still chooses cases, assertions, further probes,
findings, and verdict.

Runtime does not parse Python, decompose clause semantics, generate a malformed case,
declare coverage, edit source, add a reviewer, start a repair worker, retry a task,
import Codex Core, or create another scheduler. This selectively reuses OpenAI Codex's
retained-session and raw-observation placement principle. It does not repair or rescore
Task110.

## Artifact Identity

- Visible question SHA-256:
  `069ce43dc130d07e7ea9f10d784cd5e6c5b270f597264b58028972d26154ae0b`
- Public preactivation ledger SHA-256:
  `38e6ac7a4353a4692b68a1a1cd3ff8a527603410adb3860993f5ade7ae5e7bad`
- Hidden gold manifest file SHA-256:
  `a7cd928f7461e086bb45e16321cd299b225108e536eacd292703e0214462bbdf`
- Hidden gold stable hash:
  `13d93c46376ee281f0b2c9358ad362e642d70e1444a5ee0a4e80651df728ff01`
- Runtime result SHA-256:
  `4b14fd5141779d23598f61fc87ad8eecf9158b793591a263b7c4a3c709c3bdbe`
- Runtime manifest SHA-256:
  `a341953236140e930e6273d41b6208bbcd757a403089ed5072d1268f8fc6216f`
- Completion summary SHA-256:
  `03177f835cfc0cd4c03429148395f32f902c9c0879006d03e9e8e9b2102de5b4`
- Failure summary SHA-256:
  `24cb04a35027713ddc327549df51ae6eeb6939955b1649c1b2c05b34e73c0ac6`
- LLM topology SHA-256:
  `7c7d0c9a1931f3da13f611c6c26cb2015c5e77d8dc986f838491a2b4de996f87`
- Gold assessment SHA-256:
  `9cc8fb9cb6279b03cd4ae53bfa1939a56effe9de88fd1363d348e229d19a27f4`
- Theory document SHA-256:
  `290cefabfab15feb0fd6e2fa2cdc70907f7c0d4292fd1bac6f988433df4b2d80`
- Referee report SHA-256:
  `ad637032f6b7f7f7ca8082e2d19b4f309ec169e4cde950b8d00d3eea73c5669b`
- Evaluated estimator source hash:
  `9b56fe74d7e1e389bb4d21e8aca81282e8977a9db876145593fe45a5a4e26601`

## Final Disposition

Task110 remains permanently consumed at 0/1. The durable theory workspace, direct
source-owner revision, executable reviewer probes, exploratory and confirmatory
Simulation, optional-formalization policy, and independent hidden gate are retained.
Public ABI compliance and the second source review are not accepted as capability
success.
