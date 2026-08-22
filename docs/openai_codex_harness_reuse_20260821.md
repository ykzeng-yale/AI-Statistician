# OpenAI Codex Harness Reuse Audit

## Upstream identity

- Repository: `https://github.com/openai/codex`
- Audited branch: `main`
- Audited commit: `343074d4207d572809bd8cea15f4be1d09d98e0b`
- License: Apache-2.0
- Read-only checkout: `/Users/yukangzengcmac/.codex/external/openai-codex`
- License SHA-256: `d17f227e4df5da1600391338865ce0f3055211760a36688f816941d58232d8dc`

The audit is commit-bound. A later Codex release is a different mechanism
snapshot and must not silently replace this identity.

The immediately prior audit was pinned at
`45a3edc02a59d845eba30794796c44e5f2377408`. The 14-commit incremental
recheck to `9949c9ea` leaves tool dispatch, multi-agent context selection, and
child spawning byte-identical. The turn loop only switches stop-hook execution
from turn context to the current step context. Other relevant changes add
bounded Guardian-review evidence, fresh parent-linked internal sessions,
allowlisted executor stop hooks, richer browser/computer-use policy, Bedrock
setup, and redacted provider configuration values. They strengthen isolation,
policy ownership, and secret handling but do not justify a second scheduler,
scientific reviewer, or provider path in AI-Statistician.

The incremental recheck from `9949c9ea` to `e6a3877e` contained one commit
limited to remote installed-plugin cache reconciliation. The latest recheck
from `e6a3877e` to `970b7f2f` contains seven commits for trace telemetry,
browser/computer policy, executor-hook tests, cancellation propagation,
granular sandbox approval, Guardian classification logging, and preservation of
strict MCP review outcomes. Every core turn-loop, tool-dispatch, multi-agent,
app-server, provider, Guardian-evidence, thread-manager, and executor-hook file
listed below remains byte-identical.

The incremental recheck from `970b7f2f` to `4f39251` contains one commit for
safe suspension of an unfinished root turn before another runtime recovers the
same turn ID. It flushes history before cancellation, refuses suspension while
a loaded descendant remains live, closes the old history writer before
announcing shutdown, and deliberately records neither completion nor abort.
All previously audited turn-loop, tool-dispatch, multi-agent, app-server,
provider, review-evidence, thread-manager, executor-hook, and MCP files remain
byte-identical. This is a distributed-ownership mechanism, not a new model
workflow or scientific scheduler.

The incremental recheck from `4f39251` to `343074d` contains one commit that
reports runtime MCP connection status through the app-server protocol and TUI.
The core turn loop, tool dispatcher, parallel-safety gate, multi-agent context
selection, child spawning, provider contract, review evidence, thread manager,
executor hooks, strict MCP outcomes, and unfinished-turn suspension remain
byte-identical. The app-server README changes only to describe the new status
field. This improves observability of an external tool connection; it does not
add a reusable scientific workspace, model loop, scheduler, or collaboration
policy.

The new strict-review change preserves canonical denial, timeout, and abort
outcomes instead of flattening them into a generic decline. That reinforces an
existing AI-Statistician rule: retain the independent referee's exact findings
and disposition, keep harness failure distinct, and fail closed when no valid
decision exists. The cancellation and approval changes strengthen environment
control, but add no reusable research workspace, scientific scheduler, theory
method, simulation policy, or Lean-proving policy.

## What Codex actually contributes

Codex has a small conceptual kernel even though its production repository is
large:

1. A thread is durable conversation state, a turn is one user-to-agent run,
   and an item is one persisted message, tool call, command, or file edit.
2. Inside a turn, the same model repeatedly selects tools and receives their
   exact outputs. A final assistant response ends the turn.
3. Tool routing separates model-actionable failures from fatal runtime
   failures. Ordinary tool failures become model observations; a fatal harness
   failure aborts instead of asking the model to repair the harness.
4. The tool runtime snapshots the advertised tool surface for a sampling step,
   preserves output order, supports concurrent safe calls, serializes unsafe
   calls, and propagates cancellation.
5. Multi-agent V2 creates isolated child threads. A child can inherit no
   turns, the last N turns, or all turns. Queue-only messages do not start a
   new child turn; follow-up tasks do. Waiting is mailbox-driven rather than
   busy polling.
6. The app-server exposes thread, turn, and item events over a bidirectional
   protocol and can attach dynamic tools, sandbox policy, and workspace roots.

Primary inspected files and their SHA-256 identities:

| Upstream file | Mechanism | SHA-256 |
| --- | --- | --- |
| `codex-rs/core/src/session/turn.rs` | same-session model/tool continuation and current-step stop context | `7499497671f04186b7c31126dbdee38c5a34a022a51b55bdefca331f778e2c66` |
| `codex-rs/core/src/tools/parallel.rs` | typed dispatch, ordering, cancellation, fatal boundary | `48380e25abaf9c52e7a5de9cecf82cc4ddb84197683f73a11719de3b78c90e5a` |
| `codex-rs/core/src/session/multi_agents.rs` | context-selective child agents and mailbox guidance | `44197c5fb2b32ec158c5488b419141e9e626614c64d524b6a2a90500a272f53f` |
| `codex-rs/core/src/tools/handlers/multi_agents_v2/spawn.rs` | zero/N/all-turn fork policy | `3bb8b56b430c095bea3f7e1ccebb9a73d2c889786a281942bb0cd2ca676a1300` |
| `codex-rs/app-server/README.md` | thread/turn/item protocol, dynamic tools, managed policy, and MCP status reporting | `2cf7963a9e3c66d2e82a2f2be2f3ef73103384e8f8c48654d359f0c022508d2d` |
| `codex-rs/model-provider-info/src/lib.rs` | provider transport contract with redacted secret-bearing values | `2168b93576dff1d336f0c3d390b6ff8c38376340fc8ed2eea8da9857ddb1eeb7` |
| `codex-rs/core/src/context/guardian_review_evidence.rs` | bounded, runtime-only, authorization-bound review evidence | `b0d5cafa5529dd0ae55a44d3933a175b4d0999d73e78dc7963c1d2781088279f` |
| `codex-rs/core/src/thread_manager.rs` | fresh parent-linked internal sessions | `3bbbd6f2c68cacc1f652e57493ac15a560b2d7da2f93f797ad492d794f4e8c9d` |
| `codex-rs/core-plugins/src/executor_hooks.rs` | identity-allowlisted executor cleanup hooks | `fbdc87934d9dae73014f626dd079989986c1b1e8bcc8d068cb6f1d4fc555463a` |
| `codex-rs/core/src/session/mcp.rs` | canonical strict-review outcome propagation | `65d807c77eb76c9c6f61a27c56ae943d052e50b1966674f721f02e6a42433e44` |
| `codex-rs/core/src/session/turn_suspension.rs` | flush, descendant guard, writer close, and recoverable unfinished-turn handoff | `6b2b3be42758d1da86a6d56d823b1be886426892e54ae37a43caddb8b74f0a5d` |

## Best-leverage decision

The useful unit of reuse is a mechanism, not the whole binary:

- Keep AI-Statistician's provider-neutral `client_tool_loop` as the shared inner
  harness for TheoryDeveloper, Python/R authors, SimulationEngineer, the
  independent referee, and Formalizer. It already implements the Codex-shaped
  model -> tool -> exact observation -> same-model continuation cycle.
- Keep one outer `AgentRuntime` because scientific task intent, immutable source
  policy, independent review, confirmatory blinding, and proof authority are not
  coding-thread concerns supplied by Codex.
- Give each source owner a persistent artifact workspace and generic domain
  tools. Ordinary source or compiler failures stay with that owner; only a
  model-selected, hash-bound cross-workspace defect becomes a handoff.
- Fork independent reviewers with artifact-only context, analogous to a Codex
  child with no inherited turns. Never share author hidden reasoning or
  evaluator-only files.
- Treat model context compaction as a transport optimization. Authoritative
  mathematics, source, raw diagnostics, and reviewer findings remain in
  content-addressed files and references rather than in a lossy summary.

Directly embedding Codex app-server would duplicate thread state, scheduling,
tool persistence, permissions, and provider transport. Its Python SDK is a
client for that app-server, not a provider-neutral library containing a small
agent loop we can import. Because AI-Statistician must use Claude Haiku/Sonnet,
direct adoption would additionally require replacing the provider or building
an Anthropic-to-Responses proxy. That is more harness, not better research.

### Unfinished-session handoff decision

The new upstream suspension primitive is correct for a runtime that transfers
one active turn between workers. AI-Statistician currently has one owning
process per research run. At its bounded outer edge it already records an exact
`RuntimeAgentTaskContinuation` without marking the pending scientific task
accepted, failed, or aborted; Theory, scientific-code, reviewer, and Lean
workspaces also bind resumable progress to immutable predecessor checkpoints.
There is therefore no measured concurrent-writer failure for a Codex-style
suspension service to replace today.

