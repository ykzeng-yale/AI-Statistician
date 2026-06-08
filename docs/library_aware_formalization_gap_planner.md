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

The release-style `research-system-audit` command now runs the reusable planner
path end to end: route evaluation, refinement queue, deterministic adapter
responses, local literature/formal-source/proof-state adapter fallbacks,
refinement evidence, route-revision overlay, route-stability audit, proof-state
triage, target-prover adapter contract, publication bundle, and
publication-bundle audit are emitted as gated artifacts in
`research_system_audit_manifest.json`. That system-level artifact map also
names the route-replan standalone seed schema, the cross-prover target summary
and schema, and the publication-bundle schema catalog and schema. It also
reports cross-prover target-summary contract errors, publication-bundle
schema-catalog validity counts, and optional interactive decision-policy
resource-link check counts in the top-level audit counts.

For external prover ecosystems or paper supplements that do not have the full
AI Statistician audit pipeline, normalize a raw theorem request first, then use
the generated standalone route seed:

```bash
python3 -m ai_statistician.cli formalization-gap-planner-target-intake \
  --input data/formalization_gap_planner_target_intake_example.json \
  --out runs/current/formalization_gap_planner_target_intake

python3 -m ai_statistician.cli formalization-gap-planner-component-resource-registry \
  --out runs/current/formalization_gap_planner_component_resource_registry

python3 -m ai_statistician.cli formalization-gap-planner-llm-route-planner \
  --input runs/current/formalization_gap_planner_target_intake/formalization_gap_planner_target_intake_standalone_seed.json \
  --provider prompt_only \
  --formalization-gap-planner-component-resource-registry-dir runs/current/formalization_gap_planner_component_resource_registry \
  --out runs/current/formalization_gap_planner_llm_route_planner

python3 -m ai_statistician.cli formalization-gap-planner-standalone-plan \
  --input runs/current/formalization_gap_planner_llm_route_planner/formalization_gap_planner_llm_route_planner_standalone_seed.json \
  --out runs/current/formalization_gap_planner_standalone_plan

python3 -m ai_statistician.cli formalization-gap-planner-portable-plan-audit \
  --goal-conditioned-minimal-formalization-plan-dir runs/current/formalization_gap_planner_standalone_plan \
  --out runs/current/formalization_gap_planner_portable_plan_audit

python3 -m ai_statistician.cli formalization-gap-planner-library-coverage-map \
  --goal-conditioned-minimal-formalization-plan-dir runs/current/formalization_gap_planner_standalone_plan \
  --out runs/current/formalization_gap_planner_library_coverage_map

python3 -m ai_statistician.cli formalization-gap-planner-primitive-action-queue \
  --formalization-gap-planner-library-coverage-map-dir runs/current/formalization_gap_planner_library_coverage_map \
  --out runs/current/formalization_gap_planner_primitive_action_queue

python3 -m ai_statistician.cli formalization-gap-planner-minimal-delta-audit \
  --goal-conditioned-minimal-formalization-plan-dir runs/current/formalization_gap_planner_standalone_plan \
  --out runs/current/formalization_gap_planner_minimal_delta_audit

python3 -m ai_statistician.cli formalization-gap-planner-source-grounding-audit \
  --goal-conditioned-minimal-formalization-plan-dir runs/current/formalization_gap_planner_standalone_plan \
  --out runs/current/formalization_gap_planner_source_grounding_audit

# Optional after proof-state/refinement evidence exists: also audit prover
# residual goals for source refs, literature-search hooks, or formal boundaries.
python3 -m ai_statistician.cli formalization-gap-planner-source-grounding-audit \
  --goal-conditioned-minimal-formalization-plan-dir runs/current/formalization_gap_planner_standalone_plan \
  --formalization-gap-planner-refinement-evidence-dir runs/current/formalization_gap_planner_refinement_evidence \
  --out runs/current/formalization_gap_planner_source_grounding_audit_after_feedback
```

The `formalization-gap-planner-llm-route-planner` command is the intended
intelligence boundary for theorem understanding, literature-backed informal
route synthesis, informal DAG construction, semantic alignment hypotheses,
prover-residual interpretation, and minimal-delta rationale. By default it
stages Anthropic/Claude request packets and prompts without calling a model.
`prompt_only` remains an explicit no-provider mode. With a reviewed
`--response-json` or `--static-response-file`, it validates the LLM route
proposal and emits a revised standalone seed. With `--invoke-provider`, it can
call the configured generator backend. The public planner path records
`*_provider_execution_mode` and live-call counters so staged packets are
distinguishable from paid provider calls. For live
AI Statistician development, the default LLM runtime is Anthropic Claude API:
Sonnet 4.6 for theorem understanding, route planning, theory repair, and
formalizer work; Haiku 4.5 for cheaper structured helper tasks such as intake,
simulation planning, algorithm-planning packets, and boundary critique. The same
request/response contracts still run against explicit `openai` live generation
or `static` replay. Runtime topology validation records the intended model tier
for each LLM subsystem and rejects recognized Anthropic family drift, for example
a Haiku-designated helper configured with a Sonnet or Opus model. Accepted LLM rows must include
source-grounded informal DAG nodes, formal-realization DAG nodes, alignment
rationales, a minimality rationale, a versioned minimal-delta cost witness, and
an explicit proof-evidence boundary; `kernel_verified=true` claims are
rejected. Each row also carries a `realization_coverage_witness` summarizing
whether the selected primitives have standalone-route nodes and formal
realization nodes, whether delta primitives have route-alignment edges, and
whether any introduced primitive lacks an alignment edge. This is a portable
inspection aid for external prover teams. Evaluation rows preserve the LLM
route-adoption readiness status and blockers, so an accepted but
search-pending/refinement-pending Claude route is not reported as ready for
standalone replay. This is still planning evidence, not proof evidence. The
cost witness uses
`formalization_gap_planner_minimal_delta_cost_policy:1` and must include a
nonnegative route cost plus one `primitive_costs` row per selected primitive.
It must also include an `and_or_cost_graph` with enumerated route options,
exactly one selected option, and no listed alternative with lower `route_cost`.
Those costs are planning evidence for comparing exact reuse, wrappers, bridge
lemmas, source ports, new definitions, typeclass/import burden, semantic risk,
and reuse credit. They are not proof evidence.
Accepted LLM route-planner seeds copy that graph to the route-level and
`replan_metadata.minimal_delta_and_or_cost_graph` fields, and the standalone
input schema publishes both locations so non-Lean prover teams can inspect the
selected route and its alternatives without parsing raw LLM response rows. The
same accepted seed also preserves `realization_coverage_witness` at the route
level and under `replan_metadata.llm_route_planner_realization_coverage_witness`,
so downstream standalone planning can inspect selected/delta primitive coverage
without reopening raw LLM rows.
When such a seed is converted into the portable standalone plan, the planner
copies compact cost-graph and realization-witness traces into each row's
`standalone_input_trace`, including the effective `target_prover_family` from
the standalone input or route metadata. It reports manifest counters for
graph-bearing traces,
complete realization witnesses, missing selected formal-realization primitives,
and missing delta-alignment primitives, and uses the selected route-option and
primitive costs when present instead of falling back to coverage-label defaults.
Evaluation rows then surface `minimal_delta_cost_graph_present`,
`minimal_delta_route_option_count`, `minimal_delta_selected_route_option_id`,
`minimal_delta_selected_route_cost`, `realization_coverage_witness_present`,
`realization_coverage_complete`,
`realization_missing_selected_formal_primitives`, and
`realization_missing_delta_alignment_primitives`, making benchmark and
publication artifacts able to inspect minimal-route and realization-coverage
evidence without depending on Lean-specific internals.
The one-command reuse-smoke manifest also promotes LLM route-planner
realization-coverage counters for both primary and feedback planner passes, so
a public artifact consumer can distinguish staged prompt-only requests from
accepted routes whose selected and delta primitives are fully covered by
standalone/formal DAG nodes and alignment edges. It also forwards the
publication-bundle audit counters for the structured
`realization_coverage_witness` row-schema gate and the accepted-seed witness
preservation gate, so schema-level and seed-level portability checks are visible
without opening the nested audit manifest.

LLM route-planner request packets can also carry compact component-resource
registry context through
`--formalization-gap-planner-component-resource-registry-dir`. That context
lists planner stages, local-first resources, frontier tools such as Paperclip,
PaperQA2, LeanSearch/Loogle, Lean LSP, Rocq, Isabelle, and Agda adapters, plus
their request/response contracts and quality gates. The model may use those
rows only to choose bounded `search_requests` and `planner_next_actions`.
Registry rows are not treated as evidence that a resource was called; actual
tool outputs must still enter through source-grounding, library-coverage,
refinement-evidence, or resource-response ledger artifacts.

