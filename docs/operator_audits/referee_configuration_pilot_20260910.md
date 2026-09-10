# Referee Configuration Pilot: Initial Closeout

Date: 2026-09-10. Component evidence only; the research-laboratory goal is unmet.

## Scope And Execution

The [frozen protocol](../../benchmarks/reviewer_thinking_controls_20260909/protocol.json)
was executed once for each of its 12 case-arm pairs, in its preregistered order.
Its `prepared_unrun` field describes the preparation snapshot, not current status.
Production code remained exactly `6d8513ad0eb35caa63ec1e144632803338971762`.
The existing theory execution-preflight referee, retained tool loop, prompts and
tools were used unchanged. Each invocation received only its candidate as
`theory.md`, with isolated history/workspace and no external source access.

Both arms used direct Anthropic `claude-haiku-4-5-20251001`, max_tokens 8000 and
the existing loop limits. A used thinking 0, temperature 0, forced tools. B used
thinking 2048, automatic tools and omitted temperature. This is a comparison of
configuration bundles, not an isolated causal test of reasoning tokens.

All 12 invocations submitted. There were 94 requests and 94 successful exact-Haiku
responses, no HTTP failures/retries, and 809.393 seconds total elapsed time.
Every B session retained one signed thinking block; every A session retained zero.
That verifies native transport, not interleaved reasoning or mathematical truth.
No extra grading model, candidate retry, source correction or research draw ran.

## Paired Results

| Case | Frozen verdict | A verdict | A calls / seconds | B verdict | B calls / seconds |
|---|---|---|---:|---|---:|
| C17, matrix correct | ACCEPT | ACCEPT | 6 / 38.726 | ACCEPT | 6 / 49.820 |
| C42, matrix incorrect | REVISE | REVISE | 11 / 84.162 | REVISE | 8 / 79.659 |
| C06, moving integral incorrect | REVISE | REVISE | 7 / 58.866 | REVISE | 8 / 63.266 |
| C53, moving integral correct | ACCEPT | ACCEPT | 5 / 42.236 | ACCEPT | 6 / 35.374 |
| C28, nonuniform correct | ACCEPT | ACCEPT | 13 / 130.144 | ACCEPT | 10 / 100.855 |
| C65, Dini incorrect | REVISE | REVISE | 7 / 54.081 | REVISE | 7 / 72.082 |

Each arm matched 6/6 candidate verdicts, with zero false accepts, false rejects
or incomplete invocations on this panel. Reading the exact reports against the
frozen rubric found a valid diagnosis in each negative invocation. In particular,
the C65 supremum argument independently refutes uniform convergence despite the
additional incorrect monotonicity explanations below. These are initial findings,
not regraded research outcomes or six fully reliable referee derivations.

| Aggregate | A | B |
|---|---:|---:|
| Completed model calls | 49 | 45 |
| Sum of invocation elapsed seconds | 408.215 | 401.056 |
| Provider input tokens | 986 | 265 |
| Provider output tokens | 38,572 | 40,025 |
| Cache creation input tokens | 113,168 | 107,751 |
| Cache read input tokens | 533,080 | 421,263 |
| Scratch EXECUTED / REJECTED_CONTRACT / FAILED | 14 / 6 / 3 | 14 / 6 / 2 |
| Tool-level errors | 6 | 5 |

Token fields are original provider categories, not summed as a single billable
rate. Output includes native thinking where present. Timing is descriptive and
includes tool/provider variability, not a controlled latency improvement estimate.

## Correct Verdicts, Incorrect Review Equations

- **B/C17:** The [report, line 40](../../runs/referee_configuration_pilot_20260910/invocation_10/theory_reviews/preflight-f1349e2c2a2f56d14c13/review-edea601dd2ea6fbf7e73.md)
  writes `A^-1 B = [[0,1/3],[1/2,0]]`, which is actually `B A^-1`.
  Multiplying that displayed matrix by `A^-1` gives off-diagonals 1/9 and 1/4,
  not the next line's 1/6 and 1/6. The final derivative and candidate are correct,
  but the referee's claimed verification chain is not.
- **B/C53:** The [report, line 18](../../runs/referee_configuration_pilot_20260910/invocation_12/theory_reviews/preflight-1deb3501b2756f819f36/review-37b2449609523b10c7a7.md)
  replaces the Leibniz boundary value `f(t,t)` by `partial_x f(t,x)|x=t`.
  Here the latter is zero while the boundary value is `1/(2t)`. Later prose
  uses the correct value and derivative zero, but the displayed rule is false.
