# Main Worker Ownership

Updated: 2026-06-26

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
metric-gate repair prompts share a generated metric-repair policy. They still
require valid probability/coverage metrics when the task asks for them, but they
now reject vacuous all-covering repairs and require utility diagnostics such as
width, bias, RMSE, efficiency, or failure rate instead of encoding a
coverage-specific widening shortcut in each prompt.

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

The follow-up Critic resume
`runs/main_worker_live_runtime_resume_critic_formal_blocker_requests_probe/research_agent_runtime_manifest.json`
keeps that design generic. Instead of adding a `Nat.ceil` or
exchangeability-specific runtime rewrite, Critic now passes
`formal_blocker_resource_requests` into the pending Formalizer/ProofEngineer
task. The live pending task contains 5 typed requests covering Lean primitive
lookup, semantic alignment, proof search, and source-to-bridge blockers. Each
request recommends `formal_source_retriever`, proof search, Lean LSP/MCP when
configured, and local Lean/AXLE, and each is tagged
`FORMAL_BLOCKER_RESOURCE_REQUEST_NOT_PROOF_EVIDENCE`. The next owner should
resolve those requests through verified declarations/imports or keep an honest
`FORMAL_GAP`; the request channel is routing context only. The focused
blocker-routing test and guarded suite pass, with the final guarded run at
`304 passed in 149.49s`.

The live carry-forward probe
`runs/main_worker_live_runtime_resume_formal_blocker_request_carry_forward_probe/research_agent_runtime_manifest.json`
confirmed the next repair-loop behavior. Formalizer/ProofEngineer consumed the
typed requests far enough to emit one source-to-bridge premise derivation work
order for `hGoodRankImpliesCovered`, but the runtime correctly rejected it before
Lean because it did not reference `hQuantileThreshold`, `hGoodRank`, or `hExch`
non-vacuously. The same turn produced a local Lean failure with unknown
`Finset.univ.filter`; the pending task now carries the original 5 blocker
requests plus one new `lean_unknown_identifier` request for that API, all tagged
`FORMAL_BLOCKER_RESOURCE_REQUEST_NOT_PROOF_EVIDENCE`. Scorecard is still not
ready (`40/49` in CLI output), and no source theorem promotion work order was
emitted. The focused carry-forward tests and guarded suite pass, with the final
guarded run at `304 passed in 149.99s`.

The next live ProofEngineer/Critic sequence exposed a formal-environment bridge
contract rather than a theorem-specific repair. The resume at
`runs/main_worker_live_runtime_resume_formal_blocker_request_next_repair_probe/research_agent_runtime_manifest.json`
advanced the live scorecard to `42/49`, with 5 failed-then-passed Formalizer
Lean repair sequences and 9 compiled diagnostic candidates, but the exact
source-to-bridge candidate still failed semantic/source anchoring and the
source-theorem formal-environment signature probes reported only
`candidate_artifact_path missing`. The Critic follow-up at
`runs/main_worker_live_runtime_resume_critic_after_formal_env_probe/research_agent_runtime_manifest.json`
routed that as a formal-environment repair gap plus typed blocker requests.
The next ProofEngineer turn at
`runs/main_worker_live_runtime_resume_formal_env_repair_consumption_probe/research_agent_runtime_manifest.json`
carried 7 requests, including new `Equiv.Perm` and `Finset.univ.filter`
unknown-identifier blockers, while source-to-bridge premise checking improved
from missing semantic-anchor references to `premise_derivation_candidate_wrong_declaration`.
No source theorem proof, source-theorem promotion seed, or proof-body executor
row was produced. The bridge now classifies missing exact source-theorem
candidate artifacts as `source_theorem_candidate_materialization_required` and
keeps that contract in runtime learning rows so Formalizer/ProofEngineer must
materialize an exact Lean candidate before signature probing or proof-body
execution can run.

The follow-up materialization-contract probe at
`runs/main_worker_live_runtime_resume_candidate_materialization_contract_followup_probe/research_agent_runtime_manifest.json`
exercised that bridge live: 6 formal-environment work orders produced 6
signature-probe rows, all blocked as
`SIGNATURE_PROBE_BLOCKED_NEEDS_CANDIDATE_ARTIFACT`, with zero proof-body queue
rows and scorecard `42/49`. The next runtime design mistake was memory routing,
not theorem logic: bounded resume memory could drop those materialization rows
or merge them past the `max_rows` cap, so Critic saw only generic formal gaps.
The runtime now pins candidate-materialization rows during memory compaction,
keeps merged runtime memory bounded, recomputes the Critic proof-bank summary
from current memory, and emits a typed
`SOURCE_THEOREM_CANDIDATE_MATERIALIZATION_REQUIRED` request for
Formalizer/ProofEngineer/LeanProver. The live bounded probe
`runs/main_worker_live_runtime_resume_critic_materialization_request_bounded_probe/research_agent_runtime_manifest.json`
confirmed the handoff: pending task
`formalize-critic-repair:conformal_prediction_coverage:c3d1341e` has 4 formal
blocker requests, including the materialization request, and
`runtime_learning_memory.rows_loaded=20` with 4 pinned materialization rows.

