# OpenAI Codex harness adoption audit

Date: 2026-08-25

Baseline source audit: [`openai/codex`](https://github.com/openai/codex) at
`4213b38f3c555049bf6f494065698a3dfe587c16` (Apache-2.0).

Latest incremental recheck:
`dc08ace7821614a702b1214c9d08ae0db2634d82`.

Latest implementation commit:
`ba9e553ff9b85a4cdd7367c21abdab2be531b6c7`.

Primary references:

- [`run_turn`](https://github.com/openai/codex/blob/4213b38f3c555049bf6f494065698a3dfe587c16/codex-rs/core/src/session/turn.rs)
- [`ToolRouter`](https://github.com/openai/codex/blob/4213b38f3c555049bf6f494065698a3dfe587c16/codex-rs/core/src/tools/router.rs)
- [`ToolOrchestrator`](https://github.com/openai/codex/blob/4213b38f3c555049bf6f494065698a3dfe587c16/codex-rs/core/src/tools/orchestrator.rs)
- [`TurnContext`](https://github.com/openai/codex/blob/4213b38f3c555049bf6f494065698a3dfe587c16/codex-rs/core/src/session/turn_context.rs)
- [`apply_patch` runtime](https://github.com/openai/codex/blob/4213b38f3c555049bf6f494065698a3dfe587c16/codex-rs/core/src/tools/runtimes/apply_patch.rs)
- [atomic step activation](https://github.com/openai/codex/blob/4213b38f3c555049bf6f494065698a3dfe587c16/codex-rs/core/src/session/step_activation.rs)
- [committed step settings](https://github.com/openai/codex/blob/4213b38f3c555049bf6f494065698a3dfe587c16/codex-rs/core/src/session/step_settings.rs)
- [model-actionable tool failures](https://github.com/openai/codex/blob/4213b38f3c555049bf6f494065698a3dfe587c16/codex-rs/core/src/tools/parallel.rs)
- [tool failure taxonomy](https://github.com/openai/codex/blob/4213b38f3c555049bf6f494065698a3dfe587c16/codex-rs/tools/src/function_call_error.rs)
- [terminal-error pending-input preservation](https://github.com/openai/codex/blob/4213b38f3c555049bf6f494065698a3dfe587c16/codex-rs/core/src/tasks/regular.rs)
- [checkpoint context-window compaction](https://github.com/openai/codex/blob/4213b38f3c555049bf6f494065698a3dfe587c16/codex-rs/core/src/compact_token_budget.rs)
- [paginated thread history](https://github.com/openai/codex/blob/4213b38f3c555049bf6f494065698a3dfe587c16/codex-rs/app-server-protocol/src/protocol/v2/thread.rs)
- [multi-agent input lineage](https://github.com/openai/codex/blob/4213b38f3c555049bf6f494065698a3dfe587c16/codex-rs/core/src/session/input_queue.rs)
- [standalone sandbox implementation](https://github.com/openai/codex/tree/4213b38f3c555049bf6f494065698a3dfe587c16/codex-rs/sandboxing)
- [credential-safe Git metadata](https://github.com/openai/codex/blob/4213b38f3c555049bf6f494065698a3dfe587c16/codex-rs/protocol/src/sanitized_git_url.rs)
- [bounded reserved-tool schemas](https://github.com/openai/codex/blob/4213b38f3c555049bf6f494065698a3dfe587c16/codex-rs/tools/src/json_schema.rs)
- [OpenAI's agent-loop explanation](https://openai.com/index/unrolling-the-codex-agent-loop/)
- [OpenAI's App Server harness explanation](https://openai.com/index/unlocking-the-codex-harness/)

## Decision

Reuse the harness principles and protocol boundaries, not the Codex product
runtime as another scheduler or generator backend.

Codex is a Rust application centered on the OpenAI Responses protocol. AI
Statistician is a Python research runtime whose production workers use Claude
Haiku or Sonnet. Embedding `codex exec`, app-server, or the Python Codex SDK
would introduce a second conversation owner, a second tool router, and an
OpenAI-model dependency. The existing prohibition on treating Codex, Claude
Code, Cursor, or similar agents as a pure `GeneratorBackend` remains correct.

## Adopted principles

1. **One model-owned turn loop per workspace.** The model chooses a tool, the
   runtime executes it, and the raw observation returns to the same model
   context. Ordinary Python, R, Lean, retrieval, or compiler failures do not
   route through Architect or a repair agent.
2. **Stable tool surface.** Tools keep a deterministic order and remain stable
   during a workspace session, preserving prompt-cache prefixes. Runtime
   capability changes are appended as observations instead of rewriting old
   context.
3. **Persistent work is external state.** Markdown/LaTeX, source files, Lean
   files, and execution artifacts are authoritative. Conversation transcripts
   and cross-agent messages carry compact hash-bound references, not recursive
   copies of those artifacts.
4. **Tool failures are observations.** Model-actionable input, compiler, and
   execution errors return directly to the source-owning model. Internal
   runtime failures fail closed and do not expose secrets.
5. **Sparse collaboration.** Separate agents own separate sessions. A handoff
   names the objective and artifact references; findings are immutable,
   addressable messages. The parent coordinates only cross-workspace decisions.
6. **Lifecycle telemetry is not scientific authority.** Turn/item start and
   completion events record status, duration, usage, and artifact identity.
   They never substitute for mathematical, empirical, or kernel evidence.

## Current mapping

| Codex primitive | AI Statistician implementation |
| --- | --- |
| persistent thread and exact-prefix history | `client_tool_loop.py` session transcript and prompt caching |
| tool registry/router | caller-owned `ClientToolDefinition` plus `execute_tool` |
| function-call output returned to the same turn | `ClientToolExecutionResult` |
| rollout persistence/resume | content-addressed `ClientToolWorkspaceSessionRef` |
| shell/tool sandbox | scientific Python/R sandbox and Lean project boundary |
| parent-child message | typed `AgentTask` plus artifact/finding references |
| turn/item telemetry | `agent_runtime_substage` and compact manifests |

## Specialist collaboration

Codex supplies a reusable inner-loop principle, not the scientific workflow.
AI Statistician keeps one source-owning session for each active workspace:

| Workspace | Model-owned state and actions | Harness-owned boundary |
| --- | --- | --- |
| TheoryDeveloper | Markdown/LaTeX claims, derivations, source reads, Python/R scratch, checkpoint or honest gap | file/hash lineage, sandbox, task intent, isolated referee |
| AlgorithmEngineer | Python/R source, tests, direct execution-driven revisions | executable ABI identity, sandbox, source/result hashes |
| SimulationEngineer | exploratory or frozen confirmatory source and interpretation of raw outcomes | accepted dependency refs, blinded outcomes, frozen evaluator authority |
| Formalizer | Lean source edits, declaration search, proof-state inspection, compile-driven revisions | active Statlib/Mathlib project, target identity, axiom audit, kernel promotion |

Ordinary source, compiler, or tool-input failures remain inside the owning
session. Independent reviewers get only exact artifact references and their own
isolated tools. Architect chooses initial task intent and resolves genuine
cross-workspace conflicts or stopping; it is not a routine error router.
Formalizer may scout in parallel, but deep proof blocks completion only when the
frozen task intent requires formal evidence.

## Correction made from this audit

The independent Theory referee already owned a persistent Markdown report, but
its terminal tool also required one PASS/FAIL/UNCERTAIN value for every claim,
fixed review dimension, and estimator. That duplicated the report, enlarged a
dynamic tool schema, encouraged shallow checklist completion, and made runtime
derive scientific judgment from model-self-reported rows.

The live referee contract now carries only:

- exact report SHA-256;
- inspected evidence references;
- model-owned `ACCEPT` or `REVISE` disposition;
- actual blocking findings;
- ordered dispositions for immutable prior findings when present.

Runtime still validates report identity, source hashes, reviewer independence,
reference namespaces, prior-finding lineage, and disposition consistency.
There is no deterministic content repair and no separate repair model; a
rejected terminal envelope returns the exact validation observation to the same
reviewer session.

## Durable checkpoint context windows

The next shared scaling defect was measured in immutable live artifacts rather
than inferred from a framework diagram:

- TheoryDeveloper sessions reached 95--122 KB and 19--27 messages across
  unrelated known-result and replication tasks.
- The Statlib Formalizer session persisted a 96 KB, 41-message window, then
  resumed by replaying that complete transcript before another 21 KB current
  Lean-workspace prompt. The first resumed request therefore carried 114,050
  content characters, and its next persisted window grew to 121 KB.
- Scientific-code sessions used the same full-replay resume mechanism and have
  already reached 77 KB in a short source-revision workspace.

Checkpoint resume now follows the Codex fresh-context-window principle without
copying Codex's runtime or adding a summarizer. The shared client-tool helper:

1. verifies the sealed parent transcript bytes, model, system prompt, stable
   tool surface, session identity, and workspace root;
2. binds the new window to the exact current Theory workspace hash or verified
   scientific/Lean checkpoint ID;
3. retains the parent transcript reference and fingerprint as lineage;
4. starts the model from the current authoritative document/source,
   environment observation, and unchanged workspace tools;
5. explicitly records that the prior transcript was not replayed and no model
   or runtime summary was used.

History remains linear within each workspace segment. A durable checkpoint is
the only context-window boundary, so there is no token threshold, silent
truncation, extra model call, or content-specific compression rule. Mathematics,
code, Lean source, findings, and raw diagnostics remain external authoritative
artifacts; conversation history remains non-authoritative lineage.

## Terminal errors and pending workspace state

Upstream commit `d7510aa` fixed a subtle lifecycle bug: pending user input or
agent mail could immediately restart a turn after terminal compaction failure.
Codex now completes the failed turn and preserves that pending input for a later
explicit request. AI Statistician had the analogous problem one level higher.
Its model backend already retries the exact unanswered provider request, but
`AgentRuntime` could then rerun the entire subsystem after those request-local
retries were exhausted. A partial Theory, R/Python, Simulation, or Lean session
could therefore be discarded and regenerated from an older task payload.

Commit `700f3360` removes that whole-subsystem retry plane. The shared client-tool
loop now distinguishes three outcomes:

1. a caller-declared input error is a model-visible tool observation in the same
   session;
2. a terminal provider error seals the exact pending transcript and history,
   makes no automatic next model call, and enters the workspace's existing
   checkpoint path;
3. an internal tool failure remains secret-free and non-model-actionable, but it
   also carries the exact transcript/history needed to seal the current workspace
   rather than losing it.

`AgentRuntime` executes each subsystem once per graph node. An uncaught terminal
subsystem error records one content-addressed pending `AgentTask` for explicit
resume; it does not emit a retry event or consume another source-owner session.
Formalizer's separate provider-retry task was removed for the same reason. This
deleted more code than it added and introduced no repair worker, scheduler,
scientific rule, model escalation, or new iteration budget. Provider-local
transport retries still repeat only an identical request that produced no model
response.

The regression evidence is compositional: the shared harness and outer runtime
passed `41/41`; existing Theory, scientific Python/R, and Lean checkpoint suites
passed `85/85`; adjacent runtime, CLI, Formalizer, and audit suites passed `93/93`.
No live model call or consumed-task rerun occurred, so this is mechanism evidence
only.

## Generated-code reviewer submission

The fresh ridge known-result draw exposed another direct harness mismatch. Its
model-authored ridge source executed successfully, but the independent reviewer
put five human-readable evidence descriptions where the compact envelope
required RFC 6901 pointers. The old reviewer made one structured-output call and
terminated the full research task on this transport error.

Codex separates `FunctionCallError::RespondToModel` from fatal runtime errors.
`ToolCallRuntime` turns the former into an unsuccessful function-call output,
records it in the active conversation, and lets the same turn continue. AI
Statistician now applies that behavior through its existing provider-neutral
`client_tool_loop.py`:

1. GeneratedCodeSemanticReviewer receives the exact source and review material
   in an isolated native Claude client-tool session.
2. The model submits its Markdown review and compact judgment through one
   terminal tool.
3. Runtime validates evidence pointers, immutable lineage, verdict consistency,
   and document identity without changing the judgment.
4. An invalid submission returns the exact bounded validation observation to
   the same reviewer session as an error tool result.
5. A valid resubmission closes that workspace; repeated invalid submission still
   fails closed.

This is not a repair agent or full-packet regeneration callback. The same model
owns both submissions, the reviewed source never changes, Architect is not
invoked, and no empirical or proof authority is promoted. The one corrective
turn is available only after a real rejected terminal submission.

The upstream delta from the previously reviewed `d52478c5` pin to `7c6eb0e`
contains one commit. It scopes stop-hook rejection for unattended memory
consolidation and documents private Multi-Agent V2 analytics; the adopted
tool-error continuation, turn loop, parallel gate, and collaboration mechanisms
are otherwise unchanged.

## First disjoint live validation

The next pre-frozen task, Beta-Binomial posterior and predictive moments, used
the corrected harness in one fresh exact-Haiku run. It completed the canonical
non-formal graph and passed evaluator-only theory, executable-interface,
algorithm, and empirical authority (`1/1`). Two ordinary failures demonstrate
the useful mechanism directly: TheoryDeveloper corrected one invalid document
tool input in the same session, and AlgorithmEngineer corrected a failing
model-authored smoke check after receiving the raw sandbox result in the same
source-owning session. The compact generated-code terminal tool accepted both
executed sources, so the Ridge transport failure did not recur.

This is evidence for same-owner model/tool iteration and isolated review, not
for importing Codex itself. The task used the existing Claude provider-neutral
loop, one AgentRuntime, artifact hashes, and evaluator-only gold. It used no
Codex app-server, Responses transport, thread manager, repair worker, or second
scheduler. Formalization was not applicable. At that point the aggregate
research ladder was `1/30`; exact Lean closure remained unproved.

Operator review also found that the metric author and reviewer accepted an
internally inconsistent explanation mixing absolute standard error, relative
error, and standardized error. The shared future-task correction is prompt
level: the same models must recompute uncertainty on the metric's actual
comparison scale and report unit or arithmetic contradictions. No task formula,
numeric detector, output patch, rerun, or rescore was added.

## Source replication and grounded judgment

The next disjoint task reran the unchanged published PyMLE CIR example from a
pinned repository commit and compatibility environment. The source-owning
Haiku session selected 20 source/document tools over 14 turns, executed the
author entrypoint once, wrote a 320-line Markdown report, and committed one
hash-bound checkpoint. AgentRuntime used three outer traces and no unrelated
code, simulation, or Formalizer lane. The frozen identity/output harness passed
`11/11`, making PyMLE the first protocol-level source-replication pass and the
aggregate `2/31`.

Operator audit then found an important semantic false positive. The report
correctly denied bias inference from one seeded path but elsewhere called one
estimate substantially biased downward; the calibrated hidden Haiku judge
marked every claim satisfied. This did not justify a repair worker, phrase
detector, extra scheduler, or rescore. It justified a smaller terminal
envelope: future claim statuses must include one decisive verbatim excerpt from
the candidate, runtime verifies only that observation binding, and the public
result stores only its hash. A new unrelated contradiction diagnostic
calibrated `2/2` and failed correctly under exact Haiku.

This is the same harness principle used by Codex tool turns: a model decision
must be grounded in the actual observation that produced it. It is not a reason
to import Codex's transport or orchestration stack. The implementation changed
no net production Python lines and the full repository passed `873/873`.

The official checkout was refreshed from `70b5cfc` to `ed42068`. Two of the three
upstream commits add a turn-scoped service tier and avoid allocating strings when
counting serialized JSON bytes. The third is the terminal-error pending-input
fix adopted above. The tool router, model-actionable failure taxonomy,
context-compaction, and multi-agent message boundaries remain otherwise
compatible with the prior audit.

The checkout was subsequently fast-forwarded to `34c5303`. The relevant later
changes add a bounded Guardian transcript window, preserve authorization context,
parse Codex-managed worktree settings, instrument shell snapshots, and avoid
routing directory changes to closed agents. None warrants importing another
runtime component. AI Statistician's independent scientific reviewers should
read exact hash-bound artifacts, not a lossy parent-chat transcript, and its
canonical research graph does not own Git worktrees or user approval UI. The
general lifecycle lesson remains useful: closed specialist sessions are not
valid routing targets, while durable artifacts remain available to a fresh
explicitly authorized session.

## Complete-randomization live validation

The third disjoint post-adoption run exercised the lifecycle more sharply. In
one exact-Haiku source-owner session, a failed Python execution returned its raw
traceback, a later provider-truncated tool input was recorded without execution,
and the model then submitted and committed a passing source. An isolated source
reviewer made an invalid terminal tool submission, received the bounded validator
observation in the same context, and submitted a valid envelope. No outer
subsystem replay, RepairAgent, or Architect error route occurred.

The run still failed `0/1`, which separates harness mechanics from scientific
capability. The accepted estimator violated two explicit public ABI clauses;
exact empirical enumeration nevertheless passed `8/8`. The metric author then
received two exact independent findings but regenerated a large structured
packet whose prose changed while the two rejected numeric fields did not. The
reviewer correctly blocked confirmatory execution. Finally, author, isolated
preflight, and hidden semantic judge all accepted a derivation containing false
load-bearing intermediate algebra even though their prompts already required
reconstruction.

Commit `e7d0174a` was the first application of the same source-owner lifecycle to future metric
protocols. It replaces detached structured-output regeneration with one
persistent `metric_protocol.json` and two stable tools: exact read and complete
source submission against the current parent SHA-256. Mechanical validation
errors return to the same author transcript; an isolated pre-outcome reviewer
then returns exact findings to that same source owner, which submits changed
complete source without an Architect route or content patch. Terminal provider
or tool-loop failure seals a compact transcript/file checkpoint and authorizes no
automatic retry.

The implementation deliberately became smaller while doing this. Obsolete
response schemas, structured-output retry telemetry, duplicated ownership truth
tables, and cumulative segment counters left the canonical path. It imports no
Codex runtime component and adds no JSON patcher, RepairAgent, scheduler, formula,
numeric detector, or model escalation. Regression tests exercise invalid source
submission, exact validator feedback, parent-hash continuation, isolated review,
and same-session revision. The complete suite passed `879/879`; top-level
production Python is 149,919 lines, below its unchanged 150,000-line budget.

This is future-task mechanism evidence only. The complete-randomization run stays
immutable `0/1`, and its false intermediate mathematics remains unresolved.
The Mann-Whitney live validation below showed that this two-tool form was still an
intermediate design because the complete document remained inside a terminal call;
commit `be8d57ab` supersedes that transport without changing this historical result.

Commit `b9ece439` applies the same persistent-workspace principle to theory review.
Before candidate-document access, the existing isolated referee must write its own
reconstruction from the question, contract, and any model-selected source or scratch
observations. The same session then inspects the candidate and revises the same
Markdown report by explicit comparison. Runtime retains every version under its
SHA-256 and validates only ordering, file identity, and final-report binding. It does
not parse equations, choose a derivation, add a reviewer, make another model call, or
create a second scheduler. Checkpoint continuation preserves this chronology through
the already existing transcript and content-addressed files.

Future theory evaluation must test plausible false derivations on a disjoint frozen
task. The new chronology has regression evidence only; no consumed run may be rerun
or rescored.

## Bootstrap live validation and Simulation ownership

The next disjoint bootstrap-mean draw validated the theory chronology but exposed a
scientific-code lifecycle mismatch. TheoryDeveloper committed two authoritative
Markdown/LaTeX documents after twelve model/tool turns. The isolated referee wrote a
blind reconstruction before candidate access, inspected seven exact ranges, revised
its report, and accepted a theory packet that subsequently passed all frozen hidden
theory checks.

The same run failed `0/1` for scientific code. The estimator accepted numeric strings
through `float(value)` despite an explicit public no-coercion clause, and its isolated
reviewer false-accepted that behavior. The generated simulation used exact floating
equality in a location-shift check, so one of eight frozen contracts failed. More
importantly for harness design, the source owner had received only a smoke-success
observation before commit, while the isolated Simulation reviewer focused on the
upstream estimator rather than the exact current simulation source.

Commit `26b8e124` applies the existing Codex-shaped turn loop at that boundary:

1. one Simulation source-owning model session chooses, authors, and executes a
   separate-seed exploratory diagnostic;
2. raw sandbox output returns to that same session, which may revise source and must
   explicitly commit exact bytes;
3. those exact committed bytes execute once on the blinded confirmatory cohort;
4. confirmatory outcomes remain withheld, so a failed scored run cannot become a
   source-repair prompt;
5. the isolated generated-code reviewer is told that `exact_executed_artifacts` is
   its current target and `upstream_generated_dependency` is context only.

This is not a task-specific test prescription. The model owns the diagnostic program,
source changes, and stopping decision. The harness owns only separate seed/sandbox
identity, exact source lineage, confirmation blinding, and reviewer target identity.
The existing replay path remains zero-sampling and deterministic. No agent, module,
scheduler, retry, formula, numeric rule, or model escalation was added; `882/882`
tests passed.

The bootstrap result remains immutable `0/1`. This commit has future-task mechanism
evidence only.

Commit `5daec039` closes the corresponding Algorithm review harness gap without
adding a repair path. When, and only when, the current review target is an
Algorithm artifact whose exact source and manifest hashes agree, the same isolated
reviewer session may choose `run_exact_estimator_review_probe`. The reviewer authors
an ordinary Python or R `run_sandbox` diagnostic, and the existing scientific
sandbox binds the immutable estimator bytes behind the `estimators` interface. Raw
diagnostic output returns to that reviewer context before its terminal verdict.

The tool does not edit estimator source, select test cases, interpret results, inspect
the blinded confirmatory cohort, route work, or confer empirical/proof authority.
Simulation artifacts and hash-inconsistent Algorithm artifacts receive no probe tool.
The model may submit a review without probing. At most three ordinary probe turns are
available; the shared client-tool loop separately reserves the terminal disposition.
Thus the harness supplies executable observation while the reviewer still owns the
scientific judgment.

This is a direct selective reuse of Codex's `run_turn` principle: model-selected tool
action, caller-owned execution boundary, raw observation, then the same model context.
It is not an import of Codex core or another scheduler. The change also removes the
generated-code reviewer's obsolete fixed-dimension compatibility layer and a 247-line
unused feedback-copy utility. Production Python falls from 149,999 to 149,868 lines;
the complete repository passes `885/885`. The consumed bootstrap draw remains `0/1`,
and this mechanism requires a future disjoint frozen task for capability credit.

The upstream checkout was also refreshed from `34c5303` to `a9e447a`. The intervening
commits concern managed plugins, MCP reconnect behavior, cloud-config retry,
Guardian proxy state, goal continuation, and command migration. They do not alter the
adopted `run_turn`, `ToolRouter`, or `ToolOrchestrator` lifecycle in a way that
justifies importing Codex core, app-server, provider transport, or thread management.

## Mann-Whitney live validation and external metric state

The next disjoint Mann-Whitney R task remains immutable `0/1`, but it supplied a
cleaner diagnosis. Theory passed frozen mechanical and semantic authority `7/7`,
the exact R estimator passed `14/14`, and exact empirical enumeration passed `6/6`
over all 41 assignments. The isolated code reviewer voluntarily ran two R probes
against exact source and recovered from one invalid terminal envelope in the same
session. Simulation and Critic were never reached because metric authoring failed.

That metric session persisted 13 messages. Four complete terminal inputs were
provider-truncated and correctly not executed. A fifth 8,041-byte document reached
validation but used the wrong top-level schema. This proved that the `e7d0174a`
two-tool interface was not yet truly external-state authoring: its terminal tool
still carried the whole artifact, coupling document length to disposition liveness.

Commit `be8d57ab` adopts the closer Codex analogue for future tasks. Runtime creates
only a structural `metric_protocol.json` scaffold. The same source-owning model can
read it, apply exact unique-literal replacements against the current parent SHA-256,
receive raw tool or schema observations, and continue editing. The terminal
`commit_metric_protocol` call contains only the exact current file hash, never the
document body. A truncated edit input is not executed, while the already external
file and transcript remain available to the same session.

This deliberately reuses the principle behind Codex `apply_patch`, not its product
runtime: model-selected deltas mutate external state; exact state identity is checked
at commit; observations return to the same turn loop. The current upstream step
activation/settings code additionally reinforces that one operation should bind to
one committed settings snapshot. AI Statistician does not import Codex app-server,
thread management, provider transport, subagents, or another scheduler.

The shared prompt projection now always removes duplicated artifact trees while
preserving authority leaves, portfolio schema, hard requirements, and implementation
ABI. On a deterministic replay of the consumed transcript it reduced 54,053
characters to 25,751 and preserved all 16 authority leaves. Provider truncation,
same-session invalid-commit correction, reviewer continuation, hash lineage, and
schema validation are regression tested; the full repository passes `887/887`.
Production Python is 149,954 lines, `research_agent_runtime.py` remains 24,973 lines,
and no module, agent, scheduler, task formula, numeric rule, model escalation, or
automatic retry was added. No model call or consumed-task rerun established this
post-consumption evidence, so Mann-Whitney v1 remains `0/1`.

The official checkout was then fast-forwarded from `a9e447a` to `7e1ee6d`. The
relevant new changes make per-step settings and activation explicit and atomic;
other app-server and product changes do not alter the selective-adoption decision.

## Fixed-effect meta-analysis validation and atomic edits

The next disjoint fixed-effect meta-analysis R task also remains immutable `0/1`.
Its three-document Markdown/LaTeX theory passed `7/7` hidden mechanical checks and
`7/7` calibrated semantic claims. Exact empirical behavior passed `7/7` checks over
12,000 estimator calls. The generated R estimator passed only `12/15` public-interface
checks, however: it did not reject malformed request keys or a named `theta0`, and the
isolated reviewer missed both explicit public boundaries with its one optional probe.

The runtime then exposed a narrower workspace issue. One commit observation reported
three invalid operator values. The source-owning model understood the feedback but the
v2 tool could replace only one exact literal per turn. It repaired two rows, exhausted
the standard workspace turns, and correctly failed its terminal commit with the third
row still invalid. Simulation and Critic did not run.

Commit `27f3893a` keeps the same model, session, three tool names, turn budget, and
hash-only terminal commit. `edit_metric_protocol` now accepts one ordered batch of
model-authored exact replacements under the current parent SHA-256. Runtime validates
every replacement against progressively revised bytes before mutating the external
document; if any match is absent, none of the batch is stored. There is no arbitrary
edit-count ceiling beyond the existing request-token boundary. The obsolete v2 input
shape was removed rather than retained as a hidden fallback.

The same commit asks the existing source reviewer to actively falsify explicit public
acceptance, rejection, and boundary behavior. When its exact-artifact probe is
available, the reviewer is encouraged to cover several load-bearing cases in one
model-authored probe. The harness still does not prescribe cases, maintain a fixed
checklist, inspect hidden outcomes, interpret probe results, patch source, or add a
reviewer, retry, call, turn, scheduler, or model escalation.

One regression deliberately supplies a malformed second replacement, confirms that
the first replacement was not persisted, and then succeeds from the unchanged parent
hash in the same session. Reviewer, workspace, core architecture, and full-repository
tests pass `889/889` in 70.09 seconds. Production Python remains below the unchanged
budget at 149,988 lines; `research_agent_runtime.py` remains 24,973 lines and
`AgentRuntime` remains 1,159 lines. This is future-task mechanism evidence only and
cannot repair or rescore the consumed meta-analysis draw.

## Theory-only review and latest upstream delta

The sole frozen Rao-Blackwell/Poisson theory-only draw remains immutable `0/1`.
TheoryDeveloper authored a 251-line Markdown/LaTeX derivation, and the isolated
referee authored a 232-line report ending `ACCEPT`. The old terminal validator
nevertheless rejected `ACCEPT` because no estimator was present, even though the
frozen contract marked both scientific code and empirical evidence not applicable.
The resulting estimator revision was control-plane work created by the harness, not
mathematical progress.

Commit `3a6af408` corrects the shared boundary for future tasks. The compact upstream
contract now retains runtime-owned `dimension_requirements`. Preflight derives one
`execution_handoff_required` bit from those frozen dimensions: theory-only review can
accept coherent mathematics without an estimator, while any applicable executable
lane still fails closed without one. The fixed six-row review-considerations transport
was deleted; the referee chooses the load-bearing derivation in its Markdown workspace.
No model, agent, call, turn, parser, task formula, repair path, scheduler, or fallback
was added. The production package shrank to 149,984 lines and the complete repository
passed `892/892` in 69.42 seconds.

The OpenAI Codex checkout was independently advanced by eleven commits from `7e1ee6d`
to `7c1e36c`. The relevant change promotes paginated thread/item history and deprecates
full-history hydration for durable threads. That reinforces AI Statistician's existing
content-addressed workspace checkpoints and compact handoffs; it does not justify
embedding Codex app-server, thread storage, Responses transport, or multi-agent
scheduling. Other changes in the delta concern code-mode transport, OAuth, security
program selection, onboarding, plugins, and UI recaps and were not adopted.

This post-run mechanism evidence cannot accept, hidden-evaluate, rerun, or rescore the
consumed Rao-Blackwell candidate.

## Task-intent identity across review returns

The next disjoint Neyman-Pearson/Bernoulli theory-only draw remains immutable `0/1`.
TheoryDeveloper authored and revised one 262-line Markdown/LaTeX document, and an
isolated referee authored a 181-line report. The direct referee-to-source-owner return
then rebuilt the research question without its frozen `task_intent`. That identity
loss exposed estimator, simulation, theorem, proof-plan, and formalization artifacts
even though every non-theory lane was `not_applicable`. The model spent the remaining
workspace turns trying to satisfy those irrelevant interfaces and correctly failed
closed before hidden evaluation.

Commit `8c736798` applies the Codex committed-step identity principle at the research
boundary. Direct review returns now use the canonical task-intent-bearing question
serializer. The existing TheoryDeveloper prompt and client-tool schema project only
artifacts writable under that frozen intent; stale or inapplicable parent handoffs stay
read-only. Executable and formal tasks retain their strict interfaces. The model still
owns every mathematical statement, derivation, edit, and stopping decision.

This is an identity and tool-surface correction, not a scientific repair. No formula,
mathematical parser, packet patcher, repair agent, retry, model turn, scheduler, or
task-specific branch was added. Focused regressions pass `128/128`, the complete
repository passes `894/894`, and production Python remains under budget at 149,998
lines. Operator audit separately finds mathematical defects in both candidate and
referee; neither those findings nor the post-run correction can repair, rerun,
hidden-evaluate, or rescore the consumed draw. The aggregate remains `2/38`.

## Credential-safe metadata and bounded schemas

The upstream delta from `7c1e36c` to `42624fd6` contains three harness-level
changes relevant to this system. Codex strips authentication material from Git
remote metadata before it reaches model requests, API responses, thread state,
or rollouts; reserved tool-schema parsing now preserves numeric and string
bounds; managed worktrees gain atomic no-clobber thread ownership metadata.

Commit `ccd05f0e` adopts the first boundary directly. Research source inventory,
LeanBlueprint and Autoform profiles, formal-source topology, and Lean RAG package
audits now sanitize URL userinfo and nonstandard SCP usernames before persistence.
The conventional SSH `git@` transport identity remains, malformed helper command
payloads fail closed, and duplicate local Git subprocess wrappers were removed.

AI Statistician already sends client-tool schemas directly to Anthropic or into
the SDK strict-schema transform. A regression now carries `minimum`, `maximum`,
and `maxLength` through that boundary, preventing a future adapter from silently
dropping model-visible limits. The worktree ownership implementation is not
imported: one persistent source owner and immutable artifact lineage already
provide the relevant scientific ownership rule without a Codex worktree manager.

The focused metadata/provider panel passes `46/46`; the complete repository
passes `895/895` in 69.87 seconds; production Python is 149,999 lines. There was
no model call, scientific-content rule, new module, agent, scheduler, retry,
turn, task rerun, hidden evaluation, or score change.

The checkout was subsequently refreshed from `42624fd6` to `62bfa41a`. The
three-commit delta changes a documentation link, enterprise MCP OAuth, and TUI
hyperlink wrapping. None of the audited core harness files changed, so it adds
no research-runtime mechanism to adopt.

A final refresh advanced upstream `main` to `4213b38f`. Its three commits add
SQLite-log and skill-attribution telemetry plus attachment-owned MCP permission
profiles. Of the audited core harness files, only `TurnContext` changed: remote
workspace roots are now materialized from `PathUri` values when constructing a
tool permission profile. The model/tool loop, router, orchestrator, patch
runtime, checkpoint semantics, and collaboration lineage remain unchanged. The
owner-scoped permission principle is correct, but AI-Statistician already binds
each scientific workspace to an explicit sandbox and artifact root. Importing
Codex MCP or app-server authority would therefore duplicate the control plane;
no product code change is justified by this upstream delta.

## Observation reconciliation inside theory workspaces

The immutable Neyman-Pearson/Bernoulli referee trace exposed a more specific
inner-loop failure. The same exact-Haiku session ran a later scratch calculation
that contradicted an earlier calculation, but its final Markdown report retained
both values and a stale conclusion. Extra tools, document reads, or another
reviewer would not address that failure: the source-owning model already had the
raw observation and the writable report in one persistent loop.

Commit `1862946b` strengthens that existing Codex-shaped loop without adding a
content judge. TheoryDeveloper and the isolated referee are prompted to make
scratch programs return definition-derived quantities, predicates, residuals,
or witnesses rather than a prewritten verdict. Before checkpoint or referee
submission, the same model must reconcile later observations with active
Markdown claims by revising, retracting, or marking contradictions uncertain.
The runtime still interprets no formula and repairs no scientific content.

Focused regressions pass `89/89`; the complete repository passes `895/895` in
69.78 seconds; production Python is 149,998 lines. No model call, extra turn,
agent, retry, scheduler, task rerun, hidden evaluation, or score change occurred.
The consumed draw remains `0/1`, the aggregate remains `2/38`, and exact
development Lean closure remains `0/2`.

## Terminal validation stays with the source owner

The next frozen McNemar draw exposed a control-flow mismatch rather than a need
for another repair layer. TheoryDeveloper used thirteen exact-Haiku turns to
write and revise a 210-line Markdown/LaTeX derivation plus its compact handoff.
Its final `commit_theory_checkpoint` returned a real structural-validation tool
error for two unresolved handoff references. Because TheoryDeveloper alone had
configured zero rejected-terminal recovery turns, the retained model session
ended before it could choose the existing resumable progress disposition.

Commit `1a1f11d9` reuses the shared client-tool loop's existing Codex-shaped
terminal recovery. It reserves one opportunity only after a terminal action is
rejected. Ordinary read, edit, search, scratch, execution, and outer-iteration
budgets do not change. The exact validator observation returns to the same
source-owning model, which may make another terminal disposition: commit valid
state, report a scientific gap, or checkpoint partial work for explicit
same-owner continuation. No nonterminal research action is permitted during
that recovery turn.

This is not a RepairAgent or automatic replay. The runtime neither changes the
packet nor interprets its mathematics. The immutable McNemar draft also contains
substantive conditional-distribution and two-sided-size errors, so its score
remains `0/1` independently of the transport defect. Focused client-tool and
Theory tests pass `47/47`, the complete repository passes `897/897`, and
production Python is 149,999 lines. The aggregate is `2/39`; exact development
Lean closure remains `0/2`.

## Referee observations must reach the terminal judge

The next disjoint Aitken GLS theory-only draw validates the useful part of the
Codex-shaped architecture and exposes its next missing boundary. One persistent
TheoryDeveloper session wrote a 352-line Markdown/LaTeX derivation, an isolated
referee session inspected it and wrote a separate 266-line report, and the
terminal Critic consumed compact hash-bound evidence. The frozen runtime and
hidden authority each returned `1/1` under exact Haiku.

Operator audit found that the core BLUE covariance decomposition is correct but
several local boundary claims are not. It also found a sharper harness defect:
the referee had one rejected scratch request and one failed Python execution,
with no successful scratch run, yet its report said all symbolic and numerical
verification passed without error. The terminal Critic saw the referee's
conclusion but not enough runtime-owned scratch status to challenge that claim.

Commit `4ebef6c5` follows Codex's function-call observation principle across the
existing reviewer-to-Critic boundary. The canonical evidence view now projects
scratch `status`, whether execution occurred, return code, source and result
hashes, and bounded raw errors. A failed or rejected scratch run can remain
nonblocking when the mathematical argument is independently sufficient, but no
model may call it successful. The referee and Critic still interpret the
mathematics; runtime only preserves observation identity.

This adds no GLS rule, mathematical parser, extra call, retry, repair agent,
scheduler, output patch, or imported Codex component. Focused regressions passed
`71/71`, the broader panel `194/194`, and the complete repository `899/899`.
The consumed Aitken score remains immutable `1/1` with explicit operator
semantic and referee-evidence caveats; the aggregate is `3/40`, while exact
development Lean closure remains `0/2`.

## Latest upstream recheck

The five-commit upstream delta from `4213b38f` to `dc08ace` leaves Codex's core
turn loop, tool router, tool orchestrator, parallel-safety gate, multi-agent
mailbox, input lineage, and compaction policy byte-identical. Two new mechanisms
were examined rather than inferred from release notes.

First, Guardian now prepares a fresh internal reviewer session with custom base
instructions, no inherited developer instructions, memories, skills, apps,
collaboration, child-agent tools, or MCP servers, and an intersection with the
parent's read-only permission profile. This validates AI Statistician's existing
artifact-only referee boundary: the referee starts from one fresh client-tool
request, receives no TheoryDeveloper transcript or hidden reasoning, has a
role-specific fixed tool surface, and writes into a separate review workspace.
Scientific referees retain isolated scratch and report tools because those are
part of mathematical review, but they receive no source-author write authority
and cannot promote evidence. Importing Guardian itself would add an OpenAI/Codex
session owner without strengthening that boundary.

Second, Codex now preserves unstructured MCP output as native content items
instead of serializing an entire mixed result array into one JSON string. AI
Statistician's current Claude tools return bounded textual or JSON observations;
large mathematics and source are already read by exact file ranges, and media is
not an active scientific tool modality. Changing the provider-neutral transport
now would add a second observation representation without a measured loss. The
content-item form remains the correct adoption point if a future scientific tool
returns mixed text and media or exact typed attachments.

The inspected upstream identities are:

- isolated Guardian reviewer configuration:
  `23acf475f63165fed2837af3fc7a9f182d6bd33d492387b69ae67c3f17580097`;
- Guardian policy template:
  `f47fbb2bdba5e7528bfae7f5e2844a7d45a3a922fa74b718f22b22917376cfcf`;
- typed tool-output protocol model:
  `d884f03dad7e9c57f622f0a3d576ebe292b0beb68c3b6a71d04bd69a415936f6`.

No product code change follows from this delta. Recent live traces do contain
multi-call document reads and formal searches, but document and source reads take
milliseconds; only formal-environment search averages roughly 0.6 seconds. A new
thread pool, read/write gate, and cancellation protocol would therefore save less
time than one model turn while increasing shared-state risk. Parallel execution
remains gated on a future measured tool-latency bottleneck.

## One authoritative theory workspace

The frozen Hoeffding U-statistic draw exposed a direct violation of the external
artifact principle. Its revised Markdown document correctly changed the degenerate
root-n boundary claim, while inherited `derivation_summary` and `self_critique` JSON
still stated the rejected conclusion. The handoff had become a stale second source of
mathematical truth even though its manifest called the documents authoritative.

Commit `75f05e46` removes substantive narrative from document-backed TheoryDeveloper
handoffs. Their `theory_derivation_packet` now contains only `claim_index`,
`sanity_check_index`, and an optional `formalization_handoff`; definitions,
derivations, assumptions, counterexamples, rejected alternatives, uncertainty, and
self-critique remain in hash-bound Markdown/LaTeX. Initial authoring and same-owner
revision use the same projection. Downstream semantic material also projects older
document-backed packets to this index-only view while retaining the SHA-256 of the
complete original packet for immutable lineage. Legacy non-document theory packets
retain their existing structured contract.

This is a transport correction, not a mathematical repair. It adds no agent, model
call, scheduler, parser, formula, task rule, retry, or fallback. The complete
repository passes `901/901`; production Python is 149,997 lines under the unchanged
150,000-line control-plane budget. The consumed Hoeffding draw remains immutable
`1/1` with its operator mathematical, evaluator, and duplicate-handoff caveats. The
change receives future-task mechanism evidence only and cannot repair, rerun,
hidden-evaluate, or rescore that candidate.

## Successful probes must remain inspectable

The same frozen Hoeffding trace exposed a second observation-boundary defect.
The accepted referee did execute one Python scratch probe, but chose the easy
positive kernel `h(x,y)=xy` and checked decomposition, means, and approximate
orthogonality. That probe did not discriminate the active root-n scaling,
conditioning, or degenerate-limit transitions. The terminal Critic received
the successful status and hashes, but not the exact probe source or raw metrics,
so it could not distinguish a relevant falsification attempt from a convenient
passing example.

Commit `ba9e553f` extends the existing canonical Critic view rather than adding
another reviewer. For each successful referee scratch execution, runtime reads
the already persisted source and result, verifies the source hash and both
recorded result hashes, and transiently exposes the exact model-authored probe
plus raw metrics to the same terminal Critic call. Missing files become
`UNAVAILABLE`; changed bytes become `HASH_MISMATCH`; neither state exposes
content. The prompt asks the model to judge what the probe actually
discriminates. Runtime still supplies no formula, expected answer, statistical
interpretation, or verdict.

Deterministic inspection of the immutable Hoeffding artifact resolved its first
scratch request as `REJECTED_CONTRACT` and its second as `HASH_VERIFIED`, with
the exact 3,538-character source and nine raw metrics. This was artifact reading,
not a model call, task rerun, hidden reevaluation, or rescore. The complete
repository passes `902/902` in 69.54 seconds, and production Python is 149,991
lines under the unchanged 150,000-line budget. The aggregate remains `4/41`.

## Standalone sandbox boundary

The open-source CLI exposes `codex sandbox` independently of model execution, so
its Seatbelt, Landlock/bubblewrap, and Windows isolation code is a plausible
future native Python/R execution provider. It is not yet a production dependency.
The locally available `codex-cli 0.149.0-alpha.4.3` is not pinned to the reviewed
source commit, and a successful `pwd` probe does not establish network denial,
filesystem confinement, process restrictions, resource limits, or reproducible
artifact capture.

Adoption requires a pinned source/binary hash, macOS and Linux denial probes,
explicit readable/writable roots, network-off verification, CPU/memory/output
limits, secret-free environment tests, and result/source hash parity with the
current sandbox envelope. Until then, Pyodide/WebR plus the existing Seatbelt
profile remains the canonical scientific boundary. Codex sandboxing may add a
native package-rich backend later; it cannot silently replace or weaken the WASM
path.

## Explicit non-adoptions

- No Codex TUI, app-server, MCP server, approval UI, or thread database inside
  the canonical research runtime.
- No whole-subsystem automatic replay after a terminal provider or tool error.
- No generic shell exposed to scientific workers where a narrower Python, R,
  Lean, source, or document tool provides a stronger execution boundary.
- No task-family formulas, Lean grammar rules, tactic templates, or
  output-specific patches in the harness.
- No mandatory all-agent pipeline. Theory, empirical work, and formalization
  remain task-intent driven; deep Lean work is optional unless the task's
  evidence contract requires it.

## Next adoption gate

Do not add another abstraction merely because Codex has one. A further shared
primitive is justified only when at least two workspaces exhibit the same live
failure. Candidate mechanisms must preserve exact artifact state and finding
lineage, avoid a second scheduler, and be evaluated on disjoint frozen tasks
before receiving capability credit.
