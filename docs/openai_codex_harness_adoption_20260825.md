# OpenAI Codex harness adoption audit

Date: 2026-08-25

Baseline source audit: [`openai/codex`](https://github.com/openai/codex) at
`4213b38f3c555049bf6f494065698a3dfe587c16` (Apache-2.0).

Latest incremental recheck:
`31d338a1af4f79b106f01f2f3a43ac4617ea19bb`.

The cumulative audit through that head continues to support the same boundary:
a delegated worker receives explicit authority-scoped tools and artifact context,
while one model session consumes its own tool observations. It does not supply a
scientific planner, Theory method, Simulation evaluator, Lean policy, or reason to
embed Codex's thread manager as a second scheduler.

Latest selective-adoption implementation commits:

- `dd8ae7f2`: keep semantic absence, explicit noncoverage, and unsupported
  claims `INCONCLUSIVE`, reserving `VIOLATED` for active contradiction or an
  invalid asserted derivation; the protocol change is confined to hidden
  evaluator qualification and cannot repair or route product work;
- `ea7a6ce0`: let frozen task intent decide whether executable evaluator
  authoring requires an accepted Algorithm handoff, validate required
  dependencies before any evaluator model call, and preserve standalone
  confirmatory Simulation for empirical-only tasks;
- `ecfc2403`: give the shared Python/R source workspace an atomic ordered
  multi-hunk exact patch, and require the existing explicit source-acceptance
  gate everywhere AlgorithmEngineer counts, reuses, materializes, or resumes a
  candidate; raw smoke success without model commit remains checkpointed
  diagnostic execution;
- `11ee99bd630cca6d5d5647e7050b7c2f2259badc`: require TheoryDeveloper
  and its isolated referee to align scratch observations with the complete
  proposition being judged, including object type, domain, and dimensional
  checks, while removing task-family examples and adding no tool or call;
- `f2e39edbea3c6f0122a14827d8d996c1854966bd`: require a revision
  reviewer to read the exact current immutable source in its own retained
  session before judging historical findings;
- `464cba39753ff2959e5d0f2c08491c982745cc60`: preserve a valid,
  independently reviewed Algorithm artifact across exploratory Simulation
  handoff and reserve structured semantic-review findings for active blockers;
- `b567aaa68195e85cc6f799f727b415903251af46`: separate model-owned
  Python/R source mutation from explicit execution, preserve an unexecuted draft
  across checkpoint resume, and keep commit as a later hash-bound decision;
- `3fe4bdb9fd3a63148078261e5efc10f76066ee98`: let the native
  Simulation source session own both scientific planning and implementation
  when the runtime can express the boundary as exploratory diagnostics or a
  frozen confirmatory source-acceptance ABI, removing the detached planning
  model call without weakening preregistration, blinding, or lineage;
- `2696ebb5b9bec0e8a7f15d61dfc44ff288f35b60`: keep one complete hidden
  candidate in one semantic context and return document-wide plus per-claim
  judgments together instead of fragmenting it across one call per claim;
- `ccaca8d7ffcc9cecd0380c0cb07879bcc395647f`: preserve one isolated
  metric-reviewer's incrementally updated draft across validator corrections
  instead of requiring complete-packet regeneration;
- `5d5125607c58bc5830ac11a27c6c64ce6764e344`: separate Algorithm
  developer diagnostics from independently preregistered confirmatory
  Simulation evidence without adding a content judge or another loop;
- `5fd585b8e9b6f00435a7ca796aaad651b2f5378f`: separate same-owner
  workspace continuations from outer research-graph iterations;
- `6f588ff13cb2adf4ab01d1ec61eaecdd8842c594`: remove the mandatory
  blind-write/read/rewrite sequence from independent theory review.
- `de531ad8d4173cc406593edb76606cb10be158b7`: bind frozen executable
  identity at Theory checkpoints and keep rejected reviewer verdict feedback in
  the same model-owned session.
- `54e5ca52eca6192885a8a11775f7728997610ac7`: preserve content-addressed
  accepted files and canonical workspace lineage across deferred continuations.
- `3f0ee0131d2b298bbb668e53afc132cae0ff562a`: give Python/R source owners
  the same model-authored exact-edit and immediate-execution loop as Theory and
  Lean while consolidating duplicate edit machinery.
- `e5cccbb276bb1ef66bb5f387b1bc992b4dfaa74c`: assign production scientific
  Critic work to Sonnet after a disjoint document-session test isolated model
  judgment, rather than evidence transport, as the remaining blocker.
- `3408012fd9305de3202effbcd12c1d452cf38bb2`: externalize accepted Theory
  documents from the canonical Formalizer opening prompt while preserving exact
  hash-bound reads and searches in the same model-owned Lean session.
- `8f5d6295019100dedfa566d01c3b5dee204ead7c`: add model-owned independent
  Lean scratch execution to the existing Formalizer session without mutating or
  promoting the active candidate source.
- `efe3017bcd2bf317008d6fabc75763496a97ade3`: remove TheoryDeveloper's
  obsolete post-workspace ABI model call, JSON prompt API, stage-recovery route,
  and dead packet-retry control so mathematical documents and executable ABI
  remain in one source-owning session.
- `e3255046ccfe33b463160bb5fd8f53b619eb59d9`: make Theory progress
  checkpoints restore cumulative model-observed tool state instead of silently
  resetting scratch, source-replication, read, write, and provenance state at a
  fresh context window.
- `0824246428d4695bf273e578372cf0fae3d469de`: focus future independent
  Theory review on reconstruction from original definitions and isolate each
  evaluator-only frozen claim in its own exact-Haiku adjudication call.
- `f56db3a789de9ed25e86ed492a52ae7f6e6062a6`: keep document-authoritative
  estimator handoffs to compact executable identity and return exact unsupported
  nested ABI paths to the same Theory owner.
- `24de629178cb2c8214dcefe5c553ef1015378052`: make active Markdown authority
  explicit and let model-owned exact edits safely replace a declared number of
  repeated literals without regenerating a large file.
- `5fb0711a2852568fe884cb7bdf6cc6a492ed3732`: replace the fresh metric mini-language
  with a compact preregistration artifact and ordinary Simulation Python/R source.
- `53ef1ec62fd6a00a0ba547df1886c2ce9366f9f6`: remove the runtime-expanded Theory
  review checklist so the referee's hash-bound Markdown report owns mathematics.
- `f44fcd21cee441f0a2f9bf90a29083c09157422d`: keep fresh scientific acceptance
  protocols in model-owned Markdown and reduce the terminal commit to compact,
  hash-bound metadata while retaining the frozen JSON rebinding path.

Primary references:

- [`run_turn`](https://github.com/openai/codex/blob/b592a0bfed439386fadc69327bd49eccb074cdc6/codex-rs/core/src/session/turn.rs)
- [`ToolRouter`](https://github.com/openai/codex/blob/b592a0bfed439386fadc69327bd49eccb074cdc6/codex-rs/core/src/tools/router.rs)
- [tool-call continuation](https://github.com/openai/codex/blob/b592a0bfed439386fadc69327bd49eccb074cdc6/codex-rs/core/src/stream_events_utils.rs)
- [`ToolOrchestrator`](https://github.com/openai/codex/blob/b592a0bfed439386fadc69327bd49eccb074cdc6/codex-rs/core/src/tools/orchestrator.rs)
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
- [tool-schema sanitization](https://github.com/openai/codex/blob/daa3eaf10fda93ad8949b926c059dd8cc399f76a/codex-rs/tools/src/json_schema.rs)
- [standalone function-output turn routing](https://github.com/openai/codex/commit/b9c4b9a0cfe8544c823a5dbf6ea61fc3974500ba)
- [OpenAI's agent-loop explanation](https://openai.com/index/unrolling-the-codex-agent-loop/)
- [OpenAI's App Server harness explanation](https://openai.com/index/unlocking-the-codex-harness/)
- [OpenAI's harness-engineering principles](https://openai.com/index/harness-engineering/)
- [Codex multi-agent session instructions](https://github.com/openai/codex/blob/6c59264b14b963d45d1005e7a8b1de87d4b054e2/codex-rs/core/src/session/multi_agents.rs)
- [Codex Python SDK app-server client](https://github.com/openai/codex/blob/6c59264b14b963d45d1005e7a8b1de87d4b054e2/sdk/python/src/openai_codex/client.py)

## Decision

Reuse the harness principles and protocol boundaries, not the Codex product
runtime as another scheduler or generator backend.

Codex is a Rust application centered on the OpenAI Responses protocol. AI
Statistician is a Python research runtime whose production workers use Claude
Haiku or Sonnet. Embedding `codex exec`, app-server, or the Python Codex SDK
would introduce a second conversation owner, a second tool router, and an
OpenAI-model dependency. The existing prohibition on treating Codex, Claude
Code, Cursor, or similar agents as a pure `GeneratorBackend` remains correct.

At the current recheck pin, `run_turn` keeps one `ModelClientSession` across the
turn, `ToolRouter` maps model items to generic calls, and completed tool calls set
`needs_follow_up` so their observations re-enter the same ordered history. None
of those layers defines what code, mathematics, simulation result, or Lean proof
should say. That separation is the reusable harness contract.

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

## Explicit scientific source execution

The consumed pinball-loss task exposed one remaining mismatch with Codex's
general coding loop. `submit_scientific_source` and every exact source edit
previously launched the complete Python/R check immediately. That behavior was
tolerable for tiny estimator tests but pathological for a long Simulation run:
the first timeout was followed by another expensive execution after every
partial model-authored edit.

The shared scientific workspace now separates three decisions:

1. submit or exact-edit stores complete model-authored source bytes;
2. `run_current_scientific_source` executes the exact current hash and returns
   raw output to the same session;
3. `commit_scientific_source` may occur only on a later turn after an accepted,
   hash-bound execution observation.

The model can therefore batch coherent edits and choose when evidence is worth
the execution cost. Each newly authored hash is evaluated at most once in the
same bound environment; an unchanged parent may run once when a dependency
environment genuinely changes. A terminal checkpoint preserves a last-turn
unexecuted draft and marks its execution state explicitly, so resume neither
loses work nor fabricates an observation.

This is selective harness reuse, not a Codex runtime dependency. AgentRuntime
still owns identity, sandbox policy, provenance, and evidence authority, while
the source-owning model controls content and action order. No task formula,
diagnostic parser, automatic repair, second scheduler, model escalation, or live
evaluation was added. Focused scientific-workspace tests passed `17/17`; the
complete pre-ledger suite passed `969/969`.

## Correction made from this audit

The independent Theory referee already owned a persistent Markdown report, but
its terminal tool also required PASS/FAIL/UNCERTAIN rows for runtime-expanded
claims, estimator handoffs, and downstream simulation or formal targets, each
bound to report spans. That duplicated the report, enlarged a dynamic tool schema,
encouraged shallow checklist completion, and made runtime derive scientific
judgment from model-self-reported rows.

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
4. may replay at most eight recent exact, complete tool-call/result pairs from
   the same source-owning session before appending the current authoritative
   document/source and environment observation;
5. records the exact replay count and fingerprint, treats older history as
   lineage only, and uses no model- or runtime-authored summary.

History remains linear within each workspace segment, and only complete recent
tool pairs can cross a durable checkpoint. There is no token threshold, silent
content truncation, extra model call, or content-specific compression rule.
Mathematics, code, Lean source, findings, and raw diagnostics remain external
authoritative artifacts; conversation history remains non-authoritative working
context and lineage.

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
3. Runtime validates the complete review-input fingerprint, exact source and
   theory identities, reviewer independence, immutable lineage, verdict/finding
   consistency, and document identity without changing the judgment.
4. An invalid submission returns the exact bounded validation observation to
   the same reviewer session as an error tool result.
5. A valid resubmission closes that workspace; repeated invalid submission still
   fails closed.

This is not a repair agent or full-packet regeneration callback. The same model
owns both submissions, the reviewed source never changes, Architect is not
invoked, and no empirical or proof authority is promoted. The one corrective
turn is available only after a real rejected terminal submission.

The later Hotelling draw showed that RFC 6901 evidence pointers were themselves
an unnecessary model-facing mini-language. Its isolated simulation reviewer
authored substantive findings, then failed twice because two deep paths were
absent from a large review JSON object. The current v25 contract therefore keeps
scientific locations and line descriptions in the exact Markdown report and
removes evidence pointers from the compact verdict envelope. Runtime does not
try to prove a scientific claim by checking that a JSON path exists; it binds
the complete supplied review material and exact model-authored report instead.

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

## Exact external-source workspace boundary

The fiftieth frozen task applies the same Codex harness principle to published
source replication. The model sees a compact hash-bound manifest and uses the
existing source tools; the substantive paper, repository files, environment
lock, raw execution streams, and durable Markdown report remain external state.
Neither the task payload nor each model turn recursively embeds those files.

Calibration of the unchanged PyOD v1.1.3 ABOD example exposed one generic
sandbox mismatch: Python may ask the operating system for its current working
directory before opening an inventoried file. The source runner already bound
that directory, but the read profile did not permit the metadata lookup. The
shared correction adds the exact working-directory path as one read literal.
It does not grant a directory subpath, let the model choose a command, edit the
author source, inherit secrets, or access the network. Three exact no-argument
runs then produced identical stdout and stderr hashes, and the focused source
library panel passed `13/13`.

This is deliberately smaller than importing Codex core. AI Statistician reuses
the proven shape: one owner selects tools, raw observations return to that same
session, large state stays in files, and the harness enforces authority and
permissions. AgentRuntime still owns the outer scientific graph, while hidden
post-termination evaluators remain unable to revise the product run.

The latest upstream delta from `10d5a603` to `bde9db13` contains three commits
for Guardian endpoint separation, reviewed-action security-risk recording, and
Responses endpoint tracing. Those are useful product security and telemetry
changes but do not alter this adopted model/tool/workspace lifecycle. Importing
them would couple AI Statistician to Codex transport without improving theory,
source replication, simulation, or Lean feedback.

## Source-report authority in terminal criticism

The first frozen PyOD draw validated the external-source loop and exposed the
next missing authority edge. One persistent exact-Haiku source owner used 26
model turns and 31 model-selected tools, executed the unchanged entrypoint once,
and wrote a 504-line Markdown report. The runtime loop completed in three outer
traces with no outer tool call. The hidden mechanical harness passed `12/12`, but
the report failed calibrated semantic review at `5/6`: it declared that no
source discrepancy existed while the model-visible ABOD docstring and
constructor disagree on the default `n_neighbors` value. The immutable task is
therefore `0/1`, not a harness success disguised as scientific success.

The terminal Critic had accepted because the canonical evidence view did not
include source replication. The future-task correction follows Codex's external-
state principle directly. Critic now receives the exact hash-loaded Markdown
report, bounded immutable execution observation, and every exact hash-bound
source range read by the source owner. A zero return code is explicitly only
execution evidence. Runtime verifies lineage and storage identity, while the
model judges discrepancies, contradictions, unsupported success claims, and
unresolved gaps. Report and source text are transient prompt context and are not
copied into the persistent audit.

Commit `936bd137` adds no repair agent, content patcher, source-specific rule, retry loop,
reviewer, scheduler, or model escalation. It imports no Codex core component;
the official checkout remains an audited design reference at `bde9db13`. Two
unused legacy side-audit modules were removed instead: the token-overlap holdout
runner and a deterministic adversarial-intake side path. The production package
is now 149,859 lines across 139 modules, with the central runtime at 24,970 lines.
The complete repository passes `927/927`. No model call, rerun, hidden
reevaluation, or rescore occurred after the frozen PyOD result.

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

## Atomic theory-document edits

The latest source review also compared Codex's external-state editing model with
the remaining TheoryDeveloper tool surface. Theory mathematics already lives in
Markdown/LaTeX and the same source-owning Claude session already receives exact
read, search, scratch, validation, and checkpoint observations. One avoidable
difference remained: `edit_theory_document` could change only one unique literal
per call. A mathematical revision spanning several local passages therefore spent
extra model turns or rewrote a complete long document.

Commit `ec1f6fc8` replaces that one-edit shape with one ordered model-authored batch
bound to the current document SHA-256. Runtime evaluates each unique replacement
against progressively revised bytes and mutates the document only after the whole
batch validates. A failed later replacement leaves every earlier replacement
uncommitted, and the exact rejection returns to the same model session. The old
single-edit input is removed rather than retained as a fallback.

This adopts the useful principle behind Codex `apply_patch` without importing its
runtime or patch parser. The model still chooses every span and every byte of
mathematics; the harness owns only atomicity, file identity, and observation return.
No formula, parser, repair agent, model escalation, scheduler, extra turn, or task
rule was added. Focused adjacent regressions pass `290/290`, the complete repository
passes `904/904`, and production Python remains below its fixed budget at 149,998
lines. This is future-task mechanism evidence and does not change any consumed score.

## Reviewed-source workspace continuation

The Hotelling trace also exposed one collaboration error. A simulation reviewer
could say `REVISE` and explicitly state that the current source was sufficient,
but runtime then generated a fresh simulation planning envelope before the source
owner saw the finding. That discarded useful workspace continuity and spent a
planning-model call on routine code revision.

Commit `ea011806` keeps this inside the existing single AgentRuntime. For a
hash-valid Simulation review with `current_source_edit_sufficient=true`, runtime
restores the exact parent proposal and source, gives the model-authored finding
to the same Simulation source-owner loop, requires changed source bytes before
commit, and records that the current continuation used zero planning-model calls.
Architect is not invoked. The runtime does not patch source, interpret the
finding, add a task formula, or expose the blinded confirmatory outcome.

The same commit removes generated-code-review evidence pointers from the live
model contract. Substantive review remains Markdown; the compact envelope carries
only disposition, findings, and source-sufficiency. Focused adjacent regressions
passed `124/124`, and the complete repository passed `903/903` in 69.38 seconds.
`research_agent_runtime.py` is 24,996 lines and top-level production Python is
149,928 lines. This is future-task mechanism evidence only: the consumed
Hotelling result remains `0/1`, and the aggregate remains `4/42`.

## Explicit source commit and execution-phase separation

The next disjoint Kendall tau-a draw exercised the full Simulation source-owner
loop. It exposed two lifecycle defects that belong to the harness rather than to
Kendall mathematics.

First, every authoring submission executed the complete 5,000-replicate
confirmatory workload. The source owner repeatedly spent tens of seconds learning
whether its file executed and produced the requested output shape, even though
those same outcomes could not become confirmatory evidence before explicit
commit. Second, after the model exhausted its workspace tool budget without a
valid terminal commit, runtime retained the last executed prototype and could
still call it source-valid. Independent review therefore accepted bytes that the
source owner had never committed.

Commit `a5551714` adopts the corresponding Codex turn-lifecycle principle:

1. A same-owner authoring diagnostic uses a separate seed and at most 128
   replicates. It returns raw execution and metric shape, while frozen acceptance
   outcomes are not part of the source-commit observation.
2. The model explicitly commits exact source bytes. Only then does runtime run
   those bytes once at the complete frozen confirmatory count with outcomes
   withheld from that session.
3. Any nonempty workspace terminal failure makes the last prototype ineligible
   for promotion, even when it executed and its metric paths resolved.
4. GeneratedCodeSemanticReviewer v26 names its compact disposition
   `CURRENT_SOURCE_REWRITE_SUFFICIENT` or
   `CROSS_ARTIFACT_RESOLUTION_REQUIRED`. A defect in the exact Simulation source
   is local regardless of the word "downstream", so ordinary source revision does
   not consume an Architect call.

This does not reduce confirmatory evidence, patch generated source, interpret a
metric, or add another scheduler. It separates cheap model feedback from expensive
evidence, preserves a real commit boundary, and keeps local work with its owner.
Focused regressions passed `79/79`; the final complete repository passed `905/905` in
69.66 seconds; `research_agent_runtime.py` remains below its fixed budget at
24,998 lines.

The same Kendall audit also establishes a non-adoption boundary. TheoryDeveloper,
the independent referee, and the calibrated hidden semantic judge all missed a
false shared-index covariance despite exact Markdown, model-authored scratch, raw
`0.111111...` output, and explicit contradiction-reconciliation instructions.
That is a Haiku mathematical-reasoning failure, not evidence that runtime should
gain a Kendall formula parser, arithmetic repair worker, repeated vote, or hidden
answer feedback. Production serious-theory and mathematical-review roles remain
Sonnet; exact-Haiku evaluation remains intentionally harder. The consumed score
is immutable `0/1`, and the aggregate is `4/43`.

## Current upstream boundary recheck

The official checkout was fast-forwarded to
`2764e83626efe55f64e04d153fc99a157327f3c2`. Codex's core turn loop, tool router,
parallel-safety gate, multi-agent session/mailbox implementation, app-server API,
Python SDK contract, model-provider wire API, and experimental exec-server were
read directly. None of those inspected paths changed after the prior `dc08ace`
recheck.

The boundary remains architectural rather than ideological. Codex's Python SDK is
an app-server client and the current model-provider implementation uses the OpenAI
Responses wire API. Embedding either in the canonical Claude Haiku/Sonnet research
path would add another conversation owner and scheduler or require an
Anthropic-to-Responses gateway. Codex's standalone exec-server is model-neutral but
experimental and does not supply AI Statistician's secret-free Python/R dependency,
blinded evaluator, resource, and artifact-hash policy. Selective source-level reuse
therefore remains the stronger integration.

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

## Referee document continuity

The Gaussian-KDE draw met that two-consumer threshold. Terminal Critic already
loaded persisted referee reports by exact path, SHA-256, and byte size, while a
later TheoryDeveloper revision received only compact ledger rows and could not
read the referee's current Markdown explanation. Commit `36f90f4c` extracts one
shared hash-bound UTF-8 loader and uses the existing Theory read-only artifact
tool for the report. The model sees `review_document_markdown` and a path-free
reference; runtime does not summarize the mathematics or prescribe an edit.

The official Codex delta from `2764e83` through `21c58c9` adds turn/step-bound
environment metadata, persistent reasoning settings, paginated background-task
history, tracing, Bridge-compatible history tools, and sandbox cleanup. Those
changes reinforce lifecycle identity and observability but do not alter this
selective-adoption decision. The complete AI-Statistician suite passed `907/907`;
no new tool, agent, scheduler, retry, model call, or scientific rule was added.

## Issuing-step settings recheck

The sole upstream change from `21c58c90` to `a26f1806` makes delayed approval
decisions use the settings of the step that issued the action. A command, patch,
permission request, sandbox retry, or network action can outlive its originating
step, so consulting a newer turn's approval policy or reviewer would violate
that action's authority boundary.

The reusable invariant is narrower than importing Codex: a long-lived action
must retain the exact intent, permissions, and policy snapshot under which it was
issued. AI Statistician's current specialist loops are synchronous, and their
session-contract fingerprint already binds the exact model, system prompt, tool
descriptions and schemas, strict and terminal semantics, transcript, workspace,
and hashes. Task intent is present in the bound source-owner context, and callers
do not mutate policy while a tool batch is executing.

No product change is therefore justified. If background Python/R execution,
asynchronous Lean search, or delayed public-source acquisition is added later,
its immutable action reference must also bind the issuing task-intent and safety
settings. This is a future design constraint, not a reason to add Codex's
approval subsystem, app-server, thread manager, provider transport, or scheduler.

The new Neyman-allocation draw supplies the complementary boundary. Its
persistent Theory file loop, separate referee report, exact reads, scratch
execution, sparse handoff, and task-intent lane selection all worked. The source
owner, referee, terminal Critic, and calibrated hidden judge nevertheless
false-accepted required mathematical errors. More Codex lifecycle machinery
would not repair that reasoning failure; the correct response is honest
operator invalidation and stronger future model/evaluator evidence, without a
formula rule, retry, extra vote, or repair layer.

## Referee session lineage and review breadth

The Neyman trace still exposed two shared harness defects after separating the
mathematical false acceptance from the mechanism. Its independent referee used
the entire twelve-turn workspace segment, including two initial tool-input
errors and a rejected terminal envelope, before the loop required a final
disposition. Unlike TheoryDeveloper, the referee persisted only a redacted
history inside the review packet; there was no exact contract-bound session
artifact for operator inspection or checkpoint-lineage verification.

A comparison with Beta-Binomial, Aitken GLS, and Hoeffding U-statistics ruled
out a write-count rule. A correct task could use one initial theory draft, while
a much longer revision could still retain false mathematics. Commit
`70f5d658a2e9e8e1049debc990d8d99f9102a0e3` therefore changes only the shared
harness:

1. Independent-referee work now persists the same immutable
   `ClientToolWorkspaceSessionRef` used by TheoryDeveloper and coding
   workspaces. It binds the exact model, system prompt, complete tool surface,
   transcript bytes, and review workspace.
2. A resumed referee checkpoint validates those exact session bytes and the
   unchanged tool contract before any new model call. The existing hash-bound
   report and exact prior observations remain the scientific workspace state;
   the old conversation remains lineage, not evidence.
3. The ordinary ceilings are now 24 model turns and 48 tool calls for both
   TheoryDeveloper and the independent referee. They are capacity, not a quota:
   the model may commit or report a gap earlier, and no automatic continuation
   or extra model call was added.
4. The referee prompt asks for the smallest dependency graph covering every
   explicitly requested conclusion or scope boundary that can fail
   independently. This is a model-owned review principle, not a claim checklist,
   formula library, parser, or runtime verdict.
5. Packet history now retains only turn index and tool name/status plus a
   reference to the exact session. Per-tool redaction branches and duplicated
   result excerpts were removed.

The change is line-neutral at the architecture boundary: production Python is
149,999 lines under the existing 150,000-line budget. Focused referee tests
passed `63/63`, adjacent Architect/runtime/core tests passed `175/175`, and the
complete repository passed `908/908` in 69.26 seconds. No live model call,
consumed-task rerun, hidden reevaluation, score change, proof, formula rule,
RepairAgent, scheduler, or model escalation occurred. Neyman remains the same
immutable automated 1/1 and operator-invalidated capability result.

## Recent exact history and task-bound review

The official repository was rechecked through upstream commit
`a9ed4f154a4fad64acf538d6418d3ed012aeab86`. Three current implementation details
are directly relevant:

- [`ContextManager`](https://github.com/openai/codex/blob/a9ed4f154a4fad64acf538d6418d3ed012aeab86/codex-rs/core/src/context_manager/history.rs)
  owns normalized conversation history and preserves complete tool-call/output
  relationships.
- [`run_turn`](https://github.com/openai/codex/blob/a9ed4f154a4fad64acf538d6418d3ed012aeab86/codex-rs/core/src/session/turn.rs)
  reuses one model-client session while tools execute and observations accumulate.
- [`compact`](https://github.com/openai/codex/blob/a9ed4f154a4fad64acf538d6418d3ed012aeab86/codex-rs/core/src/compact.rs)
  treats context replacement as model-owned history. AI Statistician does not
  adopt this summarization path because it would add a model call and another
  non-authoritative scientific representation.

The consumed Normal-normal run supplied the shared-failure evidence for a
narrower adoption. It logged 119 client-tool model turns, including 83 in
SimulationEvaluator across repeated short same-owner segments. Future Theory,
scientific Python/R, and Lean checkpoint windows therefore retain up to eight
recent exact complete tool rounds after validating the sealed parent session.
The hash-bound workspace and current raw environment observation remain the
authority. Historical budget counters are explicitly stale, and no summary,
repair model, automatic continuation, or Architect reroute is introduced.

Algorithm and Simulation coding sessions now have an ordinary 24-turn capacity,
matching the existing Theory/referee scale. Capacity is not a quota: the model
can commit or report a gap earlier, and the harness makes no extra call merely
because capacity remains.

The same run also showed that one global referee acceptance can coexist with a
false intermediate equation. At that stage, commit `39d42c18` introduced an
identity-only component map derived from the question, model-authored claim
index, estimator handoff, and downstream targets. Later immutable evidence
showed that this map became a model agenda and encouraged checklist-shaped false
acceptance. Commit `53ef1ec6` therefore removes the map while retaining the
independent Markdown report, exact reads, blocker findings, identity checks, and
prior-finding lineage.

Commit `39d42c18b09c34221f6b09dc6f5f49991b9540f6` implements these changes and
deletes thirteen unreferenced legacy helpers to keep the canonical production
package at 149,994 lines. The complete suite passed `911/911` in 74.02 seconds.
No live model call, consumed-task rerun, hidden reevaluation, score change,
second scheduler, RepairAgent, Opus execution, task formula, or mandatory formal
lane was added. This is selective Codex harness reuse, not embedding Codex as a
second research runtime.

## Superseded component-to-report spans

The Normal-normal, Neyman, Fisher-z, and Kendall audits shared a narrower failure:
an isolated reviewer can reconstruct useful mathematics and still return an
unlocalizable `PASS` for a contradictory candidate step. More reviewer prose,
another vote, or a runtime algebra parser would move scientific judgment into the
harness. Commit `ea2b8bad4b735ba963904a299837d560ed016442` instead applies the
same Codex-shaped artifact principle already used for source and tool output:

1. The existing isolated referee remains the sole author of one Markdown report.
2. Its task-derived ordered component rows now contain only `PASS`, `FAIL`, or
   `UNCERTAIN` plus an inclusive line span in that report. One span may support
   several components, so mathematical prose is not copied into JSON.
3. Runtime binds each dynamic component identity to the report document, line
   range, and SHA-256 of the selected bytes. Out-of-range or stale references are
   returned as a raw tool observation to the same referee session.
4. Runtime still cannot determine whether the selected mathematics is correct.
   A hash-bound `PASS` is review traceability, not theorem, empirical, hidden-gold,
   or kernel evidence.

This span design is historical and was removed by `53ef1ec6` after Task 60 showed
that runtime-expanded components could steer the referee away from contradictions
in the authoritative document. No replacement checklist or mathematical parser
was added.

No model call, agent, scheduler, retry, formula rule, equation parser, scratch
requirement, or fixed review checklist was added. Five unreferenced helpers were
removed, leaving 142 production modules, 149,999 package lines, and 24,854 lines
in `research_agent_runtime.py`. The focused referee suite passed `65/65`; the
complete repository passed `912/912` in 70.15 seconds. These are regression facts
for future tasks and do not repair or rescore any of the forty-six consumed draws.

## Current upstream recheck and failed-review probes

The official Apache-2.0 checkout was fast-forwarded and rechecked through
[`f5420174`](https://github.com/openai/codex/commit/f5420174dafba153913a3e697f89002c338dfd7e).
The central architecture remains the same: `run_turn` keeps one model-client
session while tool outputs accumulate; `ToolOrchestrator` handles infrastructure
approval and sandbox policy; tool failures remain exact model-visible
observations. No upstream change justifies embedding Codex core, app-server,
Responses transport, Guardian, or its scheduler in AI Statistician.

Two new upstream details sharpen the selective-adoption boundary:

1. [`039eb58a`](https://github.com/openai/codex/commit/039eb58a0ba6647fb8f29fdd35341f3f1b153728)
   gives an isolated Guardian reviewer only four read-only parent-history tools;
   unrelated parent tools remain unavailable. AI Statistician should preserve the
   analogous least-authority rule: a theory, code, metric, or formal reviewer may
   read exact hash-bound source artifacts and public observations needed for its
   judgment, but it should not inherit the author's writable workspace, hidden
   evaluator authority, or broad parent tool surface.
2. [`f5420174`](https://github.com/openai/codex/commit/f5420174dafba153913a3e697f89002c338dfd7e)
   propagates the originating response-item ID through direct and nested MCP calls.
   AI Statistician already binds observations to task, handoff, source, session,
   and content hashes. Preserve that direct origin lineage; do not add a parallel
   Codex item model or duplicate artifact graph.

The forty-seventh frozen research-capability draw exposed a concrete violation of
the first principle inside generated-code review. The isolated reviewer chose to
execute an exact-estimator probe. Its first probe omitted the required sandbox
entry point; its second used the wrong callable signature and never invoked the
bound estimator. Both raw failures were available, but the old terminal contract
still allowed the reviewer to submit `ACCEPT`. The hidden evaluator later rejected
the source for violating a public no-coercion clause. The consumed task remains
immutable `0/1`.

Commit `3b28df58d3ac03af48d7f855ba912725d3324aa3` applies the Codex-shaped correction
without adding scientific rules. If a future reviewer elects to probe, terminal
`ACCEPT` now requires at least one execution that succeeded and actually invoked
the exact hash-bound estimator. A malformed probe and the terminal-validation
observation return to the same reviewer session. The reviewer owns the correction
or may submit a non-accepting judgment; runtime does not infer scientific success
from metrics and does not patch source.

This gives the specialist collaboration rule in operational form:

```text
outer research graph
  -> specialist workspace with one model-owned session
       -> read exact artifact
       -> choose general tool
       -> receive raw observation
       -> revise artifact/action in the same session
       -> commit checkpoint or report honest gap
  -> isolated least-authority reviewer
       -> read exact public artifact/observation
       -> optionally falsify with a general scratch tool
       -> resolve its own failed tool action before judgment
  -> deterministic evidence boundary and optional downstream authority
```

TheoryDeveloper should continue to own persistent Markdown/LaTeX plus Python/R
scratch; Algorithm and Simulation should own source plus execution; Formalizer
should own Lean source plus current goals, diagnostics, and proof-state retrieval.
Ordinary source, simulation, and Lean failures stay inside those sessions. The
Architect handles initial intent, real cross-workspace contradictions, and stop
decisions rather than ordinary repair traffic.

The same draw also showed that the one-shot metric semantic reviewer can accept
wrong arithmetic and a vacuous check even though its prompt already requires
independent recomputation and non-vacuity. The scientifically coherent next
mechanism, if confirmed on fresh tasks, is one reusable read-only scratch loop for
review workspaces. It is not another metric checklist, formula parser, vote,
repair agent, or subsystem-specific scheduler. One consumed failure does not
authorize a large new abstraction or a hidden-result-driven rerun.

Focused generated-code review and architecture tests passed `36/36`; the complete
repository passed `914/914` in 71.31 seconds. Compile-all, JSON parsing, and diff
checks passed, and the top-level production package remains at 149,999 lines under
its unchanged architecture budget. These are future-task mechanism facts only.

## Metric review scratch and one canonical transport

Commit `1fef5179` implements the next evidence-backed adoption without encoding the
SRSWOR answer. The consumed SRSWOR draw remains immutable `0/1`; its incorrect
constants, vacuous metric, and reviewer false acceptance were not repaired, rerun,
hidden-evaluated, or rescored.

For future tasks, ArchitectMetricSemanticReviewer now uses the existing native
client-tool loop. The isolated reviewer sees the frozen pre-execution material and
may choose the shared Python/R/SymPy scientific scratch tool to reconstruct a
constant, unit conversion, uncertainty calculation, or counterexample. Raw sandbox
output returns to that exact reviewer transcript. The model then submits one compact
terminal judgment; a mechanically invalid submission returns bounded validator
observations to the same session for one corrected disposition. Runtime records
scratch request/result hashes and the transcript fingerprint, but neither scratch nor
review becomes empirical or proof authority.

The harness does not decide when scratch is scientifically necessary, supply a
formula, interpret its output, patch a metric, prescribe a finding, add a vote, or
route the failure through Architect. The reviewer owns the calculation and judgment;
runtime owns execution isolation, immutable input identity, bounded tool lifecycle,
lineage, and terminal-envelope validation.

Two obsolete alternate transports were removed at the same time:

- GeneratedCodeSemanticReviewer no longer falls back to detached one-shot packet
  generation when native client-tool turns are absent.
- TheoryDeveloper no longer has a JSON-only core-theory generation path or its
  bounded derivation schema. Initial and revised mathematical authority must be the
  existing model-owned Markdown/LaTeX workspace. Small executable ABI envelopes
  remain structured data; they are not the mathematical workspace.

This is the useful boundary from `openai/codex`: one model-owned session, a stable
least-authority tool surface, exact tool observations, and external authoritative
artifacts. Codex core, app-server, Responses transport, Guardian, thread manager, and
multi-agent scheduler remain deliberately unembedded because they would create a
second conversation owner rather than improve statistical reasoning.

The complete repository passed `915/915` in 72.99 seconds, including real local
scientific-sandbox recomputation, rejected-terminal same-session correction, native
review transport, Markdown-only TheoryDeveloper fail-closed behavior, and runtime
scratch-capability binding. Compile-all and diff checks passed. Top-level production
Python fell from 149,999 to 149,845 lines under the unchanged 150,000-line budget.
No live model call, Opus use, new agent, scheduler, formula rule, result patch,
consumed-task rerun, hidden reevaluation, or score change occurred.

## Exact tool-origin and source-owner continuation

The official upstream head inspected on 2026-08-26 was
[`f5420174`](https://github.com/openai/codex/commit/f5420174dafba153913a3e697f89002c338dfd7e),
which carries an originating Responses item ID through direct and nested MCP tool
calls. Together with the read-only Guardian surface in
[`039eb58a`](https://github.com/openai/codex/commit/039eb58a0ba6647fb8f29fdd35341f3f1b153728),
this sharpens two local rules:

1. Every environment observation must preserve which exact model tool action
   produced it and whether the target artifact was actually invoked.
2. A source revision belongs to the source-owning model workspace and receives
   exact parent source plus raw observations. It does not restart from a planning
   envelope or travel through a content-repair agent.

The variance-ratio frozen draw supplied direct evidence for both rules. Reviewer
probe source failed before invoking the exact estimator, but the failure looked
like target-code evidence. Two later AlgorithmEngineer visits were labeled source
revision while starting with no scientific source and no reviewer observation.

Commit `f6eb861a2484393f550cc29aaa3823f346f17eef` adopts the principles at the
existing boundary. Probe records now carry `originating_tool_call_id`, direct
callable identity, target invocation state, and failure origin. Algorithm review
backedges restore hash-bound source and raw findings in the same scientific-code
workspace and skip a new planning call. Runtime still owns only provenance,
execution, permissions, budget, and terminal evidence boundaries; the model owns
all source edits and scientific judgment.

This is intentionally not a Codex-core integration. Embedding Codex app-server,
Responses transport, thread management, or its scheduler would create a second
conversation owner. TheoryDeveloper continues to use persistent Markdown/LaTeX
plus scratch tools; Algorithm and Simulation use scientific source plus raw
execution; Formalizer uses Lean source, goals, diagnostics, and retrieval. Their
collaboration remains the single typed outer research graph with sparse
cross-workspace handoffs.

The final implementation reuses the existing scientific-source lineage validator
instead of adding a parallel continuation layer. The two affected files pass
`108/108`; the complete repository passes `917/917` in 70.91 seconds. Compile-all,
JSON, architecture-budget, and diff checks pass. `research_agent_runtime.py` is
24,962 lines and top-level production Python is 149,982 lines. No live model call,
task formula, source patch, extra agent, scheduler, Sonnet call, or Opus call was
introduced.

## External authoritative context instead of prompt copies

The upstream audit was refreshed through
[`10d5a603`](https://github.com/openai/codex/commit/10d5a603aecbd73a38f3a6576cce69a78f8d6f1d).
Its newest change persists Guardian risk evidence without restoring that score as
active model state. This is another instance of the relevant boundary: durable
evidence may be retained and inspected without recursively injecting all persisted
state into every subsequent model turn.

An offline replay found the same remaining violation in AI Statistician. Algorithm
and Simulation opening prompts copied complete authoritative Theory Markdown into a
nested JSON context even though the Theory workspace already owned immutable paths,
hashes, and exact text. That cost 30,577 characters in one Algorithm context and
29,321 in one Simulation context before source work began.

Commit `173cabdb4f0ccce5e494dc760d5936f305db910e` now projects those documents to a
compact manifest containing path, SHA-256, and line count. The exact verified text
stays external and is available to the same source-owning session through the
existing read-only `search_theory_documents` and `read_theory_document` tools. No
summarizer, context agent, retrieval scheduler, repair layer, or new artifact format
was added.

Measured against the immutable replay artifacts, the Algorithm opening context fell
from 30,577 to 6,421 characters, a 79.0% reduction across three documents. The
Simulation opening context fell from 29,321 to 13,282 characters, a 54.7% reduction
across two documents. These measurements are transport facts, not evidence that a
scientific task succeeded.

The generic client-tool loop also stopped appending a private budget table to every
raw tool observation, and workspace prompts no longer advertise exact turn caps.
Internal model-turn, tool-call, no-progress, permission, terminal-disposition, and
evidence bounds are unchanged. This keeps harness policy deterministic while leaving
the model-facing scientific context focused on artifacts and environment feedback.

The focused panel passed `75/75`, the broader runtime panel passed `177/177`, and the
complete repository passed `923/923` in 79.03 seconds. Compile-all, diff hygiene,
architecture-budget, and secret checks passed. Top-level production Python is
149,997 lines. No product-model call, consumed-task rerun, hidden reevaluation,
source repair, new scheduler, Sonnet call, or Opus call occurred.

## Authority projection and document-wide review

The upstream audit remains current through
[`10d5a603`](https://github.com/openai/codex/commit/10d5a603aecbd73a38f3a6576cce69a78f8d6f1d).
The first frozen task using the external-context change supplies live evidence for
the selective adoption decision. In one persistent exact-Haiku session,
TheoryDeveloper recovered from three ordinary document-tool errors using the raw
observations, AlgorithmEngineer produced source that passed the hidden algorithm
harness `8/8`, and Simulation produced source that passed hidden empirical checks
`8/8` over 12,000 exact estimator invocations. None of those corrections passed
through Architect or a content-repair agent.

The same draw also exposed the limit of a compact envelope. The authoritative
Markdown contained a named active intermediate claim that was absent from its
structured claim index. The independent referee treated the index as its effective
component map and falsely accepted a two-component Cochran decomposition that
omitted the grand-mean rank-one term. A valid compact handoff therefore cannot be
treated as a complete inventory of the mathematics in external authoritative
files.

The hidden evaluator independently exposed authority drift: downstream runtime
consumers canonically derived `document_authoritative=true` from the document
authority and structured-handoff role, while evaluator hydration copied the same
documents without projecting that derived fact. This mechanical false negative did
not change the task result because the operator-found mathematical defect already
failed the required theory dimension.

Commit `6658c7626664b0287eaa1afc3d6cb14252225599` applies the shared correction only
to future tasks. Hidden theory hydration now reuses the canonical authority helper;
TheoryDeveloper indexes every active named intermediate inference; the isolated
referee treats that index as navigation rather than the limit of review; and Critic
cannot use an upstream `ACCEPT` or index membership as mathematical evidence. The
scientific judgment remains model-owned and document-native. Runtime still parses
no equations, inserts no statistical formula, repairs no source, and adds no agent,
scheduler, retry, or model escalation.

The focused and architecture panel passes `184/184`, and the complete repository
passes `924/924` in 78.70 seconds. Top-level production Python is 149,999 lines
under the unchanged 150,000-line budget. The consumed ANOVA draw remains immutable
at `0/1`; these regression results are future-task mechanism evidence only.

## Workspace turns are not research-graph transitions

The official checkout was refreshed through
[`7625bd56`](https://github.com/openai/codex/commit/7625bd56657da7ce6d96b6d27e983e568757cdbc).
Codex `run_turn` distinguishes one user turn from the many model inference and
tool-result cycles inside it. `StepContext` freezes the exact settings, environment,
and tool router for each sampling request, while tool failures become outputs in the
same model history. Its multi-agent layer uses persistent child threads and compact
message, follow-up, status, and completion events rather than sending every tool
action through a parent planner.

The now-published `openai_codex` Python SDK exposes that same Codex core through
app-server thread and turn lifecycle calls. It is a useful optional backend boundary,
but not a production dependency for AI Statistician: it would introduce Codex core,
app-server, thread persistence, an OpenAI Responses-compatible provider, and a second
conversation owner beside the required native Claude path and existing AgentRuntime.

Commit `5fd585b8e9b6f00435a7ca796aaad651b2f5378f` instead fixes the measured local
mismatch at the existing boundary. Explicit TheoryDeveloper, Python/R, independent
theory-referee, and Lean progress checkpoints receive an exact parent-bound
same-owner marker. AgentRuntime now accounts for those workspace continuations
separately from outer research-graph work. Both remain bounded by the existing
`max_iterations` value; there is no new configuration, scheduler, retry, agent, or
content rule. Unmarked, stale, malformed, or owner-changing routes still consume the
outer budget and cannot claim workspace status.

Each trace records its budget scope, and per-question plus top-level manifests expose
the two counts. This telemetry is control-plane evidence only. It does not validate
mathematics, code, simulations, review judgments, Lean statements, or proofs.

The focused cross-workspace panel passed `173/173`; the complete repository passed
`930/930` in 78.07 seconds. Compile-all, JSON, diff, architecture-budget, model-policy,
and secret checks passed. `research_agent_runtime.py` is 24,988 lines and top-level
production Python is 149,976 lines under the unchanged ceilings. No model call,
consumed-task rerun, hidden reevaluation, rescore, Sonnet call, or Opus call occurred.

## Referee tool order belongs to the model

The prior theory-referee harness forced one blind Markdown write before any candidate
document access and then required a second changed report after inspection. Although
that chronology was hash-bound and deterministic, it was still a prescribed reasoning
ritual. It spent extra tool calls, anchored a small model to its first generic account,
and had no live evidence of reducing false acceptance of load-bearing equations.

Commit `6f588ff13cb2adf4ab01d1ec61eaecdd8842c594` removes the chronology state,
validation, prompt rule, and read gate. The isolated referee may now search, read,
derive, use source or Python/R/SymPy scratch tools, and write or edit its report in the
order it judges useful. The harness still requires at least one exact authoritative
document read before a verdict, one model-owned hash-bound Markdown report, exact
report-line support for every frozen review component, source and artifact identity,
reviewer isolation, finding consistency, and fail-closed terminal validation.

This follows the Codex division of responsibility more closely: tools expose state and
raw observations; the model owns the work sequence; runtime owns identity, execution,
permissions, and evidence boundaries. It introduces no agent, scheduler, retry, model
escalation, equation parser, task formula, or consumed-task rescore. The focused
referee suite passed `65/65`, the final focused panel passed `120/120`, and the
complete repository passed `930/930` in 78.67 seconds. Production Python decreased
by 80 lines to 149,896 lines; this remains future-task mechanism evidence only.

## Frozen environment identity and rejected verdicts

The weighted partial-regression draw exposed two remaining mismatches with the
adopted Codex boundary. TheoryDeveloper received an operator-frozen executable
contract but renamed its estimator in the compact handoff. Later, a generated-code
reviewer exhausted ordinary probe work, submitted an invalid terminal `ACCEPT`, and
had no reserved turn after that terminal verdict was rejected. Neither defect calls
for a repair agent or a task-specific content rule.

Commit `de531ad8d4173cc406593edb76606cb10be158b7` keeps authority at the
existing boundaries:

- harness-owned frozen estimator identity and request/response layout are compared
  at initial, revised, reused, and final Theory checkpoints;
- formulas, statistical meanings, Markdown/LaTeX, Python/R source, and reviewer
  judgments remain model-owned;
- absent frozen contracts add no constraint;
- one correction turn is reserved only after runtime rejects a terminal reviewer
  verdict, and its exact observation returns to the same reviewer transcript.

This selectively reuses Codex's stable tool loop and environment-authority split.
It does not import Codex core, app-server, Responses transport, thread management,
or multi-agent scheduling, and it does not add a second conversation owner. Focused
tests passed `111/111`; the complete repository passed `936/936` in 79.75 seconds.
Production Python remains within its fixed budget at 149,996 lines. The consumed
draw remains immutable `0/1`; no model call, rerun, hidden reevaluation, rescore,
Sonnet call, or Opus call occurred.

## Stable prefix identity and accepted workspace lineage

The official checkout advanced by eight commits from
[`7625bd56`](https://github.com/openai/codex/commit/7625bd56657da7ce6d96b6d27e983e568757cdbc)
to
[`f74bcd2`](https://github.com/openai/codex/commit/f74bcd281196a752521717757f39d6c7b26affae).
The relevant changes give Responses-Lite prefix items stable IDs, expose exact
resumable misalignment details through app-server, add persistent-turn clock
tools, and classify streaming rate limits. Other commits concern Guardian V2,
macOS scratch policy, layered plugin configuration, and Vim UI motions.

Stable prefix identity and resumable exact state reinforce mechanisms already
native to AI Statistician: content hashes identify external artifacts, and an
explicit continuation preserves pending work. The delta does not justify
importing Codex provider transport, app-server, Guardian, plugin management,
thread storage, or another scheduler.

The sole Clopper-Pearson Task 52 draw then exposed four local ownership failures:
an accepted Theory manifest pointed at mutable files, an old deferred top-level
manifest ID could overwrite the accepted child identity in canonical context, a
reviewer backedge could be bypassed by outer lane coverage, and estimator-bound
simulation did not normalize the complete result before JSON transport.

Commit `54e5ca52eca6192885a8a11775f7728997610ac7` applies the Codex-style boundary
without importing Codex itself:

- accepted Theory manifests resolve to content-addressed checkpoint files;
- canonical accepted context takes precedence over stale deferred fields;
- a valid reviewer `REVISE` backedge reaches its exact source owner before outer
  evidence topology continues;
- estimator-bound Python uses the existing recursive JSON-native conversion for
  the complete result.

This is state and transport correction, not scientific repair. The same model
still owns theory, Python/R/Lean source, tool order, and revisions from raw
observations. There is no Clopper-Pearson formula, task-family branch,
RepairAgent, new retry, extra model call, second scheduler, Sonnet, or Opus.

Affected tests pass `157/157`; the complete repository passes `939/939` in
83.06 seconds. Python compile, Node syntax, diff, architecture-budget,
model-policy, and secret checks pass. `research_agent_runtime.py` is 24,986 lines
and top-level production Python is 149,999 lines under unchanged limits. The
consumed task remains immutable `0/1`; these changes are future-task mechanism
evidence only.

## Unified model-authored source editing

The official checkout was incrementally rechecked from
[`f74bcd2`](https://github.com/openai/codex/commit/f74bcd281196a752521717757f39d6c7b26affae)
through
[`daa3eaf`](https://github.com/openai/codex/commit/daa3eaf10fda93ad8949b926c059dd8cc399f76a).
Only two commits are new. `ac644ed` stops preserving `minimum`, `maximum`, and
`maxLength` in Codex's reserved-tool schema representation; runtime validation,
not a model-visible schema hint, remains the enforcement authority. AI Statistician
therefore retains bounds where its direct provider supports them, but never treats
those declarations as evidence that a call was valid. `daa3eaf` concerns Guardian
scoring for required computer-use models and does not apply to the scientific
workspace topology.

The reusable Codex mechanism remains smaller than the Codex product runtime:

```text
same source-owning model -> model-selected source action
                         -> exact environment execution
                         -> raw observation in the same session
                         -> model-selected revision or commit
```

Commit `3f0ee0131d2b298bbb668e53afc132cae0ff562a` closed the mismatch present at
that point. Scientific Python/R sessions could choose a complete submission or
one exact unique text edit; each source action then immediately executed the
complete result. Commit `b567aaa68195e85cc6f799f727b415903251af46`
subsequently separated mutation from explicit execution after a long Simulation
made the atomic behavior measurably inefficient. Ambiguous, stale,
byte-identical, or invalid actions still return as ordinary tool observations to
the same model. Runtime chooses no patch and contains no Python, R, statistical,
Lean, or benchmark-specific repair rule.

The exact-edit materializer is shared by Theory documents, metric-protocol text,
scientific source, and Lean source. Each caller retains its own authority boundary:
Theory and metric batches remain atomic, Python/R must pass its sandbox and explicit
commit gate, and Lean still requires semantic review, axiom audit, and kernel
promotion. The scientific prompt no longer prescribes a separate failure-routing
sequence; the stable tool surface exposes complete submission, exact edit, unchanged
rerun when authorized, dependency handoff when authorized, and commit.

Codex core, App Server, Responses transport, thread storage, Guardian, code-mode
host, worktree manager, provider, and subagent scheduler remain unembedded. The sole
outer scheduler is still `AgentRuntime`; TheoryDeveloper, AlgorithmEngineer,
SimulationEngineer, and Formalizer collaborate through hash-bound artifacts and
sparse typed handoffs rather than nested Codex threads.

Focused cross-workspace tests pass `113/113`; the complete repository passes
`940/940` in 80.49 seconds. Architecture and model-policy tests pass `39/39`,
compile-all and diff hygiene pass, and top-level production Python decreases from
149,999 to 149,990 lines. No model call, consumed-task rerun, hidden reevaluation,
rescore, new agent, retry, scheduler, Sonnet call, or Opus call occurred. This is
future-task harness evidence and grants no scientific or proof capability credit.

## Complete sampling-contract lineage

The current official checkout and Python SDK confirm that Codex core, not the SDK
wrapper, owns threads, turns, step settings, tool routing, persistence, compaction,
and child-agent mailboxes. The SDK starts or connects to App Server; it is not a
provider-neutral inner-loop package. Codex custom providers still speak Codex's
supported wire protocols, while AI Statistician requires Anthropic's native Claude
tool transport. Embedding the SDK would therefore add a second conversation owner
or require a translation gateway without removing `AgentRuntime`.

One narrower Codex invariant did reveal a local omission. A persisted AI
Statistician workspace transcript was bound to its model, system prompt, and exact
tool surface, but not to all sampling settings. The shared session-contract
fingerprint now also binds `max_tokens`, temperature, tool choice, parallel-tool
policy, and prompt-caching policy. A Theory, Python/R, reviewer, or Lean checkpoint
therefore cannot resume under changed sampling semantics while claiming the same
session contract.

This is a shared lifecycle correction only. It adds no agent, scheduler, retry,
content rule, statistical formula, Lean grammar rule, model escalation, or Codex
runtime dependency. Specialist collaboration remains one persistent model-owned
session per workspace plus sparse hash-bound handoffs through the sole outer
`AgentRuntime`.

## Critic evidence is now a model-owned document session

The sole rdrobust Senate Task 54 draw exposed a different failure from source
execution. The immutable entrypoint ran correctly, the source owner used one
persistent exact-Haiku tool session, and both runtime Critic and the calibrated
hidden semantic judge accepted its 749-line report. Operator inspection found an
incorrect robust point estimate, internal caveat contradictions, an ATE/local-RD
mislabel, and unsupported claims about covariate balance, causal validity, random
seeds, plotting, precision, clustering, and warning semantics. The runtime Critic
had received the report, raw output, and nine exact source ranges, but all of that
material arrived in one roughly 36k-token generation request.

Adding another reviewer, phrase detector, RD rule, report repair path, or packet
taxonomy would repeat the architecture error this project is removing. The Codex
harness lesson is narrower: large work lives behind a stable file/tool surface;
the model selects reads and searches, exact observations return to the same
transcript, and a terminal action commits the result.

The existing Critic now follows that pattern:

```text
compact canonical evidence identities + exact document catalog
  -> same Critic model chooses read_theory_document/search_theory_documents
  -> exact hash-bound line observations return to that session
  -> same model calls submit_critic_evaluation
  -> runtime validates schema, task-intent requirements, identity, and authority
```

Long strings are externalized from only the opening model context, never truncated
or discarded. Their path, original JSON location, hash, character count, and line
count remain visible, while the existing generic Theory document tools expose the
complete text. A reviewer with externalized evidence must inspect at least one exact
document before submitting, but the model owns which documents, queries, ranges,
order, and scientific judgment. Invalid terminal packets return as ordinary tool
observations in the same reviewer session. There is no live one-shot fallback, full
packet repair agent, second scheduler, or model escalation.

This change reuses `run_bounded_client_tool_loop` and the existing document tools;
`AgentRuntime` remains the only outer scheduler. It also removes the 394-line
`primitive_source_coverage_audit.py`, a June side audit with no import, test, CLI
entry, or canonical runtime consumer. Retrieval hits continue to be exposed through
the live Formalizer/RAG tools and remain non-proof evidence until active-project
Lean verification.

The mechanism applies only to future tasks. Task 54 is consumed and immutable: no
report edit, rerun, resume, hidden reevaluation, rescore, or model call is authorized.

## Document tools are not a substitute for scientific judgment

The disjoint Statsmodels ADF/KPSS Task 55 tested the new Critic document session
without changing it. The source owner used 22 exact-Haiku turns and 28 generic
tools to inspect the frozen source, run it once, write one 436-line Markdown
report, and commit a hash-bound checkpoint. The Critic then used 15 turns and 15
tools, made 14 exact accesses, and inspected all 12 externalized evidence
documents before returning `SUPPORTED`.

The transport mechanism therefore worked. Nevertheless, the report attributed
the sole KPSS warning to the wrong invocation and reversed its inequality,
converted failures to reject into substantive conclusions, defended a trend-
stationarity claim not tested by `regression="c"`, conflated differencing with
detrending, misdefined strict stationarity, and omitted required article and
snapshot identity. The Critic repeated several of those errors. A separately
calibrated exact-Haiku hidden judge also marked all ten explicit claims satisfied.

This result narrows the Codex lesson. Stable files, model-selected tools, raw
same-session observations, and terminal actions are necessary for long-context
review, but they do not manufacture scientific reasoning capacity. Adding
another read tool, synonymous prompt checklist, reviewer vote, stationarity
parser, or report-repair layer would not address the measured failure.

Commit `e5cccbb2` changes only future production model allocation: scientific
Critic work now defaults to Sonnet, matching the Theory, scientific-code,
simulation, and semantic-review tiers. Frozen `research_eval` and
`capability_eval` runs still pin every enabled role to exact
`claude-haiku-4-5-20251001`; Opus remains prohibited. The prompt, tool surface,
schema, agent graph, number of review stages, and evidence authority are
unchanged. The final focused panel passed `186/186`; the complete repository
passed `945/945` in 82.62 seconds; compile-all, JSON, diff, model-policy,
secret, and architecture-budget checks passed. Production Python remains below
the unchanged limit at 149,868 lines, with `research_agent_runtime.py` still
24,986 lines.

The official Codex checkout was incrementally rechecked from `daa3eaf` through
`f374188`. The relevant new `b9c4b9a` change allows named standalone
function-call outputs to start or steer a turn while preserving them as passive
conversation items. AI Statistician already returns exact client-tool
observations to the same source-owning session. The remaining upstream changes
concern permission context, MCP provenance, browser cleanup, retained-image
budgeting, Guardian, proxy hardening, and platform telemetry. None supplies a
provider-neutral Claude research harness or justifies embedding Codex core, App
Server, Responses transport, thread storage, or another scheduler.

Task 55 remains immutable automated `1/1` and trustworthy `0/1`. It cannot be
rerun, resumed, repaired, hidden-evaluated again, rescored, or resampled; the
model-tier correction is future-task mechanism evidence only.

## Formalizer Theory context is external state

The canonical direct-Lean path was re-audited before changing it. It already
starts one persistent Formalizer model/tool session and sends local Lean,
declaration-search, proof-state, compilation, and source-edit observations back
to that same model. The remaining mismatch was narrower: accepted
Markdown/LaTeX Theory documents were copied in full into the opening Lean prompt,
even though Algorithm and Simulation already accessed those documents through
the shared scoped document tools.

One accepted live Theory artifact measured 16,085 document bytes and 17,234
serialized prompt characters. Commit `3408012f` replaces that duplicate body in
the canonical Lean opening request with a compact path, SHA-256, line-count, and
byte-count catalog. The measured opening prompt is now 7,404 characters and does
not contain the document body. `read_theory_document` and
`search_theory_documents` return exact hash-verified ranges to the same
Formalizer session when the model asks for them. A checkpoint freezes the whole
document-set hash, so changed Theory context is rejected before another model
call.

Theory, scientific Python/R, and Lean now share one content-agnostic document
externalizer and tool executor. Exact document text remains available in the
active model transcript, but persisted telemetry stores only hashes and range
references. Theory reads are explicitly non-proof observations and cannot
satisfy an active Lean/compiler/environment evidence requirement. Formalizer
semantic review, axiom audit, exact target identity, and kernel promotion are
unchanged.

This adopts Codex's external-state and same-turn tool-observation principles,
not its product runtime. No Codex core, App Server, Responses transport, thread
store, provider, subagent scheduler, second outer loop, RepairAgent, task rule,
Lean grammar rule, retry, model call, or model-tier change was added. The
official checkout was also rechecked through `b68acc4`; the adjacent
`e56e492` standalone tool-output change further supports durable named
environment observations, while the URI policy, plugin access, and Guardian
changes do not alter this scientific workspace topology.

The focused mechanism panel passed `105/105`; the complete repository passed
`947/947` in 78.24 seconds. Production Python is 149,972 lines under the
unchanged 150,000-line architecture limit, with `research_agent_runtime.py`
unchanged at 24,986 lines. No consumed task was rerun, resumed, repaired,
reevaluated, rescored, or granted capability credit. Exact statistical theorem
closure therefore remains `0/2`.

## Lean scratch is environment feedback, not candidate source

The immutable Statlib uniform-consistency formal task exposed one generic tool
gap. Across 24 model-authored candidate checks and 10 RAG calls, the Formalizer
once placed `#print` inside a theorem body because it had no independent Lean
scratch action. That consumed task remains untouched at `0/1`; its admitted
elaboration and post-run diagnostics are not proof evidence.

Commit `8f5d6295` adds one `run_lean_scratch` action to the existing Formalizer
model/tool loop. The model supplies a complete self-contained Lean snippet and
receives the raw result from the already pinned local checker in the same
session. The active candidate bytes, declaration identity, source-update count,
and candidate-check count remain unchanged; scratch checks have a separate
counter and compact observations also reach the independent semantic reviewer.

This adopts the environment-feedback pattern of `lean-lsp-mcp`'s
`lean_run_code` and EmpericalProcessLEAN's `symbolic_check`, but does not call or
embed either runtime. It reuses AI Statistician's existing checker and adds no
provider, MCP server, agent, scheduler, retry, Lean grammar, tactic, proof
template, statistical rule, or model-tier change. The model remains responsible
for every import, query, example, source revision, and stopping decision.

A successful scratch check is explicitly non-proof. Only the exact target
candidate, independent statement-semantic review, axiom audit, and kernel gate
can promote a theorem. The complete repository passes `948/948` in 78.59
seconds; production Python is 149,998 lines and `research_agent_runtime.py`
remains 24,986 lines. No model was called and no consumed task was rerun,
resumed, repaired, reevaluated, rescored, or credited. Trustworthy capability
therefore remains `4/55` and exact statistical theorem closure remains `0/2`.

## Semantic authority follows task intent

The official OpenAI Codex checkout was rechecked at
`b68acc4d4b56fdfa1d5b6a2c36102c66876e0c46`. Its
[`run_turn`](https://github.com/openai/codex/blob/b68acc4d4b56fdfa1d5b6a2c36102c66876e0c46/codex-rs/core/src/session/turn.rs),
[`ContextManager`](https://github.com/openai/codex/blob/b68acc4d4b56fdfa1d5b6a2c36102c66876e0c46/codex-rs/core/src/context_manager/history.rs),
[`ToolRouter`](https://github.com/openai/codex/blob/b68acc4d4b56fdfa1d5b6a2c36102c66876e0c46/codex-rs/core/src/tools/router.rs),
and tool orchestrator keep the inner loop simple: one conversation owner chooses
tools, exact tool outputs re-enter ordered history, tool declaration/routing is
separate from execution, and policy is enforced at the environment boundary.
Multi-agent support uses sparse child-session messages and shared limits rather
than routing ordinary tool failures through a planning model.

The fresh affine-variance formal task validates that shape. One persistent
exact-Haiku Formalizer session selected 19 Lean tools and produced an exact,
locally compiling, identity-verified, axiom-clean theorem candidate. The task
still failed `0/1` because the cross-workspace reviewer contract required a
Theory packet even though frozen task intent marked Theory not applicable. The
review model was never called and no kernel promotion occurred.

Commit `e4d97ee6` corrects only that shared boundary. Independent semantic review
now binds either to a hash-bound Theory derivation or, for a strictly formal-only
task, to the exact operator-frozen question and Lean target contract. A missing
Theory artifact still fails closed for every task that requires theory. The
runtime does not infer mathematics, weaken a statement, patch Lean, or select a
proof.

This is also the collaboration rule for the broader system:

- Theory, Python/R, Simulation, and Lean each keep one persistent source owner
  with direct raw environment feedback.
- Independent reviewers receive immutable artifact references plus the exact
  semantic authority selected by frozen task intent.
- Architect handles initial intent, real cross-workspace conflicts, and stopping;
  it does not relay routine compiler, simulation, or proof feedback.
- Artifacts are content-addressed external state; handoffs are compact references,
  not recursively copied source or conversation payloads.

Codex itself is not embedded. Its current model-provider transport supports the
OpenAI Responses wire API, not the native Anthropic protocol used by the
canonical runtime. Importing Codex core, App Server, thread storage, provider,
SDK, or scheduler would create a second conversation owner without improving the
Claude research loop. Apache-2.0 source remains useful as a design reference and
as a possible future pinned sandbox backend after independent isolation
calibration.

The complete repository passed `951/951` after the correction. Production Python
fell to 149,830 lines because one unreferenced deterministic legacy audit module
was deleted; `research_agent_runtime.py` remains 24,986 lines. The consumed task
cannot be rerun, resumed, repaired, reevaluated, rescored, or credited, so
trustworthy full-task capability remains `4/56` and exact development theorem
closure remains `0/2`.

## Theory and ABI share one source owner

The document-native Theory workspace already asked one persistent model session
to author Markdown/LaTeX mathematics and the compact executable estimator ABI,
returning validator observations directly to that same session. A legacy branch
nevertheless remained after workspace completion: if a returned packet was
invalid, it could open a separate structured-output model call to author the ABI,
save a `TheoryDeveloperStageRecoveryCheckpoint`, and teach AgentRuntime to resume
that content phase. A tests-only `build_theory_developer_prompt()` also still
described the retired JSON-core-then-ABI protocol.

Commit `efe3017b` removes that duplicate conversation owner and its entire
supporting surface:

- no post-commit ABI generator request or full-packet JSON regeneration;
- no interface-stage schema, prompt, parser, recovery checkpoint, or runtime
  recovery route;
- no `max_validation_retries` Theory setting or CLI flag;
- no separate parent-interface binding packet copied into revision context;
- no legacy public prompt that contradicts the real Markdown/LaTeX workspace.

The canonical workspace commit validator still enforces generic cross-agent ABI
identity: every new ABI contains only executable fields, its response fields
match the model-declared outputs, its semantic references resolve, and any
frozen operator ABI remains exact. Those observations return inside the active
Theory session before checkpoint. Historical packet readers remain compatible;
the runtime does not rewrite old mathematical metadata or infer statistical
content.

This is selective Codex adoption: one ordered model/tool/observation history,
external authoritative files, and policy at the environment boundary. It does
not embed Codex core, App Server, Responses transport, provider code, thread
storage, or scheduler. The focused cross-workspace panel passed `198/198`; the
complete repository passed `951/951` in 83.21 seconds. Production Python is
148,696 lines, `research_architect.py` is 4,043 lines, and
`research_agent_runtime.py` is 24,970 lines. No model was called and no consumed
task was rerun, resumed, repaired, reevaluated, rescored, or granted capability
credit. Trustworthy capability therefore remains `4/56`, and exact development
theorem closure remains `0/2`.

## Progress checkpoints preserve environment state

TheoryDeveloper already persisted exact Markdown/LaTeX documents, compact
handoffs, and its client-tool transcript. One important Codex-style invariant was
still missing: after a model explicitly requested a progress checkpoint, the next
context window restored the files and recent transcript rounds but initialized
tool state from zero. Prior scratch refs, source reads, source-discovery refs,
source-replication manifests, and model write provenance disappeared from the
eventual evidence packet. A configured one-shot scratch or immutable source run
could therefore become available again merely because context changed.

Commit `e3255046` makes a Theory progress checkpoint the authoritative cumulative
environment state for the same source owner. Continuation now verifies workspace,
question, authoring, and operation identity; restores exact prior counters and
reference rows; preserves their order; rejects inconsistent scratch or source-run
counts; and carries the complete cumulative lineage into later checkpoints and
final evidence. The model-visible progress artifact exposes a compact catalog of
prior execution status and hashes, while mathematical interpretation remains in
model-authored documents and recent exact observations.

This adds no new tool, agent, reviewer, repair route, scheduler, provider, model
call, mathematical parser, statistical formula, Lean rule, or automatic research
action. The same model still decides whether to read, derive, search, execute,
revise, checkpoint, commit, or report a gap. Runtime only prevents a new context
window from pretending that already-observed environment state never happened.

Theory and ResearchArchitect regressions passed `91/91`; the complete repository
passed `952/952` in 78.16 seconds. Production Python is 148,890 lines,
`theory_workspace.py` is 3,830 lines, `research_architect.py` is 4,125 lines, and
`research_agent_runtime.py` remains 24,970 lines. Historical progress artifacts
with absent later fields were read successfully under empty-state defaults. No
model was called and no consumed task was rerun, resumed, repaired, reevaluated,
rescored, or granted capability credit. Trustworthy capability remains `4/56`,
and exact development theorem closure remains `0/2`.

## Scientific judgment needs focused model work

The disjoint Nadaraya-Watson Theory draw validated the Codex-style mechanics but
not the mathematics. One persistent exact-Haiku Theory session authored and
revised Markdown, ordinary tool failures returned directly to that session, two
isolated referee passes inspected hash-bound files, and the final Critic used a
separate document session. No repair worker or second scheduler participated.

The final manuscript nevertheless omitted the transformed measure in every
unscaled kernel integral. It claimed variance of order `1/n` while asserting a
`sqrt(nh)` CLT. The referee, Critic, and pre-frozen broad semantic judge all
accepted the contradiction. This is not a tool-routing or artifact-transport
failure. It is a model-focus failure: each reviewer inherited the candidate's
already-transformed expression and then verified downstream algebra.

Commit `08242464` keeps the Codex inner-loop boundary and changes one scientific
judgment principle for future tasks:

1. A Theory referee reconstructs load-bearing substitutions and asymptotic
   normalizations from original definitions, including transformed measure,
   domain, constants, variance order, and limit scale.
2. Evaluator-only semantic adjudication gives each frozen claim an isolated
   exact-Haiku candidate call. Calibration remains separate, the whole candidate
   remains visible for contradiction search, and runtime combines only the
   model-authored claim dispositions.

No task formula, symbolic parser, deterministic mathematical verdict, output
repair, retry, scheduler, model escalation, Sonnet call, or Opus call was added.
The consumed task remains immutable automated `1/1` and trustworthy `0/1`.

The official Codex checkout was incrementally rechecked from `b68acc4` through
`5af6979`. Invocation-lifetime extension capabilities strengthen turn-scoped
authority; gRPC trace propagation preserves one execution lineage; Guardian
turn/tool analytics remain content-free lifecycle telemetry; skill path aliases
reduce repeated prompt payload. These are useful confirmations of existing
boundaries, not missing scientific agents. AI Statistician should continue to
reuse Codex's simple model/tool/observation loop, external artifacts, scoped
capabilities, and trace identity without embedding Codex core, App Server,
Responses transport, thread storage, Guardian, or another scheduler.

The focused future-task mechanism panel passed `142/142`; the complete
repository passed `953/953` in 79.47 seconds. Task 57 was not rerun, resumed,
repaired, hidden-evaluated again, rescored, or resampled. Trustworthy capability
is `4/57`, and exact development theorem closure remains `0/2`.

## Compact Theory ABI and encrypted-argument delta

The weighted-isotonic draw exercised the same Codex-shaped source-owner loop for
34 exact-Haiku turns. Its Markdown authority, public-source tools, scratch
execution, and direct validator observations all worked. The remaining transport
friction was a contradictory handoff schema: document-authoritative Theory still
advertised rich estimator metadata, while the cross-agent executable ABI accepted
only compact request and response bindings. A generic rejection omitted the exact
nested paths, so the model repeatedly revised the wrong layer.

Commit `f56db3a7` applies the minimal harness correction for future tasks. The
document path now returns only estimator identity and compact executable ABI; all
formulae, algorithms, assumptions, rates, and proofs stay in Markdown/LaTeX.
Unsupported ABI metadata is reported with exact JSON paths to the same source
owner. Runtime does not project, repair, or infer the desired payload. The legacy
structured-JSON path remains compatible.

The official Codex checkout was incrementally rechecked from `5af6979` through
[`57e2edc6`](https://github.com/openai/codex/commit/57e2edc6e97474448f1fb634224471448bc09d40).
That one-commit delta marks history/notes search queries and note text as encrypted
tool arguments and sends `x-openai-encrypted-tool-arguments: true` only on the
matching backend routes, with schema and route tests. It sharpens a transport
principle: sensitive arguments should be declared and protected at the provider
boundary, while unrelated tool calls retain ordinary transport.

AI Statistician cannot copy that private Responses/backend header into its Claude
and local-workspace providers. The applicable rule is to keep credentials and
secret values out of model-visible tool payloads and persisted telemetry, expose
only necessary hash-bound metadata, and implement any future encryption in the
owning provider adapter. This delta does not add scientific judgment, collaboration
semantics, or a reason to embed Codex core, App Server, Responses transport,
history/notes storage, or another scheduler.

The future-task Theory, ABI, document-consumer, AgentRuntime, gold-evaluation, and
scientific-progress mechanism panel passed `275/275` before immutable accounting
updates. The final focused panel passed `331/331`; the complete repository passed
`955/955` in 83.05 seconds. Compile-all, JSON, diff, model-policy, and secret
hygiene passed. Task 58 remains `0/1`; it was not rerun, resumed, repaired,
hidden-evaluated, rescored, or resampled. Trustworthy capability remains `4/58`,
and exact development theorem closure remains `0/2`.

## Terminal rejection returns to the source owner

The orthogonal-Lasso draw exposed one remaining client-loop mismatch. Its metric
author stayed in one model/tool history and received three raw validator
observations. The third submission was the loop's forced terminal commit. When
that commit was rejected, the state machine permitted only another terminal
submission, so the same model could no longer inspect the authority catalog, edit
its file, and recommit. AgentRuntime blocked even though the source owner and
ordinary environment feedback were still available.

The official Codex checkout was rechecked at
[`57e2edc6`](https://github.com/openai/codex/commit/57e2edc6e97474448f1fb634224471448bc09d40).
The reusable principle is unchanged: one scoped model owns its edits; tool output
returns to that model's ordered history; capabilities are invocation-scoped; and
external files carry substantive state. Codex core, App Server, Responses
transport, thread storage, Guardian, and its scheduler remain outside AI
Statistician because importing them would create a second conversation owner and
outer scheduler without improving the native Claude scientific loop.

Commit `7b07d9e7` makes terminal validation failure an observation for the same
source owner. Under a separate bounded recovery-action budget, that model may
inspect or read, edit, and recommit. A successful commit still terminates; repeated
rejection, exhausted recovery actions, and no progress still fail closed. The
regression executes the exact sequence
`forced final commit rejected -> check/read -> edit -> final commit`.

This is harness control, not content repair. It adds no Lasso rule, semantic path,
mathematical parser, generated-output patch, RepairAgent, Architect route, retry
scheduler, provider, or model escalation. The focused client-loop suite passed
`24/24`; the cross-workspace client-tool, Lean, and ladder panel passed `329/329`;
and the complete repository passed `958/958` in 78.30 seconds. Model-policy and
ladder tests passed `89/89`; compile-all, JSON, diff, architecture line-budget,
and changed-file secret hygiene passed. Task 59 remains `0/1`; it was not rerun,
resumed, repaired, hidden-evaluated again, rescored, or resampled. Trustworthy
capability remains `4/59`, and exact development theorem closure remains `0/2`.

## Reviewer-owned probe failures stay local

The immutable Task 59 trace exposed a smaller Codex-lifecycle error after the
source-owner correction. The first generated-code reviewer wrote three probes
that failed before invoking the exact estimator. Its Markdown review explicitly
said the target source appeared correct and the failures belonged to its own
diagnostic environment. The old runtime nevertheless prohibited `ACCEPT` after
any unsuccessful optional probe. On validation retry, the same model converted
its own tool failure into a false `CROSS_ARTIFACT_RESOLUTION_REQUIRED` finding,
and AgentRuntime spent another Architect and Algorithm route on correct source.

Commit `6fda37bbc9ce8b9f3a6a55574047d8f995de3626` removes that harness-induced
distortion. A reviewer-authored probe failure is returned as an error observation
in the same ordered model/tool history. Its exact record still states whether the
target was invoked and whether the failure can be source evidence. An optional
failed probe no longer deterministically forbids a source-grounded `ACCEPT`; the
reviewer may repair and rerun its probe when execution is needed or ignore the
invalid action and judge immutable source independently.

This is the narrow Codex function-call principle: the action owner receives raw
environment failure and chooses the next action. It does not add a RepairAgent,
probe-repair workflow, finding taxonomy, packet field, Architect route, retry,
scheduler, statistical rule, ABI special case, provider, or model escalation.
Codex core, App Server, Responses transport, thread storage, Guardian, and its
outer scheduler remain intentionally excluded.

The generated-code reviewer, shared client-tool loop, and AgentRuntime panel
passed `135/135`; the complete repository passed `958/958` in 78.65 seconds.
Compile-all, JSON, diff, and changed-file secret hygiene passed. No model was
called and no consumed task was rerun, resumed, repaired, hidden-evaluated again,
rescored, or resampled. Task 59 remains `0/1`, trustworthy capability remains
`4/59`, and exact development theorem closure remains `0/2`.

## Active-document authority and repeated exact edits

The disjoint uniform-spacings draw separates the inner-loop result from the
scientific-judgment result. AlgorithmEngineer submitted several complete source
versions; the isolated reviewer wrote two invalid optional probes, saw their raw
failures in its own history, corrected the probe, executed it successfully, and
accepted exact source that later passed all `11/11` hidden ABI checks and `9/9`
hidden empirical checks. No Architect route or repair worker was needed. This is
the Codex model/tool/observation principle working as intended.

TheoryDeveloper and its isolated referee failed differently. The authoritative
Markdown contained invalid spacing indexes, contradictory forward and inverse
maps, incompatible simplex dimensions and reference measures, and many false
factorial calculations before a correct final formula. Both prompts already said
that a correct final statement does not cancel false intermediate steps, yet the
referee treated narrative self-correction as if it changed document authority.

Commit `24de6291` defines that authority without parsing mathematics: every
unmarked paragraph and equation remains active; narrative chronology cannot
revoke it; rejected exploration must be clearly delimited and unused by active
claims. The runtime still makes no content judgment.

The same draw exposed a file-edit mismatch. The metric owner received exact
errors for sixteen quoted numeric bounds, then its natural local replacement was
rejected because each literal appeared eight times. The shared exact editor now
accepts an optional positive occurrence count, verifies that count, refuses
overlapping matches, and performs one atomic model-authored replacement. The
prompt schema also shows a numeric value as a JSON number rather than a
descriptive string.

This is not a claim that the metric protocol is now well-sized. Its 22,359-character
prompt projection elicited a 15,076-byte eight-row JSON document for a simple
moment check. The architectural direction remains to move toward a compact
model-owned evaluator or envelope in the Simulation workspace, not to add more
repair agents, condition fields, or schedulers.

The focused panel passed `168/168`; the complete repository passed `960/960` in
78.45 seconds. Compile-all, JSON, diff, and changed-file secret hygiene passed.
Task 60 remains immutable `0/1`; trustworthy capability is `4/60`, and exact
development theorem closure remains `0/2`.

## Compact preregistration, ordinary Simulation source

Task 60 also demonstrated where a coding-agent harness should stop. A simple
confirmatory check was projected through a 22,359-character prompt into a
15,076-character, eight-row condition document. The model received exact validator
errors, but the size and repetition of the runtime-designed language dominated its
work. More repair actions would have preserved the wrong abstraction.

Commit `5fb0711a` removes that fresh authoring language. The pre-outcome model now
writes one four-field acceptance protocol capable of expressing arbitrary formulas,
scenarios, and joint decisions. SimulationEngineer implements the frozen protocol in
its existing Python/R coding workspace, reads raw execution failures in the same model
history, and returns `acceptance_passed` with raw measurements and per-check
diagnostics. Independent protocol review occurs before outcomes; independent source
review checks the exact implementation. AgentRuntime owns only theory identity,
hashes, blinding, lineage, and the stable boolean path. A model-supplied alternate
metric binding fails closed.

This applies Codex's scoped model/tool/observation loop without importing Codex core,
App Server, Responses transport, thread storage, Guardian, or another scheduler. The
obsolete fresh numeric-row schema and its tests were deleted; frozen legacy packets
retain their separate reconstruction path. No model was called and no consumed task
was rerun, resumed, repaired, hidden-evaluated, rescored, or resampled. The complete
repository passed `959/959` in 78.40 seconds. Task 60 remains `0/1`, trustworthy
capability remains `4/60`, and exact development theorem closure remains `0/2`.

## Markdown protocol authority and Task 61

Task 61 supplied a disjoint live check of the adopted inner-loop design. One
exact-Haiku TheoryDeveloper maintained Markdown/LaTeX across 18 model/tool turns;
AlgorithmEngineer iterated directly on raw Python execution; and an isolated code
reviewer kept invalid probes in its own session. No repair worker or routine
Architect error route was needed. The task still finished `0/1`: Theory, its
referee, and the hidden semantic judge false-accepted active mathematical errors;
the code reviewer false-accepted explicit input-boundary and exact-comparison
defects; and runtime blocked before Simulation.

The metric failure was a harness defect rather than a reason for more retries. A
long Markdown-like scientific protocol had to be escaped inside
`metric_protocol.json`; malformed escaping and ambiguous exact replacements then
consumed the ordinary action budget. Commit `f44fcd21` moves fresh substantive
protocol content into authoritative `metric_protocol.md`. The same source owner
reads and edits those exact bytes, while its terminal call carries only the
document SHA-256, evaluator identity, required replicate count, and short
rationale. Runtime binds the exact Markdown into the existing acceptance
transport. Frozen protocol rebinding remains JSON because it has a different,
already-sealed authority contract.

This is selective Codex reuse: external files own substantive state; a stable
generic tool surface returns raw observations to the same model history; and the
harness validates identity, hashes, execution, blinding, and authority. Codex
core, App Server, Responses transport, thread storage, and its scheduler remain
excluded because they would create a second conversation owner without improving
Claude's scientific judgment. No permutation rule, mathematical parser, source
patch, RepairAgent, extra model call, retry, route, provider, or model escalation
was added. Task 61 remains immutable `0/1`; trustworthy capability is `4/61`, and
exact development theorem closure remains `0/2`. The exact-Haiku/model-policy,
metric workspace, reviewer, sandbox, backend, and ladder panel passed `215/215`;
the complete repository passed `961/961` in 79.71 seconds. No live model call or
consumed-task execution occurred during this regression validation.

## Estimator diagnostics are not confirmation

The immutable Task 61 source exposed a separate evidence-ownership error. Its
Algorithm artifact combined ordinary estimator unit checks with a section labeled
as confirmatory assessment, including model-authored DGPs, thresholds, and outcome
interpretation. The code-owner loop itself behaved correctly, but the artifact
surface invited one model to author the estimator and its purported independent
confirmation in the same workspace.

Commit `5d512560` keeps the existing direct Algorithm model/tool/observation loop
and narrows only its authority. `run_sandbox` remains available for model-authored
unit, boundary, and metamorphic diagnostics of `run_estimator`; it is explicitly
developer-only. Algorithm execution artifacts now persist
`execution_phase=estimator_developer_diagnostic` and
`empirical_evidence_status=ALGORITHM_DEVELOPER_DIAGNOSTIC_NOT_CONFIRMATORY_EVIDENCE`.
Only SimulationEngineer's separately preregistered, blinded source and execution
can create confirmatory empirical evidence.

This is an evidence boundary, not a statistical rule. Runtime does not inspect
test content, recognize a DGP, rewrite source, prescribe cases, or decide whether
an estimator is correct. The source-owning model still sees raw execution and may
revise directly. No tool, agent, repair path, Architect route, retry, provider,
model escalation, or scheduler was added.

The upstream Codex checkout was also rechecked from `b592a0bf` through
[`89650c66`](https://github.com/openai/codex/commit/89650c66f2f3ff0d028d3f5d6d0b187b2ed49be5).
The two-commit delta adds per-response usage metadata and synchronous review for
sensitive MCP actions. It does not alter the core same-session model/tool loop.
Both changes reinforce existing local boundaries: telemetry is not scientific
authority, and authority-sensitive actions need an explicit owning gate. They do
not justify embedding Codex core, App Server, Responses transport, Guardian, or a
second scheduler in the Claude-first runtime.

The final focused assertions passed `3/3`; the adjacent scientific workspace,
sandbox, reviewer, research runtime, evaluation, and model-policy panel passed
`195/195`; and the complete repository passed `961/961`. No model was called and
Task 61 was not rerun, resumed, repaired, hidden-evaluated again, rescored, or
resampled. Trustworthy capability remains `4/61`, and exact development theorem
closure remains `0/2`.

## Persistent reviewer drafts and Task 62

Task 62 supplied another disjoint live check. One exact-Haiku TheoryDeveloper
maintained hash-bound Markdown/LaTeX and used direct scratch feedback. One
AlgorithmEngineer maintained executable Python, and its isolated reviewer repaired
its own failed probes in the same model/tool history before invoking the exact
target. Hidden mechanics passed theory `7/7`, algorithm `12/12`, and evaluator-only
empirical checks `11/11`. Runtime nevertheless stopped before Simulation, and the
task remains `0/1`.

The terminal failure identified a harness mismatch. The metric reviewer first
submitted a valid requirement judgment without the complete portfolio. Later
correction calls supplied the missing portfolio fields, but each call replaced the
whole object and erased the earlier requirement. This recreated a form of full
packet regeneration inside a nominally persistent coding-agent loop.

Commit `ccaca8d7` makes the reviewer draft persistent. Each terminal-tool call
recursively updates only model-supplied mapping fields, explicitly supplied arrays
replace prior arrays, and omitted fields remain intact. Raw validator observations
return to the same isolated model history. The existing complete validator remains
fail-closed. There is no runtime-authored scientific completion, packet repair
agent, Architect route, provider retry, model escalation, or second scheduler.

This adopts the useful Codex boundary rather than Codex itself: a specialist owns
one durable work state, tools return raw observations to that same session, and a
small authority layer validates identity, hashes, and terminal invariants. Theory,
Python/R, Simulation, and Lean can use that inner-loop pattern independently;
AgentRuntime should coordinate only cross-workspace intent, accepted artifact
handoffs, blinding, and stopping. Codex core, App Server, Responses transport,
thread storage, Guardian, and the Codex SDK remain excluded from the Claude-first
product path because importing them would create another conversation owner and
scheduler.

The operator audit also found an active mathematical error that no harness merge
can fix: with `beta` and `t` fixed, increasing Gamma shape `r` does not make the
Gamma-Poisson count approach a fixed-mean Poisson law. Both author and referee
accepted that extra claim. This remains exact-Haiku model-judgment evidence; it did
not trigger a Gamma-Poisson rule, deterministic equation parser, extra reviewer
vote, or hidden feedback.

The upstream Codex checkout was rechecked through
[`e9a446d7`](https://github.com/openai/codex/commit/e9a446d79dc2b40549186ac69f665794ad52cdd5).
The only new commit adds low-cardinality Guardian decision metrics with explicit
reasons for approval or deferred review. The reusable principle is to keep
lifecycle decisions reason-coded and observable while keeping telemetry outside
scientific authority. It does not change the core model/tool/observation loop and
does not justify importing Guardian.

The focused reviewer panel passed `19/19`; the shared client-tool and reviewer
panel passed `44/44`; research-eval passed `23/23`; and the complete repository
passed `965/965` in 78.25 seconds. Task 62 was not rerun, resumed, repaired,
hidden-evaluated again, rescored, or resampled. Trustworthy capability remains
`4/62`, and exact development theorem closure remains `0/2`.

## One candidate, one semantic context

Task 62 also exposed an evaluator-level context error. The hidden semantic judge
reopened the same candidate once per frozen rubric claim. Each call saw only one
criterion, and overall PASS was derived solely from those isolated rows. That design
repeated the complete documents, scaled calls with rubric size, removed cross-claim
context, and provided no explicit authority for an additional active false statement
outside the listed claims.

Commit `2696ebb5` replaces that path for future draws with one integrated candidate
adjudication. The exact-Haiku evaluator sees the complete candidate, reference, and
all frozen rubric claims together. One structured response contains an independent
`document_status`, one grounded document excerpt, and keyed status plus grounded
evidence for every required claim. Deterministic aggregation fails when either the
whole-document judgment or a required claim fails. Thus a document can fail while
all listed claims are satisfied.

This is the same context-coherence principle used in a Codex coding session: keep one
artifact and its interacting constraints in one model context instead of spawning
independent fragments and combining their votes. It does not import Codex runtime,
add a reviewer, or let evaluator output enter AgentRuntime. Calibration remains one
separate candidate-isolated call; candidate work drops from one call per claim to one
call total. No live model was called while implementing the change.

The semantic-gold and research-gold panel passed `53/53`; the complete repository
passed `967/967` in 78.15 seconds. Compileall, diff hygiene, the unchanged 150,000-line
architecture budget, and changed-file secret hygiene passed. Task 62 and every earlier
draw remain immutable, trustworthy capability remains `4/62`, and exact development
theorem closure remains `0/2`.

## Source-owned Simulation planning

The current Codex checkout was rechecked through
[`6c59264b`](https://github.com/openai/codex/commit/6c59264b14b963d45d1005e7a8b1de87d4b054e2).
The only delta after the prior `e9a446d7` pin increases Guardian V2 async-test
timeouts; it changes no production agent-loop, collaboration, tool, or state
boundary.

The deeper reuse decision remains selective. Codex's Python SDK is a typed client
that launches the bundled `codex app-server --listen stdio://`; importing it would
therefore import Codex's conversation owner, thread lifecycle, tool router, and
provider boundary rather than supply a provider-neutral inner-loop library. Codex
multi-agent V2 is useful as a collaboration vocabulary: a same-owner continuation
keeps exact session state, while a new specialist can receive no parent turns and a
small explicit task. Its default shared working directory is not sufficient for
scientific blinding or independent review, so AI Statistician keeps isolated
reviewer workspaces and content-addressed artifact references.

The local audit found one remaining violation of the reusable principle.
AlgorithmEngineer already lets one native Python/R source session plan, implement,
execute, and revise against raw observations. Confirmatory Simulation still made a
detached structured-output planning call before entering the same model's source
session, even when runtime had already frozen one stable source-acceptance ABI.

Commit `3fe4bdb9` removes that call for future exploratory runs and future
confirmatory source-acceptance runs. Runtime materializes only a deterministic
intent identity, exact accepted-estimator references, frozen requirement bindings,
replicate count, and seed-disclosure state. The Simulation source owner receives
the authoritative Theory documents, estimator ABI, frozen protocol, sandbox tools,
and raw observations in one session; it chooses the DGP, implementation, and
diagnostics. Legacy frozen metric-path packets retain their existing reconstruction
path because their binding cannot be inferred without changing scientific content.

This adds no App Server, SDK, thread manager, shared-cwd collaboration, planner
agent, repair worker, provider retry, model escalation, statistical rule, or second
scheduler. The focused source-acceptance checks passed `3/3`, the adjacent
Simulation/Runtime panel passed `132/132`, and the complete repository passed
`968/968` in 79.47 seconds. Compile-all, diff hygiene, model-policy and secret scans,
and the unchanged 150,000-line architecture budget passed; production Python is
149,270 lines. No live model was called and no consumed task was rerun, resumed,
repaired, hidden-evaluated, rescored, or resampled. Task 62 remains immutable `0/1`,
trustworthy capability remains `4/62`, and exact development theorem closure remains
`0/2`.

## Required-lane continuation and Task 65

Task 65 supplied a disjoint check of the current collaboration topology. One
exact-Haiku TheoryDeveloper maintained Markdown/LaTeX and passed hidden theory
mechanics `7/7` plus integrated semantics `7/7`. One AlgorithmEngineer received
raw review failures in the same source-owning session and regenerated executable
Python. The second isolated review accepted that source, but hidden authority found
that `truth_probability=True` still crossed the closed public contract. Hidden
algorithm checks were `10/12`; evaluator-only empirical checks were `10/10` over
30,000 calls. These are component results. Runtime never executed Simulation and
the immutable full-task score is `0/1`.

The collaboration defect was generic. The accepted Algorithm review restored an
exact deferred Critic task, and the outer policy returned it before checking for a
still-unvisited frozen required primary lane. Critic then submitted invalid ACCEPT
packets without seeing a dimension-by-dimension validator mismatch. Commit
`5f062672` preserves exact deferred specialist continuations, but lets terminal
Critic work yield to required frozen lanes. When no required lane remains, the
original Critic task is preserved. Invalid ACCEPT now receives one structured
observation listing unsupported required dimensions, `NOT_REQUESTED` mismatches,
contradictions, gap status, and blocking dimensions; the final exact invalid model
packet remains auditable.

This is selective Codex reuse, not a Codex embedding. The useful units are the
same-session model/tool/observation loop, immutable issuing-step authority, exact
continuation, typed lifecycle reasons, bounded observations, persisted external
artifacts, and explicit model policy. Theory, Python/R, Simulation, and Lean remain
independent model-owned workspaces under one AgentRuntime research graph. Codex
core, App Server, Responses transport, thread management, Guardian, shared-cwd
subagents, and provider transport remain excluded because they would add a second
conversation owner or scheduler.

The upstream source audit was refreshed through
[`5f49aba8`](https://github.com/openai/codex/commit/5f49aba876922d6f2f55caa153bbb0ed1b46feba).
The latest delta reinforces explicit delegated-model overrides, active-step model
budgets, bounded terminal-reviewed input, typed lifecycle classifications, and
frozen tool/plugin attribution. None requires a statistical rule, Lean grammar
rule, content repair, retry, extra agent, provider escalation, or task-family
route. Focused future-task checks passed `100/100`; the complete pre-ledger
repository passed `983/983`. Production Python is 149,995 lines under the unchanged
150,000-line budget. No live model was called for the correction, and Task 65 was
not rerun, resumed, repaired, hidden-evaluated again, rescored, or resampled.
Trustworthy capability remains `4/65`; exact development theorem closure remains
`0/2`.

## Explicit estimator handoff and Task 66

The official source was rechecked at current main
[`5f49aba8`](https://github.com/openai/codex/commit/5f49aba876922d6f2f55caa153bbb0ed1b46feba).
Its `run_turn` loop keeps one turn-scoped model session across model output, tool
execution, and returned observation. Its multi-agent session code propagates
explicit context rather than assuming that an independent worker can reconstruct
the issuing step's state. Shared working directories remain a Codex product
choice, not an adequate scientific authority boundary.

Task 66 isolated the corresponding local violation. TheoryDeveloper's persistent
Markdown/LaTeX workspace passed hidden mechanics `7/7` and all eight semantic
claims after `11/11` judge calibration. AlgorithmEngineer produced correct core
formulas but added an unsupported constant-outcome rejection, which the isolated
reviewer missed. Simulation then received no estimator binding even though a
hash-bound accepted Algorithm handoff existed; it reimplemented the estimator and
could not expose that defect. A later Simulation review declared zero blocking
defects while encoding one nonblocking note as a structured finding, exhausting
the source lineage. The immutable full-task result is `0/1`.

Commit `464cba39` corrects only those general harness boundaries for future work.
Simulation always attempts to validate an available accepted Algorithm handoff,
including during exploratory diagnostics. If no handoff exists, early Simulation
remains allowed; if a confirmatory task requires one, the existing fail-closed
gate remains. Once present, the existing scientific executor, rather than a new
bridge, binds exact estimator source. The semantic-review prompt tells the model
that a structured finding is an active downstream blocker and that nonblocking
notes remain in its Markdown report. Runtime does not infer blocking from severity,
edit scientific source, or add a task-specific check.

This is the maximum useful Codex reuse here. AI-Statistician keeps one native
AgentRuntime graph and separate model-owned Theory, Python/R, Simulation, and Lean
workspaces. It does not import Codex core, App Server, Responses transport,
provider client, thread manager, Guardian, shared-cwd subagents, worktree manager,
or scheduler. Full deterministic regression passed `985/985`; production Python
is 149,993 lines. Task 66 was not rerun, resumed, repaired, hidden-evaluated again,
rescored, or resampled. Trustworthy capability is `4/66`; exact development
theorem closure remains `0/2`.

## Source-owned falsification and confirmation after Task 67

Official Codex `main` was fetched again and remains pinned at
[`5f49aba8`](https://github.com/openai/codex/commit/5f49aba876922d6f2f55caa153bbb0ed1b46feba).
The reusable design remains its persistent model/tool/observation loop: the model
that owns an artifact sees raw execution output, edits its own artifact, and
continues in the same context. Cross-owner collaboration passes explicit compact
state; lifecycle, permissions, budgets, and durable identity stay outside the
model. AI-Statistician does not import Codex Core, App Server, provider transport,
thread store, shared-cwd subagents, Guardian, or another scheduler.

The immutable Task 67 draw exposed three generic failures. A reviewer attempted
three executable probes that all failed before target invocation and then accepted
the source. Exploratory Simulation successfully used the accepted estimator but
returned to Critic before authoring the required confirmatory evaluator. Separately,
both theory author and referee trusted a familiar assumption label instead of
testing its actual implication; the calibrated hidden semantic judge missed the
same error. None justifies a DID rule, Boolean patch, output repair, or retry layer.

Commit `9dcd4355` applies the Codex-style correction for future tasks. A reviewer
that chooses to probe may not use those probes to support ACCEPT until at least one
has invoked the exact immutable target; raw sandbox failure is returned to that
same reviewer, which must rewrite and rerun its own probe or submit a non-accepting
judgment. A successful exploratory simulation whose frozen intent requires an
executable evaluator now continues in the same Simulation workspace to source
authoring, existing independent semantic review, and existing exact confirmatory
replay. The handoff contains accepted estimator identity plus compact exploratory
manifest hashes, not copied prototype payloads. Routine collaboration does not go
through Architect, and the orchestration transition is not mislabeled as scientific
evidence.

TheoryDeveloper and its independent referee receive only a general scientific
instruction: interpret assumptions by mathematical content and attempt
countermodels for load-bearing implications. Runtime still encodes no theorem,
formula, assumption semantics, input type rule, DGP, threshold, source patch, Lean
grammar, or tactic. No live model was called for this correction. The final focused
panel passed `237/237`; the complete repository passed `986/986` in 78.30 seconds.
Production Python is 149,998 lines and `research_agent_runtime.py` is 24,961 lines,
both under unchanged architecture limits. Task 67 remains immutable `0/1`, trusted
capability remains `4/67`, and exact development theorem closure remains `0/2`.

## Fresh current-source observation after Task 68

Official Codex `main` was fetched again and remains
[`5f49aba8`](https://github.com/openai/codex/commit/5f49aba876922d6f2f55caa153bbb0ed1b46feba).
The relevant reusable unit is still Codex's turn-scoped model/tool/observation
lifecycle: persisted history may provide context, but an action is grounded in the
active workspace snapshot and raw current tool output. Explicit step identity,
bounded tools, compact state, and model-owned source iteration are useful here;
Codex Core, App Server, provider transport, thread storage, worktree management,
Guardian, and shared-cwd subagents would create a second conversation owner or
scheduler and remain excluded.

Task 68 exposed a narrow violation of that principle. The second generated-source
review work order correctly named the final executed confirmatory source and exact
hash. That source implemented the requested per-DGP decision checks and executed
successfully. The isolated reviewer nevertheless repeated a prior finding about
hardcoded lines from the superseded source. Historical finding prose was present in
the opening context, while no fresh tool observation forced the reviewer to inspect
the current source associated with the work-order hash.

Commit `f2e39edb` corrects the lifecycle for future tasks. A review with active prior
findings initially receives current artifact identity and hash, but not a copied
source body. In the same isolated reviewer session it must call
`read_current_generated_source` once for every current target before terminal
submission. The tool returns complete immutable source with line numbers, exact hash,
line count, and current-authority status. Historical findings remain reviewable
claims, while the fresh source observation is the current target. A first review has
no prior finding and therefore incurs no additional turn or tool call.

This is not a repair harness. Runtime neither parses source grammar nor chooses a
change. The source-owning Algorithm or Simulation model still reads raw execution
feedback and revises its own complete program; the independent reviewer still owns
semantic judgment. Runtime supplies identity, tool permission, validation, budget,
and evidence boundaries only. No statistical formula, Welch rule, Python type patch,
Lean grammar, tactic, source rewrite, retry, extra reviewer, provider, model
escalation, or second scheduler was added.

Focused reviewer and runtime regressions passed `146/146`; the complete repository
passed `988/988` in 79.56 seconds. Compile, diff, and the unchanged 150,000-line
architecture budget passed, with production Python at 149,998 lines. Task 68 was not
rerun, resumed, repaired, hidden-evaluated again, rescored, or resampled. Its
operator-invalidated result remains immutable `0/1`, trustworthy full-task
capability remains `4/68`, and exact development theorem closure remains `0/2`.

## Complete-claim alignment and current upstream recheck

Official Codex `main` was fetched through
[`8aea62b2`](https://github.com/openai/codex/commit/8aea62b2d857e950cb84366602af79403b8ed545).
The delta after `5f49aba8` adds descendant-token accounting for root goals,
active-step model token budgets, response-usage metadata, explicit delegated-model
override policy, and permission/plugin/test hardening. The production `run_turn`,
tool router, tool-output continuation, and multi-agent workspace semantics that
matter here are unchanged. Descendant usage accounting is useful lifecycle
telemetry, but importing Codex's goal extension would add product state without
improving scientific reasoning; AI Statistician already records provider usage in
each source-owning session.

The deeper Task 68 failure was not absent context or an unavailable tool. Both the
TheoryDeveloper and isolated referee executed a weaker shift check, then treated its
label as evidence for a compound interval claim that the executable predicate never
tested. They also omitted a type/dimensional audit of a displayed variance formula.
This is a model-owned claim-to-observation error, not a reason for a Welch formula,
symbolic grammar parser, deterministic mathematics patch, another reviewer, or
another scheduler.

Commit `11ee99bd` applies the smallest future-only correction. The existing Theory
and referee sessions are asked to reconstruct the complete proposition, expose its
relevant sides, residual, predicate, or witness, check object types, domains, and
dimensions, and seek a countermodel that preserves the written premises. A weaker
proxy cannot support the stronger claim merely by sharing its label. DID-specific
group/baseline examples were removed. Tool surfaces, turn and call budgets, model
policy, workspace ownership, artifact formats, and AgentRuntime topology are
unchanged.

The focused Theory/referee panel passed `156/156`; the complete repository passed
`988/988` in 78.68 seconds. Production Python is 149,999 lines under the unchanged
150,000-line budget. No live model was called, and no consumed task was rerun,
resumed, repaired, hidden-evaluated again, rescored, or resampled. Task 68 remains
immutable `0/1`, trustworthy capability remains `4/68`, and exact development
theorem closure remains `0/2`.

## Upstream Codex recheck and Neyman-Scott evaluator false positive

Official Codex `main` was refreshed through
[`e931d07b`](https://github.com/openai/codex/commit/e931d07b88338c1898ad37b056aedf5458037de6).
The current source reinforces four mechanisms that AI Statistician should reuse as
principles rather than dependencies:

1. `run_turn` keeps one turn-scoped model session alive across model, tool, and raw
   observation continuations. Transport retries are separate from source revision.
2. world-state sections emit identity-bound diffs and retire replaced context instead
   of repeating unchanged instructions or recursive payloads.
3. executed tool calls retain call identity and completion state while bounding copied
   arguments and prioritizing recent observations.
4. Guardian review receives an exact current action plus a compact transcript delta,
   explicitly treats the transcript as untrusted evidence, and keeps reviewer state
   separate from the source-owning session.

AI Statistician already uses the corresponding scientific form: one AgentRuntime,
persistent Theory/Python/R/Simulation/Lean owner sessions, exact artifact hashes,
direct environment feedback, content-addressed continuation references, and isolated
review sessions. Importing Codex Core, App Server, Responses transport, thread store,
Guardian, or multi-agent shared-working-directory semantics would duplicate the
scheduler and weaken scientific artifact isolation. Codex's new extension and
multi-agent lifecycle code does not change that conclusion.

Task 69 provides a useful negative result. Its exact-Haiku TheoryDeveloper wrote a
persistent Markdown/LaTeX derivation, the isolated referee read and scratched against
it, and the calibrated hidden semantic judge ran only after termination. Nevertheless,
all three accepted an active probability-limit equality containing one extra `1/T`.
The referee also miscomputed a displayed variance by a factor of ten and then called
the matching scratch result a 920% Monte Carlo discrepancy. Exact workspaces and tools
made the error auditable; they did not make Haiku reason correctly.

The correct response is not another product layer. The existing prompts already say
that a correct conclusion cannot cancel a false intermediate equality and already
offer Python/R/SymPy scratch. No formula rule, parser, repair worker, extra reviewer,
repeated sample, retry, scheduler, provider, or model escalation is added.

The evaluation lesson is narrower. Calibration used concise negative notes under an
overall-status schema, while the live candidate used a long integrated document and
per-claim schema. Before a future unrelated authority is activated, the exact
candidate-mode semantic path should pass the full reference and reject at least one
realistic long-form near miss with a correct headline conclusion and a material active
contradiction. That negative remains evaluator-only, is frozen before the first
product call, and never becomes runtime feedback. Task 69 remains immutable `0/1`,
trustworthy capability remains `4/69`, and exact development theorem closure remains
`0/2`.

## Candidate-mode activation without another runtime

Commit `6d751fb6` turns the Task 69 evaluator lesson into one bounded shared
mechanism. New schema-4 authorities must provide at least one hash-bound long-form
near miss. Protocol v5 sends each near miss through the exact integrated candidate
schema in its own exact-Haiku call, with private identity and expected status omitted,
then sends the frozen full reference as the activation candidate. A false-accepted
negative fails activation before AgentRuntime makes its first product-model call.

Activation and post-runtime hidden evaluation call the same semantic execution
function. The result cannot edit a workspace, route a task, retry a candidate, or
enter runtime feedback. This follows Codex's useful principle of one owner loop plus
exact current observations while keeping evaluator authority isolated from the
source-owning session.

The change also removes the 671-line `fresh_start_cross_task_e2e.py` side audit and
its isolated tests. No product or CLI path used it, and it required Lean closure for
every task despite the current task-intent-driven optional-formalization contract.
The complete repository passes `983/983`; production Python is `149638` lines, 359
fewer than before this mechanism. No formula, parser, repair worker, retry, extra
reviewer, scheduler, provider runtime, Sonnet, or Opus call was added.

## One model-owned loop, without a terminal-repair state machine

Official Codex `main` was refreshed through
[`f6494dc8`](https://github.com/openai/codex/commit/f6494dc8f5969e8576a8a0945a674f2a15ac4de6).
Its canonical
[`run_turn`](https://github.com/openai/codex/blob/f6494dc8f5969e8576a8a0945a674f2a15ac4de6/codex-rs/core/src/session/turn.rs)
continues one model session across tool calls and observations. Relevant upstream
commit
[`0182ff34`](https://github.com/openai/codex/commit/0182ff34)
also finalizes the tool plan against the explicit model selected for the issuing
step. This reinforces a stable, caller-owned tool surface and exact turn identity;
it does not justify a second scheduler or a task-specific repair controller.

Before commit `e282aeb1`, AI Statistician's shared client-tool loop had accumulated a
separate terminal-decision phase, reserved terminal retries, forced recovery-action
turns, and terminal-specific routing metadata. A rejected checkpoint or verdict
could therefore change the harness phase even though the correct owner was still the
same Theory, scientific-code, Lean, or reviewer model. That was unnecessary control
logic and made nominal workspace budgets differ from the actual number of model
turns.

Commit `e282aeb1` removes that state machine. A terminal submission is now an
ordinary model-selected tool call. Rejection is returned as a raw error observation
to the same transcript, after which the model may choose any still-authorized tool.
Every action and resubmission remains inside one explicit total-turn budget; ordinary
workspace actions retain their separate caller-owned budget. Callers that already
expose a validation-retry setting translate it only into additional ordinary model
turns. There is no forced terminal mode, hidden recovery allowance, content patch,
repair agent, or automatic outer reroute.

The same primitive now governs Theory checkpoints, Python/R workspaces, Lean source
iteration, metric authoring, independent semantic review, preflight review, and the
final Critic. Their domain tools and verifier authorities remain distinct; only the
interaction principle is shared. Codex Core, App Server, SDK threads, OpenAI model
transport, thread storage, and shared-working-directory subagents remain excluded
because importing them would duplicate AgentRuntime and violate the Claude-only
provider boundary. The [Codex SDK](https://learn.chatgpt.com/docs/codex-sdk) remains
useful reference material, not a runtime dependency.

Focused workspace regressions passed `250/250`; the complete repository passed
`983/983` in 84.88 seconds. Compileall and diff checks passed. The change is a net
reduction of 262 lines and leaves top-level production Python at 149,430 lines. No
live model was called. Task 70's visible Fieller benchmark remains unconsumed: no
product call, semantic activation call, hidden evaluator call, retry, rerun, score,
or runtime feedback occurred.

## Fieller draw: patch ergonomics and commit-aware continuation

Task 70 consumed one exact-Haiku product draw and one post-runtime hidden
evaluation under schema-4 authority. It is permanently `0/1`; trustworthy
aggregate credit is `4/70`.

The draw supplies positive evidence for the scientific architecture rather than
for the complete system. TheoryDeveloper maintained two authoritative
Markdown/LaTeX documents, used local scratch and exact edits, explicitly
checkpointed them, and passed independent preflight. The hidden mechanical
theory harness passed `7/7`. The qualified integrated exact-Haiku semantic judge
passed `4/4` calibration cases and `1/1` long-form near miss, then marked the
candidate document `PASS` with all eight rubric claims satisfied. Formalization
was correctly not applicable and never ran.

The Algorithm workspace exposed a generic harness integration defect. Its model
submitted complete Python, received raw sandbox errors, edited directly, and
executed four distinct hashes. Two executions exited successfully, but the
model's own diagnostic output still reported metamorphic failures. The model
continued editing and exhausted the segment immediately after an unexecuted
final edit, so it never called `commit_scientific_source`. The workspace
correctly produced a resumable exact checkpoint. AlgorithmEngineer then
incorrectly treated the last raw `smoke_passed` value as accepted source and
attempted source-packet materialization before same-owner continuation. The
materializer failed closed because explicit workspace evidence and one model
identity were absent. No accepted algorithm handoff existed, so hidden algorithm
and empirical evaluators correctly did not run.

Commit `ecfc2403` makes two shared future-task corrections:

1. Algorithm source acceptance, pass counts, source reuse, source-owned packet
   materialization, and checkpoint resume all use the existing explicit
   scientific-source gate. Successful process execution with a workspace
   failure remains diagnostic execution, not accepted code, and its checkpoint
   returns to the same source owner without Architect routing.
2. `edit_current_scientific_source` now accepts an ordered array of exact edits
   and applies the whole patch atomically. This mirrors Theory's existing batch
   edits and Codex's grammar-delimited multi-hunk
   [`apply_patch`](https://github.com/openai/codex/blob/f6494dc8f5969e8576a8a0945a674f2a15ac4de6/codex-rs/core/src/tools/handlers/apply_patch.lark),
   reducing one-edit-per-turn churn while leaving all source content with the
   model.

No auto-commit, forced terminal turn, hidden retry, repair phase, diagnostic
parser, task formula, extra reviewer, agent, Architect route, scheduler, provider,
or model escalation was added. Focused scientific workspace and continuation
tests passed `25/25`; the mechanism-only repository passed `985/985` in 81.02
seconds. After adding the immutable Task 70 ledger assertion, the complete
repository passed `986/986` in 80.87 seconds. Task 70 was not rerun, resumed,
repaired, hidden-evaluated again, rescored, resampled, or manually committed.

## Task-intent-driven evaluator dependencies

The executable evaluator lane already matched the useful Codex harness pattern:
one Simulation model authors ordinary Python/R source, executes it directly,
receives raw observations in the same session, explicitly commits exact bytes,
and sends those bytes to an isolated reviewer before one blinded confirmatory
replay. The remaining defect was outside that inner loop. Runtime universally
required an accepted Algorithm handoff at confirmation and could begin evaluator
authoring before checking that dependency.

Commit `ea7a6ce0` makes the dependency belong to frozen task intent. A task whose
scientific-code dimension is required must present a validated accepted Algorithm
handoff before any evaluator-authoring model call. A task whose scientific-code
dimension is not applicable can author and confirm an evaluator without stale
Algorithm fields. An optional valid handoff is still preserved when the task has
one. Exploratory Simulation remains available as an early diagnostic; only frozen
confirmatory evidence is dependency-gated.

The cohesive authoring-task builder moved into the existing evaluation protocol
module, leaving `research_agent_runtime.py` at 24,998 lines under its enforced
25,000-line architecture budget. Runtime still chooses no estimator, DGP, metric,
threshold, formula, source patch, or repair action. No new agent, scheduler, retry,
fallback, task branch, Codex runtime, or model escalation was added.

The affected evaluator/runtime panel passed `110/110`; the complete repository
passed `987/987` in 81.46 seconds. No live model was called, no task was consumed,
and Task 70 remains immutable `0/1` with the trusted aggregate unchanged at
`4/70`. Future tests and evaluations remain exact
`claude-haiku-4-5-20251001`; production remains Sonnet or below; Opus remains
prohibited.

## Semantic qualification without product repair

Task 71's preactivation exposed a general evaluator distinction rather than a
product-runtime failure. An incomplete document that explicitly declines to
claim a result is unsupported, not contradicted. Protocol v9 therefore tells
the independent judge to use `INCONCLUSIVE` for omitted or explicitly
uncovered claims and to reserve `VIOLATED` for an active false assertion or
invalid asserted derivation. This is scientific evidence semantics, not a
statistical formula, document parser, or output repair rule.

The first protocol-v8 qualification and the first protocol-v9 qualification
both passed three of four cases because the nominal partial control also
narrowed an arbitrary-CDF target to continuous distributions. The hidden
control was replaced before any product call by a clean arbitrary-CDF setup
whose proof obligations are explicitly unresolved. The final exact-Haiku
qualification passed `4/4` calibration cases, `1/1` integrated long-form near
miss, and the eight-claim reference. All three attempts remain recorded; no
result entered AgentRuntime.

This preserves the useful Codex boundary: validation owns action and evidence
semantics, while the source-owning model owns substantive work. The hidden
authority is frozen and hash-bound outside the model workspace, activation
reuses the qualified record with zero additional semantic calls, and the sole
future product draw remains one direct AgentRuntime execution. No second model
session, repair worker, retry path, scheduler, or Codex runtime was added.

## Task 71 and the current Codex harness boundary

The official Codex repository was inspected again at upstream commit
`f1bb4c168d7b7bcfab8083d8cb34996bf2332c3a`. Its current turn runner keeps one
turn-scoped model session, samples from the exact accumulated history, executes
requested tools, records their outputs, and continues the same loop while a
tool call or stop hook requires follow-up. Its tool router likewise binds one
final model-visible tool plan to the matching executable registry, while every
invocation carries exact tool, call, source, payload, and session identity.

Those are the Codex mechanisms AI-Statistician should reuse as principles:

1. Each substantive owner keeps one persistent model/tool/observation loop.
2. Raw Python, R, Lean, search, and document observations return to that same
   owner; ordinary failures do not route through Architect or a repair agent.
3. The advertised tool contract and executable implementation are one surface.
4. Artifacts and tool calls have exact identity and external content-addressed
   storage rather than recursively copied payloads.
5. An independent reviewer may block promotion and return a compact observation
   to the source owner, but it does not rewrite the work.

Task 71 confirmed that this execution shape now works. Simulation received a
semantic finding and continued with the same source-owning model without an
Architect round trip or repair worker. The remaining failure was scientific
judgment: the theory asserted an arbitrary-CDF theorem while deriving only the
finite-discrete case, and both the independent referee and hidden semantic judge
missed that strict scope contraction. The Simulation reviewer also accepted a
source whose returned decision was constant rather than computed from its own
diagnostics.

The future-only response is therefore a protocol clarification inside the
existing loops, not a new harness layer. Theory must reconcile active
quantifiers with proof branches; the referee and hidden judge must treat a
strict-subdomain derivation supporting a broader active conclusion as an
invalid asserted derivation; and the Simulation source reviewer must trace the
acceptance output back through every load-bearing computed check. Runtime still
does not parse mathematics, infer code semantics, choose a threshold, repair a
source, or add a task-specific rule.

Importing Codex Core, App Server, Responses transport, thread storage, Guardian,
worktrees, or Codex collaboration agents would create a second orchestration
plane without supplying statistical semantics, empirical blinding, Lean kernel
authority, or scientific evidence calibration. The right reuse is the small
session-and-tool-loop principle above, while AI-Statistician retains its own
task-intent evidence contract and specialist scientific environments.

## Current Codex session audit and Claude transport reuse

Official Codex `main` was refreshed through
[`ec9620c2`](https://github.com/openai/codex/commit/ec9620c231396895194329c410f3ec360b4cadef).
The two-commit delta after the Task 71 audit adds configurable exposure for the
sleep tool and authentication-recovery progress. Neither changes the central
execution contract. Codex still creates one turn-scoped `ModelClientSession`,
reuses its provider transport and sticky state across tool continuations, rebuilds
one exact step context and finalized tool router, and returns each completed tool
output to the same accumulated history.

AI Statistician already matched the scientific part of that contract: one
AgentRuntime, persistent model-owned Theory/Python/R/Simulation/Lean sessions,
stable tools for each session, and raw observations returned to the issuing model.
The remaining transport mismatch was concrete. `AnthropicGeneratorBackend`
constructed a new Anthropic SDK client for every ordinary generation and every
client-tool round. The immutable Task 72 run contains 68 client-tool model-round
records, so one run alone discarded the SDK connection pool dozens of times.

Commit `f4a097a4` retains one Anthropic SDK client for the lifetime of a backend at
one resolved timeout. The existing lock makes initialization atomic. Every sampling
call still supplies its exact model, messages, tool definitions, tool choice,
temperature, prompt-cache request, and model-tier metadata; SDK retries remain zero
and the existing provider-local request retry policy is unchanged. This is transport
reuse, not conversation summarization or hidden session state.

No Codex Core, App Server, SDK thread, OpenAI model transport, tool scheduler,
subagent manager, repair worker, fallback, extra model call, or research budget was
added. A new ToolRouter clone was also rejected: the current client-tool loop already
freezes one unique tool-definition tuple for the session, and Task 72 showed no
unavailable-tool or internal-dispatch mismatch. Refactoring every specialist tool
behind another registry without a measured failure would add an interface rather
than remove one.

The shared model-backend and client-tool regressions passed `58/58`; the complete
repository passed `990/990` in 81.39 seconds. No live model call or task activation
occurred. Task 72 and all prior draws remain immutable, trusted aggregate credit
remains `4/72`, all future tests and evaluations remain exact
`claude-haiku-4-5-20251001`, production remains Sonnet or below, and Opus remains
prohibited.

## Optional diagnostics do not own reviewer verdicts

The post-Task 72 harness audit found one remaining contradiction in the otherwise
model-owned generated-code review loop. `run_exact_estimator_review_probe` was
documented as optional: a reviewer-side source failure before target invocation was
returned as a raw tool error, explicitly marked as covering nothing, and could be
ignored while the independent model reviewed the exact immutable target source.
Nevertheless, a separate runtime condition prohibited `ACCEPT` after any such failed
probe until another probe reached the target. A reviewer that never used the optional
tool could accept from source, while one that attempted a diagnostic had its verdict
controlled by its own scaffolding error.

Commit `073d2e42` deletes that procedural verdict controller and its contradictory
prompt sentence. It does not convert a failed probe into evidence. The exact
observation remains `is_error=true`, `target_source_invoked=false`,
`failed_probe_is_target_source_evidence=false`, and
`NOT_EMPIRICAL_ACCEPTANCE_OR_PROOF`. Immutable source identity, independent model
identity, finding-ledger consistency, Markdown review identity, lineage validation,
and downstream promotion gates are unchanged. The isolated reviewer may repair and
rerun when execution matters, submit `REVISE`, or ignore invalid diagnostic scaffolding
and judge the exact source itself.

This follows the useful Codex harness boundary: tools expose observations, while the
model owns substantive interpretation. No probe retry, extra turn, fallback,
source patch, acceptance default, repair agent, Architect route, or second scheduler
was added. The change is a net deletion of 56 lines. Reviewer, AgentRuntime,
client-tool, and architecture tests passed `153/153`; the complete repository passed
`990/990` in 81.77 seconds. No live model call occurred. Task 72 was not rerun,
resumed, repaired, re-evaluated, rescored, or resampled and remains immutable `0/1`;
trusted aggregate credit remains `4/72`.

## Review prose is not a token gate

The same audit found one deterministic content proxy in executable-evaluator review.
For `ACCEPT`, runtime required the model-authored Markdown to contain the literal
public entrypoint and every authority-output field. Mentioning those tokens did not
prove that the reviewer traced the implemented decision, and a correct explanation
could describe the dependency path without copying identifier spellings. The rule
therefore tested prose serialization rather than scientific-code semantics.

Commit `d3597ae7` deletes the 23-line token parser. The reviewer still receives the
exact source, current-target role, entrypoint, outputs, runtime arguments, and the
general instruction to trace the returned decision backward through every
load-bearing computed check. Its Markdown content and SHA-256 remain immutable review
evidence; its findings and verdict remain model-authored. Runtime continues to verify
document identity, source identity, review-input fingerprint, independent invocation,
finding-ledger consistency, parent lineage, empirical blinding, and promotion status.

The focused reviewer, AgentRuntime, and architecture panel passed `128/128`; the full
repository passed `990/990` in 81.38 seconds. The change is a net deletion of 27 lines.
No model call, task activation, retry, content repair, acceptance default, parser
replacement, or scheduler was added. All consumed tasks remain immutable and trusted
aggregate credit remains `4/72`.

## Canonical runtime does not import the legacy research lab

The product import graph still had one hidden architecture coupling.
`research_agent_runtime.py` imports only `build_research_evaluation_summary` from
`research_evaluation.py`, but that module eagerly imported the old
`research_lab.py` seed benchmark. As a result, importing canonical AgentRuntime also
loaded the large registered-procedure simulator and its task-family keyword/metric
heuristics even though no canonical call used them. An isolated process confirmed the
pre-change state: `ai_statistician.research_lab in sys.modules` was `True` immediately
after importing AgentRuntime.

Commit `32a04928` moves those two legacy imports inside the explicit
`run_research_seed_eval` entrypoint. Canonical AgentRuntime import now leaves
`research_lab` unloaded, while an actual empty-seed call to the old entrypoint still
loads and completes normally. A subprocess architecture regression enforces this
boundary without relying on pytest's already-populated module cache.

This change adds no module, adapter, router, fallback, scheduler, model call, or task
rule. It does not certify the legacy simulator; it prevents its registered answers and
keyword heuristics from entering the live product dependency graph accidentally. The
AgentRuntime, research-evaluation, and core panel passed `120/120`; the complete
repository passed `991/991` in 86.60 seconds. No task was activated and trusted
aggregate credit remains `4/72`.

## Actual CLI startup and hidden authority are outside AgentRuntime

The prior import fix covered a direct `research_agent_runtime` import but not the
real product command. Importing `cli.py` still loaded `research_lab.py` through a
shared question-file loader and several legacy audit modules. In addition,
`run_research_agent_runtime` accepted an evaluator-only gold manifest, activated its
hidden authority before the product loop, scored it after termination, and embedded
the score in the canonical runtime manifest. The model never received those values,
but the ownership boundary was weaker than the documented design.

Commit `af085faa` moves unchanged JSON/Markdown question loading into
`research_schema.py`; `research_lab.py` re-exports it for compatibility. Legacy
benchmark and audit implementations now load only inside their explicit commands.
Fresh processes importing either the direct runtime or the actual CLI leave both
`research_lab` and `research_gold_evaluation` absent from `sys.modules`, while an
explicit old seed evaluation still loads and completes on demand.

The same commit removes hidden gold from the AgentRuntime signature, imports,
artifacts, and manifest. Evaluator-facing CLI code validates frozen task scope before
product execution and, only after the product loop returns, loads the persisted
per-question results. Content-addressed artifacts are rehydrated only when artifact
identity, declared kind, and stable content hash match. A tampered blob fails closed.
The separate gold evaluator then writes its existing evaluator artifact and controls
the evaluation command's exit status; nothing is returned to a model, blackboard,
retriever, continuation, or source-revision loop.

This follows Codex's useful authority split: the product turn owns its tools and
observations, while external evaluation observes completed artifacts rather than
becoming a tool of the turn. No agent, retry, fallback, repair path, content rule,
task-family branch, second scheduler, model call, or Codex runtime dependency was
added. Focused boundary tests passed `78/78`, the AgentRuntime and question-contract
panel passed `113/113`, and the complete repository passed `992/992` in 83.43
seconds. All 72 consumed draws remain immutable at trusted aggregate `4/72`.

## Current Codex source audit and terminal continuation

Official Codex `main` was fetched and rechecked through
[`6be2a6ca`](https://github.com/openai/codex/commit/6be2a6ca952ac9f70676ce4dd07fda27175aa9dd).
The current [`run_turn`](https://github.com/openai/codex/blob/6be2a6ca952ac9f70676ce4dd07fda27175aa9dd/codex-rs/core/src/session/turn.rs)
still states the reusable core directly: the model selects function calls, the
harness executes them, their outputs return to the same accumulated model session,
and an assistant response without another call completes the turn. OpenAI's
[Codex as a platform](https://developers.openai.com/blog/codex-as-a-platform)
describes the same product boundary: an application supplies its domain context and
tools while the harness owns the action loop, execution boundaries, and continuation.

That is the maximum useful reuse for AI Statistician. The scientific mapping is:

| Research capability | Codex-shaped ownership in AI Statistician |
| --- | --- |
| Theory development | One persistent Markdown/LaTeX workspace; the same TheoryDeveloper reads, searches, edits, runs Python/R scratch work, receives observations, and commits or reports a gap. |
| Scientific coding | One source-owning model edits Python/R source, executes it, reads raw interpreter and consumer observations, and revises in the same session. |
| Simulation | The source owner implements and diagnoses exploratory or frozen confirmatory execution; independent review may block promotion but does not repair source. |
| Lean formalization | One Formalizer session edits Lean, compiles, inspects goals/LSP output, retrieves declarations, and revises; the kernel remains final proof authority. |
| Collaboration | One outer AgentRuntime allocates task intent and genuinely cross-workspace handoffs through immutable artifact references. Routine tool failures stay inside the issuing workspace. |

The newer Codex context manager, history budgets, parallel tool runtime, agent
registry, subagent lifecycle, app-server, and SDK are orthogonal product services,
not a replacement scientific architecture. Codex's provider surface is OpenAI
Responses-compatible, whereas this project deliberately uses native Anthropic
Haiku for tests/evaluations and Sonnet or below for production. Embedding Codex Core
or App Server would therefore add another conversation owner, provider boundary,
tool router, scheduler, and persistence model. It would not improve statistical
reasoning, simulation validity, theorem fidelity, or Lean proof search.

Task 73 exposed one narrower lifecycle defect in the local shared loop. A Critic used
its last ordinary turn to read another artifact and received the raw observation, but
there was no subsequent sampling turn in which the same model could submit its
terminal disposition. This violated the model -> tool -> observation -> model
continuation invariant even though ordinary action accounting itself was correct.

`run_bounded_client_tool_loop` now permits exactly one control-plane continuation
when, and only when, the final normal turn requested an ordinary workspace tool and
the session defines a terminal tool. The continuation:

- retains the same model, transcript, provider session, and stable tool definitions;
- can submit only a terminal disposition and executes no further research action;
- is forced to the terminal tool when the workspace has exactly one terminal tool;
- is not opened after a terminal attempt, so a rejected terminal submission receives
  no hidden retry;
- cannot route through Architect, another model, a repair agent, or a fallback.

This is a lifecycle correction, not extra research budget. It applies equally to
Theory checkpoints, scientific source submission, Lean gap/proof disposition, and
Critic evaluation. Focused client-loop, Theory, scientific-code, Lean, and Critic
regressions exercise the shared boundary. No task-specific formula, source patch,
Lean grammar rule, reviewer verdict, or evaluator content enters runtime.

Future Codex mechanisms remain evidence-triggered. Context compaction is appropriate
only if durable artifact references plus recent observations no longer fit a model
window; dynamic tool discovery is appropriate only if a measured tool-catalog cost
appears; parallel tool execution is appropriate only for independent read-only
actions. None justifies a second scheduler, nested Codex threads, routine subagent
delegation, or another repair taxonomy.

## Interpreter-neutral published-source execution

The next measured gap was below the agent layer. Published-source replication used
the correct Codex-shaped ownership loop, but its pinned executor still required a
`.py` entrypoint, a Python executable, and a runtime-generated Python package probe.
That made the supposedly general research-source tool unable to execute an official
R paper example without adding an R-specific worker or bypassing provenance.

Source-execution schema v3 keeps the same tool and executor while binding a generic
runtime language, interpreter, entrypoint-prefix arguments, explicit non-secret
runtime environment, and model-visible environment probe. The manifest SHA-256 binds
the complete command contract. Security-owned environment keys cannot be overridden;
the model cannot alter the command; schema v1/v2 Python manifests remain loadable.
Runtime child executables are individually hash-bound and are both readable and
executable inside the sandbox. Forking is available to immutable published runtime
code, while process execution remains exact-allowlist-only, network remains denied,
and ordinary writes remain confined to the staged output workspace.

The mechanism was tested with the journal-distributed, unmodified 115-line R source
for Zeileis (2004), *Econometric Computing with HC and HAC Covariance Matrix
Estimators*. An explicit R 4.4.3 environment pins `sandwich`, `lmtest`,
`strucchange`, `scatterplot3d`, and `zoo`. Independent manual runs and three product
sandbox runs completed the HC/HAC, structural-change, and graphics workflow. The
successful sandbox runs had identical stdout and stderr hashes. Raw PDF hashes vary
because R embeds creation time, but all seven normalized rendered pages had identical
pixel hashes, so evaluation can compare scientific output rather than unstable PDF
metadata.

This adds no R agent, repair route, language grammar, scheduler, provider, or expected
statistical value to the product. It applies the same Codex invariant one level lower:
the harness exposes a stable executable tool and raw observation; the source-owning
model interprets the result and writes its own report.

## Task 74 validates the action loop, not the scientific prose

Task 74 consumed the first exact-Haiku product draw of that generic R mechanism at
code head `9feec25d`. The Architect handed the source-replication task directly to
one persistent source owner. Across eight turns, the same model searched and read the
official source snapshot, ran the operator-pinned R entrypoint, received raw stdout
and stderr, attempted to read binary `Rplots.pdf`, received the ordinary non-UTF-8
tool error, wrote a durable Markdown report, and committed its checkpoint. The
Critic then reviewed externalized immutable evidence. The complete run used three
outer graph steps. No source repair agent, fallback, task-specific R worker, routine
Architect route, second scheduler, model escalation, or Formalizer was involved.

One remaining control-plane mismatch was visible before that clean source loop. The
first Architect structured packet repeated a simulation target although empirical
evidence was not applicable. Runtime validation rejected it and the legacy helper
regenerated the complete Architect packet, so this nominally one-stage plan used two
model calls. Frozen task intent should remain runtime-owned while Architect emits
only substantive planning decisions and one next action. That simplification should
remove full-packet regeneration rather than adding an Architect repair worker.

The mechanical result is strong scoped evidence: the unmodified source returned 0,
all source/interpreter/environment/output identities matched, and the frozen hidden
source harness passed 12/12. The automated report evaluator also returned 10/10
`SATISFIED`, so the command reported hidden `1/1`.

Operator audit nevertheless invalidated full-task credit. The report called
`p = 0.05586` significant at the 5% level, inferred heteroskedasticity and an ordered
robustness scale from standard-error magnitudes, inferred test power from one pair of
observed p-values, added unsupported historical explanations for estimated breaks,
and claimed logical PDF reproducibility despite explicitly not inspecting the
visuals. Runtime Critic and the calibrated hidden exact-Haiku judge both accepted
those claims.

This is the important harness boundary. Codex's model -> tool -> observation -> same
model loop solved the execution and collaboration problem cleanly; it cannot make a
weak scientific author or referee correct. Adding a p-value parser, HC rule, economic
event blacklist, repair queue, another reviewer agent, or retry would overfit the
consumed output and move scientific ownership back into Python. The automated `1/1`
therefore remains immutable, but trustworthy capability credit is `0/1` and the
aggregate remains `4/74`. Exact source execution remains component evidence.

The system response is evidence discipline, not another middle layer: production may
use Sonnet for scientific roles, frozen tests/evaluations continue to expose exact
Haiku limitations, operator authority can invalidate correlated author/referee false
acceptance, and future tasks remain disjoint. Task 74 will never be rerun, resumed,
repaired, hidden-evaluated again, rescored, resampled, or supplied its hidden/operator
findings as model feedback.

The research-ladder ledger passed `72/72`; the complete repository passed `997/997`
in 82.49 seconds. Compileall, JSON, diff hygiene, secret scanning, and the unchanged
production architecture budget passed at 149,991 lines. No post-run product or hidden
evaluator model call occurred.

Commit `7d9278b769be47b2c119c08d5b63832974940afb` removes the measured Architect
regeneration dependency for future tasks. Frozen task intent now owns whether formal
or empirical evidence is applicable, so model-emitted targets outside an inactive
lane are discarded during the existing normalization step. Targets in every active
lane remain model-authored. This is control-envelope normalization, not scientific
content repair: it adds no agent, retry, fallback, task rule, or second scheduler.
Task 74's historical two Architect calls, one regeneration, automated `1/1`, and
trustworthy `0/1` remain unchanged. Architect routing passed `26/26`, Architect plus
core passed `34/34`, and the complete repository passed `997/997` in 81.39 seconds at
149,997 production Python lines. No product or evaluator model call occurred.

## 2026-08-28 upstream refresh and bounded observation fidelity

Official Codex `main` was fetched again and pinned at
[`94311d44`](https://github.com/openai/codex/commit/94311d447587411789533c47601fd8bc9d81eb48).
Since the prior `6be2a6ca` audit, `7d6f808b` refactors TUI keymap conflict checks and
`94311d44` forwards image content from the history-notes extension. Neither changes
the core model/tool action loop, tool registry, sandbox orchestrator, session
ownership, or multi-agent control boundary.

The source-level decision therefore remains selective adoption, not embedding.
Theory, Python/R, simulation evaluation, and Lean continue to use the existing
provider-neutral `ClientToolTurnRequest` and one AI Statistician `AgentRuntime`.
Importing Codex Core, App Server, its OpenAI Responses transport, thread store, or
agent scheduler would create a second conversation and orchestration owner while
violating the exact-Haiku evaluation boundary. Codex collaboration contributes one
useful principle instead: the parent model delegates only genuinely independent
work, child state remains session-scoped, and sparse messages or immutable artifact
references cross sessions. Routine compiler, interpreter, simulation, and retrieval
observations stay with the issuing source owner.

One small shared mechanism was worth adopting from Codex's centralized output-budget
discipline. Long client-tool observations previously kept only their first 60,000
characters, which could discard the final Python traceback, R diagnostic, referee
finding, or Lean goal. The common loop now truncates only the middle and records the
original character and line counts, preserving both setup and terminal diagnostics.
This is one central transport policy used by every workspace. It adds no repair
phase, retry, router, content parser, task rule, acceptance condition, or model call.

## Task 76 validates singular continuation ownership

The BOCD Gamma-Poisson L2 draw exercised the intended Codex-shaped collaboration
boundary: persistent Markdown/LaTeX Theory and Python/Simulation source owners used
stable tools, exact artifacts, and raw observations; independent reviewers received
hash-bound artifacts; Formalizer remained optional and did not run. The draw still
failed. Its theory and estimator reversed the conjugate state update, while both
independent Haiku reviewers false-accepted the core semantics. A coding-agent loop
does not make the model infallible, and more routing layers would not repair that.

The run did expose one harness defect. A valid Simulation `REVISE` handoff carried
both stale scientific-progress state and a new semantic-review continuation, so the
same source owner was blocked before another model call. Commit `b9297aef` now makes
the semantic revision supersede stale progress/replay markers and returns exact
reviewed source plus raw findings to that owner. The existing reviewer tool also
states its stable probe ABI and asks the same model to distinguish self-consistency
from an independently derived discriminating oracle. Runtime supplies no BOCD rule,
test case, source patch, retry, agent, scheduler, provider, or verdict.

This is the reusable Codex principle at the right boundary: one owner, one retained
model/tool history, stable tools, raw observations, and sparse immutable handoffs at
genuine independence boundaries. Codex Core, App Server, Responses transport,
thread storage, provider state, worktree management, and multi-agent scheduling
remain deliberately outside AI Statistician because they would create a second
runtime rather than strengthen scientific reasoning.

## Task 77 isolates two harness-owned invariants

The de-biased-Lasso L2 draw used the intended collaboration shape: persistent
Markdown/LaTeX Theory, a same-owner Python coding loop, a same-owner Simulation
authoring loop, hash-bound independent reviews, and no compulsory Formalizer. It
still ended `BLOCKED` and scored hidden `0/1`. The mathematical author and referee
made substantive KKT and remainder errors, and the estimator violated its visible
closed ABI despite accurate core numerics and 5/5 hidden empirical checks. Those are
model capability failures, not reasons to embed another orchestrator.

Read-only trace inspection refined both responsibilities. The complete frozen
contract already reached the Algorithm source owner and reviewer as
`question.estimator_execution_contract`; a compact Theory interface summary was also
described as executable authority. The Codex-like invariant is explicit precedence:
runtime-owned tool and question contracts control, while editable model summaries are
context only. No new handoff format is needed.

The authoring gate also already permits `acceptance_passed=false` after valid
execution. The later source instead returned early at the 128-replicate diagnostic,
called the required estimator zero times, and reused 128 as its future confirmatory
request. The source owner therefore needs an unambiguous tool contract: a small
diagnostic still exercises every required dependency, its scientific result may be
false, and `requested_runtime_replicates` names a future count chosen independently of
diagnostic outcomes.

This is the maximum useful reuse from the current OpenAI Codex harness for these
workspaces: centralized immutable tool authority, persistent source ownership, raw
observations, content-addressed artifacts, and clean terminal semantics. Importing
Codex Core, App Server, Responses transport, thread state, provider state, worktrees,
or its multi-agent scheduler would duplicate AI Statistician's AgentRuntime and break
provider-neutral exact-Haiku evaluation. Commit
`a2aa8428bc623d3dfb2bbc850e60088ec34f93d2` changes only the existing Algorithm,
Simulation, and independent-review prompts; AgentRuntime receives no new branch or
gate. Focused regression passed 145/145 and the complete repository passed 1002/1002
without rerunning Task 77.

## 2026-08-28 second upstream refresh

Official Codex `main` was fetched again at
[`31d338a1`](https://github.com/openai/codex/commit/31d338a1af4f79b106f01f2f3a43ac4617ea19bb),
four commits after the prior `94311d44` pin. Two commits concern Guardian score and
approval-test behavior, one separates HTTP retry-backoff integration testing, and
`dc2ccc68` makes spawned Codex agents inherit the root session's service tier.

The service-tier change reinforces one useful control-plane invariant: a root-owned
execution policy must remain coherent across delegated sessions. AI Statistician
already applies the stronger frozen-evaluation form of this invariant. One exact
evaluation model and tier are normalized at the root, every enabled specialist and
reviewer is checked against that policy before the graph runs, and any mismatch fails
closed. Production intentionally retains role-level Haiku/Sonnet selection under the
global Sonnet-or-below ceiling, so copying Codex's single service-tier implementation
would remove a deliberate scientific-resource choice rather than improve safety.

The core `run_turn`, `ToolRouter`, parallel-tool gate, and session-level collaboration
principles are unchanged in this delta. No new Codex component is adopted. In
particular, Codex Core, App Server, Responses transport, thread persistence, Guardian,
worktree management, and its agent scheduler remain outside the canonical runtime.
Theory, Python/R, Simulation, and Lean continue to share the provider-neutral
`client_tool_loop`, with one source-owning model session per workspace and sparse
hash-bound handoffs through the sole `AgentRuntime`.

The next meaningful evidence is therefore a disjoint frozen live task, not another
wrapper. It must test whether the existing Theory -> R source -> Simulation -> review
collaboration preserves one-owner raw-feedback iteration and strict evidence
boundaries. A failure may justify simplifying an existing shared interface, but cannot
justify embedding Codex or adding another scheduler, repair agent, fallback, or
task-specific rule.
