# Runtime Design Drift Audit

Updated: 2026-08-10

## Verdict

The earlier runtime accumulated a second orchestration plane, source-repair
workers, theorem-specific bridges, recursive payloads, and audit surfaces that
were much larger than the research loop they were meant to support. That was a
design error. It made one model failure fan out into packet repair, queue
materialization, routing, promotion, and fallback stages instead of returning the
raw observation to the model that owned the source.

The current uncommitted cleanup has corrected the largest part of that drift:

- `research_agent_runtime.py` is about 20k lines rather than about 101k;
- the package has 137 top-level Python modules rather than 261;
- the post-runtime formal execution plane is gone;
- the formal-gap-planner, source-bridge, repair-patch-rerun, and certificate
  module families are gone from the canonical package;
- Python/R and Lean now use direct same-model source-feedback loops;
- the metric reviewer now reports findings without selecting an owner or route;
- formal capability scoring reads those integrated loop artifacts;
- proof-bank source is opt-in and cannot silently replace live proving;
- a dead post-result metric-candidate rerun path is gone.

This is a structural correction, not evidence of research success. The latest
authoritative development panel remains 0/2 exact source-theorem closures, and no
fresh live panel has yet run against the simplified architecture.

## Remaining wrong decisions

### 1. Metric protocol remains oversized

The metric authoring, semantic-review, and theory-preflight modules total roughly
10k lines. This cleanup removed `repair_scope`, `recommended_repair_scope`,
top-level repair recipes, and deterministic reviewer-to-owner routing. A rejected
protocol can receive one complete same-author rewrite; after that, raw findings go
to the Architect.

The remaining problem is duplicated claim schemas, identity audits, finding-ledger
projections, and large packet histories. Consolidation must preserve the frozen
confirmatory protocol and independent reviewer while reducing payload and code.

### 2. Theory is still packet-first

Increasing token limits or requiring more equation strings does not create a
research agent. Theory needs a persistent workspace containing definitions,
equation derivations, lemma dependencies, assumption use, counterexamples, and
feedback-linked revisions. The compact JSON object should index those artifacts,
not substitute for them.

### 3. The outer runtime is still too central

Twenty thousand lines is a large improvement but remains too much for one control
module. Subsystems should own their direct workspace loops, while the outer graph
owns transitions and authority. Extraction should reduce central branches and
state, not create adapter families or a second framework layer.

### 4. Current success evidence predates the cleanup

Unit tests can show that transport and boundaries work. They cannot show that a
fresh statistical question reaches rigorous theory, scientific execution,
independent review, exact formalization, and kernel closure. That claim requires a
new exact-Haiku cross-family development run after this change lands.

## Decisions that are not mistakes

- A small executor ABI is a general tool contract, not a statistical answer.
- Same-model structured-output retry from raw schema errors is transport, not a
  hidden semantic repair agent.
- Independent semantic review is a genuine authority boundary.
- Frozen pre-result metric identity prevents post-hoc gate mutation.
- Hash, target, project, declaration, budget, permission, and kernel gates belong
  in deterministic infrastructure.
- Statlib/Mathlib naming, imports, and existing declarations should be retrieved
  as context; runtime should not reimplement them as hardcoded Lean rules.

## Next correction order

1. Land and verify the deletion-first runtime simplification.
2. Consolidate duplicate metric schemas and finding-ledger machinery.
3. Build the artifact-backed TheoryDeveloper workspace.
4. Run the fresh two-family development panel with exact Haiku, real Python/R,
   task-bound formal RAG, live Lean feedback, and exact kernel closure.
5. Only after development closure, unlock held-out tasks without adding
   task-family conditions based on their outcomes.

The active design contract is [production_design.md](production_design.md).
