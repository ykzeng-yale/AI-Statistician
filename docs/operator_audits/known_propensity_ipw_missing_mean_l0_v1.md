# Task109 Operator Audit: Known-Propensity IPW Missing Mean

Date: 2026-08-29

## Immutable Evaluation Boundary

Task109 is the sole consumed exact-Haiku draw for
`known_propensity_ipw_missing_mean_known_result`. The visible question was frozen at
commit `b39f3c28`; hidden authority was qualified and the public preactivation ledger
was pushed at `b8039ffa` before the first product-model call.

The product run, one post-runtime hidden assessment, all workspaces, and all outputs
are immutable. They must never be rerun, resumed, repaired, reevaluated, rescored,
resampled, manually patched, exposed to a source owner, or model-escalated. This audit
does not feed observations back into the consumed runtime.

## Result

- Runtime status: `BLOCKED` after 11 outer iterations.
- Final classification: `required_research_evidence_missing`.
- Full hidden task: failed, 0/1.
- Trusted capability credit: 0/1; aggregate remains 7/109.
- Formalization: not applicable; Formalizer correctly did not run.
- Model: `claude-haiku-4-5-20251001` only. No Sonnet or Opus call ran.
- Product calls: 78 total, comprising one Architect structured-output call and 77
  retained client-tool turns. The retained loops executed 80 tools and returned three
  raw tool errors to their current owners.
- Hidden assessment: one invocation and two exact-Haiku semantic calls; no runtime
  feedback was generated.

## What Worked

The canonical harness exercised the intended model-owned workspaces without a repair
agent or second scheduler:

- TheoryDeveloper authored a 299-line Markdown/LaTeX document, used scratch execution,
  and explicitly committed a hash-bound checkpoint.
- The independent mathematical referee received the immutable document in a clean
  context, read exact ranges, ran its own scratch source, wrote a Markdown report, and
  submitted its own judgment.
- AlgorithmEngineer wrote and revised exact Python source in one retained coding
  session and repeatedly ran the current bytes against the scientific sandbox.
- GeneratedCodeSemanticReviewer authored and executed its own diagnostic probe against
  the immutable estimator before accepting it.
- SimulationEngineer authored exploratory and confirmatory source, consumed the exact
  estimator, received raw execution output, and completed the frozen product-side
  simulation.
- CriticEvaluator inspected externalized exact evidence through the retained tool loop.
- The outer evidence contract rejected the final research result despite the Critic's
  requested `ACCEPT` disposition.

These are real harness and component observations. They do not establish scientific
correctness or full-task success.

## Theory Findings

The authoritative document contains material active falsehoods and contradictions.

1. Lines 36-47 claim
   `E[R_i Y_i / pi(X_i) | X_i] = Y_i` and pull `Y_i` outside the conditional
   expectation because it is supposedly fixed given `X_i`. Under the stated model,
   `Y_i` is generally not measurable given `X_i`. Conditioning on `(X_i, Y_i)` gives
   `Y_i`; conditioning only on `X_i` gives `E[Y_i | X_i]`.
2. Lines 96-100 describe an exact finite-sample asymptotic-linear identity using a
   generic `o_p(n^-1/2)` remainder instead of stating that the remainder is identically
   zero. A zero remainder is technically an `o_p` term, but the requested exact identity
   and its decisive simplification were not presented faithfully.
3. Lines 143-148 write an active variance expression with one power of the propensity
   in `E[R_i Y_i^2 / pi(X_i)]`. Squaring the weighted contribution requires
   `E[R_i Y_i^2 / pi(X_i)^2]`, which reduces under MAR to
   `E[Y_i^2 / pi(X_i)]`.
4. Lines 219-225 repeat the same denominator-power error in the positivity argument.
5. Lines 251-257 state that estimating a propensity necessarily makes variance larger.
   That general claim is false; estimated weights can reduce variance under suitable
   correctly specified or calibrated procedures.
6. Later summaries contain the correct variance formula, so the document leaves
   mutually inconsistent active assertions rather than a clean current derivation.

The hidden mechanical theory authority passed 7/7 checks, and its exact-Haiku semantic
judge marked all 8/8 target claims satisfied. Operator inspection invalidates that
semantic judgment as a false positive. Because the automated full task already failed,
the task is recorded as `FAILED`, not as an automated-pass operator-invalid case.

## Referee Findings

The 274-line independent report false-accepted the document with no blocker.

- It repeated the false conditional-measurability argument and explicitly called it
  correct.
- It silently reconstructed the correct squared-denominator variance while accepting
  the candidate's different written formula.
- Its scratch program tested unconditional mean and variance behavior. Those numerical
  endpoints cannot validate the disputed conditional random-variable identity.
- It summarized nearly every section as correct instead of treating exact candidate
  expressions as falsification targets.

