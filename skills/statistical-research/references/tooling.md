# Local Tooling

The skill itself needs only the host's native file/search/execution tools.
Use the researcher's existing local Python/R environment. Installing the
AI-Statistician application or Lean foundation is optional for this entry point.
No API key is included or required by the skill.

Locate the actual checkout and read its README; do not guess a machine path.
The integrated research workflow is migrating to the pinned Agentic Scientist
backbone in `third_party/ai-scientist-v3`, with statistical customization under
`integrations/agentic-scientist`. Use its pipeline directly, not a call to the
legacy `research-agent-runtime` inside another graph. Existing standalone
Python/R and Lean tools may be reused without invoking that old scheduler.
The legacy application remains available for its recorded experiments. Current
model tests use a separately pinned local Qwen endpoint. Hosting this skill in
Codex/Claude Code/Kimi does not make those hosts stateless model providers or
establish the new backbone's single-API implementation.

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
