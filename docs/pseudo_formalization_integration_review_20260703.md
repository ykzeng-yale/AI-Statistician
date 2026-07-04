# Pseudo-Formalization Integration Review

Date: 2026-07-03

## Verdict

Add a pseudo-formalization lane to the Formalizer/ProofEngineer stack, but only
as a non-kernel planning, decomposition, faithfulness, and block-verification
artifact.

Do not treat pseudo-formal verification as theorem proof evidence. Source theorem
proof still requires local Lean/AXLE/kernel verification of the intended formal
claim.

After checking arXiv:2605.20531 and `Slim205/pseudo-formalization`, this is
worth making a first-class Formalizer/ProofEngineer capability model, not a
replacement for the Lean prover. The right integration level is:

- LLM-driven pseudo-formal rewriting, faithfulness checking, block verification,
  calibration, and residual routing.
- Typed packets and runtime work orders inside our existing AgentRuntime.
- No direct proof promotion from PF/BV, even when every block is accepted.

The released repo is most useful as a reference implementation of prompts,
parsing, calibration, and benchmark methodology. It should not be vendored as a
core prover dependency: provider calls must go through our generator backend,
runtime audit, and proof-evidence boundary.

## Why It Fits This System

The current formalization bottleneck is not just "bad Lean syntax". The hard
blocker is the transition:

source theorem proof body -> exact semantic anchors -> source-to-bridge work
orders -> Lean candidates -> local Lean/AXLE replay -> kernel evidence.

The PF/BV architecture is useful because it inserts a structured mathematical
middle layer before Lean. It asks the LLM to rewrite a proof into self-contained
blocks with explicit premises, conclusions, proof text, dependencies, and source
anchoring, then verifies each block independently. This directly targets our
current failure mode: a full source theorem is too large and underspecified for
one Lean translation pass, while helper-only Lean candidates often lose the
source theorem target.

## Boundary

Pseudo-formal rows must carry a proof boundary at least as strict as existing
Formalizer and route-planner rows:

- `proof_evidence_status`: `PSEUDO_FORMAL_VERIFICATION_NOT_PROOF_EVIDENCE`
- `kernel_verified`: `false`
- `source_theorem_kernel_verified`: `false`
- `promotion_gate`: `requires_target_prover_kernel_replay`

PF/BV evidence can justify routing, retrieval, decomposition, and repair
priorities. It cannot close a theorem, promote a source theorem, or satisfy
readiness gates that require kernel evidence.

## Proposed Architecture

1. `TheoryDeveloper` emits equation chains, assumptions, theorem cards, and
   proof obligations.
2. `PseudoFormalizer` emits a `PseudoFormalProofPacket`:
   - theorem/proposition/lemma/claim/fact blocks
   - local premises and inherited assumptions
   - conclusion
   - proof text
   - dependency IDs
   - source anchors into theorem cards, derivation trace rows, paper text, or
     proof-body snippets
   - semantic primitive requirements
   - external theorem/library citations
   - Lean feasibility triage: `lean_now`, `needs_rag`, `needs_library`,
     `needs_semantic_definition`, or `pseudo_only`
3. `PseudoFormalFaithfulnessChecker` compares each block to the original theory
   artifact and flags omissions, strengthened claims, silently repaired steps,
   notation drift, or missing assumptions.
4. `PseudoFormalBlockVerifier` verifies each block independently with an LLM,
   using only the declared premises and already accepted dependency statements.
5. `PseudoFormalToLeanWorkOrderRouter` converts accepted and failed blocks into:
   - formal target candidates
   - source-to-bridge premise derivation candidates
   - exact semantic-definition authoring work orders
   - Lean/RAG retrieval queries
   - proof-body repair queues
   - formal gap rows when Lean foundation coverage is missing
6. `AgentRuntime` runs the existing local Lean/AXLE/prover gates. Only those
   gates may create kernel proof evidence.

## What To Reuse From Slim205/pseudo-formalization

Reuse the design pattern, not the repo wholesale:

- structured rewrite prompts with explicit block types and dependency rules
- the dependency DAG plus scope-inheritance forest idea
- faithfulness checking before trusting a rewrite
- regeneration after faithfulness discrepancies
- block-level verifier prompts
- calibrator logic that maps block failures back to original source locations
- pessimistic aggregation over independent rollouts
- benchmark harness ideas for comparing PF/BV against direct LLM-as-judge

Avoid copying benchmark-specific or paper-specific assumptions into runtime.
Any provider/model adapter should be behind our generator backend and typed
artifact schema.

Also avoid importing hardcoded model names, ad hoc XML parsing as the runtime
source of truth, or benchmark data with unclear redistribution/training status.

## Evaluation Gates

The first implementation should be evaluated by generic gates:

- packet schema validity and DAG well-formedness
- source-anchor coverage for every nontrivial block
- no strengthened or weakened block statements after faithfulness check
- block verifier verdicts calibrated back to source theorem/proof-body locations
- number of routed Lean/RAG/semantic-definition work orders produced
- pseudo-to-Lean conversion success rate under local Lean/AXLE
- reduction in repeated parser/import/API failure loops
- zero `kernel_verified=true` promotion from PF/BV artifacts alone

## First Repo Target

Implement the contract first, before adding another live LLM path:

- `ai_statistician/pseudo_formalization.py`
- tests for packet normalization, DAG validation, faithfulness blockers, and
  proof-evidence boundary rejection
- Formalizer prompt hook that can request a pseudo-formal packet when
  source-theorem proof-body repair is blocked by missing semantic anchors or
  Lean library coverage
- runtime adapter that turns pseudo-formal block verdicts into existing formal
  gap, source-to-bridge, semantic-definition, and Lean/RAG work-order rows

This is the right system-level correction because it strengthens the feedback
loop instead of adding more theorem-specific runtime branches.
