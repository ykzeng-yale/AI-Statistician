# Portable Research Entry Point

The `skills/statistical-research` package is an initial host-native research
entry point: one skill and two relative references, without a model client,
scheduler, credentials or machine paths. It does not yet constitute the complete
portable evidence/tool release or a demonstrated scientific improvement.

From this checkout, install a project-local link into a supported discovery
directory. Do not overwrite an existing same-named skill. A copied directory
works as well; keep its `references/` beside `SKILL.md`.

Codex or Kimi:

```sh
mkdir -p .agents/skills
ln -s ../../skills/statistical-research .agents/skills/statistical-research
```

Claude Code:

```sh
mkdir -p .claude/skills
ln -s ../../skills/statistical-research .claude/skills/statistical-research
```

These commands are alternatives for the host in use. Current official skill
discovery and symlink behavior are documented by
[Codex](https://learn.chatgpt.com/docs/build-skills),
[Claude Code](https://code.claude.com/docs/en/skills), and
[Kimi](https://moonshotai.github.io/kimi-cli/en/customization/skills.html).
Confirm the skill is visible in the chosen host before a research run; changes
may require starting a new host session. Do not infer live host conformance from
successful file installation.

Use the researcher-selected host/model and its actual execution permissions for
ordinary work. Publication efficacy tests currently use local Qwen only; no
cloud host/model experiment is implied by these installation instructions.
The operator separately authorizes the installed local Claude Code host for
compatibility and user-workflow checks. These are not official open-weight
scientific results, and direct Anthropic API experiments remain excluded.
Record unavailable execution, search or independent-review capabilities rather
than silently replacing them. Native Python/R compute and optional pinned Lean
can remain on the local machine. No new VM or network proxy is required here.

## Verified Boundary

On 2026-10-01, the standard skill validator passed. Temporary project-link tests
preserved all relative references and refused an overwrite. A native Codex
`app-server` `skills/list` request discovered the enabled skill from a temporary
project, using an isolated empty `CODEX_HOME`; no thread or model turn was started.
This tests host discovery without embedding app-server in the research product.

```sh
AI_STATISTICIAN_CODEX_SKILL_CONFORMANCE=1 .venv/bin/pytest -q tests/test_portable_skill.py
```

That command passed all three checks. Claude Code and Kimi discovery/runtime
have not been tested; their instructions above follow official documented paths.
Scientific efficacy and researcher usability are not established by discovery.
The application wheel also built and installed into a clean Python 3.12 venv;
its CLI and native local-backend factory loaded outside the source checkout.
That does not establish complete Python/R/Lean research on a clean machine.