The next live consumption probe moved the system into a concrete candidate-repair
loop rather than another missing-artifact loop. The patched rerun at
`runs/main_worker_live_runtime_resume_candidate_materialization_import_request_probe/research_agent_runtime_manifest.json`
materialized an exact source-theorem-shaped candidate artifact for
`split_conformal_finite_sample_coverage`, wrote the project-local proof-state
mirror, and ran local Lean. It failed as non-proof evidence with
`lean_parser_or_syntax_error` (`unexpected token '}'`) and produced pending
ProofEngineer task `formalize-lean-repair:conformal_prediction_coverage:452c609f`;
scorecard stayed `42/49`, kernel-verified helper/subclaim rows rose to 16, and
formal gaps rose to 26. The generic follow-up patch also converts unavailable
Lean imports from precheck/local-Lean repair contracts into typed
`lean_unavailable_import` formal blocker requests with validator-suggested
replacement modules when present. This keeps API/import repair in the
FormalSourceRetriever/Lean LSP/local Lean loop instead of hardcoding a theorem
rewrite in AgentRuntime.

The immediate ProofEngineer continuation at
`runs/main_worker_live_runtime_resume_exact_candidate_syntax_repair_probe/research_agent_runtime_manifest.json`
retried the exact source-theorem-shaped candidate and again hit local Lean
`lean_parser_or_syntax_error` (`unexpected token '}'`). This is still progress
relative to the earlier missing-artifact state because the runtime now has a
concrete artifact, kernel-check path, and project-local proof-state mirror; it
is not proof evidence. The pending task is now
`formalize-lean-repair:conformal_prediction_coverage:b4a5f536`, with scorecard
`42/49`, 18 kernel-verified helper/subclaim rows, and 27 formal gaps. The
generic runtime patch from this observation preserves `target_lean_file`,
`target_lean_line`, `target_lean_column`, and `target_lean_declaration` in
Formalizer Lean-candidate learning rows, bounded runtime memory, and proof-bank
summary repair memory so later ProofEngineer/Critic turns can distinguish
"exact target artifact failed local Lean" from "candidate artifact missing."

The patched repeated-syntax probe at
`runs/main_worker_live_runtime_resume_repeated_syntax_failure_escalation_patched_probe/research_agent_runtime_manifest.json`
confirms the design-level fix for that loop. The LLM again emitted a broad
Lean theorem statement that local Lean rejected at line 2 column 14, so no proof
was promoted and the scorecard remained `42/49`. The pending ProofEngineer task
`formalize-lean-repair:conformal_prediction_coverage:639d096a` now carries a
`repeated_syntax_failure=true` local-Lean repair contract and a typed
`lean_repeated_parser_or_syntax_failure` formal blocker request. That blocker is
non-proof evidence: it tells ProofEngineer to fail closed to `FORMAL_GAP` or
emit one minimal ASCII/core Lean support lemma through a support channel, with
local Lean rerun before any executable claim can be promoted.

The follow-up probes tightened that contract without adding a conformal-theorem
rewrite to AgentRuntime. In
`runs/main_worker_live_runtime_resume_repeated_syntax_contract_followup_probe/research_agent_runtime_manifest.json`,
the repair contract was carried forward but the next candidate retried the
source theorem with Lean syntax that this project rejects (`Type*` caused the
same parser failure). The runtime now prechecks that Lean parser compatibility
issue, rejects executable source-theorem retries while a repeated-syntax
fail-closed contract is active, and normalizes `FORMAL_GAP` entries by stripping
`sorry`/placeholder Lean sketches. The next live probe,
`runs/main_worker_live_runtime_resume_repeated_syntax_failclosed_normalized_probe/research_agent_runtime_manifest.json`,
confirmed the architectural move: the source theorem stayed fail-closed and the
model tried a `source_theorem_target_known=false` support lemma instead. That
support lemma then failed no-import local Lean on `Real`/order arithmetic, so
the runtime refreshed stale repair contracts from carried diagnostics and
classified the failure as `lean_no_import_noncore_arithmetic`. The latest live
probe,
`runs/main_worker_live_runtime_resume_core_helper_contract_refresh_probe/research_agent_runtime_manifest.json`,
ended with scorecard `42/49`, pending task
`formalize-lean-repair:conformal_prediction_coverage:18707790`, 26
kernel-verified helper/subclaim rows, 31 formal gaps, 24 local Lean-checked
candidate artifacts, and 10 compiled candidate artifacts. The pending contract
now requires either a pure core-Lean `Prop` support helper or a verified import
route through FormalSourceRetriever/Lean LSP/local Lean before any executable
claim can be promoted.