For feedback passes after prover/resource attempts, the request packet now also
includes `context_packet.feedback_loop_summary` when residual, refinement,
route-revision, or interactive-session evidence is present. This summary is a
derived route-repair brief: residual-goal count and text, evidence-row counts,
acceptance/source/coverage status counts, replan flags, repair-focus strings,
admissible source refs and formal declarations, realization-coverage witness
summaries, and bounded recommended next actions. Incomplete realization coverage
adds explicit repair actions for missing formal realization nodes or missing
route-alignment edges. It does not replace raw rows and is not proof evidence;
it gives the LLM planner a compact view of what changed and what still needs
search, library grounding, proof-state feedback, or route revision.

Accepted LLM route-planner responses also materialize their bounded
`search_requests` as portable refinement work. A `literature` request becomes a
`literature_discovery` hook, a `formal_library` request becomes a
`lean_library_grounding` hook, and a `prover_feedback` request becomes a
`proof_state_feedback` hook. The accepted standalone seed records these hooks
and matching route-revision triggers under both route-level fields and
`replan_metadata`, so the standalone planner and refinement queue can dispatch
the requested work without parsing raw LLM text. The request remains planning
evidence only; its response must still enter through source grounding,
library-coverage, refinement-evidence, or prover-feedback ledgers before route
repair is accepted.
Accepted rows also carry `route_adoption_status` and
`route_adoption_blockers`. A row can satisfy the JSON/source/formal alignment
contract while still being `PENDING_REFINEMENT_BEFORE_ROUTE_ADOPTION` because it
asked for additional literature search, formal-library search, prover feedback,
planner next actions, or uncertainty review. Only
`READY_FOR_STANDALONE_REPLAY` means the route has no unresolved LLM-planner
handoff blockers under the current evidence bound. The standalone seed and each
standalone-plan `standalone_input_trace` preserve the same fields, so a public
consumer can filter adoption-ready route plans without reopening raw LLM
responses.
The response contract also rejects target-prover drift: any explicit
`target_prover_family` in the response payload, standalone route,
`replan_metadata`, or formal-realization nodes must match the request target
prover family, modulo accepted aliases such as Coq/Rocq. The standalone seed
still writes the request target explicitly, but mismatched LLM proposals are not
silently accepted and overwritten.
Formal-library reuse is likewise target-aware. The request context exposes a
legacy flat `available_formal_declarations` list containing declarations
compatible with the request target, plus structured
`available_formal_declaration_rows` with `declaration`,
`target_prover_family`, and source-field provenance. Response validation filters
candidate declarations through those structured rows when present, so a Rocq
route cannot cite a Lean-only declaration merely because both appeared in a
mixed library context.

For a paper supplement or external prover smoke test, the same public path can
be run as one command:

```bash
python3 -m ai_statistician.cli formalization-gap-planner-reuse-smoke \
  --input data/formalization_gap_planner_target_intake_example.json \
  --target-prover-family rocq \
  --out runs/current/formalization_gap_planner_reuse_smoke
```

The one-command smoke path has two separate LLM route-planner controls. The
initial theorem-route planner uses `--llm-route-planner-provider`, and the
post-feedback rerun over the route-replan seed, residual goals, and
interactive-session context uses `--feedback-llm-route-planner-provider`. Both
default to Anthropic/Claude staging with `--*-model-tier auto`, but they do not
call the API unless the matching `--*-invoke-provider` flag is set. The
reuse-smoke manifest records `staged_live_provider_prompt_no_api_call` versus
`live_provider_invoked`, plus the number of requested live provider calls and
the Haiku/Sonnet/Opus request-tier distribution. To run the second pass with
Claude after the deterministic residual/context stages have completed, use
`--feedback-llm-route-planner-provider anthropic
--feedback-llm-route-planner-invoke-provider`; Anthropic defaults to Claude
Sonnet 4.6 unless a model is supplied. Static or reviewed JSON responses can be
passed with the matching `--feedback-llm-route-planner-static-response-file` or
`--feedback-llm-route-planner-response-json` flags for no-cost reproducible
review.

The reuse-smoke manifest names both the route-replan standalone seed and its
`formalization_gap_planner_route_replan_standalone_seed.schema.json`, so an
external prover or planner team can discover and validate the next-round input
without importing AI Statistician internals. The seed carries the revised
informal DAG nodes, revised formal-realization DAG nodes, the legacy
`revised_lean_realization_dag_nodes` alias, and exact revised route-alignment
edges in each route and in its `replan_metadata`, and the
sidecar standalone-input schema publishes those optional route and metadata
fields for external validators. The publication-bundle audit reports
seed-alignment and seed-DAG preservation counters. It also names the cross-prover
target summary and `formalization_gap_planner_cross_prover_target_summary.schema.json`,
which tell non-Lean prover teams how to filter aggregate packet and response
JSONL files for their prover family. Each target-prover adapter packet also
enriches `standalone_input_trace` with `source_prover_family`,
`source_target_prover_family`, `target_prover_family`,
`target_library_snapshot_ref`, and `trace_target_projection`; the packet
validator rejects rows whose trace target does not match the packet's adapter
target. This keeps a Lean-origin route and a Rocq/Isabelle/Agda target replay
distinguishable inside the same publication bundle. Finally, it names
`contract/formalization_gap_planner_schema_catalog.json` and its schema from
the publication bundle so downstream consumers can discover every reusable
contract file from the smoke manifest. The same artifact map names
`formalization_gap_planner_prover_adapter_response.schema.json`, so external
prover teams can validate adapter responses before replay or promotion. The
interactive decision-policy rows in the smoke output are generated with the
component-resource registry attached, so their component ids, local-first
resources, frontier-escalation resources, and resource-contract ids are
populated and then rechecked by the publication-bundle audit. When no
`--ground-truth` file is supplied, the smoke command also writes a generated
`formalization_gap_planner_reuse_smoke_route_truth.json` derived from its
selected route so the evaluation and ablation schemas can be exercised in a
single command. That generated route truth is contract smoke data, not
independent publication evidence; pass a curated route-truth file for real
planner-quality metrics. The evaluation output also copies its exact route
truth input to `formalization_gap_planner_evaluation_ground_truth.json`, and
the publication bundle copies that file with the optional evaluation artifacts.
Its reproduction manifest includes a `run_evaluation` command that uses this
bundled evaluation truth when it is present, otherwise it falls back to the
bundle benchmark truth. The bundle audit checks that matched evaluation rows
resolve against the copied evaluation truth and that the recorded route,
delta, and existing-reuse ground-truth primitive fields match that copied file,
so a bundle cannot silently pair evaluation rows with a different route-truth
input. It exposes aggregate checked/valid counters for the copied truth file,
row-to-truth matches, and primitive-field consistency so downstream gates do
not need to scan every audit row.

