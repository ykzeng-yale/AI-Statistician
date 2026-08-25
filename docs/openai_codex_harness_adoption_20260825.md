# OpenAI Codex harness adoption audit

Date: 2026-08-25

Upstream reviewed: [`openai/codex`](https://github.com/openai/codex) at
`d52478c52ef09f001142a4b82339467c3880877f` (Apache-2.0).

Primary references:

- [`run_turn`](https://github.com/openai/codex/blob/d52478c52ef09f001142a4b82339467c3880877f/codex-rs/core/src/session/turn.rs)
- [`ToolRouter`](https://github.com/openai/codex/blob/d52478c52ef09f001142a4b82339467c3880877f/codex-rs/core/src/tools/router.rs)
- [parallel tool execution](https://github.com/openai/codex/blob/d52478c52ef09f001142a4b82339467c3880877f/codex-rs/core/src/tools/parallel.rs)
- [app-server thread/turn/item protocol](https://github.com/openai/codex/blob/d52478c52ef09f001142a4b82339467c3880877f/codex-rs/app-server/README.md)
- [multi-agent message tool](https://github.com/openai/codex/blob/d52478c52ef09f001142a4b82339467c3880877f/codex-rs/core/src/tools/handlers/multi_agents_v2/message_tool.rs)
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

## Explicit non-adoptions

- No Codex TUI, app-server, MCP server, approval UI, or thread database inside
  the canonical research runtime.
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
failure. The next likely candidate is provider-neutral transcript compaction at
durable checkpoints for genuinely long-horizon Theory and Lean sessions. It
must preserve exact artifact state and finding lineage and should be evaluated
on disjoint frozen tasks before becoming canonical.