The next continuation exercised that contract rather than adding another local
rewrite. In
`runs/main_worker_live_runtime_resume_core_helper_precheck_followup_probe/research_agent_runtime_manifest.json`,
the model emitted a no-import core `Prop` helper and local Lean compiled it.
The runtime counted it as a diagnostic helper only:
`source_theorem_target_known=false`, `source_theorem_kernel_verified=false`, 25
local Lean-checked Formalizer candidates, 11 compiled candidate artifacts, 28
kernel-verified helper/subclaim rows, and 32 formal gaps. A follow-up Critic
continuation at
`runs/main_worker_live_runtime_resume_compiled_core_helper_critic_typed_import_request_probe/research_agent_runtime_manifest.json`
kept the helper out of the source-theorem proof lane and moved the remaining
formalization blocker to an import/environment route. The pending task is now
`formalize-critic-repair:conformal_prediction_coverage:dbe373a3`; its feedback
classifies the `Mathlib.olean` missing-object-file diagnostic as
`lean_import_environment_missing` and carries a typed `lean_unavailable_import`
blocker request from `critic_local_lean_formalization_feedback`. That request is
non-proof evidence and asks the prover/RAG stack to use a verified local import,
remove the guessed import, or fail closed with a dependency `FORMAL_GAP`.
Successful local Lean exits with only warnings are no longer converted into
`lean_local_check_failed` repair contracts when replayed through runtime memory.

The next live continuation shows why this should stay a design-level repair
rather than a conformal-specific patch. In
`runs/main_worker_live_runtime_resume_typed_import_blocker_followup_probe/research_agent_runtime_manifest.json`,
the pending `formalize-critic-repair:conformal_prediction_coverage:dbe373a3`
task consumed the typed `lean_unavailable_import`/`Mathlib.olean` blocker, but
the model still emitted a no-import helper using `Real`, order typeclasses, and
`linarith`. Local Lean rejected the exact artifact with `lean_unknown_tactic`
and `lean_no_import_noncore_arithmetic`; the run ended at scorecard `42/49`
with pending task `formalize-lean-repair:conformal_prediction_coverage:8133e814`,
26 local Lean-checked Formalizer candidates, 11 compiled candidate artifacts,
30 kernel-verified helper/subclaim rows, and 33 formal gaps. The fix is now in
the generic contract path: when the Mathlib root import is unavailable, any
no-import diagnostic helper is prechecked as core-Lean-only unless a narrow
import has already been verified in the configured project, the prompt compactor
preserves that repair rule, and the helper example is a generic `core_prop_bridge`
rather than a split-conformal-specific name. This keeps Claude acting as a
ProofEngineer over exact diagnostics and prover/RAG resource requests instead of
learning another runtime corner case.

The patched live continuation confirmed the intended behavior. In
`runs/main_worker_live_runtime_resume_mathlib_root_core_helper_gate_probe/research_agent_runtime_manifest.json`,
the ProofEngineer task `formalize-lean-repair:conformal_prediction_coverage:8133e814`
returned a no-import core `Prop` bridge,
`split_conformal_core_prop_bridge_repair`, and local Lean compiled the exact
artifact. The manifest records it as
`FORMALIZER_DIAGNOSTIC_HELPER_LOCAL_LEAN_KERNEL_VERIFIED_NOT_SOURCE_THEOREM_PROOF`
with `source_theorem_target_known=false`, 27 local Lean-checked Formalizer
candidates, 12 compiled candidates, 32 kernel-verified helper/subclaim rows, 34
formal gaps, and next task `critic:conformal_prediction_coverage:ad2b4eaa`.
The remaining formal blocker is still the mature prover/RAG work: derive
`hGoodRankImpliesCovered` from exact source semantic anchors such as
`hQuantileThreshold` and `hExch`, or report the dependency as a source-theorem
`FORMAL_GAP`; do not treat the helper as proof of
`split_conformal_finite_sample_coverage`.

A follow-up Critic handoff probe is recorded at
`runs/main_worker_live_runtime_resume_critic_semantic_anchor_feedback_join_probe/research_agent_runtime_manifest.json`.
It leaves the scorecard at 42/49 and the evidence counts unchanged, but fixes a
design-level feedback loss: the pending Formalizer repair task
`formalize-critic-repair:conformal_prediction_coverage:318aa3cf` now carries
first-class `source_to_bridge_premise_derivation_feedback`,
`semantic_anchor_blocker_feedback`, and
`missing_semantic_anchor_references=["hC"]` for the
`hGoodRankImpliesCovered` premise instead of leaving the semantic-anchor failure
buried in generic blocker text. This is still repair context, not proof
evidence; the next worker should consume it through the Formalizer/ProofEngineer
and prover/RAG path.

