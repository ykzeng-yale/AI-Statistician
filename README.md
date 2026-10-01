# AI Statistician

AI Statistician is an in-progress autonomous statistical theory laboratory. Its
target is to take a fresh research question or paper through rigorous theory,
scientific Python/R implementation and simulation, plus Lean formalization and
exact kernel-checked theorem closure when task intent requests it, inside one
evidence-preserving agent runtime.

This repository is not yet the finished system. The latest authoritative
cross-family development panel remains at 0/2 exact source-theorem closures, and
the held-out panel is sealed. Passing unit tests or compiling support lemmas does
not change that claim.

The canonical architecture and current boundary are documented in
[Production Design](docs/production_design.md). Read the [original product goal](docs/goal-ai-statistician.md)
and [current execution goal](docs/current_execution_goal.md); current worker status
is machine-readable in [main_worker_status.json](docs/main_worker_status.json).

The current delivery goal is two distinct, evidence-backed publications: a
portable research harness for existing coding agents and a complete single-API
multi-agent statistical research system. See the [publication programme](docs/publication_programme.md).
The initial [portable skill installation](docs/portable_harness_installation.md)
and [local Qwen testing](docs/local_qwen_testing.md) are available separately;
neither is a claim of publication-ready scientific performance.

## Architecture

There is one outer typed graph:

```text
Goal, source horizon, and task-intent evidence requirements
  -> source search / baseline reproduction when applicable
  -> persistent Markdown/LaTeX Theory <-> exploratory Python/R diagnostics
  -> independent review of stable claims and exact scientific source
  -> frozen confirmatory Simulation
  -> final critic and task-intent-bound evidence report

Stable claims -> intent-selected Lean workspace -> separately reported kernel evidence
```

Theory, Python, R, and Lean use the same source-agent pattern:

```text
model chooses a tool, writes complete source, or authors an exact structured edit
  -> isolated environment applies or executes the exact artifact
  -> raw observation returns to the same model
  -> model authors the next source or edit
```

The runtime owns generic edit/application semantics, execution, artifact hashes,
target identity, budgets,
permissions, checkpoints, independent-review separation, and evidence labels.
It does not author source patches, statistical answers, Lean grammar fixes, or
tactic recipes. There is no hidden repair agent or post-runtime scheduler.
Complete coding-agent CLIs are not treated as normal pure-LLM providers; any
future adapter must preserve the same execution and evidence boundaries.

Only a semantically accepted, exact hash-bound target that passes a fresh local
Lean identity and axiom check can become source-theorem proof evidence.

## Model Policy

Local inference is now the default. Future model tests use the existing
`Qwen3-4B-Instruct-2507` deployment through a local OpenAI-compatible endpoint;
no Anthropic API calls or automatic cloud fallback are used for new tests.
Historical Haiku evaluations and qualifications remain unchanged. Legacy
`--research-eval` and hidden-gold protocols still encode their original Haiku
authority: a new Qwen publication protocol must be qualified separately before
scientific comparisons. Local transport conformance is not research success.

The standalone system does not require Claude Code. Explicit Anthropic production
support remains available, capped at Sonnet, but it is not the testing backend.

Relevant environment variables:

```text
ANTHROPIC_API_KEY
AI_STATISTICIAN_LOCAL_BASE_URL=http://127.0.0.1:8081/v1
AI_STATISTICIAN_LOCAL_MODEL=Qwen3-4B-Instruct-2507
AI_STATISTICIAN_CLAUDE_HAIKU_MODEL
AI_STATISTICIAN_CLAUDE_SONNET_MODEL
```

Never commit credentials. The runtime records the resolved provider, model,
tier, token use, latency, and tool-turn count in evidence artifacts.

