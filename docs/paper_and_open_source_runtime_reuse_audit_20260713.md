# Paper And Open-Source Runtime Reuse Audit

Date: 2026-07-13 (repository tips refreshed 2026-07-14)

## Purpose

This audit separates three claims that must not be conflated:

1. a paper or repository was collected and reviewed;
2. a design or implementation was adapted into AI-Statistician; and
3. a capability ran inside the current AgentRuntime and produced admissible
   evidence.

Only the third claim is runtime capability evidence. Retrieval hits, external
benchmark results, pseudo-formal verdicts, generated code proposals, and Lean
diagnostics retain their narrower evidence boundaries.

## Historical Collection Coverage

The checked-in `AI for Math Resources/paper_links.json` contains 122 links in
eight groups: system agents, Lean/RL provers, autoformalization and benchmarks,
conjecturing, formal RAG, foundations, multimodal mathematics, and code/data.
`AI for Math Resources/coverage_audit.md` separately records 98 verified manual
additions and flags names that could not be verified. This is a bibliography and
design corpus, not proof that all 122 systems are installed or active.

A read-only rescan of all paper/chat attachments supplied to this project found
243 URL occurrences and 189 raw unique URLs. The latter includes paper pages,
repositories, individual commits, documentation, tracking-parameter variants,
and malformed punctuation variants; it is not a claim of 189 distinct papers.
Within the explicitly rechecked attachment set, 31 distinct raw GitHub
repository URLs reduce to 29 after normalizing two `.git` duplicates. Their
families are all assigned below to active source, source-study, benchmark/data,
or deferred-by-current-blocker status; repository mention alone is not an
integration decision.
The attached `master_ai_for_math_formal_verification.md` is byte-identical to
the checked-in copy. Newer sources from the persisted build chat are covered in
the source-family table below rather than silently omitted from the May corpus.

The architecture should reuse a source only when its mechanism addresses a
measured blocker. Vendoring every paper implementation would create conflicting
orchestration planes, duplicate model clients, and unreviewed evidence rules.

## Collection-Wide Admission Map

This map accounts for every layer of the historical collection. Representative
names identify mechanism families; they do not transfer external benchmark
scores into this runtime.

| Collection layer | Representative source families | Mechanism decision for AI-Statistician |
| --- | --- | --- |
| Research agents and discovery systems | AI Co-Mathematician, DAP, RMA, AlphaEvolve, AlphaProof Nexus | Reuse long-horizon memory, proposer/critic separation, immutable candidate populations, and discovery-withheld evaluation. Keep one Architect control plane. |
| Kernel and formal foundations | Lean, Mathlib, CompCert, HoTT, SAT/DRAT/GRAT, hardware verification | Lean kernel replay is directly relevant and authoritative. Other foundations remain design references until a statistical task requires their logic or proof-certificate domain. |
| Formal data, autoformalization, and benchmarks | ProofNet, miniF2F, MMFormalizer, MerLean, symbolic-equivalence autoformalization | Reuse source spans, exact statement identity, dependency DAGs, split hygiene, and statement-fidelity review. Benchmark success is never source-theorem proof evidence. |
| Formal RAG and memory | LeanDojo/ReProver, LeanSearch/Finder, Loogle, MathlibGraph, LeanExplore, premise selection | Admit providers behind typed proof-state queries, accessible-premise filtering, provenance, and matched retrieval ablations. Search hits remain non-proof evidence. |
| Prover engines and RL | HTPS, DeepSeek-Prover, Goedel/Seed/EvolProver, Process-Verified RL, LeanAgent, LEGO-Prover, LeanHammer | Reuse tactic-state search, value/reranking interfaces, failed-attempt replay, and bounded exploration. Do not hand-code theorem tactics or import external success counts. |
| Construction, conjecturing, and counterexamples | FunSearch, AlphaGeometry/formal-conjectures, PatternBoost, Int2Int, LeanConjecturer, learning-to-disprove | Candidate evolution and counterexample workers are valuable after theory artifacts have stable identities. They are not the current earliest blocker, so they stay outside the default path for now. |
| Multimodal and diagrammatic mathematics | MathNet, MathVerse/MathVista, PolyMATH, Quantomatic, graph/string-diagram systems | Defer default integration until a held-out statistical task actually contains figures or diagrammatic proof obligations. Text-only claims must not pretend this capacity is active. |
| Code, datasets, and project pages | Mathlib, Lean benchmark corpora, formal-conjecture repos, proof graphs, project tool servers | Pin only the exact source commit, license, data split, and adapter used by an eval. Repository presence alone is not runtime evidence. |

The 29 normalized GitHub URLs from the explicitly rechecked attachments are
accounted for as follows. CodexProver, OpenProver, and Slim205
pseudo-formalization were supplied separately by the user and are covered in
the core matrix.