Target intake extracts objects, assumptions, procedure, claim, theorem shape,
source refs, primitive seeds, and literature/Lean queries from a raw theorem
request. The standalone command accepts the resulting seed or a hand-authored
route JSON with coverage labels such as `exact_exists`, `wrapper_needed`,
`bridge_needed`, `source_port_needed`, and `new_theory_needed`. It emits the
same portable `goal_conditioned_minimal_formalization_plan_manifest.json`
consumed by the evaluation, refinement, prover-adapter, and publication-bundle
commands. The portable-plan audit validates schema identity, two-DAG structure,
AND/OR graph shape, work packets, interactive hooks, and absence of
kernel-proof claims. The library-coverage-map command exports one row per
selected primitive, mapping the informal route atom to the selected current
library realization candidate and classifying it as exact reuse, near reuse,
wrapper, bridge, source port, new theory, or unknown/unaligned. It writes
`formalization_gap_planner_library_coverage_map.jsonl` plus
`formalization_gap_planner_library_coverage_map_row.schema.json` so downstream
prover systems can inspect library coverage without parsing the full plan. The
primitive-action-queue command consumes that coverage map and writes
`formalization_gap_planner_primitive_action_queue.jsonl` plus
`formalization_gap_planner_primitive_action_queue_row.schema.json`: one
executable work order per selected primitive, with action kinds such as target
prover replay, compose existing declarations, write wrapper, prove bridge
lemma, source port, design new theory fragment, or rerun library alignment.
These are operational work orders and acceptance gates, not proof evidence. The
action-resource-plan command then joins those primitive work orders to the
component-resource registry and writes
`formalization_gap_planner_action_resource_plan.jsonl` plus
`formalization_gap_planner_action_resource_plan_row.schema.json`. Each row names
the planner components, local-first resources, frontier escalation tools,
adapter ids, aggregate resource contracts, per-resource request/response
contract maps, escalation triggers, stop conditions, and reproduction commands
needed for that primitive action.
This makes tool choice auditable for other prover ecosystems without turning
resource routing metadata into proof evidence. The resource-request-queue
command expands those rows into one dispatch packet per local-first or frontier
resource and writes `formalization_gap_planner_resource_request_queue.jsonl`
plus `formalization_gap_planner_resource_request_queue_row.schema.json`. Each
packet carries the primitive id, route id, component ids, resource id, request
phase, the resource-specific contract id and request/response fields, evidence
inputs, expected outputs, acceptance gate, stop conditions, an execution hint,
and the explicit proof boundary. It is the executable interface for literature
search, formal-source search, Lean-library lookup,
Lean/LSP/Lake/LeanDojo-style prover feedback, and cross-prover/publication
audits; it is still not theorem proof evidence. When both action-resource and
request-queue artifacts are bundled, the publication audit checks that each
request row resolves to its action-resource row and matches the selected
resource's contract map, so stale per-tool contract fields cannot silently pass
as schema-valid dispatch packets. Resource-request rows also carry a structured
`dispatch_spec` in both the row and nested `request_payload`, giving external
MCP/CLI runners a normalized dispatch kind, adapter surface, command, hint,
expected response artifact, and response-JSONL contract without importing AI
Statistician internals. The
resource-response-ledger command validates local or frontier resource outputs
against those request packets and writes
`formalization_gap_planner_resource_response_ledger.jsonl`,
`formalization_gap_planner_resource_response.schema.json`, and
`formalization_gap_planner_resource_response_ledger_row.schema.json`. Missing
responses are recorded as `AWAITING_RESOURCE_RESPONSE`, not failure; malformed
responses and `kernel_verified=true` claims are rejected in this adapter layer.
Accepted responses can add source refs, Lean declaration hits, coverage
updates, prover diagnostics, residual goals, or route-revision reasons, but
they remain planner feedback rather than theorem proof evidence. When bundled,
the publication audit checks that each ledger row resolves to its request row
and that matched plus missing response fields exactly account for that
resource request's response contract. Ledger rows also retain the request
`dispatch_spec` and structured `candidate_declaration_rows`, so response
provenance still names the adapter surface and formal-declaration target after
the original request packet has been consumed. Present responses that echo the
wrong resource, expected artifact, dispatch spec, or declaration provenance are
rejected before they can become accepted planner feedback. When supplied to the
route-revision overlay, accepted ledger rows with actionable feedback
become conservative non-proof overlay proposals while awaiting or rejected rows
do not change the route. When both artifacts are bundled, the publication
audit checks each overlay `resource_response_ledger:*` evidence reference
against an accepted, response-present, contract-valid ledger row and verifies
that the overlay's compact `applied_resource_response_traces` match the
bundled ledger rows, including dispatch and declaration-provenance context. The
minimal-delta audit checks structural cost accounting, selected-cut
consistency, `do_not_formalize_now` exclusions, work-packet scope, and obvious
same-target dominated route alternatives; it also writes
`formalization_gap_planner_minimal_delta_decisions.jsonl` plus
`formalization_gap_planner_minimal_delta_decision_row.schema.json` so external
users can inspect the exact costed cut decision per route. This is still not a
proof of semantic optimality. The source-grounding audit writes
`formalization_gap_planner_source_grounding_row.schema.json` beside its JSONL
so external users can validate every source-backed, source-search-pending,
formal-boundary, or unaccounted route-node row without importing this codebase.
When passed a refinement-evidence directory, the same audit also emits
`prover_residual_goal` rows for proof-state residuals. Those rows distinguish
source-backed residual side conditions from residuals that still need bounded
literature discovery or an explicit formal-gap boundary before route repair can
promote them into the next informal DAG.
The reuse-smoke command orchestrates target intake,
standalone planning, portable-plan audit, library-coverage map,
primitive-action queue, minimal-delta audit, source-grounding audit,
evaluation, prover-adapter packets,
deterministic refinement responses, refinement
adapter registry, adapter-registry audit, component-resource registry,
component-resource registry audit, action-resource plan, resource-request
queue, resource-response ledger, local
literature/formal-source/proof-state adapter fallbacks, evidence,
route-revision overlay, route-stability audit, route-replan handoff,
route-replan handoff audit, proof-state triage,
interactive session with component/resource contract links, ablation study,
cross-prover matrix audit, publication bundle export, and
bundle audit under one output directory while preserving the same proof-boundary
discipline. The bundled reproduction manifest includes the route-replan
handoff, handoff audit, and proof-state triage commands; when those optional
artifacts are included, the bundle audit also checks that revised route
revision overlay rows satisfy the published row schema, route-alignment counts
and resource-response-ledger proposal counts remain consistent, revised route
alignment edges survive handoff and standalone-planner roundtrip, and applied
proposal/evidence ids, hook kinds, prover diagnostics, source refs, and Lean
declaration hits survive from packaged handoff rows into the standalone seed
metadata.

Planner quality can be scored against a curated or held-out theorem-route file:

```bash
python3 -m ai_statistician.cli formalization-gap-planner-benchmark \
  --out runs/current/formalization_gap_planner_benchmark

python3 -m ai_statistician.cli formalization-gap-planner-benchmark-audit \
  --formalization-gap-planner-benchmark-dir runs/current/formalization_gap_planner_benchmark \
  --out runs/current/formalization_gap_planner_benchmark_audit

python3 -m ai_statistician.cli formalization-gap-planner-adapter-registry \
  --lean-rag-db runs/current_status_lean_rag_dependency_graph/stat_inference.sqlite \
  --out runs/current/formalization_gap_planner_adapter_registry

python3 -m ai_statistician.cli formalization-gap-planner-adapter-registry-audit \
  --formalization-gap-planner-adapter-registry-dir runs/current/formalization_gap_planner_adapter_registry \
  --out runs/current/formalization_gap_planner_adapter_registry_audit

python3 -m ai_statistician.cli formalization-gap-planner-component-resource-registry \
  --formalization-gap-planner-adapter-registry-dir runs/current/formalization_gap_planner_adapter_registry \
  --out runs/current/formalization_gap_planner_component_resource_registry

python3 -m ai_statistician.cli formalization-gap-planner-component-resource-registry-audit \
  --formalization-gap-planner-component-resource-registry-dir runs/current/formalization_gap_planner_component_resource_registry \
  --out runs/current/formalization_gap_planner_component_resource_registry_audit

python3 -m ai_statistician.cli formalization-gap-planner-action-resource-plan \
  --formalization-gap-planner-primitive-action-queue-dir runs/current/formalization_gap_planner_primitive_action_queue \
  --formalization-gap-planner-component-resource-registry-dir runs/current/formalization_gap_planner_component_resource_registry \
  --out runs/current/formalization_gap_planner_action_resource_plan

python3 -m ai_statistician.cli formalization-gap-planner-resource-request-queue \
  --formalization-gap-planner-action-resource-plan-dir runs/current/formalization_gap_planner_action_resource_plan \
  --out runs/current/formalization_gap_planner_resource_request_queue

python3 -m ai_statistician.cli formalization-gap-planner-resource-response-ledger \
  --formalization-gap-planner-resource-request-queue-dir runs/current/formalization_gap_planner_resource_request_queue \
  --out runs/current/formalization_gap_planner_resource_response_ledger

python3 -m ai_statistician.cli formalization-gap-planner-evaluation \
  --goal-conditioned-minimal-formalization-plan-dir runs/current/goal_conditioned_minimal_formalization_plan \
  --ground-truth runs/current/formalization_gap_planner_benchmark/formalization_gap_planner_ground_truth.json \
  --out runs/current/formalization_gap_planner_evaluation
```

The repo ships a reusable default route-truth file at
`data/formalization_gap_planner_ground_truth.json`. The benchmark export command
writes a versioned manifest, JSONL route summary, markdown report, and a copy of
that ground-truth file for publication artifacts. It also writes
`formalization_gap_planner_benchmark_route.schema.json` and schema-valid counts
for every route-truth row, so external benchmark users can validate the label
contract without importing this repository. The benchmark-audit command
checks that route-truth examples have source references, distinct theorem
families, required/existing/delta primitive consistency, coverage-label
discipline, held-out/public split metadata, and explicit proof-boundary text.
The evaluation writes row-level route recall/precision, Lean-delta
precision/recall, existing-library reuse precision/recall, coverage-label
accuracy, two-DAG readiness, selected-primitive alignment coverage,
feedback-loop readiness, and the proof-boundary check. It writes
`formalization_gap_planner_evaluation_row.schema.json`,
`formalization_gap_planner_evaluation_ground_truth.json`, and row schema-valid
counts for those diagnostics. These scores are
benchmark evidence about planning quality, not theorem proof evidence.