The isolation, file tools, scratch execution, and report persistence worked. The
scientific judgment did not.

## Scientific-Code Findings

The estimator's core numerical method is correct: it computes the unnormalized
fixed-`n` inverse-probability weighted mean, contribution sample variance, standard
error, interval, and observed count. Hidden valid-domain behavior and invariance checks
passed, and hidden empirical authority passed all 12/12 checks over 6,000 estimator
calls.

The exact source nevertheless violates the visible closed request ABI. It converts
inputs with NumPy `dtype` coercions and `float(...)`, does not require the exact request
key set, and therefore accepts Boolean, floating, string, or extra-field forms that the
public contract says to reject. Hidden algorithm authority failed two of nine aggregate
checks, including strict malformed-request behavior.

The independent source reviewer authored a 12-case probe, but all cases were valid or
inside the valid domain. It never exercised the public anti-coercion and closed-object
requirements, then accepted with zero finding. This is a generic contract-derived
falsification failure, not an IPW-specific coding defect in the harness.

## Critic And Evidence Findings

The final canonical view contained the runtime-derived required gap
`empirical.executable_evaluator_authority_output_invalid`. The Critic still marked all
required dimensions supported, disclosed no blocking dimension, and requested
`ACCEPT`. The outer evidence gate correctly produced
`REQUIRED_RESEARCH_EVIDENCE_MISSING` and blocked the task.

This confirms that final authority remained outside the LLM judgment. It also exposed a
shared tool-loop defect: the Critic terminal validator did not return that mechanical
mismatch to the same model before accepting its packet.

## Shared Future-Task Change

Commit `94f18d2f949312f67b3d1c77cbbb6bbf237172d3` changes only shared future-task
mechanisms:

- the existing mathematical referee prompt asks the model to preserve the candidate's
  exact exponent, denominator, sign, conditioned sigma-field, and random object, and to
  audit measurability before moving factors through expectations;
- the existing source-review prompt asks the model-authored probe to exercise every
  public request field's stated rejection behavior and the closed-object rule before
  accepting;
- the existing Critic terminal validator rejects `ACCEPT` when runtime-derived required
  evidence gaps are nonempty and returns that raw observation to the same retained
  Critic session;
- the OpenAI Codex harness audit is pinned to `63d21388` and records explicit
  continuation provenance without importing Codex Core or another scheduler.

No task formula, IPW rule, mathematical parser, content patcher, repair worker, retry,
fallback, new agent, new scheduler, mandatory Formalizer, Sonnet, or Opus was added.
The shared change does not repair or rescore Task109.

## Artifact Identity

- Visible question SHA-256:
  `ec0c1504ca53e9dc408e966b763281784285405d4cd2af216c9896a88dda8dbf`
- Public preactivation ledger SHA-256:
  `b47c3be754c07206cbd6169d85cc920b1563f0f3fe38c4b3b789d1d89fc12dc3`
- Hidden gold manifest file SHA-256:
  `c26a92dafb1cc186d9296bd9b2d8f3f96c3476a04962ad8c0bb40cb69304bb51`
- Hidden gold stable hash:
  `4754ac5c1ea4e0d85731580d8a1856432095cd5fa841fac2e9e2aa2450c60776`
- Runtime result SHA-256:
  `d8875a34b076eda4329d188d5835fe035824cb6f7db75a2f2e36d8abae404e64`
- Runtime manifest SHA-256:
  `906213a445406324da45da4dfeeeabc08d34492c766dfa1bc44e04671a42ee1e`
- Completion summary SHA-256:
  `7dc4638ee52cc83441e4c23976d97df64ca387d985850d2596663dd2734974f1`
- Failure summary SHA-256:
  `1001d94570be4c465263633e61c4bed50bd92b14387c13c3075413de52f7bc94`
- LLM topology SHA-256:
  `52723e286e0d6024c193dc4fd8235fdc0bc1289594ae3adacb336e43b88ab729`
- Gold assessment SHA-256:
  `a0512746c7c969e1255ef2474ff6dd5990cc82e0324cb30420814d7f63a1f5aa`
- Theory document SHA-256:
  `f7793c93755eded2d763ca5e92dcc8a2dcb12a8c41a86860cc8540e965373a51`
- Referee report SHA-256:
  `95e0490e0a4bdffd21fb2aca40600299c80587a1af7d6153e98c9bc0c37dc09c`
- Evaluated estimator source hash:
  `06015ca1d75c1288c9533f95400da3e9ccf14c4f00f179462ee6bab485855a4d`

## Final Disposition

Task109 remains permanently consumed at 0/1. The durable workspace, direct coding and
simulation loops, isolated review contexts, optional-formalization policy, hidden
component authorities, and fail-closed final gate are retained. The author/referee
mathematics, public ABI compliance, source-review falsification, hidden semantic judge,
and Critic consistency are not accepted as capability success.