| Attachment repository bucket | Normalized repositories | Decision |
| --- | --- | --- |
| Current runtime or pinned mechanism source | `ykzeng-yale/AI-Statistician`, `ykzeng-yale/EmpericalProcessLEAN`, `Goedel-LM/Goedel-Prover-V2`, `PatrickMassot/leanblueprint`, `cameronfreer/lean4-skills`, `lean-dojo/ReProver`, `oOo0oOo/lean-lsp-mcp`, `project-numina/kimina-lean-server`, `project-numina/numina-lean-agent`, and the pinned `ykzeng-yale` Atlas/Autoform forks | Keep exact commits and source-specific license/evidence boundaries. Only AI-Statistician and explicitly configured providers are live runtime components. |
| Formal libraries or search infrastructure | `YuanheZ/lean-stat-learning-theory`, `leanprover-community/mathlib4`, and `cs-lean/cslib` | Statistical-learning source is restored locally; Mathlib remains the kernel library. CSLib is unrelated combinatorics infrastructure and is deferred until a task requires it. |
| Benchmark, corpus, or contamination-sensitive result source | `AxiomMath/putnam2025`, `MoonshotAI/CombiBench`, `facebookresearch/Lyapunov`, `google-deepmind/formal-conjectures`, `leanprover-community/mathlib49`, `liuchengwucn/FIMO`, `openai/miniF2F`, `zawagner22/transformers_math_experiments`, and `zhangir-azerbayev/ProofNet` | Use only in separately registered held-out or source-fidelity evaluations with split, license, and contamination metadata. Do not index them into the default proof memory. |
| Construction or theorem-system mechanism source | `AxiomMath/axplorer`, `FacebookResearch/Int2Int`, `facebookresearch/atlas-lean`, `facebookresearch/autoform-bot`, `google-deepmind/alphageometry`, and `wiio12/LEGO-Prover` | Retain candidate-evolution, modular-decomposition, and evaluator-loop ideas. They do not justify importing a second orchestrator, another theorem system's parser, or external success claims. |

## Core Reuse Matrix

| Source | Reviewed source state | Current AI-Statistician use | Admission decision |
| --- | --- | --- | --- |
| Lean 4 / Mathlib | Local Lean toolchain and tracked Lake projects | Local `lake env lean`, Lean/LSP feedback, and exact source-target checks are the final proof path | Keep local kernel replay authoritative. Do not replace model-generated Lean with grammar rewrite rules. |
| EmpericalProcessLEAN | Clean signed RAG checkout `4a3b2856`; graph has 26,378 declarations and 75,497 edges | `formal_source_*`, `lean_rag_dependency.py`, proof bank, and full-live runtime retrieval | Keep retrieval non-proof and signature checked. Remote `main` remains at `94035519`; newer theorem branches `66383d97` (Vaart general studentization) and `eec585aa` (Chewi local Lipschitzness) are source candidates only and are not part of the signed graph until rebuilt and re-audited. |
| Statistical Lean source set | Restored current-machine checkouts of FormalSLT `5fc12196`, lean-rademacher `f34ab4f0`, LML `b2fba433`, brownian-motion `bdf5ea0c`, kolmogorov_extension4 `bb869685`, SciLean `95f8119a`, and lean-stat-learning-theory `216e578c` | A targeted current-code inventory run reports 8/8 local-ready sources when LeanBlueprint `56e066d3` is included, spanning 903 matching source files. This repairs the stale prior-Mac paths. FormalSLT, Rademacher, and LML permit retrieval/training export; Brownian and SciLean retain retrieval-only policy. | Source availability is restored, but a multi-source graph must still be rebuilt, signed, and ablated before claiming live RAG use. Do not treat checkout presence or unsound/WIP declarations as theorem support. |
| OpenProver | Clean `main` at `533b40d` | Bounded HLM provider, Lean LSP/MCP goal feedback, and proof-search diagnostics behind AgentRuntime flags | Keep as a typed worker/provider. Local Lean/AXLE remains final authority. Provider transport and target binding must remain scoped and secret-free. |
| CodexProver | Remote coordination branch now at `d6345529` | Packet identity, runtime-read auditing, scoped MCP transport, target/hash binding, independent exact checks, pre-registered episode control, and compact hash-bound Prover instruction packets are reuse candidates | Do not merge its orchestrator or committed run corpus. Its compact-packet smoke reduces packet-listed instruction bytes while preserving frozen target identity; reuse that mechanism as prompt-cost design evidence, not theorem evidence. Its v2.1 pool remains underpowered at 28/30 screened targets, so finish only the two frozen first attempts and make no causal MCP claim. |
| Slim205 pseudo-formalization / arXiv:2605.20531 | Clean `main` at `0aa51d2` | `pseudo_formalization.py`, typed work orders, faithfulness boundaries, and the AgentRuntime `PseudoFormalBlockVerifier` | Keep PF/BV as decomposition, calibration, and routing evidence only. Never promote an accepted block to Lean proof evidence. |
| LeanDojo / ReProver | Clean source-study checkouts at LeanDojo-v2 `936ea0dd` and ReProver `fd6d99c0` | LeanDojo-style proof-state packets and retrieval concepts are present; no trained ReProver tactic-state policy is active | This remains a real prover gap. Add a typed tactic-state provider and held-out evaluation instead of hardcoding tactics or Lean syntax. |
| Loogle, Lean premise selection, LeanHammer, Lean Finder-style retrieval | Reviewed in the formal-RAG collection | Loogle is optional; local hybrid retrieval and proof-bank search are active | Improve query generation, accessibility filtering, reranking, and proof-state feedback. A search hit is never proof evidence. |
| Lean comparator / lean-eval | Primary repository reviewed | Not currently integrated | Evaluate as a mature exact-statement and sandboxed Lean benchmark gate. Adoption requires toolchain compatibility and must not create a second proof authority. |
| Prior Mac Pro AI-Statistician snapshot | Snapshot `1dde8179`, 442 unique commits, about 38 GB dirty state | Current tree already contains the stronger typed runtime lineage | Do not overlay it. Reuse only isolated protocol concepts after comparing tests and current ownership boundaries. |

