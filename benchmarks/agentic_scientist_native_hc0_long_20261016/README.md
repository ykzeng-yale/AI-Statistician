# Native Long-Workflow Development Condition

Prospective follow-up to the terminal
[native HC0 condition](../agentic_scientist_native_hc0_20261016/analysis.md).
Neither previous arm is resumed, repaired or rescored. The question, unsolved
starter, fixed acceptance requirements and complete 12-cell, 5000-dataset-per-cell
evaluator are unchanged. Reuse that condition's `prepare.py` for two fresh task
trees. This is exposed known-method reconstruction, not a new H/S publication
comparison, blind rediscovery, autonomous study design or a real-data application.

## Fixed Model And Resources

Use the same exact Qwen3.8-27B BF16 weights and locked vLLM/worker archives.
The [pinned model card](https://huggingface.co/Qwen/Qwen3.8-27B/blob/1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0/README.md)
documents native 262144 context and optional 1M YaRN. This condition explicitly
uses the documented factor-4 override without editing the original model files.
It is a derived 1M-context deployment, not a native-context or quality claim;
static YaRN may affect short-context performance. All roles and both arms use
the same deployment and sampling settings. There is no automatic model fallback.

The combined output cap is 393216 tokens. This gives room for the card's suggested
262144 reasoning plus 131072 final tokens, but does **not** enforce separate caps
or promise that output allocation. One request may take up to four hours. Each
arm gets its own 48-hour standard-tier, one-B200 allocation, with 12 hours for
ideation, 24 hours for authoring, 12 hours for host evaluation/source review and
12 hours per report attempt. The cumulative 48-hour wall limit still applies.
The second arm depends on termination of the first, not its scientific success;
it does not inherit the first arm's remaining wall time or files.

The corrected client retains native opaque continuation state, and system-level
stage ownership resolves the prior prompt conflict. These changes and larger
resources form one joint development condition, not a component-effect study.
No fresh scientific outcome is claimed at preparation. Startup verifies the
served context before any research request; this is not long-context accuracy
qualification. Preserve every startup, tool, source, evaluation and review failure.

## Execution

`run_condition.sh` reuses the existing upstream investigation/posthoc controller.
It does not add a scheduler, repair agent, answer template or diagnostic stage.
Freeze product/upstream archives, the existing three integration patches, both
task trees, API config and deployment receipt before submission. Record exact
hashes and resource routing in `precall.json` and job IDs in `submission.json`.
The running service is loopback-only and terminates with its owning job.

Submitted jobs are **29726507** (stock) and **29726508** (statistical, afterany
stock); both were pending at submission. See [submission.json](submission.json).
The [first live prefix](runtime_observation.json) verifies the derived-context
service startup and fourteen returned tool/native-state turns in stock ideation.
It is not terminal research evidence; statistical still waits for stock.
No official H/S experiment or publication-checklist item is completed by this
condition. Source-bound AI review remains fallible feedback, not proof.