The ablation study compares the observed planner with counterfactual
`no_literature_evidence`, `no_lean_grounding`, `no_proof_state_feedback`, and
`no_route_planner` variants. It is a diagnostic for which signal families matter
for route recall, Lean-delta recall, reuse, feedback readiness, and
route-adoption readiness under the current evidence bound; it is not theorem
proof evidence. `research-system-audit` promotes the evaluation and ablation
route-adoption counts into its top-level `counts` payload so AI Statistician
runs can be filtered by adoption readiness without parsing nested planner
artifacts. The publication-bundle audit recomputes the ablation
`largest_route_adoption_ready_drop_variant` from packaged JSONL rows and rejects
bundles whose manifest-level route-adoption aggregate drifts from those rows.

The adapter registry command records which refinement tools can satisfy each
hook, which response fields they must emit, and whether local commands,
packages, credentials, or configured paths are present. Built-in offline
adapters should be ready in a normal checkout; live Paperclip/PaperQA/OpenScholar,
LeanSearch/Loogle/LeanExplore/local Lean RAG, Lean/LSP, and LeanDojo-style
adapters may report `NEEDS_INSTALL`, `NEEDS_CREDENTIALS`, or
`NEEDS_CONFIGURATION` until configured. Registry rows are integration readiness
evidence, not proof evidence. The command also writes
`formalization_gap_planner_adapter_registry_row.schema.json` and row
schema-valid counts so external users can validate the frontier-tool/MCP
inventory without importing this repository.
The adapter-registry audit validates that the registry covers the required
literature, formal-library, proof-state, route-revision, offline-regression,
and cross-prover reuse surfaces; it also checks response fields, resource URLs,
portability targets, adapter-registry JSONL row schema conformance, and
proof-boundary discipline.
The component-resource registry sits one level above adapters: it maps target
intake, literature route synthesis, informal DAG decomposition, formal-library
coverage, minimal-delta planning, prover feedback, route revision, and
cross-prover publication to local fallbacks and frontier tools such as
Paperclip/PaperQA/OpenScholar, LeanSearch/Loogle/LeanExplore, Lean/LSP,
LeanDojo/ReProver, Rocq LSP/SerAPI, Isabelle/Sledgehammer, and Agda
Search/Auto surfaces. It also emits one execution-plan row per planner
component with local-first resources, frontier escalation resources, adapter
ids, evidence inputs, expected outputs, escalation triggers, and stop
conditions. Resource rows include `capability_tags` and `validation_signals`,
component rows include `required_quality_signals`, execution-plan rows include
`quality_gates`, and resource-contract rows include
`response_validation_signals`. These fields make local-first/frontier
escalation auditable: a source-search tool must return source refs or explicit
literature gaps, a library-search tool must return formal hits or coverage
updates, and a prover-feedback tool must return diagnostics or residuals
without promoting proof claims. It now also emits one resource-contract row per
local fallback, frontier tool, MCP surface, or prover resource, recording the
request fields, response fields, deployment requirements, output artifact kind,
escalation policy, and acceptance gate. Its audit checks architecture,
execution-plan coverage, quality gates, and resource request/response contracts
only; it is not a claim that any tool response is correct or any theorem is
proved. Publication bundles include JSON Schemas for execution-plan rows and
resource-contract rows so external systems can validate the
local-first/frontier-escalation plan and frontier-tool/prover-resource
contracts without importing AI Statistician code.
The action-resource-plan command is the per-primitive join over this registry:
`target_prover_replay` actions use cross-prover publication and prover-feedback
resources, `prove_bridge_lemma` actions use formal-library coverage,
minimal-delta, and prover-feedback resources, and `source_port` actions use
literature synthesis, informal DAG decomposition, and formal-library coverage
resources. Every exported row carries local-first resources, frontier
escalation resources, adapter ids, resource-contract ids, request fields,
response fields, stop conditions, and proof-boundary text. This is the
planner's concrete answer to which frontier tools or MCPs a primitive action
should use, while still deferring proof acceptance to target-prover replay.

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

python3 -m ai_statistician.cli formalization-gap-planner-local-literature-adapter \
  --formalization-gap-planner-refinement-queue-dir runs/current/formalization_gap_planner_refinement_queue \
  --base-response-jsonl runs/current/formalization_gap_planner_refinement_adapter/formalization_gap_planner_refinement_evidence_responses.jsonl \
  --literature-root /path/to/local/paper_or_text_corpus \
  --out runs/current/formalization_gap_planner_local_literature_adapter

python3 -m ai_statistician.cli formalization-gap-planner-local-formal-source-adapter \
  --formalization-gap-planner-refinement-queue-dir runs/current/formalization_gap_planner_refinement_queue \
  --base-response-jsonl runs/current/formalization_gap_planner_local_literature_adapter/formalization_gap_planner_refinement_evidence_responses.jsonl \
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
  --formalization-gap-planner-resource-response-ledger-dir runs/current/formalization_gap_planner_resource_response_ledger \
  --out runs/current/formalization_gap_planner_route_revision_overlay

python3 -m ai_statistician.cli formalization-gap-planner-route-stability-audit \
  --goal-conditioned-minimal-formalization-plan-dir runs/current/goal_conditioned_minimal_formalization_plan \
  --formalization-gap-planner-refinement-evidence-dir runs/current/formalization_gap_planner_refinement_evidence \
  --formalization-gap-planner-route-revision-overlay-dir runs/current/formalization_gap_planner_route_revision_overlay \
  --out runs/current/formalization_gap_planner_route_stability_audit

python3 -m ai_statistician.cli formalization-gap-planner-route-replan-handoff \
  --goal-conditioned-minimal-formalization-plan-dir runs/current/goal_conditioned_minimal_formalization_plan \
  --formalization-gap-planner-route-revision-overlay-dir runs/current/formalization_gap_planner_route_revision_overlay \
  --formalization-gap-planner-route-stability-audit-dir runs/current/formalization_gap_planner_route_stability_audit \
  --out runs/current/formalization_gap_planner_route_replan_handoff

python3 -m ai_statistician.cli formalization-gap-planner-route-replan-handoff-audit \
  --formalization-gap-planner-route-replan-handoff-dir runs/current/formalization_gap_planner_route_replan_handoff \
  --out runs/current/formalization_gap_planner_route_replan_handoff_audit

python3 -m ai_statistician.cli formalization-gap-planner-proof-state-triage \
  --formalization-gap-planner-route-revision-overlay-dir runs/current/formalization_gap_planner_route_revision_overlay \
  --out runs/current/formalization_gap_planner_proof_state_triage

python3 -m ai_statistician.cli formalization-gap-planner-interactive-session \
  --goal-conditioned-minimal-formalization-plan-dir runs/current/goal_conditioned_minimal_formalization_plan \
  --formalization-gap-planner-refinement-queue-dir runs/current/formalization_gap_planner_refinement_queue \
  --formalization-gap-planner-refinement-evidence-dir runs/current/formalization_gap_planner_refinement_evidence \
  --formalization-gap-planner-route-stability-audit-dir runs/current/formalization_gap_planner_route_stability_audit \
  --formalization-gap-planner-route-replan-handoff-dir runs/current/formalization_gap_planner_route_replan_handoff \
  --formalization-gap-planner-proof-state-triage-dir runs/current/formalization_gap_planner_proof_state_triage \
  --formalization-gap-planner-component-resource-registry-dir runs/current/formalization_gap_planner_component_resource_registry \
  --out runs/current/formalization_gap_planner_interactive_session

python3 -m ai_statistician.cli formalization-gap-planner-ablation-study \
  --goal-conditioned-minimal-formalization-plan-dir runs/current/goal_conditioned_minimal_formalization_plan \
  --formalization-gap-planner-evaluation-dir runs/current/formalization_gap_planner_evaluation \
  --formalization-gap-planner-interactive-session-dir runs/current/formalization_gap_planner_interactive_session \
  --out runs/current/formalization_gap_planner_ablation_study

python3 -m ai_statistician.cli formalization-gap-planner-prover-adapter-contract \
  --goal-conditioned-minimal-formalization-plan-dir runs/current/goal_conditioned_minimal_formalization_plan \
  --target-prover-family rocq \
  --library-snapshot-ref rocq_snapshot_identifier \
  --out runs/current/formalization_gap_planner_prover_adapter_contract

python3 -m ai_statistician.cli formalization-gap-planner-cross-prover-matrix-audit \
  --goal-conditioned-minimal-formalization-plan-dir runs/current/goal_conditioned_minimal_formalization_plan \
  --out runs/current/formalization_gap_planner_cross_prover_matrix_audit