## Repository And Branch Synchronization

All four user-owned repositories were fetched before this audit, and the
connected GitHub application reports no open pull requests across them.

| Repository | Remote branch state checked | Integration decision |
| --- | --- | --- |
| `AI-Statistician` | Current main-worker branch plus `codex/ai-stat-lab-sync-main-20260706`, `codex/ai-stat-lab-sync-20260625`, and default/main lineage | Current branch is the only active commit stream. The Mac Pro sync branch is a source-study snapshot, not an overlay candidate. |
| `CodexProver` | Five remote branches; newest coordination tip `d6345529` | Inspected the resumable screening runner and compact instruction-packet addition. Reuse pre-registration, target isolation, runtime-read audit, independent exact checks, immutable failure lineage, and hash-bound prompt compaction, but not the underpowered cohort as MCP-effect evidence. No matched retry may be dispatched from this cohort. |
| `OpenProver` | Only `main`, tip `533b40d` | Existing bounded HLM/LSP provider remains the integration surface; there is no hidden branch with a stronger live engine to merge. |
| `EmpericalProcessLEAN` | Signed integration branch `4a3b2856`, remote `main` at `94035519`, fresh theorem branches `66383d97`/`eec585aa`, and historical proof/RAG branches | Keep `4a3b2856` as the current signed RAG graph. Treat the studentization and convex-analysis branches as theorem-source candidates for a future multi-source rebuild, not as automatically trusted additions. |

## Prior-Chat Sources Beyond The Main Collection

The persisted build chat contains additional papers and repositories that are
not all present in `paper_links.json`. Their primary paper pages and available
source repositories were rechecked rather than treating earlier chat summaries
as implementation evidence.

