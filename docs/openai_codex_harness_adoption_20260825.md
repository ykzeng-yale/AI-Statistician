# OpenAI Codex harness adoption audit

Date: 2026-08-25

Upstream reviewed: [`openai/codex`](https://github.com/openai/codex) at
`34c5303f49d08a5a41294e2531d1e64b40c0302d` (Apache-2.0).

Latest implementation commit:
`e7d0174a0028aa8ee9371bf2794660a045c465d0`.

Primary references:

- [`run_turn`](https://github.com/openai/codex/blob/34c5303f49d08a5a41294e2531d1e64b40c0302d/codex-rs/core/src/session/turn.rs)
- [`ToolRouter`](https://github.com/openai/codex/blob/34c5303f49d08a5a41294e2531d1e64b40c0302d/codex-rs/core/src/tools/router.rs)
- [model-actionable tool failures](https://github.com/openai/codex/blob/34c5303f49d08a5a41294e2531d1e64b40c0302d/codex-rs/core/src/tools/parallel.rs)
- [tool failure taxonomy](https://github.com/openai/codex/blob/34c5303f49d08a5a41294e2531d1e64b40c0302d/codex-rs/tools/src/function_call_error.rs)
- [terminal-error pending-input preservation](https://github.com/openai/codex/blob/34c5303f49d08a5a41294e2531d1e64b40c0302d/codex-rs/core/src/tasks/regular.rs)
- [checkpoint context-window compaction](https://github.com/openai/codex/blob/34c5303f49d08a5a41294e2531d1e64b40c0302d/codex-rs/core/src/compact_token_budget.rs)
- [app-server thread/turn/item protocol](https://github.com/openai/codex/blob/34c5303f49d08a5a41294e2531d1e64b40c0302d/codex-rs/app-server/README.md)
- [multi-agent message tool](https://github.com/openai/codex/blob/34c5303f49d08a5a41294e2531d1e64b40c0302d/codex-rs/core/src/tools/handlers/multi_agents_v2/message_tool.rs)
- [standalone sandbox implementation](https://github.com/openai/codex/tree/34c5303f49d08a5a41294e2531d1e64b40c0302d/codex-rs/sandboxing)
- [OpenAI's agent-loop explanation](https://openai.com/index/unrolling-the-codex-agent-loop/)

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

Commit `e7d0174a` applies the same source-owner lifecycle to future metric
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
Future theory evaluation must include plausible false derivations and genuine
independent reconstruction; no consumed run may be rerun or rescored.

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