python3 -m ai_statistician.cli formalization-gap-planner-publication-bundle \
  --paper-library-dir /path/to/local/paper_or_text_corpus \
  --lean-rag-db runs/current_status_lean_rag_dependency_graph/stat_inference.sqlite \
  --formalization-gap-planner-target-intake-dir runs/current/formalization_gap_planner_target_intake \
  --goal-conditioned-minimal-formalization-plan-dir runs/current/goal_conditioned_minimal_formalization_plan \
  --formalization-gap-planner-evaluation-dir runs/current/formalization_gap_planner_evaluation \
  --formalization-gap-planner-ablation-study-dir runs/current/formalization_gap_planner_ablation_study \
  --formalization-gap-planner-portable-plan-audit-dir runs/current/formalization_gap_planner_portable_plan_audit \
  --formalization-gap-planner-library-coverage-map-dir runs/current/formalization_gap_planner_library_coverage_map \
  --formalization-gap-planner-primitive-action-queue-dir runs/current/formalization_gap_planner_primitive_action_queue \
  --formalization-gap-planner-action-resource-plan-dir runs/current/formalization_gap_planner_action_resource_plan \
  --formalization-gap-planner-resource-request-queue-dir runs/current/formalization_gap_planner_resource_request_queue \
  --formalization-gap-planner-resource-response-ledger-dir runs/current/formalization_gap_planner_resource_response_ledger \
  --formalization-gap-planner-minimal-delta-audit-dir runs/current/formalization_gap_planner_minimal_delta_audit \
  --formalization-gap-planner-source-grounding-audit-dir runs/current/formalization_gap_planner_source_grounding_audit \
  --formalization-gap-planner-refinement-queue-dir runs/current/formalization_gap_planner_refinement_queue \
  --formalization-gap-planner-refinement-adapter-dir runs/current/formalization_gap_planner_refinement_adapter \
  --formalization-gap-planner-local-literature-adapter-dir runs/current/formalization_gap_planner_local_literature_adapter \
  --formalization-gap-planner-local-formal-source-adapter-dir runs/current/formalization_gap_planner_local_formal_source_adapter \
  --formalization-gap-planner-local-proof-state-adapter-dir runs/current/formalization_gap_planner_local_proof_state_adapter \
  --formalization-gap-planner-refinement-evidence-dir runs/current/formalization_gap_planner_refinement_evidence \
  --formalization-gap-planner-route-revision-overlay-dir runs/current/formalization_gap_planner_route_revision_overlay \
  --formalization-gap-planner-route-stability-audit-dir runs/current/formalization_gap_planner_route_stability_audit \
  --formalization-gap-planner-route-replan-handoff-dir runs/current/formalization_gap_planner_route_replan_handoff \
  --formalization-gap-planner-route-replan-handoff-audit-dir runs/current/formalization_gap_planner_route_replan_handoff_audit \
  --formalization-gap-planner-proof-state-triage-dir runs/current/formalization_gap_planner_proof_state_triage \
  --formalization-gap-planner-interactive-session-dir runs/current/formalization_gap_planner_interactive_session \
  --formalization-gap-planner-prover-adapter-contract-dir runs/current/formalization_gap_planner_prover_adapter_contract \
  --formalization-gap-planner-cross-prover-matrix-audit-dir runs/current/formalization_gap_planner_cross_prover_matrix_audit \
  --formalization-gap-planner-adapter-registry-audit-dir runs/current/formalization_gap_planner_adapter_registry_audit \
  --formalization-gap-planner-component-resource-registry-audit-dir runs/current/formalization_gap_planner_component_resource_registry_audit \
  --out runs/current/formalization_gap_planner_publication_bundle

python3 -m ai_statistician.cli formalization-gap-planner-publication-bundle-audit \
  --publication-bundle-dir runs/current/formalization_gap_planner_publication_bundle \
  --out runs/current/formalization_gap_planner_publication_bundle_audit
