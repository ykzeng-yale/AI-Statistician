# Main Worker Ownership

Updated: 2026-06-25

This document records the main-worker operating contract for AI Statistician.
It complements `docs/multi_codex_coordination.md` and
`docs/ai_statistician_multi_codex_blueprint.md`.

## Role

The main worker owns the central integration path from live agent runtime to
verifiable evidence:

```text
Architect policy
  -> LLM TheoryDeveloper proposal
  -> generated simulation / algorithm code execution
  -> Formalizer / ProofEngineer Lean candidate materialization
  -> local Lean / AXLE diagnostics and repair
  -> CriticEvaluator agenda and runtime learning rows
  -> cross-task capability evidence
```

The main worker should take the harder repo-wide work: runtime orchestration,
evidence-contract semantics, live capability evaluation, repair-loop plumbing,
and GitHub coordination. Other Codex sessions should still own focused lanes,
but the main worker is responsible for making their outputs converge into the
product path instead of becoming disconnected audits.

## Immediate Main Goal

Reach a live, GitHub-reviewable AI Statistician capability milestone:

1. Start from `codex/ai-stat-lab-sync-20260625` or a focused child branch.
2. Run an Architect-controlled runtime path with a declared
   `formal_verification_policy` and `recommended_research_path`.
3. Show generated algorithm and generated simulation code executing locally,
   with stdout/stderr/result artifacts captured.
4. Show a failed-then-passed repair sequence for at least one generated code
   path.
5. Show Formalizer/ProofEngineer receiving local Lean or AXLE diagnostics,
   materializing a repaired Lean candidate, and rerunning the verifier.
6. Preserve the proof boundary: helper proofs and runtime `ACCEPTED` statuses
   do not prove the source theorem.
7. Add a second task-family capability run beyond conformal prediction before
   claiming generality.

## Evidence Gates

Use the capability ladder from `docs/multi_codex_coordination.md`:

- L2: live Architect-controlled runtime completes.
- L3: generated algorithm/simulation code executes locally.
- L4: generated code fails, returns diagnostics, and is repaired.
- L5: Formalizer emits a materialized Lean candidate checked by local Lean.
- L6: ProofEngineer consumes verifier/proof-state traces and repairs.
- L7: helper or bridge subclaims are kernel verified.
- L8: the full source theorem is kernel verified.

Do not promote static replay, deterministic templates, retrieval hits, queue
creation, or broad release audits to capability evidence.

## Collaboration Protocol

- Push focused child branches with the `codex/` prefix.
- Prefer PRs or branch updates back to `codex/ai-stat-lab-sync-20260625` until
  the merge target is explicit.
- Keep one branch focused on one capability seam.
- Cite exact manifest paths and counts when reporting Lean/AXLE evidence.
- Never commit `.env`, raw API keys, or unredacted provider responses.
- Use `docs/main_worker_status.json` as the compact status handoff for other
  Codex workers.

## Current Main-Worker Lane

Branch:

```text
codex/runtime-eval-alignment-20260625
```

Current lane:

```text
runtime/evaluation alignment and evidence-readiness
```

First concrete change in this lane: `doctor` now reports local Lean/Elan binary
readiness separately from AXLE package/API readiness. This matters because
component capability tests can fail on first-use Lean toolchain installation
before they reach the actual generated Lean candidate.

Second concrete change in this lane: `research-agent-runtime
--capability-eval-preset minimal-live` now auto-detects the repo-local
`legacy_sources/emperical_process_lean` Lake project before falling back to
machine-specific LeanPractice paths. Future workers should be able to run the
strict live preset from this repo without manually passing `--lean-project`.

Third concrete change in this lane: AlgorithmEngineer and SimulationEngineer
metric-gate repair prompts now explicitly steer live coding-agent repair toward
conservative finite-width coverage intervals and half-width widening/recompute
when a pilot interval under-covers. This keeps the repair gate honest while
making the intended repair behavior legible to the LLM.

