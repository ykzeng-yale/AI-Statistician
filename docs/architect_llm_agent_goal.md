# Architect and Workspace Responsibilities

Updated: 2026-09-09.

The product objective is [goal-ai-statistician.md](goal-ai-statistician.md).
The operative delivery objective is [current_execution_goal.md](current_execution_goal.md).
Implementation and evidence boundaries belong in [production_design.md](production_design.md).
This document is a role map, not a second goal or completion protocol.

## One Graph, Retained Workspaces

`AgentRuntime` is the sole outer research graph. Architect chooses the initial
research path, resolves genuine cross-workspace conflicts and stopping decisions,
and preserves frozen user/benchmark intent. Routine file, compiler, simulation,
reviewer, and Lean observations return to their source owner without new routing.
The current graph is serial; logical independence is not concurrent execution.

TheoryDeveloper owns durable Markdown/LaTeX definitions, assumptions, derivations,
claim dependencies, counterexamples and gaps. Compact JSON indexes those files;
it is neither the mathematical argument nor a correctness certificate. Theory can
request literature, source reproduction and exploratory Python/R when useful.

AlgorithmEngineer, SimulationEngineer and Formalizer configure the shared retained
`client_tool_loop.py` with scoped environments. They can inspect files, author
complete source or exact edits, run current source, read raw observations and
revise. The harness applies model edits but never invents their content.

Independent reviewers inspect exact artifacts in separate contexts, may run
isolated diagnostic probes when available, and report grounded findings. They do
not modify the author's source or select routing. Clean-context model review is
fallible, especially when author and reviewer share the same model.

Critic reports the evidence required by task intent, including unresolved gaps.
Execution establishes execution; frozen independent evaluators establish their
empirical gates; only exact-target, statement-reviewed, axiom-clean active-project
Lean checking establishes proof. None establishes novelty automatically.

Complete coding-agent CLIs are not normal pure-LLM providers. The current backend
calls Anthropic directly; adopting Codex principles does not require embedding
Codex Core, App Server, Claude Code, or another scheduler.

## Completion and Verification

Formalization is required, advisory or not applicable according to frozen intent.
It does not block an ordinary research task merely because the product also has
a prover. Existing strict-formal development and held-out gates are unchanged.

Use synthetic mechanism tests during development, then fresh independently
qualified evaluations on unrelated tasks. Never resume, repair or rescore a
consumed evaluation. A task-specific answer, extra reviewer, fixed derivation
length or Lean grammar patch is not a shared mechanism improvement.

Tests and evaluations use exactly `claude-haiku-4-5-20251001`. Opus and automatic
escalation are forbidden. See the current goal for measured milestones and the
[redesign audit](original_goal_harness_redesign_20260909.md) for remaining work.
