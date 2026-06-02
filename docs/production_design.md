# AI Statistician Production Design

This folder is the production-oriented successor to `Preliminary Attempt/`.
The goal is not to make a bigger interview demo. The goal is a system whose
claims are auditable:

1. The theory layer emits only estimator families with registered formal
   obligations.
2. The formal layer proves Mathlib-backed obligations through a verifier.
3. The algorithm layer uses vetted implementations for the estimator family.
4. The simulator measures bias, RMSE, empirical SE, estimated SE, and 95%
   coverage.
5. Retrieval is audited over the full local statistics proof bank rather than
   treated as a hard-coded lemma lookup.
6. Every run writes a JSON trace that can be used for debugging, evaluation,
   and future training.

## Current Implemented Architecture

```text
OpenResearchQuestion
  -> ProblemFormalizer
       problem class, DGP sketch, estimand, assumptions, asymptotic regime
  -> TheoryPlanner
       registry-backed candidate procedure, informal derivation text, theorem goals
  -> KnowledgeRetriever
       method cards + local Lean/proof-search sources + paper/source grounding
  -> FormalSubclaimProver
       AXLE/mock verification for registered Mathlib-backed subclaims
       explicit FORMAL_GAP records for frontier theorem pieces
  -> AlgorithmEngineer / Registry
       vetted implementation + code hash
  -> ResearchSimulator
       DGP environment, Monte Carlo diagnostics, simulation diagnosis
  -> ResearchReport
       theory plan + proof status + simulation evidence + next_iteration_agenda
```

The base `AIStatisticalTheoryLab.run()` path is a one-pass production scaffold.
The simulator and formal prover do not disappear at the bottom of the pipeline:
their failures are classified into `next_iteration_agenda` items with an owner
agent, trigger, action, evidence, and stop condition.

The first live loop over this scaffold is `ResearchLoopCoordinator.iterate()`.
It executes the agenda routes that are safe today: Monte Carlo precision
failures trigger a larger-budget rerun, monitor-only traces terminate cleanly,
formal gaps are reviewed against attached local Lean/source hits, and simulation
theory/procedure failures can be converted into scoped revision artifacts. There
is a narrow default `DefaultProofEngineer`: for a `FORMAL_GAP`, it can select
an already registered proof-bank bridge, verify that bridge with the configured
verifier, and emit a contract-complete repair artifact for downstream theory
plan promotion. When the bridge is kernel verified, the coordinator now requests
a bounded rerun and carries a `proof_bridge_integration` theory revision into
the next round. `AIStatisticalTheoryLab` applies that revision by attaching the
verified proof obligation to the matching theorem goal and procedure roadmap.
The theorem status remains `FORMAL_GAP`; the bridge is a verified dependency,
not a proof of the full frontier theorem. There is also a conservative
`DefaultTheoryDeveloper`: for a `THEORY_OR_PROCEDURE_ISSUE`, it turns failed
simulation diagnostics such as coverage or bias into a concrete revised
procedure/theorem/assumption artifact. This is not yet free-form theory
invention. When the artifact satisfies its contract, the coordinator carries it
as revision state into the next round, where `AIStatisticalTheoryLab` applies it
as a safe overlay before retrieval, proof, and simulation: it may rename and
annotate the candidate procedure and add new theorem goals/formal gaps, but it
does not change the vetted algorithm implementation. A conservative
`DefaultAlgorithmEngineer` handles `IMPLEMENTATION_OR_NUMERICAL_ISSUE` by
emitting a repair artifact with the current implementation hash, reproduction
test context, finite-metric/numerical-guard patch summary, and rerun metric
targets. This is a repair contract, not arbitrary generated code execution. The
coordinator also has a
registered live-repair handler interface: a
TheoryDeveloper, ProofEngineer, AlgorithmEngineer, or simulator-extension agent
can be plugged in for a trigger such as `THEORY_OR_PROCEDURE_ISSUE`; if it
returns a contract-complete repair artifact and requests a rerun, the
coordinator executes the next round inside the same bounded loop. The contract
is trigger-specific: theory repairs must include revised procedures/theorem
goals/assumption deltas/expected simulation deltas; proof repairs must include
AXLE-verifiable proof fields and cannot request a rerun unless
`kernel_verified=true`. Routes that need substantive new proof search,
sandboxed code patching, or simulator construction still stop honestly with
`REQUIRES_PROOF_ENGINEER` or `REQUIRES_SIMULATOR_EXTENSION`, or with a scoped
repair proposal, unless a stronger handler is registered.

Current release-style evidence for this bounded loop is split intentionally:
`proof-audit --local-lean` verifies the registered proof bank at `112/112`, while
`research-system-audit` exercises the loop, Lean-RAG dependency retrieval, proof
bridge routing, and simulation/audit gates. When the system audit is not run
with `--local-lean`, its proof rows are scaffold evidence rather than fresh
kernel evidence. The status remains `FORMAL_GAPS_BRIDGED`, which is intentional:
proof bridges are integrated into the theory roadmap while the remaining
asymptotic/frontier primitives stay explicitly open.

`StatisticalQuestion` can come from the built-in registry or from JSON. External
questions may name a supported `dgp_family` and `estimator_family` explicitly,
or the intake layer can infer them for the supported families below. Unsupported
or ambiguous questions fail before simulation rather than silently inventing
unsupported formal guarantees.

Architecture audit:

```bash
python3 -m ai_statistician.cli architecture-audit \
  --out runs/architecture_audit
```

This writes `architecture_audit_manifest.json` and `architecture_audit.md`. The
expected status is `PARTIAL_LIVE_FEEDBACK_LOOP_WITH_SCOPED_AUTONOMY`: correct
for the current auditable release scaffold, still not correct as a claim of a
fully autonomous AI statistician.

Bounded research loop:

```bash
python3 -m ai_statistician.cli research-loop \
  --question-file examples/research_questions.json \
  --max-rounds 2 \
  --runs 100 \
  --out runs/research_loop
```

This writes `research_loop_manifest.json`, one trace per question, and
`research_loop_repair_tasks.jsonl`. When a live handler actually executes, the
loop also writes `research_loop_live_repair_artifacts.jsonl`, a first-class
record of verified bridge artifacts or contract-checked theory/algorithm repair
outputs. The repair-task JSONL turns blocked routes into agent-ready repair
tasks with prompts, context, output contracts, and acceptance criteria. Together
these files are the first executable bridge from `next_iteration_agenda` to live
action, training/exportable repair work, and replayable repair artifacts. It is
not yet full autonomous theory repair.

Repair-task audit and training export:

```bash
python3 -m ai_statistician.cli research-loop-repair-audit \
  --loop-dir runs/research_loop \
  --out runs/research_loop_repair_audit
```

This validates every loop repair task and writes
`research_loop_repair_sft_train.jsonl`,
`research_loop_repair_sft_validation.jsonl`, and
`research_loop_repair_audit_manifest.json`. These are planning examples for the
next TheoryDeveloper / ProofEngineer / AlgorithmEngineer agents; they do not
claim the repair has already been solved.

Executed live-repair artifacts have a separate audit because they are stronger
than planning tasks: they are the handler outputs that may include AXLE/Lean
kernel evidence or rerun-ready theory/algorithm artifacts.

```bash
python3 -m ai_statistician.cli research-loop-live-repair-audit \
  --loop-dir runs/research_loop \
  --out runs/research_loop_live_repair_audit
```

This validates `research_loop_live_repair_artifacts.jsonl` independently and
writes `research_loop_live_repair_sft_train.jsonl`,
`research_loop_live_repair_sft_validation.jsonl`, and
`research_loop_live_repair_audit_manifest.json`. Proof repair artifacts are
training-ready only when their output contract is satisfied and AXLE/Lean kernel
verification evidence is present for `axle_lean_kernel` claims. This closes a
small but important architecture loop: live feedback no longer ends as a log; it
becomes validated repair data for future ProofEngineer / TheoryDeveloper
training.

The first proof-search controller is deliberately bounded and whole-proof level:

```bash
python3 -m ai_statistician.cli proof-search-audit \
  --max-obligations 12 \
  --policy-model-json runs/proof_policy_model/proof_policy_model.json \
  --value-model-json runs/proof_search_value_model/proof_search_value_model.json \
  --out runs/proof_search_audit
```

`BestFirstWholeProofSearchController` builds a candidate proof-body frontier
from registered proof memory, expected-lemma templates, built-in whole-proof
tactic templates, retrieved proof-bank neighbors, formal-source declaration
templates from the local Lean/StatInference/Atlas index, and optional probes.
It can score each candidate with the trained whole-proof policy ranker and the
trained value model, then verifies expanded nodes with the configured verifier.
The audit writes `proof_search_results.jsonl` with node-level verifier feedback,
tactic-template counts, retrieval candidate counts, formal-source candidate
counts, base scores, policy scores, and value scores. This is a real search
controller rather than one-shot lookup, but it is not tactic-state best-first
search, MCTS, or RL yet; those remain the next prover-engine layer.

The node traces can be exported as process-reward/value-model data:

```bash
python3 -m ai_statistician.cli proof-search-training-export \
  --results-jsonl runs/proof_search_audit/proof_search_results.jsonl \
  --out runs/proof_search_training_export
```

Each row preserves the theorem, candidate proof body, verifier errors, reward,
and `kernel_verified` flag. This converts verifier feedback into learning data
without claiming a trained value model exists yet.

The first actual training stage is a small deterministic value baseline:

```bash
python3 -m ai_statistician.cli proof-search-value-train \
  --train-jsonl runs/proof_search_training_export/proof_search_process_train.jsonl \
  --validation-jsonl runs/proof_search_training_export/proof_search_process_validation.jsonl \
  --out runs/proof_search_value_model
```

It fits logistic feature weights over proof-search node features such as
candidate source, score, proof-body markers, and verifier errors. This closes
the first training-pipeline gap in an auditable way while keeping the limit
clear: it is a baseline value model, not a neural tactic policy or RL prover.
The local/AXLE verifier wrappers reject `sorry`, `admit`, and introduced
`axiom`s before invoking the backend. This is required because Lean can compile
`sorry` with a warning; the AI Statistician proof boundary treats placeholders
as failed candidates, not kernel evidence. Current local-kernel release evidence
exports `24` proof-search process examples from the audit sample: `12` positive
kernel-verified registered proofs and `12` negative rejected invalid probes.

The first trainable proof-policy stage is separate from the value baseline:

```bash
python3 -m ai_statistician.cli proof-policy-train \
  --train-jsonl runs/proof_training_export/proof_sft_train.jsonl \
  --validation-jsonl runs/proof_training_export/proof_sft_validation.jsonl \
  --out runs/proof_policy_model
```

It trains a logistic whole-proof candidate ranker over proof SFT examples. The
model ranks known proof bodies as candidates for a theorem; it does not generate
novel Lean syntax and it is not a tactic-state policy.

Algorithm repair promotion is intentionally one more step beyond generic live
repair auditing:

```bash
python3 -m ai_statistician.cli algorithm-repair-promotion \
  --loop-dir runs/research_loop \
  --out runs/algorithm_repair_promotion
```

This filters `algorithm_repair_from_numerical_failure` artifacts into
`algorithm_repair_promotion_queue.jsonl`. The queue contains sandbox patch
candidates with implementation hashes, reproduction context, and rerun gates. It
rejects any artifact that embeds executable code fields such as `generated_code`
or `python_code`; the next worker must create the patch in a sandbox, run the
algorithm audit, and rerun finite simulations before promotion.

The first bounded sandbox worker is:

```bash
python3 -m ai_statistician.cli algorithm-repair-sandbox \
  --promotion-dir runs/algorithm_repair_promotion \
  --out runs/algorithm_repair_sandbox
```

It still does not mutate production code. It checks that each candidate targets
the current vetted implementation hash, reruns the algorithm registry audit, and
emits `algorithm_repair_sandbox_results.jsonl` with allowed patch scopes and the
next required gate. This is the bridge between repair contracts and future
patch/apply/rerun automation.

The second bounded sandbox worker records non-mutating application evidence:

