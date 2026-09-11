# Research Harness Reuse Strategy

Research date: 2026-09-11. AI-Statistician baseline: `884b77da`.
Scope: coding-agent harnesses, mathematical research, scientific research,
formalization, research memory, and evaluation. This is an engineering research
report, not a new runtime, benchmark activation, or capability result.

## Executive Decision

**Reuse more executable infrastructure and source-grounded operating knowledge;
add less orchestration.** The existing single outer research graph and retained
Anthropic tool loop are the right ownership boundary. They are not a reason to
reimplement every environment, parser, search component, or library extractor.
Conversely, a popular framework is not automatically a suitable dependency.

The highest-value change is to let the product researcher acquire permitted
sources, construct an isolated environment, execute and inspect a baseline, and
continue research in that same project. Currently, important parts of this work
are still prepared by the operator. A better prompt cannot expose an unavailable
action. More reviewer qualification does not close that product gap.

The second priority is reusable, versioned operating context and recoverable
research memory. Repo-To-Skill provides a particularly relevant new direction:
distill repository knowledge into progressively loaded skills without replacing
the downstream harness. Its controlled results use GPT-5.5, not this project's
Haiku model, and include preparation outside the downstream execution budget.
That makes it a testable adoption hypothesis, not a transferable success rate.[^arex-paper]

For Lean, reuse elaborated dependency extraction, stable statement identities,
goal-aware retrieval, and curated library conventions. Keep proof attempts
separate from target statements. Do not import an entire mission service,
Slurm controller, or tactic-search framework merely to obtain those features.

This report does **not** establish new research-E2E success. It does not justify
reopening any consumed evaluation. The native goal's stale text remains unchanged;
the operative execution goal is maintained in the repository.

## Evidence and Coverage

The supplied local collection contains **120 unique URLs in eight groups**, not
120 independently read papers. All 120 title/URL rows were triaged; the collection
outline, coverage audit, verification caveats, and relevant master-outline sections
were read. The HTML presentations were inventoried, not counted as extra papers.
The original files were not modified. Their primary registry, `paper_links.json`,
has SHA-256 `4c9c9828ab69c4028c5429ee0be6852385e5a358cd59eb8aae50fe922a35aa7b`.

| Local group | URLs | Relevance to this implementation |
|---|---:|---|
| Mathematical research systems | 14 | Research workspace, exploration, verification |
| Provers, RL, self-play | 30 | Separate inference infrastructure from model training |
| Autoformalization and benchmarks | 15 | Target fidelity and evaluator design |
| Conjectures, counterexamples, lemma discovery | 18 | Model-led falsification and reusable knowledge |
| Retrieval and dependency graphs | 13 | Accessible premises and source identity |
| Logic, HoTT, certificates, diagrammatic foundations | 22 | Background; not six new product subsystems |
| Multimodal mathematics | 6 | Future figure/equation ingestion, not current core scope |
| Other code and datasets | 2 | Benchmark resources |

The collection's dependency spine is pedagogical. It must not become a product
pipeline that requires formal proof before informal discovery can proceed. Its
own `needs_verification.md` appropriately withholds uncertain names such as
QED-Bridge and an exact Mini-CTX-v2 paper. This review does not upgrade those
entries to verified sources. The linked Lean `transfer` documentation is from
the old Mathlib documentation tree; availability in the active Lean 4 project
must be checked, not inferred from that link.

Evidence below distinguishes:

- **Code inspected:** named implementation files at an exact commit, not an audit
  of every line, dependency, branch, or security property in that repository.
- **Paper inspected:** relevant architecture, evaluation, or limitation sections;
  reported results remain the authors' results.
- **Inventory/prior audit:** local Git identity and an existing adoption record,
  without claiming a fresh implementation review.
- **Proposal:** a recommended change, not an installed or tested capability.

New searches used primary papers, official engineering publications, and original
repositories. Secondary search results were discovery leads, not evidence for
architecture or performance claims. No external setup script, research agent,
model benchmark, or contributed skill script was executed during this review.

## What the Systems Actually Teach

### Coding Harnesses: Keep the Loop Small, Not the Environment Powerless

Codex separates a tool's advertised contract, execution lifetime, cancellation,
and parallel admission. Its inspected `ToolCallRuntime` retains the step that
advertised a tool and uses a read/write gate for parallel versus exclusive calls.
This is a useful mechanism for concurrent observations without concurrent edits
to the same artifact. It is not permission to import Codex's entire product
control plane.[^codex]

Pi similarly separates durable agent messages from the model-input conversion.
The current loop has explicit continuation, steering, turn preparation, and
truncated-tool-call handling. Describing today's repository as merely four tools
and a tiny prompt misses real lifecycle machinery. Reuse the separation between
stored history and the context selected for one model call, not its TypeScript
application around our Python graph.[^pi]

mini-SWE-agent supplies a genuinely small command environment. Its Docker adapter
can execute arbitrary commands, but also interprets a magic stdout line as task
submission and merges stderr into stdout. Its default run arguments do not by
themselves supply this project's network, secret, or evidence policy. Reusing it
unchanged would therefore replace more than command execution.[^mini]

OpenHands is useful when a product wants an integrated remote agent platform.
Its inspected `DockerWorkspace`, however, starts an OpenHands agent-server image
and exposes workspace operations through HTTP. It is not a standalone container
wrapper. Adopting its conversation, server, and workspace stack here would be a
runtime replacement, not a small plugin.[^openhands]

