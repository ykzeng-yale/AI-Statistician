# OpenAI Codex Harness Adoption
Updated: 2026-09-03. Current audited upstream: [`openai/codex` at `728cb12f`](https://github.com/openai/codex/tree/728cb12fe5794b0c3a8e776fb4994b1650b973a8), Apache-2.0. Codex still does not supply a reusable statistical or Lean control plane, so AI Statistician adopts no first-execution bypass or second runtime.

This document records the current architectural decision. Earlier chronological
adoption notes remain available in Git history; they are not repeated here because
the repository should provide a small map with progressive disclosure, not a growing
instruction transcript.

## Decision

Reuse Codex's harness invariants inside AI Statistician's native Anthropic-backed
workspaces. Do not embed Codex Core, App Server, Responses transport, thread store,
worktree manager, Guardian, or multi-agent scheduler.

Codex is a general software-agent runtime. It does not supply statistical semantics,
scientific evaluation authority, a theory-development method, or Lean theorem
identity. Importing its product runtime would add a second conversation owner, tool
router, provider contract, and scheduler while the frozen product and evaluation
contract requires native Claude Haiku. Selective reuse gives us the useful behavior
without duplicating the control plane.

## Adopted Invariants

1. **One retained model/tool loop per workspace.** A model chooses a tool, the
   environment executes it, and the exact observation returns to the same model
   context. Python, R, Lean, retrieval, schema, and compiler failures do not route
   through Architect or a repair agent.
2. **Capability-accurate stable tools.** One retained session sees one ordered tool
   contract. A tool is omitted when its executor or authority is absent; an empty
   backend is not advertised as a capability.
3. **Files are authoritative state.** Markdown/LaTeX, Python/R, Lean, review reports,
   and execution artifacts live once as hash-bound files. Messages and tasks carry
   references rather than recursive payload copies.
4. **The model authors every substantive edit.** Runtime may apply an exact atomic
   edit and reject stale or ambiguous input, but it does not write mathematics,
   source patches, statistical answers, Lean syntax, imports, tactics, or proof
   bodies.
5. **Tool failures divide at the environment boundary.** Model-actionable failures
   become observations. Internal failures stop and preserve pending state without
   exposing secrets or starting a correction worker.
6. **Natural termination and explicit continuation.** A response with no tool call
   ends the current workspace segment. Exact state and transcript lineage may be
   checkpointed for an explicit continuation; the harness does not append a private
   instruction and resample or promote free-form text as domain evidence.
7. **Review is isolated and findings-first.** A reviewer sees the exact objective and
   immutable candidate, reports every discrete material finding, and does not fix the
   source. Findings return to the original source owner.
8. **Enforce boundaries, not implementations.** Identity, provenance, permissions,
   budgets, blinding, frozen task intent, and verifier authority are mechanical.
   Research content, tool choice, derivation order, experiments, and proof strategy
   remain model-owned.
9. **One schema defines each tool ABI.** The model-visible contract, executable
   argument validation, and terminal disposition must agree. A prose example is not
   a second enum. This is the direct lesson from Task108's Critic transport failure
   and Codex's separation of tool specifications from registered runtimes.
10. **Authorization, durable state, and conversation lineage are distinct.** A root fingerprint binds
    the exact question and runtime-owned operator requirements, excluding a propagated
    model plan. Resumable Theory transcripts also bind the exact durable workspace
    hash. Compaction, replanning, review, and feedback cannot silently change state or authority. Authorization
    fields must gate tool/model execution; telemetry-only denial is an authority bug.
11. **Execution success is observation, not semantic authority.** Codex's detached
    review contract requires a demonstrated defect, and Guardian treats transcript,
    tool arguments, and tool results as untrusted evidence. AI Statistician applies
    the same rule to mathematical scratch, simulation diagnostics, source retrieval,
    and Lean feedback: a successful tool call proves that the submitted action ran,
    not that its encoded stochastic model, theorem statement, or interpretation was
    correct. The responsible model must inspect those choices before promoting an
    observation to a finding or claim.

## Implementation Map

| Codex primitive | AI Statistician implementation |
|---|---|
| `run_turn` model/tool continuation | `client_tool_loop.run_bounded_client_tool_loop` |
| `ToolRouter` model-visible specification plus executable registry | ordered `ClientToolDefinition` values plus the workspace execution callback |
| turn-scoped model-visible tool plan | `ClientToolTurnRequest` plus workspace-specific `ClientToolDefinition` values |
| function-call output returned to the model | `ClientToolExecutionResult` appended to the same Anthropic message history |
| model-actionable versus fatal tool failure | `ClientToolInputError` versus `ClientToolRuntimeError` |
| external file edits and `apply_patch` semantics | model-authored hash-bound whole-file writes or atomic exact-edit batches; Python/R and Lean target/support manifests open first, exact files are read on demand, and accepted Lean projects persist as content-addressed references |
| thread persistence and context windows | root-authorized, content-addressed `ClientToolWorkspaceSessionRef` with durable-state-bound checkpoint windows |
| sandboxed command execution | `scientific_sandbox` and the active Lean project checker |
| detached exact-input review | Theory referee, scientific-source reviewer, formal-target reviewer, and final Critic workspaces |
| request-scoped capability plan and sparse delegation | Architect-selected evidence dimensions over configured workspaces, plus the sole typed `AgentRuntime`, exact artifact references, and preserved pending work before a frozen cross-owner continuation |
| trusted continuation lineage | exact parent `ClientToolWorkspaceSessionRef`, checkpoint identity, and typed `AgentTask`/artifact references |
| reviewer tool output as untrusted evidence | reviewer-owned same-language probes and falsification of scratch assumptions, source observations, and candidate semantics before a finding is submitted |

`client_tool_loop.py` is the shared inner harness. Theory, scientific coding,
Simulation, Lean, and isolated reviewers configure domain tools and terminal actions;
they do not implement competing agent loops. The session contract fingerprint binds
the exact model, system prompt, tool schemas, sampling settings, workspace identity,
immutable source/tool-environment snapshot, and root authorization fingerprint before a checkpoint can resume.
Hidden semantic evaluator qualification follows the same lifecycle separation: it
runs in an evaluator-owned session and is written as a hash-bound activation record.
The product CLI verifies and reuses that record before runtime; it cannot qualify a
judge inline and then continue directly into the first product model turn.

This mapping does not justify a new global tool framework. The current shared loop
already separates advertised definitions from execution. A registry extraction is
worth doing only when a measured workspace defect shows duplicated dispatch or ABI
drift that the extraction actually removes.

## Workspace Responsibilities

| Workspace | Model-owned work | Harness-owned authority |
|---|---|---|
| TheoryDeveloper | Search sources, write and locally revise Markdown/LaTeX, run scratch calculations, retract claims, expose unresolved gaps | File identity, immutable checkpoints, source horizon, budgets, and artifact hashes |
| AlgorithmEngineer | Navigate frozen projects or public repositories, explicitly import selected exact source or text assets, write Python/R source, execute current bytes, inspect raw stderr/tests, revise the same project | Source horizon, isolated scientific environment, resource/secret policy, source lineage |
| SimulationEngineer | Search methodological sources, write or extend simulation source, run exploratory diagnostics, inspect consumer output | Source horizon, frozen confirmatory protocol, hidden cohorts, metric authority, execution evidence |
| Formalizer | Search Statlib/Mathlib, inspect goals, write target/support modules, choose build order, compile, and revise from raw diagnostics | Active foundation identity, exact project hash, kernel and axiom authority |
| Independent reviewer | Read exact immutable candidate and report discrete findings | Clean context, read-only candidate, reviewer identity, no source edits |
| Architect | Resolve unfrozen evidence requirements and genuine cross-workspace conflicts | One outer graph, operator-frozen intent, stopping and resource ownership |

Every authoring workspace therefore has the same small inner shape:

```text
model chooses read/search/edit/execute
  -> domain environment returns the raw observation
  -> the same retained model context decides the next action
  -> explicit checkpoint, honest gap, or natural stop
```

There is no content-level repair harness between those steps.

## Research Collaboration

The outer graph coordinates objectives and evidence dependencies, not routine source
work:

```text
Question and source horizon
  -> persistent Theory workspace <-> exploratory Python/R and Simulation
  -> independent theory/source review
  -> frozen confirmatory evaluation
  -> optional, advisory, or required Lean workspace
  -> multidimensional Critic report and verifier gates
```

Theory may use literature search, scratch calculation, and early diagnostic code in
the same long-horizon investigation. Algorithm and Simulation can begin once their
consumed estimand, DGP, and executable interfaces are stable; they need not wait for
every theorem. Exploratory outcomes may revise theory but cannot satisfy frozen
confirmatory gates.

Formalization is selected by task intent. A light Lean scout may run in parallel to
expose ambiguous definitions, while expensive proof normally begins after the exact
statement stabilizes. A formal gap blocks only a required formal task. Lean retrieval,
compilation, and proof-state output return to the same Formalizer; only the active
kernel and exact theorem-identity gate can create proof evidence.

Architect handles initial planning, true cross-workspace conflicts, resource
allocation, and stopping. It is not a message bus for compiler errors, reviewer
findings with an unambiguous source owner, or local source revision.

Codex Multi-Agent V2 makes two distinctions that AI Statistician should preserve
without importing its scheduler:

- A spawned worker may inherit no turns, a bounded tail, or full history. Independent
  scientific reviewers should receive no author conversation history, only the exact
  objective and immutable artifact references. Source-owner continuation should
  resume its own bounded history and checkpoint.
- A queued `send_message` does not itself start another turn, while a
  `followup_task` does. In AI Statistician, an informational message is context only;
  an explicit typed `AgentTask` is what authorizes work. Neither one is evidence until
  its referenced artifact is executed, reviewed, or kernel-verified by the relevant
  authority.

The current outer runtime has one explicit `next_task`. Consequently,
`dual_track` currently describes dependency policy, not concurrent execution. Do not
hide that fact or add a second scheduler. If independent Theory, empirical, and Lean
work later demonstrate a real wall-clock bottleneck, extend the same runtime with a
minimal ready set of hash-bound tasks, deterministic join semantics, and no shared
mutable workspace. That change needs a concurrency test and a measured benefit.

## Deliberate Exclusions

- **Codex Core or App Server:** would duplicate session ownership and use a different
  provider protocol.
- **Codex SDK as a wrapper:** it is a client for Codex's App Server, not a small
  provider-neutral loop; adopting it would reintroduce the duplicated runtime above.
- **Codex multi-agent scheduler or Symphony:** would create a second outer graph and
  does not add statistical reasoning or evidence authority.
- **Shared evaluator worktrees:** would weaken hidden-gold and reviewer isolation.
- **Generic shell access in every product workspace:** domain sandboxes expose the
  required scientific and Lean capabilities without secrets, network leakage, or
  evaluator access.
- **Codex as a pure generator backend:** a complete coding agent owns tools and state;
  pretending it is a stateless LLM would make execution lineage ambiguous.

These exclusions are not claims that the components are poor. They preserve the
single-runtime, exact-Haiku, and verifier-owned authority contracts of this project.

## Current Assessment

The inner harness is no longer the main architecture blocker. It preserves exact files, capability-matched tools and instructions, root authorization, durable-state-bound transcript continuation, isolated review, and bounded continuation. Lean target/support files use model-selected compile order and incremental `.olean` reuse inside one session, while semantic review and kernel promotion bind and cleanly replay the same content-addressed project. Same-owner progress and author-review-author feedback stay inside independently bounded collaboration segments; Theory scratch allowances are segment-local while execution lineage remains cumulative, and accepted evidence entering another lane and cross-artifact conflicts remain outer graph transitions.
For file-backed Theory revisions, the isolated referee may request an exact parent-to-current unified diff from the immutable checkpoint manifest; the diff is navigation only, current candidate ranges remain mandatory review input, and neither a changed hunk nor its hash is mathematical evidence.
Fresh unfrozen tasks now receive one Architect-authored four-dimension capability plan over only configured workspaces; frozen operator intent wins, model-owned dimensions remain revisable on genuine replans, and the provider schema is the sole structural contract.
Three immutable evaluations refined these boundaries without changing scores:

- Task111 separated theory quality from finite exploratory readiness and made source
  hash changes provenance rather than evidence of finding progress.
- Task112 showed that successful referee scratch execution validates only the submitted
  program. A blocker now requires the referee to check its stochastic object and
  assumptions against the candidate, source, and frozen objective; unresolved conflict
  remains uncertainty.
- Task113 showed the positive Codex pattern: exact-Haiku TheoryDeveloper passed hidden theory authority using Markdown/LaTeX, scratch, and checkpoint tools, while
  AlgorithmEngineer wrote, ran, edited, reran, and committed source in one retained owner loop. It remains immutable 0/1, leaving 7/113 overall, because reviewer-owned
  probe failures, pre-candidate JSON normalization, and a reviewer-local regeneration budget were misattributed to or prematurely terminal for source work.

For future tasks, a probe failure before target invocation cannot support a source judgment. Reviewer-authored Python or R probes now invoke exact immutable candidates
with native request and response values in the same runtime; only final probe metrics cross the JSON boundary. A source-only finding returns to its immutable source owner
under the sole AgentRuntime budget; only a genuine cross-artifact conflict reaches Architect, and outer exhaustion preserves the pending task. Confirmatory Simulation
retains its separately bounded fresh-cohort adaptation and JSON-finite ABI. The model still chooses cases, findings, code, Lean actions, and verdicts; runtime enforces
identity, execution, and provenance. No consumed task is reassessed.

Required pinned replication stays in the retained Theory source-owner loop. The model runs one immutable operator-curated snapshot, audits raw observations and exact reads,
writes Markdown, and binds the report alone or into the same physical Theory workspace. The full evidence view retains that report, while a Theory packet excludes it from mathematical authority; non-theory tasks continue the frozen plan without another Architect call.
Algorithm and Simulation resolve the exact checkpoint and read its report through hash-bound tools. Their retained source owner can create, read, edit, remove, or atomically import model-selected exact UTF-8 source, configuration, fixture, or text-data files from an observed frozen snapshot or previously completed commit/path/hash-bound public reads, then run and commit the complete Python/R project; one project hash binds every file through independent review, downstream estimator execution, and hidden evaluation. Empty text files are valid; binary assets remain in the separately bound replication lane. Any failed import identity leaves the project unchanged. The Critic reloads the same evidence; execution never validates theory, code, simulation, novelty, or proof.
Declared PDFs and images now use the same Codex-style raw-observation principle: the exact hash-rechecked bytes return as provider-native media only when the source owner selects inspection. The harness neither captions them nor promotes visual access into semantic authority. [Anthropic's client-tool contract](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls) explicitly permits image and document content inside `tool_result`.
The same sparse-collaboration rule now applies when a Theory referee keeps findings active but marks a finite execution handoff ready: frozen task intent selects Algorithm or direct Simulation, that retained owner runs its normal source/tool loop, and compact raw exploratory observations return to the exact parent Theory workspace. Confirmatory evaluator authoring stays unavailable until independent Theory acceptance; no Architect message loop, repair worker, or second scheduler mediates ordinary execution feedback.

Remaining capability gaps are scientific rather than reasons to import Codex. Source owners can select horizon-safe arXiv text, navigate frozen or pinned GitHub trees, and atomically import selected exact source and text assets. Evaluators can acquire an exact public GitHub SHA through a shallow no-credential HTTPS-only fetch, or freeze an existing local commit, including empty text, binary execution assets, and identity-checked relative links to regular files in that same tree; all later object reads disable lazy fetch before the no-network copy-on-write replication lane. Git LFS/submodules, directory or chained links, arbitrary publisher PDF/OCR, environment reconstruction, binary dataset acquisition, and judged paper reproduction remain incomplete:

- long-horizon TheoryDeveloper quality and independent mathematical falsification;
- arbitrary package/environment reconstruction, datasets, and full paper projects;
- proof-state-driven Lean closure on exact statistical theorems;
- fresh cross-family end-to-end evidence.

Public sources remain model-selected, hash-bound literature inputs, never review or proof. Provenance is recorded when a workspace runs; unreachable post-hoc inference
and closure-counting code is removed rather than retained.

The next change should be justified by a disjoint frozen evaluation or a concrete
shared mechanism defect. No consumed task is rerun, repaired, rescored, or used to
introduce task-family rules.

## Primary Sources

- [OpenAI Codex repository](https://github.com/openai/codex)
- [`run_turn`](https://github.com/openai/codex/blob/728cb12fe5794b0c3a8e776fb4994b1650b973a8/codex-rs/core/src/session/turn.rs) and [`ToolRouter`](https://github.com/openai/codex/blob/728cb12fe5794b0c3a8e776fb4994b1650b973a8/codex-rs/core/src/tools/router.rs) at the audited pin
- [Detached review skill](https://github.com/openai/codex/blob/728cb12fe5794b0c3a8e776fb4994b1650b973a8/codex-rs/skills/src/assets/samples/review-agent/SKILL.md) and [Guardian evidence treatment](https://github.com/openai/codex/blob/728cb12fe5794b0c3a8e776fb4994b1650b973a8/codex-rs/ext/guardian-v2/src/sync_reviewer/prompt.rs)
- [Multi-Agent V2 spawn and fork semantics](https://github.com/openai/codex/blob/728cb12fe5794b0c3a8e776fb4994b1650b973a8/codex-rs/core/src/tools/handlers/multi_agents_v2/spawn.rs)
- [Multi-Agent V2 queued-message versus follow-up semantics](https://github.com/openai/codex/blob/728cb12fe5794b0c3a8e776fb4994b1650b973a8/codex-rs/core/src/tools/handlers/multi_agents_v2/message_tool.rs)
- [Host-verified answers retained across compaction and rollback](https://github.com/openai/codex/commit/5971d428)
- [Experimental token-budget context management, limited to eligible Codex-backend sessions](https://github.com/openai/codex/commit/cff76fa9)
- [App Server protocol](https://github.com/openai/codex/blob/728cb12fe5794b0c3a8e776fb4994b1650b973a8/codex-rs/app-server/README.md)
- [Codex as a platform: build on the open agent harness](https://developers.openai.com/blog/codex-as-a-platform)
- [Unlocking the Codex harness](https://openai.com/index/unlocking-the-codex-harness/)
- [Harness engineering](https://openai.com/index/harness-engineering/)
For the product graph and current measured capability, read [`production_design.md`](production_design.md) and [`main_worker_status.json`](main_worker_status.json).