```bash
python3 -m ai_statistician.cli algorithm-repair-sandbox-apply \
  --sandbox-dir runs/algorithm_repair_sandbox \
  --out runs/algorithm_repair_sandbox_apply
```

It accepts only `SANDBOX_PATCH_PLAN_READY` rows, checks that production was not
mutated, reruns the deterministic algorithm registry audit, and emits
`algorithm_repair_sandbox_apply_results.jsonl`. The resulting artifact is still
not a production patch: `patch_applied_to_production=false`,
`patch_application_mode=non_mutating_guard_plan`, and the required next gate is
an isolated code patch plus finite simulation rerun. This keeps the feedback
loop executable and auditable without admitting arbitrary generated code.

The third bounded sandbox worker adds rerun-style evidence:

```bash
python3 -m ai_statistician.cli algorithm-repair-sandbox-rerun \
  --apply-dir runs/algorithm_repair_sandbox_apply \
  --question-file examples/research_questions.json \
  --runs 50 \
  --out runs/algorithm_repair_sandbox_rerun
```

It locates the target procedure in the open-question registry, reruns the
current vetted simulator, and records baseline plus ledger-level guarded
metrics. This is still not patched-code evidence. The artifact explicitly says
`production_patch_applied=false` and requires a future isolated workspace patch
with before/after simulation comparison before any production promotion.

The fourth bounded sandbox worker executes the first isolated patch comparison:

```bash
python3 -m ai_statistician.cli algorithm-repair-sandbox-patch-eval \
  --apply-dir runs/algorithm_repair_sandbox_apply \
  --question-file examples/research_questions.json \
  --runs 50 \
  --out runs/algorithm_repair_sandbox_patch_eval
```

It writes a deterministic finite-metric guard patch into
`isolated_patch_workspace/`, imports that module, and compares baseline
simulator metrics against the isolated patched simulator. It still does not run
LLM-provided code and still does not mutate production:
`production_patch_applied=false`, `promotion_ready=false`. The purpose is to
turn AlgorithmEngineer repair plans into executable before/after evidence while
preserving the review gate for any real source commit.

## Target Closed-Loop Research Lab

The broader target is not only a registered estimator executor. It is an AI
statistical theory lab that can accept paper-style open questions and produce an
auditable research trace, then actively revise itself from verifier and
simulator feedback:

```text
OpenResearchQuestion
  -> ProblemFormalizer
  -> ResearchCoordinator.iterate(max_rounds)
       -> LLM TheoryDeveloper
            propose/revise estimand, estimator/test/procedure, assumptions,
            theorem statements, informal proof plan, and expected diagnostics
       -> Retrieval Layer
            Mathlib, StatInference, EmpiricalProcessLEAN, atlas-lean,
            papers, proof bank, Autoform targets, provider-fusion candidates
       -> Formalizer + ProofEngineer
            formalize definitions/theorems, prove available subclaims,
            repair statements/proofs, or emit explicit FORMAL_GAP
       -> AlgorithmEngineer
            implement or repair vetted/sandboxed procedure code
       -> ResearchSimulator / Empirical Critic
            run DGP/stress tests, classify bias/SE/coverage/FDR/power failures
       -> Coordinator diagnosis
            proof syntax/type error -> Formalizer repair
            missing lemma -> retrieval/proof-bank expansion
            assumptions too weak -> TheoryDeveloper revision
            biased estimator or wrong SE -> TheoryDeveloper revision
            implementation/numerical issue -> AlgorithmEngineer repair
            DGP mismatch -> ProblemFormalizer/Simulator revision
  -> ResearchReport + AuditTrace + ProofBank/Gaps/Training Queues
```

So the intended system is not `question -> theory -> proof -> code -> sim ->
report`. It is a closed loop:

```text
question
  -> informal statistical theory development
  -> formalization/proof attempts
  -> algorithm implementation
  -> simulation criticism
  -> theory/proof/algorithm revision
  -> repeat until proved/validated, explicitly gapped, or budget exhausted
```

Current honest boundary: `TheoryPlanner` already emits informal derivation text
and theorem roadmaps, `FormalSubclaimProver` already performs real AXLE/Lean
verification for registered proof-bank obligations, `ResearchSimulator` already
diagnoses failures, and `ResearchLoopCoordinator` now executes the scoped
actions above, including `DefaultProofEngineer`,
`DefaultTheoryDeveloper`, `DefaultAlgorithmEngineer`, and registered live repair
handlers when supplied. The
missing architecture piece is default substantive autonomous *solution* of
repairs: an LLM TheoryDeveloper that can invent and justify new estimator
families rather than only applying scoped overlays, a ProofEngineer that proves
new Lean obligations rather than only bridge-selecting from the proof bank, and
an isolated AlgorithmEngineer worker that applies real code patches and reruns
finite simulation diagnostics from simulator evidence. The current algorithm
repair lane reaches non-mutating sandbox apply and current-registry rerun
artifacts; it intentionally stops before production mutation.

The CLI entry point is:

```bash
python3 -m ai_statistician.cli research-benchmark \
  --question-file examples/research_questions.json \
  --runs 100 \
  --out runs/research_benchmark
```

The same loader accepts paper-style Markdown/text files. A Markdown file may use
sections of the form `## question_id: Title`, an optional `Tags:` line, and a
free-form abstract-style description:

```bash
python3 -m ai_statistician.cli research-benchmark \
  --question-file examples/research_paper_abstracts.md \
  --runs 100 \
  --out runs/research_paper_benchmark
```

Real AXLE verification for the Mathlib-backed subclaims:

```bash
/Users/yukang/LeanProjects/LeanPractice/.venv/bin/python \
  -m ai_statistician.cli research-benchmark \
  --real-lean \
  --runs 60 \
  --out runs/research_benchmark_axle
```

Human-readable research report:

```bash
python3 -m ai_statistician.cli research-report \
  --run-dir runs/research_benchmark \
  --out runs/research_report
```

This consumes persisted research traces and writes `research_report.md` plus
`research_report_manifest.json`. The report is not new proof evidence; it is a
review layer over the audited traces, assembling problem extraction, informal
procedure derivations, theorem goals, proved subclaims, formal gaps, simulation
diagnostics, stress tests, paper/source grounding, and local Lean/StatInference
candidates into one document.

Typed claim ledger:

```bash
python3 -m ai_statistician.cli claim-ledger \
  --run-dir runs/research_benchmark \
  --out runs/claim_ledger
```

This consumes the same persisted research traces and writes
`claim_ledger_manifest.json`, `claim_ledger.jsonl`, and `claim_ledger.md`.
Unlike the human report, it is a machine-facing coordination substrate: every
problem card, informal procedure derivation, theorem goal, formal subclaim,
simulation row, and next-iteration agenda item becomes a typed claim row with a
separate evidence level.  This is the artifact future theory/proof/simulation
agents should update when closing the loop.  It deliberately distinguishes
retrieval/gap evidence from Lean-kernel proof evidence and simulation support
from formal proof.

Research trace audit:

```bash
python3 -m ai_statistician.cli research-trace-audit \
  --run-dir runs/research_benchmark \
  --out runs/research_trace_audit
```

The audit validates that each research trace matches the benchmark manifest,
contains the extracted problem specification, source-text extraction evidence
for the problem class / DGP / estimand / assumptions / asymptotic regime,
candidate procedures, theorem goals, a first-class `theory_plan` tying the
informal derivation to candidate procedures, retrieval context, theorem
roadmap, proof/gap status, simulation plan, and a `next_iteration_agenda` that
routes formal gaps, failed proof obligations, and simulation diagnoses back to
the responsible agent. It also validates retrieved knowledge cards, related
local paper/source hits, formal proof/gap records, exported gap skeleton files,
simulation metrics, diagnostic-to-metric coverage, stress-test ledgers, vetted
research algorithm fingerprints, and honest limitations when gaps remain.

The `paper_sources` section is a separate local retrieval layer over the
frontier statistical-theory benchmark and the AI-for-math paper log. For
frontier benchmark papers, `expected_theoretical_results` and
`evaluation_prompt` are recorded as withheld fields and are not used in the
search text, so this grounding layer can be audited without leaking benchmark
answers into the theory planner.

Each simulation row also includes the problem's declared `stress_tests` plus a
compact `stress_test_metrics` object. These rows are intentionally diagnostic
rather than over-claimed: they certify that the simulation layer evaluated the
declared stress scenarios against available metrics, while full theorem-level
coverage for those scenarios remains part of the formal-gap backlog when it is
not already in the proof bank.

The `next_iteration_agenda` is the explicit research-loop handoff. Each item
has an owner agent (`formal_verifier`, `theory_developer`,
`algorithm_engineer`, `simulator_agent`, or `research_coordinator`), a trigger,
an action, evidence, and a stop condition. This keeps the trace from ending at
"metrics plus gaps": it records exactly what the next round should repair or
formalize. Trace audit checks this semantically, not only structurally: every
`FORMAL_GAP`, failed proof obligation, and non-OK simulation diagnosis must
have a matching agenda item routed to the owner implied by the trace evidence.

Formal gap backlog audit:

```bash
python3 -m ai_statistician.cli research-gap-audit \
  --run-dir runs/research_benchmark \
  --out runs/research_gap_backlog
```

This aggregates every `FORMAL_GAP` across a benchmark run into
`research_gap_backlog_manifest.json` and a Markdown report. Each row links the
unproved theorem goal to its Lean skeleton artifact, proof strategy, required
formal primitives, candidate procedure, retrieved knowledge cards, already
verified subclaims, and retrieved local Lean/StatInference declarations from the
formal-source index. Each missing primitive also carries its own
`primitive_formal_source_hits` list, which turns broad frontier gaps into
actionable theorem-mining tasks such as "find local support for Slutsky" or
"find local support for Davis-Kahan" instead of only retrieving candidates for
the whole theorem goal. This makes the formalization frontier auditable as a
library-construction backlog rather than leaving it spread across individual
traces. The release-style `research-system-audit` includes this as a gate.

Formalization target queue:

```bash
python3 -m ai_statistician.cli formalization-target-audit \
  --run-dir runs/research_benchmark \
  --out runs/formalization_target_audit
```

This consumes the formal-gap backlog and ranks missing primitives into concrete
Lean theorem-development targets. Each row records the primitive, how many gaps
it unlocks, affected problem classes and theorem goals, local Mathlib/
StatInference declaration candidates, supporting proof-bank obligations, and a
suggested next proof-bank or library step. The release-style
`research-system-audit` writes this queue as
`formalization_target_audit/formalization_target_manifest.json`, so the lab can
move from "known gaps" to a prioritized theorem-building plan.
Rows also include `bridge_readiness`, for example
`PROOF_BANK_AND_LOCAL_SOURCE` when a target has both a local declaration
candidate and existing AXLE-verified proof-bank obligations to build from.
They also include `bridge_candidate_obligations`: a narrower, token- and
tag-aware ranking over the supporting proof obligations, so the next theorem
developer sees the most relevant verified bridge first instead of an
alphabetical list of every proof obligation attached to the broader theorem
goal.

Formal-gap Lean task export:

```bash
python3 -m ai_statistician.cli formal-gap-task-export \
  --run-dir runs/research_benchmark \
  --out runs/formal_gap_lean_tasks
```

This converts every audited `FORMAL_GAP` skeleton into a JSONL Lean task using
the legacy `lean_task.schema.json` shape (`task_id`, `imports`, `namespace`,
`statement`, `allowed_sorry`, `tags`, `dependencies`, and
`expected_patterns`) plus richer statistical metadata. These tasks are not proof
claims. They are theorem-development work packets for a future formalizer,
LeanDojo/ReProver-style search loop, or human Lean developer. The release-style
`research-system-audit` writes them as
`formal_gap_lean_tasks/formal_gap_lean_tasks.jsonl`.

Autoform target export:

```bash
python3 -m ai_statistician.cli autoform-target-export \
  --run-dir runs/research_benchmark \
  --out runs/autoform_targets
```