```

This queue routes each theorem plan into literature discovery, Lean-library
grounding, proof-state feedback, and route-revision items. Optional evaluation
and replay-calibration manifests add route-truth mismatches and prover residuals
as prioritization signals. The adapter command is a deterministic offline
producer that turns the shipped route-truth labels into response JSONL for local
end-to-end tests and writes the shared refinement-tool response schema plus
schema-valid counts beside that JSONL. The local literature adapter can replace
`literature_discovery` rows with source-backed route evidence from a local
text/markdown/json corpus or mark focused literature gaps for later
Paperclip/PaperQA/OpenScholar search. The local formal-source adapter can then
replace
`lean_library_grounding` rows with real declaration-search evidence from the
current formal-source backend and optional Lean RAG dependency DB, while
preserving other adapter responses. The local proof-state adapter can then
replace `proof_state_feedback` rows with local Lean diagnostics, blocks
`sorry`/`admit`/`axiom` skeletons before invocation, reports name-only or
otherwise non-Lean skeletons as statement-materialization gaps, and merges
residual goals into the same evidence JSONL. Live Paperclip/PaperQA/OpenScholar,
LeanSearch/Loogle/LeanExplore, and Lean/LSP/prover adapters should emit the
same response contract. Each local adapter also writes
`formalization_gap_planner_refinement_tool_response.schema.json` beside its
local-only and merged response JSONL files, plus local and merged
schema-valid counts in its manifest, so adapter outputs are self-describing
before they enter the evidence aggregator. The evidence command validates tool
responses keyed by `refinement_item_id` and emits route-revision proposals. The overlay command
applies those proposals back to matching route plans without mutating the
original manifest, recording changed primitives, revised DAG nodes, residual
goals, source refs, revised informal-to-realization alignment edges, and the
next required replay gate. The route-replan handoff
command converts that overlay plus the stability decision into
`formalization_gap_planner_route_replan_standalone_seed.json`, which can be fed
back into `formalization-gap-planner-standalone-plan` for the next planning
round. It also writes
`formalization_gap_planner_route_replan_standalone_seed.schema.json` beside the
seed so a downloaded handoff is a self-describing standalone planner input; the
schema includes optional replan metadata fields for revised DAG nodes,
alignment edges, applied feedback ids, resource-response traces, pending or
rejected resource-response request ids, prover diagnostics, source refs, and
Lean declaration hits. The standalone planner copies that seed provenance into
each roundtrip goal-plan row as `standalone_input_trace`, so later prover queues
can recover which overlay, resource-response-ledger row, prover diagnostic, and
revised DAG/alignment payload shaped the route. The
handoff audit checks that schema id, checks the seed, verifies exact
row-to-seed preservation of revised alignment edges and revised informal/Lean
DAG nodes, rejects promoted proof claims, and runs a standalone planner
round-trip that must preserve `standalone_input_trace`; this is replayability
evidence, not theorem proof evidence. The proof-state triage command turns overlay-level prover statuses into
ranked work items for statement materialization, local Lean repair, or
environment configuration.
The interactive-session command joins the plan, refinement queue, evidence,
stability audit, replan handoff, and proof-state triage into one route-level
ledger of next bounded actions: run literature search, Lean grounding,
proof-state feedback, replan, or target-prover replay. It also writes
`formalization_gap_planner_interactive_decision_policy.jsonl` and
`formalization_gap_planner_interactive_decision_policy_row.schema.json`, which
record the trigger signals, evidence inputs, required tool contracts, concrete
component-resource ids, local-first resources, frontier-escalation resources,
resource-contract ids, required quality signals, execution quality gates,
response-validation signals, stop conditions, and fallbacks explaining why that
next action is bounded and appropriate. If no component-resource registry is
provided, the decision-policy rows still validate but leave the concrete
resource and quality-gate fields empty.
Those session and decision-policy rows can be passed back into
`formalization_gap_planner_llm_route_planner`, so the next LLM route-planning
packet sees the current bounded interaction state, selected tools, quality
gates, stop conditions, and fallback actions rather than replanning from only
static route artifacts.
Literature, Lean-search, prover-diagnostic responses, revision overlays,
proof-state triage rows, interactive-session rows, and decision-policy rows are
route evidence only.
The prover-adapter contract command turns portable work packets into
target-prover mapping packets for Lean, Rocq/Coq, Isabelle, Agda, or another
ecosystem, and validates adapter responses without accepting kernel-proof
claims in the mapping layer. It publishes both
`formalization_gap_planner_prover_adapter_packet.schema.json` and
`formalization_gap_planner_prover_adapter_response_validation_row.schema.json`
with schema-valid counts, so downstream prover adapters can validate requested
work packets and replay-response validation rows without importing this repo.
The cross-prover matrix audit reruns that packet export for the declared public
reuse targets, currently Lean4, Rocq, Isabelle, and Agda, checks packet-count
consistency, verifies that every target packet still carries both route
alignment and `standalone_input_trace` provenance, aggregates target-specific
packet JSONL, and preserves the same proof-boundary discipline. It also
publishes and validates the matrix-row schema, the aggregated prover-adapter
packet schema, and the aggregated response-validation row schema beside the
cross-prover JSONL files.
The publication bundle command packages the portable schema, contract,
prover-adapter packet/response-validation schemas, cross-prover matrix-row
schema, cross-prover target-summary schema, refinement work-item and
tool-response schemas, interactive next-action and decision-policy row schemas,
component execution-plan schema,
component-resource row schemas, component-resource contract-row schema,
library-coverage map row schema, primitive-action queue row schema,
action-resource plan row schema, resource-request queue row schema,
resource-response schema, resource-response-ledger row schema,
source-grounding row schema, route-revision overlay, route-replan handoff, and
route-replan handoff-audit row schemas,
benchmark route-row schema, evaluation row schema, benchmark,
benchmark audit, adapter registry, docs, and optional run artifacts into a
reusable directory for paper supplements or downstream prover adapters; it also writes
`contract/formalization_gap_planner_schema_catalog.json` and its JSON Schema as
a machine-readable index of the reusable contract and schema files. The Python
API exposes `schema_catalog_json_schema()` and `validate_schema_catalog_payload()`
so downstream consumers can validate the index directly, including
bundle-local relative-path resolution when they have the exported bundle, plus
`reproduce/formalization_gap_planner_reproduction_manifest.json` with
bundle-relative artifacts, entry points, and commands for external reuse. The
manifest includes the standalone planner path and the refinement rerun path:
queue export, resource-request queue export, resource-response ledger export,
deterministic adapter responses,
local literature adapter, local
formal-source adapter, local proof-state adapter, refinement-evidence
aggregation, route-revision overlay, route-stability audit, interactive
session export, and feedback LLM route-planner rerun with interactive-session
context.
session summary. It also includes
`examples/formalization_gap_planner_standalone_example.json` and
`examples/formalization_gap_planner_target_intake_example.json` so downstream
users can run the public path immediately after replacing local corpus,
formal-source, Lean-RAG, and Lake-project placeholders. The bundle is still not
proof evidence. The publication-bundle audit
then checks the bundle is self-contained, schema-consistent, has the required
adapter registry, benchmark, benchmark-audit, and reproduction artifacts,
includes the published planner/prover/refinement/component/benchmark/evaluation
schemas, validates the schema catalog and its bundle-relative paths, validates optional deterministic and local adapter JSONL rows against
the shared refinement-tool response schema when those artifacts are packaged, and
validates optional library-coverage map, prover-adapter, and cross-prover
matrix rows against their published schemas when those artifacts are packaged.
It also validates optional target-intake rows against the published
target-intake row schema, standalone seed contracts, packaged goal-plan rows
against the published gap-plan row schema, minimal-delta decision rows,
source-grounding rows, refinement work-item rows, adapter-registry audit checks, and
component-resource-registry audit checks against their public contracts or
schemas. For optional interactive-session artifacts, it resolves
decision-policy component ids, local/frontier resource ids, and
resource-contract ids against the bundled component-resource registry. It also
checks resource-request payload identity and dispatch specs, resource-response
ledger rows against their request contracts, route-revision
resource-response-ledger traces, route-stability awaiting/rejected request ids,
and interactive-session next-command guidance against the same request ids.
`research-system-audit` republishes these counts so the integrated AI
Statistician run and the standalone reusable component expose the same drift
signals. Manifest counts and proof-boundary text are checked, and the
proof-evidence boundary is preserved.

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

- `formal_realization_dag_nodes` / `formal_realization_dag_edges`
  Current-library reuse, near matches, wrappers, bridge lemmas, source ports,
  new primitives, and excluded alternatives. `lean_realization_dag_nodes`
  remains a legacy alias for Lean-oriented clients; prover-generic artifacts
  should prefer the `formal_*` field names.

- `route_alignment_edges`
  Explicit links from informal semantic atoms to formal realization candidates.
  Each selected primitive should have one of these edges before the route is
  handed to a prover adapter; the portable-plan audit checks the edge source
  and target nodes and rejects missing selected-primitive alignments. The
  standalone planner and portable-plan audit also write
  `formalization_gap_planner_route_alignment_edge.schema.json`, so external
  prover adapters can validate these links independently of the full plan
  manifest.

The portable-plan audit also writes
`formalization_gap_planner_portable_plan_audit_row.schema.json` and records
`n_row_schema_valid` / `n_row_schema_invalid`, so external systems can validate
the audit JSONL itself before using its route diagnostics.

The library-coverage map writes
`formalization_gap_planner_library_coverage_map_row.schema.json` and records
`n_coverage_rows`, coverage-bucket counts, `n_rows_with_alignment`, and row
schema-valid counts. This is the compact artifact for deciding which selected
route primitives are already covered by the current library and which require a
wrapper, bridge lemma, source port, or new theory before prover replay.
Rows keep the legacy flat `candidate_declarations` list for simple consumers,
and also publish `candidate_declaration_rows` with `declaration`,
`target_prover_family`, and `source_field` so external Lean/Rocq/Isabelle/Agda
adapters do not have to infer declaration provenance from strings.
The primitive-action queue carries the same structured declaration rows into
target-prover work orders, so replay workers can validate prover-family
compatibility without reopening the full coverage-map manifest.
Action-resource plans and resource-request dispatch payloads preserve those
rows as well, which keeps MCP/CLI requests self-contained for external prover
workers and publication-bundle replay.

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
- `informal_knowledge_dag_nodes` and `formal_realization_dag_nodes`: the two
  aligned route DAGs. `lean_realization_dag_nodes` is accepted as a backward
  compatible alias for existing Lean-specific artifacts.
- `route_alignment_edges`: source/target links proving which informal route
  atoms correspond to exact reuse, wrappers, bridges, source ports, or new
  formalization candidates in the realization DAG.
- `route_revision_triggers`: residual-goal, source-gap, or first-principles
  risk events that should revise the route.
- `next_work_packets`: bounded prover work items with source and kernel gates.

The same shape can be adapted to Lean, Rocq/Coq, Isabelle, Agda, or a mixed
symbolic/statistical verifier, as long as the adapter can assign costs to
existing reuse and missing formalization work. Prover-adapter packets preserve
the relevant `route_alignment_edge` for each primitive, so a target-prover
adapter can see which informal semantic atom and Lean realization candidate it
is translating.

Every run also writes
`library_aware_formalization_gap_plan.schema.json` and
`library_aware_formalization_gap_plan_row.schema.json` for JSONL row consumers,
plus `formalization_gap_planner_route_alignment_edge.schema.json`. The full
plan schema id is:

```text
urn:ai-statistician:schemas:library-aware-formalization-gap-plan:1
```

The gap-plan JSONL row schema id is:

```text
urn:ai-statistician:schemas:library-aware-formalization-gap-plan-row:1
```

The route-alignment edge schema id is:

```text
urn:ai-statistician:schemas:formalization-gap-planner-route-alignment-edge:1
```

The library-coverage map row schema id is:

```text
urn:ai-statistician:schemas:formalization-gap-planner-library-coverage-map-row:1
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
   the Lean realization DAG, explicit informal-to-realization alignment edges,
   route revision triggers, and AND/OR route view.

4. `formalization_gap_planner_target_intake`
   Normalizes a raw theorem request into objects, assumptions, procedure,
   claim, theorem shape, source refs, primitive seeds, and literature/Lean
   grounding queries. It also emits a standalone planner seed. This is target
   intake only, not route evidence or proof evidence.