Fourth concrete change in this lane: AlgorithmEngineer and SimulationEngineer
generated-code contracts now distinguish the literal packet entrypoint
`run_sandbox` from the function signature
`def run_sandbox(seed: int, replicates: int) -> dict`, and normalize
signature-shaped metadata before validation. This removed the live
AlgorithmEngineer packet-validation stop caused by a prompt/schema mismatch.

Fifth concrete change in this lane: Formalizer capability-eval prompts and
validators now apply an initial coverage target-shape guard. Conformal source
theorem `formal_targets` must preserve a probability/measure coverage
conclusion instead of replacing the theorem with a rank-arithmetic helper.
The runtime audit also now carries Formalizer local-Lean/proof-state counters
from the manifest into the capability scorecard.

Live evidence collected on 2026-06-25:

- `runs/main_worker_doctor_live_env/doctor_manifest.json`: live environment
  ready for Anthropic and AXLE when keys are loaded via process environment.
- `runs/main_worker_live_runtime_minimal/research_agent_runtime_manifest.json`:
  5-iteration budget reached only SimulationEvaluator repair; scorecard 29/49.
- `runs/main_worker_live_runtime_minimal12/research_agent_runtime_manifest.json`:
  12-iteration budget reached generated algorithm fail-then-pass repair and
  Formalizer/ProofEngineer local Lean diagnostics; scorecard 32/49.
- `runs/main_worker_live_coding_agent_repair_eval_both_guided/coding_agent_generated_code_repair_eval_manifest.json`:
  standalone live combined coding-agent repair eval passed with one
  AlgorithmEngineer and one SimulationEngineer fail-then-pass repair sequence.
- `runs/main_worker_live_runtime_with_coding_gate_both_guided/research_agent_runtime_manifest.json`:
  attached live coding-agent repair component gate passed inside the runtime
  audit with live, non-fixture evidence; scorecard 31/49.
- `runs/main_worker_live_runtime_resume_entrypoint_hardened/research_agent_runtime_manifest.json`:
  resumed from the prior AlgorithmEngineer validation failure and reached
  integrated generated AlgorithmEngineer code execution; scorecard 31/49.
- `runs/main_worker_live_runtime_resume_formalizer_shape_guard/research_agent_runtime_manifest.json`:
  resumed after generated simulation repair, reached two integrated generated
  AlgorithmEngineer executions, produced probability/measure-shaped Formalizer
  candidates, and ran local Lean/proof-state feedback; after the audit counter
  fix, `runtime_capability_audit_after_counter_fix/research_agent_runtime_audit_manifest.json`
  reports scorecard 36/49.
- `runs/main_worker_live_runtime_resume_blocked_import_followup/research_agent_runtime_manifest.json`:
  resumed the Mathlib-blocked ProofEngineer task and produced one
  failed-then-passed Formalizer Lean repair sequence, ending with a compiled
  `source_theorem_target_known=false` diagnostic helper; scorecard 38/49.
- `runs/main_worker_live_runtime_resume_algorithm_formalizer_combined_probe/research_agent_runtime_manifest.json`:
  resumed from the AlgorithmEngineer pending task and follow-up Critic task,
  preserving one integrated generated AlgorithmEngineer repair sequence, one
  generated SimulationEngineer repair sequence, and one Formalizer Lean
  candidate repair sequence in the same runtime lineage; scorecard 40/49.
- `runs/main_worker_live_runtime_resume_mathlib_narrow_import_probe/research_agent_runtime_manifest.json`:
  after `lake exe cache get`, the runtime distinguishes unavailable umbrella
  `import Mathlib` from verified narrow Mathlib submodules. The live resume
  reached scorecard 41/49 and 6 real kernel-verified helper/subclaim rows, but
  still produced zero source-to-bridge work orders or source-theorem promotion
  seeds.