Do not add a lease manager, heartbeat, writer process, or app-server merely to
imitate the upstream API. If AI-Statistician later permits two workers to take
ownership of one active run, the adoption gate is concrete: flush authoritative
artifacts, reject transfer while a child workspace is live, atomically fence the
old owner, close its writer, and recover the same task and workspace identities
without a terminal scientific disposition. That mechanism should replace the
then-measured handoff code behind the existing provider-neutral checkpoint
boundary; it must not become another research planner.

### Canonical role rematerialization

Codex does not justify separate harness implementations for each scientific
role. AI-Statistician rematerializes one shared inner loop with different
workspace tools and evidence visibility:

| Role | Persistent authority | Model-owned loop | Cross-role output |
| --- | --- | --- | --- |
| TheoryDeveloper | Markdown/LaTeX claim and derivation files | read, write/edit, source lookup, Python/R scratch, checkpoint or honest gap | document and compact claim/ABI references |
| AlgorithmEngineer | exact Python/R estimator source | replace source, execute, read raw sandbox result, revise or report a hash-bound dependency defect | independently reviewed source and ABI reference |
| SimulationEngineer | exact Python/R experiment source plus frozen metric contract | execute against injected reviewed estimator, inspect raw or blinded observations, revise its own source or explicitly return a dependency defect | exploratory or confirmatory evidence artifact |
| Formalizer | exact Lean source in one pinned project | inspect goal/context, task-bound RAG, edit, compile, and iterate from raw diagnostics | optional formal status or kernel-checked evidence |
| Independent reviewer | isolated report workspace | inspect immutable author artifacts and permitted sources without inherited author turns | exact findings and disposition, never a repair |

The outer `AgentRuntime` communicates these roles through content-addressed
references and only arbitrates task intent, visibility, evidence authority, and
genuine ownership conflicts. Routine compiler, sandbox, retrieval, or review
feedback stays in the source owner's loop. This is the useful Codex composition:
one generic coding-agent interaction model, several domain workspaces, and no
second agent framework around them.

## Fit with AI-Statistician

AI-Statistician already has the correct two scales of control:

- `AgentRuntime` is the outer scientific evidence graph. It owns task intent,
  artifact identity, independent review, routing across research domains, and
  final evidence status.
- `client_tool_loop` is the inner coding-agent loop. The source-owning model
  selects tools, receives raw observations, and revises Theory Markdown,
  Python/R source, simulation source, or Lean source in the same context.

Codex therefore validates the inner-loop direction; it does not justify
placing another Codex thread manager around `AgentRuntime`.

### Adopted now

1. Unknown tool-runtime exceptions fail immediately through a secret-free
   `ClientToolRuntimeError`. They are not converted into a fake observation
   that asks TheoryDeveloper, AlgorithmEngineer, Simulator, or Formalizer to
   repair runtime code. Declared model-actionable input errors and explicitly
   classified, secret-free environment failures may return as tool observations;
   the owning model can change its action or report a gap, but no repair layer
   edits the harness.
2. Read-heavy Theory and Lean workspaces permit multiple independent model
   tool calls in one provider turn. The model may batch independent reads,
   searches, or inspections; runtime still processes side effects in stable
   order, and terminal actions must remain last.
3. Scientific source execution stays observation-sequential. A revised Python
   or R program must see the prior execution result before another candidate
   is generated; parallel speculative submissions would spend execution
   evidence without feedback.
4. Theory author stopping is model-owned. The complete document write and its
   exact tool result already remain in the same client-tool session, so runtime
   no longer forces the author to reread every line at the final document hash
   before requesting independent review. Model-chosen reads remain recorded,
   while the isolated referee must inspect authoritative theory through separate
   hash-bound tools and cannot accept from the structured index alone.
5. Python and R source workspaces now survive an exhausted inner tool-loop
   segment without regenerating their planning envelope. The next outer-runtime
   step returns the exact content-addressed source and its raw execution
   observation to the same AlgorithmEngineer or SimulationEngineer. Accepted
   sibling sources are referenced without re-execution, and a continuation is
   authorized only after a new sandbox check. A stale checkpoint, changed hash,
   overlapping continuation, or no-progress lineage fails closed before a model
   call; ordinary source continuation never routes through Architect.
6. Referee-driven TheoryDeveloper revision no longer has a separate one- or
   two-round cap. The independent reviewer and TheoryDeveloper can continue
   through the existing outer AgentRuntime budget while the immutable finding
   ledger shows scientific progress. Runtime derives progress from prior
   findings marked resolved or retracted; merely adding a new finding while an
   old one remains unresolved is stagnation and stops before another theory
   model call. Revision count remains lineage telemetry, not a second budget.
7. Lean source workspaces now survive an exhausted inner tool-loop segment as
   one same-owner session. The checkpoint binds the immutable parent, exact
   current source, declaration, raw Lean diagnostic, latest RAG/proof-state
   observations, checked candidates, and observed-progress identities. The
   next outer step carries only a content-addressed observation reference; it
   does not regenerate a Formalizer packet or route through Architect. A
   tampered, stale, overlapping, or observation-free continuation stops before
   another provider call.
8. The independent theory referee now has the same durable-session semantics.
   When one inner segment ends after real document inspection, task-bound source
   retrieval, scratch execution, or terminal-validator feedback, AgentRuntime
   stores one content-addressed checkpoint and returns it to the same isolated
   reviewer in the next outer step. The checkpoint retains only exact
   model-visible observations, cumulative environment budgets, coverage refs,
   and immutable theory/material bindings; the task carries one
   `RuntimeArtifactRef`. It never copies author reasoning, asks Architect to
   replan, edits the referee report, or treats partial review work as acceptance.
   Tampering, a stale predecessor, repeated observations, or an observation-free
   segment stops before another reviewer call.
9. A TheoryDeveloper session reserves one control-plane terminal disposition
   after its unchanged environment-action budget. A final valid document write
   can therefore be followed by the same model's explicit checkpoint commit or
   gap report instead of being stranded by the tool-call counter. The reservation
   adds no research action, turn, retry, or runtime-authored stopping decision.
10. Executable scientific tasks freeze one compact, model-visible estimator ABI
    before the first model call. The same contract reaches the Theory, Python/R,
    Simulation, review, and Critic contexts, while schema-v2 hidden checks cite
    its stable public clauses and remain isolated after runtime termination. A
    task with hidden empirical assessment adds only public `empirical_claims`;
    general theory remains Markdown/LaTeX rather than an ABI claim taxonomy.
    Agent outputs do not copy the full contract. This applies Codex's stable tool
    surface and exact observation-binding principle to scientific evaluation;
    it does not ask runtime to interpret statistics or repair model source.
11. Confirmatory simulation precision is now model-owned. The pre-execution
    metric-planning model selects one replicate count for the shared portfolio,
    explains its Monte Carlo precision in the existing requirement rationales,
    and an isolated reviewer checks that choice before outcomes are available.
    AgentRuntime preserves the accepted count exactly through Simulation source
    authoring and execution. Runtime supplies only a wall-clock limit and a high
    sandbox safety ceiling; neither is a statistical default. Exploratory runs
    retain their separate operator-selected fallback.