This is the operational bridge from the AI Statistician formal-gap queue to the
Autoform-Bot harness. It consumes the audited Lean task export and writes
`autoform_targets.yaml` in Autoform-Bot's `FormalizationTarget` shape
(`name`, `description`, `kind`, `location`, `lean_declaration`, `lean_file`),
plus an `autoform_book/` Markdown directory containing book-style descriptions
of each theorem-development target. The target descriptions preserve
`FORMAL_GAP`, required primitives, proof-bank dependencies, and problem-class
metadata, so Autoform-Bot can assess or route the target without mistaking it
for a verified theorem. The release-style `research-system-audit` writes this
export as `autoform_targets/autoform_targets.yaml` and includes it as a gate.

Proof-bank expansion candidates:

```bash
python3 -m ai_statistician.cli proof-bank-expansion-export \
  --run-dir runs/research_benchmark \
  --out runs/proof_bank_expansion
```

This consumes the formal-gap Lean tasks and the formalization target queue, then
reuses the legacy `lemma_proposal.schema.json` and
`theorem_hole_promotion_queue.schema.json` shapes from the old AI-Statistician
repo. The output is deliberately not a proof-bank admission. It writes
`lemma_proposals.jsonl`, a theorem-hole promotion queue, and a Markdown report
that say which primitive should become the next minimal AXLE-verified bridge
lemma, which local Mathlib/StatInference declarations and current proof-bank
obligations support it, and why most current frontier skeletons remain blocked
by `h_frontier_missing_*` placeholders. This gives the formal verifier a
concrete next proof-bank expansion queue while preserving the invariant that
only AXLE `verify_proof` results enter the proof bank.

The JSONL rows expose proof-search routing fields at top level: `primitive`,
`action_class`, `bridge_readiness`, `candidate_declarations`,
`bridge_candidate_obligations`, `source_gap_ids`, and explicit promotion
blockers such as `candidate_statement_has_placeholder_assumption`. These fields
are retrieval/planning evidence only; the row still remains blocked until a
non-placeholder proof body passes AXLE/Lean verification.

RAG collaboration handoff:

```bash
python3 -m ai_statistician.cli rag-collaboration-export \
  --system-audit-manifest runs/current_continuous_mapping_wrappers_queuefix_system_audit/research_system_audit_manifest.json \
  --out runs/current_rag_collaboration_handoff
```

This is the compact interface between this AI Statistician thread and the
separate RAG/prover-search infrastructure work. It packages the active
proof-bank fingerprint, kernel-verified proof count, `lean_rag` dependency-graph
path, retrieval benchmark/ablation evidence, remaining formal primitive queue,
and the top non-composition handoff targets with query hints. It is deliberately
not another search index and not proof evidence. The intended collaboration loop
is: RAG infrastructure improves or replaces the provider, exports its DB path,
schema summary, and retrieval-eval manifest, then AI Statistician reruns
`research-system-audit --lean-rag-db ...` and checks whether retrieval and proof
capacity actually improve.

Standalone retrieval benchmark command:

```bash
python3 -m ai_statistician.cli formal-source-retrieval-benchmark \
  --suite all \
  --lean-rag-db runs/current_status_lean_rag_dependency_graph/stat_inference.sqlite \
  --out runs/formal_source_retrieval_all_benchmark
```

The suite choices are `default`, `external`, and `all`. `default` is the stable
release retrieval gate. `external` covers broader user-intent theorem-family
queries over FormalSLT, lean-rademacher, Lean Machine Learning, BrownianMotion,
KolmogorovExtension, and SciLean. `research-system-audit` now writes all three
manifests so RAG capacity can be tracked without treating retrieval hits as Lean
proof evidence.

Research trace training export:

```bash
python3 -m ai_statistician.cli research-training-export \
  --run-dir runs/research_benchmark \
  --out runs/research_training_export
```

This turns audited research traces into training-data substrates for the
agentic theory lab. It writes SFT JSONL examples for problem formalization,
theory-plan generation, formal-gap routing, and simulation critique, plus coarse
GRPO seed tasks where the simulator pass/fail result becomes a reward label.
The export also writes a legacy-compatible `training_manifest.schema.json`
payload so older AI-Statistician training/evaluation code can consume the same
examples. This is still an exporter, not a trainer: no model checkpoint is
created or registered, and all rows preserve provenance back to the trace that
generated them. `research-system-audit` includes this export as a release gate
so future training work has a stable, audited data source.

Research policy baseline:

```bash
python3 -m ai_statistician.cli research-policy-baseline \
  --train-jsonl runs/research_training_export/research_sft_train.jsonl \
  --validation-jsonl runs/research_training_export/research_sft_validation.jsonl \
  --out runs/research_policy_baseline
```

This no-training baseline retrieves the nearest training trace example for each
validation problem-formalization, theory-plan, formal-gap-routing, or
simulation-critique task. It reports exact completion match, same-task routing,
same-problem-class retrieval, valid-JSON rate, and JSON top-level key F1. The
metric is deliberately modest: it is a floor for future trained research agents
to beat, not a claim that nearest-neighbor memory solves theory development.
`research-system-audit` runs this baseline after `research-training-export`.

Next-iteration queue:

```bash
python3 -m ai_statistician.cli next-iteration-audit \
  --run-dir runs/research_benchmark \
  --out runs/next_iteration_queue
```

This aggregates every per-trace `next_iteration_agenda` item into a run-level
agent work queue. The manifest groups tasks by owner (`formal_verifier`,
`theory_developer`, `algorithm_engineer`, `simulator_agent`, and
`research_coordinator`), trigger, and priority. This is the operational bridge
from trace-level evidence to the next development round: formal-gap items become
Lean-library/proof-bank tasks, failed proofs become proof-repair tasks, and
failed simulations become theory, algorithm, simulator, or Monte Carlo rerun
tasks. `research-system-audit` writes this queue as
`next_iteration_queue/next_iteration_queue_manifest.json`.

Research source inventory:

```bash
python3 -m ai_statistician.cli research-knowledge-audit \
  --out runs/research_knowledge_audit
```

The knowledge audit now includes a lightweight local-source inventory. It checks
that the lab can actually see the AI-for-math paper collection, Mathlib
Probability and MeasureTheory trees, local StatInference workspaces,
lean-stat-learning-theory, the vendored EmpericalProcessLEAN main snapshot in
`legacy_sources/emperical_process_lean/`, the vendored legacy AI-Statistician
source pool in `legacy_sources/ai_statistician/`, the local
`ykzeng-yale/atlas-lean` probability/statistics/analysis/Fourier/functional-
analysis/differential-analysis/projection subtrees, the local
`ykzeng-yale/autoform-bot` harness checkout, and OpenProver. The vendored
Lean/stat files are treated as source pools, not as the active runtime:
EmpericalProcessLEAN contributes current shared probability/asymptotics/
empirical-process foundations, while legacy AI-Statistician contributes
theorem-hole benchmark JSONL, schemas, and proof-training artifacts. Atlas is
used as retrieval evidence for theorem planning/proof-bank expansion, and
AutoformBot is used as a harness integration target for statement extraction,
Lean checking, dependency-graph evaluation, proof-checker wrappers, REPL/LSP
tooling, Lean proof-pattern skill docs, evaluation, and visualization. The
inventory records provenance and default export policy; SFT/GRPO-style training
exports omit external declaration payloads unless
`AI_STATISTICIAN_INCLUDE_EXTERNAL_TRAINING_SOURCES=1` is set for an
owner-authorized local export. The
inventory records
file counts, extension counts, keyword evidence, git commit/remote provenance,
usage policy, and a fingerprint that is also included in research-trace
provenance. This is still a small deterministic
resource index, not a full semantic RAG system, but it prevents the workflow
from claiming to use local formalization resources that are absent.
Trace audit applies the same grounding contract per run: each normalized
problem class must include its primary statistical-method card, at least one
local Lean/stat formal source, and at least one retrieval/search-system source.

Research multi-seed evaluation:

```bash
python3 -m ai_statistician.cli research-eval \
  --question-file examples/research_questions.json \
  --n-seeds 3 \
  --runs 80 \
  --out runs/research_eval
```

This reruns the full open-question benchmark across multiple simulation seeds,
audits every seed-level research trace, and writes
`research_evaluation_manifest.json` with per-question ready rates and
per-procedure metric means/standard deviations. With `--real-lean`, the
Mathlib-backed subclaims are verified through AXLE on every seed run, while
frontier theorem goals remain explicit gaps.

Research capability audit:

```bash
python3 -m ai_statistician.cli research-capability-audit \
  --out runs/research_capability_audit
```

This is the requirement-level audit for the broad AI Statistical Theory Lab
goal. It writes `research_capability_audit_manifest.json` and
`research_capability_audit.md` with rows for intake, problem formalization,
informal theory planning, knowledge retrieval, AXLE-backed proof-bank
subclaims, Lean gap skeletons, vetted algorithms, simulations, structured
simulation adjudication, traces, frontier coverage, and the not-yet-achieved
arbitrary-frontier-theory target. The current scaffold should pass
`all_current_release_requirements_met=true`; the broader research goal
intentionally remains `goal_complete=false`.

Research system audit:

```bash
python3 -m ai_statistician.cli research-system-audit \
  --runs 100 \
  --out runs/research_system_audit
```

The system audit is the preferred single command for evaluating this layer. It
runs proof-bank retrieval, frontier precision audit, research capability audit,
research knowledge-source audit, research algorithm audit, proof verification,
proof-training export, the proof-policy baseline, prover-component audit, the
frontier research benchmark, frontier theory-target grading, the research trace
audit, formal-gap backlog, formalization target queue, formal-gap Lean task
export, formal-source graph, next-iteration queue, and the human-readable
research report, then writes
`research_system_audit_manifest.json` with gates and artifact paths. The
training, baseline, and theory-target gates check
artifact integrity and scoring coverage, not model quality: they make
verifier-positive proof attempts available for future SFT/rejection sampling,
record the no-training proof-memory baseline that trained policies must beat,
quantify how much of the withheld paper-theory target text is recovered, and
check that every simulation contains a deterministic diagnosis routing failures
to the theory developer, algorithm engineer, simulator environment, or a larger
Monte Carlo run instead of leaving metric failures as unstructured text. Trace
audit also checks that every theory plan includes a next-iteration agenda with
owner counts, a stop condition, and semantic coverage of formal gaps, failed
proof obligations, and non-OK simulation diagnoses. The next-iteration queue
gate then checks that those per-trace agendas aggregate into a run-level agent
worklist.
With `--real-lean`, the proof gate and benchmark subclaims use AXLE
`verify_proof`; frontier theorem goals still remain explicit formal gaps unless
they have been added to the proof bank as real obligations.

Research algorithm audit:

```bash
python3 -m ai_statistician.cli research-algorithm-audit \
  --out runs/research_algorithm_audit
```

Research procedures such as `oracle_aipw`, `split_conformal_poly`,
`kaplan_meier_fixed_time`, `median_of_means_mean`,
`neyman_conservative_variance`, `ols_hc1`, `benjamini_hochberg`,
`bernoulli_lr_eprocess`, `spiked_pca`, and `hill_tail_quantile` are
fingerprinted from the Python source that implements the
simulation/evaluation algorithm. Each research trace records the vetted
algorithm ID, version, registry status, and SHA-256 source hash so simulation
diagnostics are tied to implementation provenance.

Research knowledge audit:

```bash
python3 -m ai_statistician.cli research-knowledge-audit \
  --out runs/research_knowledge_audit
```

This validates the problem-aware knowledge layer used in research traces. It
checks that each card points at an existing local source or valid URL, that each
supported problem retrieves its primary statistical method card as the top hit,
and that the trace includes both a local formal source such as Mathlib,
StatInference, EmpiricalProcessLEAN, or lean-stat-learning-theory and a
retrieval/search source such as Lean Finder, Loogle, ReProver, or OpenProver.

Research intake audit:

```bash
python3 -m ai_statistician.cli research-intake-audit \
  --out runs/research_intake_audit
```