| Source family | Mechanism worth reusing | Current implementation reality | Required next action |
| --- | --- | --- | --- |
| MerLean (`2602.16554`) | LaTeX statement extraction, statement/dependency DAG, Lean realization, and human-readable LaTeX round trip | `paper_theory_roundtrip.py` is a useful local-TeX scaffold, but it does not yet ingest arbitrary papers or establish statement fidelity at MerLean scale. The official example-output checkout exposes paired `lean`/`uses` blueprint nodes, but not the MerLean agent implementation and has no repository-root license. | Adapt the metadata shape only: parser-backed source spans, definition/assumption identity, bidirectional statement review, and held-out paper eval. Do not copy unlicensed source or count extracted/translated text as proof. |
| Discover and Prove / DAP (`2604.15839`) | Separate answer/theory discovery from formal proof and evaluate without leaking the answer in the target | Official MIT checkout `6dd99de4` was inspected. It provides Hard-Mode datasets, self-verification/correction prompts, discover-then-rewrite ablations, Goedel-Prover sampling, and Kimina checking. AI-Statistician has withheld fields and discovery-oriented prompts, but no measured hard-mode discovery-to-proof closure. | Adapt its answer-withholding and ablation contracts into fresh statistical tasks, with immutable target identity. Do not import its string-based rewrite pipeline, model clients, or second orchestrator. |
| Goedel-Prover V1/V2 and Kimina Lean Server | Preserve failed attempts, attach compiler errors at their source positions, generate bounded child corrections, and verify candidates concurrently under explicit project/resource settings | Pinned source shows Goedel V2 assigning stable original, generation, and correction IDs and feeding Lean errors into two correction rounds. It also contains ad hoc theorem-string extraction that is unsuitable as a semantic boundary. Kimina is an MIT FastAPI/Lean-REPL verification transport with bounded REPL count, wait/command timeouts, memory limits, project selection, parallel clients, and optional infotrees; it is not a proof-search policy. | Adapt typed error spans and immutable parent/child attempt lineage into the existing AgentRuntime. Evaluate Kimina only as an optional parallel verifier transport against the same target/project hashes; keep local Lean/AXLE authoritative and do not import either source's parser, model client, or orchestration loop. |
| Ax-Prover (`2510.12787`) and `lean-lsp-mcp` | General LLM coding agent directly interacting with Lean goals, diagnostics, search, and multi-attempt tools | Tool names and typed feedback contracts exist; local compile and some provider traces are real. This is not yet evidence that the current default proof loop uses the complete MCP tool sequence effectively | Use the pinned `lean-lsp-mcp` provider through AgentRuntime, record each real tool call/result, and run a matched feedback-only versus feedback-plus-search escalation evaluation. |
| `lean4-skills` | A mature host-agnostic LLM workflow: preserve statement headers, search before proving, inspect exact LSP goals, run bounded plan/work/checkpoint/review/replan cycles, and distinguish kernel-certified refutation from an uncertified witness | The MIT checkout `5a331e22` was inspected. Its skill and scripts are useful workflow references, while its host commands, user-prompt hooks, commit behavior, and broad tactic/style reference pack do not belong inside the statistical runtime. AI-Statistician already has pieces of the cycle but still splits proof work between AgentRuntime and post-loop workflows. | Adapt the target-header fence, typed LSP-first tool policy, bounded-cycle state, and certified-disproof evidence boundary into one Architect-owned proof task. Do not turn its prose rules into a Lean grammar rewriter or install its host orchestrator inside AgentRuntime. |
| LEGO-Prover and Axiom `axplorer` | Modular lemma decomposition plus a reusable skill library; evaluator-guided candidate generation and local repair | Pinned source confirms LEGO-Prover is an older Isabelle/LangChain pipeline with regex extraction and its own control plane. `axplorer` is an Apache-2.0 combinatorial construction/search system, not a Lean proof-state explorer. | Reuse only immutable modular-lemma/candidate-population concepts after theorem artifacts have stable identities. Do not import either orchestrator, model client, benchmark score, or theorem-system-specific parser. |
| AlphaProof Nexus (`2605.22763`), LEAP (`2606.03303`), and LeanMarathon (`2606.05400`) | Candidate evolution, informal blueprint plus Lean feedback, target-fidelity review, dynamic-leaf proof DAGs, scoped worker edits, and recoverable rounds | Strategy-plan, queue, and repair artifacts cover pieces of this design, but the runtime still has post-loop proof workflows and no durable dynamic-leaf scheduler. AlphaProof's public checkout is a successful-proof/results corpus, not its agent code; no official LEAP implementation was surfaced by the paper page/search. | Adapt LeanMarathon's node contracts, target reviewer, dynamic-leaf readiness, and local transaction lineage into the one AgentRuntime. Treat AlphaProof results as a contamination-sensitive proof corpus, and do not infer LEAP implementation details beyond the paper. |
| Aria (`2510.04520`) and LeanArchitect (`2601.22554`) | Definition-grounded statement construction and a synchronized formal/informal dependency graph | Minimal formalization plans and Lean-blueprint knowledge exist, but no LeanArchitect-backed shared theorem graph governs the live run. LeanArchitect is pinned source; no official Aria repository was surfaced by the current paper page/search. | Introduce a versioned theorem-blueprint artifact whose statement hash, source span, dependencies, and Lean declaration are checked at every handoff. Use Aria's paper mechanism, not an unverified similarly named repository. |
| LeanExplore (`2506.11085`), LeanPremise, and LeanHammer (`2506.07477`) | Hybrid semantic/lexical/graph retrieval, context-adaptive premise selection, ATP translation, and proof reconstruction | Hybrid local RAG and optional search hooks exist, but these providers are not admitted by a held-out tactic-state ablation | Add typed provider adapters and compare local RAG, LeanExplore, state search, and hammer premises on the same accessible-premise proof states. Retrieval success remains non-proof evidence. |
| AlphaEvolve (`2506.13131`) and ERA/FUTS | Maintain a scored population of executable programs and choose parents using evaluator feedback instead of repeatedly replacing one draft | Algorithm/Simulation currently run bounded generated-code repair, but do not maintain a candidate population or exploration/exploitation controller | Generalize generated drafts into immutable parent/child candidate nodes and adapt ERA's evaluator-driven FUTS controller behind a matched single-retry baseline. |
| RMA (`2605.22875`) | Long-horizon problem analysis, literature grounding, fair comparison, shared memory, proposer/verifier revision | Typed memory and specialist packets exist, while TheoryDeveloper remains too compressed for serious long-horizon derivation. The paper explicitly says implementations will be released upon acceptance, so there is no public code to pin today. | Add serious-theory mode with an assumption ledger, equation/lemma DAG, independent critic, and simulation/prover counterfeedback; reevaluate source reuse only after an official release. |
| Numina-Lean-Agent (`2601.14027`), ReProver, Atlas Lean, and Autoform-Bot | Mature agent work discipline, tactic-state retrieval/search, broader Lean source corpus, and formalization/evaluation harnesses | Local source checkouts exist. Atlas is retrieval-only; Autoform has export/audit harnesses; ReProver and Numina are reference implementations rather than active default provers | Reuse typed provider and evaluation contracts selectively. Do not import their model clients, orchestration loops, or external benchmark claims as runtime evidence. |

## Pinned Source Study Checkouts

These clean external checkouts were synchronized for source-level comparison.
They are not vendored dependencies and their presence is not capability
evidence.

