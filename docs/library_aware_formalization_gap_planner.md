# Library-Aware Formalization Gap Planner

The planner is the research-facing layer above proof search. Its job is not to
prove a theorem directly. Its job is to answer a more global question:

```text
Given a target theorem T and a current formal library snapshot L,
what small additional formalization Delta should be built first so that
L + Delta is a plausible route to a kernel-checked proof of T?
```

This is intentionally narrower than formalizing a whole field. The planner
selects existing declarations, theorem compositions, minimal wrappers, bridge
lemmas, source ports, and new primitive obligations for a single theorem route.
It also emits `do_not_formalize_now` hints for adjacent theory that is real but
not on the cheapest current route.

## Component Boundary

The component is exposed by:

```bash
python3 -m ai_statistician.cli goal-conditioned-minimal-formalization-plan \
  --formalization-delta-plan-dir runs/current/formalization_delta_plan \
  --formal-verifier-queue-dir runs/current/formal_verifier_queue \
  --out runs/current/goal_conditioned_minimal_formalization_plan
```

The output manifest identifies itself as
`library_aware_formalization_gap_planner`. It is planning evidence only. A row
does not become theorem proof evidence until a target prover, currently
AXLE/local Lean in this repository, verifies the named theorem or bridge proof
with no placeholder axioms, `sorry`, or `admit`.

Planner quality can be scored against a curated or held-out theorem-route file:

```bash
python3 -m ai_statistician.cli formalization-gap-planner-benchmark \
  --out runs/current/formalization_gap_planner_benchmark

python3 -m ai_statistician.cli formalization-gap-planner-adapter-registry \
  --lean-rag-db runs/current_status_lean_rag_dependency_graph/stat_inference.sqlite \
  --out runs/current/formalization_gap_planner_adapter_registry

python3 -m ai_statistician.cli formalization-gap-planner-evaluation \
  --goal-conditioned-minimal-formalization-plan-dir runs/current/goal_conditioned_minimal_formalization_plan \
  --ground-truth runs/current/formalization_gap_planner_benchmark/formalization_gap_planner_ground_truth.json \
  --out runs/current/formalization_gap_planner_evaluation
```

The repo ships a reusable default route-truth file at
`data/formalization_gap_planner_ground_truth.json`. The benchmark export command
writes a versioned manifest, JSONL route summary, markdown report, and a copy of
that ground-truth file for publication artifacts. The evaluation writes
row-level route recall/precision, Lean-delta
precision/recall, existing-library reuse precision/recall, coverage-label
accuracy, two-DAG readiness, feedback-loop readiness, and the proof-boundary
check. These scores are benchmark evidence about planning quality, not theorem
proof evidence.

The adapter registry command records which refinement tools can satisfy each
hook, which response fields they must emit, and whether local commands,
packages, credentials, or configured paths are present. Built-in offline
adapters should be ready in a normal checkout; live Paperclip/PaperQA/OpenScholar,
LeanSearch/Loogle/LeanExplore/local Lean RAG, Lean/LSP, and LeanDojo-style
adapters may report `NEEDS_INSTALL`, `NEEDS_CREDENTIALS`, or
`NEEDS_CONFIGURATION` until configured. Registry rows are integration readiness
evidence, not proof evidence.

The interactive hooks can then be materialized as tool-facing refinement work:

