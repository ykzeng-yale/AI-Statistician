# AI Statistician

AI Statistician is an in-progress autonomous statistical theory laboratory. Its
target is to take a fresh research question or paper through rigorous theory,
scientific Python/R implementation and simulation, plus Lean formalization and
exact kernel-checked theorem closure when task intent requests it, inside one
evidence-preserving agent runtime.

This repository is not yet the finished system. Official open-weight scientific
comparisons have not started. Older development runs and sealed panels are
archived, not publication baselines or gates on the new studies. Passing unit
tests or compiling support lemmas does not establish scientific correctness or
a benefit from the harness or multi-agent collaboration.

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
Historical Haiku evaluations and qualifications remain archived and unchanged;
they are not official publication results or baselines. New `--research-eval`
and capability runs bind every live role to local Qwen. Hidden-gold schema 5 and
semantic protocols 26/27 require fresh independent qualification; historical
authority cannot be relabelled. Local transport conformance is not research success.

The standalone system does not require Claude Code. Explicit Anthropic production
support remains available, capped at Sonnet, but it is not the testing backend.
The installed local Claude Code host is separately authorized for portable
harness compatibility/user-workflow tests, not the open-weight main experiments.

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

Anthropic-specific thinking support is legacy/explicit production configuration,
not the Qwen protocol or an active publication experiment. Preserve archived
records without continuing their tuning or scorecard.

The first [native Qwen host pilot](benchmarks/publication_development/kimi_type_ms_20261001/README.md)
recorded two failed source reproductions and a missing skill-activation boundary.
Native discovery and mock activation checks now pass, but neither establishes
scientific efficacy. The official open-weight studies remain prospective.
The later [FDA paper-to-code pair](benchmarks/publication_development/kimi_fda_20261002/README.md)
verified actual skill uptake but both draws failed: native compaction exceeded
the frozen context in one arm; the other delivered unexecuted, invalid code and
missing outputs. These are immutable development failures, not publication results.

## Setup

