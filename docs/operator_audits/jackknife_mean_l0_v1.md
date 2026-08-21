# Jackknife Mean L0 v1 Operator Audit

## Disposition

The single frozen exact-Haiku run is **failed, evaluation-design-invalid, and
closed**. AgentRuntime stopped in TheoryDeveloper before independent review,
algorithm authoring, simulation, Critic, or hidden execution. The raw research
and hidden-gold outcomes remain `0/1`; the task must not be rerun, repaired, or
retrospectively rescored.

Run directory:
`runs/main_worker_research_l0_jackknife_mean_20260821_v1_codex_referee_continuation_exact_haiku`

Immutable evidence hashes:

- Runtime manifest SHA-256: `839f8a92ee48be49625249a7c0597fb577799efbd80a476d838db4f150c6df38`
- Hidden-gold report SHA-256: `a280164cc075eccb9bf956959878683bfaca08b8bb08501db9cdda26dfe992c1`
- Runtime failure summary SHA-256: `24cbc2455293961620b127bcb13ded2efa3dd17e23c27ae8a6ba714565db9239`
- Theory document SHA-256: `700f903b101208641c309c5ad5f3c9226420219baae4c828ffc9abf957f1bc5f`

Every enabled role used `claude-haiku-4-5-20251001`; no Sonnet or Opus
escalation occurred. Formalization was `not_applicable` and was not a blocker.

## Live Trajectory

The run completed three outer traces: Architect, task-bound source retrieval,
and TheoryDeveloper. In eleven model turns, TheoryDeveloper executed twelve
tools: it inspected its workspace, searched and read all three frozen source
documents, wrote a 240-line Markdown/LaTeX derivation, wrote its compact
handoff, attempted one local edit that failed, reread the affected document,
successfully edited it, and wrote the final handoff.

The last successful `write_theory_workspace` observation reported all of the
following at once:

- `workspace_valid=true`
- `checkpoint_commit_ready=true`
- no checkpoint blockers or validation errors
- zero model tool calls remaining
- one standard turn remaining
- `final_disposition_required=false`

On the next provider turn, the same model selected a client tool, but the
generic loop rejected it before execution because the model-tool call budget
was exhausted. The terminal failure was
`theory_developer_packet_validation_failed`. A recovery checkpoint retains the
candidate but cannot authorize continuation of this consumed task.

## Theory Audit

The unaccepted document cleanly separates deterministic finite-sample algebra
from iid finite-variance statements. Its displayed derivations correctly obtain
the delete-one mean, the average of leave-one-out estimates, the identity
`V_J = s^2/n`, and the corresponding unbiasedness statement under the stated
sampling assumptions.

This operator reading is diagnostic only. No isolated referee accepted the
document, no hidden semantic evaluation ran, and no executable consumer tested
the handoff. The document therefore earns no accepted theory, code, empirical,
or end-to-end credit.

The document also omits the visible callable signature `run_estimator(request)`
from its algorithm specification. That is a real model-owned contract omission,
but no generated source was produced or executed in this run.

## Evaluation Design Defect

The visible task lists an output field named `estimate` without defining its
statistical meaning. The model supplied one coherent interpretation aligned
with the named jackknife-variance procedure. The frozen hidden algorithm
authority imposed a different interpretation that was not entailed by the
visible task or model-visible source snapshot.

Consequently, this benchmark cannot fairly attribute any hidden algorithm
failure to the model even if the code lane had run. Hidden execution did not run
in fact. Future tasks must define the meaning, shape, units, and indexing of
every required output field before gold is frozen, and evaluator preactivation
must verify that all hidden ABI assertions follow from the visible contract.
No hidden expected value or evaluator implementation is added to runtime RAG.

## Shared Harness Correction

Code commit `0d8a01e5` reserves one control-plane terminal disposition after
the unchanged research-action tool budget. This allows the source-owning model
to explicitly commit a valid checkpoint or report a gap after its last research
action. It does not add a research turn, read, write, scratch execution, retry,
agent, Architect iteration, model tier, or content rule.

This follows the useful OpenAI Codex harness distinction between iterative
environment actions and the model-owned action that terminates a turn. It does
not import Codex app-server, thread scheduling, provider transport, or a second
persistence authority. The affected panel passed `169/169` and the full suite
passed `778/778` in 65.02 seconds. These are deterministic mechanism results;
the frozen jackknife outcome remains unchanged.
