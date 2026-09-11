# AI Statistician Production Design

## Product target

AI Statistician is an autonomous statistical theory laboratory. Given a fresh
research question or paper, it should be able to:

1. inspect prior literature, code, and data under a recorded source policy;
2. identify the estimand, assumptions, procedure, and theorem targets;
3. develop a reviewable theory argument with equation and lemma lineage;
4. implement and test scientific Python or R code;
5. run exploratory and then frozen confirmatory simulations;
6. when task intent requests it, formalize the exact target in Lean; and
7. grow source-identified reusable research and proof artifacts, measuring cross-task reuse.

Every lane stops honestly with accepted evidence, an explicit unresolved gap, or
a budget-bound failure. Formal evidence is one dimension of the product result,
not a universal prerequisite for empirical or theoretical research credit.

The product is not a collection of task-specific scripts, a theorem answer bank,
or an audit dashboard. The model performs semantic research and source authoring.
The harness supplies a reliable environment and preserves evidence boundaries.

## Canonical control graph

There is one outer `AgentRuntime` graph:

```text
Goal, source policy, and task-intent evidence contract
  -> source scout or exact replication when relevant
  -> iterative theory workspace <-> exploratory scientific workspace
  -> independent theory and source review
  -> frozen confirmatory simulation
  -> optional, advisory, or required Lean workspace
  -> final retained Critic with a per-dimension evidence vector
```

Frozen source-only or theory-only intent starts TheoryDeveloper directly; exact
formal-only intent starts its RAG/Formalizer path. Otherwise the Architect resolves
all four evidence dimensions over the configured workspace inventory, may revise its own dimensions on genuine replans, handles cross-workspace conflicts, and decides when to stop; only operator-requested dimensions are frozen. Each Architect plan or cross-workspace route is one provider-native structured control call: an invalid envelope fails closed without resampling, model-authored scientific stop conditions cannot lower host-owned call or revision budgets, and irrelevant discovery lists may remain empty. A
workspace-continuation budget covers same-owner progress and detached author-review-author work; each contiguous collaboration segment is bounded independently, while total telemetry accumulates. Accepted evidence entering a new lane and genuine cross-artifact conflicts remain outer graph transitions. Its boundary preserves the exact pending task without asking Architect. Routine syntax, ABI,
compiler, simulation, or Lean failures stay with the model that owns the source.

Every source-owning workspace uses the same loop:

```text
model inspects objective and artifacts
  -> model chooses a tool, writes complete source, or authors an exact edit
  -> isolated environment applies or executes the exact artifact
  -> raw observation returns to the same model
  -> model revises the source or artifact
  -> pass, explicit gap, or lineage budget exhaustion
```

There is no post-runtime scheduler and no separate repair agent. A resumed run
continues from content-addressed artifacts and workspace checkpoints in the same typed
graph. Outer-budget exhaustion stores the exact pending `AgentTask`. A terminal
provider or internal-tool error seals current source-owner state and stops without
restarting the subsystem. Manifests carry only task, checkpoint, and continuation
references; explicit resume hash-verifies them. Provider-local retries repeat only the same unanswered request; substantive failures remain terminal. Unexpected Formalizer exceptions use the shared runtime boundary, not message-keyword provider classification or a separate failure-artifact pipeline.

