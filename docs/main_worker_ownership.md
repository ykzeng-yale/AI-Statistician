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

Live evidence collected on 2026-06-25:

- `runs/main_worker_doctor_live_env/doctor_manifest.json`: live environment
  ready for Anthropic and AXLE when keys are loaded via process environment.
- `runs/main_worker_live_runtime_minimal/research_agent_runtime_manifest.json`:
  5-iteration budget reached only SimulationEvaluator repair; scorecard 29/49.
- `runs/main_worker_live_runtime_minimal12/research_agent_runtime_manifest.json`:
  12-iteration budget reached generated algorithm fail-then-pass repair and
  Formalizer/ProofEngineer local Lean diagnostics; scorecard 32/49.

The 12-iteration run is evidence for live generated-code execution, one
AlgorithmEngineer repair sequence, Formalizer candidate materialization, local
Lean tool calls, and proof-state feedback rows. It is not source theorem proof:
`real_kernel_verified_subclaims=0`, `formal_gaps=3`, and the terminal state was
`MAX_ITERATIONS_REACHED` with a pending ProofEngineer repair task.

## Delegation To Other Codex Workers

These are useful parallel lanes, but the main worker should integrate their
outputs into the runtime path:

- Formalizer/ProofEngineer worker: fix conformal target-shape drift and ensure
  repaired candidates preserve the probability/coverage theorem shape.
- Algorithm/Simulation worker: attach generated code repair sequences to the
  current task, not only aggregate history.
- Proof-library worker: add reusable statistics kernels with local Lean/AXLE
  manifests.
- RAG/OpenProver worker: feed source hits and prover diagnostics into
  Formalizer/ProofEngineer prompts without treating retrieval as proof.
- Cross-task evaluation worker: add non-conformal task-family capability runs.

The main worker should not delegate away the integration burden: every lane
must end in runtime artifacts, evidence ledger rows, tests, and a GitHub-visible
branch or PR.