- **B/C65:** The [report, lines 25-31](../../runs/referee_configuration_pilot_20260910/invocation_06/theory_reviews/preflight-a687fbb66441cc41a6d5/review-6d1490164207b16fc769.md)
  calls `1/4, 1/4, 3/16, ...` at `x=1/2` an increase-then-decrease witness.
  It is nonincreasing, so that is not a counterexample to monotonicity.
  The separate supremum limit `exp(-1)` is correct and suffices for rejection.
- **A/C65:** The [report, line 26](../../runs/referee_configuration_pilot_20260910/invocation_09/theory_reviews/preflight-226ba66f1038b43613f7/review-597dbc5c3f72ad6f54fd.md)
  also overgeneralizes an increase-then-decrease pattern to a fixed interior
  point without restricting it; the assertion fails for `x >= 1/2`.
  Its independent supremum derivation still supports the negative diagnosis.

These examples establish a distinction between verdict correctness and review
fidelity. They are not a qualified report-quality score or a claim that all other
reports are error-free. File hashes establish identity, not the correctness of
equations or accuracy of narrative line citations. No original report was edited.

## Interface Friction And Decision

All 12 first scratch attempts supplied top-level scripts instead of the documented
`run_sandbox` entry point. The description was present in the actual Anthropic tool
serialization; this is not a missing-description transport bug. There were 45
scratch requests: 28 EXECUTED, 12 REJECTED_CONTRACT and 5 FAILED. Execution failures
included missing names/keys, non-string JSON keys and an underspecified symbolic
limit. B/C65 had no successful scratch, although its analytical supremum argument
was valid. Scratch use or success was not a mandatory completion condition.

Ten submission attempts were rejected over evidence references/envelope shape;
one report read exceeded EOF. These are tool/interface costs separate from
mathematical diagnosis. Scratch status is also distinct from tool-level `is_error`.
All observations returned to the same source owner; no repair agent or Architect
rerouting was introduced. The model authored every source/report revision.

The primary comparison is a ceiling result and is inconclusive. Cost differences
are small and inconsistent across cases. Keep thinking off by default. Do not
infer population accuracy, significance, better scientific judgment, or research
E2E readiness. No product code, prompt, model default or runtime limit changed.
No stronger model, extra reviewer, mandatory scratch ritual or mathematical rule
is justified by these data. A future interface/context change needs a demonstrated
shared cause; it must not be tuned by repeating these consumed controls.

Return to the complete source-aware research objective, with independently frozen
authority for a fresh known-result task. No next task is activated by this audit,
and no more elementary controls are authorized merely to obtain a favorable score.

## Immutable Local Evidence

The [initial analysis](../../runs/referee_configuration_pilot_20260910/initial_analysis.json)
binds all source/report/session hashes and original HTTP/progress/review packets.
The [activation](../../runs/referee_configuration_pilot_20260910/activation.json)
predates the first model request. The [terminal](../../runs/referee_configuration_pilot_20260910/terminal.json)
is the historical execution closeout; its audit-pending field is not rewritten.
Raw sessions and operator artifacts remain local in gitignored `runs/`, not a
portable public evidence bundle. This committed audit records their identities:

| Artifact | SHA-256 |
|---|---|
| Protocol | `bc865a65c4c785593582969b484f601396d6f9a60beaafed418d2b7813eff464` |
| Activation | `26da765ae51114def8571d376d9ee23a950b9f13225c994a6b59d02b9ed70226` |
| Terminal | `93f3990fc44175a02f36bdf0b1a3bfe4fde4362392bbe30bd506418f50dd1e47` |
| Initial analysis | `c4dfa201c7a027c5c30342eb1f50dbdcd11cdf838cd7cdbebc837598f0b24ec8` |

The 114 numbered and four standalone research draws retain their original
outcomes. This separate component pilot adds zero research-task or proof credit.

Closeout verification: `tests/test_core.py` and
`tests/test_reviewer_thinking_controls.py` passed 18 tests in 0.57 seconds;
`git diff --check` passed. The full suite was not rerun for these documentation-only
changes. Its 1309-test result belongs to the frozen source commit, not this audit.
