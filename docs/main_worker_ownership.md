# Main Worker Ownership

Updated: 2026-08-10

This task is the sole active implementation stream for AI Statistician. The
worker owns the central runtime, direct scientific and Lean workspaces,
cross-family evaluation, verification, commits, and pushes.

## Operating contract

- Work from `codex/runtime-eval-alignment-20260625` and keep `origin/main` on the
  same reviewed commit when changes are ready.
- Commit and push directly. Do not create a pull request unless the user changes
  this instruction.
- Inspect remote branches before integration, but do not assume another worker
  is active and do not overwrite unrelated user changes.
- Never use credentials pasted into chat or committed files. Use the machine's
  configured Git authentication; exposed tokens must be revoked separately.
- Prefer deletion and consolidation over compatibility wrappers.
- Repair system mechanisms, prompts, context, tools, and feedback loops rather
  than hand-editing benchmark outputs.
- Keep tests and live evaluations pinned to exact Haiku; never use Opus.
- Preserve independent semantic review, frozen pre-result evaluation, artifact
  hashes, exact target identity, and Lean kernel authority.
- Do not open held-out tasks until the frozen development gate passes.

## Completion discipline

No audit percentage, test count, retrieved theorem, compiled helper lemma, or LLM
judgment is an end-to-end success claim. Completion requires a fresh task lineage
from plan and theory through model-authored scientific execution and exact
source-theorem kernel closure.

Current status is recorded in [main_worker_status.json](main_worker_status.json),
and the canonical design is [production_design.md](production_design.md).
