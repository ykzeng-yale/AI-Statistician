# Native API Workflow Observation

Both arms stopped before scientific authoring. Stock completed 12 model turns
and 11 file-tool calls; statistical completed 14 turns and 13 calls. All executed
tools succeeded. Neither arm wrote its idea/rubric proposal or entered the source,
simulation, independent-review or reporting stages. The exact terminal records
and archive identities are in [observed_results.json](observed_results.json).

Each last request returned `finish_reason=length`, using all 32768 allowed output
tokens without a complete tool call. The provider returned normally in about
357 seconds, below the 1800-second request timeout. The total reported usage is
274078 input and 88372 output tokens. These are model-turn costs, not simulated
datasets or independent research draws. No theorem or method was assessed.

## Source-Level Findings

The model's [pinned official card](https://huggingface.co/Qwen/Qwen3.8-27B/blob/1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0/README.md)
documents retained native reasoning for multi-turn work. Installed vLLM 0.31.0
returns `reasoning` and normalizes the older `reasoning_content` alias. The frozen
client kept visible text and tool calls but dropped those fields before subsequent
requests. The earlier probe's stored native schema response contains a nonempty
`reasoning` field; its successful short tool-feedback check did not qualify this
state-retention capability. Missing thinking cannot be recovered from the saved
canonical transcript. No private reasoning is reproduced here.

The rendered upstream prompt also required model-written global memory in paths
that the native participant intentionally could not write. Its native ownership
clarification appeared only before that prompt in a user message. The existing
stage responsibilities must instead have unambiguous system-level authority.
This does not require mathematical rules, a new agent, content repair or wider
file access.

Both are established interface findings, not evidence that either alone caused
these stops. They must not be presented as a measured explanation or efficacy
result. The separate fixes preserve native state as opaque provider text and move
the existing ownership contract to the system message. Fresh evidence is needed.

## Resource Interpretation And Next Boundary

The output allowance was a real binding limit. The card reports a 32768-output
coding-benchmark condition, but separately recommends substantially more output
for long agentic reasoning. Its larger suggested reasoning/final budgets are
described under a 1M-context condition, whereas this deployment used native 262144
context. Do not copy the larger numbers without qualifying combined context,
memory and stage/request timing. Conversely, this failure cannot establish the
model's unrestricted capacity. No automatic budget increase or substitution is
made to the consumed condition.

Before another complete-workflow condition, verify native state continuity,
coherent prompts and adequate model/context/output resources together. Preserve
the full question and actual theory/code/study/report obligations. Do not add
task-specific answer rules, turn this into a new sequence of toy capability gates,
or bypass ideation after observing these outcomes and call it the same comparison.
An explicit fixed-task entry path is an architectural option, not an implemented
or qualified replacement here. Future conditions must be declared prospectively.

The Slurm job ended `FAILED`, exit `1:0`, after 35m12s; both outer phases returned
2 and the owned server shut down normally. Neither arm was resumed or rerun.
This adds no official H/S result or publication completion credit.