The intake audit checks both sides of the paper-style question boundary:
supported examples in `examples/research_questions.json` and
`examples/research_paper_abstracts.md` must normalize into registered research
problem classes, while frontier topics outside the current lab surface in
`examples/research_unsupported_paper_abstracts.md` must route to
`unsupported_frontier_question` instead of receiving invented procedures or
fake formal guarantees. This is also included as a gate in
`research-system-audit`.

Frontier coverage audit:

```bash
python3 -m ai_statistician.cli frontier-coverage-audit \
  --out runs/frontier_coverage_audit
```

This parses `docs/frontier_stat_theory_benchmark.md`, which contains
DOI-backed recent paper-style questions from JASA, Annals of Statistics, JRSSB,
and Biometrika, then runs the deterministic `ProblemFormalizer` on every entry.
The output reports current supported/unsupported coverage by topic and problem
class. The gate only requires that the benchmark parses cleanly; unsupported
rows are expected and represent the research roadmap, not failures.

Frontier precision audit:

```bash
python3 -m ai_statistician.cli frontier-precision-audit \
  --out runs/frontier_precision_audit
```

This validates that every supported frontier classification has direct evidence
in the paper body fields: title, open question, assumptions, or expected
results. It deliberately ignores broad topic labels, so a row under a mixed
topic such as `multiple_testing_conformal_selection` cannot pass merely because
the topic contains useful words. `research-system-audit` includes this as a gate
to keep reported frontier coverage conservative.

Frontier backlog audit:

```bash
python3 -m ai_statistician.cli frontier-backlog-audit \
  --out runs/frontier_backlog_audit
```

This turns unsupported rows in the 60-paper frontier corpus into an explicit
future-theory roadmap instead of leaving them as a raw count. Each unsupported
paper gets a roadmap domain, a missing problem-class name, likely statistical
methods, and required formal primitives. This preserves the honesty boundary:
unsupported topics still do not run through the simulator or proof bank, but
they become auditable library-construction work items.

Frontier smoke benchmark:

```bash
python3 -m ai_statistician.cli frontier-smoke-benchmark \
  --runs 60 \
  --out runs/frontier_smoke_benchmark
```

This selects supported entries from the 60-paper frontier corpus, at most one
per currently supported problem class by default, and runs the full research
workflow on those real paper-style questions. The output includes the selected
paper IDs, the generated benchmark traces, trace audit, and formal-gap backlog.
With `--real-lean`, the Mathlib-backed subclaims are verified through AXLE.
This is a smoke test of executable paper-style coverage, distinct from the
coverage audit's broader classification count.

The smoke benchmark also writes `frontier_theory_target_audit/`. This audit
uses the withheld `expected_theoretical_results` only after trace generation and
computes token-overlap coverage between the generated theorem/procedure plan
and the paper's expected theory targets. The gate checks that every selected
trace was scored against available gold targets; the coverage rate is
diagnostic, not a claim that the current system has reconstructed or proved the
full frontier paper theorem.

The same grader is available directly:

```bash
python3 -m ai_statistician.cli frontier-theory-target-audit \
  --run-dir runs/frontier_smoke_benchmark/research_benchmark \
  --out runs/frontier_theory_target_audit
```

The current benchmark covers fourteen frontier-style but controlled problems:

- semiparametric ATE estimation with an oracle AIPW estimator;
- split conformal prediction with distribution-free marginal coverage;
- right-censored survival inference with Kaplan-Meier survival estimation;
- robust mean inference with a median-of-means estimator;
- differentially private inference with a Gaussian-mechanism clipped-mean estimator;
- nonparametric regression inference with a polynomial-sieve pointwise estimator;
- Bayesian predictive-distribution-to-prior calibration with a normal-conjugate posterior estimator;
- measurement-bias-adjusted educational assessment ranking with country/item bias correction;
- design-based conservative variance inference for randomized experiments;
- heteroskedastic regression inference with HC1 robust standard errors.
- large-scale multiple testing with Benjamini-Hochberg FDR control.
- sequential anytime-valid Bernoulli testing with a likelihood-ratio e-process.
- high-dimensional PCA signal-subspace inference under a spiked covariance model.
- extreme-value tail-index and high-quantile inference with Hill/Weissman estimators.

This layer is intentionally honest. It does not claim to prove a full JASA/AOAS
paper theorem in Lean. It proves the Mathlib-backed subclaims available in the
local proof bank, for example indicator expectations, probability normalization,
expectation linearity, variance nonnegativity, finite-sample mean unbiasedness,
sieve-relevant finite-sample Chebyshev bounds, contrast variance decomposition,
and a noised-estimator Chebyshev bridge. The latter proves that independent
mean-zero additive noise preserves unbiasedness, adds variance, and gives an
error tail bound using `Var(X)+Var(Z)`, while the contrast-variance bridge
proves `Var(X-Y)=Var(X)-2Cov(X,Y)+Var(Y)` for L2 estimators and directly
supports ATE and design-based difference-in-means traces. The hard theory pieces such
as AIPW double robustness, asymptotic normality, conformal rank coverage,
sandwich covariance consistency, DP Gaussian-mechanism calibration, privacy
composition, predictive-prior coherence, posterior credible-interval
calibration, IRT measurement-invariance identifiability, rank-functional
uncertainty theory, high-dimensional PCA perturbation bounds, and
regular-variation order-statistic theory are recorded as `FORMAL_GAP` with the missing
formalization work spelled out. Each gap records machine-readable required
primitives such as `conditional_expectation`, `iid_empirical_mean_clt`,
`epsilon_delta_dp_definition`, `davis_kahan_sin_theta`, or `regular_variation`,
and each gap also gets a Lean-facing skeleton under `formal_gaps/*.lean`.
Those skeletons deliberately use placeholder assumptions
named `h_frontier_missing_*`, so they are roadmap artifacts, not verified
theorem claims. The simulator then checks whether the proposed procedure behaves
as expected in the DGP environment, so each trace separates:

- what is already proved in Lean/AXLE,
- which AXLE-verified proof obligations support each theorem goal,
- what has a Lean theorem skeleton but remains a formal gap,
- what is empirically supported by simulation,
- what remains a research-library backlog item.

The theorem-goal support map is deliberately partial. For instance, it can say
that the AIPW double-robustness goal is supported by the proved AIPW expectation
decomposition, or that the private mean error-decomposition goal is supported by
proved additive-noise unbiasedness, variance, and Chebyshev obligations. It
still leaves the unproved conditional-expectation, empirical-process, privacy,
or asymptotic primitives in `FORMAL_GAP`.

The trace audit enforces this chain: every theorem goal listed by a candidate
procedure must appear in the trace-level theorem-goal registry and must be
covered by either a verified Lean subclaim or an exported formal-gap skeleton.
This prevents procedures from carrying undocumented theorem promises.

## What Is Actually Proved

The system includes estimator-level Lean obligations that AXLE has verified:

- `constant_estimator_unbiased`: expectation of a constant estimator is the
  target constant.
- `constant_estimator_variance_zero`: variance of a constant estimator is zero.
- `mean2_estimator_expectation`: expectation of a two-variable mean estimator is
  the mean of expectations.
- `mean2_estimator_unbiased`: if two integrable component estimators are each
  unbiased for the same target, their two-variable average is unbiased for that
  target.
- `difference_estimator_unbiased`: if two integrable estimators are unbiased
  for targets `thetaX` and `thetaY`, their difference is unbiased for the
  contrast `thetaX-thetaY`; this is the reusable expectation bridge for
  difference-in-means, treatment-effect, and contrast estimators.
- `difference_estimator_variance_decompose`: for L2 estimators `X` and `Y`,
  the contrast estimator `X-Y` has variance
  `Var(X)-2Cov(X,Y)+Var(Y)`, using Mathlib's `variance_fun_sub`; this is the
  reusable second-moment bridge for ATE contrasts and design-based variance
  decompositions. It does not prove randomization, covariance estimation, or
  asymptotic normality.
- `randomization_variance_decomposition_bridge`: the same `variance_fun_sub`
  second-moment identity exposed under the missing design-based primitive name
  for L2 potential-outcome or estimator functions `Y1` and `Y0`. This improves
  primitive routing for `randomization_variance_decomposition`, but still does
  not prove assignment uniformity or the full finite-population randomization
  variance theorem.
- `affine_estimator_expectation`: for an integrable estimator `X`, the affine
  shrinkage estimator `a*X+b` has expectation `a*E[X]+b`, supporting posterior
  mean and prior-shrinkage traces.
- `affine_estimator_variance`: for an L2 estimator `X`, the affine shrinkage
  estimator `a*X+b` has variance `a^2 Var(X)`, supporting posterior,
  linear-smoother, and bias-adjusted ranking SE traces.
- `mean2_estimator_variance_indep`: for independent L2 component estimators,
  the variance of their average `(X+Y)/2` is `(Var(X)+Var(Y))/4`.
- `estimator_error_chebyshev`: if an estimator has finite second moment and
  mean `theta`, its absolute-error tail probability is bounded by
  `Var(X) / c^2`.
- `block_estimator_chebyshev_bound`: the same Chebyshev tail-control pattern
  exposed as a block-estimator bridge for robust median-of-means traces. This
  verifies the block failure probability ingredient and deliberately leaves the
  binomial median amplification theorem as a separate formalization target.
- `chebyshev_block_failure_bound_bridge`: a domain-named robust-mean wrapper
  around the same Chebyshev block-estimator inequality. It closes the named
  primitive `chebyshev_block_failure_bound` for queue/routing purposes, without
  proving independent block construction or a sharp MoM concentration theorem.
- `median_of_means_failure_union_control`: a finite block-event union bridge
  for robust mean traces. If the MoM failure event is contained in the finite
  union of bad block events, and each bad block has a local error budget, then
  the MoM failure probability is controlled by the sum of those budgets. This
  bridges block-level Chebyshev control toward the MoM theorem skeleton without
  claiming the binomial majority tail or sharp sub-Gaussian deviation theorem.
- `median_of_means_deviation_bridge`: a domain-named wrapper for the missing
  primitive `median_of_means_deviation`, reusing the finite bad-block union
  skeleton. It improves formalization-target routing while preserving the
  binomial median tail as an explicit formal gap.
- `neyman_variance_conservative_algebra`: a design-based finite-population
  variance bridge. If exact randomization variance decomposes as an observable
  Neyman bound minus a nonnegative treatment-effect variance term, then the
  observable bound is conservative. This verifies the core algebraic
  conservativeness step while leaving complete randomization and the
  finite-population randomization variance derivation as formal gaps.
- `finite_population_ate_mean_difference`: a deterministic potential-outcome
  target bridge. For a finite population, the mean of unit-level effects
  `Y(1)-Y(0)` equals the treated potential-outcome mean minus the control
  potential-outcome mean. This formalizes finite-population ATE algebra while
  leaving assignment distribution and randomization-unbiasedness proofs as
  separate formalization targets.
- `complete_randomization_uniform_assignment_mass`: a finite uniform-assignment
  distribution bridge. For any finite nonempty assignment space, Mathlib's
  uniform PMF assigns each assignment mass `1/card`. This upgrades the
  complete-randomization distribution primitive while leaving fixed-treated-count
  combinatorics and design-based covariance calculations as formal gaps.
- `uniform_rank_pmf_mass`: a finite uniform-rank distribution bridge. For a
  finite nonempty rank space `Fin n`, Mathlib's uniform PMF assigns every rank
  mass `1/n`. This upgrades conformal rank-uniformity traces with a verified PMF
  primitive while leaving the exchangeability-to-uniform-rank and
  order-statistic conformal coverage theorems as formal gaps.
- `exchangeable_scores_uniform_rank_bridge`: a domain-named split-conformal
  wrapper for the missing `exchangeable_scores` primitive. It verifies the
  finite uniform-rank PMF ingredient after score exchangeability has been
  reduced to a uniform rank; it does not prove that exchangeability reduction.
- `bh_threshold_grid_mono`: a deterministic Benjamini-Hochberg threshold-grid
  bridge. For nonnegative nominal FDR level `q`, the grid `q*k/m` is monotone in
  the rank index `k`. This upgrades ordered-p-value and BH step-up fixed-point
  traces with a verified algebraic primitive while leaving BH self-consistency
  and FDR control as formal gaps.