After restoring the prior-Mac statistical sources and LeanDojo-v2, the current
source-inventory implementation reports 33/33 references valid, 33/33 locally
ready, zero clone-required entries, and zero missing required entries. This is
source availability evidence only; the signed runtime graph and provider
admission remain separate gates.

| Repository | Commit | License | Reuse scope |
| --- | --- | --- | --- |
| `YuanheZ/LeanMarathon` | `e2febe2c` | Apache-2.0 | Target review, dynamic-leaf DAG, scoped worker and resume contracts |
| `hanwenzhu/LeanArchitect` | `d9013cc0` | Apache-2.0 | Lean-owned blueprint metadata and dependency extraction |
| `oOo0oOo/lean-lsp-mcp` | `83b02865` (0.28.0) | MIT | Typed goal, diagnostic, local/remote search, and multi-attempt provider surface |
| `justincasher/lean-explore` | `3a52d6b9` | Apache-2.0 | Hybrid semantic/BM25/graph retrieval provider |
| `JOSHCLUNE/LeanHammer` | `3ef50193` | Apache-2.0 | Hammer/reconstruction provider candidate |
| `hanwenzhu/premise-selection` | `d3080a1d` | Apache-2.0 | Context-adaptive premise selection candidate |
| `google-research/era` | `440711e3` | Apache-2.0 | Evaluator-driven program candidate tree/search contract |
| `liuchengwucn/discover-and-prove` | `6dd99de4` | MIT | Hard-Mode answer withholding, discovery/self-correction, and matched rewrite ablations |
| `Goedel-LM/Goedel-Prover` | `d80349d9` | MIT | Baseline proof-generation and verifier pipeline reference only |
| `Goedel-LM/Goedel-Prover-V2` | `2e9036e1` | README advertises Apache-2.0; no repository-root license file found | Error-position feedback and immutable initial/correction attempt lineage only; no code copying or runtime dependency |
| `project-numina/kimina-lean-server` | `fb2393de` | MIT | Optional parallel Lean-verifier transport candidate with explicit project, timeout, REPL, and memory controls |
| `cameronfreer/lean4-skills` | `5a331e22` | MIT | LSP-first, statement-preserving, bounded prove/review/replan workflow reference |
| `wiio12/LEGO-Prover` | `357672c7` | MIT | Modular lemma/skill-memory reference only; Isabelle-era pipeline and external scores are not imported |
| `AxiomMath/axplorer` | `3298b1af` | Apache-2.0 | Evaluator-guided construction/local-search reference; not a Lean prover |
| `google-deepmind/alphaproof-nexus-results` | `0647711a` | Apache-2.0 / CC-BY with source-specific terms | Successful proof artifacts and target-fidelity examples only; contamination-sensitive and not agent code |
| `doxtor6/MerLean-examples` | `b7f72365` | No repository-root license found | Source study of paired Lean/LaTeX blueprint output only; no code copying or runtime dependency |
| `Robby955/FormalSLT` | `5fc12196` | MIT | Statistical-learning theorem source; inventory and future signed-RAG input |
| `auto-res/lean-rademacher` | `f34ab4f0` | MIT | Rademacher/McDiarmid/Dudley theorem source; inventory and future signed-RAG input |
| `LeanMachineLearning/LML` | `b2fba433` | Apache-2.0 | Bandit/regret/algorithm theorem source; inventory and future signed-RAG input |
| `RemyDegenne/brownian-motion` | `bdf5ea0c` | Apache-2.0 | Retrieval-only stochastic-process theorem source |
| `RemyDegenne/kolmogorov_extension4` | `bb869685` | Apache-2.0 | Measure-extension theorem source; inventory and future signed-RAG input |
| `lecopivo/SciLean` | `95f8119a` | Apache-2.0 | Retrieval-only calculus/optimization theorem source |
| `YuanheZ/lean-stat-learning-theory` | `216e578c` | Apache-2.0 | Statistical-learning theorem source; inventory and future signed-RAG input |
| `PatrickMassot/leanblueprint` | `56e066d3` | Apache-2.0 | Blueprint metadata/tooling reference; not a paper parser or proof authority |
| `lean-dojo/LeanDojo-v2` | `936ea0dd` | Apache-2.0 | Proof-state interaction and tracing reference; no trained tactic policy is active |
| `lean-dojo/ReProver` | `fd6d99c0` | MIT | Tactic-state retrieval/search reference implementation |
| `project-numina/numina-lean-agent` | `1c9af8a5` | README declares MIT; no repository-root license file found | Agent/tool-loop and per-round trace reference; no code copying until license packaging is clarified |
| `ykzeng-yale/atlas-lean` fork | `c5a10f1a` | CC BY-NC 4.0 with no-training rider | Retrieval corpus source study only; excluded from training and model evaluation |
| `ykzeng-yale/autoform-bot` fork | `f137da6c` | CC BY-NC 4.0 | Statement/evaluation harness source study only; no commercial/default dependency |

The remaining collection layers, including conjecturing, counterexample search,
foundations, diagrammatic proof, and multimodal mathematics, were classified in
the eight-layer inventory. They should not be installed merely for coverage.
Their mechanisms enter the runtime only when a measured statistical-theory
blocker and an admissible held-out evaluation justify the integration.

