# Original Goal, Local Literature and Harness Redesign

Audit date: 2026-09-09. Inspected product baseline: `db6e434b`.
This is the implementation-grounded redesign rationale, not another scheduler,
model prompt, completion protocol or claim that every proposed capability exists.
The operative goal is [current_execution_goal.md](current_execution_goal.md).

## Finding

The original aim is a statistical research laboratory, not a theorem-only service
or a succession of one-shot benchmark answers. The initial downloaded goal and the
current [product objective](goal-ai-statistician.md) require rigorous theory,
scientific Python/R, literature and source reuse, empirical validation, optional
formal proof, reusable mathematical libraries and eventual cross-task improvement.

The narrow one-result objective had become an inadequate delivery strategy. The
older Architect goal also contradicted the current implementation: it made Lean
universal, described full packet regeneration, prohibited reviewer execution and
listed the already-built Theory workspace as future work. Those statements are
removed, not implemented anew. Current status no longer reports speculative
readiness percentages.

The latest [trimmed-mean draw](operator_audits/trimmed_mean_l0_v1.md) completed the
internal graph but failed frozen independent gold. Theory structural checks were
7/7, but semantic review recorded three violated and two inconclusive claims out
of six; algorithm acceptance was 2/5 and empirical acceptance 0/7. Reviewer and
Critic stages consumed 77 of 102 product turns. This demonstrates a reliability
gap, not a need for another fixed review sequence, smaller budget or task formula.
It does not isolate the mathematical cause; this audit neither reruns the draw nor
reads hidden expected answers to manufacture a correction.

## Coverage and Limits

The user-supplied local resource directory is a catalog, not a full-paper corpus:

`/Users/yukangzengcmac/Documents/Codex/2026-06-25/now/AI-Statistician/AI for Math Resources/`

All four Markdown files were read: the master collection, full collection,
coverage audit and needs-verification list. The complete `paper_links.json` was
parsed: 120 unique URLs, including alternate publication/project links, not 120
distinct fully read papers. The HTML/TXT files are alternate catalog views. The
JSON SHA-256 is `4c9c9828ab69c4028c5429ee0be6852385e5a358cd59eb8aae50fe922a35aa7b`.

The catalog spans system overviews (14 links), proving/RL/self-play (30),
autoformalization/data/benchmarks (15), conjecture/counterexamples (18), RAG/graphs
(13), logic/HoTT/transport/SAT (22), multimodal work (6), and code/data (2).
These are collection categories, not independent efficacy evidence.

The original `/Users/yukangzengcmac/Downloads/goal-ai-statistician.md`, current goal/design/status/adoption documents and
relevant historical project documentation were compared with current source.
Existing historical audits retain prior conversation/resource coverage; this
revision does not claim a fresh line-by-line reread of every past conversation,
branch, book or repository. The historical project copy was not modified.

Primary full-text reading included all eight pages of the local Numina paper,
pages 1-9 of the 26-page LeanMarathon paper, Prove2Me's web paper sections, selected
Co-Scientist sections, the AxProverBase abstract and source, and Statlib's roadmap.
Selected source paths and exact local identities are recorded below. Metadata-only
checkouts and uninspected paper sections are not promoted to reviewed methods.

Unresolved catalog names such as Mini-CTX v2, a standalone LeanDojo-v2 paper,
QED-Bridge and several private-sounding Axiom/AlphaProof titles remain unverified.
HoTT, diagram rewriting and hardware verification are adjacent resources, not a
reason to add those subsystems to a statistical lab now. No book-scale proof
coverage, trained policy, remote service access or new library compatibility was
established by catalog inspection.

## What Current Code Actually Supports