The next two live probes exposed and patched the deeper design issue. In
`runs/main_worker_live_runtime_resume_formalizer_semantic_anchor_consumption_probe/research_agent_runtime_manifest.json`,
the Formalizer authored a matching `hGoodRankImpliesCovered` request and a core
Lean helper in the same packet, but the normalizer only autofilled
source-binding metadata from prior runtime memory. The packet therefore could
not promote same-packet request/candidate pairs generically. The runtime now
enriches `source_to_bridge_premise_derivation_candidates` from candidate
requests emitted in the same Formalizer packet, while preserving the proof
boundary: copied metadata only makes the candidate eligible for validation and
later local Lean/AXLE checks.

`runs/main_worker_live_runtime_resume_formalizer_validation_repair_after_pending_premise_gate_probe/research_agent_runtime_manifest.json`
then reran the helper-only validation-repair handoff. The first LLM attempt was
rejected with a generic capability-eval error:
`helper-only formal_targets do not satisfy this gate` for pending premise
`hGoodRankImpliesCovered`; the retry was also rejected because it emitted a
source-to-bridge candidate shell without Lean source. The latest pending task is
`formalize-repair:conformal_prediction_coverage:c75867ab`. This is the right
design posture: Claude can still use helpers as diagnostics, but once runtime
memory says a source-to-bridge premise derivation is pending, progress requires
a concrete structured candidate with copied request metadata, required semantic
anchors such as `hC`, and verifier-ready Lean source, or an honest FORMAL_GAP.

The next continuation reached that structured-candidate shape. In
`runs/main_worker_live_runtime_resume_pending_premise_repair_followup_probe/research_agent_runtime_manifest.json`,
the Formalizer emitted four source-to-bridge premise derivation work orders,
including a no-import core `Prop` candidate for `hGoodRankImpliesCovered` whose
proof body is the exact source anchor application `hC hGoodRank`. The in-run
bridge still skipped local Lean on that row because the generic premise-name
check did not recognize premise names embedded as theorem-name segments and the
bridge injected `import Mathlib` into import-free core candidates. The bridge is
now patched generically: it preserves import-free source, removes the fallback
`import Mathlib`, and recognizes premise-name identifier segments in generated
declaration names. Replaying the live queue through
`runs/main_worker_live_runtime_resume_pending_premise_repair_followup_probe_after_bridge_patch/source_to_bridge_premise_derivation_bridge/source_to_bridge_premise_derivation_proofengineer_bridge_manifest.json`
with local Lean verifies one of four rows, the `hGoodRankImpliesCovered`
premise derivation. The remaining rows still fail for real missing-anchor or
wrong-declaration reasons. This is premise-derivation evidence only; the full
`split_conformal_finite_sample_coverage` source theorem and exact semantic
definitions remain unproved. The latest pending task is now
`critic:conformal_prediction_coverage:13db26c0`.

The in-band continuation is now recorded at
`runs/main_worker_live_runtime_resume_bridge_verified_critic_consumption_after_final_prune_probe/research_agent_runtime_manifest.json`.
It preserves the patched bridge evidence
(`source_to_bridge_premise_derivation_from_formalizer_bridge_n_kernel_verified=1`)
and fixes the stale-agenda design issue: the final
`runtime_next_action_agenda.jsonl` no longer carries
`formal_gap:source_to_bridge_premise_derivation` or stale
`hGoodRankImpliesCovered` gap rows. It exports one
`SOURCE_TO_BRIDGE_PREMISE_DERIVATION_KERNEL_VERIFIED` integration action for
`hGoodRankImpliesCovered`, while retaining unnamed adapter-object exact
semantic-definition gaps. The scorecard remains 42/49, the terminal pending
task is `formalize-critic-repair:conformal_prediction_coverage:f828c460`, and
the next step is to consume the verified premise in the adapter/exact proof path
without claiming full source theorem proof.

The verified-premise adapter retry patch then closed a bounded-memory handoff
gap. Runtime learning compaction now pins kernel-verified source-to-bridge
premise derivations and adapter blockers, and the proof-bank summary treats a
verified premise row as enough adapter retry context even if the older adapter
feedback row has fallen out of the compacted window. A live resume at
`runs/main_worker_live_runtime_resume_verified_premise_adapter_retry_after_memory_patch_probe/research_agent_runtime_manifest.json`
loaded 30 memory rows, retained the verified `hGoodRankImpliesCovered` premise,
queued one source-theorem proof-body adapter work order for
`split_conformal_finite_sample_coverage`, and ran the adapter bridge. The bridge
replay at
`runs/main_worker_live_runtime_resume_verified_premise_adapter_retry_after_memory_patch_bridge_replay/source_theorem_proof_body_adapter_proofengineer_bridge_manifest.json`
also removed the bad root `import Mathlib` fallback from core `Prop` adapter
skeletons. The adapter still does not kernel-verify; it is a generated
non-evidence skeleton with unsolved goals. The next worker should generate a
real adapter proof candidate that consumes the verified premise and then rerun
the exact proof-body path, while keeping exact semantic-definition gaps as
formal blockers rather than proof evidence.

