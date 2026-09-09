# Critic Transport Correction

Date: 2026-09-09. Starting code: `76e5d02e`.

## Evidence

An unrelated synthetic empty-workspace request using the current Critic terminal
schema reproduced HTTP 400 `invalid_request_error`: the compiled grammar was too
large. Disabling parallel tool use did not change that failure. Native tool use
with the identical input schema, without provider strict compilation, returned a
complete tool call with exact Haiku and no transport retry or capability fallback.

The consumed weighted-Rademacher draw recorded only `BadRequestError`, not the
provider message. These probes establish a defect in its shared static Critic
contract; they do not recover the original missing error text or reassess that
candidate. No consumed evaluation was loaded into a model, resumed or rescored.

| Synthetic Probe | Attempted Calls | Successful Responses | Seconds |
|---|---:|---:|---:|
| Strict, parallel permitted | 1 | 0 | 0.641 |
| Strict, parallel disabled | 1 | 0 | 0.831 |
| Native tool, identical schema | 1 | 1 | 12.462 |
| Actual Critic workspace after correction | 2 | 2 | 33.123 |

Every request used `claude-haiku-4-5-20251001` through the project's direct
Anthropic backend. The last probe returned REJECT with missing theory, code and
empirical evidence; it did not manufacture acceptance. Its retained reviewer loop
used two calls and two terminal submissions. This is mechanism evidence, not a
research result or a calibration of mathematical reviewer accuracy.

## Change

Only the Critic terminal tool stops requesting provider strict grammar compilation.
The complete original JSON Schema remains model-visible and is now checked locally
with `jsonschema.Draft202012Validator` before normalization. The existing semantic,
lineage and required-evidence checks follow unchanged. Invalid submissions return
their exact schema paths or evidence mismatch to the same retained reviewer.

No schema fields, scientific acceptance requirements, tools, model tiers or budgets
were dropped. No automatic fallback, provider restart, repair agent, second
scheduler or task-family rule was added. Other workspaces' strict-tool choices are
unchanged. The standard validator replaces the unavailable transport guarantee;
there is no hand-written schema interpreter.

This follows the documented separation between provider grammar limits and local
validation: [Anthropic structured-output limits](https://platform.claude.com/docs/en/build-with-claude/structured-outputs#schema-complexity-limits)
and [JSON Schema validation](https://python-jsonschema.readthedocs.io/en/stable/validate/).

## Verification

The focused Critic/backend/tool-loop panel passed 98 tests in 3.57 seconds.
Regressions cover missing nested fields, wrong nested types, extra authority fields,
missing dimensions, and an invalid ACCEPT corrected in the same session. Long
document and source-result inspection tests continue to use the same tools.
Compilation succeeded. The full suite passed 1,290 tests in 390.37 seconds.

All 114 numbered tasks and both standalone draws remain consumed and unchanged.
The next research-first candidate is the new fixed-alphabet multinomial entropy
task, not a formal-only substitute. Its product draw must wait for a separately
qualified, frozen authority. The native research-E2E goal remains active and unmet.
