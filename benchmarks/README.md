# StatInferBench

This directory will contain generated and curated benchmark tasks for statistical inference theorem proving in Lean.

Initial benchmark families:

- asymptotic calculus;
- convergence in probability and distribution;
- ERM consistency;
- empirical process bounds;
- M-estimation and Z-estimation;
- causal identification;
- influence-function linearization.

`seeds.jsonl` is the initial checked-in benchmark database. Regenerate it from
the typed Python registry with:

```bash
statlean seed-benchmarks --output benchmarks/seeds.jsonl
```

Each record is a `BenchmarkTask` with a rendered `LeanTask`. Use
`statlean render-task <task_id>` for prompt construction and
`statlean verify-benchmarks` to produce verifier reports.