The next patch makes that handoff less brittle. The adapter bridge now extracts
checked Lean signature excerpts from verified source-to-bridge premise artifacts
and carries them through learning rows, bounded memory, proof-bank summaries,
and Formalizer prompts. Replaying the adapter bridge at
`runs/main_worker_live_runtime_resume_verified_premise_adapter_retry_signature_context_bridge_replay/source_theorem_proof_body_adapter_proofengineer_bridge_manifest.json`
still correctly leaves the adapter unverified, but the row and skeleton now show
the exact checked `hGoodRankImpliesCovered` theorem header. A two-iteration live
continuation at
`runs/main_worker_live_runtime_resume_verified_premise_adapter_signature_context_probe/research_agent_runtime_manifest.json`
kept the scorecard at 42/49, emitted four source-to-bridge premise work orders
with one kernel-verified row, and surfaced the real next blocker: reviewed
adapter-object semantic definitions for `coverage_event`, `good_rank_event`,
and `C_n`. Bounded memory now pins the latest unique copies of those blockers
plus adapter feedback carrying verified premise ids/signatures, so a short
resume window does not forget either the checked premise or the
semantic-definition frontier.

The latest bridge hygiene patch keeps that frontier from duplicating itself.
Replaying the same live source-to-bridge queue through
`runs/main_worker_live_runtime_resume_verified_premise_adapter_signature_context_deduped_semantic_work_orders_replay/source_to_bridge_premise_derivation_bridge/source_to_bridge_premise_derivation_proofengineer_bridge_manifest.json`
still sees four input premise work orders and one kernel-verified premise
derivation, but now emits exactly three adapter-object semantic-definition work
orders instead of nine repeated rows. The merged work orders are
`coverage_event`, `good_rank_event`, and `C_n`; each carries all three live
adapter-instantiation group ids plus required bridge premises
`hGoodRankImpliesCovered` and `hQuantileThreshold`. This is queue hygiene and
repair context only. The reviewed exact semantic definitions, real adapter
proof candidate, and full source theorem proof remain open.

The next patch makes the metadata path artifact-first instead of heuristic-first.
Source-to-bridge candidate-request rows now preserve
`premise_semantic_dependency_requirements` through metadata authoring memory,
the Formalizer prompt asks for requirements grounded in retrieved formal-source
declarations, prover diagnostics, or exact theorem binders, and the premise
bridge consumes explicit work-order/request/grouped-request requirements before
falling back to local inference. A regression verifies that an explicit
retrieved requirement overrides the older conformal coverage hint in both the
check row and generated skeleton. Replaying the latest live queue at
`runs/main_worker_live_runtime_resume_verified_premise_adapter_signature_context_artifact_semantic_requirements_replay/source_to_bridge_premise_derivation_bridge/source_to_bridge_premise_derivation_proofengineer_bridge_manifest.json`
preserved the current frontier: four input premise work orders, three merged
semantic-definition work orders, and one kernel-verified premise derivation.
This is still non-proof routing context until local Lean/AXLE verifies the
exact semantic definitions, adapter proof, and full source theorem.

The current design cleanup addresses the brittleness behind the latest live
packet-validation loop. Formalizer packet normalization now treats any emitted
Lean source as executable work and marks it
`expected_status=NEEDS_KERNEL_CHECK`; only empty source-theorem gap rows remain
`FORMAL_GAP`. It also reroutes helper/adapter-shaped Lean candidates that were
mislabeled as probability/coverage source-theorem targets into diagnostic
helper rows, then adds an explicit empty source-theorem `FORMAL_GAP`. This is
artifact-contract repair, not proof evidence. The live follow-up at
`runs/main_worker_live_runtime_resume_target_shape_normalizer_probe/research_agent_runtime_manifest.json`
still reports scorecard 42/49, but the validator failure has narrowed to the
real semantic blocker: the source-to-bridge candidate must reference
`hQuantileThreshold` and `hGoodRank` non-vacuously, or emit no executable
candidate and report that exact semantic-anchor gap.

