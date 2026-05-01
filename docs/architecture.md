# StatLeanAgent Architecture

StatLeanAgent is a verifier-first multi-agent system for Lean formalization of statistical inference. It is not a single theorem-proving model. It is a coordinated workflow where agents propose formal statements, search premises, generate proofs, verify with Lean, mine reusable lemmas, curate a growing library, and train better models from verified traces.

## Core Principle

Lean verification is necessary but not sufficient. A theorem can compile and still be statistically meaningless if its assumptions encode the conclusion or if the formal statement drifts from the intended claim. The system therefore separates:

- kernel correctness: checked by Lean;
- formalization fidelity: checked by formalization critics and humans;
- library usefulness: checked by curation and downstream reuse;
- training utility: checked by benchmark performance.

## Agent Roster

The initial system has 14 agents.

| Agent | Responsibility | Code ownership |
|---|---|---|
| Problem Ingest | Normalize textbook/paper/user claims into `StatClaim` records. | `schemas/stat_claim.schema.json`, raw claim artifacts |
| Formalization | Produce Lean theorem skeletons and definition variants. | `StatInference/`, `schemas/lean_task.schema.json` |
| Library Cartographer | Retrieve mathlib, seed-project, and local premises. | premise indexes and retrieval code |
| Proof Planner | Decompose target theorems into subgoals and sublemmas. | proof plans |
| Tactic Synthesizer | Generate stepwise tactics from proof states. | tactic attempts |
| Whole-Proof Generator | Generate complete proof candidates. | whole proof attempts |
| Verifier | Run Lean/Pantograph/Kimina Lean Server and normalize feedback. | verification artifacts |
| Error Repair | Classify failures and propose minimal patches. | repair artifacts |
| Lemma Miner | Identify reusable lemmas from traces and failures. | lemma candidates |
| Library Curator | Promote only useful, verified, non-vacuous lemmas. | curation policy |
| Benchmark Generator | Produce `StatInferBench` tasks and splits. | benchmarks and schemas |
| Reward and Evaluation | Score attempts and model performance. | reward code and eval logs |
| Trainer | Build SFT, DPO, and GRPO datasets/runs. | training manifests |
| Worktree Steward | Allocate isolated worktrees and branches. | worktree manager |

## Data Flow

```text
Natural-language theorem
  -> Problem Ingest Agent
  -> StatClaim
  -> Formalization Agent
  -> LeanTask
  -> Library Cartographer
  -> premise bundle
  -> Proof Planner
  -> proof plan + sublemma candidates
  -> Tactic Synthesizer / Whole-Proof Generator
  -> ProofAttempt
  -> Verifier
  -> VerificationReport
  -> Error Repair or Library Curator
  -> Benchmark Generator
  -> Trainer
```

## Verifier Loop

The verifier loop is the core runtime.

1. Generate a Lean statement or proof attempt.
2. Run Lean through Lake, Pantograph, Kimina Lean Server, or optional AXLE
   helper calls.
3. Parse diagnostics, proof states, first failing tactic, and local progress.
4. Reject any proof containing `sorry`, `admit`, unreviewed `axiom`, or unsafe shortcuts.
5. Feed the normalized result to repair, reward, curation, and training.

AXLE is a repair and extraction assistant, not the acceptance authority.  It can
run `check`, `extract_decls`, `repair_proofs`, `sorry2lemma`, and related tools
on standalone Lean snippets, but any candidate copied into `StatInference` must
still pass local `lake build` and semantic review.

## Worktree Isolation

Agents that may write code must work in isolated git worktrees:

```text
.worktrees/
  formalization/        branch agent/formalization
  tactic-synthesizer/   branch agent/tactic-synthesizer
  benchmark-generator/  branch agent/benchmark-generator
```

The main checkout remains the integration branch. No agent should write directly to another agent's owned paths. The Library Curator and Worktree Steward are responsible for merge readiness.

## Library Growth Policy

The system follows curated lemma growth, not free axiom invention.

A lemma can be promoted only if:

- Lean verifies it without `sorry`;
- it introduces no unreviewed axioms;
- it has explicit assumptions;
- it is not a duplicate of mathlib or the local library;
- it is used by at least one downstream task or unlocks a planned theorem cluster;
- it has semantic notes explaining the statistical meaning;
- it does not make assumptions that trivially encode the conclusion.

## Training Loop

Training proceeds only after a seed library and benchmark exist.

1. SFT on accepted proof traces and human-written Lean proofs.
2. DPO on Lean-labeled preference pairs: accepted or locally useful attempts versus rejected attempts.
3. GRPO with dense verifier rewards: proof completion, valid tactic count, goal closure, premise use, first-error position, timeout penalties, and forbidden-token penalties.

The first production-scale RL backend should be `verl` plus Kimina Lean Server. Early debugging can use TRL.