- `bh_threshold_fixed_point_bridge`: the same deterministic threshold-grid
  monotonicity exposed under the `bh_threshold_fixed_point` primitive name. It
  verifies the algebraic ingredient used by BH fixed-point traces, while still
  leaving existence of a data-adaptive fixed point, ordered p-value
  self-consistency, power, and FDR control as formal gaps.
- `potential_outcome_observed_consistency`: a deterministic causal-inference
  bridge. For binary treatment assignment, the observed outcome equals `Y(1)`
  on treated units and `Y(0)` on control units by definition. This upgrades the
  potential-outcome consistency primitive while leaving conditional
  exchangeability, positivity, and ATE identification as formal gaps.
- `propensity_score_ne_zero_of_lower_bound`: a causal positivity bridge. A
  propensity score bounded below by a strictly positive constant is nonzero,
  which gives inverse-propensity and AIPW traces a verified denominator-safety
  primitive while leaving overlap, conditional exchangeability, and
  identification as formal gaps.
- `propensity_weight_mul_cancel_of_lower_bound`: the corresponding
  inverse-weight algebra bridge. Under the same strict positive lower bound,
  the proof bank now verifies `p⁻¹ * p = 1`, so
  `propensity_weight_identity` has a direct Lean bridge while conditional
  exchangeability, nuisance correctness, identification, and double robustness
  remain formal gaps.
- `mean2_estimator_chebyshev_indep`: combines unbiasedness, L2 closure,
  independence variance additivity, variance scaling, and Chebyshev to bound
  the absolute-error probability of `(X+Y)/2` by
  `((Var(X)+Var(Y))/4) / c^2`.
  This obligation records dependency edges to the expectation, variance, and
  Chebyshev proof obligations; release audits check that the dependency graph is
  known and verified.
- `finite_sample_mean_unbiased`: for any nonzero finite sample size `n`, if
  each component estimator indexed by `Fin n` is integrable and unbiased for
  `theta`, the arithmetic sample mean estimator is unbiased for `theta`.
- `finite_sample_mean_variance_indep`: for pairwise independent L2 component
  estimators indexed by `Fin n`, the arithmetic sample mean has variance equal
  to the sum of component variances divided by `n^2`; this uses Mathlib's
  `IndepFun.variance_sum` finite-sum variance theorem.
- `finite_sample_mean_chebyshev_indep`: combines finite-sample mean
  unbiasedness, the pairwise-independent variance identity, and Chebyshev's
  inequality to bound the absolute-error probability of the arithmetic mean by
  the proved finite-sample variance divided by `c^2`.
- `event_indicator_expectation`: expectation of an event indicator estimator is
  the event mass.
- `finite_event_indicator_mean_unbiased`: for any nonzero finite sample size
  `n`, if every measurable event indexed by `Fin n` has common probability `p`,
  the arithmetic mean of its event indicators is unbiased for `p`.
- `finite_union_bound`: a Bonferroni-style finite union bound
  `μ (⋃ i∈I, A i) ≤ ∑ i∈I, μ(A i)` proved directly from Mathlib's
  `measure_biUnion_finset_le`, supporting conformal coverage counting,
  BH/FDR error decompositions, and finite-horizon anytime-valid error control.
- `finite_null_pvalue_no_false_rejection_probability`: a finite valid-null
  p-value bridge. If each true null p-value satisfies
  `P(p_i <= tau_i) <= tau_i` at its chosen threshold and the thresholds sum to
  `α_total`, then the no-false-rejection event has probability at least
  `1-α_total`. This supports p-value validity and BH/FDR skeleton traces while
  leaving step-up self-consistency and FDR decomposition as formal gaps.
- `leave_one_out_fdr_decomposition_bridge`: the same finite p-value
  no-false-rejection bound exposed under the `leave_one_out_fdr_decomposition`
  primitive name. It verifies the finite union/decomposition ingredient used by
  BH leave-one-out arguments, while still leaving ordered p-values, BH
  self-consistency, independence conditioning, and full FDR control as formal
  gaps.
- `finite_conformal_rank_coverage_counting`: a split-conformal finite-rank
  counting bridge. If each bad-rank event has a local probability budget and
  those budgets sum to `α_total`, then the complement of the bad-rank event has
  probability at least `1-α_total`. This is the verified finite-sample counting
  ingredient for conformal coverage traces, while exchangeability, rank
  uniformity, and the order-statistic quantile theorem remain explicit formal
  gaps.
- `order_statistic_quantile_rule_bridge`: a domain-named split-conformal
  wrapper for the missing `order_statistic_quantile_rule` primitive. It reuses
  the finite bad-rank union/complement algebra to verify the coverage ingredient
  associated with an order-statistic bad-rank set, without proving the score
  exchangeability or quantile construction theorem.
- `finite_family_absolute_error_union_control`: a finite-family estimator
  bridge: if each absolute-error event
  `{ω | radius i ≤ |X_i ω-theta_i|}` has local error budget `α_i`, then the
  probability that any estimator exceeds its radius is bounded by
  `∑ i∈I α_i`.
- `finite_family_absolute_error_simultaneous_coverage`: composes that
  absolute-error union bridge with complement-event probability algebra to show
  that the simultaneous no-error event has coverage at least `1-α_total`
  whenever the local budgets sum to `α_total`. This is a verified finite-sample
  bridge for simultaneous confidence bands and ranking uncertainty; it still
  does not prove CLT calibration or standard-error consistency.
- `top_rank_correct_of_uniform_error_separation`: a deterministic ranking
  bridge: if one target is separated from every competitor by more than twice a
  common error radius, and all estimates are within that radius of their
  targets, then the separated item is ranked top by the estimates. This turns
  simultaneous absolute-error control into finite-sample top-rank reliability,
  without claiming full rank-functional asymptotics.
- `finite_horizon_type1_union_control`: a sequential finite-horizon bridge:
  if each monitored rejection event `A_i` has mass at most `α_i`, then the
  probability of rejecting at some monitored time is at most `∑ i∈I, α_i`.
  This closes the finite-horizon union-allocation ingredient for sequential
  traces without claiming Ville's inequality or full anytime-valid
  supermartingale control.
- `selected_bad_event_probability_le_finite_union_budget`: a post-selection
  finite-union bridge. If a data-dependent selector always picks from a finite
  candidate set, then the selected bad event is contained in the finite union
  of all candidate bad events and is controlled by the same Bonferroni budget.
  This supports selected intervals, model-confidence sets, adaptive
  active-learning choices, and post-detection changepoint traces while leaving
  selective CLTs and bootstrap validity as explicit formal gaps.
- `selected_good_event_coverage_of_finite_union_budget`: the coverage-form
  companion to the selected bad-event bridge. Under the same finite-candidate
  selector and Bonferroni-budget assumptions, plus measurability of the selected
  bad event, it proves the selected-good event has probability at least
  `1-α_total`. This is the verified finite-sample ingredient for selected
  interval coverage before any selective asymptotic theory is claimed.
- `sequential_elimination_rule_finite_union_control`: a sequential
  model-confidence bridge. If a data-dependent elimination rule selects one
  candidate from a finite active set and each candidate bad-elimination event
  has a local error budget, then the selected elimination bad event is bounded
  by the finite union budget. This is the verified finite-sample ingredient for
  sequential elimination traces, not a proof of bootstrap validity or full
  selective inference.
- `finite_horizon_evalue_markov_type1_control`: a finite-horizon e-value
  exceedance bridge:
  measurable ENNReal coordinates `E_i` with Markov tail budgets
  `(∫⁻ E_i)/u_i ≤ α_i` satisfy
  `μ (⋃ i∈I, {ω | u_i ≤ E_i ω}) ≤ α_total` whenever
  `∑ i∈I α_i ≤ α_total`. It composes Mathlib's Markov inequality with a
  finite union allocation and is the verified bridge now attached to
  `eprocess_type1_control`, `nonnegative_supermartingale`, and
  `ville_inequality` formalization primitives. It is not a proof of optional
  stopping or Ville's inequality.
- `filtration_mono_measurable_set`: filtration monotonicity for event
  measurability:
  `MeasurableSet[ℱ i] A -> i ≤ j -> MeasurableSet[ℱ j] A`, proved from
  Mathlib's `Filtration.mono`. It is the verified bridge now attached to the
  `filtration` primitive and a candidate bridge for stopping-time/Ville
  skeletons. It is not a proof of optional stopping or Ville's inequality.
- `stopping_time_le_event_measurable`: the defining stopping-time event
  measurability theorem
  `IsStoppingTime ℱ τ -> MeasurableSet[ℱ i] {ω | τ ω ≤ i}`, wrapped around
  Mathlib's `IsStoppingTime.measurableSet_le`. It is a verified primitive for
  stopped-process, optional-stopping, and e-process theorem skeletons, but it
  does not prove optional-stopping validity or Ville's inequality.
- `submartingale_expected_stopped_value_mono`: the forward optional-stopping
  expectation monotonicity theorem for bounded stopping times:
  `Submartingale f 𝒢 μ -> IsStoppingTime 𝒢 τ -> IsStoppingTime 𝒢 π ->
  τ ≤ π -> (∀ ω, π ω ≤ N) -> μ[stoppedValue f τ] ≤ μ[stoppedValue f π]`,
  wrapped around Mathlib's `Submartingale.expected_stoppedValue_mono`. This is
  now a verified bridge for optional-stopping theorem skeletons, but it is not
  an e-process construction, Ville inequality, or nonnegative-supermartingale
  maximal inequality.
- `submartingale_stopped_process`: stopped-process closure for real-valued
  submartingales:
  `Submartingale f 𝒢 μ -> IsStoppingTime 𝒢 τ ->
  Submartingale (stoppedProcess f τ) 𝒢 μ`, wrapped around Mathlib's
  `Submartingale.stoppedProcess`. This is a verified bridge for stopped-process
  and nonnegative-supermartingale skeletons.
- `supermartingale_expected_stopped_value_antimono`: bounded optional-stopping
  expectation monotonicity for real-valued supermartingales:
  if `τ ≤ π`, then `μ[stoppedValue f π] ≤ μ[stoppedValue f τ]`. It reuses
  Mathlib's `Supermartingale.setIntegral_le` and stopped-value decomposition,
  giving e-process/Ville skeletons a direct expectation-budget theorem.
- `submartingale_doob_maximal_ineq`: finite-horizon Doob maximal inequality for
  nonnegative real-valued submartingales, wrapped around Mathlib's
  `maximal_ineq`. This gives the Ville/e-process route a verified maximal
  inequality bridge over running suprema while still leaving full e-process
  construction and anytime type-I control as formal gaps.
- `submartingale_doob_maximal_budget`: a budgeted corollary of the same Doob
  inequality:
  if `ENNReal.ofReal (∫_{sup f ≥ ε} f_n dμ) ≤ ε * α`, then
  `ε * μ {sup f ≥ ε} ≤ ε * α`. This is the finite-horizon maximal-tail budget
  step needed by Ville-style type-I arguments.
- `submartingale_doob_maximal_probability_bound`: the ENNReal cancellation
  corollary after the budgeted Doob step:
  if `ε ≠ 0` and `ENNReal.ofReal (∫_{sup f ≥ ε} f_n dμ) ≤ ε * α`, then
  `μ {sup f ≥ ε} ≤ α`. It uses `ENNReal.mul_le_mul_iff_right`, so the
  remaining Ville/e-process gaps are now the e-process construction and
  terminal-budget proof, not the post-Doob algebra.
- `submartingale_ae_tendsto_limit_process`: almost-everywhere convergence of
  an L1-bounded real-valued submartingale to Mathlib's filtration
  `limitProcess`, wrapped around `Submartingale.ae_tendsto_limitProcess`.
  This is now attached to survival/Kaplan-Meier, Nelson-Aalen, backward-
  martingale, and sequential theorem skeletons as a real convergence bridge;
  it is not a martingale CLT or product-limit delta-method proof.
