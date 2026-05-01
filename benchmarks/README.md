# StatInferBench

This directory will contain generated and curated benchmark tasks for statistical inference theorem proving in Lean.

Seed benchmark families:

- asymptotic calculus;
- asymptotic bridge projections;
- convergence in probability and distribution;
- ERM consistency;
- estimator interfaces;
- empirical process bounds;
- M-estimation and Z-estimation;
- causal identification;
- causal bridge projections;
- influence-function linearization.
- theorem-hole subgoal-completion tasks for multi-goal proof repair.

`seeds.jsonl` is the checked-in deterministic seed benchmark database. Regenerate it from
the typed Python registry with:

```bash
statlean seed-benchmarks --output benchmarks/seeds.jsonl
```

Each record is a `BenchmarkTask` with a rendered `LeanTask`. Use
`statlean render-task <task_id>` for prompt construction and
`statlean verify-benchmarks` to produce verifier reports.

The theorem-hole tasks are marked as `subgoal_completion` and set
`lean_task.allowed_sorry = true`.  This confines placeholders to benchmark
skeletons used for proof-repair data; the `StatInference` Lean library itself
must remain free of `sorry`, `admit`, `unsafe`, and unreviewed axioms.
