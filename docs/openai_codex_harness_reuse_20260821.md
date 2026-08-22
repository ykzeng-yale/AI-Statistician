# OpenAI Codex Harness Reuse Audit

## Upstream identity

- Repository: `https://github.com/openai/codex`
- Audited branch: `main`
- Audited commit: `970b7f2ff4f612b8e8cd340eb6b6d789d7141dd2`
- License: Apache-2.0
- Read-only checkout: `/Users/yukangzengcmac/.codex/external/openai-codex-970b7f2f`
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
| `codex-rs/app-server/README.md` | thread/turn/item protocol, dynamic tools, and managed policy | `6255f38ce9fe1aaf6a19c79d0bccb00fbd35066267a410feec638ae504d387bd` |
| `codex-rs/model-provider-info/src/lib.rs` | provider transport contract with redacted secret-bearing values | `2168b93576dff1d336f0c3d390b6ff8c38376340fc8ed2eea8da9857ddb1eeb7` |
| `codex-rs/core/src/context/guardian_review_evidence.rs` | bounded, runtime-only, authorization-bound review evidence | `b0d5cafa5529dd0ae55a44d3933a175b4d0999d73e78dc7963c1d2781088279f` |
| `codex-rs/core/src/thread_manager.rs` | fresh parent-linked internal sessions | `3bbbd6f2c68cacc1f652e57493ac15a560b2d7da2f93f797ad492d794f4e8c9d` |
| `codex-rs/core-plugins/src/executor_hooks.rs` | identity-allowlisted executor cleanup hooks | `fbdc87934d9dae73014f626dd079989986c1b1e8bcc8d068cb6f1d4fc555463a` |
| `codex-rs/core/src/session/mcp.rs` | canonical strict-review outcome propagation | `65d807c77eb76c9c6f61a27c56ae943d052e50b1966674f721f02e6a42433e44` |

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
   while the isolated referee still has to inspect every authoritative document
   under its separate hash-bound coverage gate.
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

These changes add no model call, retry, turn, agent, scheduler, model tier,
statistical formula, Lean grammar rule, or repair recipe.

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
calibration remain operator responsibilities. All seventeen scored tasks are
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
