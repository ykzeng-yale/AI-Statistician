# Preregistered Referee Configuration Diagnostic

Prepared 2026-09-09. No provider call has occurred. This is a six-document
component pilot, not a research-E2E draw, authority qualification, or a claim of
scientific improvement. It introduces no product module, scheduler or prompt rule.

## Comparison

Use the production `review_architect_theory_execution_preflight` entry point at
code commit `6d8513ad0eb35caa63ec1e144632803338971762`, with the current unchanged
production prompts and tools. Call Anthropic directly with exactly
`claude-haiku-4-5-20251001`, tier `haiku`, `max_tokens=8000`, and the existing
24-turn / 48-call / 2-no-progress-turn limits. Do not raise limits, continue an
incomplete session, retry a candidate, or escalate the model.

- A: thinking budget 0, temperature 0, existing forced-tool behavior.
- B: thinking budget 2048, automatic tools, provider-native temperature behavior.

Set `AI_STATISTICIAN_HAIKU_TOOL_THINKING_BUDGET_TOKENS` explicitly before request
construction. The environment value is resolved into the request and its session
identity. B changes tool choice and temperature compatibility as well as thinking;
this estimates the operational configuration bundle, not the isolated causal
effect of reasoning tokens. Both arms have the same total output ceiling. Hidden
thinking is not a scored artifact or a substitute for a reviewable report.

## Inputs And Isolation

The opaque case IDs, order and expected judgments are in `protocol.json`. Its
labels and this document are evaluator-only. Give each invocation only its
candidate, copied to a new workspace as `theory.md`, under this common question:

> Assess the candidate derivation in theory.md for mathematical correctness under
> its stated assumptions. Review the intermediate reasoning as well as the final
> conclusion. Report unresolved errors without silently changing the candidate.

Freeze intent as theory and unresolved_gaps required; all other evidence
dimensions not_applicable. Create the source manifest with the existing
`theory_workspace_document_manifest`; bind the resulting source packet hash.
There is no algorithm handoff and no obligation to formalize these documents.
Enable the existing Python/R `TheoryScratchpadConfig` with seed 20260909,
replicates 100 and timeout 20 seconds. This is a scratch default, not a mandatory
simulation size or a required tool call. Do not provide prior findings, author
scratch, a source library, a retrieval provider, or web access. The six documents
are self-contained; scratch and the full production document/report tools remain.

Use fresh isolated directories and empty model history for every case-arm pair.
Do not expose sibling candidates, expected verdicts, other reports, protocol data
or results from consumed research tasks. Follow the frozen order once; each pair
gets one invocation only. Log an attempt before its first model request. A provider
failure, truncation, non-submission or exhausted budget stays an incomplete result;
it is not a mathematical rejection. An interrupted invocation is not resumed.

## Frozen Analysis

The three correct documents have complete elementary derivations. The three
incorrect documents each have a decisive mathematical error specified in the
evaluator labels. The offline exact checks in `tests/test_reviewer_thinking_controls.py`
validate those labels independently of the product model. They do not prove that
an LLM will recognize the errors or that this small panel is representative.

Record for every invocation: exact input/source/code hashes, resolved model
configuration, completed model turns and attempted requests (including failures),
tool calls, provider token usage, elapsed time, terminal status, source-bound
review report and unresolved findings. Keep original provider/loop metadata; do
not estimate missing usage. The retained loop already supplies sessions and usage.

Primary report: paired correct decisions, false accepts, false rejects and
incomplete results. A REVISE on an incorrect document counts as a correct diagnosis
only if its report identifies the labeled mathematical defect, not merely a
formatting complaint; audit the source-bound report using the frozen rubric.
Never count all-REVISE or incomplete output as reliable review. Also report report
quality and actual cost descriptively, with all individual cases, not just a sum.

With only three paired mathematical families, do not calculate or advertise
population accuracy, statistical significance, E2E readiness, or a best-of success.
Keep thinking off by default after this pilot. More correct judgments with no new
false acceptance can justify a larger fresh comparison, not automatic deployment.
A ceiling result in both arms or mixed results is inconclusive. Any later study
must use new controls and cannot tune prompts or repeat this panel.

Credentials must come from trusted current process configuration. Never load keys
from the conversation, historical files, logs or Git. This preparation leaves all
114 numbered and four standalone consumed evaluations untouched.