- `runs/main_worker_live_runtime_resume_phantom_next_action_normalized_probe/research_agent_runtime_manifest.json`:
  after adding a packet normalizer for phantom source-to-bridge `next_actions`,
  the live resume reached 8 real kernel-verified helper/subclaim rows and 5
  compiled Formalizer diagnostic helpers. It still ended at
  `MAX_ITERATIONS_REACHED` with pending task
  `formalize-repair:conformal_prediction_coverage:b3bbbf62`.
- `runs/main_worker_live_runtime_resume_placeholder_fail_closed_probe/research_agent_runtime_manifest.json`:
  after adding a fail-closed normalizer for repeated placeholder Lean sketches,
  the live resume produced no new packet-validation failure after the prior
  proof-hole rows. It reached candidate precheck/local Lean repair, then Critic
  reroute, with `kernel_verified_subclaims=14`,
  `n_formalizer_lean_candidate_local_lean_compiled=6`, and pending task
  `formalize-critic-repair:conformal_prediction_coverage:460b3dc4`.
- `runs/main_worker_live_runtime_resume_critic_metadata_agenda_probe/research_agent_runtime_manifest.json`:
  after teaching Critic to treat compiled diagnostic-helper bridge blockers as
  source-binding metadata work, the live one-iteration resume emitted
  `formal_gap:source_to_bridge_metadata_authoring` and a
  `SOURCE_TO_BRIDGE_METADATA_BLOCKER` learning row before generic proof-bank
  expansion. The row carries helper ids
  `split_conformal_coverage_prop_helper_v3` and
  `split_conformal_core_prop_coverage_bridge_helper`, records
  `PENDING_SOURCE_TO_BRIDGE_METADATA_AUTHORING`, and routes to pending task
  `formalize-critic-repair:conformal_prediction_coverage:d59f0093`.
- Resume-time Formalizer memory now preserves that metadata blocker through CLI
  compaction and converts it into
  `recommended_formalizer_target_mode=source_to_bridge_metadata_authoring_required`
  with an explicit `source_to_bridge_metadata_authoring_contract`. The next
  Formalizer/ProofEngineer step is to author exact
  `source_to_bridge_premise_derivation_candidate_request` metadata before
  executable premise candidates are queued; this remains orchestration context,
  not source-theorem proof evidence.
- `runs/main_worker_live_runtime_resume_metadata_request_artifact_probe_keyed/research_agent_runtime_manifest.json`:
  after loading the attached Anthropic key from its prose-formatted
  `Anthropic API Key:` line into `ANTHROPIC_API_KEY`, the one-iteration resume
  reached `MAX_ITERATIONS_REACHED` instead of the earlier missing-key failure.
  The live Formalizer emitted
  `formalizer_proposal:f3fb62bfe04f7a578fcd5f45` with one complete
  `SourceToBridgePremiseDerivationCandidateRequest`
  `request:hGoodRankImpliesCovered`; runtime recorded it as
  `SOURCE_TO_BRIDGE_METADATA_AUTHORING_REQUEST_NOT_PROOF_EVIDENCE` and still
  produced zero executable source-to-bridge work orders in that same iteration.
  Scorecard remains 41/49, with `kernel_verified_subclaims=14` and
  `formal_gaps=19`.
- `runs/main_worker_live_runtime_resume_metadata_request_consumption_probe/research_agent_runtime_manifest.json`:
  a two-iteration live resume consumed that request far enough to enter
  `recommended_formalizer_target_mode=source_to_bridge_premise_derivation_required`,
  but the Formalizer packet failed validation because its emitted
  `source_to_bridge_premise_derivation_candidates` entry did not copy the
  request id/object. This identified the next blocker as request consumption,
  not metadata authoring.
- `runs/main_worker_live_runtime_resume_metadata_request_autofill_probe/research_agent_runtime_manifest.json`:
  after preserving the nested request through Formalizer memory compaction and
  adding an unambiguous single-request/single-candidate autofill, the live
  repair no longer failed on missing source-binding metadata
  (`missing_source_binding_contract_metadata=false`). The failure moved to the
  stricter semantic-anchor check:
  `source_to_bridge_premise_derivation_candidates Lean candidate missing required
  semantic anchor references: hQuantileThreshold, hGoodRank`. Runtime still
  emitted zero executable source-to-bridge work orders, so no proof evidence was
  claimed.
