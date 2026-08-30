# OpenAI Codex Harness Adoption

Updated: 2026-08-30

Current upstream reference: [`openai/codex` at `dde85b43`](https://github.com/openai/codex/tree/dde85b435b16994f956bce08e5fb796ed94c27fd), Apache-2.0. The reproducible harness audit remains pinned at `63d21388`; the complete delta to the current head only relocates TUI Vim-history tests and does not change any audited harness surface.

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
   instruction and resample.
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
10. **Continuation provenance is explicit.** Automatic continuation keeps its exact
    parent transcript and checkpoint lineage. New reviewer feedback, a changed
    objective, or another external observation enters through a new typed task or
    explicitly identified current context; it is never silently attributed to the
    old root. This follows Codex's current invalidation of trusted turn lineage when
    external context or goal edits make attribution ambiguous.

## Implementation Map

| Codex primitive | AI Statistician implementation |
|---|---|
| `run_turn` model/tool continuation | `client_tool_loop.run_bounded_client_tool_loop` |
| `ToolRouter` model-visible specification plus executable registry | ordered `ClientToolDefinition` values plus the workspace execution callback |
| turn-scoped model-visible tool plan | `ClientToolTurnRequest` plus workspace-specific `ClientToolDefinition` values |
| function-call output returned to the model | `ClientToolExecutionResult` appended to the same Anthropic message history |
| model-actionable versus fatal tool failure | `ClientToolInputError` versus `ClientToolRuntimeError` |
| external file edits and `apply_patch` semantics | model-authored hash-bound whole-file writes or atomic exact-edit batches |
| thread persistence and context windows | content-addressed `ClientToolWorkspaceSessionRef` and checkpoint windows |
| sandboxed command execution | `scientific_sandbox` and the active Lean project checker |
| detached exact-input review | Theory referee, scientific-source reviewer, formal-target reviewer, and final Critic workspaces |
| sparse multi-agent delegation | the sole typed `AgentRuntime` outer research graph and artifact references |
| trusted continuation lineage | exact parent `ClientToolWorkspaceSessionRef`, checkpoint identity, and typed `AgentTask`/artifact references |

`client_tool_loop.py` is the shared inner harness. Theory, scientific coding,
Simulation, Lean, and isolated reviewers configure domain tools and terminal actions;
they do not implement competing agent loops. The session contract fingerprint binds
the exact model, system prompt, tool schemas, sampling settings, and workspace
identity before a checkpoint can resume.

This mapping does not justify a new global tool framework. The current shared loop
already separates advertised definitions from execution. A registry extraction is
worth doing only when a measured workspace defect shows duplicated dispatch or ABI
drift that the extraction actually removes.

## Workspace Responsibilities

| Workspace | Model-owned work | Harness-owned authority |
|---|---|---|
| TheoryDeveloper | Search sources, write and locally revise Markdown/LaTeX, run scratch calculations, retract claims, expose unresolved gaps | File identity, immutable checkpoints, source horizon, budgets, and artifact hashes |
| AlgorithmEngineer | Write Python/R source, execute current bytes, inspect raw stderr and tests, revise the same source | Isolated scientific environment, resource and secret policy, source lineage |
| SimulationEngineer | Write or extend simulation source, run exploratory diagnostics, inspect consumer output | Frozen confirmatory protocol, hidden cohorts, metric authority, execution evidence |
| Formalizer | Search Statlib/Mathlib and project declarations, inspect goals, write Lean, compile, and revise from raw diagnostics | Active Lean project identity, theorem target hash, kernel and axiom authority |
| Independent reviewer | Read exact immutable candidate and report discrete findings | Clean context, read-only candidate, reviewer identity, no source edits |
| Architect | Choose initial evidence requirements and resolve genuine cross-workspace conflicts | One outer graph, task intent, stopping and resource ownership |

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

The inner harness is no longer the main architecture blocker. It already preserves
same-owner feedback, exact files, stable tools, sparse handoffs, checkpoint identity,
and isolated review. Task111 exercised six visits to one durable Theory workspace and
five clean referee workspaces. Its latest referee found the finite estimator handoff
ready while retaining publication-level proof findings, and four consecutive reviews
reported no prior-finding progress. The old outer gate nevertheless blocked all
exploratory code and treated each source-hash change as progress.

The measured shared correction remains inside the existing retained workspaces. An
isolated referee now reports full theory quality separately from finite exploratory-
execution readiness, and the outer graph continues a rejected theory lineage only
when the referee records actual finding progress. Exact source hashes remain
provenance. The model still chooses derivations, edits, code, experiments, tools,
findings, and verdicts; runtime does not parse mathematics or generate a repair. This
is Codex-style observation placement and explicit state transition, not a new worker,
scheduler, content rule, model escalation, or second runtime. Task111 remains
immutable 0/1.

Remaining capability gaps are scientific rather than reasons to import Codex:

- long-horizon TheoryDeveloper quality and independent mathematical falsification;
- robust paper/code/data acquisition and replication;
- broader multi-file Python/R research projects;
- proof-state-driven Lean closure on exact statistical theorems;
- fresh cross-family end-to-end evidence.

The next change should be justified by a disjoint frozen evaluation or a concrete
shared mechanism defect. No consumed task is rerun, repaired, rescored, or used to
introduce task-family rules.

## Primary Sources

- [OpenAI Codex repository](https://github.com/openai/codex)
- [`run_turn` at the audited pin](https://github.com/openai/codex/blob/63d213884daea50e4f74efc192cdc44f549b67d5/codex-rs/core/src/session/turn.rs)
- [`ToolRouter` at the audited pin](https://github.com/openai/codex/blob/63d213884daea50e4f74efc192cdc44f549b67d5/codex-rs/core/src/tools/router.rs)
- [Multi-Agent V2 spawn and fork semantics](https://github.com/openai/codex/blob/63d213884daea50e4f74efc192cdc44f549b67d5/codex-rs/core/src/tools/handlers/multi_agents_v2/spawn.rs)
- [Multi-Agent V2 queued-message versus follow-up semantics](https://github.com/openai/codex/blob/63d213884daea50e4f74efc192cdc44f549b67d5/codex-rs/core/src/tools/handlers/multi_agents_v2/message_tool.rs)
- [Goal-continuation lineage preservation and invalidation](https://github.com/openai/codex/commit/4210c08defe92fe8828f789b6f9fda287ad3709e)
- [App Server protocol](https://github.com/openai/codex/blob/63d213884daea50e4f74efc192cdc44f549b67d5/codex-rs/app-server/README.md)
- [Unrolling the Codex agent loop](https://openai.com/index/unrolling-the-codex-agent-loop/)
- [Unlocking the Codex harness](https://openai.com/index/unlocking-the-codex-harness/)
- [Harness engineering](https://openai.com/index/harness-engineering/)

For the canonical product graph and evidence boundaries, read
[`production_design.md`](production_design.md). For current measured capability, read
[`main_worker_status.json`](main_worker_status.json).