| Subsystem | Observed implementation | Remaining design or capability gap |
|---|---|---|
| Outer graph | [AgentRuntime](../ai_statistician/agent_runtime.py) owns one current task and synchronously runs it; progress/continuation and outer transitions are distinguished | No concurrent ready-set or isolated result joins. `dual_track` does not mean simultaneous execution |
| Shared harness | [client_tool_loop.py](../ai_statistician/client_tool_loop.py) retains author history, scoped tools, raw observations, checkpoints and terminal dispositions | Keep instructions consistent with actual tools; preserve useful long work without turning context/authority into recursive payloads |
| Theory | [theory_workspace.py](../ai_statistician/theory_workspace.py) has MD/LaTeX reads, search, writes, exact edits, scratch, discovery, project execution, progress and explicit commit/gap; canonical callers require document authority | Long arguments and honest gap handling are possible, not demonstrated reliable. Dependency-linked local revision and referee falsification need scientific evaluation, not another JSON DAG schema |
| Review | Independent retained sessions inspect exact files and can use isolated probes; [research_architect.py](../ai_statistician/research_architect.py) already asks for whole-argument review | Same-model author/reviewer errors can correlate. More calls or checklist fields do not establish truth |
| Source discovery/reproduction | [discovery](../ai_statistician/research_source_discovery.py) supports Crossref/arXiv/GitHub; [source library](../ai_statistician/research_source_library.py) pins snapshots and permits model-selected execution in a prepared environment | General publisher PDF/OCR, data acquisition and environment reconstruction remain incomplete. Fresh per-command project copies do not provide a persistent install/edit/run research environment |
| Scientific code | [scientific_code_workspace.py](../ai_statistician/scientific_code_workspace.py) supports multi-file code, exact edits and run-current; Python scientific packages and WebR exist | Finite WASM/package support is not arbitrary Python/R, native libraries or GPU support. Broader environments need isolation and dependency identity, not a new coding agent |
| Simulation | Model-authored evaluator source, independent preregistration review, exploratory/confirmatory separation and blinded confirmation already exist | A correctly executed, frozen but scientifically wrong protocol can still pass runtime review. Calibration and independent result comparison remain necessary |
| Lean | [Lean tool loop](../ai_statistician/lean_candidate_revision_tool_loop.py) supports files, edits, compile, state, retrieval and optional search | Current exact statistical proof success is narrow; project/index mismatch and incomplete provider inputs remain relevant. Do not repeat the obsolete claim that there is no state feedback |
| Formal RAG | [dependency retrieval](../ai_statistician/lean_rag_dependency.py) and [proof-state trace retrieval](../ai_statistician/lean_proof_state_trace_rag.py) are source-bound and state-aware | Cross-version corpus text is not an accessible imported premise. Successful retrieval must lead to active-project elaboration and useful proof work |
| Final authority | Exact hashes, independent statement review, local axiom checks and task-intent requirements distinguish kinds of evidence | Model approval, runtime ACCEPTED and gold acceptance must remain distinct; none alone demonstrates open research or novelty |
| Reuse/learning | Existing retrieval, verified artifacts and trace/training-data export | No demonstrated autonomous library growth across unrelated tasks or learned research/tactic policy. Export is not learning |

At the inspected baseline there are 139 top-level Python modules and about 149k
package lines; the central research runtime is 24,810 lines, not the old 101k.
The old repair/post-runtime planes are no longer the main diagnosis. The remaining
size is still substantial: add responsibility only by consolidating an existing
owner, not by growing another parallel abstraction.

## Target Design by Responsibility

### Theory and Research Collaboration

Keep mathematics in ordinary Markdown/LaTeX files with stable claim labels,
definitions, assumptions, equation justifications and explicit unresolved points.
The model chooses decomposition and derivation length. Existing file tools should
support gradual work, local corrections and source-grounded counterexamples; a
compact reference index serves transport, not mathematical authority.

A reviewer examines a stable snapshot, tries to refute load-bearing claims and
reports concrete source locations. Correctness cannot be enforced with a fixed
number of equations, a PASS prefix or mandatory scratch quota. Ordinary feedback
returns to the same author. A changed premise should invalidate dependent evidence,
not erase unrelated work or trigger a fresh Architect plan by default.

