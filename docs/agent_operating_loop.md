# Agent Operating Loop

The 14-agent system is an execution architecture, not a claim of full autonomy.
Agents propose artifacts; Lean, tests, CI, and humans decide what is accepted.

Each stage emits typed artifacts that can be checked, benchmarked, reused, and
traced back to a worktree or agent heartbeat.

## Green Baseline Contract

An agent may call a change ready only after it reports:

- changed files and owning agent;
- `pytest` or `.venv/bin/pytest` status;
- `lake build` status when Lean files or benchmark Lean tasks changed;
- benchmark regeneration or verification status when benchmark artifacts changed;
- retrieval index or SFT/DPO/GRPO manifest regeneration status when those
  artifacts changed;
- unresolved blockers and any human decisions needed.

## Stages

1. `problem_ingest`: normalize textbook/paper claims into `StatClaim`.
2. `formalization`: produce Lean theorem skeletons without changing meaning.
3. `library_cartographer`: index and retrieve mathlib plus local
   `StatInference` premises.
4. `proof_planner`: decompose theorem into sublemma candidates.
5. `tactic_synthesizer`: generate state-local tactics.
6. `whole_proof_generator`: generate full proof candidates when stepwise search
   is inefficient.
7. `verifier`: run Lean/Pantograph/Kimina and normalize feedback.
8. `error_repair`: classify failures and propose minimal repairs.
9. `lemma_miner`: extract reusable helper lemmas from traces and failures.
10. `library_curator`: gate promotion into the Lean library.
11. `benchmark_generator`: convert holes/traces into `StatInferBench`.
12. `reward_eval`: score attempts and aggregate metrics.
13. `trainer`: generate auditable SFT/DPO/GRPO manifests.
14. `worktree_steward`: isolate code-writing agents in git worktrees.

## Promotion Gate

A result can be promoted only if:

- `pytest` passes;
- benchmark JSONL can be regenerated deterministically when benchmark seeds
  changed;
- Lean builds locally and in CI when Lean-facing code changed;
- no forbidden proof placeholders are accepted;
- the theorem is not a duplicate or vacuous restatement;
- retrieval and training artifacts cite their source benchmark/verifier inputs;
- the owning agent reports changed files, validation, and blockers;
- a human reviewer approves statistical meaning and theorem strength.

## Heartbeat Monitoring

Each active worker should emit a compact heartbeat with:

- agent id and role;
- branch or worktree;
- current task and touched paths;
- last validation command and result;
- next action or blocker;
- timestamp.

The monitor should flag:

- missing or stale heartbeats;
- failing GitHub Actions jobs for Python or Lean;
- benchmark task count, split balance, or verifier-status drift;
- stale retrieval indexes or training manifests;
- new `sorry`/`admit`/`axiom`/`unsafe` occurrences;
- unexpected edits outside an agent's assigned files.

## Human-Guided Boundary

The system is human-guided because formal verification is necessary but not
sufficient. Lean can reject bad proofs, but it cannot choose the research
agenda, validate modeling assumptions, detect every vacuous statistical
definition, or decide that a benchmark split is scientifically fair.

Humans remain responsible for theorem selection, statistical semantics,
promotion into `StatInference`, held-out benchmark policy, baseline
interpretation, and approval of SFT/DPO/GRPO training runs.