Pinned Haiku tool workspaces can opt into native extended thinking with
`AI_STATISTICIAN_HAIKU_TOOL_THINKING_BUDGET_TOKENS`. It defaults to `0` (off);
an enabled value must be at least 1024 and below each affected request's
`max_tokens`, which remains the total output ceiling. Enable it before freezing a
fresh run. The resolved request uses automatic tool selection, preserves signed
thinking blocks and binds the budget into session identity. It does not enable
interleaved thinking, escalate models or change tool-free Architect calls.
Hidden-gold reviewers use the same explicit setting; qualification and candidate
review must share its frozen value. Changing it invalidates prior qualification.
This is supported transport, not demonstrated improvement in scientific accuracy.
See [Anthropic's thinking documentation](https://platform.claude.com/docs/en/build-with-claude/extended-thinking).
These thinking settings apply only to historical/explicit Anthropic use, not Qwen.

## Setup

Create the Python environment:

```bash
git submodule update --init --recursive
python3 -m venv .venv
.venv/bin/pip install -e '.[test,llm]'
```

Prepare the repository-pinned scientific Python and R WASM runtimes:

```bash
npm ci
npm run prepare:scientific-sandbox
```

The scientific sandbox uses Pyodide for Python and WebR for R. Generated code
runs in bounded subprocesses without inherited secrets or network access. If a
required runtime is absent, the system records a capability blocker instead of
silently executing in the host process.

An explicit [offline native project tool](docs/research_harness_reuse_strategy.md#offline-native-project-tool)
also lets Theory and Scientific owners run their own commands in a persistent
Linux project. It requires a configured Apple container service and pinned images;
it does not replace reviewed source execution or confirmatory evaluation.

Lean proving defaults only to the source-controlled
`external/EmpericalProcessLEAN-main` gitlink. That project pins Lean, Mathlib, and
Statlib and must be built locally before a live formal evaluation. Alternate Lake
projects require an explicit `--lean-project`; the runtime does not silently fall
back to a historical snapshot. Use `doctor` to inspect retrieval, LSP/MCP, AXLE,
and Lean availability.

## Basic Commands

```bash
.venv/bin/python -m ai_statistician.cli list
.venv/bin/python -m ai_statistician.cli doctor --out runs/doctor
.venv/bin/python -m ai_statistician.cli research-agent-runtime --help
.venv/bin/python -m ai_statistician.cli research-agent-runtime-audit --help
.venv/bin/pytest -q
```

`research-agent-runtime` is the canonical product path. The CLI also contains
offline corpus, retrieval, proof-search, training-export, and historical audit
utilities. Those commands are support tools; their outputs do not establish
end-to-end research capability.

Published papers and pinned repository text can be exposed directly to the same
TheoryDeveloper session with `--research-source-manifest`; see
[Research Source Snapshots](docs/research_source_snapshots.md). The runtime checks
visibility, path containment, and hashes, while the model chooses searches and
interprets exact line-addressed source text. Hidden evaluation gold never belongs
in that snapshot. A separate execution manifest either fixes one preregistered
command or lets that same retained source owner iteratively choose commands inside
the frozen project while the runtime keeps the interpreter, environment, network,
resources, and source bytes fixed. The owner explicitly selects which completed
attempt its report advances; every attempted command remains immutable lineage
that the terminal Critic independently reloads. Model-selected runs remain
exploratory and cannot satisfy the operator-fixed preregistered replication gold.

The frozen development/held-out protocol is
[`benchmarks/autonomous_cross_family_e2e_protocol_20260713.json`](benchmarks/autonomous_cross_family_e2e_protocol_20260713.json).
Do not run or inspect held-out outcomes until the development gate passes.

## Formal Retrieval

The formalizer can retrieve declaration signatures, modules, dependencies, and
source context from configured Mathlib, Statlib/StatInference,
`lean-stat-learning-theory`, `EmpericalProcessLEAN`, OpenProver, and CodexProver
resources. The preferred policy is:

1. reuse active Mathlib/Statlib definitions and declaration conventions;
2. search task-bound source scopes and current proof state;
3. let the model choose premises and complete Lean source;
4. check the exact source in the active project;
5. treat every hit or generated proof candidate as context until kernel rerun.

Proof banks are optional baselines, not the default live proving policy. Old
source snapshots remain useful as RAG or evaluation data but cannot override the
active project's imports, names, or kernel.

## Evidence Boundary

Artifacts distinguish at least these states:

- LLM theory or code proposal;
- source-grounded review judgment;
- isolated Python/R execution;
- simulation under a frozen protocol;
- retrieved formal context;
- locally compiled Lean candidate artifact;
- independently accepted exact theorem statement;
- exact source-theorem kernel promotion.

An unreviewed Lean file may record `candidate_kernel_verified=true` when its exact
bytes compile, while generic `kernel_verified` and
`source_theorem_kernel_verified` remain false. This prevents a helper or weakened
statement from being counted as the requested theorem.

## Current Structure

The earlier architecture accumulated a 101k-line runtime plus large
repair/bridge/planner module families. The current cleanup has reduced the
central runtime to about 24k lines and the top-level package to fewer than 150
modules. Structural regression tests prevent those control planes from silently
returning.

The largest remaining design debts are:

- an oversized metric authoring/review/preflight implementation;
- frozen projects support same-owner command diagnosis in an operator-owned
  environment, but dependency reconstruction, external datasets, Git LFS, and
  complete paper environments remain incomplete;
- the persistent Markdown/LaTeX TheoryDeveloper and source-grounded referee still
  need unrelated live known-result evidence;
- no post-simplification live two-family exact-theorem closure yet;
- incomplete arbitrary-paper ingestion and learned research/proof policies.

The next capability gate is a fresh exact-Haiku development panel using real
scientific and Lean tools. Shared mechanism failures may improve prompts,
workspace tools, retrieval, or evidence infrastructure; they may not introduce
task-family answers or benchmark-specific rules.

## Repository Map

```text
ai_statistician/                 Runtime and subsystem implementation
benchmarks/                      Frozen evaluation protocols and suites
docs/                            Product design, evidence, and operating status
data/                            Evaluation fixtures and source metadata
legacy_sources/                  Non-authoritative source/RAG snapshots
runs/                            Generated execution and audit artifacts
tests/                           Mechanism and evidence-boundary regression tests
```