5. `formalization_gap_planner_llm_route_planner`
   Builds the LLM planning request packet from a standalone target route plus
   optional source, coverage, resource-response, refinement-evidence,
   route-revision, prover-residual, interactive-session, and decision-policy
   context. Resource-response ledger rows include bounded response summaries,
   source snippets or payload excerpts, response artifacts, contract status,
   route-evidence nodes, coverage updates, and residual goals, so a feedback
   LLM pass can revise from actual literature/tool evidence rather than only
   audit counters. The request packet also exposes `available_source_refs` and
   `available_formal_declarations`, and accepted LLM responses may cite only
   those source refs and formal declarations. If a needed source or declaration
   is missing from the evidence packet, the LLM must emit a bounded literature
   or formal-library `search_request` rather than inventing a citation id or
   claiming unsupported library coverage. Residual interpretations are also
   evidence-bounded: they may cover only residual goals listed in the request
   packet, and when request residuals are present every residual must receive
   an interpretation plus a `route_repair` or `repair_action`. It can run in
   prompt-only mode, validate a reviewed/static LLM JSON response, or invoke a
   configured generator backend. Accepted responses produce a revised
   standalone seed with source-grounded informal DAG nodes, formal realization
   nodes, alignment rationales, minimal-delta rationale, search requests, and
   the proof-evidence boundary. The accepted LLM DAG, route-alignment edges,
   minimal-delta plan, search requests, residual interpretations, and provider
   provenance are also copied into the seed route's `replan_metadata`, so the
   standalone planner trace and source-grounding audit can inspect the LLM
   route instead of losing it at handoff. The publication-bundle audit now
   checks accepted LLM rows against both their request packets and the packaged
   standalone seed, including row-id provenance, provider/model/request
   metadata, source refs, formal declarations, residual-goal coverage,
   introduced-primitive evidence bounds, minimal-delta metadata, revised
   informal/formal-realization DAG nodes, realization-coverage witnesses, and
   normalized alignment edges for both primary and feedback LLM route-planner
   artifacts. Evaluation manifests also summarize route-adoption readiness
   (`READY_FOR_STANDALONE_REPLAY`,
   `PENDING_REFINEMENT_BEFORE_ROUTE_ADOPTION`, awaiting, and rejected) plus the
   blocker counts that explain why an accepted LLM route still needs another
   literature/library/prover-feedback pass. The publication-bundle audit
   recomputes those readiness aggregates from packaged evaluation JSONL rows and
   rejects bundles whose evaluation manifest silently drops or rewrites them.
   Accepted responses must also satisfy primitive-set coherence: selected
   primitives must appear in the standalone route and formal-realization DAG,
   and wrapper/bridge/source-port/new-theory delta primitives must have
   route-alignment edges. New selected or delta primitives that were not already
   present in the target route or context packet must be justified by an
   aligned informal DAG node with grounded source evidence, a matching bounded
   literature search request, or an explicit formal-gap boundary; internally
   coherent but unsupported primitive invention is rejected before seed
   generation. Its public row schema defines a structured
   `realization_coverage_witness`, so bundle consumers can validate selected,
   delta, introduced, and aligned primitive coverage without relying on
   free-form row text. If a component-resource registry directory is supplied, request
   packets also include a bounded `component_resource_registry_context` with
   compatible resources, execution plans, and response contracts. That context
   is planner guidance only; it cannot justify source-backed claims, formal
   declaration reuse, or residual interpretations without corresponding
   evidence rows. This is the main intelligence boundary for route synthesis
   and repair; it is not theorem proof evidence.

6. `formalization_gap_planner_standalone_plan`
   Builds the same portable planner manifest from standalone theorem-route JSON
   containing a target prover family, library snapshot reference, primitive
   coverage labels, source references, and candidate declarations. Downstream
   library-coverage artifacts re-emit those declarations as target-aware
   `candidate_declaration_rows`. This is the independent reuse entry point for
   systems that do not run the AI Statistician audit pipeline.

7. `formalization_gap_planner_portable_plan_audit`
   Validates any portable planner manifest before downstream reuse. It checks
   schema identity, proof-boundary discipline, two-DAG and AND/OR graph
   presence, selected-primitive alignment edges, work-packet gates,
   interactive hooks, and rejects kernel-proof claims in the planning layer.
   The audit JSONL is self-contained: each check row carries its proof-boundary
   status and is validated against
   `formalization_gap_planner_portable_plan_audit_row.schema.json`.
   The companion `formalization_gap_planner_library_coverage_map` command
   exports a smaller per-primitive coverage table from the same manifest. Each
   row aligns one selected informal primitive to a current-library realization
   candidate and records the next formalization action class under the published
   library-coverage-map row schema.
   The companion `formalization_gap_planner_primitive_action_queue` command
   turns those coverage rows into primitive-level work orders with action kind,
   owner, priority, tools, acceptance gate, and expected outputs under the
   published primitive-action-queue row schema.

8. `formalization_gap_planner_adapter_registry`
   Records the live/offline adapter inventory, preflight readiness, output
   response contracts, row schema, and proof-evidence boundary for literature,
   Lean grounding, proof feedback, and route revision.

9. `formalization_gap_planner_adapter_registry_audit`
   Validates required frontier-tool coverage, response contract fields,
   resource links, prover-family portability, adapter-row schema conformance,
   and proof-boundary discipline for the adapter registry.

10. `formalization_gap_planner_component_resource_registry`
   Records the architecture-level mapping from planner components to local
   fallbacks, frontier resources, MCP/CLI surfaces, cross-prover resources, and
   integration contract fields. It also exports deterministic execution-plan
   rows that tell external users which local resources to try first, when to
   escalate to frontier tools, and which outputs stop the stage. It also
   exports one resource-contract row per tool/resource with request fields,
   response fields, deployment requirements, and acceptance gates. Publication
   bundles ship schemas for resource rows, component-resource rows,
   execution-plan rows, and resource-contract rows. This is the auditable
   answer to which tools each component should use; it is not tool output or
   proof evidence.

11. `formalization_gap_planner_component_resource_registry_audit`
   Validates that every planner component has a local fallback, frontier
   resources, contract fields, execution-plan coverage, resource-contract
   coverage, cross-prover reuse targets, resource links, proof-boundary
   discipline, and resource, component-resource, execution-plan, and
   resource-contract row conformance to the published JSON Schemas.
   The downstream `formalization_gap_planner_action_resource_plan` export then
   joins primitive action-queue rows to those component resources and contracts,
   producing one local-first/frontier-escalation resource plan per primitive
   action under
   `formalization_gap_planner_action_resource_plan_row.schema.json`.

12. `formalization_gap_planner_resource_request_queue`
   Expands each action-resource plan into per-resource dispatch packets for
   local-first and frontier resources. Rows carry the primitive id, route id,
   resource id, phase, the exact contract id and request/response fields for
   that resource, execution hint, structured `dispatch_spec`, acceptance gate,
   stop conditions, and proof-boundary text. The nested `request_payload` is
   self-contained: it includes the generated `resource_request_id`, request
   rank, expected response artifact, response-contract fields, and dispatch
   spec an external MCP/CLI adapter needs to emit a valid response row. They
   are adapter work packets, not
   theorem proof evidence. Publication-bundle audit rows also verify that each
   request resolves to a bundled action-resource plan and matches that plan's
   per-resource contract maps.

13. `formalization_gap_planner_resource_response_ledger`
   Validates local or frontier responses keyed by resource request, records
   matched and missing response-contract fields, source refs, Lean declaration
   hits, coverage updates, prover diagnostics, residual goals, and route
   revision recommendations. It also carries forward the request
   `dispatch_spec` so downstream route-revision traces remain tied to the
   requested adapter surface. Missing responses are awaiting work; kernel-proof
   claims are rejected. Ledger rows are adapter evidence and planner feedback,
   not theorem proof evidence. Publication-bundle audit rows also verify
   request-row resolution and response-contract field accounting.

14. `formalization_gap_planner_refinement_queue`
   Turns route-revision triggers and interactive hooks into auditable work
   orders for literature tools, Lean search, LSP/prover diagnostics, and
   route-DAG revision.

15. `formalization_gap_planner_refinement_adapter_responses`
   Produces conservative local response JSONL from route-truth benchmark labels
   so the refinement loop can be exercised without live MCP credentials. It is
   adapter output, not proof evidence.

16. `formalization_gap_planner_source_grounding_audit`
   Checks each informal route-DAG node for attached source refs, declared
   formal-gap boundaries, or bounded literature-search obligations. It keeps
   source discipline explicit before route promotion.

17. `formalization_gap_planner_local_literature_adapter`
   Replaces literature-discovery rows with local source-backed route evidence
   from text/markdown/json corpora, or emits focused literature-gap nodes when
   the local corpus has no match. It is route evidence, not proof evidence.

18. `formalization_gap_planner_local_formal_source_adapter`
   Replaces Lean-library-grounding rows with local declaration-search evidence
   from the formal-source backend and optional Lean RAG dependency DB, while
   preserving other adapter responses.

19. `formalization_gap_planner_local_proof_state_adapter`
   Replaces proof-state-feedback rows with local Lean diagnostics and residual
   goals, while preserving merged literature and Lean-grounding responses. It
   blocks `sorry`/`admit`/`axiom` skeletons, classifies non-Lean skeletons as
   statement-materialization gaps, and remains diagnostic feedback, not proof
   evidence.

20. `formalization_gap_planner_refinement_evidence`
   Records tool responses to the refinement queue and normalizes literature
   evidence, Lean declaration hits, coverage updates, prover diagnostics,
   residual goals, and route-revision proposals. It also exports
   `formalization_gap_planner_refinement_evidence_row.schema.json` so accepted
   and awaiting evidence rows can be validated outside AI Statistician.

21. `formalization_gap_planner_route_revision_overlay`
   Applies accepted route-revision proposals back to the selected route plan as
   a non-mutating overlay with changed primitives, DAG nodes, source refs,
   residual goals, revised route-alignment edges, and replay gates. Rows with
   revised selected primitives that lack a matching informal and formal
   realization node are rejected before handoff. Publication bundles that
   include the resource-response ledger also validate overlay evidence ids
   against accepted ledger rows and validate the compact
   `applied_resource_response_traces` copied from those ledger rows.