Early code is useful when an executable interface is understood, even if asymptotic
theory remains open. Small simulations and symbolic/numeric checks can expose
ambiguity; they do not prove a theorem. Heavy formalization generally waits for
stable statements, with earlier investigation of useful foundational lemmas.
These activities are currently interleaved. Genuine parallelism needs isolated
workspaces, versioned inputs and explicit joins in the existing outer graph.

### Sources, Algorithms and Experiments

Discovery is a tool available to the working researcher, not another routing
agent. When prior code is relevant, reproduce the original before claiming an
extension, subject to the task's source horizon and visibility restrictions.
Record commit, data and environment; absent or unavailable inputs are visible gaps.

The next environment improvement should extend the existing project executor with
model-controlled file/command work under a reproducible, isolated environment.
Separate permitted dependency acquisition from no-network execution and preserve
the same project across related exploratory commands. This is proposed work, not
currently arbitrary-paper reproduction. Avoid package-specific installers or
running untrusted repository setup with host secrets.

Algorithm and Simulation remain configurations of the same source loop. The
model owns the estimator and scientific tests; the executor owns a small ABI and
raw observations. Exploratory candidate search can use a trustworthy executable
score, but the confirmatory protocol, hidden data and acceptance criteria must not
become search feedback. Precision/stopping is an experimental decision frozen
before confirmatory results, not a universal repetition count or post-hoc gate.

### Formalization, RAG and Library Growth

The prover is a general Lean coding workspace, not a Python tactic generator.
Let the model inspect definitions, actual goals, accessible declarations and raw
compiler diagnostics, then edit and check. Start with existing active-project
objects. Never prescribe grammar repair, theorem-family patterns or a search tree
merely because one output failed. MCTS and trained tactic policies are optional
future methods, not prerequisites for calling the current source loop agentic.

Follow Statlib/Mathlib's semantic modules, reusable abstractions and source-facing
documentation. General missing foundation lemmas belong in the appropriate
upstream-oriented module, not a task-ID-named bridge. Promote a selected lemma only
after its statement, dependencies, project version, license and kernel check are
known. Test that a disjoint task can actually import and use it; a declaration
inventory or proof export does not establish reusable knowledge.

Optional formal failure is reported alongside other evidence. Required formal
completion needs exact target identity, independent statement-faithfulness review
and a clean transitive axiom check in the active project. Kernel validity cannot
establish that the Lean statement faithfully captures the intended mathematics.

## Selective Literature and Code Reuse

The conclusion is selective reuse, not harness-free autonomy. Mature systems still
choose environments, authorities, memory and search policies. Importing their
controllers wholesale would undo the existing single-runtime simplification.

