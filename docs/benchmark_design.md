# StatInferBench Design

`StatInferBench` is the benchmark family for Lean statistical inference tasks.

## Task Types

- `formal_only`: theorem statement is fixed; model outputs a proof.
- `formalization`: natural-language claim is provided; model outputs Lean statement and proof.
- `repair`: broken Lean proof is provided; model repairs it.
- `subgoal_completion`: proof context and goal are provided; model closes the goal.
- `lemma_growth`: model proposes and proves a reusable helper lemma.

## Difficulty Ladder

- `S0`: solved by `simp`, `rfl`, or direct theorem application.
- `S1`: one relevant premise plus rewriting.
- `S2`: 3 to 8 tactic steps.
- `S3`: requires a local helper lemma.
- `S4`: requires a new reusable abstraction.
- `S5`: requires refactoring theorem statements or assumptions.

## Domain Tags

- `asymptotic_calculus`
- `convergence_in_probability`
- `convergence_in_distribution`
- `empirical_process`
- `erm_consistency`
- `m_estimation`
- `z_estimation`
- `influence_function`
- `causal_identification`
- `ipw`
- `aipw`
- `bootstrap`

## Evaluation

Primary metrics:

- proof completion rate;
- pass@k;
- valid tactic rate;
- local lemma usage;
- unknown identifier rate;
- timeout rate;
- verifier calls per solved proof;
- average proof length;
- curation acceptance rate.

Train/dev/test splits must be by dependency cluster so the test set measures generalization to new theorem families, not memorization of nearby proofs.