The follow-up cleanup converts that remaining packet-validation loop into a
typed non-proof blocker instead of another ad hoc theorem patch. Formalizer
normalization now drops source-to-bridge candidates whose Lean source omits
required semantic anchors outside comments, records
`source_to_bridge_semantic_anchor_blocker`, and removes executable next-actions
for the dropped candidate. The live resume at
`runs/main_worker_live_runtime_resume_semantic_anchor_blocker_normalized_probe/research_agent_runtime_manifest.json`
preserved one kernel-verified `hGoodRankImpliesCovered` premise derivation and
three adapter-object semantic-definition work orders, dropped one invalid
candidate missing `hQuantileThreshold`, `hGoodRank`, and `hExch`, and moved the
pending task to ProofEngineer Lean precheck repair
`formalize-lean-repair:conformal_prediction_coverage:a5b6f426`. This is the
right design boundary: Claude can propose Lean, R/Python, and proof plans, but
unanchored bridge derivations become explicit semantic/prover work, not
runtime-approved proof evidence.

The next routing cleanup keeps adapter proof attempts inside the adapter bridge
instead of duplicating them as generic Formalizer Lean-candidate repairs.
Rerouted source-to-bridge adapter helpers now carry
`runtime_materialization_route=source_theorem_proof_body_adapter_bridge`, and
the generic materializer skips adapter-named formal targets when
`source_theorem_target_known=false`. The first live probe at
`runs/main_worker_live_runtime_resume_adapter_route_normalized_probe/research_agent_runtime_manifest.json`
showed why the fallback was needed: Claude emitted a direct adapter target with
`source_theorem_target_known=false` and an unavailable
`Mathlib.Algebra.Order.Floor` import, which still entered generic precheck. The
follow-up at
`runs/main_worker_live_runtime_resume_adapter_route_direct_skip_probe/research_agent_runtime_manifest.json`
moved out of Formalizer Lean precheck entirely: the pending task is now
`critic:conformal_prediction_coverage:a68cd26d`, with no candidate diagnostics,
while adapter failures remain in
`runtime_source_theorem_proof_body_adapter_proofengineer_bridge` as
`adapter_candidate_not_evidence_eligible` or adapter/local Lean environment
blockers. Scorecard remains 42/49; helper/subclaim rows reached 44, but no
source theorem or full frontier theorem is proved.

The latest exact-semantic queue cleanup is a design-level handoff fix, not a
new theorem shortcut. After
`runs/main_worker_formalizer_after_full_exact_queue_feedback_live`, the Critic
resume `runs/main_worker_resume_critic_placeholder_resource_requests_live`
generated four typed exact semantic-definition blocker requests from the full
queue, preserving `good_rank_event`, `C_n`, `coverage_event`, and `covered` as
separate placeholder-level work for FormalSourceRetriever/proof search/Lean
LSP/local Lean. The follow-up Formalizer resume
`runs/main_worker_formalizer_after_placeholder_resource_requests_live` consumed
those requests, kept `kernel_verified_subclaims=72` and `formal_gaps=54`, and
ended with pending task `formalize-repair:conformal_prediction_coverage:c297d6c1`
because the local packet validator rejected a non-theorem Lean sketch in a
`formal_targets` row. Repair feedback now explicitly distinguishes executable
Lean theorem/lemma candidates from empty `FORMAL_GAP` source-theorem rows with
typed blockers. The source theorem is still unproved; exact proof-body execution
remains gated by semantic review/import repair and local Lean/AXLE verification
of the intended declaration.

The next resume fixed the stale-carried-feedback shape rather than adding a
new conformal special case. Pending Formalizer repair tasks now refresh
`validation_repair_directives` from their stored `validation_errors` at
resume-time, so older manifests inherit the current validator contract before
Claude is prompted again. The live continuation at
`runs/main_worker_formalizer_after_validation_directive_refresh_live` cleared
the non-theorem Lean-sketch loop and handed off to
`critic:conformal_prediction_coverage:de008099`, with
`kernel_verified_subclaims=74`, `formal_gaps=55`, and scorecard 44/49 not ready.
The source theorem row is an empty `FORMAL_GAP`, while the executable bridge
helper is explicitly marked `source_theorem_target_known=false`. One
`hGoodRankImpliesCovered` source-to-bridge premise derivation compiled locally
as premise-derivation evidence only; the source theorem and semantic
definitions remain unproved. The exact semantic-definition Lean repair frontier
is still three typechecked definition candidates requiring review plus the
`C_n` Lake/import-environment repair blocker.

The next Critic/Formalizer turn exposed and fixed another handoff-shape issue:
Critic regenerated one exact-semantic blocker request per placeholder, but the
placeholder, gate, and queue status were only embedded in prose. The request
converter now emits `placeholder_symbol`, `proof_body_gate_status`,
`runtime_queue_status`, and `request_fingerprint` as first-class fields, and
the merged exact-semantic repair feedback carries compact gate/status summaries.
The patched Critic replay
`runs/main_worker_critic_after_exact_request_metadata_v2_live` hands off
`formalize-critic-repair:conformal_prediction_coverage:64946840` with four
machine-actionable exact-semantic blocker requests. The consuming Formalizer run
`runs/main_worker_formalizer_after_exact_request_metadata_live` advanced support
subclaims to 76 and formal gaps to 56, then rerouted to
`critic:conformal_prediction_coverage:07104fdc`. The source theorem remains an
empty `FORMAL_GAP`; the new executable helper remains
`source_theorem_target_known=false`; and exact semantic-definition repair still
requires review of three typechecked candidates plus the `C_n` import/Lake
environment blocker.

