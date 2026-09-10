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

## Architecture

- `ai_statistician/agent_runtime.py` is the sole outer typed research graph.
- `ai_statistician/client_tool_loop.py` is the shared retained model/tool loop.
- Theory, Python/R, Simulation, Lean, and reviewers configure that loop with scoped
  tools; do not add another scheduler, repair agent, or generic agent framework.
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

- Tests and evaluations use exactly `claude-haiku-4-5-20251001`.
- Opus is forbidden. Never add automatic model escalation.
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