- `docs/runtime_design_drift_audit_20260625.md` records the design correction
  for this lane: evidence-boundary guards may stay in the core runtime, but
  conformal/source-to-bridge tactics should move into typed artifacts, policy
  packs, or ProofEngineer adapters. The first concrete extraction is
  `ai_statistician/source_to_bridge_metadata.py`, which owns
  `SourceToBridgePremiseDerivationCandidateRequest` normalization and
  request-shell handling while `research_agent_runtime.py` delegates through a
  thin compatibility wrapper. This is still non-proof orchestration memory.

The 12-iteration run is evidence for live generated-code execution, one
AlgorithmEngineer repair sequence, Formalizer candidate materialization, local
Lean tool calls, and proof-state feedback rows. It is not source theorem proof:
`real_kernel_verified_subclaims=0`, `formal_gaps=3`, and the terminal state was
`MAX_ITERATIONS_REACHED` with a pending ProofEngineer repair task.

The attached coding-agent repair gate is implementation capability evidence,
not theorem proof and not an integrated runtime success by itself. In the
5-iteration attached run, the component gate passed with
`attached_algorithm_repair_sequences=1` and
`attached_simulation_repair_sequences=1`, but the short integrated runtime still
ended at `AlgorithmEngineer algorithm_engineer_packet_validation_failed` before
showing same-run integrated repair loops or any kernel-verified subclaim.

The combined Algorithm/Formalizer probe is the strongest current integrated
capability evidence: `n_generated_code_sandbox_executed=2`,
`n_generated_code_sandbox_failed_then_passed_repair_sequences=1`,
`n_generated_simulation_sandbox_failed_then_passed_repair_sequences=1`,
`n_formalizer_lean_candidate_failed_then_passed_repair_sequences=1`,
`n_formalizer_lean_candidate_local_lean_checked=4`, and
`n_formalizer_lean_candidate_local_lean_compiled=2`. It is still not source
theorem proof: `n_kernel_verified_subclaims=0`, `n_formal_gaps=7`, the compiled
Lean candidates are diagnostic helpers with
`source_theorem_target_known=false`, and the pending task remains a
Formalizer/Critic repair.

The newest Formalizer probes improve the environment and packet plumbing but
do not change the proof boundary. The configured Lean project can compile
narrow imports such as `Mathlib.MeasureTheory.Measure.ProbabilityMeasure` and
`Mathlib.Probability.IdentDistribIndep`, while root `import Mathlib` still
fails because `Mathlib.olean` is absent. Compiled candidates remain
`source_theorem_target_known=false` diagnostic helpers unless a future packet
emits concrete `source_to_bridge_premise_derivation_candidates` with copied
source-binding metadata and local Lean/AXLE verifies the intended
probability/measure coverage claim.

The latest live blocker is no longer the `sorry` packet-validation loop and no
longer the source-binding metadata copy barrier. The runtime now has one
complete metadata-authoring request in memory and can autofill it into a single
unbound source-to-bridge candidate before validation. The next blocker is
semantic: the candidate must reference `hQuantileThreshold` and `hGoodRank`
non-vacuously in the Lean proof body, without putting adapter objects such as
`coverage_event` or `good_rank_event` in theorem binders. The next worker should
resume `formalize-repair:conformal_prediction_coverage:1af7fb86`; only after a
locally valid source-to-bridge candidate is emitted should runtime queue the
premise derivation for local Lean/AXLE.