## Fresh Cross-Family Runtime Evidence

The full-live run
`runs/main_worker_fresh_cross_family_full_live_20260713_v1` used two unrelated
fresh families:

- `experimental_design/design_based_variance_bound`
- `multiple_testing/multiple_testing_fdr_bh`

Both reached live Architect, RetrievalMemory, TheoryDeveloper, generated-code
workers, Formalizer, local Lean feedback, and ProofEngineer. The result was
honestly incomplete: two `MAX_ITERATIONS_REACHED` statuses, scorecard 88/112,
66 kernel-verified support subclaims, eight formal gaps, zero generated algorithm
sandbox executions, and zero exact source-theorem closures.

The earliest coding failures were infrastructure failures rather than missing
task-specific formulas:

- a raw substring guard interpreted the suffix `os.` inside
  `conservativeness_ratios.` as operating-system access;
- one generated estimator alias did not bind to the Architect-owned gap ID;
- a simulation subprocess reached execution but returned tuple dictionary keys;
  the final `TypeError` was truncated, a partial JSON file was parsed as a metric,
  and the failure was mislabeled as no executable draft.

The current patch fixes the shared mechanism, not the generated task outputs:
AST/capability validation replaces raw forbidden substrings and local-method
enumeration; one unambiguous generated target is provenance-bound to the
canonical gap key; results are serialized before publication; subprocess
diagnostics retain the final exception; and execution failures are distinct
from missing drafts and metric-gate failures.

The capability contract also exposes the complete, untruncated list of
Architect-owned implementation-gap IDs. The prompt and validator now agree
that every gap receives one matching implementation target and generated
draft; only a single-gap task permits automatic identity binding. This removes
the prior contradiction in which validation required all gaps while the model
was instructed to emit exactly one draft.

The broader public-method policy was also adversarially checked. A canary found
that a generator frame plus callable-name rebinding could recover a restricted
builtin even without private attribute syntax. The generic sandbox boundary now
rejects frame-reflection access and protected-binding rebinding while retaining
ordinary generator expressions,
blocks reflective string formatting, and launches with a deterministic
secret-free environment. These are execution-security constraints, not
statistical formula or task-specific coding rules.

The first post-patch two-family run,
`runs/main_worker_fresh_cross_family_full_live_20260713_v2_generated_feedback_patch`,
improved the scorecard to 94/112 and produced one live generated algorithm
execution/pass plus three live generated simulation executions. It remained
incomplete: statuses were one `BLOCKED` and one `MAX_ITERATIONS_REACHED`, only
one simulation passed its runtime gate, 30 support subclaims were kernel
verified, eight formal gaps remained, and exact source-theorem closure stayed
zero.

That run exposed a second generic policy defect. The old coverage gate searched
the entire serialized blackboard, so phrases such as `assumption coverage` and
formal-source `coverage_status` caused a multiple-testing task to require an
interval-coverage metric. Two locally executed FDR/power result packets were
therefore rejected for an irrelevant reason, and AlgorithmEngineer was starved
behind the bounded simulation retry. Coverage requirement detection now reads
only explicit metric-contract, acceptance-gate, target, and flag fields. Tags,
source coverage metadata, and general objectives cannot activate it.

A fresh FDR-only full-live run,
`runs/main_worker_fdr_full_live_20260713_v3_explicit_metric_contract`, verified
the behavioral change: the first generated simulation executed with return
code zero, no parse error, no metric-gate error, and continued directly to a
generated AlgorithmEngineer sandbox that also executed with return code zero.
The run still ended `MAX_ITERATIONS_REACHED`, scorecard 91/112, with 30 verified
support subclaims, four formal gaps, and zero exact theorem closures. These
passes establish executable feedback and remove the false coverage rejection;
they do not establish that every natural-language FDR/utility acceptance
inequality was checked. Converting those gates into typed metric-path/operator/
threshold contracts is now an explicit remaining requirement.

The next FDR full-live run,
`runs/main_worker_fdr_full_live_20260713_v4_typed_metric_contract`, exercised
those typed paths but exposed a deeper evaluator-design error. Simulation and
AlgorithmEngineer authored both their generated code and their own required
acceptance gates. The packets could therefore invent statistically false or
irrelevant required conditions, including an all-null FDR-equals-zero condition,
or use a metric key that their own generated artifact did not return. Typed
syntax made these failures observable; it did not make self-authored gates
independent.

The current patch moves empirical requirement authority upstream. In capability
evaluation, ArchitectCoordinator must emit an immutable, source-anchored,
domain-neutral requirement set before either coding agent runs. A requirement
fixes metric semantics, measurement protocol, comparison, tolerance,
aggregation or quorum, target subsystem, and source anchors. Coding agents may
bind only the generated artifact and result path; they cannot invent, omit, or
weaken a required condition. AgentRuntime independently reopens the Architect
plan, validates every artifact/requirement pair, recomputes fingerprints, and
rejects the packet before sandbox execution when authority is missing or
changed. Capability scorecards count only runtime-bound, authority-validated
contracts whose required rows pass. A coding-agent packet cannot satisfy that
row by agreeing with itself.

