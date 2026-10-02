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
[Kimi Code](https://moonshotai.github.io/kimi-code/en/customization/skills).
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

The Codex check and two filesystem checks passed. The current native Kimi Code 2.1.1 also
discovered the project-linked skill through ACP `initialize` / `session/new`,
advertised its slash command, and closed the session. The loopback inference
sentinel received zero requests. This uses the upstream CLI, not a Kimi adapter
inside our product. The old Python `kimi-cli` is archived; pin the current
[`@moonshot-ai/kimi-code`](https://github.com/MoonshotAI/kimi-code) instead.

```sh
AI_STATISTICIAN_KIMI_SKILL_CONFORMANCE=1 \
AI_STATISTICIAN_KIMI_EXECUTABLE="$KIMI_BIN" \
  .venv/bin/pytest -q tests/test_portable_skill.py
```

`KIMI_BIN` selects an operator-installed CLI; the tests never download a host.
They isolate `HOME` and `KIMI_CODE_HOME`, configure only a fake loopback model
endpoint, and send no scientific task. A separate parameterized ACP
`session/prompt` check explicitly invokes `/skill:statistical-research` and
asserts that the entire skill body reaches the captured model request. The
endpoint returns a fixed mock response, not live inference. Combined Codex/Kimi
opt-in conformance passed five checks. Ordinary tests skip these native checks.
Claude Code discovery/runtime has not yet been tested.
On 2026-10-02 a [separate real-Qwen ACP probe](../benchmarks/publication_host_conformance/kimi_acp_qwen_20261002/README.md)
verified the same native activation surface with the exact skill body in persisted
model context, one actual file read and a correct receipt. It used two local
Qwen requests; neither the installed skill nor product source was changed.
This is body-uptake/tool conformance, not a scientific task or an efficacy comparison.
Scientific efficacy and researcher usability are not established by discovery.
The application wheel also built and installed into a clean Python 3.12 venv;
its CLI and native local-backend factory loaded outside the source checkout.
That does not establish complete Python/R/Lean research on a clean machine.

The fresh local-Qwen [development replication pilot](../benchmarks/publication_development/kimi_type_ms_20261001/README.md)
ended with two failed R reproductions and no demonstrated skill-body uptake.
In this installed Kimi version, a literal slash command supplied through
non-interactive `--prompt` remained plain user text; discovery alone did not
activate the skill. Use the host's actual skill activation surface and verify
body consumption before freezing a scientific comparison. The ACP mock check
and the new independent live conformance check establish that surface, not
research efficacy. The pilot remains consumed and
separate from the unactivated official studies and historical Haiku records.

The [subsequent FDA development pair](../benchmarks/publication_development/kimi_fda_20261002/README.md)
verified real skill-body uptake but neither draw completed numerical reproduction.
Native context compaction and owner execution/claim reliability remain real
limitations. Host exit zero, installed skills and written reports do not establish
scientific completion; the records also disclose normalized versus raw output capture.
