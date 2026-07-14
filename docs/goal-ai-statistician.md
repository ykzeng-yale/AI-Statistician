# AI Statistician Objective

Build the next-generation fully autonomous AI Statistical Theory Lab in
`/Users/yukangzengcmac/AI-Statistician`: a powerful open-statistical-research
development system that can ingest arbitrary JASA/AOAS/frontier-style
statistical theory questions, propose and iterate new
theory/estimators/tests/procedures, retrieve paper/Lean/Mathlib/StatInference/
OpenProver knowledge with efficient hybrid search, expand reusable Lean proof
libraries and prove progressively stronger theorem families in AXLE/Lean,
implement and stress-test algorithms/simulations, distinguish proved subclaims
from formal gaps honestly, learn from proof/simulation traces, and evaluate the
system on broader frontier benchmarks with real AXLE/kernel evidence.

## Generalization And Evaluation Invariants

The system is not optimized around one conformal, FDR, causal, or other named
question. A single question may be used as a diagnostic canary, but it cannot
define a runtime rule or establish general AI Statistician capability.

Every central change must therefore satisfy all of the following:

1. The implementation and acceptance contract are domain-neutral. Core runtime
   code must not branch on a statistical family, theorem name, metric name,
   generated output key, Lean grammar fragment, or benchmark-specific alias.
2. Development evidence uses at least two unrelated statistical families under
   the same code and configuration. A disjoint panel with at least two further
   frozen families is withheld from prompt/rule changes and used to test
   transfer.
3. The split between development, cross-family regression, and held-out tasks is
   recorded before the held-out run. A failure may improve the general agent,
   feedback, retrieval, sandbox, or evaluator interface, but may not add a rule
   that recognizes that task's vocabulary or expected answer.
4. Coding agents generate theory, Python/R implementations, simulations, and
   Lean candidates from LLM context. Runtime code supplies typed artifact,
   security, resource, lineage, and evidence contracts plus exact execution or
   compiler feedback; it does not repair statistical formulas or Lean proofs by
   hand.
5. Candidate generation and acceptance are independent. A coding agent cannot
   author or weaken its own required gate, retrieval cannot verify a theorem,
   and component calibration cannot substitute for evidence consumed inside the
   one Architect-owned AgentRuntime.
6. Completion still requires two unrelated fresh families to close the full
   theory, implementation/simulation, formal RAG, iterative Lean feedback,
   Critic, and exact source-theorem kernel loop. Broader held-out failures remain
   visible and cannot be hidden by an aggregate checklist score.
7. Two-family S14 closure is a required integration milestone, not sufficient
   evidence that the general lab is complete. Product-level readiness also
   requires breadth across the 10 canonical S1 tasks, blind target recovery on
   the 12-topic/60-question frontier suite, transfer to the frozen held-out
   families, serious long-form theory derivation, scientific Python and R
   execution, arbitrary-paper ingestion, and reusable proof progress beyond
   support lemmas. No single task or two-task panel can satisfy those claims.
8. Executability and scalar metrics are necessary but not semantic review. A
   distinct LLM reviewer must compare generated algorithms and simulations with
   the question, rigorous theory trace, frozen experiment contract, exact code,
   executed runtime arguments, and returned metrics. Review findings are typed
   non-proof feedback routed to the originating coding agent for a fresh run.
   Formal targets require the analogous immutable semantic-claim contract and
   independent review; matching a declaration name is not enough to preserve a
   theorem.

## Current Milestone Status

The domain-neutral generated-code semantic-review loop is now part of the one
AgentRuntime. It is required by full capability evaluation and is scored only
when both generated algorithm and generated simulation artifacts receive
lineage-valid independent Opus acceptance. This closes the specific
"runnable-but-vacuous experiment" design gap exposed by the frozen survival and
sequential development panel; it does not close S14 or establish theorem proof.

The next central gaps remain: demote the named-family `research_lab` registry to
an optional baseline provider; add serious long-form equation/lemma-DAG theory
development with critic revision; provide broad scientific Python and R coding
environments; bind formal targets to immutable semantic claims with independent
review; and complete iterative exact-source Lean proof search with local
compiler/LSP/kernel feedback on both development families before touching the
held-out panel.

For the operational multi-worker contract, see
[`docs/ai_statistician_multi_codex_blueprint.md`](ai_statistician_multi_codex_blueprint.md).
The current frozen S14 split is machine-readable at
[`benchmarks/autonomous_cross_family_e2e_protocol_20260713.json`](../benchmarks/autonomous_cross_family_e2e_protocol_20260713.json).