| Resource and inspected pin | Reading and adoption decision |
|---|---|
| [OpenAI Codex `8e6a44b4`](https://github.com/openai/codex/blob/8e6a44b4/codex-rs/core/src/session/turn.rs) | Inspected turn implementation, existing adoption map and official platform article. Retain file/tool history, truthful capabilities, explicit boundaries and source ownership. No Core/App Server/SDK scheduler embedding |
| [Numina `1c9af8a5`](https://github.com/project-numina/numina-lean-agent/tree/1c9af8a52e715f22fede766425ba3d3b95526132) | Full local paper, README and runner. General coding tools, Lean feedback, retrieval and long-proof decomposition are useful. Its stronger model tiers and human-assisted paper example do not establish exact-Haiku efficacy |
| [AxProverBase `0f5a80aa`](https://github.com/Axiomatic-AI/ax-prover-base/tree/0f5a80aa4c5adf7fa03909b69c8ee374c9846c10) | Abstract and `prover/agent.py`. Actual implementation has LangGraph, proposer/builder/reviewer/memory and typed feedback. Reuse iterative environment feedback, not its controller or a misleading claim of zero structure |
| [LeanMarathon `e2febe2c`](https://github.com/YuanheZ/LeanMarathon/tree/e2febe2ce717ef5d8410909683f6f5b301bda4c2) | Local README, paper pp. 1-9 and DAG tracker. Evolving blueprint, scoped dependencies and checked joins inform long projects; its phased/refiner/cluster workflow is not a drop-in statistical harness |
| [Prove2Me `16e3fb51`](https://github.com/prove2me/prove2me_workspace/tree/16e3fb51a061c05ea83e07617400fd642a9eac81) | Paper and `mission_auditor.md`: stable theorem objects, separate proof attempts, blinded read-back and checked conditional reductions. Local read-back and axiom boundaries are already adopted; remote Formalpedia is not connected |
| [ReProver `fd6d99c0`](https://github.com/lean-dojo/ReProver/tree/fd6d99c01e8bd8fd8f3fd1de4cd0bc4a7f158eaa) | `proof_search.py`, generator and premise access code. Retrieve using goal, file and location; only imported or earlier accessible premises are valid candidates. Do not copy a second search controller |
| [OpenProver `3960746d`](https://github.com/ykzeng-yale/OpenProver/tree/3960746da0691e727cf77442ff8df355afa72ba3) | README and algorithm design; existing optional LSP/MCP/search provider. Returned candidates still need exact active-project checking |
| [CodexProver `d6345529`](https://github.com/ykzeng-yale/CodexProver/tree/d634552975fd87a43aac4fc9a4d594573a7beba1) | README and local branch inventory; historical evidence and retrieval conventions, not a merge of its packet/controller stack |
| [ERA `440711e3`](https://github.com/google-research/era/tree/440711e3bef52692e18eaa2400462cc01052d756) | `implementation/futs.py` and README: model candidate generation, execution and scored search. Apply only with reliable exploratory scores; never optimize on sealed confirmation |
| [LEGO-Prover `357672c7`](https://github.com/wiio12/LEGO-Prover/tree/357672c7751cd0c84aff6bf72a3d1bf97614e81d) | `lego_prover/agents/skill.py`: verified reusable lemma memory is relevant, but inspected code targets Isabelle `.thy`, not a Lean plug-in. Do not port naming/similarity heuristics as mathematical rules |
| [Pseudo-formalization `0aa51d25`](https://github.com/Slim205/pseudo-formalization/tree/0aa51d25726c8a801db329343a1474c8536f8980) | README and prior adoption record. Structural advisory criticism only, never kernel proof or another repair lane |

The [official Codex platform description](https://developers.openai.com/blog/codex-as-a-platform)
supports separating the agent loop's context, tools and progress from surrounding
product integration. Here that is an architectural reference, not a requirement
to send Anthropic research through Codex. The detailed boundary remains in the
[existing Codex adoption document](openai_codex_harness_adoption_20260825.md).

[Numina's paper](https://arxiv.org/abs/2601.14027),
[AxProverBase's paper](https://arxiv.org/abs/2602.24273) and
[LeanMarathon's paper](https://arxiv.org/abs/2606.05400) use different task scopes,
models and supervision. Their results are not a benchmark of this system or proof
that a specific iteration count is optimal. [Prove2Me](https://arxiv.org/html/2608.28433v1)
also makes statement auditing central; its human mission audit is not reproduced
by merely using the same Haiku model in two contexts. The [local adoption record](prove2me_adoption_20260904.md)
documents remote authorization, toolchain and licensing limits; do not vendor the
workspace or claim service access without resolving them.

[AI Co-Scientist](https://arxiv.org/html/2502.18864v1) is a scientist-in-the-loop
hypothesis system with external validation, not evidence that a model referee can
certify autonomous mathematical discovery. Its hypothesis-generation and criticism
ideas fit open exploration; exact program or theorem claims still need their own
executors and authorities.

### Lean Foundation Compatibility

| Source | Actual boundary |
|---|---|
| [EmpericalProcessLEAN `4cec7860`](https://github.com/ykzeng-yale/EmpericalProcessLEAN/tree/4cec7860c926feebd4cbcdaccedb63b2156972dd) | Active repository gitlink; its StatInference/Mathlib/Statlib dependency identity is the execution authority |
| [Statlib active `6575d611`](https://github.com/stat-lib/statlib/tree/6575d611b5d32ef6013e9560d30b1a82a1972fb6) | Active statistical foundation with Lean 4.30 and Mathlib `81343555`; retain this pin until a separately verified migration |
| [Statlib checkout `01d2a037`](https://github.com/stat-lib/statlib/tree/01d2a03770455f5c775bb25c57e7fbb8e1eaf8d8) | README and `Statlib/Inference.lean` inspected. Newer upstream is discovery/design context, not silently importable. Prior combined migration had 207 errors; not rerun here |
| [Statistical learning theory `d0f506f0`](https://github.com/YuanheZ/lean-stat-learning-theory/tree/d0f506f0a695018265dccb33bcb05e2f5ca1c876) | README and `SLT/SubGaussian.lean` inspected. Layer foundational probability/concentration before statistical applications, with source references and small reusable lemmas. Checkout/traces use different Lean versions from the active project |
| Stat-Lean `855b6afb` | Existing discovery corpus; no new build or portability claim in this audit |

The [Statlib roadmap](https://stat-lib.github.io/roadmap.html) is a priority map,
not a list of already-proved theorems. Its use of shared Mathlib probability types,
statistical inference abstractions and upstream-oriented foundations informs
organization; wholesale renaming of our library or merging every branch would
not establish compatibility. Local branch tips were inventoried, not exhaustively
reviewed or merged. The three statistical books remain source material, not a
claim that their full formalizations have been inspected or completed here.

## Implementation and Test Plan

| Order | Change in an existing owner | Verification and stopping criterion |
|---|---|---|
| 1, this revision | Reconcile goal/role documents; correct Theory prompt references to nonexistent write quotas; label serial graph honestly | Existing continuation test must retain real progress, reject fabricated progress and advertise the actual shared budget; full suite before push |
| 2 | Diagnose general author/referee reliability and expensive repeated inspections before modifying prompts or tools | Disjoint synthetic counterexamples and source-bound review cases; measure useful findings and calls. No task-answer coaching, new mandatory review layer or old-candidate regrading |
| 3 | Extend source-project/environment continuity for demonstrated paper reproduction needs | Isolated edit/install/run sequence, environment replay, missing dependencies/data, no secrets/network leakage and honest unavailable-input result |
| 4 | Unify active Lean project and retrieval identity; reuse selected checked declarations | Imported-premise availability, source-path/version mismatch, changed target, transitive axioms, independent statement read-back; later fresh scoped exact proof |
| 5 | Add only useful independent execution to the sole outer graph | Cancellation/resume, conflicting writes, stale joins, changed claim dependency and independent-branch survival; no benchmark-only scheduler |
| 6 | Evaluate multi-family research, public replication, hidden reimplementation/rederivation and actual verified-artifact reuse | Preregistered task-specific gold and separate dimensions/costs; retain failures; existing strict held-out gate stays sealed |

Scientific reliability, not more mechanisms, is the immediate priority after this
audit. Long-horizon work should be allowed to continue when it makes real progress;
more turns alone are not evidence of better mathematics. The latest run cannot
justify either automatic budget cuts or unbounded repetition.

The ladder then proceeds to historical rediscovery, extensions and open problems.
Blind source access does not erase training-set familiarity. Report contamination
limits, independent expert review needs, uncertainty and negative results. Learned
policies or autonomous skill growth require measured disjoint-task benefit, not
just exported traces. No new evaluation or framework is activated by this report.