12. Public literature and repository discovery now follows Codex's dynamic-tool
    boundary without adding a Scout agent. The existing TheoryDeveloper model
    chooses a query, receives bounded Crossref or GitHub metadata, selects an
    opaque result handle, and reads exact source text in the same transcript.
    GitHub file reads are pinned to a concrete commit no later than the explicit
    source horizon. Runtime owns the two fixed API hosts, secret isolation,
    horizon, byte bounds, hashes, and citation refs; it does not choose the query,
    source, interpretation, or next research action. The implementation uses the
    official [Crossref REST API](https://www.crossref.org/documentation/retrieve-metadata/rest-api/)
    and [GitHub REST API](https://docs.github.com/en/rest) directly behind the
    existing model-neutral client-tool executor. Live discovery is scouting
    evidence only and is rejected for the frozen cross-family protocol; strict
    historical evaluation and exact replication still require an operator-frozen
    `ResearchSourceSnapshot` and execution manifest.
    A declared public-API failure is returned to the same TheoryDeveloper as a
    bounded error observation, so it can choose another source or continue with
    an honest gap. Unknown provider exceptions still terminate as harness faults;
    there is no automatic retry, fallback query, or source-repair agent.
    The independent theory referee receives the same optional two-tool surface in
    a separate provider session whose opaque handles are not shared with the author.
    The referee chooses its own query and source; search metadata has no citation
    handle, and only exact content the referee elects to read becomes a hash-bound
    `S#H#` observation. The source body stays in the active model transcript (and an
    exact resumable checkpoint when needed), while final review evidence retains the
    provider, horizon, revision, path, full-content hash, visible-content hash, and
    citation identity without copying the body. This reduces author source-selection
    bias without adding a reviewer, route, retry, automatic search, or proof claim.
13. The independent referee's substantive report is now a model-owned Markdown
    workspace rather than one large terminal JSON string. The same isolated model
    can write the complete report, read exact line ranges, apply hash-bound local
    edits after another reasoning step, and finally submit only the current report
    SHA plus compact statuses and findings. A checkpoint carries only the draft
    manifest and validates the file before continuation; it does not copy the report
    body. A stale hash returns to the same referee as an actionable tool observation,
    while a missing or tampered draft fails before acceptance. This adds no reviewer,
    model turn allowance, retry, scheduler, or runtime-authored mathematical action.
14. Theory, Algorithm, Simulation, and Lean source owners now persist their exact
    model-visible client-tool transcript as an immutable content-addressed session
    artifact. A progress checkpoint carries only a compact session reference. The
    next same-owner segment verifies the model, system prompt, tool names and
    terminal semantics, verifies the transcript bytes and hash, restores every
    prior assistant tool call and raw tool result, then appends the continuation
    objective. It does not reconstruct context from a repair packet or ask Architect
    to summarize the failure. Dynamic artifact schemas may change as the workspace
    grows without changing session identity; switching model, system prompt, tool
    identity, transcript bytes, workspace, or owner fails before another model call.
    Independent reviewers still receive artifact-only context and never inherit an
    author's transcript.
15. The independent theory referee now chooses its own document context in the same
    way that a Codex coding agent chooses files and ranges. Runtime still requires at
    least one exact read of authoritative theory, records every range and hash, and
    rejects acceptance from the structured handoff alone, but it no longer requires
    exhaustive line coverage of every document. The review prompt asks the model to
    identify and try to falsify the load-bearing dependency chain, instantiate any
    invoked standard result in the candidate's notation, and mark materially unchecked
    claims `UNCERTAIN`. Ordered claim statuses remain a compact disposition index; the
    Markdown report carries the actual mathematical argument. One uninterrupted review
    segment now permits twelve tool turns instead of five, so ordinary reads, source
    lookup, scratch work, and report editing do not require an outer AgentRuntime
    checkpoint. This removes a deterministic context-selection rule and adds no agent,
    scheduler, formula check, reviewer vote, or runtime-authored mathematical result.
16. Canonical referee sampling no longer duplicates the legacy structured derivation,
    equation, assumption, sanity-check, theorem-card, and lemma-card bodies beside the
    authoritative document catalog. The prompt keeps the research question, task
    contract, compact claim/dependency slots, and estimator/simulation interface; the
    same model obtains mathematical bytes through exact document reads or an available
    model-directed compact search. The full structured artifacts remain content-addressed
    for runtime identity and tool retrieval. A deterministic reconstruction of the
    consumed exponential-rate artifact produced a 23,835-byte sampling prompt while
    omitting or tool-gating 16,697 bytes of duplicated structured-anchor content. This
    changes context projection only and does not reinterpret, repair, rerun, or rescore
    that artifact.

These changes add no mandatory model call, retry, reflection turn, agent,
scheduler, model tier, statistical formula, Lean grammar rule, or repair recipe.

Codex ordinarily lets a final assistant message end a turn. AI-Statistician keeps
small typed terminal tools where the product must distinguish a proposed theory
checkpoint, an honest unresolved gap, a reviewed scientific-source handoff, and a
formal gap. Those tools do not diagnose or repair content. They bind the model's
disposition to the exact current artifact hash so independent review and kernel
authority cannot be inferred from free-form prose. This is an intentional evidence
boundary divergence, not a second reasoning layer.

### Live implication

The frozen jackknife-mean L0 draw provided a direct harness counterexample. Its
last successful theory write was valid and commit-ready, but the shared tool-call
counter reached zero while one provider turn remained. The next model-selected
terminal action was rejected before execution. Code commit `0d8a01e5` now keeps
one terminal disposition outside the unchanged research-action allowance.

This is the narrow Codex-style principle worth reusing: one same-session model
receives exact environment observations and remains responsible for ending its
own turn. AI-Statistician still retains `AgentRuntime` as the only outer
scientific scheduler and Claude as the required provider path. Codex thread,
app-server, Responses transport, and multi-agent persistence are not imported.
The consumed task remains `0/1`; deterministic regression cannot rescore it.

The later paired ratio-of-means L0 draw showed that the caller-local `+1` was
not a true reservation. Its final ordinary write was valid and commit-ready but
consumed that nominal slot; the following exact-Haiku response returned one
terminal tool call, which the shared global call guard rejected before dispatch.
Commit `3bfa8daa378480fdd1e11acae3b229abf3abd3d7` restores the intended
Codex-style lifecycle at the shared-loop boundary: ordinary environment actions
have one budget, while one same-session terminal disposition and any explicitly
configured same-session terminal retries have a separate control-plane budget.
Nonterminal tools remain visible for prompt-cache stability but cannot execute
after action exhaustion. Theory and Lean no longer emulate terminal capacity
with caller-local arithmetic.

This corrects the earlier audit's overstatement that commit `0d8a01e5` had
already placed terminal disposition outside the action allowance. That commit
only enlarged one caller's undifferentiated count. The paired-ratio draw remains
an immutable `0/1`; `151/151` caller tests and the `812/812` full suite are
mechanism evidence, not permission to rerun or rescore it.

### AR1 live validation

The frozen stationary-AR(1) L0 draw exposed a second, more general harness
counterexample. Simulation source intentionally called the accepted estimator
on an all-zero series and handled its `ValueError` as an expected domain
rejection. The callback wrapper changed that exception into a runtime-specific
type, and the outer runtime then classified every caught estimator exception as
an AlgorithmEngineer defect. This overrode the consumer model's own executed
program and caused repeated AlgorithmEngineer/SimulationEngineer handoffs until
the outer iteration budget was exhausted.

Code commit `dd3d09bfbf02565a97fcb588a573a5d178d9da34` applies the Codex-style
boundary directly:

- a bound Python or R dependency preserves its original exception inside the
  consuming sandbox;
- an exception handled by model-authored consumer source remains an ordinary
  consumer program result;
- only an exception escaping the sandbox is an unhandled execution failure and
  returns as a raw observation to the same SimulationEngineer session;
- cross-workspace handoff occurs only when that model explicitly invokes
  `report_bound_dependency_failure` with the exact accepted source identity;
- runtime verifies artifact IDs and hashes but does not infer scientific defect
  ownership from exception syntax.

The exact frozen estimator and third simulation source were replayed only as a
deterministic mechanism check. The fixed callback executed 75 estimator calls,
preserved the expected zero-series rejection, and left a separate failed
constant-series assertion visible as a Simulation-owned source defect. The
affected panel passed 137 tests, the ladder panel passed 14 tests, and the full
suite passed 793 tests. The frozen draw remains `0/1`; the replay is not a
rerun, rescore, or capability claim.

This is also the collaboration rule for Theory, Python/R, Simulation, and Lean:
raw observations stay with the source-owning model unless that model explicitly
reports a hash-bound dependency defect. There is no deterministic content
router, repair agent, task-specific exception table, new retry, or additional
scheduler.

The same boundary applies to confirmatory design. Runtime may verify that the
fresh portfolio names one positive execution count and that the sandbox can
accept it, then copy that exact model decision into evaluator ABI rows. It may
not choose 80, 100, or any other scientific precision on the model's behalf.
The planning model and independent reviewer own that decision before execution;
a mismatch or unsupported precision fails closed without an outcome-informed
rewrite.

### Fisher-z live validation

The frozen Fisher-z L0 draw is the first direct live validation of the current
Codex-style Theory and Algorithm loops together. TheoryDeveloper received a
failed localized document edit as a raw observation and corrected the document
in the same session. AlgorithmEngineer received a real sandbox traceback for a
nonexistent SciPy import, submitted a new complete source in the same session,
and reached independent code acceptance. Neither path invoked a RepairAgent or
routine Architect route.

The run also establishes the limit of harness reuse. The isolated exact-Haiku
referee used six tool turns, read the complete theory document, ran one
model-authored scratch program, searched the frozen source snapshot, and still
false-accepted incorrect Gaussian moment covariances and an unsupported decisive
delta-method step. Codex-style observation binding can make mathematical work
inspectable and iterative; it cannot turn model judgment into proof or replace
model capability. Adding a formula parser, another vote, or a post-hoc repair
agent would violate the intended boundary. Production may use Sonnet, while
frozen capability tests remain exact Haiku as required.

The terminal metric failure exposed a separate interface defect. One
portfolio-level model decision was repeated in every row, and exact Haiku chose
5,000 replicates for six rows and 300 for two invariant rows. Commit
`fbea1af3edee3de033f29dfd79e622ed213b8495` moves that choice to one top-level
fresh response field and copies it unchanged into evaluator rows. The affected
panel passed 129 tests and the full suite passed 805 tests. No retry, model call,
statistical default, frozen-path change, rerun, or rescore was added; Fisher-z
remains `0/1`.

The false acceptance also exposed a harness limitation in the old referee output
surface: six turns of mathematical work ended by regenerating the entire report as
one terminal JSON field. Commit `c2239ea9` gives that same referee an isolated,
hash-bound Markdown report workspace and leaves only a compact SHA/status envelope
at the terminal boundary. This makes long reasoning locally editable and resumable;
it does not repair the Fisher mathematics, change the model, add another vote, or
claim that document iteration improves correctness. The affected 139-test panel and
the full 808-test suite pass; the consumed Fisher candidate remains `0/1` and all
seventeen scored tasks remain `0/17`.

A later cross-run audit of the Fisher-z and exponential-rate traces found a narrower
shared attention-allocation defect: exhaustive line coverage and a short tool segment
encouraged broad paraphrase while both reports waved through their decisive transition
as standard algebra or standard asymptotics. The current correction removes exhaustive
coverage, gives the same isolated model a longer uninterrupted session, and focuses its
prompt on a model-selected load-bearing chain and attempted falsification. It does not
encode either task's formula or assert that exact Haiku will now judge the mathematics
correctly. The frozen runs remain unchanged failures; only future disjoint tasks can
provide capability evidence.

### Exponential-rate live validation

The frozen exponential-rate MLE L0 draw is the clearest end-to-end validation of the
current Codex-shaped source loops. TheoryDeveloper recovered from a hash-bound edit
error in its own Markdown workspace. AlgorithmEngineer submitted source that failed a
real sandbox execution, received the raw observation in the same exact-Haiku session,
rewrote the complete source, executed successfully, and then used a distinct terminal
commit. SimulationEngineer likewise executed and committed its own source. Independent
reviewers received exact artifacts without inherited author turns, all eight runtime
metric contracts passed over 65,020 estimator calls, and formalization remained
nonblocking because task intent marked it not applicable.

Frozen post-termination gold still rejected the full task. The active theory applies
total-sample Fisher information inside a `sqrt(n)` limit and produces a limit variance
that still contains `n`, while calling the next correct standardized display
equivalent. Both the isolated referee and Critic false-accepted that inconsistency. The
estimator formulas and hidden empirical checks passed, but source coercion accepted a
boolean sample entry contrary to the public ABI; the one-shot code reviewer missed it.

This result sets the correct reuse boundary. Codex-style tool binding supplies durable
workspaces, exact observations, same-owner revision, isolated review context, and clear
harness-failure separation. It does not supply mathematical judgment or guarantee that
two calls to the same small model are independent in capability. At the time of that
run, no formula parser, boolean special case, extra vote, retry, prompt patch, rerun, or
rescore was added. The task remains immutable `0/1`, and the ladder becomes `0/21`.
The later generic referee context-selection correction described above does not repair
or rescore this artifact.

### Reused collaboration semantics

| AI-Statistician relation | Codex analogue | Required policy |
| --- | --- | --- |
| Same Theory/Python/R/Lean owner continues after raw feedback | another tool cycle or follow-up turn on one thread | retain the exact owner and workspace identity |
| Same owner resumes long mathematical work | resumed thread/follow-up task | load the hash-bound checkpoint and changed document ranges, not a copied semantic packet |
| Independent theory or code review | child with `fork_turns=none` | provide immutable artifact/source refs, never the author's hidden reasoning transcript |
| Algorithm or simulation consumes stable theory | queue-only message plus artifact | send a content-addressed ABI and claim refs; do not copy the full workspace |
| Simulation exposes a theory defect | follow-up task to the owning workspace | return the raw observation and bound artifact hashes; Architect is used only for a genuine ownership conflict |
| Optional Lean scout | isolated child over a stable theorem checkpoint | it may report formal status but cannot block non-formal evidence dimensions |
| Deep Lean proof | persistent source-owning coding thread | use goal, diagnostics, task-bound RAG, source edits, and kernel checks in one loop |

The independent reviewer and hidden evaluator must not adopt Codex's ordinary
shared-directory assumption. They require explicit visibility roots and
artifact-only inputs so author source, evaluator gold, and private results do
not become mutually visible.

## What is deliberately not imported

The current `openai_codex` Python SDK launches or connects to Codex app-server,
and the audited provider layer supports the Responses wire API. Directly using
it would replace the required Claude Haiku/Sonnet path or require a new
Anthropic-to-Responses proxy. It would also create a second scheduler and a
second persistence authority beside AgentRuntime.

Therefore this snapshot does not add:

- an `openai_codex` runtime dependency;
- an OpenAI model call or provider fallback;
- Codex thread state as a second scientific blackboard;
- shared author/reviewer/evaluator filesystem access;
- automatic subagent spawning for routine handoffs;
- a generic shell with access to evaluator-only artifacts.

The Rust sandbox, app-server, and MCP host remain future reuse candidates only
if they can be consumed behind the existing model-neutral tool executor and
visibility policy. They must replace measured local code, not wrap it.

## Next evidence gate

This adoption is a harness correction, not a capability result. It requires
deterministic regression proving that:

- declared model-actionable errors still return to the same model;
- an unexpected executor exception ends the loop before another model call and
  does not expose its message;
- multi-call turns retain call order and exact observation binding;
- Theory and Lean advertise multi-call turns while scientific source execution
  remains sequential;
- all frozen research outcomes remain unchanged.

No consumed benchmark may be rerun to claim that this mechanism works.

The visible-executable-contract correction has focused regression evidence only.
It validates stable public clauses, exact runtime and prompt propagation, legacy
question compatibility, evaluator identity binding, and fail-closed rejection of
unstated hidden-check semantics. A hidden empirical check must additionally cite
one of the compact public `empirical_claims`; no general theory schema was added.
Structural clause references remain provenance, not proof that a hidden check is
scientifically entailed; that preactivation audit and independent harness
calibration remain operator responsibilities. All nineteen scored tasks are
consumed and closed. No new live draw is authorized until a future unrelated
task is frozen and pushed under schema v2 before its first model call.

The deterministic continuation regression is complete at code commit
`9de34cf231b59f35985170775314834eeeebaf2d`: Algorithm and simulation both
resume with zero new planning calls and one same-owner source call; checkpoint
tampering and no-progress lineage are rejected. The focused workspace/runtime
panel passed 121 tests and the full local suite passed 769 tests. This is
mechanism evidence only: no model call, frozen-task rerun, scientific acceptance,
hidden-gold credit, or Lean proof credit was produced.

The theory-continuation correction is regression-validated at code commit
`fbc59a5fea8fca5bd99852d995ae68057ffddb83`. The redundant runtime config,
CLI flag, prompt budget, binding limit, and special reserved-revision exception
were deleted. A round-eight lineage that closes its prior finding continues to
round nine, while a lineage that closes none stops immediately. The affected
panel passed 229 tests and the full local suite passed 770 tests. No model call
or frozen-task rerun occurred, so this supplies no mathematical or E2E credit.

The Lean-continuation correction is regression-validated at code commit
`a1f47e08`. A two-segment source session restores the exact failed source,
compiler stderr, and formal-environment search result; the second segment does
not recheck or reinterpret the parent and retains its original parent hash.
Runtime continuation uses the same Formalizer and one hash-bound observation
reference, while content tampering and no-new-observation lineage fail closed.
The Lean/AgentRuntime panel passed 111 tests and the full local suite passed 773
tests in 72.97 seconds. No model call, benchmark rerun, theorem proof, hidden
evaluation, retry increase, turn increase, or new scheduling layer occurred.

The independent-referee continuation is regression-validated at code commit
`d64fd895`. A two-segment review restores the exact prior Markdown read, source
handle, and terminal-validator observation, then permits the same reviewer to
submit a complete review without rereading or regenerating its context. A real
`AgentRuntime` integration resolves the checkpoint through the blackboard,
calls the referee twice, and calls Architect planning zero times. Content
tampering and no-new-observation lineage fail before a provider call. The full
local suite passed 776 tests in 72.25 seconds. No live model call, frozen-task
rerun, retry or turn increase, mathematical acceptance, hidden-gold credit,
empirical credit, or proof credit was produced.

The model-authored confirmatory-precision correction is regression-validated:
the compact author schema preserves a 7,300-replicate model choice, inconsistent
portfolio counts and counts beyond the sandbox safety capacity fail closed, the
independent review prompt distinguishes scientific precision from runtime
capacity, the accepted contract replaces only the confirmatory execution count,
and Simulation source plus execution receive that exact count. The focused panel
passed 197 tests and the full local suite passed 795 tests in 64.59 seconds.
No model call, frozen-task rerun, result inspection, new agent, retry, outer
iteration, statistical formula, Lean rule, or capability credit was produced.

The model-owned referee-report workspace is regression-validated at code commit
`c2239ea9`. One deterministic exact-Haiku transport fixture writes, reads, locally
edits, and submits the same Markdown report by hash; another receives a stale-hash
error and corrects the edit in the same session. A two-segment review submits the
restored draft without rewriting it, report prose is omitted from checkpoint and
persisted history, and external draft tampering stops before a provider call. The
focused and adjacent panel passed 139 tests and the full local suite passed 808 tests
in 64.54 seconds. No Claude call, benchmark rerun, task result, mathematical
acceptance, empirical credit, or proof credit was produced.

The exact claim-DAG handoff is regression-validated at code commit `6c850df7`.
Document-native TheoryDeveloper packets now retain their complete compact claim
index when rich legacy prose rows are capped. AlgorithmEngineer,
SimulationEngineer, and Formalizer receive one shared model-facing envelope,
`referenced_claim_ids` plus rationale, whose provider schema enumerates exact
current identities. The runtime resolves declared prerequisites for independent
generated-code review; it does not infer mathematics or repair an unsupported
reference. Historical four-list fuzzy alignment remains old-artifact read
compatibility and is absent from canonical document-native prompts.

An immutable replay of the consumed Fisher-z Theory packet now exposes all 12
claims and 12 dependency edges instead of the first three definitions. Selecting
`est_fisher_pearson_z` resolves to that claim and its two declared definitions. The
focused document/scientific-schema panel passed 41 tests, Formalizer/reviewer
compatibility passed 31, runtime/estimator compatibility passed 75, and the full
suite passed 809 tests in 64.45 seconds. `research_agent_runtime.py` remains 24,999
lines. No Claude call, consumed-task rerun, mathematical acceptance, empirical
credit, Lean proof, or E2E credit was produced; Fisher-z remains `0/1` and the
scored ladder remains `0/17`.

The model-owned symbolic-scratch extension is regression-validated at code commit
`c109cedb`. The existing Python/R theory scratch tool, used by both TheoryDeveloper
and the isolated referee, now exposes SymPy 1.14.0 and its pinned mpmath dependency
through Pyodide 314.0.2. Package preparation caches the exact wheels; generated
execution still has no network, secrets, or general host filesystem. The same model
authors the expression and complete source, receives the raw observation, and decides
whether and how to revise its Markdown/LaTeX argument.

The seven-part review protocol remains seven parts. Its existing counterexample
clause now asks the model, when computation is useful, to challenge the disputed
intermediate claim or dependency transition rather than treating a final estimator
or output-distribution simulation as validation of upstream algebra. This is prompt
and tool capacity, not a symbolic validator or mandatory ritual. A real isolated
SymPy execution passed, the focused theory/scientific/referee panel passed 133 tests,
and the full suite passed 810 tests in 67.07 seconds. No Claude call or frozen rerun
occurred, so no theory, empirical, proof, or E2E credit is claimed.

The scalar control-variate draw then supplied live evidence for both the terminal
disposition and artifact-projection principles. After all ordinary theory actions
were spent, the same exact-Haiku session successfully committed through its reserved
terminal disposition. Theory review, algorithm execution and independent review,
and metric review completed. The first Simulation planning request nevertheless
failed before generation because a complete 4.7 MB accepted handoff, including
4,000 raw smoke-result rows, was recursively copied into generic environment
feedback as well as represented by the intended compact handoff. The resulting
prompt contained 1,130,071 tokens.

Commit `dd3cb36c236e360c52f397998464997b0c08c7c8` applies Codex's bounded
sampling-context principle at that measured boundary. Exact source and raw outcomes
remain authoritative content-addressed artifacts. The execution handoff keeps exact
reviewed source plus immutable hashes but references smoke outcomes by hash; the
Simulation model receives one identity/hash/ABI projection and no source or historical
outcome bytes. The runtime still injects and executes the exact reviewed source.
An immutable replay reduced 6.8 MB of live feedback to a 45,314-byte prompt while
preserving the full ABI and hashes. Two pathological regressions and the full 815-test
suite passed. No second scheduler, provider, router, repair layer, model call, retry,
budget increase, task rule, or statistical content was added. The consumed task
remains `0/1` and was not resumed or rescored.

### Persisted tool-trace implication

The same immutable scalar run exposed a second, narrower artifact-boundary
violation after model sampling was fixed. Its scientific executor had already
written exact result artifacts and bound them by output paths and hash, but a
3,215,807-character stdout value was copied into both the persisted runtime trace
and the separate tool-call ledger. This did not alter model behavior, but it made
two audit views carry another roughly 6.6 MB of duplicate payload.

Commit `bd8961ab38c157e25a7fd323a017ecc5b7a9a550` keeps complete tool
observations in the source-owner runtime and full execution artifacts. Compact
trace serialization retains bounded head/tail text, exact text hash, character
and UTF-8 byte counts, truncation status, output paths, and output hash. It may
bound text only when both external output locations and identity exist; a large
observation without external authoritative output remains exact inline. The
separate tool-call ledger now derives from this same compact trace rather than
copying the full in-memory call again.

An immutable replay reduced the largest scalar tool record from 3,370,158 to
18,379 bytes and the complete ten-row trace from 3,440,322 to 89,326 bytes, a
38.51x reduction. The focused panel passed 18 tests and the full suite passed
816 tests. No prompt, feedback loop, model call, agent, scheduler, provider,
budget, scientific content, evaluator result, proof status, or frozen score
changed; the ladder remains `0/19`.

### Scientific-source disposition implication

The consumed Pearson multinomial draw exposed the next concrete Codex-style lifecycle
boundary. AlgorithmEngineer submitted source that executed successfully at the process
level, but the old submission tool terminated its model workspace immediately. The
model therefore never received a later turn in which to inspect the exact execution
observation, including its own failed smoke diagnostic, before the source advanced.
Runtime parsing of arbitrary nested diagnostic fields would have replaced model judgment
with another content rule; a separate repair worker would have split source ownership.

Commit `f4fe83ed539046c4de3c8eeb7444f5bdd13428ba` instead keeps one source-owning
session: submit exact source, execute it unchanged, return the raw observation, then let
that same model revise or explicitly commit the unchanged accepted hash on a later turn.
A submit-plus-commit in one model response is rejected because no observation has yet
entered the transcript. Included dependency outcomes remain exact-hash validated, while
deliberately withheld outcomes retain only a nonempty content reference and cannot be
reconstructed as an empty payload.

This reuses Codex's turn/tool/observation principle inside the existing provider-neutral
loop. It imports no Codex provider, app-server, thread manager, scheduler, repair layer,
or scientific rule. Lifecycle and immutable-ledger regressions are included in the full
`819/819` passing suite. The Pearson run remains immutable `0/1`; the correction is
eligible only for a newly frozen, disjoint task.

### Executable-ABI implication

The consumed exponential-rate draw exposed a different harness overreach rather
than an execution-loop defect. After TheoryDeveloper had already authored the
mathematics in its persistent Markdown/LaTeX workspace, a second structured phase
required it to restate every output's sample-size order and a typed polynomial/log
rate decomposition. Those fields were validated, copied through prompts, and
reviewed, but no Python/R executor, metric calculation, proof gate, or evaluator
used them as executable semantics. They created a second, less expressive
mathematical authority that could disagree with the document.

Commit `a0271fde7a5d2a32106a3d4c13b7aa6517ad89dc` applies Codex's
tool-contract boundary to that interface. New estimator ABIs contain request name,
meaning, and lifecycle binding plus response name, meaning, normalization, and one
exact derivation reference. Asymptotic orders, rates, theorem conclusions, and
their arguments remain only in model-owned theory documents. The canonical author
schema and fallback validator both reject mathematical metadata in a new ABI.
Legacy packets remain readable for audit, while preflight and Simulation prompts
omit the retired fields and implementation handoffs project old contracts onto the
minimal executable shape with source identity retained.

This is a net deletion, not a statistical validator or another handoff layer. The
focused Theory/ABI/Simulation/preflight panel passed 129 tests and the full local
suite passed `820/820` in 66.88 seconds. No model call, benchmark draw, rerun,
resume, output repair, hidden-gold feedback, formula rule, retry, agent, scheduler,
model escalation, mathematical acceptance, empirical credit, or proof credit was
added. The exponential-rate task remains immutable `0/1`, and the scored ladder
remains `0/21`.

### Document-authority consumer implication

The same consumed exponential-rate artifact exposed one remaining mismatch with
Codex's workspace-first design. TheoryDeveloper had authored a 9,552-byte
Markdown/LaTeX document as the declared mathematical authority, and the planning
models received that exact file. The later Python/R source-owning sessions,
however, still received only a copied estimator or ADeMP JSON object. Planning
prompts also carried the exact document alongside duplicated problem, formula,
theorem, algorithm-sketch, and simulation prose. The authority declaration was
therefore not true at the point where source was actually edited.

Commit `fc7d335c` supplies one shared, hash-bound theory context to both the
AlgorithmEngineer and SimulationEngineer planning views and to their actual
model -> source tool -> raw observation sessions. For a document-native packet,
the context contains the exact documents, the complete compact claim DAG, and
only estimator identity plus the projected executable ABI. It excludes the
duplicated problem card, formula, algorithm sketch, theorem card, and ADeMP
prose. A packet with documents but inconsistent authority metadata fails closed.
Historical no-document packets keep their old structured fallback for replay.

The existing executable-field projector is reused for old ABIs; it removes
retired rate metadata without interpreting or repairing any mathematical claim.
On immutable replay, the Algorithm planning context fell from 20,712 to 17,067
bytes and the Simulation context from 16,271 to 15,123 bytes while preserving
the complete document and claim identities. The focused panel passed `79/79`
and the full local suite passed `822/822` in 66.71 seconds.

This change adds no Codex app-server, provider, thread manager, scheduler,
reviewer, repair layer, model call, retry, turn, task rule, formula parser, Lean
rule, benchmark rerun, score, or capability credit. The remaining measured debt
is the separate structured planning turn before each scientific source-owner
session. That split should be removed only when source identity, frozen metric
authority, and independent-review lineage can move into the same existing
workspace loop; it must not be hidden behind another adapter or scheduler.

### Single-session Algorithm implication

Code commit `84940729` removes that split for fresh AlgorithmEngineer work on
the native client-tool path. The structured Algorithm proposal was not an
execution authority and its strategy prose was regenerated by the source owner
before any tool use. The source session already received the exact question,
hash-bound Theory documents, complete claim DAG, estimator ABI, sandbox tools,
and raw observations. It can therefore plan, author, execute, revise, and
explicitly commit one exact source without a separate preliminary model request.
This removes exactly one provider request per fresh Algorithm task; it does not
add turns or enlarge the source workspace budget.

After accepted execution, runtime creates only a compatibility projection for
the existing independent-review ABI. It contains estimator identities, exact
source hashes, source-workspace artifact and transcript identities, model
provenance, and the immutable Theory-owned executable ABI. It contains no copied
mathematical explanation, implementation strategy, repair instruction, or new
claim-alignment handoff. The independent reviewer already fails safely to the
complete canonical mathematical core and every authoritative Markdown/LaTeX
document when no model-authored alignment packet exists. Exact source bytes are
rehash-checked before the projection is admitted.

An incomplete first source segment can now resume by a stable source-workspace
intent before any proposal packet exists. The same content-addressed checkpoint,
source bytes, and raw sandbox observation return to AlgorithmEngineer; ordinary
continuation still bypasses Architect. Historical structured providers, old
artifacts, Theory-revision source replay, and consumer backedges retain their
existing paths.

SimulationEngineer deliberately keeps its separate pre-execution planning call.
That stage owns frozen metric-path bindings and confirmatory replicate selection
before outcome-bearing source execution, so merging it without an in-session
freeze tool would weaken blinding rather than simplify the harness. Formalizer
and TheoryDeveloper continue to use their existing direct domain workspaces.

Direct routing, no-proposal continuation, provenance-only review projection,
legacy fallback, semantic review, and source-workspace regressions are included
in the full `825/825` passing suite (66.91 seconds).
`research_agent_runtime.py` is 24,913 lines under the unchanged strict
25,000-line limit. No Claude call, benchmark rerun, resume, output repair,
statistical rule, Lean rule, hidden evaluation, proof, score, or E2E capability
credit was produced; the consumed ladder remains `0/21`.

### Single-session Theory ABI implication

Code commit `b54864809740c4d35c3b1e33bf3e97d8d8118786` removes the
equivalent split from the canonical TheoryDeveloper path. The persistent
Markdown/LaTeX workspace previously authored the mathematics and compact claim
graph, then a second generator-only request asked the same owner to translate
each estimator into its executable ABI. That extra phase had no independent
authority: it neither reviewed the theory nor executed the interface, and its
validation failures left the source-owning workspace.

The document workspace now owns `estimator_interface_contract` as part of its
compact `estimator_specs` handoff. Initial work and targeted revisions receive
the complete ABI shape in their workspace catalog, submit exact interface bytes
with the documents, and receive generic shape and exact-reference validation
observations in the same model transcript. A revision keeps the parent's exact
ABI when estimator semantics are unchanged; if the model changes estimator
semantics or outputs, the prompt makes that same model responsible for revising
the ABI. Runtime adds only the immutable contract ID and provenance record. It
does not infer a request field, response field, normalization, mathematical
rate, or correction.

The canonical document path therefore has one Theory model/tool/observation
session and zero dedicated estimator-interface model requests. Historical
JSON-only parser and replay providers retain the existing two-phase compatibility
path; they are not a product fallback. Initial invalid-ABI feedback, targeted
revision feedback, progress continuation, unchanged-parent retention, and legacy
compatibility regressions are included in the full `825/825` passing suite
(66.97 seconds).

No Claude call, benchmark draw, rerun, resume, output repair, research turn,
budget increase, agent, scheduler, provider, statistical rule, Lean rule, hidden
evaluation, proof, score, or E2E capability credit was produced. The consumed
ladder remains immutable `0/21`.

### Exact session-contract implication

The official `openai/codex` checkout was fetched again on 2026-08-22 and is
exactly at Apache-2.0 `main` commit
`343074d4207d572809bd8cea15f4be1d09d98e0b`. Its tool runtime admits explicitly
parallel-safe calls through a shared read lock and serializes all other calls
through a write lock; its multi-agent guidance keeps immediate critical-path work
with the current owner and delegates only bounded, nonduplicated sidecars. The
inspected source hashes are:

- `codex-rs/core/src/tools/parallel.rs`:
  `48380e25abaf9c52e7a5de9cecf82cc4ddb84197683f73a11719de3b78c90e5a`;
- `codex-rs/core/src/tools/handlers/multi_agents_spec.rs`:
  `3ccedea36cc1c40e846a5c363edf614aba2b923055a86aff36a2473890de1be5`;
- `codex-rs/core/src/session/turn.rs`:
  `7499497671f04186b7c31126dbdee38c5a34a022a51b55bdefca331f778e2c66`.

AI-Statistician keeps the corresponding scientific division of responsibility:
one source-owning session handles the immediate Theory, Python/R, Simulation, or
Lean action; independent reviewers receive artifact-only contexts; optional
retrieval and light formal scouting are sidecars; and task-intent evidence
requirements, not a model's accidental route, determine which missing authority
must run next. A complete deterministic `run_research_agent_runtime` regression
now proves that `source_replication=required` enters the existing TheoryDeveloper
source workspace even when Architect requests an unrelated Simulation lane, then
terminates without Critic, Simulation, or Formalizer work after the hash-bound
source checkpoint is recorded.

The audit also found one content-addressing defect in our persisted specialist
sessions. Their contract hash included model, system prompt, tool names, strictness,
and terminal semantics, but omitted the exact tool descriptions and JSON input
schemas shown to the model. An old transcript could therefore resume after a tool
contract changed while retaining the same reference identity. Contract schema 2
now hashes the complete provider-visible tool definition. Description or schema
drift fails closed before any Theory, scientific-code, Simulation, or Lean session
is restored. TheoryDeveloper's read/write ABI is now stable across workspace
progress: current artifact names remain model-visible state and are validated by
the executor with ordinary tool feedback, rather than being baked into a changing
JSON-schema enum.

This is an integrity correction to the existing provider-neutral tool loop. It
adds no OpenAI provider, Codex app-server, thread manager, scheduler, subagent,
repair worker, model turn, retry, scientific rule, Lean grammar or tactic rule,
benchmark draw, output repair, score, or capability credit. Existing consumed
tasks and their recorded outcomes remain immutable.

### File-backed artifact implication

The first frozen Trimmed Match L1 draw exposed a direct violation of the same
principle. Its exact source-replication manifest was about 207 KB because it
retained two evaluator-authoritative CSV payloads. The hidden evaluator encoded
that data inside generated Python source, so the scientific sandbox rejected the
wrapper at its 100 KB source boundary before the identity harness ran. Separately,
the model-authored report failed calibrated semantic review after the visible
execution descriptor omitted the operator-fixed argument vector. The consumed
task remains a `0/1` hidden-gold failure; neither defect is rescored or repaired
post hoc.

The shared correction follows Codex's artifact/item separation instead of adding
another evaluator or repair path:

- executable Python/R remains a small independently validated artifact;
- selected input data is staged as a separate immutable file with exact SHA-256,
  rechecked by the sandbox runner, then supplied to `run_sandbox` as data;
- the hidden artifact evaluator uses that data binding rather than embedding a
  candidate packet in source;
- the operator-fixed source working directory and argument vector are included in
  the model-visible, hash-bound execution descriptor and result observation;
- TheoryDeveloper's existing scratch tool can receive selected published-source
  result files, so the same model can write Python/R to inspect exact outputs.

This adds no agent, scheduler, retry, content repair, statistical rule, benchmark
exception, or model call. The evaluator still owns hidden acceptance; the model
still owns interpretation. The focused regression is `114/114` and the full
suite is `839/839` in 69.22 seconds.

### Incremental Lean source implication

Code commit `cb70e09c3fbd2c9b95c3ed5c06cc3f1646330898` closes one
remaining mismatch with Codex's workspace-first coding loop. Formalizer already
kept one persistent model/tool transcript and returned raw Lean diagnostics, but
every correction required another complete `lean_source` value. For a long proof,
that made a one-line model decision pay the transport and regeneration cost of the
whole file.

The same existing Formalizer session now offers `edit_current_lean_source` beside
complete submission. The model supplies one exact `old_text` substring and its
replacement. Runtime verifies that the substring occurs exactly once, including
overlapping occurrences, materializes those model-authored bytes without parsing
Lean, checks the complete resulting source in the active project, and returns the
raw observation to the same model. Missing, ambiguous, unchanged, oversized, or
previously checked results remain ordinary tool feedback. Complete submission is
still used for first authoring, declaration-identity changes, and broad rewrites.

This is not a Lean repair engine. Runtime chooses no theorem statement, import,
identifier, proof term, tactic, or edit. A locally compiling result still requires
the existing independent target-semantic review, axiom audit, and exact
target-bound kernel promotion. Checkpoint continuation retains the exact current
source and can continue with another model-authored edit without Architect or a
second scheduler.

The final focused Lean, semantic-review, and shared client-tool panel passed
`77/77`; the full repository suite passed `843/843` in 67.93 seconds. No model
call, retry, turn increase, agent, repair worker, Lean grammar or tactic rule,
benchmark rerun, score, proof, or capability credit was added. The frozen ladder
remains immutable `0/23`, and strict development closure remains `0/2`.

### Frozen exact-target implication

Code commit `9812446fa0c4b48f0873518c30158a4268a78430` adds the
smallest missing task surface for evaluating the Codex-style Lean workspace in
isolation. An operator may now attach one hash-bound `formal_target_contract` to
a proof-only question. The contract carries the exact Lean source prefix,
declaration identity, active-project identity, and target hash; it contains no
proof. The existing RetrievalMemory worker consumes that target and returns
directly to the existing Formalizer session. Architect and TheoryDeveloper do not
rewrite an already-frozen theorem, while ordinary research tasks retain their
current graph.

This path reuses existing typed theorem-goal overrides, formal RAG, source
inspection, proof search, raw Lean checks, same-session source editing,
independent whole-target semantic review, axiom audit, and kernel promotion. It
adds no scheduler, agent, provider, repair worker, Lean parser, tactic rule, or
theorem-specific product logic. The central runtime remains below its regression
budget at 24,984 lines; pure target projection lives in the existing runtime
research-problem adapter.

The first disjoint formal L0 authority is Statlib's measure-inference implication
from uniform consistency to pointwise consistency. The exact target and fixed
Lean 4.30/Statlib environment are visible. The human proof and evaluator remain
outside the repository and model workspace. Before any product call, the hidden
harness accepted the human proof and rejected a weakened conclusion, an added
assumption, `sorry`, and a custom axiom (`5/5`). Repo tests passed `848/848` in
68.13 seconds. Commit `9812446f` was pushed to both canonical refs before the
external authority was bound to it. No product model call, theorem attempt,
runtime proof, score, or capability credit has yet occurred; the prior 23 tasks
remain immutable at `0/23`.

Commit `c4289cdb210b993aba04e44aa357010c52888653` closes one
pre-execution profile inconsistency: `research_eval` now enables the existing
Formalizer and independent target reviewer when a selected question explicitly
declares `formal=required`, while ordinary research tasks still keep the formal
lane optional. This is task-intent dispatch, not Lean content logic. It adds no
agent, scheduler, repair action, tactic, or retry. The focused profile/runtime
panel passed `103/103`, the complete suite passed `849/849` in 68.25 seconds,
and the unchanged hidden gold/negative set recalibrated `5/5` after binding the
new code identity. No product call has occurred.

Commit `40c1a9e508558b1294470d566f3af51eca5615ba` also corrects the
CLI description to state this same task-intent contract. The complete suite
remained `849/849` in 68.16 seconds, and the external authority was rebound and
recalibrated `5/5` without changing its target, gold proof, negatives, or
evaluator logic. No product call has occurred.

Commit `d81ac4212501558d750bfc2a4b160f3f853b1724` makes the
profile's internal contract state the same selected-task formal behavior. The
focused profile suite passed `22/22`; the unchanged hidden authority again
calibrated `5/5`. No product call has occurred.

### First exact-target result

The single authorized exact-Haiku draw is now consumed. The existing Formalizer
workspace did execute as a coding-agent loop: two same-owner segments produced 24
model-authored source updates, 24 local Lean checks, and 10 formal-RAG calls, with
no Architect call. One candidate elaborated only through `sorryAx`; the independent
axiom audit rejected it. The model ended with a formal-gap report, so there were
zero kernel-verified subclaims and no exact theorem closure. Runtime and the one
post-termination hidden evaluation both failed; the immutable ladder is `0/24`.
The task cannot be rerun, resumed, repaired, or rescored.

This result supports the Codex harness choice but not the prover capability claim.
The model owned every Lean edit and saw raw compiler/search observations; the
harness correctly refused to turn elaboration, retrieval, or a model-reported
foundation gap into proof. It also exposed three generic observation defects:

- selected-task `formal=required` was respected by dispatch and final evaluation,
  but two internal evidence-contract fields still inherited a capability-eval-only
  condition;
- proof-state inspection could label a goal-free elaborated declaration as locally
  accepted even when structured axiom audit had found `sorryAx`;
- exact declaration source already existed in the active RAG snapshot, but the
  read-only source-inspection tool was unavailable without an LSP declaration
  provider.

Post-run commit `fe7c7055` fixes those shared mechanisms for future tasks. It makes
explicit formal research intent authoritative across the evidence contract, binds
proof-state feedback to the existing structured axiom audit, and lets the same
Formalizer session inspect a model-selected declaration through the active
project/RAG snapshot. Runtime selects no declaration, source edit, proof term,
tactic, or repair. The declaration tool only resolves files within the bound Lean
project and labels its output as non-proof evidence.

Focused regression passed `124/124`; the complete suite passed `854/854` in 68.22
seconds with `research_agent_runtime.py` reduced to 24,745 lines. No product call,
benchmark rerun, hidden rescore, agent, scheduler, retry, turn increase, theorem
rule, Lean grammar/tactic rule, proof, or capability credit was added. Exact run and
authority hashes are recorded in
`docs/operator_audits/statlib_uniform_consistency_formal_l0_v1.md`.

### One Theory workspace action budget

Code commit `9cf75411746fcc7b5bc400649a75442b2805c770` removes a remaining
non-Codex-shaped control split from TheoryDeveloper. The same persistent model session
previously faced independent read and write quotas in addition to its model-turn and
tool-call boundaries. That classified budget could reject a mathematically useful sixth
write even when unused reads or ordinary actions remained, so the harness rather than
the model selected the research-action mix.

TheoryDeveloper now receives one shared ordinary-tool budget for model-selected reads,
searches, complete document writes, hash-bound local edits, and Python/R scratch work.
The maximum model turns remain separately bounded, execution tools retain their real
sandbox and source safety caps, no-progress termination remains active, and the shared
client-tool loop still reserves one terminal checkpoint or honest-gap disposition
outside the ordinary action budget. CLI configuration and topology evidence record the
same policy explicitly.

This adopts the useful Codex harness principle without importing Codex runtime: one
source owner chooses environment actions from a stable tool surface and consumes raw
observations in the same session. It adds no agent, scheduler, repair path, statistical
formula, Lean rule, or product model call. The dependent Theory/Architect/runtime panel
passed `208/208`; the complete repository suite passed `857/857` in 68.13 seconds, and
compile-all, model-policy, JSON, and diff checks passed. This is future-task regression
evidence only. The consumed formal draw remains `0/1`, the ladder remains `0/24`, and
strict development theorem closure remains `0/2`.

### Theory authority edge after the twenty-fifth draw

The first scalar score-information draw exposed a different harness defect. The
TheoryDeveloper used the intended Codex-shaped inner loop: one persistent model
session made ten model-selected tool calls, read the authoritative Markdown
workspace, ran two scratch checks, and committed a 352-line derivation. The outer
graph then skipped the existing isolated referee because that review edge was
coupled to empirical metric authoring. Terminal Critic accepted the same author's
unreviewed artifact, while hidden gold correctly withheld theory credit. The draw
is consumed and remains `0/1`; it is never eligible for rerun or rescore.

Code commit `9fbbeaba610a48bfbce84a80b4b91802fe301ba9` makes strict
review outcome propagation an evidence-authority rule for every task that asks for
theory. It reuses the existing artifact-only Markdown referee workspace. Rejection
returns exact findings to the same TheoryDeveloper workspace; acceptance binds the
review packet and exact theory hash, then compiles the already authored Architect
plan. A theory-only task creates no metric gate and does not claim that Python/R,
simulation, or Lean is applicable. A direct terminal-Critic call without that exact
acceptance now stops before a Critic model request.

This is the same separation used by Codex strict review: the model remains free to
author and revise content inside its workspace, while the harness preserves the
independent decision and prevents a later component from flattening or bypassing
it. No theory formula, checklist item, repair agent, scheduler, retry, model turn,
resource cap, Formalizer requirement, or benchmark exception was added. Runtime
and evaluation share one hash-lineage validator instead of maintaining parallel
review rules. The relevant focused panel passed `214/214`; the complete repository
passed `860/860` in 72.19 seconds. These facts apply to future disjoint tasks only;
the immutable ladder remains `0/25`.

### Required review projection after the twenty-sixth draw

The disjoint Basu-theorem draw exercised the intended inner Theory workspace but
found one remaining outer-graph projection defect. TheoryDeveloper used eleven
same-session model/tool turns and committed a 304-line, 20,551-byte Markdown/LaTeX
artifact. The runtime-requested contract required isolated review, but the
nonempty Architect plan omitted that runtime-owned field and shadowed the complete
contract. TheoryDeveloper therefore returned to Architect instead of the existing
referee. Architect mislabeled terminal Critic as independent review; Critic's
deterministic backstop correctly blocked before its model call. Hidden theory
evaluation did not execute, and the consumed task remains `0/1`.

Code commit `8ef61b0b9625bf99e4f783dad7781b4c1bfdba77` applies the
strict-disposition part of the Codex harness lesson at the actual authority edge.
Architect normalization now preserves the runtime-owned review requirement, and
explicit `task_intent.theory=required` is checked again at TheoryDeveloper's exit.
The exact live shadowing shape is a regression: a nonempty plan contract lacking
the flag still routes the immutable Theory artifact to the existing isolated
preflight operation.

This adds no reviewer, model call, retry, repair action, scheduler, mathematical
rule, task-family branch, or Formalizer requirement. It does not import Codex's
app-server, Responses transport, provider, thread manager, or subagents. The
focused suite passed `123/123`; the full repository passed `861/861` in 72.84
seconds. The correction is future-task mechanism evidence only, and the immutable
ladder remains `0/26`.

### Compiled post-Theory collaboration edge

Code commit `6598ed348152999c317b83b9b2d48d1582231321` removes one
remaining routine outer-model hop. On a task where Theory is supporting rather
than required final evidence, TheoryDeveloper previously committed its artifact
and then created an `architect-after-theory` task asking Architect to choose again.
The original validated Architect packet already contained the research path and
applicable evidence dimensions, so this second sampling call added cost and could
contradict the plan without adding new scientific evidence.

AgentRuntime now compiles that existing model-authored plan directly into the next
workspace. The transition uses current task intent, the plan's ordered workspaces,
the newly produced theory identity, and its model-authored estimator interfaces.
It does not inspect mathematical prose or select a statistical method. Required
theory still routes through the isolated referee; a theory revision that invalidates
descendants still follows the existing dependency-rebuild path; genuine
independently established cross-workspace conflicts may still reach Architect.

The exact regression uses optional Theory plus required scientific code and proves
that the next task is AlgorithmEngineer with the same `n_runs`, seed, theory ID,
and original Architect plan, with no `runtime_architect_operation`. The focused
collaboration panel passed `135/135`; the complete repository passed `862/862` in
72.47 seconds. Product runtime changed by one net line and remains below its
25,000-line guard. No model call, task rerun, reviewer, repair action, scheduler,
scientific rule, or capability credit was added; the ladder remains `0/26`.

### One exploratory Simulation session

Code commit `9a224b534cc8cce2fce48a8834810e2ac502b257` removes the
remaining routine two-call split for fresh exploratory simulation. Previously the
SimulationEngineer sampled a structured planning packet and then opened a second
source session. When native client tools are available, generated source is
required, no upstream estimator is bound, and the phase is exploratory, `propose()`
now emits only a deterministic, hash-stable intent envelope without a provider
call. The same SimulationEngineer session chooses the DGP and diagnostics, writes
Python or R, executes the exact source, reads raw observations, and revises it.

The envelope contains identity and transport facts, not a runtime-authored
simulation design. Confirmatory work remains unchanged: frozen metric authority,
accepted estimator lineage, cohort blinding, and independent review still govern
execution. A failed source-owned session resumes from its exact intent and source
checkpoint; a missing or stale bound packet fails before another model call.

This adopts Codex's same-turn model/tool continuation without importing its
app-server, thread manager, Responses provider, permission system, or subagent
scheduler. Theory Markdown/LaTeX, Algorithm Python/R, independent review, and Lean
already use the shared provider-neutral loop; no new framework layer is needed.
The full repository passed `863/863` in 72.26 seconds, compile-all and diff checks
passed, and architecture budgets remain below 25,000 runtime lines, 150,000 package
lines, and 400 production-design lines. No product model call, benchmark draw,
rerun, rescore, scientific rule, proof, or capability credit occurred.

### Complete graph, incomplete scientific judgment

The twenty-seventh disjoint draw is the first clean live separation between the
Codex-shaped collaboration harness and scientific correctness. Uniform endpoint
v1 completed Architect planning, an eight-turn TheoryDeveloper Markdown/LaTeX
session, a five-turn isolated referee session with two scratch checks, Algorithm
source execution, independent source review, frozen metric review, one exploratory
Simulation source session, independent Simulation review, and terminal Critic.
AgentRuntime ended `ACCEPTED`; visible `research_eval` was complete and
mode-conformant. Formalizer correctly did not run because formal evidence was not
applicable.

Hidden gold nevertheless returned `0/1`. Mechanical theory checks passed `7/7`,
but the calibrated semantic judge returned `FAIL`. The scientific harness passed
formula, schema, output, permutation, and rescaling checks but rejected the public
invalid-request behavior: the exact source converted sample elements to NumPy
floats before type validation. Hidden empirical evaluation passed `8/8` over
15,000 estimator invocations. Runtime review had false-accepted both artifacts.

This is the desired evidence boundary working: a healthy trajectory and passing
empirical component cannot masquerade as a correct full task. It also locates the
next problem inside existing model-owned sessions rather than in a missing router,
fallback, or repair worker. AlgorithmEngineer must exercise the complete visible
ABI before commit, and the isolated source reviewer must compare actual language
behavior with every public entrypoint, field, type, domain, shape, edge case, and
rejection clause.

Commit `b49a8f5a` implements exactly that shared correction. It adds one
`executable_interface_alignment` dimension to the existing reviewer, strengthens
the existing Algorithm source-owner prompt, and records privacy-preserving
claim/check hashes plus statuses in evaluator-only reports. It adds no source edit,
deterministic type grammar, retry, agent, scheduler, model call, statistical rule,
or hidden feedback. The consumed candidate remains `0/1`; the ladder remains
`0/27`.

The focused regression passed `147/147`, the complete repository passed `865/865`
in 68.54 seconds, and production Python remains below the unchanged architecture
budget at 149,998 lines. This reinforces the official Codex reuse decision: keep
the provider-neutral same-model tool loop and artifact/session lifecycle, but do
not embed Codex app-server, Responses transport, thread manager, or a second
scheduler around Claude specialists.

### Model-directed referee context and artifact parity

Commit `778b2aac` applies the same thin-harness principle to the remaining theory
review mismatch. The referee system prompt now establishes only role, falsification
stance, model-directed context selection, and evidence boundaries. Detailed review
obligations live once in the versioned task protocol already supplied to the same
tool session. This removes the contradictory demand to read and paraphrase every
line while retaining hash-bound reads, raw scratch observations, independent report
authority, and compact terminal statuses.

The hidden semantic evaluator now inspects the canonical model-authored theory
artifact rather than only its file-backed half. It receives authoritative
Markdown/LaTeX plus a hash-bound JSON projection of the exact estimator identity,
inputs, outputs, executable interface contract, and termination guarantee authored
by TheoryDeveloper. Hidden references, rubric text, thresholds, and results remain
outside AgentRuntime, and no evaluator observation can return to the source owner.

This is selective mechanism reuse, not Codex embedding: no app-server, Responses
provider, thread manager, subagent scheduler, repair worker, retry, mathematical
parser, statistical formula, or extra model call was added. The focused panel passed
98/98, the complete repository passed 865/865 in 68.48 seconds, compile-all and diff
checks passed, and production Python remains 149,999 lines. The consumed Uniform
draw stays 0/1 and the capability ladder stays 0/27.