Anthropic's standalone sandbox runtime is the more promising narrow dependency:
it wraps ordinary processes using OS sandboxing and network filtering without
requiring Claude Code or a model provider. Its default filesystem read access is
broad, so explicit read restrictions and adversarial isolation tests are mandatory.
It does not freeze package versions or make an environment reproducible by
itself.[^srt]

**Implementation qualification, 2026-09-11:** the pinned npm release `0.0.76`
was tested through its standalone SDK on this macOS host. It remains a development
dependency used only by [qualification fixtures](../tests/test_native_project_execution.py),
not a product executor or model tool. Five checks pass: scoped filesystem and
credential isolation with raw feedback, ordinary local Python environment/package
preparation, command timeout, output limits, and proxy allow/deny versus direct
socket denial. The proxy fixture explicitly clears localhost bypass and uses the
proxy's numeric loopback address; default Python/urllib localhost resolution did
not work under the restricted read profile. This is not a claim of arbitrary
networked package-manager compatibility or native R support.

One **strict expected qualification failure** is retained: a child that creates
a new session can write into the project after the wrapper has returned its
receipt and called SRT reset. The test triggers that write after return, then
kills its own synthetic child. This is a process-lifetime gap in our proposed
embedding, not evidence that the child escaped SRT's file/network policy. Do not
activate this candidate, freeze its still-mutable workspace as execution evidence,
or patch around it with a new process-tree controller. A qualified Linux/OCI
lifetime boundary is a separate adoption requirement. No Linux test, R process,
model call, research draw, or replication/proof credit came from this experiment.

**OCI/VM qualification, 2026-09-11:** Apple's standalone `container` supplies
the missing kind of lifetime boundary without an agent framework. Release 1.4.1
at `9a8917ca2da5cd6ba059b9ba5ca5a74892e9bb7d` was inspected and run on macOS
26.5.2/arm64. Its signed installer SHA-256 is
`c0d2716afefbb194c93fae662e9cae7cc186bcbcf746816608ec673dd648a6a4`;
Apple package signature, notarization and executable signature checks passed.
The payload was expanded under the existing external-resource directory and
started using official `--install-root`/`--app-root` options, without a system
installation. No Docker/Podman runtime was already installed on this host.[^apple-container]