```bash
python3 -m ai_statistician.cli formalization-gap-planner-refinement-queue \
  --goal-conditioned-minimal-formalization-plan-dir runs/current/goal_conditioned_minimal_formalization_plan \
  --formalization-gap-planner-evaluation-dir runs/current/formalization_gap_planner_evaluation \
  --formal-verifier-replay-calibration-dir runs/current/formal_verifier_replay_calibration \
  --out runs/current/formalization_gap_planner_refinement_queue

python3 -m ai_statistician.cli formalization-gap-planner-refinement-adapter-responses \
  --formalization-gap-planner-refinement-queue-dir runs/current/formalization_gap_planner_refinement_queue \
  --ground-truth runs/current/formalization_gap_planner_benchmark/formalization_gap_planner_ground_truth.json \
  --out runs/current/formalization_gap_planner_refinement_adapter

python3 -m ai_statistician.cli formalization-gap-planner-local-formal-source-adapter \
  --formalization-gap-planner-refinement-queue-dir runs/current/formalization_gap_planner_refinement_queue \
  --base-response-jsonl runs/current/formalization_gap_planner_refinement_adapter/formalization_gap_planner_refinement_evidence_responses.jsonl \
  --lean-rag-db runs/current_status_lean_rag_dependency_graph/stat_inference.sqlite \
  --out runs/current/formalization_gap_planner_local_formal_source_adapter

python3 -m ai_statistician.cli formalization-gap-planner-local-proof-state-adapter \
  --formalization-gap-planner-refinement-queue-dir runs/current/formalization_gap_planner_refinement_queue \
  --base-response-jsonl runs/current/formalization_gap_planner_local_formal_source_adapter/formalization_gap_planner_refinement_evidence_responses.jsonl \
  --lean-project /Users/yukang/LeanProjects/LeanPractice \
  --out runs/current/formalization_gap_planner_local_proof_state_adapter

python3 -m ai_statistician.cli formalization-gap-planner-refinement-evidence \
  --formalization-gap-planner-refinement-queue-dir runs/current/formalization_gap_planner_refinement_queue \
  --response-jsonl runs/current/formalization_gap_planner_local_proof_state_adapter/formalization_gap_planner_refinement_evidence_responses.jsonl \
  --out runs/current/formalization_gap_planner_refinement_evidence

python3 -m ai_statistician.cli formalization-gap-planner-route-revision-overlay \
  --goal-conditioned-minimal-formalization-plan-dir runs/current/goal_conditioned_minimal_formalization_plan \
  --formalization-gap-planner-refinement-evidence-dir runs/current/formalization_gap_planner_refinement_evidence \
  --out runs/current/formalization_gap_planner_route_revision_overlay
```

This queue routes each theorem plan into literature discovery, Lean-library
grounding, proof-state feedback, and route-revision items. Optional evaluation
and replay-calibration manifests add route-truth mismatches and prover residuals
as prioritization signals. The adapter command is a deterministic offline
producer that turns the shipped route-truth labels into response JSONL for local
end-to-end tests. The local formal-source adapter can then replace
`lean_library_grounding` rows with real declaration-search evidence from the
current formal-source backend and optional Lean RAG dependency DB, while
preserving other adapter responses. The local proof-state adapter can then
replace `proof_state_feedback` rows with local Lean diagnostics, blocks
`sorry`/`admit` skeletons before invocation, and merges residual goals into the
same evidence JSONL. Live Paperclip/PaperQA/OpenScholar,
LeanSearch/Loogle/LeanExplore, and Lean/LSP/prover adapters should emit the
same response contract. The evidence command validates tool responses keyed by
`refinement_item_id` and emits route-revision proposals. The overlay command
applies those proposals back to matching route plans without mutating the
original manifest, recording changed primitives, revised DAG nodes, residual
goals, source refs, and the next required replay gate. Literature, Lean-search,
prover-diagnostic responses, and revision overlays are route evidence only.

## Interactive Literature-To-Lean Route Loop

The planner should be used as an interactive route-synthesis loop, not as a
single-shot proof bot:

```text
new theorem request
  -> bounded literature/evidence search
  -> informal knowledge DAG
  -> Lean realization DAG
  -> minimal Lean delta route
  -> leaf-level prover/LSP attempts
  -> residual feedback
  -> revised route or explicit remaining gaps
```

The expansion rule is evidence-bounded: search papers until the proof route
stabilizes, stop when new sources stop adding required assumptions or
primitives, and use Lean failures to trigger only focused literature or
library searches. This prevents "read all literature first" behavior and keeps
the objective theorem-conditioned.

The current manifest therefore exports two separate DAG views:

- `informal_knowledge_dag_nodes` / `informal_knowledge_dag_edges`
  Source-facing definitions, assumptions, proof steps, theorem variants, and
  required math concepts.

- `lean_realization_dag_nodes` / `lean_realization_dag_edges`
  Current-library reuse, near matches, wrappers, bridge lemmas, source ports,
  new primitives, and excluded alternatives.

`route_revision_triggers` and `interactive_refinement_hooks` record when the
system should search more literature, search more Lean, request LSP/prover
feedback, strengthen or weaken assumptions, or abandon an expensive route.

## Portable Contract

The planner is Lean-backed today, but the exported contract is prover-agnostic.
A prover adapter should provide:

- `target_theorem`: formal skeleton or structured informal theorem goal.
- `library_snapshot`: indexed declarations, dependency metadata, proof-bank
  actions, source coverage, and prior verifier attempts.