The follow-up Critic replay showed that late exact-semantic work-order memory
also has to update the pending task agenda, not only blocker requests. The
runtime now injects `formal_gap:source_theorem_exact_semantic_definition_repair`
into `high_priority_agenda` when pending-task memory enrichment merges exact
semantic-definition repair feedback, ordered after formal-environment repair
when both are active. The patched Critic replay
`runs/main_worker_critic_after_exact_agenda_enrichment_live` handed off
`formalize-critic-repair:conformal_prediction_coverage:f32a20c8` with four
structured exact-semantic blocker requests and an explicit exact-semantic agenda
row. The consuming Formalizer run
`runs/main_worker_formalizer_after_exact_agenda_enrichment_live` advanced support
subclaims to 78 and formal gaps to 57, then rerouted to
`critic:conformal_prediction_coverage:d4a10a5c`. The source theorem and exact
semantic definitions remain unproved; this is still orchestration progress
toward reviewed definitions and a later local Lean/AXLE source-theorem proof.

The next live Critic replay exposed an evidence-boundary failure mode at the
CriticEvaluator layer itself. A prior live attempt died as a subsystem exception
when the optional LLM Critic packet included forbidden proof-completion wording.
CriticEvaluator now treats that as a local packet-validation event:
`RuntimeCriticEvaluatorValidationFailure` records the invalid packet as
`CRITIC_PACKET_VALIDATION_FAILURE_NOT_PROOF_EVIDENCE`, emits repair directives,
and then deterministic Critic routing continues to the appropriate
TheoryDeveloper/Formalizer/ProofEngineer task. The patched live replay
`runs/main_worker_critic_validation_failclosed_live` did not fail; it produced a
valid Critic proposal and handed off
`formalize-critic-repair:conformal_prediction_coverage:480c63dd` with the four
exact-semantic placeholders still present. The scorecard remains 44/49, support
subclaims remain 78, formal gaps remain 57, and the source theorem is still not
kernel verified.

The next Formalizer/ProofEngineer continuation
`runs/main_worker_formalizer_after_critic_validation_failclosed_live` consumed
that handoff, advanced support subclaims to 80 and formal gaps to 58, and
rerouted to `critic:conformal_prediction_coverage:a4147833`. It also exposed a
generic routing metadata bug: runtime truth-table feedback could route exact
source proof-body repair with an empty target when the manifest stored the
target only in list-valued proof-body repair fields. Runtime truth-table
learning rows now recover source-theorem target names from scalar target fields,
proof-body repair target-name lists, adapter target-name lists, exact repair
target-name lists, and deterministic theorem goals; generated agenda rows use
that target as `target_ids`. The patched Critic replay
`runs/main_worker_critic_after_truth_target_repair_live` now exports the
truth-table agenda for `split_conformal_finite_sample_coverage` and hands off
`formalize-critic-repair:conformal_prediction_coverage:380685c5`. The source
theorem remains unproved, with exact semantic review/import repair still the
active frontier.

The next Formalizer continuation showed that target identity still needed to be
first-class at the source-to-bridge and semantic-primitive queue boundary.
Fresh work orders had theorem names and goal lists, but not top-level
`target_ids`; nested premise-derivation candidate requests also lacked
`target_ids`. The runtime now stamps and backfills those fields for
source-to-bridge premise-derivation work orders, semantic primitive work orders,
and generated next-action rows. Helmholtz reviewed the patch and found a
multi-target smearing risk, so explicit `target_ids`, `target_id`, or
`source_theorem_goal_id` now win over broad `target_theorem_goal_ids` fallback.
The final live replay
`runs/main_worker_formalizer_after_explicit_target_boundary_live` keeps target IDs
complete across agenda rows, source-to-bridge work orders, semantic primitive
work orders, exact-semantic work orders, adapter work orders, promotion work
orders, the promotion handoff, and the blocked materialization seed. The score
remains 44/49 and the source theorem is still unproved; the correct next
frontier is reviewed exact semantic definitions plus the `C_n` Lean/import
environment blocker, not promotion of helper or retrieval evidence.