The [original qualification fixture](https://github.com/ykzeng-yale/AI-Statistician/blob/66da48fbb05ad5e3050d7547145b0c688b4f24c5/tests/test_oci_project_execution.py)
uses pinned official Python 3.12.13 and R 4.6.1 OCI digests, no network attachment,
read-only guest root, dropped Linux capabilities, an unprivileged guest UID,
one writable synthetic project, bounded CPU/memory/time/output, and no inherited
credentials, SSH forwarding or host-home mount. Separate output streams retain
raw diagnostics. Each command ends with upstream VM deletion before a receipt;
we do not implement process-tree monitoring. Six checks pass: file/network/secret
isolation with a nonzero exit, offline Python environment/package reuse, offline
R package/library reuse, and detached-child containment after normal exit,
timeout and output overflow. In the three lifetime cases, the host creates a
trigger after receipt that would allow a surviving child to write; no late write
occurs and the container is absent. This exercises actual native R, not WebR.

The first five-check run exposed a fixture I/O bug: after overflow it stopped
reading but kept the pipes open, blocking upstream deletion on output backpressure.
Closing the abandoned readers before deletion fixed that generic ownership error;
the subsequent six-check run passed in 20.28 seconds. Cleanup failure produces no
receipt, not a successful execution. This is not an upstream security certification.
The live tests are opt-in through `AI_STATISTICIAN_TEST_APPLE_CONTAINER`, require
an already started exact-version service and locally acquired digest-addressed
images, and never install software or start services during default pytest runs.

That initial qualification was test-only. The following integration replaces its
duplicate runner with tests against the product adapter. The macOS SRT
non-adoption result remains unchanged; native plumbing is not autonomous reproduction.

### Offline Native Project Tool

The concrete [native adapter](../ai_statistician/native_project.py) now exposes
`run_project_command` to the existing Theory and Scientific source owners only
when explicitly configured. There is no new scheduler, agent or error-repair
policy. The model supplies the exact shell command and environment key. It can
create files, install local Python/R dependencies and run tests in `/work` across
commands and session reconstruction. Ordinary command errors return unchanged.

Each command uses a new upstream VM around the same named project volume. The
guest has no network, no host credentials, no control socket, a read-only root,
and no capabilities. Only a trusted empty-volume ownership initializer gets
CHOWN; model commands are non-root. A model-selected, previously acquired exact
repository revision can mount read-only at `/source`; unlisted files or changed
source identity prevent the mount. No author/evaluator/session store is mounted.

Receipts bind command, exact runtime/image/owner policy, optional source identity,
parent receipt, raw stream hashes and the volume's before/after hashes. Upstream
VM deletion precedes sealing. On the next valid invocation, interrupted commands
are cleaned up and reported, not replayed. If the receipt was sealed before state persistence failed, recovery
adopts those exact bytes rather than regenerating the result. The newly requested
command is not run during recovery. This is interruption recovery for exploratory
tools, never permission to reopen a consumed scientific evaluation.

The [adapter tests](../tests/test_native_project.py) exercise actual Python/R,
dependency reuse, denied network/host access, source selection, retained owner
feedback, volume exhaustion, mutation detection and both receipt interruption
points. They exposed a real configuration mismatch: requesting 64 MiB produced a
128 MiB ext4 image. The adapter checks actual allocation against the configured
limit before executing anything, not just the upstream metadata field. No custom
filesystem formatter or process-tree monitor was introduced.

To enable prospectively, set `AI_STATISTICIAN_NATIVE_PROJECT_CONFIG` to an explicit
local JSON policy with exactly these fields:

```json
{
  "container_executable": "/absolute/path/to/container",
  "environments": {
    "python": "docker.io/library/python@sha256:4766d8b510c428e595d74b9cc5bbb2fae8e26316fffb4adc89908d79aacd58a2",
    "r": "docker.io/library/r-base@sha256:41d5564375009abf74a63987fd7fb9b44c90b1580b310be10ef973abe92496c3"
  },
  "cpus": 1,
  "memory_bytes": 536870912,
  "volume_bytes": 134217728,
  "timeout_seconds": 30,
  "max_output_bytes": 1000000
}
```

These are example explicit limits, not automatic product defaults. The operator
must start qualified container 1.4.1 and preload the chosen digest-addressed images.
The adapter never starts services, fetches images or switches execution backends.
Volumes persist for continuation; their owned names and receipts are recorded under
the source workspace's `.native_project` directory. Remove an owned volume with
the upstream volume command only when abandoning that exploratory workspace.

Native success cannot accept scientific source, certify reproduction, confirm a
metric or prove a theorem. Existing release/review/confirmation paths are unchanged.
Independent reviewers do not receive this tool. Networked package acquisition,
environment reconstruction from an arbitrary paper, portable Linux-host support,
and fresh model-driven scientific capability still need evidence. Abrupt host
controller death can leave its VM running until the next invocation or explicit
operator cleanup; this adapter is not an unattended VM lease service. The wall
timeout depends on the controller remaining alive. No model API
call, benchmark activation or research credit came from this integration.

### Long-Horizon Theory: Native Files, Uncertainty, and Recoverable Context

The AI co-mathematician is an interactive, asynchronous mathematical workspace:
agents use shared files and communication, track uncertainty and failed hypotheses,
and produce native mathematical artifacts. Its human-directed workbench is not
evidence of fully autonomous statistical discovery, but its representation of
unfinished research is directly relevant.[^comath]

Aletheia uses a generator, natural-language verifier, and reviser on top of Gemini
Deep Think. It also emphasizes literature and computation tools, while noting
that real citations can still be misrepresented. It is evidence against treating
either zero-shot generation or citation existence as sufficient. It does not
require us to instantiate a new Reviser role: our original source owner can do
that work after independent feedback.[^aletheia]

Anthropic's long-running application study also retains structured planning and
evaluation, rather than removing all harness rules. It reports that some older
continuation scaffolding became unnecessary with stronger models. The general
lesson is to ablate scaffolding against the actual model, not copy either the old
rule or its removal universally. These experiments used Opus; this project must
not reproduce their model configuration.[^anthropic-long]

Its managed-agent architecture makes a stronger reusable distinction: the durable
session, model harness, and execution sandbox have independent lifetimes. Stored
events remain available even when the context window is compacted. Credentials
are not placed in the generated-code environment. This separation is useful with
direct Anthropic API calls; the hosted service itself is not required.[^anthropic-session]

### Operational Knowledge: A Real Reuse Opportunity, Not Another Router

The inspected AREX-Skill repository has separate portable repository skills and
a DisCo runtime derived from Pi. Its architecture supports loading a small part
of a larger corpus and records source provenance. The portable content, not the
copied coding-agent runtime, is the relevant adoption unit.[^arex-code]

The `statsmodels` skill is a useful concrete example: it routes to focused API
guidance and records a source commit. It also instructs readers not to return to
original documentation. We must not adopt that restriction. A generated skill
can be stale or wrong; current source and actual execution remain available to
the model. Its environment smoke helper was inspected by reference, not executed
or independently certified here.[^arex-statsmodels]

This resolves a false choice in earlier discussions. Domain knowledge is allowed
in source-grounded, optional context. It is not allowed to become a hidden
runtime branch or a benchmark-answer prompt. A skill may explain an API or a
published method; it must not silently prescribe an acceptance threshold, change
the estimand, or force an error-specific repair. Skill construction must not read
hidden benchmark answers, and its cost must be reported separately from research.

**Implemented context boundary, 2026-09-11:** Theory, Scientific and Lean owners
now configure one shared `read_workspace_history` tool in the existing retained
loop. Exact tool observations are stored as content-addressed files beside the
existing session records, independently of bounded model messages. A session keeps
only its own observation references and a hash-bound parent link. The model can
inspect a catalog or read selected character ranges, including older windows and
previously omitted long results, without replaying the old tool.
Selectors use stable content hashes, not per-window ordinals, so a replayed
omission notice still identifies the same original observation. Namespace,
authorization, contract and byte-identity checks remain in the existing store;
assistant thinking/signatures are not part of the observation surface. Independent
reviewers do not receive author-history access. This implements the durable-event
versus selected-context distinction, not a new memory service, summary model or
demonstration of improved mathematical judgment. Consumed evaluations are unchanged.

PaperQA offers another concrete reuse boundary. Its `read_doc` handles document
parsing/chunking through a supplied PDF parser; `Docs` adds indexing, embeddings,
and model-backed evidence gathering. Start below its agent layer. Do not call
`aquery` as an untracked second researcher or inherit model/embedding defaults.
PDF extraction still needs page identity and equation-quality checks; document
RAG is not a theorem parser.[^paperqa]

### Scientific Discovery: Search Needs a Trustworthy Objective

ERA's small `futs.search` accepts generation and execution callbacks and ranks
candidate programs. It is unusually suitable for direct, attributed algorithmic
reuse when an exploratory score already exists. It should replace a candidate
selection routine inside an existing workspace, not schedule the whole research
lab. It cannot supply a valid statistical objective.[^era]

ShinkaEvolve provides a larger program database and evolutionary search machinery,
including parent selection, islands, and model selection. These are optional
optimization methods, not requirements for theory development. A single fixed
Haiku model rules out copying its model-ensemble policy. ERA is the lower-complexity
first candidate unless an experiment shows the larger search machinery is needed.[^shinka]

AI Scientist-v2 uses an experiment manager, staged search, candidate journals,
execution results, and plotting/review machinery. Its source is not a minimal
unconstrained agent: the manager encodes main experimental stages and the journal
has many task-specific fields. The inspected release also uses a custom AI
Scientist Source Code License. Learn from experiment ancestry and negative results;
do not copy its controller or assume permissive licensing.[^scientist]

Kosmos uses parallel literature and analysis work linked through a structured
world model. Its paper reports 79.4% accuracy across 102 statements, with only
57.9% accuracy for synthesis statements. These are small, selected report-level
measurements, not general statistical-research reliability. The important lesson
is claim-to-source/analysis traceability and skepticism at synthesis boundaries;
no audited reusable Kosmos core implementation was established here.[^kosmos]

Robin has public code, but important literature/data-analysis services require
Edison access. Its biomedical ranking pipeline is not a general mathematical
reasoner. FARS reports four sequential stages and a shared auditable workspace,
including failed or negative trajectories; publication count is not correctness.
Neither supplies a reason to recreate a compulsory multi-stage waterfall here.[^robin][^fars]

### Lean: Compose Checked Dependencies, Not Repair Taxonomies

Numina's inspected runner invokes Claude CLI and tracks statements, rounds, and
safe verification. AxProverBase actually uses a LangGraph with proposer, builder,
reviewer, memory, and typed feedback. Both support environment-driven iteration;
neither supports the claim that all mature provers have no control structure.
Their drivers should not be embedded alongside our retained API loop.[^numina][^axprover]

LeanMarathon has a concrete DAG query server and isolated proof work, but also
Slurm jobs, GitHub handoffs, refiners, and stop hooks. Its DAG server depends on
its blueprint verifier and LeanArchitect format. Reuse dependency-scoped views
or the component only where that format is already used; do not import its
cluster/workflow machinery into ordinary statistical research.[^leanmarathon]

Prove2Me separates immutable statements from multiple proof attempts, supports
conditional reductions, and uses blinded read-back plus human auditing of a
curated mission core. A sorry-free parent file importing an open child is still
conditional, not a closed theorem. Our final authority must check the complete
dependency closure in the active project; a remote accepted sketch cannot replace
that check.[^prove2me-paper]

The current public workspace contains an especially useful extractor:
`extract_decl_graph.lean` walks the elaborated environment and distinguishes
`typeDeps` from `valueDeps`, retaining relevant private/internal dependencies.
It is an example parameterized by editing project roots, not a ready universal
package. No root license was found in the inspected checkout. Adaptation or
vendoring requires clear terms and active-toolchain compatibility; the native
Lean API approach can be adopted without copying its example wholesale.[^prove2me-code]

ReProver makes premise accessibility explicit using file and position, then
executes model tactics against Lean state. Its retriever/search stack includes
trained models and older toolchain dependencies. The useful contract is accessible
premises plus state/action feedback, not a promise that adding MCTS or a vector
index makes the current Haiku prover stronger.[^reprover]

## Current Product Gaps and Their Replacement Boundaries

| Priority | Observed implementation | Consequence | Change and consolidation target |
|---|---|---|---|
| 1 | `theory_workspace.py:615-625` requires configured source execution for required replication; `research_source_project.py` acquisition is exposed through CLI, not this researcher tool surface | Operator prepares part of the research environment | Make acquisition and environment preparation model-directed within the existing source/project workspace; reuse the existing snapshot and execution identities |
| 1 | `scientific_sandbox.py` has a finite Pyodide package cache and base-oriented webR surface | Arbitrary published Python/R projects remain out of reach | Add a native isolated command backend to the existing project executor, not one installer or fallback per package |
| 2 | `client_tool_loop.py:554-675` restores checkpoint-bound state and optionally recent complete rounds; it is not general model-selectable access to all prior observations | Durable lineage is stronger than long-horizon working memory | Extend reads over the existing immutable session/artifact store; avoid a second memory database or mandatory summary agent |
| 2 | Public discovery has search/read observations and exact source handles, but no coherent model-owned environment lifecycle | Finding a repository is not reproducing it | Connect existing discovery, acquisition, file import, and command execution; keep one provenance chain |
| 3 | `agent_runtime.py` owns serial/interleaved workspace transitions | Independent experiments or stable-lemma work cannot yet overlap | Add isolated ready-task execution and exact-input joins inside that graph; retain one writer per artifact |
| 3 | `lean_rag_dependency.py` includes source-derived lexical reference inference | Useful discovery references are not complete elaborated dependencies | Prefer native environment extraction for compiled libraries; retain lexical fallback only as explicitly non-authoritative discovery |

These are interface and environment limitations. They do not establish that every
mathematical failure is a harness defect. The existing Markdown/LaTeX theory
workspace, direct Python/R/Lean feedback, scoped file edits, independent review,
and optional formal intent are real and should not be rebuilt under new names.

### 1. Model-Owned Source and Environment Work

Public acquisition now connects a permitted source handle to an immutable
snapshot and existing read/import tools. The next native integration should let
the researcher author its environment recipe and run ordinary project commands.
The model chooses dependencies, entrypoint, tests, exploratory changes, and
interpretation. The executor records the resolved source, data, package state,
working directory, outputs, and process status.

The standalone macOS SRT prototype failed lifetime qualification. The explicit
Apple OCI/VM candidate above passes six native checks, but its test fixture is not
a product adapter. Keep the current WASM backend where it is selected; never
silently switch environments after failure. Native adoption is an execution
selection, not model escalation, a new agent framework, or scientific authority.

Dependency acquisition and computation need different capabilities. Installation
can use explicitly allowed registries in a disposable secret-free environment;
frozen confirmation runs from the resolved environment without network access.
No model API key, evaluator directory, host home directory, or Docker control
socket belongs inside generated-code execution. A source repository's setup
commands are untrusted code, not authorization.

The replacement removes the need for Codex to manually install one paper's R
packages, select its command, or translate an installation error into product
rules. It does not remove operator control over allowed resources or data access.
Use ordinary package managers and pinned environment artifacts, not a registry
of package-specific recovery handlers.

### 2. Long-Horizon Theory and Useful Operating Context

Retain authoritative mathematics in Markdown/LaTeX, with model-chosen claim labels,
assumptions, derivations, unresolved gaps, and rejected approaches. Do not mandate
a fixed number of files, equations, candidates, or counterexample attempts.
Stable claim references are useful; a large compulsory JSON ontology is not.

Expose prior research observations by exact session/artifact reference and bounded
range through existing read mechanisms. A model-authored checkpoint can summarize
what matters, while original observations remain recoverable. Summaries are
working context, not replacements for sources or proof evidence. The current
checkpoint identity and authorization checks must survive this change.

Offer a small, versioned catalog of relevant operating references through existing
source/file tools. Start with selected, inspected package and Lean workflows, not
all 5,000 AREX skills in a system prompt. The model decides what to open. Content
must retain provenance, applicability, unresolved verification status, and access
to its original source. Do not install DisCo or add its router/controller.

An operating reference helps use a tool; a reusable theorem or statistical method
needs its own statement, assumptions, source, and validation. Neither is a hidden
answer bank. A later disjoint task must demonstrate actual use before we call
this capability improvement or library learning.

### 3. Collaboration Without Routine Architect Routing

Theory can request an exploratory implementation once the relevant estimand and
interface are usable, before the complete theory is finished. Simulation can
return a concrete counterexample or disagreement. The original author revises
the affected claims; ordinary code/Lean errors remain local to their source owner.

For parallel work, use exact input versions, isolated writable projects, and
result references. A join checks whether its parent inputs are still current.
Changed premises invalidate dependent evidence, not unrelated work. A model may
replan when findings genuinely conflict or a research direction changes; the
Architect should not mediate every search, edit, or compile result.

Start with safe independent observations or independent experiment projects.
Do not implement a multi-agent message bus, global knowledge-graph service,
or a second scheduler merely to obtain concurrency. Count provider calls,
environment time, and research decisions separately. A tool result is not itself
a new scientific planning iteration.

### 4. Formal Library Reuse and Foundation Management

The latest inspected Statlib is `78eb985e`, declaring Lean `v4.33.0-rc2` and
Mathlib `3ef2c2e2`. The active EmpericalProcessLEAN foundation remains a different,
older compatible set. The existing migration audit already found whole-project
failures on a prior 4.33 candidate. This review did not compile the new pin or
promote it. New upstream declarations must remain discovery-only until checked
in the selected project.[^statlib][^migration]

Statlib organizes statistical definitions over measures/kernels, with mathematical
modules and a separate `ForMathlib` area. Its roadmap is a research agenda, not
implemented coverage. SLT provides another useful pattern: topic modules and
precise textbook theorem references, with human-supervised statement checking.
Neither justifies claiming all three books are formalized or merging incompatible
libraries wholesale.[^statlib][^slt]

For our previous book/library work, retain source book/edition/theorem references,
canonical mathematical names, assumptions, module imports, and checked dependency
closures. Compare existing declarations before inventing another definition.
Use a dedicated library migration to reconcile genuine conflicts, with model-led
edits and whole-project Lean checks; do not add Python grammar patches.

For reusable foundations, prefer curated Statlib/Mathlib-style modules. For
application-specific claims, Prove2Me-style independent statement/proof objects
are useful. These are complementary roles, not a reason to atomize every basic
definition or recreate Formalpedia locally. Existing RAG should expose the active
module, statement, source, and actual accessibility to the proving model.

Heavy formalization is optional unless the frozen task requires it. It can run
alongside confirmatory simulation after statements stabilize; foundational lemmas
can be investigated earlier. An advisory formal failure is a finding, not a
universal veto on empirical work.

## Adoption Ledger

Pins below identify inspected snapshots, not production dependencies. Source paths
are relative to their upstream repositories. A missing root license is a recorded
uncertainty, not a claim that no permission can exist elsewhere.

| Resource / pin | Inspected boundary | Decision |
|---|---|---|
| Codex `654b0a77` | `core/src/tools/parallel.rs`, `router.rs` under `codex-rs` | Adapt lifecycle/concurrency contracts; Apache-2.0; no runtime embedding |
| Pi `b2158840` | `packages/agent/src/agent-loop.ts` | Adapt history/context/continuation separation; MIT; no second loop |
| mini-SWE-agent `04d809ce` | `src/minisweagent/environments/docker.py`, default-agent entrypoints | Small environment reference; MIT; remove submission coupling if reused |
| OpenHands SDK `9bc73b48` | Docker workspace and terminal/conversation layout | Defer full stack; MIT; not a standalone executor |
| Anthropic sandbox runtime `c392e6cf` | `sandbox-manager.ts`, configuration and security documentation | Test-only; detached macOS process lifetime failed qualification; Apache-2.0 |
| Apple container `9a8917ca` / 1.4.1 | Startup, forced VM deletion, volume allocation and native adapter checks | Explicit offline Theory/Scientific command tool; no second scheduler or custom process monitor; Apache-2.0 |
| AREX-Skill `ac3fe1af` | Architecture, statsmodels skill and provenance | Select portable operating context; inspect per-file terms; no DisCo runtime |
| PaperQA `57e89f72` | `src/paperqa/readers.py`, `docs.py` boundaries | Reuse parsing/chunk provenance below agent layer; Apache-2.0 |
| ERA `440711e3` | `implementation/futs.py` | Direct search-component candidate only with a trustworthy exploratory score; Apache-2.0 |
| ShinkaEvolve `9912af12` | `shinka/database/dbase.py`, search design | Defer larger evolutionary machinery; Apache-2.0; no model ensemble |
| AI Scientist-v2 `96bd5161` | Experiment manager, journal, license | Design reference; custom source license; no controller copy |
| Robin `4a5cce31` | Candidate/analysis boundaries, async utilities, README | Design reference; Apache-2.0; external service dependence |
| Numina `1c9af8a5` | `scripts/runner.py` | General Lean workspace pattern; no Claude CLI driver; root license not found |
| AxProverBase `0f5a80aa` | `src/ax_prover/prover/agent.py` | Feedback/independent review reference; no LangGraph import |
| LeanMarathon `e2febe2c` | DAG server and workspace/worktree design | Dependency-scoped context; no Slurm/PR/stop-hook controller |
| Prove2Me `efc07126` | `mission_auditor.md`, `extract_decl_graph.lean` | Statement/proof split and native extraction; root license not found; no service access claimed |
| ReProver `fd6d99c0` | Premise accessibility and tactic execution | Reuse state/accessibility contracts; check model/toolchain dependencies before code adoption |
| Statlib `78eb985e` | `Inference.lean`, module tree, Lake/toolchain configuration | Foundation candidate, not active authority; Apache-2.0 |
| SLT `d0f506f0` | Committed README/module map and source references | Reusable mathematics and conventions; Apache-2.0; working-tree changes left untouched |

Previously supplied resources remain important, but were not falsely counted as
fresh whole-repository audits:

- EmpericalProcessLEAN `4cec7860`: active foundation and existing migration audit.
- OpenProver `3960746d`: local identity and existing source/provider adoption map.
- CodexProver `d6345529`: local identity and prior architecture/branch audit.
- Discover-and-Prove `6dd99de4`: local inventory and primary paper; not a new
  implementation-level adoption decision in this review.
- Kosmos, Aletheia, AI co-mathematician, and FARS: relevant paper sections; no
  audited deployable core established here. Denario's public description names
  AG2/LangGraph/cmbagent and GPL-3/Apache components; it is not a low-cost way to
  preserve our single graph.[^denario]

The previous [Codex adoption map](openai_codex_harness_adoption_20260825.md),
[Prove2Me boundary](prove2me_adoption_20260904.md), and
[original-goal audit](original_goal_harness_redesign_20260909.md) remain useful.
The change in emphasis is executable environment reuse and verified operating
context, not another round of controller wrappers.

## Verification Before Capability Claims

Use deterministic harness tests for mechanics and fresh, prospectively defined
tasks for scientific capability. Do not mine consumed evaluations for new prompt
rules or use their outputs to qualify a replacement judge.

| Proposed change | Mechanism verification | Fresh capability evidence |
|---|---|---|
| Native source environment | Secret/host/evaluator isolation; denied network; exact source/environment identity; process cancellation; no silent backend switch | Product chooses and reproduces permitted Python and R projects without operator-authored install/entrypoint repair |
| Recoverable research memory | Old observations remain byte-identical and accessible only to authorized sessions; stale inputs cannot gain current authority | Long derivation continues across context windows, preserving a failed approach and revising a dependent claim correctly |
| Operating references | Version/provenance visibility; hidden-source exclusion; skill content cannot grant tools or alter gates | Preregistered disjoint matched task variants with/without selected context; report preparation and downstream cost separately |
| Isolated concurrency | No shared writes; exact-input joins; changed parent invalidates only dependent results; cancellation is observable | Theory and independent experiment/lemma work overlap and their findings are actually consumed |
| Native Lean dependency graph | Compare extracted dependencies to compiled fixtures, including private constants and open children | Retrieved supporting lemma is imported and used in an unrelated exact target under the active project |

PaperBench supplies an important distinction between implementing code and
actually reproducing paper results, with author-developed rubrics and a separate
judge benchmark. CORE-Bench varies how much reproducibility infrastructure is
provided. ScienceAgentBench tests concrete scientific programs across tasks;
SciAgentArena expands the scientific scale. Reuse their task/evaluator separation
and existing public artifacts where licenses and scope fit, rather than inventing
another product-specific rubric framework.[^paperbench][^corebench][^sciencebench][^sciarena]

The evaluation ladder remains: known-result components, source replication,
paper-to-code reproduction, hidden known-theory rederivation, historical
rediscovery, extensions, then genuine open questions. Publication cutoffs do not
remove pretraining contamination. Do not treat paper-count, Elo, imports,
compilation of helpers, or reviewer agreement as a research-E2E win.

All model tests remain direct API calls to exactly
`claude-haiku-4-5-20251001`. No Opus, automatic escalation, external service agent,
or default third-party model is introduced. This report has made no model calls
and had not executed or installed the proposed components at the initial review.
The later SRT qualification and explicit OCI/VM integration above record their
setup, test coverage and adoption boundaries; they do not retroactively expand
the literature audit.

## Sources

Numbered references identify primary materials and inspected source paths.
Access date for online sources: 2026-09-11. Short Git pins in the ledger resolve
to the full pins in these source links.

[^codex]: OpenAI, [Codex tool execution](https://github.com/openai/codex/blob/654b0a77d0d2f81aa21f61caf7af4be88fe550bb/codex-rs/core/src/tools/parallel.rs), [tool router](https://github.com/openai/codex/blob/654b0a77d0d2f81aa21f61caf7af4be88fe550bb/codex-rs/core/src/tools/router.rs). Official [runtime options](https://developers.openai.com/api/docs/guides/agents#compare-agent-runtime-options) distinguish managed Codex, SDK, and direct API responsibilities.
[^pi]: Mario Zechner and contributors, [Pi agent loop](https://github.com/badlogic/pi-mono/blob/b215884021491772a1eb7a9f92c6653a2a52a69d/packages/agent/src/agent-loop.ts).
[^mini]: SWE-agent contributors, [mini-SWE-agent Docker environment](https://github.com/SWE-agent/mini-swe-agent/blob/04d809ceab9df28f9adaed044884180159172930/src/minisweagent/environments/docker.py), [agent](https://github.com/SWE-agent/mini-swe-agent/blob/04d809ceab9df28f9adaed044884180159172930/src/minisweagent/agents/default.py).
[^openhands]: OpenHands, [Docker workspace](https://github.com/OpenHands/software-agent-sdk/blob/9bc73b48bda5d345049e44df0199d04939ac0aba/openhands-workspace/openhands/workspace/docker/workspace.py).
[^srt]: Anthropic, [standalone sandbox runtime](https://github.com/anthropic-experimental/sandbox-runtime/tree/c392e6cf9f8df957c66d9ab1461e2cfa99b1ab5d), [sandbox manager](https://github.com/anthropic-experimental/sandbox-runtime/blob/c392e6cf9f8df957c66d9ab1461e2cfa99b1ab5d/src/sandbox/sandbox-manager.ts).
[^apple-container]: Apple, [container 1.4.1 release](https://github.com/apple/container/releases/tag/1.4.1), [official startup paths](https://github.com/apple/container/blob/9a8917ca2da5cd6ba059b9ba5ca5a74892e9bb7d/Sources/ContainerCommands/System/SystemStart.swift), [forced deletion](https://github.com/apple/container/blob/9a8917ca2da5cd6ba059b9ba5ca5a74892e9bb7d/Sources/Services/ContainerAPIService/Server/Containers/ContainersService.swift), [guest shutdown](https://github.com/apple/container/blob/9a8917ca2da5cd6ba059b9ba5ca5a74892e9bb7d/Sources/Services/RuntimeLinux/Server/RuntimeService.swift). Apache-2.0. Named implementation paths inspected, not a full repository/security audit.
[^comath]: Zheng et al., [AI co-mathematician](https://arxiv.org/html/2605.06651v2), May 2026, workspace and collaboration sections.
[^aletheia]: Feng et al., [Towards Autonomous Mathematics Research](https://arxiv.org/html/2602.10177v1), February 2026, sections 2 and 5.
[^anthropic-long]: Anthropic, [Harness design for long-running application development](https://www.anthropic.com/engineering/harness-design-long-running-apps), March 24, 2026.
[^anthropic-session]: Anthropic, [Scaling Managed Agents: Decoupling the brain from the hands](https://www.anthropic.com/engineering/managed-agents), April 8, 2026. Also [context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents), September 29, 2025.
[^arex-paper]: Chen et al., [Repo-To-Skill: Distilling GitHub Repositories Into AI4AI Skills](https://arxiv.org/html/2609.02749v1), September 2, 2026, sections 3-5 and appendix A. The PaperBench comparison reports 29.45% versus 39.59%, a 10.14-point difference, not a 34.4-point difference; that latter number is relative improvement.
[^arex-code]: VectorSpaceLab, [AREX-Skill architecture](https://github.com/VectorSpaceLab/AREX-Skill/blob/ac3fe1afa80fb9a09775ecfb2b6cc3ba850a2db6/docs/architecture.md).
[^arex-statsmodels]: VectorSpaceLab, [statsmodels operating skill](https://github.com/VectorSpaceLab/AREX-Skill/blob/ac3fe1afa80fb9a09775ecfb2b6cc3ba850a2db6/skills/repositories/repo-skills/statsmodels/SKILL.md), [provenance](https://github.com/VectorSpaceLab/AREX-Skill/blob/ac3fe1afa80fb9a09775ecfb2b6cc3ba850a2db6/skills/repositories/repo-skills/statsmodels/references/repo-provenance.md).
[^paperqa]: FutureHouse, [PaperQA readers](https://github.com/Future-House/paper-qa/blob/57e89f7223b0960d5ee5ea048c69e3c47e088572/src/paperqa/readers.py), [document store](https://github.com/Future-House/paper-qa/blob/57e89f7223b0960d5ee5ea048c69e3c47e088572/src/paperqa/docs.py).
[^era]: Google Research, [ERA flat-UCB search](https://github.com/google-research/era/blob/440711e3bef52692e18eaa2400462cc01052d756/implementation/futs.py).
[^shinka]: Sakana AI, [ShinkaEvolve](https://arxiv.org/abs/2509.19349), September 2025; [program database](https://github.com/SakanaAI/ShinkaEvolve/blob/9912af12d423504b8d580f4179fd15f5f88b8c50/shinka/database/dbase.py).
[^scientist]: Sakana AI, [AI Scientist-v2 experiment manager](https://github.com/SakanaAI/AI-Scientist-v2/blob/96bd51617cfdbb494a9fc283af00fe090edfae48/ai_scientist/treesearch/agent_manager.py), [journal](https://github.com/SakanaAI/AI-Scientist-v2/blob/96bd51617cfdbb494a9fc283af00fe090edfae48/ai_scientist/treesearch/journal.py), [license](https://github.com/SakanaAI/AI-Scientist-v2/blob/96bd51617cfdbb494a9fc283af00fe090edfae48/LICENSE).
[^kosmos]: Mitchener et al., [Kosmos: An AI Scientist for Autonomous Discovery](https://arxiv.org/html/2511.02824v1), November 2025, section 2.1 and evaluation methods.
[^robin]: FutureHouse, [Robin](https://github.com/Future-House/robin/tree/4a5cce310f3bc7663a67117db88af43b84733ffe), especially README prerequisites and `robin/analyses.py`, `candidates.py`, `utils.py`.
[^fars]: Tang et al., [FARS: A Fully Automated Research System Deployed at Scale](https://arxiv.org/html/2606.31651v1), June 30, 2026, architecture and deployment limitations. Related [AI co-scientist](https://arxiv.org/html/2502.18864v1), February 2025, section 4 explicitly distinguishes Elo from independent ground truth.
[^numina]: Project Numina, [runner](https://github.com/project-numina/numina-lean-agent/blob/1c9af8a52e715f22fede766425ba3d3b95526132/scripts/runner.py); [paper](https://arxiv.org/abs/2601.14027), January 2026, previously inspected in the original-goal audit.
[^axprover]: Axiomatic AI, [AxProverBase agent](https://github.com/Axiomatic-AI/ax-prover-base/blob/0f5a80aa4c5adf7fa03909b69c8ee374c9846c10/src/ax_prover/prover/agent.py); [paper](https://arxiv.org/abs/2602.24273), February 2026.
[^leanmarathon]: Yuanhe Zhang and contributors, [LeanMarathon DAG server](https://github.com/YuanheZ/LeanMarathon/blob/e2febe2ce717ef5d8410909683f6f5b301bda4c2/mcp-servers/dag-tracker/dag_tracker_mcp.py), [README](https://github.com/YuanheZ/LeanMarathon/blob/e2febe2ce717ef5d8410909683f6f5b301bda4c2/README.md); [paper](https://arxiv.org/abs/2606.05400), June 2026.
[^prove2me-paper]: Chen et al., [Prove2Me](https://arxiv.org/html/2608.28433v1), August 28, 2026, sections 3-4.
[^prove2me-code]: Prove2Me, [declaration extractor](https://github.com/prove2me/prove2me_workspace/blob/efc071262fe7aa27eac5059809abe111e7865c53/scripts/extract_decl_graph.lean), [read-back guidance](https://github.com/prove2me/prove2me_workspace/blob/efc071262fe7aa27eac5059809abe111e7865c53/references/mission_auditor.md).
[^reprover]: LeanDojo, [premise accessibility](https://github.com/lean-dojo/ReProver/blob/fd6d99c01e8bd8fd8f3fd1de4cd0bc4a7f158eaa/common.py), [proof search](https://github.com/lean-dojo/ReProver/blob/fd6d99c01e8bd8fd8f3fd1de4cd0bc4a7f158eaa/prover/proof_search.py), [LeanDojo paper](https://arxiv.org/abs/2306.15626), 2023.
[^statlib]: Statlib, [inference definitions](https://github.com/stat-lib/statlib/blob/78eb985eb37d3e85f93ad76ddd6ff3ae55bf2a1d/Statlib/Inference.lean), [Lake configuration](https://github.com/stat-lib/statlib/blob/78eb985eb37d3e85f93ad76ddd6ff3ae55bf2a1d/lakefile.toml), [roadmap](https://stat-lib.github.io/roadmap.html).
[^migration]: AI-Statistician, [Statlib 4.33 migration audit](statlib_4_33_migration_audit_20260830.md), existing measured build evidence, not rerun here.
[^slt]: Yuanhe Zhang, Jason D. Lee, Fanghui Liu, [Statistical Learning Theory in Lean](https://github.com/YuanheZ/lean-stat-learning-theory/blob/d0f506f0a695018265dccb33bcb05e2f5ca1c876/README.md), [AI4SLT paper](https://arxiv.org/abs/2602.02285). README's reported coverage and supervised-development claims were not independently rebuilt here.
[^denario]: AstroPilot-AI, [Denario](https://github.com/AstroPilot-AI/Denario), public project description and licensing boundary; no local code audit.
[^paperbench]: OpenAI, [PaperBench](https://openai.com/index/paperbench/), April 2, 2025; [public implementation](https://github.com/openai/frontier-evals/tree/main/project/paperbench). No evaluator code imported in this review.
[^corebench]: [CORE-Bench](https://arxiv.org/html/2409.11363v1), September 2024, reproducibility task design.
[^sciencebench]: [ScienceAgentBench](https://arxiv.org/html/2410.05080v1), October 2024, scientific-program evaluation.
[^sciarena]: [SciAgentArena](https://arxiv.org/abs/2606.12736), June 2026; [project and task resources](https://sciagentarena.github.io/). Resource-level inspection, not independent benchmark execution.
