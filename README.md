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
[Production Design](docs/production_design.md). The product objective is in
[Agent Runtime Goal](docs/architect_llm_agent_goal.md), and current worker status
is machine-readable in [main_worker_status.json](docs/main_worker_status.json).

## Architecture

There is one outer typed graph:

```text
Goal, source policy, and plan
  -> source search or exact replication when available
  -> persistent Markdown/LaTeX Theory workspace
  -> Scientific coding and simulation workspace
  -> Independent semantic review
  -> Lean formalization workspace
  -> Final critic and kernel gate
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

Anthropic is the current live provider. Production may use Haiku or Sonnet;
Opus is forbidden. Every test and evaluation call is pinned to exactly
`claude-haiku-4-5-20251001`, including retries.

Relevant environment variables:

```text
ANTHROPIC_API_KEY
AI_STATISTICIAN_CLAUDE_HAIKU_MODEL
AI_STATISTICIAN_CLAUDE_SONNET_MODEL
```

Never commit credentials. The runtime records the resolved provider, model,
tier, token use, latency, and tool-turn count in evidence artifacts.

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
in that snapshot.

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
- source acquisition and exact paper/code/data replication are not yet a complete
  model-owned workspace;
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