Create the Python environment:

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[test]'
```

The default local Qwen transport needs no cloud SDK or key. The `llm` extra is
for explicitly selected Anthropic production support, not local-model tests.

Prepare the repository-pinned scientific Python and R WASM runtimes:

```bash
npm ci --omit=dev
npm run prepare:scientific-sandbox
```

The application wheel includes the execution adapters, but not npm dependencies
or downloaded scientific wheels. When using an installed wheel from a different
working directory, point the existing runtime discovery setting to the
`node_modules` prepared above:

```bash
export AI_STATISTICIAN_SCIENTIFIC_SANDBOX_NODE_MODULES="$(pwd)/node_modules"
```

The [fresh-environment installation record](benchmarks/publication_release_qualification_20261003/README.md)
tests this layout outside the source checkout on macOS. It is not a clean-machine,
cross-platform, native host-activation or model-driven scientific result.

The default scientific sandbox uses Pyodide for Python and WebR for R. Generated code
runs in bounded subprocesses without inherited secrets or network access. If a
required runtime is absent, the system records a capability blocker instead of
silently selecting an unconfigured host interpreter.

For installed native packages, configure [Python](#native-python-execution) or
[R](#native-r-execution) explicitly. The model selects `scientific_native_python`
or `scientific_native_r` in its existing source or scratch tool. Both reuse the
same project, estimator and input ABI, return raw observations to the same author,
and never fall back to another backend. Native Python/R currently
requires macOS `sandbox-exec`; this is not yet a clean-machine cross-platform release.
Operator-selected local worker ports are optional, not a model permission upgrade;
their network boundary is described below.

An explicit [offline native project tool](docs/research_harness_reuse_strategy.md#offline-native-project-tool)
also lets Theory and Scientific owners run their own commands in a persistent
Linux project. It requires a configured Apple container service and pinned images;
it does not replace reviewed source execution or confirmatory evaluation.

### Native Python Execution

Set `AI_STATISTICIAN_NATIVE_PYTHON_CONFIG` to an operator-owned JSON file using
the [same process resource fields](#native-r-execution), with `schema_version: 1`,
`runtime_language: "python"`, exact `runtime_version` and `package_versions` for
the selected environment. Bind the environment's Python executable and SHA-256;
include its base interpreter/library read roots if it is a virtual environment.
Python uses `-B -s`, preserving the bound virtual environment without inherited
secrets or user-site access. No additional package such as `jsonlite` is needed.

The trusted adapter reuses the existing Python project/estimator ABI. It checks
the interpreter and declared package versions before model source runs, and
returns raw tracebacks without AST content patches or WASM import restrictions.
The installed environment controls native package access; the model's dependency
list documents intent, not a native import-security boundary. Freeze package bytes
separately for experiments. The resource, immutable-input and local-port limitations
below also apply. Node's heap bound is not a native Python memory limit.

### Native R Execution

Set `AI_STATISTICIAN_NATIVE_R_CONFIG` to one operator-owned JSON file containing:

- `schema_version: 1`, `runtime_version`, and `package_versions` (exact R package
  names mapped to versions, including `jsonlite` for the result bridge).
- `environment_root`, `interpreter_executable_relative_path`, and
  `interpreter_executable_sha256` for the installed Rscript.
- `runtime_read_roots`, `runtime_executables` (absolute launcher paths mapped to
  SHA-256), and `runtime_environment` (for example, explicit R home/library paths).
- Optional `runtime_local_ports`: unique integer ports, empty by default. The
  source and native scientific executors permit bind/listen on those ports and outbound
  connections only to loopback at those ports. Native worker listeners can bind
  all interfaces: this is **not loopback-only inbound isolation**. Choose dedicated
  unoccupied ports, not inference, assessor or other service ports; do not enable
  it for tasks requiring complete network denial. Match and freeze this permission
  across experimental arms. Set any library-specific worker-port environment in
  `runtime_environment`; the executor neither invents it nor edits generated code.

These reuse the source executor's resource fields, without task or paper bindings.
Discovery validates resources; execution revalidates configuration and R/package
versions. Version pins are not package-content hashes; publication environments
must separately freeze their library inventory. The configuration and hash enter
the request. Native R limits CPU, elapsed time, output and open files; Node's heap
limit applies to the trusted adapter, not R memory. R resolves installed transitive
dependencies; declare directly used packages, without adding task-specific rules.
Source, project and input hashes are checked before preparation and after execution.
R writes only its own working tree; trusted requests/adapters remain outside that
write boundary. Raw stream/result reads reject links and nonregular files.
Hidden evaluators select their own frozen `execution_profile`, not the candidate's
choice. Execution is engineering evidence, not mathematical or statistical validity.

Lean proving defaults only to the source-controlled
`external/EmpericalProcessLEAN-main` gitlink. That project pins Lean, Mathlib, and
Statlib and must be built locally before a live formal evaluation. Alternate Lake
projects require an explicit `--lean-project`; the runtime does not silently fall
back to a historical snapshot. Use `doctor` to inspect retrieval, LSP/MCP, AXLE,
and Lean availability.
Initialize the optional foundation only when using it, with authorized repository
access:

```bash
git submodule update --init --recursive external/EmpericalProcessLEAN-main
```

Unavailable Lean repository access does not block installing the Python package,
running local Python/R tools or a non-formal research task. `doctor` checks
installation/configuration without making a model request; its readiness flags
do not attest a running server, weights, scientific correctness or research success.

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

The archived strict-formal development/held-out protocol is
[`benchmarks/autonomous_cross_family_e2e_protocol_20260713.json`](benchmarks/autonomous_cross_family_e2e_protocol_20260713.json).
Leave its held-out tasks sealed and consumed outcomes unchanged. Its development
gate is not a prerequisite for the new open-weight publication studies; use the
prospective [publication experiment design](docs/publication_experiments.md).

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

The next scientific evidence comes from the fresh open-weight publication
studies, not continued Haiku score tracking or an old development-panel gate.
Shared mechanism failures may improve context, workspace tools, retrieval or
evidence infrastructure; they may not introduce task-family answers or
benchmark-specific rules. Lean is required only by the frozen task intent.

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