- `submartingale_l1_tendsto_limit_process`: L1 convergence of a uniformly
  integrable real-valued submartingale to Mathlib's filtration `limitProcess`,
  wrapped around `Submartingale.tendsto_eLpNorm_one_limitProcess`. This gives
  survival/Kaplan-Meier, Nelson-Aalen, and martingale-convergence theorem
  skeletons a stronger norm-convergence bridge while still leaving martingale
  CLTs, Greenwood consistency, and product-limit delta-method arguments as
  formal gaps.
- `martingale_ae_eq_condexp_limit_process`: representation part of the L1
  martingale convergence theorem. A uniformly integrable real martingale
  satisfies `f n =ᵐ μ[limitProcess f | 𝒢 n]`, wrapped around Mathlib's
  `Martingale.ae_eq_condExp_limitProcess`. This gives conditional-expectation,
  martingale-definition, survival/Kaplan-Meier, and Nelson-Aalen theorem
  skeletons a direct limit-process conditional-expectation bridge while still
  leaving product-process martingale construction and martingale CLTs as formal
  gaps.
- `integrable_ae_tendsto_condexp_filtration`: upward martingale convergence
  for conditional expectations in the almost-everywhere sense. If an integrable
  real function is measurable with respect to the terminal sigma-field
  `⨆ n, 𝒢 n`, then `μ[g | 𝒢 n]` converges almost everywhere to `g`, wrapped
  around Mathlib's `Integrable.tendsto_ae_condExp`.
- `integrable_l1_tendsto_condexp_filtration`: the matching L1/eLpNorm upward
  theorem for conditional expectations, wrapped around
  `Integrable.tendsto_eLpNorm_condExp`. It gives conditional-expectation,
  iterated-expectation, exogeneity, and martingale-definition theorem skeletons
  a direct convergence bridge while preserving model-specific identification
  and empirical-process remainder arguments as formal gaps.
- `event_probability_mono`: event monotonicity `A ⊆ B -> μ(A) ≤ μ(B)`,
  proved directly from Mathlib's `measure_mono`; this is the reusable
  bad-event-containment step used before applying union or tail bounds.
- `independent_event_inter_probability`: event-independence algebra
  `IndepSet A B μ -> μ(A ∩ B) = μ(A) * μ(B)`, proved directly from
  Mathlib's `IndepSet.measure_inter_eq_mul`; this supports independent
  null-p-value decompositions and sequential likelihood-ratio product
  arguments.
- `independent_null_event_family_inter_probability`: finite-family event
  independence algebra
  `iIndepSet A μ -> μ (⋂ i ∈ I, A i) = ∏ i ∈ I, μ (A i)`, proved directly
  from Mathlib's `iIndepSet.meas_biInter`; this is the verified bridge now
  attached to the BH/FDR `independent_null_pvalues` primitive. It proves the
  product-form null-event probability ingredient only, not p-value validity,
  ordering, or the full BH step-up FDR theorem.
- `independent_null_event_family_compl_inter_probability`: finite-family
  complement-event independence algebra
  `iIndepSet A μ -> μ (⋂ i ∈ I, (A i)ᶜ) = ∏ i ∈ I, μ (A i)ᶜ`. This uses
  `iIndepSet_iff` plus measurability of complements in the generated
  singleton sigma-algebras, giving BH/FDR and familywise-error traces a
  verified "no false null event" product bridge while preserving the full BH
  theorem as a formal gap.
- `independent_null_pvalues_bridge`: the same complement-product independence
  algebra exposed under the `independent_null_pvalues` primitive name for
  finite true-null rejection events. It verifies the independence ingredient
  used by FDR leave-one-out arguments, while still leaving p-value validity,
  ordering, self-consistency, and BH FDR control as formal gaps.
- `finite_null_family_no_false_rejection_probability`: a finite null-family
  familywise-error bridge. If every true-null rejection event has local budget
  `α_i` and the budgets sum to `α_total`, then the probability of no false
  rejection is at least `1-α_total`. This gives multiple-testing traces a
  verified no-false-rejection coverage ingredient while still leaving the
  ordered-p-value, BH self-consistency, and leave-one-out FDR arguments as
  explicit formal gaps.
- `first_borel_cantelli_limsup_zero`: the first Borel-Cantelli repeated-event
  control lemma `sum μ(A_n) < ∞ -> μ(limsup A_n)=0`, wrapped around Mathlib's
  `MeasureTheory.measure_limsup_atTop_eq_zero`; this supports convergence,
  rare repeated tail events, and sequential monitoring formal gaps.
- `second_borel_cantelli_limsup_one`: the independent-event recurrence
  counterpart `iIndepSet A μ -> sum μ(A_n)=∞ -> μ(limsup A_n)=1`, wrapped
  around Mathlib's `ProbabilityTheory.measure_limsup_eq_one`; this supports
  extreme-tail recurrence and infinite-exceedance arguments.
- `adapted_hitting_after_is_stopping_time`: a discrete adapted-process hitting
  time is a stopping time, wrapped around Mathlib's
  `Adapted.isStoppingTime_hittingAfter`; this is a verified primitive for
  optional-stopping/e-process theorem skeletons.
- `event_indicator_product_integral_eq_inter`: product-of-event-indicators
  algebra for sequential likelihood-ratio traces. For measurable events `A`
  and `B`, the proof bank verifies
  `∫ 1_A * 1_B dμ = μ.real (A ∩ B)`, giving `adapted_product_process`,
  `bernoulli_likelihood_ratio`, and `conditional_expectation_product_step`
  direct bridge candidates while preserving the full likelihood-ratio martingale
  theorem as a formal gap.
- `independent_event_indicator_product_lintegral_eq_mul`: independence-aware
  product-indicator algebra for sequential Bernoulli/product-process traces.
  For independent measurable events `A` and `B`, the proof bank verifies
  `∫⁻ 1_A * 1_B dμ = μ A * μ B`, giving
  `independent_bernoulli_sequence`, `adapted_product_process`,
  `bernoulli_likelihood_ratio`, `conditional_expectation_product_step`, and
  `martingale_definition` a direct factorization bridge while preserving the
  full conditional-expectation and likelihood-ratio martingale theorem as a
  formal gap.
- `independent_event_indicator_condExp_filtration_eq_prob`: a direct
  conditional-expectation bridge for independent Bernoulli/event sequences.
  For an independent sequence of measurable events, the proof bank verifies
  `μ[1_{s_j} | filtrationOfSet s i] =ᵐ μ.real (s_j)` whenever `i < j`, using
  Mathlib's Borel-Cantelli conditional-expectation lemma. This gives
  `conditional_expectation_product_step`, `independent_bernoulli_sequence`,
  `adapted_product_process`, `bernoulli_likelihood_ratio`, and
  `martingale_definition` a stronger route toward the product-process
  martingale proof, while still leaving the full conditional-expectation
  preservation theorem as a formal gap.
- `independent_real_condExp_natural_eq_mean`: a real-valued sequence version of
  the same conditional-expectation pattern. For an independent real-valued
  stochastic sequence, the proof bank verifies
  `μ[X_j | Filtration.natural X i] =ᵐ μ[X_j]` for `i < j`, using Mathlib's
  `iIndepFun.condExp_natural_ae_eq_of_lt`. This now bridges
  `sample_moment_lln`, `iid_empirical_mean_clt`,
  `exogeneity_moment_condition`, `conditional_expectation`, and
  `martingale_definition` to a kernel-checked independence/filtration theorem,
  while still leaving LLN and full asymptotic-normality proofs as
  formal gaps.
- `iid_real_clt_tendsto_distribution`: the first registered full asymptotic
  limit theorem bridge in the proof bank. It wraps Mathlib's one-dimensional
  iid real central limit theorem
  `tendstoInDistribution_inv_sqrt_mul_sum_sub`, verifying convergence in
  distribution of the centered sqrt(n)-scaled partial sum to a Gaussian law.
  This gives `iid_empirical_mean_clt`, `multivariate_score_clt`,
  `wald_interval_slutsky`, and `influence_function_variance` a kernel-checked
  CLT starting point while still leaving multivariate score CLTs, sandwich
  variance consistency, and estimator-specific asymptotic normality as
  formal gaps.
- `tendsto_in_distribution_continuous_mapping`: the Mathlib continuous mapping
  theorem for convergence in distribution. It wraps
  `TendstoInDistribution.continuous_comp`, giving delta-method-style and
  transform-theorem skeletons a kernel-checked transport step while leaving
  differentiability and model-specific linearization as formal gaps.
- `slutsky_add_negligible_zero_real`: the real-valued Slutsky addition bridge.
  It wraps `TendstoInDistribution.add_of_tendstoInMeasure_const`, proving that
  adding a real remainder converging to zero in probability preserves the
  distributional limit. It is now linked to Wald, influence-function, AIPW, and
  heteroskedastic-regression theorem plans, but it still assumes the negligible
  remainder premise rather than proving an empirical-process bound.
- `aipw_score_expectation_decompose`: expectation of an AIPW-style contrast plus
  augmentation score decomposes by linearity.
- `aipw_score_expectation_target_of_aug_cancel`: if the contrast term has
  expectation `psi` and treated/control augmentation expectations cancel, then
  the full AIPW-style score also has expectation `psi`. This is the verified
  algebraic bridge attached to `nuisance_correctness_cases`; it is not a proof
  of conditional expectation residual identities or semiparametric double
  robustness.
- `conditional_mean_residual_zero_of_mean_eq`: if an integrable real outcome
  has mean `m`, then the centered residual `Y - m` has mean zero. This is the
  ordinary centered-mean fallback for residual moment arguments.
- `condexp_integral_eq_integral_real`: the integral of a real conditional
  expectation equals the original integral. This is the Mathlib
  `integral_condExp` bridge now attached to `conditional_expectation`,
  `iterated_expectation`, and exogeneity theorem skeletons; it still assumes
  the conditioning sigma-field setup rather than proving model assumptions.
- `condexp_tower_of_sub_sigma_real`: the tower property for real conditional
  expectations over nested sigma-fields. This wraps Mathlib's
  `condExp_condExp_of_le` and gives causal-identification, filtration,
  martingale, and iterated-expectation theorem plans a direct kernel-verified
  bridge for `E[E[X|m2]|m1] = E[X|m1]`; it still assumes the nested
  sigma-field hypotheses rather than deriving model-specific exchangeability.
- `conditional_mean_residual_zero_of_condExp_ae_eq`: if a conditional
  expectation given a score sigma-field equals a supplied score-space version
  almost everywhere, then the centered residual has population integral zero.
  This is the direct finite bridge now attached to
  `conditional_mean_residual_zero` and `exogeneity_moment_condition`; it proves
  the residual-zero consequence of a conditional-expectation equality while
  still assuming that equality as a premise.
- `aipw_score_expectation_target_of_zero_aug`: if the contrast term has
  expectation `psi` and both augmentation residual terms have mean zero, then
  the AIPW-style score has expectation `psi`. This is the direct finite bridge
  from future conditional-mean-residual-zero lemmas to the double-robustness
  theorem skeleton.
- `aipw_score_integrable_of_components`: if the contrast, treated
  augmentation, and control augmentation terms are integrable, then the full
  AIPW-style score is integrable. This is the verified bridge now attached to
  `integrability_of_score_terms`; it is an integrability side-condition theorem,
  not a nuisance-rate or asymptotic-normality result.
- `variance_nonneg`: variance is nonnegative.
- `variance_indep_add`: variance adds for independent L2 random variables.

These are deliberately chosen because Mathlib already contains the needed
measure/probability facts. The system now includes a full one-dimensional iid
real CLT bridge, but it still does not claim multivariate score CLTs, MLE
consistency, semiparametric efficiency, or problem-specific asymptotic
normality end to end.

## Existing Code Reuse

The package integrates existing systems where appropriate:

- `Preliminary Attempt/` remains archived as the research prototype and eval
  history.
- `OpenProver` is used opportunistically for Lean-style tokenization in
  retrieval if `/Users/yukang/Documents/OpenProver/src` or `OPENPROVER_SRC`
  exists.
