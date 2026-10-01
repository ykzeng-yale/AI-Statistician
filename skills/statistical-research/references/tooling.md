# Local Tooling

The skill itself needs only the host's native file/search/execution tools.
Use the researcher's existing local Python/R environment. Installing the
AI-Statistician application or Lean foundation is optional for this entry point.
No API key is included or required by the skill.

For the standalone application, locate the actual checkout and read its README
setup and `ai-statistician --help`; do not guess a machine-specific path. The
application supplies model-driven source workspaces and its own outer graph.
Do not nest that graph inside a host-managed multi-agent graph and call it a
single architecture. Current model tests use a separately pinned local Qwen
endpoint. Hosting this skill in Codex/Claude Code/Kimi does not mean those hosts
are interchangeable stateless model providers.

For optional Lean work in EmpericalProcessLEAN:

```sh
lake env lean path/to/Changed.lean
lake build Relevant.Module
python3 scripts/shared_proof_retrieval.py --help
python3 scripts/stat_axiom_scan.py --help
```

Run these in the selected pinned project. Use retrieval when definitions or
proof state justify it, not as a mandatory ritual. The repository AGENTS file
documents shared verifier ownership. Axiom checks must use freshly built
declarations; root compilation or retrieval metadata alone is not a theorem
audit. External libraries with incompatible toolchains stay discovery sources
until an explicit tested project migration.