The follow-up Critic replay exposed one remaining target mismatch: the generic
local-Lean unavailable-import blocker from
`critic_local_lean_formalization_feedback` still targeted the question id
instead of the theorem goal. Unavailable-import blocker construction now
receives the full formalization manifest and prefers explicit target IDs plus
deterministic theorem goals before falling back to question id. The fresh live
replay `runs/main_worker_critic_after_import_blocker_target_fix_live` keeps four
high-priority agenda rows and 11 blocker requests with zero missing
`target_ids`; the local-Lean `Mathlib` unavailable-import request now targets
`split_conformal_finite_sample_coverage`. The handoff remains
FormalizationEvaluator work, and no source-theorem proof evidence is claimed.

The next Formalizer continuation exposed the same target-provenance bug at the
formal-environment repair boundary. The live artifact
`runs/main_worker_formalizer_after_import_blocker_target_fix_live/runtime_source_theorem_formal_environment_work_orders.jsonl`
had 74 `SourceTheoremFormalEnvironmentWorkOrder` rows with theorem names but no
top-level `target_ids`; Helmholtz then found the downstream
formal-environment ProofEngineer bridge dropped the same identity in repair
packets, signature probes, runtime learning rows, and possible proof-body work
orders. Runtime formal-environment producers and the bridge now derive target
identity from explicit `target_ids`/`target_id`/`source_theorem_goal_id` before
falling back to broad `target_theorem_goal_ids` or theorem names. Deterministic
replay over the saved 74-row result and targetless live queue now yields zero
missing `target_ids` in work orders, repair packets, signature probes, and
learning rows. This is still routing/provenance repair only; the exact source
theorem remains unproved.

The next live continuation
`runs/main_worker_formalizer_after_formal_env_target_provenance_live/research_agent_runtime_manifest.json`
advanced the scorecard to 44/49 with 110 kernel-verified support subclaims and
73 formal gaps, but exposed one more route-critical target leak:
`formalizer_lean_candidate_kernel_feedback` learning rows were pinned into
runtime memory without `target_ids`. Formalizer Lean candidate materialization
now derives canonical target context from candidate metadata and
`source_theorem_target_provenance`, copies it into candidate rows, learning
rows, live proof-state requests, compact memory summaries, and memory retention
pin keys, and normalizes truth-table feedback to the same `target_ids` alias.
Because long resume chains can carry old materialization manifests with stale
embedded learning rows, runtime learning export now recomputes Formalizer
candidate learning rows from `candidate_rows` instead of trusting precomputed
targetless rows. A fresh live continuation
`runs/main_worker_critic_after_formalizer_memory_target_ids_live/research_agent_runtime_manifest.json`
still ends at the expected 44/49 scorecard gate, then deterministic replay over
its saved result regenerates 75 Formalizer candidate feedback rows with zero
missing `target_ids`; six old helper rows without source-theorem provenance are
scoped to their local Lean declaration but leave theorem-goal identity empty.
This is memory/routing repair only; helper compilation remains non-proof
evidence for the source theorem.

The next audit-alignment patch fixes a related Architect evidence-boundary
smell. Long resume chains can keep the architect-prefixed `runtime_stage` while
the current iteration budget executes only a pending Formalizer/ProofEngineer
or Critic task. The runtime manifest now records
`runtime_architect_coordinator_registered`,
`runtime_architect_coordinator_executed`, and
`n_runtime_architect_coordinator_traces`; the evidence truth table reports
`architect_control=PROPAGATED_FROM_RESUME` when Architect-derived context is
carried but no `ArchitectCoordinator` trace ran. Recomputing the audit over
`runs/main_worker_formalizer_after_primary_typechecked_review_routing_live`
keeps the strict scorecard blocker `architect_orchestrated=false` while still
preserving the propagated research-path contract as continuity context. This
avoids overstating subsystem resume runs as live Architect-controlled
capability evidence.

The follow-up runtime/eval patch makes that boundary actionable instead of only
auditable. `research-agent-runtime --resume-runtime-manifest` keeps the old
exact-pending-task behavior by default, but a new `--resume-through-architect`
mode runs an `ArchitectCoordinator` resume-review turn first, then reroutes to
the original pending subsystem task with refreshed `architect_context` and a
typed `runtime_resume_review` object. The runtime manifest records the
Architect trace counters, and `research-agent-runtime-audit` accepts the
resume-specific sequence `ArchitectCoordinator -> original pending owner`
without pretending that a full cold-start subsystem chain was replayed. This is
the path future capability resumes should use when the claim is
Architect-controlled runtime continuation.

## Delegation To Other Codex Workers

These are useful parallel lanes, but the main worker should integrate their
outputs into the runtime path:

- Formalizer/ProofEngineer worker: repair the remaining semantic-anchor gap for
  `hQuantileThreshold` and `hGoodRank`, and keep helper/adapter candidates out
  of source-theorem proof evidence unless local Lean/AXLE verifies the intended
  formal claim.
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