- Loogle integration is exposed as a small optional retriever class. It is not
  required for the default offline run.
- AXLE is the remote proof-verification backend for `--real-lean`; local
  `lake env lean` kernel checking is available through `--local-lean`.
- The local formal-source index performs declaration-level retrieval with
  theorem compression features: binder counts, premise heads, conclusion head,
  left/right equality heads, and major symbols. This is the local-first
  counterpart to Loogle/Lean Finder style premise selection and avoids passing
  thousands of irrelevant lemmas to the LLM.
- `formal-source-audit` persists that declaration corpus as
  `formal_source_index.sqlite` using SQLite FTS, giving a cheap local
  candidate-generation pass before Lean-shape reranking and AXLE proof
  attempts.
- `formal-source-graph-audit` adds a graph-style retrieval layer over the same
  declarations by connecting Lean declarations to compressed theorem symbols.
  It expands formal-gap queries through nearby Mathlib/StatInference
  declarations with shared heads such as `variance`, `IndepFun`, `Rademacher`,
  `Hajek`, or `ConditionalExpectation`.
- The default persisted research benchmark backend now fuses those two paths:
  `sqlite_fts_shape_graph_hybrid` first asks the SQLite FTS/shape index for
  bounded candidates, then expands them through the declaration-symbol graph
  and merges the two rankings. This keeps runtime local/reproducible while
  moving formal-gap grounding closer to the provider-fusion architecture used
  by Loogle/Lean Finder/ReProver-style premise selection.
- The backend can now fuse the shared `EmpericalProcessLEAN/lean_rag`
  dependency graph as a third provider. The standard local DB
  `runs/current_status_lean_rag_dependency_graph/stat_inference.sqlite` is
  auto-discovered when present; pass `--lean-rag-db path/to/stat_inference.sqlite`
  or set `AI_STATISTICIAN_LEAN_RAG_DB` only to override that path. This adapter
  reuses the other machine's source-derived declaration graph:
  statement/proof/mixed references, fan-in/fan-out, `has_sorry`, and FTS over
  signatures/proofs. It treats every hit as a premise suggestion that must be
  checked by the local Lean kernel.
- The system audit also records the shared `lean_rag` package contract through
  `ai-statistician lean-rag-package-audit` and the
  `--lean-rag-package-root` option. This reads the package knowledgebase rather
  than vendoring generated DBs: `source_registry.json` supplies trust policy,
  `seed_queries.jsonl` supplies reusable Durrett/Chewi/Vaart retrieval recipes,
  and the shared graph manifest reports indexed/dirty/failed checkouts when it
  exists. This gives monitors and side proof chats a cheap way to confirm that
  they are using the current shared RAG infrastructure.
- The source inventory now also tracks the local LeanSearchClient checkout
  (`#leansearch`, `#loogle`, and state-search syntax) and the local LeanDojo-v2
  checkout (repository tracing, proof-state datasets, retrieval-augmented
  proving, SFT/GRPO, and LeanProgress-style value models). These are integration
  targets, not mandatory runtime dependencies for the offline release gate.
- The source inventory and formal-source index now track a shallow local
  `ykzeng-yale/atlas-lean` mirror, with upstream-compatible fallback. The search database indexes its focused
  probability, high-dimensional statistics, probabilistic-methods, real
  analysis, Fourier analysis, functional analysis, differential analysis, and
  projection-theory subtrees. Default source audits include Atlas-specific
  retrieval queries for sub-Gaussian MGF bounds, probability limit theory,
  characteristic-function weak convergence, Hilbert/projection identities,
  Sobolev/Taylor-style analysis, and geometric projection lemmas.
- The source inventory also tracks a shallow local
  `ykzeng-yale/autoform-bot` mirror, with upstream-compatible fallback. `autoform_harness` records reusable
  statement-extraction, multi-agent formalization, Lean-checking,
  dependency-graph evaluation, proof-checker, REPL/native-LSP, Lean skill-doc,
  evaluation, and visualizer entrypoints. This is an integration adapter, not a
  vendored training dataset. `autoform-harness-audit` exposes that readiness
  check as a direct CLI gate, and `autoform-target-export` then converts
  audited FORMAL_GAP tasks into Autoform-compatible target YAML and a book-style
  Markdown directory, so the external harness has a concrete input queue.
- The open-question `research-benchmark` path now accepts the same persisted
  backend and the CLI defaults to it. Formal-gap skeletons are therefore
  grounded through the local SQLite FTS + Lean-shape + symbol-graph path used by
  the source audits, with a separate symbol-graph audit recording graph
  expansion quality.
- CSLib is useful to track as an external Lean library for future algorithm and
  proof-search infrastructure work, but it is not yet a priority runtime corpus
  for statistical probability/asymptotic lemmas.

This is intentionally integration-first. Retrieval and proof search should
reuse Loogle, Lean Finder, LeanDojo/ReProver, OpenProver, and AXLE rather than
being rebuilt inside this repo.

## Running

Offline smoke test:

```bash
python3 -m ai_statistician.cli demo --runs 200 --out runs/smoke
```

External JSON question file:

```bash
python3 -m ai_statistician.cli demo \
  --question-file examples/questions.json \
  --runs 300 \
  --out runs/external
```

Partial JSON question file with inferred families/parameters:

```bash
python3 -m ai_statistician.cli demo \
  --question-file examples/partial_questions.json \
  --runs 300 \
  --out runs/partial
```

LLM-gated theory intake for supported families:

```bash
/Users/yukang/LeanProjects/LeanPractice/.venv/bin/python \
  -m ai_statistician.cli theory-intake \
  --question-file examples/llm_theory_questions.json \
  --llm-theory
```

The LLM proposal agent is deliberately constrained. It may classify a natural
language question into one of the supported families, but the registry still
gates execution. If Haiku proposes `weibull`, `cox_model`, or any other
unsupported family, the system rejects the question before simulation or Lean
verification.

Question JSON contract:

```json
{
  "id": "external_normal_mean",
  "title": "Estimate a normal mean",
  "dgp": "X_i iid Normal(mu=1.25, sigma=2.0)",
  "target": "mu = E[X]",
  "dgp_family": "normal",
  "estimator_family": "sample_mean",
  "true_params": {"mu": 1.25, "sigma": 2.0},
  "n_obs": 100,
  "tags": ["mean", "normal"]
}
```

Supported `dgp_family` values today: `normal`, `bernoulli`, `constant`.
Supported `estimator_family` values today: `sample_mean`,
`sample_variance`, `sample_proportion`, `constant_estimator`.

For these supported cases, the intake layer can parse parameters such as
`Normal(mu=1.5, sigma=0.75)`, `Bernoulli(p=0.42)`, and `constant c=2.25`.
Normal questions can target either the mean (`sample_mean`) or variance
(`sample_variance`) while sharing the same DGP parser.
For unsupported examples such as Weibull hazards, Cox models, missing-data
targets, or semiparametric efficiency questions, the system should currently
return an unsupported-family error and route the request to roadmap work.

Every `demo` run writes one JSON trace per question plus `manifest.json`.
Run, evaluation, retrieval, proof, algorithm, and system-audit manifests include
stable registry fingerprints where relevant. These hashes cover the question
registry, estimator registry, vetted algorithm registry, and proof bank, so a
saved run can be tied back to the exact source registries that produced it.

Trace audit:

```bash
python3 -m ai_statistician.cli trace-audit \
  --run-dir runs/partial \
  --out runs/trace_audit_partial
```

Each per-question trace includes `trace_version`, creation time, provenance
fingerprints, the normalized question, estimator, proof checks, algorithm
metadata, simulation metrics, and final status. The trace audit checks that
trace files match their `manifest.json`, that provenance fingerprints agree,
that proof and simulation sections are present, and that algorithm hashes are
well-formed. The unified system audit includes this as a release gate.

Intake safety audit:

```bash
python3 -m ai_statistician.cli intake-audit --out runs/intake_audit
```

This verifies that supported external and partial question examples normalize
into registered DGP/estimator families, while unsupported examples in
`examples/unsupported_questions.json` are rejected before estimator selection,
Lean verification, or simulation. The unified system audit includes this as a
release gate.

Multi-seed evaluation:

```bash
python3 -m ai_statistician.cli eval \
  --question-file examples/questions.json \
  --n-seeds 3 \
  --runs 300 \
  --out runs/eval_external
```

This writes per-seed traces plus `evaluation_manifest.json`, with acceptance
rate, mean coverage, and mean RMSE by question.

Full proof-bank audit:

```bash
python3 -m ai_statistician.cli proof-audit \
  --negative-controls \
  --out runs/proof_audit
```

Real AXLE proof-bank audit:

```bash
/Users/yukang/LeanProjects/LeanPractice/.venv/bin/python \
  -m ai_statistician.cli doctor --out runs/doctor
/Users/yukang/LeanProjects/LeanPractice/.venv/bin/python \
  -m ai_statistician.cli proof-audit --real-lean --out runs/proof_audit_axle
```

Local Lean kernel proof-bank audit, useful when the AXLE Python package or API
is unavailable but a pinned Mathlib Lake workspace exists locally:

```bash
python3 -m ai_statistician.cli proof-audit \
  --local-lean \
  --lean-project /Users/yukang/LeanProjects/LeanPractice \
  --out runs/proof_audit_local_lean
```

Current full-bank local Lean evidence (2026-06-02):

```text
verified=112/112
kernel=112/112
verifier=local.lake_env_lean
strength=local_lean_kernel_batch
proof_bank_fingerprint=dcbb1825151a6779ab2726a7c998a0723c05debe98d6fbb034f5bd2a3d2d644f
```

Run `doctor` in the same Python runtime first. It reports
`real_lean_ready`, `real_lean_blockers`, `llm_theory_ready`, and
`llm_theory_blockers`, so a release audit can distinguish "API key is present"
from "the AXLE/Anthropic client package is actually importable." The current
local venv can pass offline gates with mock proof rows, but real Lean evidence
requires either the `proof` extra in the runtime that invokes `--real-lean`, or
the `--local-lean` backend with a local Lake project. Both AXLE and local Lean
rows set `kernel_verified=true` only when a real Lean kernel check succeeds;
mock-positive rows remain regression-test evidence only.
For proof-bank audits, the local Lean backend batches positive obligations into
one namespaced Lean file and runs `lake env lean` once, falling back to
per-obligation checks only when the batch file fails. This keeps full-bank
kernel audits practical while preserving precise diagnostics on failure.
The release-style research-system audit runs this proof-bank audit before
frontier/research smoke gates so a caching verifier can reuse the full-bank
kernel results downstream; for real AXLE or local-Lean runs, the proof gate
requires `all_kernel_verified=true`.
The same audit also uses a persistent SQLite formal-source index cache by
default (`runs/formal_source_index_cache/formal_source_index.sqlite`). Repeated
release audits can copy that cache into the run directory instead of rescanning
all local Mathlib/StatInference/Atlas Lean sources. Use
`--refresh-formal-source-index-cache` when local formal sources have changed, or
pass `--formal-source-index-cache ""` to force the old per-run rebuild path.
The manifest includes a `timings` block with coarse stage elapsed milliseconds
and `slowest_stages`, plus `counts.audit_slowest_stage`, so optimization work
can target the actual bottleneck in the current environment.
Because frontier coverage is a breadth smoke gate, `research-system-audit`
uses a separate `--frontier-smoke-runs` budget (default 25) instead of the main
`--runs` budget. Raise it for a heavier frontier simulation pass; leave it low
for fast release checks while `research-benchmark` and `research-eval` carry
the heavier simulation evidence.