The latest one-iteration resume from that semantic-anchor repair moved into a
different concrete ProofEngineer blocker. The Formalizer packet produced
`split_conformal_hGoodRankImpliesCovered_bridge_helper`, but local Lean rejected
it because `Nat.ceil` is unknown in the configured
`legacy_sources/emperical_process_lean` project. The pending task is now
`formalize-repair:conformal_prediction_coverage:5e0ee83f`, carrying a
`local_lean_repair_contract` with `unknown_identifiers=["Nat.ceil"]`. This should
be repaired through verified local Lean APIs, formal-source/RAG lookup, or an
honest FORMAL_GAP; do not add a conformal-specific Python rewrite for `Nat.ceil`.

The generic runtime fix added after this audit is path hygiene for prover
infrastructure. Generated Formalizer Lean candidates still keep their canonical
kernel/audit artifact under `runs/`, but when a Lean project is configured the
runtime also writes an ignored project-local mirror under
`<lean_project>/.lake/ai_statistician_formalizer_candidates` for Lean LSP/MCP
proof-state inspection. `live_proof_state_request`, learning rows, and
ProofEngineer repair context now distinguish `kernel_check_artifact_path` from
`proof_state_artifact_path`, so LSP-style tools get a file with a Lean-project
ancestor without changing what counts as proof evidence. The regression
`test_formalizer_candidate_materialization_mirrors_project_local_lsp_artifact`
and the guarded suite `tests/test_source_to_bridge_metadata.py
tests/test_research_agent_runtime.py` pass (`302 passed in 154.29s`). A live
probe at
`runs/main_worker_live_runtime_resume_project_local_lsp_probe/research_agent_runtime_manifest.json`
did not materialize a new post-patch candidate, so the mirror has not yet been
live-exercised.

The follow-up design fix wires formal-source grounding into that same repair
loop instead of adding a `Nat.ceil` or conformal-specific rewrite. A configured
`FormalSourceRetriever` is now carried by `FormalizationEvaluator`/`ProofEngineer`;
Lean-candidate failures and carried packet-validation repair contexts attach
bounded `formal_source_grounding_hits` next to their retrieval seeds before
prompting Claude. These hits are API/premise suggestions only and are tagged
`FORMAL_SOURCE_RETRIEVAL_GROUNDING_NOT_PROOF_EVIDENCE`; local Lean/AXLE on the
exact repaired artifact remains the only promotion gate. The focused grounding
tests and the guarded suite `tests/test_source_to_bridge_metadata.py
tests/test_research_agent_runtime.py` pass (`304 passed in 154.72s`).

The live audit probe
`runs/main_worker_live_runtime_resume_formal_source_grounding_audit_probe/research_agent_runtime_manifest.json`
exercised the prompt-time grounding observation: 5 grounding query groups and 9
formal-source hits were recorded as
`FORMAL_SOURCE_RETRIEVAL_GROUNDING_NOT_PROOF_EVIDENCE`. The Formalizer did not
retry the bad `Nat.ceil` Lean helper; it kept the source theorem as a
`FORMAL_GAP`, named `Nat.ceil` and exchangeability-definition blockers, and
routed to Critic/next-action planning. Scorecard remained `41/49`; no source
theorem or frontier theorem proof was produced.

## Delegation To Other Codex Workers

These are useful parallel lanes, but the main worker should integrate their
outputs into the runtime path:

- Formalizer/ProofEngineer worker: fix conformal target-shape drift and ensure
  repaired candidates preserve the probability/coverage theorem shape without
  sorry/hole placeholders or phantom source-to-bridge actions.
- Algorithm/Simulation worker: promote the integrated generated
  AlgorithmEngineer and SimulationEngineer repair evidence into registered
  production algorithms only after registry tests and reruns pass.
- Proof-library worker: add reusable statistics kernels with local Lean/AXLE
  manifests.
- RAG/OpenProver worker: feed source hits and prover diagnostics into
  Formalizer/ProofEngineer prompts without treating retrieval as proof.
- Cross-task evaluation worker: add non-conformal task-family capability runs.

The main worker should not delegate away the integration burden: every lane
must end in runtime artifacts, evidence ledger rows, tests, and a GitHub-visible
branch or PR.