This mechanism adapts, rather than imports, several mature source ideas: DAP's
withheld-answer and matched-ablation discipline; Goedel-Prover V2's immutable
initial/correction identities; CodexProver's pre-registration, packet binding,
runtime-read audit, and independent exact evaluator; and ERA/AlphaEvolve-style
separation between candidate generation and evaluator feedback. It remains one
typed child path of the existing Architect/AgentRuntime control plane. No
external model client, parser, benchmark score, run corpus, or second
orchestrator is imported.

This is still empirical-control infrastructure, not semantic authority or
proof. Architect can propose a schema-valid but statistically poor requirement.
A subsequent milestone must bind every requirement source anchor to accepted
question/theory artifacts and obtain an independent Theory/Critic semantic
review before the requirement becomes a capability acceptance gate. Local
execution remains implementation/simulation evidence; exact theorem claims
still require the target-bound Lean/AXLE kernel path.

The subsequent FDR v5 invocation was stopped and is not capability evidence.
Its first Architect response remained schema-invalid after bounded repair, and
the CLI then began a detached coding-agent component calibration despite the
integrated runtime failure. That diagnostic exposed two design errors rather
than an FDR theorem problem: full-live still had a second post-runtime
evaluation plane, and legacy metric refresh could discard typed-contract
context. The current implementation removes automatic component calibration
from full-live, preserves Architect requirement authority through repair and
refresh, and permits execution-only debug checks only when no typed contract is
required. Optional standalone component commands remain available as explicitly
non-integrated calibration.

FDR is now classified only as a historical canary. The next evaluation is
pre-registered in
`benchmarks/autonomous_cross_family_e2e_protocol_20260713.json`: survival and
sequential inference form the development panel; high-dimensional PCA and
extreme-value inference form the disjoint held-out panel. The CLI rejects a
partial panel, a one-family full-live selection, resume state, or prior task
learning memory before making a model call. The development panel has now run
through v8: both survival and sequential tasks ended `BLOCKED`, with a
`95/118` capability scorecard, 72 kernel-verified support subclaims, 8 formal
gaps, and zero exact source-theorem closures. The held-out panel remains unrun,
and no panel result has been promoted to exact source-theorem evidence.

## July 15 Planner Follow-Through Evidence

The live Formalizer PF/BV component run
`main_worker_formalizer_pf_dynamic_schema_20260714_v23_source_anchor_envelope`
produced a validator-accepted, source-anchored pseudo-formal packet with four
work-order rows and three routable rows. Its evidence status remains explicitly
non-proof; it did not establish a Lean theorem.

Fresh development-panel run v24 reached generated simulation, independent
semantic review, generated algorithm execution, Formalizer, local Lean/LSP
feedback, ProofEngineer, and contract-valid GapPlanner actions in both the
survival and sequential families. Both tasks then failed at the same generic
handoff defect: contract-revision tasks discarded the upstream theory,
simulation, and algorithm artifact IDs. The run ended `BLOCKED` 2/2 with an
88/125 scorecard, zero kernel-verified subclaims, four formal gaps, and zero
exact source-theorem closures. Commit `d9f04875` changed the revision task to
inherit the current typed inputs and added a runtime regression for all three
artifact IDs; the complete 1,110-test runtime file passed before the commit.

Fresh v25 behaviorally confirmed that correction: the sequential task completed
two lineage-bound contract revisions without the prior
`formalization_gap_planner_action_upstream_lineage_missing` failure. It instead
failed closed after the staged response contract remained incomplete. The only
remaining stage error rejected a substantive boundary that explicitly named
the short structured primitive ID `t1`; the old anchor heuristic ignored all
tokens shorter than four characters. The current correction admits exact
token-sequence matches against structured primitive/declaration/node/route IDs
while retaining placeholder and unrelated-prose rejection. Replaying the exact
v25 stage artifact changes the boundary result from rejected to anchored without
altering its generated content.

The v25 survival task independently exposed a provider-budget problem: both
large route-planner calls returned zero tokens after the ordinary 120-second
model timeout. Full-live now gives an otherwise unspecified GapPlanner call a
240-second provider budget while preserving explicit operator overrides. v25
ended `BLOCKED` 2/2 with a 95/125 scorecard; both generated simulations and both
generated algorithms executed and passed independent semantic review, but
kernel-verified subclaims and exact source-theorem closures remained zero. The
PCA/extremes held-out panel therefore remains locked.

Fresh v26 confirmed the provider-budget correction behaviorally. The survival
planner crossed the old 120-second boundary, returned a source-bound response,
incrementally reused accepted staged fragments across two contract revisions,
and finally compiled contract-valid action rows into an immutable
ProofEngineer work order. The work order drove formal-source retrieval and a
new LLM Formalizer packet, rather than being promoted as proof. That packet
failed local validation because it emitted an empty optional PF/BV shell. The
subsequent Formalizer repair task preserved the work-order ID and hash in its
typed inputs but replaced the environment feedback containing the bound payload,
so the next validator correctly failed closed before another model, retriever,
or Lean call. Provider, packet-validation, and Lean-candidate repair feedback
must all inherit the same immutable action binding; this is a generic child-task
lineage invariant, not a survival-specific repair.