This writes `proof_audit_manifest.json` plus one exported Lean file per formal
obligation. The Lean exports are intentionally per-obligation files because
several examples reuse helper names such as `constantEstimator`.
It also writes `proof_attempts.jsonl` and
`proof_attempt_log_manifest.json`. Those rows are the first verifier-filtered
training substrate: they include the formal statement, spliced Lean candidate,
candidate hash, verifier, `verification_strength`, `kernel_verified`, reward,
errors/first error, retrieval hits, and a `supervision_target` for successful
proof bodies. Mock-positive rows are regression-test evidence only; AXLE or
local-Lean rows with `kernel_verified=true` are Lean-kernel proof evidence. This is
proof-level logging only; tactic-state transitions and process rewards remain
future work.
With `--negative-controls`, the audit also records one intentionally empty
proof body per obligation. These negative rows are not theorem checks; they are
controlled verifier-error examples for repair/value-model data. The unified
`research-system-audit` enables them for the offline mock verifier and skips
them for `--real-lean` to avoid doubling remote AXLE calls.
The capability audit uses the same distinction: available subclaims are marked
`ACHIEVED` for the AXLE requirement only when the latest proof audit has
`all_kernel_verified=true` and covers the full registered proof bank; otherwise
they remain `PARTIAL` while still passing offline release gates as regression
evidence.
Use `proof-training-export` to convert a checked attempt log into deterministic
whole-proof SFT data:

```bash
python3 -m ai_statistician.cli proof-training-export \
  --attempt-log runs/proof_audit/proof_attempts.jsonl \
  --out runs/proof_training_export
```

This writes `proof_sft_train.jsonl`, `proof_sft_validation.jsonl`,
`proof_sft_all.jsonl`, and `proof_training_manifest.json`. The train/validation
split is deterministic from the attempt id so reruns are comparable. The
release-style `research-system-audit` now emits this export automatically from
its proof-audit attempt log so training data provenance is captured beside the
proof, retrieval, simulation, and gap manifests.

Use `proof-repair-export` to turn failed attempts into repair examples:

```bash
python3 -m ai_statistician.cli proof-repair-export \
  --attempt-log runs/proof_audit/proof_attempts.jsonl \
  --out runs/proof_repair_export
```

This writes `proof_repair_train.jsonl`, `proof_repair_validation.jsonl`,
`proof_repair_all.jsonl`, and `proof_repair_manifest.json`. Each row pairs a
failed proof body plus verifier errors with an accepted proof body for the same
obligation. This is the first verifier-feedback dataset for proof repair; it
does not replace tactic-state tracing or process rewards, but it stops failed
proof attempts from being discarded as unstructured audit text.

Before training a model, run the no-training whole-proof baseline:

```bash
python3 -m ai_statistician.cli proof-policy-baseline \
  --train-jsonl runs/proof_training_export/proof_sft_train.jsonl \
  --validation-jsonl runs/proof_training_export/proof_sft_validation.jsonl \
  --out runs/proof_policy_baseline
```

This nearest-neighbor proof-memory policy reports top-1/top-k exact completion
match and whether the predicted source obligation was already in the
validation example's retrieved context. It is intentionally weak; future
whole-proof SFT or rejection-sampling policies should beat it. The unified
`research-system-audit` also runs this baseline automatically after exporting
the proof SFT data, so every release snapshot has a no-training policy floor.
The same audit now also runs `proof-policy-train`, producing
`proof_policy_model.json` and train/validation prediction rows as the first
trained whole-proof policy baseline.
The research-agent side has an analogous `research-policy-baseline` over
problem-formalization, theory-plan, formal-gap-routing, and simulation-critique
examples exported from full research traces.

Retrieval audit:

```bash
python3 -m ai_statistician.cli retrieval-audit --out runs/retrieval_audit
```

This ranks each Mathlib-backed obligation against the entire local statistics
proof bank and reports top-1, top-k, and MRR. It is a premise-selection smoke
test, not a proof checker; the proof checker remains AXLE.

Optional Loogle evidence:

```bash
python3 -m ai_statistician.cli retrieval-audit \
  --loogle \
  --out runs/retrieval_audit_loogle
```

The Loogle mode calls the public Mathlib search service and stores returned
declaration names beside the local retrieval audit. It does not change the
release gate, because network search availability should not decide whether a
local build passes. The current JSON endpoint is identifier-oriented, so this is
a namespace/name-resolution smoke test for registered expected lemmas. Semantic
natural-language premise retrieval remains a Lean Finder/ReProver-style roadmap
item.

Formal source index:

```bash
python3 -m ai_statistician.cli formal-source-audit --out runs/formal_source_index
```

This is the local theorem-mining layer for proof-bank expansion. The source
inventory only checks that local formal sources exist; the formal source index
extracts Lean declaration names/signatures from Mathlib Probability/MeasureTheory,
StatInference, EmpiricalProcessLEAN, and lean-stat-learning-theory, then audits
search queries for reusable theorem families such as finite-sum variance,
Bonferroni/finite union bounds, Chebyshev tails, CLT skeletons, Borel-Cantelli,
conditional expectation, sub-Gaussian learning, empirical-process tools, and
Godambe/bootstrap algebra. The intended workflow is: index first, reuse or adapt
existing declarations second, and only then add a new AXLE proof-bank obligation.
Research benchmark traces also attach the top local declaration hits to every
`FORMAL_GAP` subclaim and copy them into the generated Lean skeleton comments,
so a gap is always accompanied by concrete local source candidates rather than
only a free-text missing-primitive label.

Formal source graph:

```bash
python3 -m ai_statistician.cli formal-source-graph-audit \
  --out runs/formal_source_graph
```

This audits graph expansion over the declaration corpus. Nodes are Lean
declarations and compressed theorem symbols; edges record which declarations
mention each symbol. The report surfaces high-degree cross-source symbols and
checks graph-expanded retrieval for variance, Hajek ratio, Wald variance,
Rademacher, martingale, Borel-Cantelli, and independence queries. This is the
current lightweight graph-RAG layer for formal statistics: useful for finding
reusable local declarations. If a `lean_rag` SQLite graph exists at the
standard local path, or is supplied through `--lean-rag-db` or
`AI_STATISTICIAN_LEAN_RAG_DB`, the research benchmark, research loop, primitive
coverage, and system audit fuse dependency-direction evidence from that graph.
This auto-discovery applies to both SQLite-backed retrieval and the lighter
in-memory fallback. Kernel-extracted proof-state graphs remain a future
LeanDojo/ReProver-style integration.

Shared `lean_rag` package audit:

```bash
python3 -m ai_statistician.cli lean-rag-package-audit \
  --package-root /path/to/EmpericalProcessLEAN/lean_rag \
  --out runs/lean_rag_package_audit
```

This checks required scripts/docs, source-registry trust policy, seed query
lanes, and any available `build/lean_graph/shared_manifest.json`. It is the
fast monitor for whether the external RAG package is usable; it does not treat
generated external indexes as proof evidence.

Algorithm registry audit:

```bash
python3 -m ai_statistician.cli algorithm-audit --out runs/algorithm_audit
```

The algorithm registry is the source of truth for executable estimators. Each
registered implementation has a stable ID, summary, version, registry status,
and SHA-256 hash of the Python source. Question traces include this metadata so
simulation reports are tied to the exact implementation that produced them.

Readiness doctor:

```bash
python3 -m ai_statistician.cli doctor --out runs/doctor
```

The doctor command is the operator preflight. It checks required runtime pieces
such as Python, `numpy`, the package directory, examples, non-empty proof and
algorithm registries, and optional production integrations such as `AXLE_API_KEY`,
the `axle` package, `ANTHROPIC_API_KEY`, the `anthropic` package, OpenProver, and
the latest run manifests. Secret values are never printed. The command writes
`doctor_manifest.json` so environment readiness can be archived next to proof,
algorithm, retrieval, and system-audit manifests.

Capability audit:

```bash
python3 -m ai_statistician.cli capability-audit --out runs/capability_audit
```

The capability audit maps the project objective to current source and manifest
evidence. It checks question intake, estimator selection, multi-agent
orchestration, AXLE-backed proof verification hooks, vetted algorithms, Monte
Carlo diagnostics, trace persistence, retrieval/prover integration, release
gates, and roadmap documentation. It intentionally marks Lean verification as
`PARTIAL`: the current system has real Mathlib-backed finite proof obligations,
but not full asymptotic statistical proofs. This makes the completion boundary
auditable instead of relying on informal claims.

Prover component audit:

```bash
python3 -m ai_statistician.cli prover-component-audit --out runs/prover_component_audit
```

The prover component audit maps the current AI Statistician system to the
AI-for-math stack in `AI for Math Resources/master_ai_for_math_formal_verification.md`:
hard verifier, formal data/autoformalization, premise retrieval, tactic/proof
policy, search/RL, subgoal decomposition, skill library, construction,
counterexample generation, simulation, provenance, and model training. This is
the honest check for whether we have actually trained/built each component. It
is now part of `research-system-audit`, so the single release manifest records
both production-readiness gates and the remaining prover-stack training gaps.
Current expected result: proof-bank verifier evidence, benchmark data,
simulation gates, and provenance are release-ready under the audited scaffold.
The latest release-style audit passes after bounded adaptive Monte Carlo reruns
resolve precision-limited simulator rows.  Retrieval, subgoal planning, skill
memory, construction, counterexample loops, and proof-attempt logging are
partial; tactic policy, proof search, value/RL, and model training are not yet
production-strength.  Passing these gates still does not mean arbitrary
frontier asymptotic theorems are fully proved in Lean.

Unified system audit:

```bash
python3 -m ai_statistician.cli system-audit \
  --include-partial-examples \
  --runs 300 \
  --out runs/system_audit
```

Real AXLE system audit:

```bash
/Users/yukang/LeanProjects/LeanPractice/.venv/bin/python \
  -m ai_statistician.cli system-audit \
  --real-lean \
  --runs 200 \
  --seeds 20260528 20260529 \
  --out runs/system_audit_axle
```

This writes `system_audit_manifest.json` with release gates: algorithm audit,
retrieval audit, proof-bank audit, one-shot question runs, and optional
multi-seed evaluation. It is the release-style artifact to inspect before
trusting a build.

Release bundle:

```bash
python3 -m ai_statistician.cli release-bundle \
  --include-partial-examples \
  --runs 300 \
  --out runs/release_bundle
```

The release bundle is the top-level handoff artifact. It runs the readiness
doctor, capability audit, and unified system audit into one directory, then
writes `release_manifest.json` with a stable `release_id`, gate summary,
provenance fingerprints, counts, and paths to every sub-manifest. Use this when
you want one auditable folder that says exactly which question registry,
estimator registry, algorithm registry, and proof bank were released.

Real AXLE release bundle:

```bash
/Users/yukang/LeanProjects/LeanPractice/.venv/bin/python \
  -m ai_statistician.cli release-bundle \
  --real-lean \
  --include-partial-examples \
  --runs 200 \
  --seeds 20260528 20260529 \
  --out runs/release_bundle_axle
```

This is the strongest current release check. It requires the real AXLE and
Anthropic-ready runtime, runs `axle.verify_proof` through the bundled proof and
question gates, and includes `real_lean_ready` in the top-level release gates.

Real Lean verification through AXLE, using the existing venv if needed:

```bash
/Users/yukang/LeanProjects/LeanPractice/.venv/bin/python \
  -m ai_statistician.cli demo --real-lean --runs 300 --out runs/axle
```

The real Lean path uses `AXLE_API_KEY` from `.env`.
`research-system-audit` wraps the selected verifier in an in-run cache, so the
same registered obligation is kernel-checked once and reused across frontier
smoke, proof-bank audit, and research benchmark stages. The output counts
`verifier_cache_hits`, `verifier_cache_misses`, and `verifier_cache_size` to make
that reuse auditable.

## Next Production Steps

- Broaden supported estimators beyond normal means, normal variances,
  Bernoulli proportions, and constant estimators.
- Add a Loogle/Lean Finder/ReProver retrieval provider and measure cold-to-RAG
  proof lift on the local statistics proof bank.
- Add sandboxed execution before allowing any LLM-written Python algorithm into
  the registry.
- Add a Lean project for long-lived statistics definitions that should become
  Mathlib or `StatInference` contributions.
- Continue formalizing stronger statistical guarantees beyond the current
  finite-sample unbiasedness facts, then asymptotic statements only after the
  required probability theory infrastructure exists.
