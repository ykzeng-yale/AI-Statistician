# OpenAI Codex Harness Adoption

Updated: 2026-08-29

Current upstream reference: [`openai/codex` at `b8c86376`](https://github.com/openai/codex/tree/b8c86376a258e55efc8e5ecfbabc21c16c07d814), Apache-2.0.

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

## Implementation Map

| Codex primitive | AI Statistician implementation |
|---|---|
| `run_turn` model/tool continuation | `client_tool_loop.run_bounded_client_tool_loop` |
| turn-scoped model-visible tool plan | `ClientToolTurnRequest` plus workspace-specific `ClientToolDefinition` values |
| function-call output returned to the model | `ClientToolExecutionResult` appended to the same Anthropic message history |
| model-actionable versus fatal tool failure | `ClientToolInputError` versus `ClientToolRuntimeError` |
| external file edits and `apply_patch` semantics | model-authored hash-bound whole-file writes or atomic exact-edit batches |
| thread persistence and context windows | content-addressed `ClientToolWorkspaceSessionRef` and checkpoint windows |
| sandboxed command execution | `scientific_sandbox` and the active Lean project checker |
| detached exact-input review | Theory referee, scientific-source reviewer, formal-target reviewer, and final Critic workspaces |
| sparse multi-agent delegation | the sole typed `AgentRuntime` outer research graph and artifact references |

`client_tool_loop.py` is the shared inner harness. Theory, scientific coding,
Simulation, Lean, and isolated reviewers configure domain tools and terminal actions;
they do not implement competing agent loops. The session contract fingerprint binds
the exact model, system prompt, tool schemas, sampling settings, and workspace
identity before a checkpoint can resume.

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

## Deliberate Exclusions

- **Codex Core or App Server:** would duplicate session ownership and use a different
  provider protocol.
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
and isolated review. Recent theory evaluations instead exposed model/reviewer
scientific errors inside valid harness traces, including active false assertions in a
publishable Markdown argument. The future-task correction asks the existing author
and referee sessions to audit both the load-bearing chain and all remaining active
claims; it adds no parser, repair worker, scheduler, formula, or model escalation.

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
- [`run_turn` at the audited pin](https://github.com/openai/codex/blob/b8c86376a258e55efc8e5ecfbabc21c16c07d814/codex-rs/core/src/session/turn.rs)
- [tool runtime at the audited pin](https://github.com/openai/codex/blob/b8c86376a258e55efc8e5ecfbabc21c16c07d814/codex-rs/core/src/tools/parallel.rs)
- [review rubric at the audited pin](https://github.com/openai/codex/blob/b8c86376a258e55efc8e5ecfbabc21c16c07d814/codex-rs/prompts/templates/review/rubric.md)
- [Unrolling the Codex agent loop](https://openai.com/index/unrolling-the-codex-agent-loop/)
- [Unlocking the Codex harness](https://openai.com/index/unlocking-the-codex-harness/)
- [Harness engineering](https://openai.com/index/harness-engineering/)

For the canonical product graph and evidence boundaries, read
[`production_design.md`](production_design.md). For current measured capability, read
[`main_worker_status.json`](main_worker_status.json).