The general harness audit is reproducibly pinned to [OpenAI Codex at `8e6a44b4`](https://github.com/openai/codex/tree/8e6a44b4); the changes after the prior `03467026` pin add managed `codex exec` worktrees and narrow asynchronous user-message guidance but do not add a scientific control plane. We adopt incremental history, stable capability-accurate tools and matching prompt instructions, raw tool-error feedback, atomic omission of oversized observations, no implicit replay after failed authentication recovery, checkpoint/resume, cancellation, bounded context, explicit continuation provenance, isolated findings-first review over the exact target and hash-bound replication results, host-owned authority independent of compaction, and queued-message versus work-trigger semantics. Repository documents are a map and system of record, not one giant injected manual. A tool is stable within one retained session but is omitted when its underlying workspace or authority is absent; an empty search surface is not a model capability. The Claude transport retains one Anthropic SDK client across consecutive rounds while every request still binds its exact model, history, tools, metadata, immutable source/tool environment, root authorization fingerprint, and, for Theory continuation, exact durable workspace hash. Codex's experimental context manager is backend-specific and is not copied into the Claude transport. Codex Core, App Server, SDK, provider transport, worktree management, and multi-agent scheduler remain outside the product because importing them would create a second runtime rather than improve statistical reasoning. The exact selective-adoption map is maintained in [`openai_codex_harness_adoption_20260825.md`](openai_codex_harness_adoption_20260825.md).
We do not embed `codex-core`, App Server, its Responses transport, shared-directory subagents, or another scheduler. Each scientific workspace is the domain session and AgentRuntime remains the sole outer graph; any sidecar requires model, tool, lineage, isolation, and resume parity and can never become authority.
Like Codex `run_turn`, a response without a tool call ends the workspace segment. The harness persists the exact response and state for explicit hash-verified continuation; it never appends a private tool instruction or resamples. Progress attributes the inner subsystem, agent, and stage separately from the outer task owner. Each independent reviewer submits a complete judgment through one schema-validated terminal tool; invalid submissions return full validator observations to the same retained reviewer and never become a runtime-merged partial draft.

## Progressive commitment

The graph imposes no universal research order. TheoryDeveloper chooses early
Crossref/arXiv/GitHub queries and source handles; the harness owns hosts, source horizon,
secrets, byte bounds, checkpoint-durable exact observations, identity, hashes, and citations, but not interpretation.
Frozen source execution has two explicit authorities. Schema 1-3 fixes one operator-curated command for preregistered exact replication. Schema 4 keeps the exact snapshot, interpreter, packages, network denial, secrets policy, and resource limits operator-owned while the retained Theory source owner selects a project entrypoint, working directory, arguments, and declared outputs; raw feedback returns to that same session and each attempt runs in a fresh workspace. At checkpoint that owner explicitly selects one completed attempt while runtime preserves the complete command lineage; the terminal Critic independently verifies that selection and reloads every attempt observation. The latter is exploratory reproduction until an independent hidden evaluator judges it, never preregistered replication or proof. In either mode the owner audits exact observations, text reads, and hash-rechecked provider-native PDF/image results, then uses a narrow checkpoint only when downstream task intent excludes Theory and otherwise binds the report into an integrated Theory workspace. Visual access changes observation fidelity, not semantic authority.
For non-theory tasks that checkpoint is an immutable prerequisite to the already frozen code/simulation plan; for integrated tasks the report stays in full workspace evidence but is excluded from mathematical Theory authority. Algorithm and Simulation read the exact report on demand as replication evidence.
Runtime externalizes hash references and rejects mutation; execution and report content cannot validate theory, generated code, simulation, or proof.

Theory remains long-horizon and iterative. As soon as the estimand, DGP,
procedure interface, and a testable claim are stable enough, exploratory coding
can interleave with theory and return non-confirmatory counterexamples to TheoryDeveloper.
An accepted exploratory implementation returns to the exact parent Theory workspace whenever review is still `REVISE`; evaluator authoring and confirmatory execution fail closed until theory authority is accepted.
Independent theory review establishes a stable checkpoint before frozen confirmation. A light
formalization scout may expose missing definitions; expensive Lean proving normally follows stable statements unless intent selects `proof_first`. The current outer runtime executes one workspace at a time: `dual_track` is a dependency policy, not implemented concurrency. Future independent work must use this same graph with isolated workspaces and hash-bound joins.

## Responsibility boundary

The LLM owns:

- statistical definitions, assumptions, derivations, and counterexamples;
- complete Python, R, and Lean source;
- retrieval queries and selection of useful premises;
- responses to raw compiler, test, simulation, and proof-state observations;
- explicit declarations that an upstream theory or target is inconsistent.

The harness owns:

- typed task transport and content-addressed artifact references;
- isolated tool execution, resource limits, network policy, and secret isolation;
- exact source hashes, target identity, lineage budgets, and checkpoints;
- schema validation for compact control envelopes and typed tool inputs;
- independent-review separation and frozen evaluation authority;
- immutable evidence labels and Lean kernel promotion.

Feedback is data, not an executable instruction channel. Preserve model and tool
observations without recursive field-name blacklists. Only explicit model actions
can request tools or edits, and those actions still pass the host-owned checks.
Scientific mistakes alone do not justify another harness rule or reviewer loop.

The harness must not own:

- runtime-authored source edits or string patches;
- theorem-family formulas, expected answers, thresholds, or aliases;
- Lean grammar fixes, tactic recipes, or model-facing compiler interpretations;
- reviewer-selected repair owners followed by deterministic routing;
- hidden bridge, queue, materializer, promotion, or fallback workflows;
- proof credit for retrieval hits, LLM judgments, pseudo-formal text, or compilation of a weaker theorem.

`packet_validation.py` carries typed failure observations and compatibility JSON
extraction; it never calls a model or regenerates content. Substantive theory, Python, R, and Lean belong in model-owned
workspaces where the same model receives raw observations and authors the next state.
Runtime may apply an exact model-authored write or edit but never chooses its content.
Theory uses direct document reads, searches, complete writes, hash-bound local edits,
and compact handoff writes in the same source-owner session.

## Theory workspace

TheoryDeveloper maintains an artifact-backed research workspace, not a JSON answer.
It owns exact definitions, assumptions and use sites, equation/lemma dependencies,
executable procedure semantics, counterexamples, gaps, and revision lineage. There is no JSON-only core-theory fallback: a provider without native client-tool turns fails closed before mathematical authoring.
Compact packets are handoff indexes: problem and simulation handoffs contain claim IDs, theorem and formalization handoffs contain claim/path references, and estimator handoffs contain only executable ABI. Validators reject duplicated formulas, assumptions, theorem prose, proof arguments, simulation designs, and semantic constraints in fresh JSON. Serious theory has no per-field caps; one selector defines both the model-visible output contract and writable handoff tools for explicit task intent, so non-applicable lanes are absent rather than advertised as unusable empty artifacts.
The validator checks only typed handoff structure and formal artifacts depend on intent. Historical packets remain readable, but fresh no-intent authoring exposes only the mathematical core until the Architect binds a request-scoped plan.
Durable Markdown/LaTeX is the publishable current argument, not a transcript of false starts. An integrated replication report is a separate workspace document and cannot be the sole mathematical document in a Theory packet. Exploration stays in scratch or is explicitly delimited as `SCRATCH` or `REJECTED`; a later correction does not silently deactivate earlier active text.

Discovery and revision share exact parent and reviewer artifacts. Theory authors and
referees execute ordinary Python/R scripts; hash-bound output and errors return to
the same model. Scratch requires no function or JSON return; confirmation retains
its separate metric ABI. Only model-authored edits apply, and scratch is not proof.

Structural validity does not stop the session. Within one shared ordinary-action budget,
the model chooses its mix of reads, searches, writes, edits, and scratch work, then continues, reports a gap, or calls `commit_theory_checkpoint`. No tool kind has a separate attempt quota; document-backed continuation preserves cumulative execution lineage under the same workspace and outer continuation bounds. The harness still owns total action and turn bounds, no-progress termination, execution safety caps, and the reserved terminal disposition. A commit proposes independent review; it is not evidence.
Continuation may preserve a new hash-bound source, scratch, or workspace observation before any authoritative edit; an unchanged reread cannot manufacture progress, and observation-only state remains unaccepted.

Supporting Theory completion compiles the validated Architect plan into the next
workspace; required review and genuine conflicts retain their authority paths.

When prior work is permitted, the same TheoryDeveloper session can inspect a frozen snapshot, Crossref record, horizon-safe exact-version arXiv HTML, or navigate pinned public repository directories and text without a LiteratureAgent.
An independent referee gets a separate opaque-handle session and chooses its own queries. It first reconstructs the requested load-bearing chain, then sweeps every other active assertion for contradictory definitions, explanations, assumptions, measure/type declarations, regularity, and scope.
It writes one findings-first authoritative Markdown report. Its compact envelope contains only the report hash, inspected references, disposition, actual blockers, and prior-finding statuses. Runtime checks identity and traceability, not mathematics; evaluator gold remains excluded from all live discovery.

## Scientific coding workspace

AlgorithmEngineer and SimulationEngineer own complete source and use the shared
`ScientificCodeWorkspace` loop. Python and R are first-class languages. The
pinned Pyodide/WebR profile checks explicit package declarations against
runtime-observed namespaces, bounds subprocesses, omits secrets, and blocks network.
Safety comes from isolation and resource policy, not from banning the scientific
computing ecosystem.

The runtime may require a small general executor ABI, but it may not encode a
statistical answer. Syntax, safety, ABI, runtime, serialization, and consumer failures
return raw observations to the same source owner; exploratory work may also return
explicitly non-confirmatory empirical diagnostics. Permitted diagnostics remain complete in hash-bound read-only documents, available through existing search and line/character-range reads across checkpoints.
Only the exact current source-bound observation can authorize release; earlier diagnostics remain readable history. Identical source is a tool no-op rather than a runtime edit.
Outcome visibility is applied before externalization; the runtime neither summarizes errors by position nor authors a content repair. Raw diagnostics are not by themselves a data-blinding guarantee: confirmation data must remain outside exploratory execution.

Exploratory source may start before the complete theorem program is closed once
its consumed interfaces are stable. A bound replication report is exposed through
the same hash-bound read-only document tools but never as mathematical authority.
Such runs may falsify theory but cannot satisfy frozen confirmatory gates. The same model may atomically import selected exact UTF-8 source modules, configuration, fixtures, or text data from either previously completed commit/path/hash-bound public reads or an observed evaluator-approved frozen snapshot; any failed identity check leaves the project unchanged, and one complete project hash binds every imported file through execution and independent review. For evaluator-approved replication, an exact public GitHub SHA may be fetched shallowly through an empty no-credential HTTPS-only Git home, or an existing local commit may be used; both enter the same complete blob/mode/hash-bound freezer and no-network copy-on-write executor. Every fresh run binds declared outputs, both raw streams, post-run workspace identity, mutation state, errors, and undeclared output-root artifacts into its artifact identity; only a clean execution can enter Critic or hidden-gold success gates. Snapshot-time Git object reads disable lazy fetch, credentials, prompts and transports, while missing blobs and escaping, dangling, directory, chained, or mutated links fail closed. Acquisition, snapshot, import, and execution remain observations, never semantic authority.

For live providers with native client tools, fresh Algorithm planning envelopes carry
only artifact identity and immutable bindings. Simulation instead starts from one
runtime-owned source intent with no separate model planner. In both lanes, source is
authored in the same retained model-owned workspace. Submission and exact edits store
complete Python or R source. The existing run tool may also select an exact current project script for exploratory tests, importing/source-loading the unchanged project instead of copying functions into a second scratch program.
These model-selected scripts use the existing isolated Python/R runner, may choose diagnostic seed/replicates, and receive no confirmation data or bound estimators. Their exact observations remain readable across checkpoints and cannot update release authority.
The bound execution check still runs only on explicit request, so the owner can batch tests and edits before an expensive simulation. A later `commit_scientific_source` requires an
accepted current-project observation from that bound check, never merely a successful diagnostic script.
No repair worker, diagnostic parser, or content patch intervenes. Estimator IDs stay frozen.
Structured-source packets are historical replay only; fresh authoring fails closed without native client tools.

Confirmatory iteration stops when source is execution-valid. Realized values,
threshold verdicts, and value-derived hashes are withheld from the source model and semantic reviewer, which checks exact source, runtime arguments, frozen measurement
contract, result schema, and theory alignment. After `ACCEPT`, the immutable outcome
is released once to Architect by reference, and the same Simulation source cannot
retry. Execution is not statistical validity or theorem proof.

If Architect assigns a released outcome to AlgorithmEngineer, runtime restores the exact
parent source and frozen Simulation continuation by hash. The same coding workspace
revises complete source, receives independent review, and replays the frozen consumer
on the new cohort without a new proposal, Formalizer detour, or runtime-authored edit.

For rejected source, the reviewer asks whether editing only that source can close
all findings with theory, contract, and consumer fixed; it names no owner, route,
or edit. Sufficient findings return to the coding workspace; otherwise one compact
observation goes to Architect. Source stays in the store, outside the control task.

The reviewer owns executable-contract decomposition. Public clause IDs are navigation
addresses, not proof that a compound clause was tested. The model runs adversarial probes,
separates relevant positive, malformed, boundary, transformation, and output obligations,
and reports untested obligations. Runtime verifies execution and lineage, not semantics
or a declared coverage list. After each exact-source probe, its raw observation and the
unchanged public contract return together to the same reviewer context; this improves
attention without adding a contract parser, generated case, or deterministic verdict.

For outer-graph completion, an Algorithm or Simulation lane is complete only when
its active manifest has an independent `ACCEPT` bound to the current immutable
parents. The accepted review is the completion authority; handoff history and an
earlier source-task execution are not. A changed Theory or Algorithm parent makes
the prior review ineligible without rerouting through Architect. ACCEPT rows merge
by source workspace and immutable parent lineage so accepting Simulation cannot
erase the current Algorithm acceptance, or vice versa.

When the frozen protocol requires generated algorithm code, confirmatory
simulation can consume an estimator only through a hash-bound handoff produced by
accepted independent semantic review. A sandbox artifact that executed but was
rejected is failed evidence, not an implicit downstream dependency. Exploratory
simulation remains available when the frozen contract does not require that
handoff.

## Empirical protocol

For fresh tasks, exact executable Simulation source is the preregistration authority.
The same source-owning model authors DGPs, measurements, formulas, decision logic,
diagnostics, and replicate justification in ordinary Python or R before confirmatory
outcomes exist. Runtime validates only a generic executor ABI: one exact Boolean
`acceptance_passed` and one positive `requested_runtime_replicates` within sandbox
capacity. It contains no statistical threshold, formula, DGP, or repair rule.

There is no universal replicate count such as 100. Before outcomes are revealed,
the evaluator freezes a task-specific budget from a declared Monte Carlo standard
error, interval-width, or power target plus resource limits. Exploratory runs may
be small and adaptive but are labelled non-confirmatory. Confirmatory replication
may stop only by its predeclared precision rule, never because the observed result
crossed a desired threshold.

The minimal source-owner pattern is:

```text
Simulation owner writes and runs source on non-confirmatory diagnostics
  -> raw environment feedback returns to that same model session
  -> owner commits exact source bytes and requested confirmatory size
  -> isolated reviewer inspects those exact bytes without outcomes
  -> ACCEPT releases one exact-hash replay on the hidden cohort
  -> outcome is terminal evidence; it cannot trigger source revision
```

The reviewer may read/search hash-bound exact source and Theory documents and use isolated
Python/R/SymPy probes, but must judge semantics, pre-outcome independence, and diagnostic
sufficiency rather than trust a returned Boolean. A rejection returns exact findings to the same source owner. Frozen
legacy metric packets remain reconstructable for old evidence only; they are not a fresh
authoring path. There is no prose-to-source translator, packet repair worker, result-informed
revision, or routine Architect hop.

## Lean formalization workspace

Formalization policy is `required`, `optional`, or `advisory` and scheduling is
`proof_first`, `simulation_first`, or `dual_track`. A formal gap blocks only a
required formal contract. Optional/advisory gaps are disclosed in the final
evidence vector and cannot erase accepted theory or empirical evidence. Conversely,
simulation or review can never be promoted to theorem proof. Optional/advisory
product work defaults to `simulation_first`; explicit tasks may choose another path,
while strict formal-capability evaluation remains `required` and `dual_track`.

Formalizer/ProofEngineer receives an exact goal reference from the outer graph;
runtime resolves its ID/hash without a second LLM target-binding call. The same
client-tool workspace owns authoring and revision. The model chooses retrieval,
inspection, target/support edits, dependency order, submission or a task-bound gap.
Files are checked unchanged. Session-local `.olean` reuse requires exact support
hashes and build order; drift rebuilds, and final promotion starts clean.
Raw failures and complete rejected candidates return to the model, without a
second field-whitelisted or length/depth-clipped projection, including startup/checkpoint diagnostics. Runtime
injects no import, statement, tactic or proof body; unknown fields confer no authority.

One turn/call budget covers every action. The initial message carries target/support
manifests, hashes, declaration and complete Lean observations; exact files are read on demand.
One bounded transcript retains actions and observations with a cacheable append-only prefix.
Fresh revision sessions check their initial source; continuations retain exact checkpoint observations and recent history, not new verification evidence.
Declaration inspection resolves the model-selected active-project symbol through
task-bound RAG and OpenProver's `lean-lsp-mcp`; the candidate file is only a local
fallback. All such observations remain explicitly non-proof evidence.

The stable initial/revision tool surface offers target/support read-write-edit operations,
support compilation, declaration/proof-state inspection, formal RAG, model-intent-bound proof search, and a typed
formal gap. The same Formalizer supplies OpenProver's current context and target from its Lean observation; no hidden normalizer model or packet regeneration may reinterpret that task. A revision gap preserves exact target provenance, clears proof-candidate
source fields, and remains non-proof. Gap reporting needs no successful compilation or mandatory tool-use sequence; it records the model's unresolved work, not a verified library defect, and preserves exact source and observations. Model-authored helper stubs may compile so the model can test a parent reduction before solving its children; no compiled sketch is proof evidence.
Independent review distinguishes semantic defects from incomplete proofs. The final active-project target must pass the transitive axiom audit, including imported helpers; changing a dependency invalidates its earlier project identity.

Every changed statement receives independent review in one retained session: first read exact Lean and support code with question/theory/author judgments inaccessible, record a hash-bound Markdown read-back, then reveal intent for comparison.
Read-back remains immutable within that review; code comments are still untrusted visible source, and this model-assisted comparison is not human certification. When a candidate is rejected, it cannot be handed back unchanged after temporary edits:
the same Formalizer receives a hash-bound observation and must submit a changed
target/support project or report an unresolved formal gap. A source candidate can count as theorem evidence
only when all of the following bind to the same artifact:

- question, theorem target, declaration, content-addressed project, build order, path, and source hash;
- independent semantic acceptance of the exact statement;
- a fresh active-project Lean check of the exact bytes;
- Lean/AXLE/kernel success with no admitted proof or unsupported axiom policy.

An accepted statement is not a proof. A compiled helper lemma is not exact-target
closure. Retrieval, proof-state analogies, proof banks, and pseudo-formalization
are context only. Before promotion, a compiling artifact may record
`candidate_kernel_verified=true`, but generic `kernel_verified` and
`source_theorem_kernel_verified` remain false.

Formal RAG should align with Mathlib and Statlib declaration conventions and reuse
their active imports and definitions before introducing project-local APIs. The
canonical gitlinked `EmpericalProcessLEAN` project pins the active Lean, Mathlib,
Statlib/StatInference foundation; `lean-stat-learning-theory` and OpenProver/
CodexProver are additional resources. Search results must preserve source snapshot,
module, declaration signature, dependencies, and active-project compatibility.
See the [Statlib roadmap](https://stat-lib.github.io/roadmap.html) and
[ReProver](https://github.com/lean-dojo/reprover) for library and proof-state
search reference designs. Local Lean remains the authority.

## Artifact and observation model

Persistent control state should stay close to these primitives:

```text
TaskRef: id, owner, objective_ref, workspace_ref, budget
ArtifactRef: id, path, hash, type
Observation: tool, status, stdout_ref, stderr_ref, artifact_hash
Decision: action, target_ref, rationale_ref
```

Substantive artifacts live once in the content-addressed store. Tasks and traces
carry references, not recursive copies of prior tasks, deferred tasks, source,
and manifests. Full raw output remains available by reference; prompts receive
only the current source, active observations, target identity, and bounded
retrieval context. Semantic handoffs explicitly project current substantive
fields; provider transport, tool history, telemetry, and prior drafts stay in
the source trace rather than becoming review or retrieval inputs.

Workspace completion is parent-bound. A Theory revision retires active Algorithm,
Simulation, Formalization, accepted-review, and handoff references; historical IDs
remain audit-only. A lane counts as completed only when its recorded parent IDs
match the current immutable parents, so an old success cannot close a revised
lineage.

## Model policy

Anthropic is the current live provider. Opus is forbidden everywhere. Production
may use Haiku or Sonnet and has a hard Sonnet ceiling. Tests and evaluations use
exactly `claude-haiku-4-5-20251001` for every live model call, including retries.
They never escalate after a failure.

Tier overrides are `AI_STATISTICIAN_CLAUDE_HAIKU_MODEL` and
`AI_STATISTICIAN_CLAUDE_SONNET_MODEL`. The global
`AI_STATISTICIAN_LLM_MODEL` must not collapse cost-aware Haiku/Sonnet routing.
Every request records its resolved provider, model, tier, token use, latency, and
tool-turn count.

## Evaluation authority

Unit tests validate mechanisms, not research capability. Startup reads frozen
semantic/mechanical qualification and exact input hashes; it never reruns controls.
Task intent selects required evidence dimensions; aggregates cannot hide failures. Hidden-gold protocols 22/23 provide complete, unchanged candidate/reference files through existing read/search tools, isolated Python/R scratch and private Markdown referee reports. The artifact-specific rubric defines the review's obligations; the original question supplies target context, not responsibility for completing other stages. The native submission separates claim support (ESTABLISHED / NOT_ESTABLISHED) from document-wide error assessment (MATERIAL_ERROR_FOUND / NO_MATERIAL_ERROR_FOUND / UNRESOLVED), replacing the ambiguous SATISFIED/VIOLATED labels rather than adding another review. Existing document-status output normalizes the error assessment to FAIL/PASS/INCONCLUSIVE; overall acceptance additionally requires every claim established. Missing support alone is INCONCLUSIVE, never acceptance or a demonstrated error. Harness code does not interpret the report's mathematics or change its text. Full-task acceptance independently requires every frozen evidence dimension and terminal acceptance. Citation indexes locate text without replacing full documents; private document identities are rechecked at activation. Qualification stops after the first failed frozen control, retaining reports and marking unreviewed candidates NOT_RUN. Native request construction is shared with qualification hashing: the existing session fingerprint binds prompts, tools and sampling settings; loop and scratch settings are also frozen. The exact original-question mapping delivered to the reviewer is also hash-bound to qualification; a changed or missing context identity is rejected before calls, never backfilled from the current task. Old or changed request contracts are rejected without reexecution. Review strategy, budgets and qualification criteria are unchanged; no consumed case is rerun or relabeled. Mechanism tests do not establish referee reliability.

For formal-only gold, the visible `formal_target_contract` is the exact statement. The
canonical evaluator already binds it to unchanged model source, independent semantic
acceptance, clean axiom audit, and fresh Lean kernel promotion; gold consumes that typed
closure instead of adding a hidden proof, model judge, or second verifier.

The frozen cross-family protocol remains the strict integrated formal gate and requires
exact source-theorem closure. It measures S13, not universal product completion:
optional formalization cannot weaken S13, and S13 failure cannot erase accepted
non-formal evidence.

Benchmarks progress from reproducible published results through paper-to-code, hidden
rederivation, historical rediscovery, near-frontier extension, and true open problems.
Only hidden-gold levels measure correctness; open problems report evidence and gaps,
never success from model agreement.

## Structural constraints

New work must not reintroduce:

- a second orchestration plane after `AgentRuntime` returns;
- theorem-specific bridge/executor module families;
- a repair-patch-rerun queue hierarchy;
- routine Architect hops for local environment failures;
- dependent lanes consuming an older rejected parent after its required revision fails;
- recursive artifact payloads or manifest truth-table expansion;
- task-family conditionals in canonical authoring, proving, or review code;
- proof-bank candidates as the default live proving policy;
- additional framework wrappers before the current graph is smaller.

Repository tests enforce coarse canonical-runtime, package, and design-document size budgets as regression alarms.
The preferred response is deletion and consolidation, not moving code behind a new interface.

## Current implementation map

- `agent_runtime.py`: typed scheduling, task references, artifacts, and evidence.
- `research_agent_runtime.py`: canonical outer graph and subsystem adapters.
- `scientific_code_workspace.py`: shared direct Algorithm/Simulation Python/R source-feedback loop; neither owner has a separate planner packet.
- `scientific_sandbox.py`: isolated Pyodide/WebR execution.
- Lean revision and kernel-promotion modules: direct checks and exact evidence gate.
- `formal_source_index.py` and scoped retrievers: declaration-level formal RAG.
- `packet_validation.py`: typed validation failures and no-generation JSON reading.
- `research_agent_runtime_audit.py`: integrated evidence audit, not a scheduler.
Priorities are model-owned counterchecks, execution timing, independent gap review, and fresh evidence; never add repair agents or theorem-specific rules.