- `existing_reuse_nodes`: declarations or verified obligations already present
  in the current library.
- `minimal_additional_formalization_nodes`: wrappers, bridges, source ports, or
  new primitives selected for this theorem.
- `and_or_plan_nodes` and `and_or_plan_edges`: selected AND requirements plus
  OR alternatives excluded from the current minimal cut.
- `informal_knowledge_dag_nodes` and `lean_realization_dag_nodes`: the two
  aligned route DAGs.
- `route_revision_triggers`: residual-goal, source-gap, or first-principles
  risk events that should revise the route.
- `next_work_packets`: bounded prover work items with source and kernel gates.

The same shape can be adapted to Lean, Rocq/Coq, Isabelle, Agda, or a mixed
symbolic/statistical verifier, as long as the adapter can assign costs to
existing reuse and missing formalization work.

Every run also writes
`library_aware_formalization_gap_plan.schema.json`. The schema id is:

```text
urn:ai-statistician:schemas:library-aware-formalization-gap-plan:1
```

## Route Objective

The planner optimizes a heuristic objective rather than claiming a mathematical
minimum:

```text
cost(route) =
  declaration_delta_cost
  + import_cone_penalty
  + dependency_depth_penalty
  + blocker_penalty
  - verified_reuse_credit
```

The exported `optimization_objectives` are:

- minimize new declarations
- minimize import cone
- minimize dependency depth
- minimize typeclass and statement-shape risk
- maximize existing verified library reuse
- avoid field-wide formalization not needed for this theorem

Rows also receive a `pareto_profile`, such as `reuse_existing_library`,
`wrapper_only_delta`, `minimal_bridge_cut`, `source_grounded_port`, or
`least_first_principles_exposure`. This avoids pretending that "minimal" is a
single universal scalar.

## Planner Algorithm

The current implementation composes four existing AI Statistician artifacts:

1. `formalization_delta_plan`
   Builds primitive-level actions and theorem-level route summaries.

2. `formal_verifier_queue`
   Adds route ranking, import/dependency context, source trust, semantic
   faithfulness, proof-attempt history, and kernel-smoke calibration.

3. `goal_conditioned_minimal_formalization_plan`
   Narrows global missing theory into theorem-specific selected nodes,
   excluded alternatives, portable work packets, the informal knowledge DAG,
   the Lean realization DAG, route revision triggers, and AND/OR route view.

4. `formalization_gap_planner_adapter_registry`
   Records the live/offline adapter inventory, preflight readiness, output
   response contracts, and proof-evidence boundary for literature, Lean
   grounding, proof feedback, and route revision.

5. `formalization_gap_planner_refinement_queue`
   Turns route-revision triggers and interactive hooks into auditable work
   orders for literature tools, Lean search, LSP/prover diagnostics, and
   route-DAG revision.

6. `formalization_gap_planner_refinement_adapter_responses`
   Produces conservative local response JSONL from route-truth benchmark labels
   so the refinement loop can be exercised without live MCP credentials. It is
   adapter output, not proof evidence.

7. `formalization_gap_planner_local_formal_source_adapter`
   Replaces Lean-library-grounding rows with local declaration-search evidence
   from the formal-source backend and optional Lean RAG dependency DB, while
   preserving other adapter responses.

8. `formalization_gap_planner_local_proof_state_adapter`
   Replaces proof-state-feedback rows with local Lean diagnostics and residual
   goals, while preserving merged literature and Lean-grounding responses. It
   blocks `sorry`/`admit` skeletons and remains diagnostic feedback, not proof
   evidence.

9. `formalization_gap_planner_refinement_evidence`
   Records tool responses to the refinement queue and normalizes literature
   evidence, Lean declaration hits, coverage updates, prover diagnostics,
   residual goals, and route-revision proposals.

10. `formalization_gap_planner_route_revision_overlay`
   Applies accepted route-revision proposals back to the selected route plan as
   a non-mutating overlay with changed primitives, DAG nodes, source refs,
   residual goals, and replay gates.

11. `formalization_gap_planner_benchmark`
   Exports reusable route-truth labels for evaluation: required primitives,
   actual existing reuse, actual Lean delta, coverage classification, source
   references, and proof-evidence boundaries.

12. `formal_verifier_replay_export`
   Turns selected routes into theorem/bridge replay tasks. This is the handoff
   to actual proof attempts, not proof evidence.

## Statistics-Specific Value