22. `formalization_gap_planner_route_stability_audit`
   Decides whether each route has stabilized under the current evidence bound
   or should expand literature search, Lean-library grounding, proof-state
   feedback, or route replanning. It is a stop/expand planning audit, not proof
   evidence. It exports
   `formalization_gap_planner_route_stability_audit_row.schema.json` so
   downstream replanning and interactive-session systems can validate the
   stop/expand ledger.

23. `formalization_gap_planner_route_replan_handoff`
   Converts route-revision overlays and stability decisions into a replayable
   standalone seed for the next planner round. Handoff rows preserve the
   revised informal DAG nodes, revised formal-realization DAG nodes where
   available, the legacy revised Lean-realization alias, and revised
   route-alignment edges, and copy them into each seed route and its replan
   metadata so the next planner run can be audited for two-DAG alignment
   continuity.
   They also preserve applied proposal ids, evidence ids, hook kinds,
   compact resource-response traces, pending or rejected resource-response
   request ids, prover-attempt statuses, diagnostic signatures, residual
   goals, source refs, and Lean declaration hits so resource-response-ledger
   feedback is not lost
   before the next route synthesis pass. The seed is planning input, not proof
   evidence. It exports
   `formalization_gap_planner_route_replan_standalone_seed.schema.json` beside
   the seed so downstream planner reruns can validate the handoff input.

24. `formalization_gap_planner_route_replan_handoff_audit`
   Validates the handoff manifest and standalone seed, checks proof-boundary
   discipline, verifies that preserved alignment edges cover revised selected
   primitives, checks exact row-to-seed preservation of revised DAG and
   alignment payloads plus provenance continuity from handoff rows into
   seed-route metadata, and reruns the standalone planner on the generated seed
   to check that the roundtrip regenerates selected-primitive alignment and
   carries the seed provenance forward in `standalone_input_trace`. It is a
   replayability audit, not theorem proof evidence. It exports
   `formalization_gap_planner_route_replan_handoff_audit_row.schema.json` so
   downstream bundle consumers can validate each audit check row without
   importing AI Statistician.

25. `formalization_gap_planner_proof_state_triage`
   Ranks route-overlay proof-state statuses into materialization, local Lean
   repair, environment-configuration, or review work items. It is a proof-worker
   handoff, not theorem proof evidence. It also exports
   `formalization_gap_planner_proof_state_triage_row.schema.json` so external
   worker queues can validate triage rows without importing AI Statistician.

26. `formalization_gap_planner_interactive_session`
   Joins the current route plan, refinement queue, evidence rows, stability
   decisions, replan handoff, and proof-state triage into one next-action
   ledger for each route. It records the bounded interaction to run next plus a
   decision-policy row explaining trigger signals, evidence inputs, stop
   conditions, and fallback actions. All rows stay outside the proof-evidence
   boundary.

27. `formalization_gap_planner_benchmark`
   Exports reusable route-truth labels for evaluation: required primitives,
   actual existing reuse, actual Lean delta, coverage classification, source
   references, proof-evidence boundaries, and the benchmark route-row JSON
   Schema with schema-valid counts.

28. `formalization_gap_planner_benchmark_audit`
   Validates the route-truth benchmark itself: theorem-family diversity,
   source-reference coverage, required/existing/delta primitive consistency,
   coverage-label completeness, public/held-out split metadata, and explicit
   non-proof-evidence boundaries.

29. `formalization_gap_planner_ablation_study`
   Compares the observed planner with no-literature, no-Lean-grounding,
   no-proof-feedback, and no-route-planner counterfactuals. It is planning
   diagnostic evidence only, not theorem proof evidence. It exports
   `formalization_gap_planner_ablation_study_row.schema.json` and the
   `largest_route_adoption_ready_drop_variant` aggregate so paper supplements
   can validate counterfactual metric rows and route-adoption drop summaries
   independently.

27. `formal_verifier_replay_export`
   Turns selected routes into theorem/bridge replay tasks. This is the handoff
   to actual proof attempts, not proof evidence.

30. `formalization_gap_planner_prover_adapter_contract`
   Exports portable work packets as target-prover mapping tasks and validates
   target-prover adapter responses for Lean, Rocq/Coq, Isabelle, Agda, or
   another prover family. Each packet carries its route-alignment edge and
   alignment status. It writes a packet JSON Schema for incoming adapter work
   and a response JSON Schema for adapter output; the reuse-smoke manifest
   exposes both schema files as top-level reusable artifacts. It rejects
   `kernel_verified=true` claims because proof promotion belongs to a separate
   target-prover replay/calibration gate.

31. `formalization_gap_planner_cross_prover_matrix_audit`
   Reruns target-prover packet export for Lean4, Rocq, Isabelle, and Agda from
   the same portable plan, checks packet-count consistency, packet-schema
   validity, alignment-backed packet consistency, `standalone_input_trace`
   provenance counts, and rejection counts, and writes aggregate
   packet/validation JSONL plus
   `formalization_gap_planner_cross_prover_target_summary.json` for downstream
   prover adapters. The target summary records the target families, packet
   counts, standalone-trace counts, replan-metadata trace counts, and per-target
   filter values needed to consume the aggregate JSONL files from a publication
   bundle. It also writes
   `formalization_gap_planner_cross_prover_target_summary.schema.json`, and the
   reuse-smoke manifest exposes both files as top-level discoverable artifacts.

32. `formalization_gap_planner_publication_bundle`
   Packages the portable schema, contract, route-truth benchmark,
   route-truth benchmark audit, adapter registry, component-resource registry,
   benchmark route-row schema, evaluation row schema, prover-adapter
   packet/response schemas, refinement work-item/tool-response/evidence-row
   schemas, library-coverage map row schema, primitive-action queue row schema,
   resource-response schema, resource-response-ledger row schema,
   route-stability audit row schema, route-replan handoff-audit row schema,
   portable-plan audit row schema,
   ablation-study row schema,
   proof-state triage row schema, docs, and optional run artifacts into a
   self-contained research
   supplement/reuse bundle. It also writes a
   machine-readable schema catalog for all reusable bundle contracts, a
   reproduction manifest with downstream commands, including the local
   adapter/refinement loop and feedback LLM route-planner rerun, and runnable
   example inputs. The bundle
records the proof boundary and remains route/planning evidence only. The
reuse-smoke manifest exposes the schema catalog and schema as top-level
artifacts for external users. The reproduction manifest includes a
`run_evaluation` command; for bundles with optional evaluation artifacts, that
command uses
`artifacts/formalization_gap_planner_evaluation/formalization_gap_planner_evaluation_ground_truth.json`
so reruns score against the same route-truth input as the packaged evaluation.
The bundle audit also resolves each matched evaluation row's `match_key`
against that copied route-truth file and compares the recorded ground-truth
primitive fields to the copied route-truth row. Its manifest summarizes these
as checked/valid counts for the copied truth file, route-truth match
resolution, and route/delta/existing-reuse primitive consistency.

33. `formalization_gap_planner_publication_bundle_audit`
   Validates a bundle after export or download: required files exist, schema
   ids match, adapter registry, component-resource registry, benchmark, and
   benchmark-audit manifests are usable, docs are present, required
   standalone, local-adapter, refinement, and audit reproduction commands and
   example inputs are available, component execution-plan JSONL rows satisfy
   the published schema, benchmark route rows satisfy the benchmark route-row
   schema, optional evaluation rows satisfy the evaluation row schema, optional
   refinement evidence rows satisfy the published evidence-row schema, optional
   route-stability rows satisfy the published stability-row schema, optional
   portable-plan audit rows satisfy the published audit-row schema, optional
   route-replan handoff-audit rows satisfy the published audit-row schema,
   optional ablation-study rows satisfy the published ablation-row schema and
   recomputed route-adoption drop aggregate,
   optional proof-state triage rows satisfy the published triage-row schema,
   optional library-coverage map rows satisfy the published coverage-map row
   schema, optional primitive-action queue rows satisfy the published
   action-queue row schema, optional resource-response ledger rows satisfy the
   published response-ledger row schema, optional
   prover-adapter response schemas carry the published schema id, optional
   cross-prover packet rows satisfy the prover-adapter packet schema and carry
   nonempty `standalone_input_trace` provenance, optional
   interactive decision-policy component/resource/contract links resolve to
   bundled component-resource registry rows, optional
   evaluation ground-truth copy, match, and primitive-consistency counters can
   be used as aggregate publication gates, optional
   artifacts are copied inside the bundle, the schema catalog resolves to
   bundle-local contract/schema paths, and proof-boundary text remains intact.

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
- residual/side-condition primitive precision and recall against
  `expected_residual_primitives` and `expected_residual_goals` route-truth
  labels
- alignment coverage for selected informal primitives against formal
  realization candidates
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