The v26 sequential task exposed a separate upstream contract defect. Two fresh
LLM simulations executed and were independently reviewed, but the reviewer
found both an estimand substitution and an Architect-authored frozen gate that
was mathematically infeasible for the named fixed Bernoulli likelihood-ratio
process. The frozen source anchor claimed
`KL(Bernoulli(0.75) || Bernoulli(0.5))` was about `0.415`; the expression written
in the same requirement is about `0.131`, below its required `0.2` per-step
growth threshold. A second optional requirement also encoded "at least eight
rejections" while its prose intended "at most eight." The runtime correctly
kept both defects open and did not let the coding agent weaken Architect
authority. The design correction is an independent pre-execution semantic and
mathematical-feasibility review of Architect metric requirements, with typed
feedback routed to an Architect revision before thresholds are frozen and any
empirical result is observed. Post-result threshold relaxation remains
forbidden.

The shared runtime correction now distinguishes independent semantic-review
findings with a typed `repair_scope`. A defect resolvable entirely by fresh
source code receives one bounded coding-agent revision. `upstream_theory`
routes exact findings through ArchitectCoordinator to theory repair.
`upstream_metric_contract` deterministically records
`EVALUATION_PROTOCOL_REVISION_REQUIRED`, preserves the failed execution and
frozen requirement fingerprint, and stops the current candidate before another
Retrieval -> Theory -> Simulation cycle. The legacy ambiguous scope remains
replay-compatible but is not emitted by new reviews. Before execution, a
separate Opus reviewer now checks every Sonnet-authored candidate across six
domain-general semantic and mathematical dimensions; only an independently
accepted, fingerprint-bound set can freeze. The author/reviewer loop lives in
dedicated modules and contains no sequential-test validator, hardcoded
numerical correction, task-family formula, or Lean grammar.

Overall v26 ended `BLOCKED` 2/2 with a 94/125 scorecard, three generated
simulation executions, one generated algorithm execution, zero kernel-verified
subclaims, two formal gaps, and zero exact source-theorem closures. No legacy
post-runtime theorem fallback ran, and the PCA/extremes held-out panel remains
locked.

The fresh v27 development run at commit `2d88881e` ended with both tasks at
`MAX_ITERATIONS_REACHED`, scorecard 89/125, zero exact theorem closures, and no
held-out unlock. It verified that source-code and upstream semantic findings
reach typed owners, but it also showed three repeated Architect whole-chain
replans per task with unchanged frozen requirement-set IDs. That negative
evidence motivated the independent pre-execution reviewer and explicit
post-result protocol disposition above. A new cross-family live run is still
required; unit and replay evidence cannot establish E2E readiness.

## Reuse Rules

An external mechanism may enter the default runtime only when all of the
following hold:

- source commit, license, configuration, and relevant assets are pinned;
- the adapter is a typed AgentTask/AgentStepResult child of the one Architect
  control plane;
- generated artifacts and feedback have immutable parent/child hashes;
- provider calls are scoped and secret-free;
- retrieval, empirical execution, pseudo-formal review, and kernel proof remain
  distinct evidence classes;
- a fresh held-out evaluation compares the mechanism against a matched control;
- no theorem-specific alias, grammar rewrite, tactic template, or validator
  relaxation is added to make one benchmark pass.

## Next Integration Order

1. Run a fresh cross-family development evaluation with the independent metric
   reviewer enabled. Require accepted pre-execution certificates for both task
   families, no repeated whole-chain replan under an invalid frozen protocol,
   and exact source-theorem kernel closure before held-out unlock. Then add
   task-agenda/budget reservation so empirical repair cannot starve the proof
   lane.
2. Preserve CodexProver's 30-target frozen cohort through its final two first
   attempts, then close it as underpowered without replacement targets or
   matched retries. Pre-register a better-powered exact-feedback-only versus
   exact-feedback-plus-MCP study before adapting any OpenProver/LSP escalation
   policy; do not import its orchestrator or run corpus.
3. Add a real tactic-state prover provider using OpenProver and
   LeanDojo/ReProver-style state/retrieval/search contracts; retain local Lean as
   final authority. Evaluate Kimina separately as a throughput transport on the
   same target/project hashes, not as a second proof authority.
4. Build signed multi-source RAG snapshots for selected EmpericalProcessLEAN
   branches, with commit-level provenance and retrieval ablations before default
   admission.
5. Add declared scientific Python and R execution environments with resource
   isolation, package manifests, exact stdout/stderr feedback, and task-supplied
   metric contracts.

No source reviewed here closes the current completion gate. The project remains
incomplete until two unrelated fresh statistical tasks each finish theory,
implementation/simulation, formal RAG, iterative Lean repair, Critic review,
and exact source-theorem kernel closure.
