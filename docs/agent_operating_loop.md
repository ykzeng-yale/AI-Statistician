# Agent Operating Loop

The 14-agent system is an execution architecture, not a claim of full autonomy.
Each stage emits typed artifacts that can be checked, benchmarked, and reused.

## Stages

1. `problem_ingest`: normalize textbook/paper claims into `StatClaim`.
2. `formalization`: produce Lean theorem skeletons without changing meaning.
3. `library_cartographer`: retrieve mathlib and local `StatInference` premises.
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
13. `trainer`: generate SFT/DPO/GRPO manifests and launch training jobs.
14. `worktree_steward`: isolate code-writing agents in git worktrees.

## Promotion Gate

A result can be promoted only if:

- `pytest` passes;
- benchmark JSONL can be regenerated deterministically;
- Lean builds in CI;
- no forbidden proof placeholders are accepted;
- the theorem is not a duplicate or vacuous restatement;
- the owning agent reports changed files and validation.

## Monitoring

Monitoring checks:

- GitHub Actions status for Python and Lean jobs;
- benchmark task count and split balance;
- accepted/rejected verifier status counts;
- local lemma usage in benchmark tasks;
- new `sorry`/`admit`/`axiom`/`unsafe` occurrences;
- whether recent commits increased or reduced proof/eval coverage.