For statistical theory, most expensive failures are hidden assumptions and
overbroad formalization choices. A theorem may need a measurability bridge,
wrapper around convergence notation, or a special empirical-average lemma. It
usually should not trigger a full formalization of all empirical process theory.

The planner therefore records:

- selected primitives for this theorem
- exact reuse candidates
- bridge and wrapper nodes
- source-discovery nodes
- first-principles nodes, if unavoidable
- explicit `do_not_formalize_now` exclusions
- blocked-only-by reasons
- theorem-specific worker packets

This makes library growth compound: when a future Lean/mathlib/StatInference
snapshot gains a relevant theorem, the same planner should lower the route cost
and convert some missing nodes into reuse nodes.

## Evaluation Targets

A publication-quality evaluation should measure:

- route recall and precision against held-out human or kernel-verified route
  truth
- Lean-delta precision and recall for the selected wrappers, bridges, source
  ports, and new primitive obligations
- coverage classification accuracy for `already exists`, `wrapper`, `bridge`,
  `source discovery`, and `new theory` labels
- delta size: new wrappers, bridges, definitions, and theorem obligations
- import cone and dependency depth
- route cost versus a human minimal-delta plan
- proof-bank and local-library reuse
- rate of avoiding unrelated field-wide formalization
- downstream proof-attempt success after replay
- semantic faithfulness of selected route to the informal theorem

The key claim should be modest and testable: the planner predicts a smaller and
more useful formalization Delta than generic premise retrieval or whole-field
formalization baselines, while preserving an honest proof-evidence boundary.

## Tool/Resource Map

The route planner is a component boundary; the following tools are optional
adapters, not proof evidence:

- Literature discovery: [Paperclip](https://paperclip.gxl.ai/docs),
  [PaperQA2](https://github.com/Future-House/paper-qa),
  [OpenScholar](https://arxiv.org/abs/2411.14199),
  [Semantic Scholar API](https://www.semanticscholar.org/product/api),
  [OpenAlex Works API](https://docs.openalex.org/api-entities/works), arXiv.
- Paper-to-agent source adapters:
  [Paper2Agent](https://arxiv.org/abs/2509.06917) can inspire a
  `PaperFormalizationAgent` that exposes definitions, assumptions, theorem
  variants, proof-step graphs, and cited prerequisites as route evidence.
- PDF/math extraction: [GROBID](https://github.com/grobidOrg/grobid),
  [Nougat](https://arxiv.org/abs/2308.13418),
  [olmOCR](https://arxiv.org/abs/2502.18443), Marker.
- Informal route decomposition:
  [Aria](https://arxiv.org/abs/2510.04520),
  [DRIFT](https://arxiv.org/abs/2510.10815),
  [ProofFlow](https://arxiv.org/abs/2510.15981), and
  [LeanArchitect](https://arxiv.org/abs/2601.22554) are the closest
  dependency-graph and blueprint-alignment analogs for extracting or revising
  the informal knowledge DAG.
- Lean grounding: [LeanSearch v2](https://arxiv.org/abs/2605.13137),
  [LeanExplore](https://arxiv.org/abs/2506.11085),
  [Loogle](https://loogle.lean-lang.org/), and the local Lean RAG DB.
- Proof-state feedback: the local Lake/Lean adapter,
  [lean-lsp-mcp](https://github.com/oOo0oOo/lean-lsp-mcp), Lean LSP, and
  `lake build`.
- Premise/proof search: [LeanDojo/ReProver](https://github.com/lean-dojo/ReProver),
  [LeanHammer](https://arxiv.org/abs/2506.07477), plus Lean tactics such as
  `aesop`, `simp`, `exact?`, and `apply?`.
- Agent orchestration: [Ax-Prover](https://arxiv.org/abs/2510.12787),
  [AlphaEvolve](https://arxiv.org/abs/2506.13131), and
  [AlphaProof Nexus](https://arxiv.org/abs/2605.22763) are orchestration
  references for verifier-aware attempt loops; their outputs should enter as
  prover feedback or route-revision evidence, not direct proof claims.
- Evaluation: [SorryDB](https://arxiv.org/abs/2603.02668), held-out proved
  theorem routes, and real missing-gap tasks.

Paperclip/PaperQA2/OpenScholar-style outputs should be recorded as route
evidence only. A Lean/LSP/prover output should be recorded as residual feedback
unless and until the target prover kernel verifies the final theorem with no
placeholder axioms, `sorry`, or `admit`.
