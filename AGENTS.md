# AI Statistician Agent Map

Read this file first, then load only the documents relevant to the task. Do not use
the entire `docs/` directory as one prompt.

## Start Here

- Product and current limits: `README.md`
- Current measurable objective and resource decisions: `docs/current_execution_goal.md`
- Canonical graph and evidence boundaries: `docs/production_design.md`
- Current measured status: `docs/main_worker_status.json`
- Delivery and Git ownership: `docs/main_worker_ownership.md`
- Codex harness adoption boundary: `docs/openai_codex_harness_adoption_20260825.md`
- New user-selected backbone and migration limits: `integrations/agentic-scientist/README.md`
- Agentic Scientist source/evaluation audit: `docs/ai_scientist_v3_evidence_review_20261015.md`

## Architecture

- The 2026-10-15 user-selected new backbone is the pinned Sakana Agentic Scientist
  in `third_party/ai-scientist-v3`. Use its existing task/config/prompt/stage
  interfaces. The initial statistical integration is not completed research-E2E
  or a completed single-API migration.
- `ai_statistician/agent_runtime.py` remains the sole graph of the legacy
  standalone implementation and its preserved experiments. Never call that graph
  from the new backbone or run both as competing controllers.
- Reuse suitable scientific/Lean tools and retained-session components without
  adding another scheduler, repair agent, or generic agent framework. Do not keep
  expanding the legacy controller instead of carrying out the requested migration.
- Preserve validated statistical workspaces, source/reviewer authority, Python/R,
  simulation and Statlib/RAG/Lean assets; only the outer coordinator is replaced.
- Keep Paper S's single-model-API requirement: a CLI-backed upstream run is not
  evidence that the standalone specialist implementation is complete.
- Substantive mathematics and source live in hash-bound Markdown/LaTeX or source
  files. Tasks and traces carry references rather than recursive copies.
- The same source owner receives raw environment or reviewer observations and authors
  every revision. Runtime never writes statistical answers, source patches, Lean
  grammar fixes, tactics, or proof bodies.

## Evidence

- Preserve frozen task intent, artifact lineage, independent review, blinding, and
  verifier authority.
- Formalization is optional, advisory, or required according to task intent. Only an
  exact identity-bound, axiom-clean active-project Lean check can become proof
  evidence.
- Unit tests and model agreement are mechanism evidence, not end-to-end capability.
- Consumed evaluations are immutable: never rerun, repair, reassess, or rescore them.

## Model Policy

- Future model tests and evaluations use open-weight Qwen on the authorized Macs
  or Bouchet. Larger models and long runs are authorized; the observed
  `Qwen3-4B-Instruct-2507` Q4_K_M baseline is not a capacity ceiling.
  Freeze and verify weights, runtime, template, sampling and resource configuration
  before each new condition. Deterministic unit tests do not call a model.
- Use one consistent model condition across each comparison. Yale's shared Qwen
  service is a development option; Paper S and reproducible publication runs need
  a verified direct API and fixed weights/runtime, normally a task-owned Bouchet
  deployment. Do not build around the old 4B machine limit or silently change
  models after observing a result. See `docs/local_qwen_testing.md`.
- Do not call Anthropic for future testing. Legacy Haiku fixtures and consumed
  evaluations remain immutable. Do not reinterpret their scores as Qwen results.
- Official publication experiments start fresh with open-weight models. Historical
  Haiku runs are development records, not publication baselines or gates on the new
  studies. Claude Code is authorized only as a local coding host for portable
  harness compatibility/user-workflow tests, separately from scientific comparisons.
- Opus and automatic cloud/model escalation are forbidden.
- Never commit credentials or recover them from chat, logs, Git history, or
  incidental files. The operator-designated, gitignored `.env` is an authorized
  current credential source: use the existing CLI loader and never print values.
  An absent process variable alone does not establish missing configuration.

## Working Style

- Inspect existing code and Git state before editing.
- Prefer deletion and consolidation over wrappers, compatibility fallbacks, new
  packet types, or task-family conditionals.
- Fix shared prompts, context, tools, feedback, or evidence mechanisms rather than a
  generated benchmark answer.
- Use `apply_patch` for manual edits and keep unrelated user changes intact.

## Verification

```bash
.venv/bin/python -m compileall -q ai_statistician
.venv/bin/pytest -q
```

Use focused tests while iterating, then run the full suite before pushing a shared
mechanism change. Follow `docs/main_worker_ownership.md` for branch and push policy.
