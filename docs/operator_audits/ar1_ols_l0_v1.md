# Stationary AR(1) OLS L0 v1 Operator Audit

## Disposition

The single frozen exact-Haiku product draw is **failed, consumed, and closed**.
AgentRuntime reached independently accepted theory and algorithm artifacts, but
the Algorithm-Simulation collaboration loop exhausted all 24 outer iterations
before an accepted simulation, simulation review, or Critic decision. The
research and full hidden-gold outcomes remain `0/1`; the task must not be
rerun, repaired, resumed, or retrospectively rescored.

Run directory:
`runs/main_worker_research_l0_ar1_ols_20260821_v1_schema_v2_codex_exact_haiku`

Immutable evidence hashes:

- Runtime manifest SHA-256: `f7fda082e7b21c3aa60a7f01b92930ddf3d6b8a6960b011eb9503ad5d0a64b0f`
- Hidden-gold report SHA-256: `0f832286e140a38d641399c4e98f0d13567ae18b797d43718f1af6d64dfb0db6`
- Runtime failure summary SHA-256: `71549aa27482fe4bbbc55c749b4212a61aa4c2daf613431a707d61651c24c2ba`
- Runtime completion summary SHA-256: `28779bc8fd4c3245caa8b327cd9670d67dd28558edbca95245a10e4a50a135ca`

Every enabled role used `claude-haiku-4-5-20251001`; no Sonnet or Opus
escalation occurred. Formalization was `not_applicable` by frozen task intent,
no formal lane ran, and Lean was not a blocker.

## Live Trajectory

TheoryDeveloper searched the three-document task snapshot, read the relevant
sources, used a scientific scratch execution, and authored two persistent
Markdown/LaTeX documents before explicitly committing its checkpoint. An
isolated referee read both documents, used its scratch and source tools, and
accepted the theory packet.

AlgorithmEngineer then authored one executable estimator. Its local sandbox
passed, an independent code-semantic reviewer accepted it with no findings, and
the exact reviewed source was frozen in the downstream handoff. Architect's
metric author and isolated metric reviewer also completed the pre-execution
protocol and authorized simulation.

The first Simulation workspace used three direct source submissions. It fixed a
JSON serialization error and a missing callback invocation itself. Its third
source executed the estimator on the main DGPs, but one deliberate invalid-input
probe called the estimator on an all-zero series. The estimator correctly raised
`ValueError`, and the simulation source explicitly intended that rejection to
count as a passed edge case. The sandbox callback changed the exception to
`AcceptedEstimatorRuntimeError`, recorded every caught estimator exception as a
fatal dependency failure, and terminated the Simulation workspace.

Runtime then reopened AlgorithmEngineer even though the reviewed estimator hash
had not changed. Six Simulation reroutes and six Algorithm revision checkpoints
followed; Algorithm source submission recorded one success and 48 failures in
the full progress trace. The terminal kind was
`budget_exhausted_with_pending_next_task`, not a completed scientific result.

## Hidden Evaluation

The evaluator-only phase ran only after AgentRuntime terminated and generated
no runtime feedback. It found:

- accepted theory: all 7 hidden semantic checks passed;
- accepted scientific source: all 11 hidden algorithm checks passed;
- accepted scientific source under hidden empirical evaluation: all 9 checks
  passed across 7,500 estimator invocations;
- full task: failed because runtime never accepted simulation or reached Critic.

These component passes are real evidence that the accepted model artifacts were
scientifically useful. They do not override the frozen runtime completion
contract or turn the task into a `1/1` success. Hidden expected values and
evaluator source remain outside repository, RAG, and model workspaces.

## Shared Harness Defect

The callback wrapper violated ordinary coding-agent semantics in two ways. It
changed the exception class visible to consumer code, and it let runtime infer
cross-workspace fault ownership merely because a bound estimator raised. The
runtime could not know whether the consumer request satisfied the estimator's
model-authored input domain. A valid expected-rejection test was therefore
converted into an Algorithm repair loop.

The research summary also reported
`metric_protocol_independently_accepted=false` because it located the reviewed
metric packet only through a final reviewed simulation manifest. This erased a
completed upstream stage when downstream work remained incomplete.

## Shared Correction

Code commit `dd3d09bfbf02565a97fcb588a573a5d178d9da34` makes the scientific
callback transparent. Python and R callbacks preserve the original exception
type inside model-authored consumer code. A handled exception remains part of
the consumer program result; only an exception escaping `run_sandbox` is an
execution failure.

Unhandled dependency observations now return first to the same Simulation
coding session. The model can revise its current source or explicitly call
`report_bound_dependency_failure`. Runtime verifies the existing source IDs and
hashes before transferring that raw observation; it does not choose the owner,
edit either source, add a repair agent, or increase any turn, retry, or outer
iteration budget. Research evaluation now finds an independently accepted
metric protocol directly by its theory packet ID and hash, without treating it
as simulation acceptance.

A deterministic, non-product replay of the exact frozen estimator and third
simulation source under the corrected callback executed successfully, recorded
75 estimator invocations, preserved the expected zero-series rejection, and
reported no estimator runtime failure. It also retained a model-authored
constant-series metric defect for the Simulation workspace to revise. This
replay is mechanism evidence only. The affected panel passed `137/137`, the
capability-ladder panel passed `14/14`, and the full suite passed `793/793` in
64.55 seconds. The frozen AR(1) result remains unchanged at `0/1`.
