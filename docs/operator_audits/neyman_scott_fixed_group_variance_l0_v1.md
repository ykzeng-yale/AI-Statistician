# Operator audit: Neyman-Scott fixed-group variance L0 v1

## Immutable draw boundary

Task `neyman_scott_fixed_group_variance_known_result` consumed exactly one
fresh product draw and exactly one post-runtime hidden evaluation from sealed code
head `18019bb7f213042ae32e791febc45c89f5ba1326`. All seven enabled roles used exact
`claude-haiku-4-5-20251001`; no Sonnet or Opus call occurred.

The immutable run is:

`runs/main_worker_research_l0_neyman_scott_20260827_v1_codex_workspace_exact_haiku`

Product status was `ACCEPTED`, research completion was `1/1`, and automated hidden
gold was `1/1`. Formalization was correctly not applicable, and neither Formalizer
nor the formal-target reviewer executed. This task must never be rerun, resumed,
repaired, hidden-evaluated again, rescored, or resampled.

## What executed

The single AgentRuntime graph consumed eleven outer steps:

1. Architect selected the Theory workspace.
2. TheoryDeveloper used one persistent Markdown/LaTeX workspace with exact reads,
   writes, Python scratch observations, and an explicit checkpoint.
3. A separate read-only theory-referee session accepted the two current documents.
4. AlgorithmEngineer authored, executed, revised, and committed one Python estimator.
5. An isolated source reviewer probed and accepted the exact estimator source.
6. SimulationEvaluator authored and executed an exploratory diagnostic against the
   accepted estimator.
7. An isolated source reviewer accepted the exploratory source.
8. The same Simulation owner converted the current source into a preregistered
   confirmatory evaluator and executed an authoring diagnostic.
9. A second isolated review accepted that exact confirmatory source.
10. AgentRuntime replayed the frozen source on the withheld confirmatory cohort; all
    four designs passed at 128 replicates and made 512 bound-estimator invocations.
11. Critic accepted theory, scientific code, and empirical dimensions and disclosed
    the finite-design and non-proof boundaries.

This is real evidence for persistent model-tool-observation workspaces, exact source
binding, independent source review, confirmatory replay, optional formalization, and
post-runtime hidden-evaluator isolation. It is not trustworthy full-task theory
capability because the accepted mathematical authority is internally false.

## Operator findings

### 1. The active probability-limit derivation contains a false equality

The authoritative theory correctly derives

`sigma_hat_ML_squared = RSS/(N*T)`

and

`RSS/[N*(T-1)] -> sigma_squared`.

At lines 121-124 of `neyman_scott_theory.md`, however, it writes

`RSS/(N*T) = (1/T) * {RSS/[N*(T-1)]} * ((T-1)/T)`

and then claims that the right-hand side converges to
`((T-1)/T)*sigma_squared`. Both steps are false: the displayed product has one
extra factor `1/T` and would converge to `((T-1)/T^2)*sigma_squared`. The correct
factorization is

`RSS/(N*T) = {RSS/[N*(T-1)]} * ((T-1)/T)`.

The document's final limit is correct, but a correct conclusion does not deactivate
the false intermediate equality used to derive it. This is a material active
derivation error under the frozen theory contract.

### 2. The independent referee repeated the error and misread its own scratch output

The preflight report repeats the same extra-`1/T` factor at lines 99-105 and calls
the transition correct. It also reports the correct formula

`Var(sigma_hat_ML_squared) = 2*(T-1)*sigma_squared^2/(N*T^2)`

but then evaluates it as `0.00444` for `N=10`, `T=3`, and
`sigma_squared=1`. The actual value is `4/90 = 0.04444`. Its observed scratch
variance `0.0453` is close to the exact target, yet the report calls it a 920%
Monte Carlo discrepancy and rationalizes that nonexistent discrepancy as sampling
noise.

The report later describes a simulation target with an extra `N` in the variance
denominator. The terminal Critic repeats that wrong denominator and the erroneous
`0.00444` narrative while marking theory `SUPPORTED`. These are correlated model
judgment failures, not missing files, missing tools, or runtime-authored mathematics.

### 3. Automated semantic authority false-accepted the active contradiction

The frozen mechanical theory harness passed `7/7`. The exact-Haiku semantic judge
first passed all `12/12` opaque calibration cases, then marked the candidate document
`PASS` and all `8/8` rubric claims `SATISFIED`. Its prompt explicitly said that a
correct final conclusion cannot cancel a false intermediate derivation, but the model
still selected supporting passages and missed the displayed contradiction.

The calibration suite included concise wrong-denominator, wrong-degrees-of-freedom,
dimensional, asymptotic-regime, contract, and evidence-authority negatives. It did not
exercise a realistic long-form candidate that states the correct headline result
while retaining one false load-bearing equality under the exact integrated candidate
schema. Passing concise calibration is therefore not semantic authority for this
long document.

Operator inspection overrides the automated pass. The task receives no trusted
theory or full-task capability credit.

### 4. Scientific code and empirical components pass independently

The exact accepted estimator source identity
`e65feb98ca480efbd930ec7d0d735c177d5854e586289b6f0840b2894f71be43`
passed all fifteen hidden algorithm checks. It implements the within-group RSS,
`RSS/(N*T)`, and `RSS/[N*(T-1)]`, rejects the frozen malformed-input cases, and
satisfies the declared invariances.

The evaluator-only empirical component passed all twelve checks across six frozen
designs and 12,000 accepted-estimator invocations. Runtime's separately frozen
confirmatory source also used the bound accepted estimator mechanically and all four
of its designs passed. These results support implementation and finite-design
behavior only; they cannot repair or prove the invalid active derivation.

### 5. Runtime and hidden-evaluator boundaries remained sound

The run contains no hidden-authority path, hidden expected value, or hidden result in
the runtime artifact store, traces, observations, or handoffs. Hidden evaluation ran
only after AgentRuntime terminated and generated no runtime feedback. Runtime marked
simulation as non-proof evidence, formalization as not applicable, and kernel proof
as absent. The failure is scientific judgment, not evidence leakage or proof-status
inflation.

## Evidence hashes

- Visible question file bytes: `09e8e31029a52efdafeb08f69a47534f56011153e0edd0a784cc3e15d3e71db5`
- Frozen gold manifest stable identity: `c53f443ec4764d77cd4f66cf0f705145ee9eef367fc1e9c5505f32a6ba1c2de8`
- Frozen gold manifest bytes: `4fae41b5a1092b425b3882e845d7958ecbee4580fe57d3a5c4550d521e6acfb8`
- Runtime manifest bytes: `f156fcd031764ff7ae507b047f4febe1f0d76e5bff6cd5f4de35cfe680e9f480`
- Runtime result bytes: `3cc9983efde2a67e4b33b7babe603284a65df1492f8da48e19bbc16701693184`
- Hidden evaluation bytes: `0627929ab887214f3277203ae9b3c01512a2e96712b254f4c7d689c01300818f`
- Runtime LLM topology bytes: `07199a7198d75729529f4f76f7ebc20537371b06fbc601e12d2aa8c6381906d2`
- Accepted theory packet: `cbf38f4a8d0895fe4786f1ed369f5769055e9ff36ae4b989e8a63d8a9d163d51`
- Accepted theory document set: `f6095600ba69c333cf20c8824b63b548687dc11677803ab014773c21169c6786`
- Theory document bytes: `3bc3105eaa3bc182144b1760b695d232212777e40e9e8969a3ba3efb98c0fe0a`
- Estimator document bytes: `6b07f232ebe52057b2aa5f5b9a95b27e11bdd74c98d871dec6061f3e073f4bb0`
- Theory review bytes: `74738a8aa3b6359489af99fa2898b0aa3a22d944d95b2c6da77ac82cd292951b`
- Confirmatory source file bytes: `7b0f2733549bcc277954817da0e01b41083d2db7e97bb144ff57d189a66a9975`
- Hidden theory mechanical result: `2448162397b7703a7f48b7085f566f96c6179c7bac3eeaf4f72af86fd45a11b6`
- Hidden theory semantic result: `5161a6d6d5a73a447ee94f079fdf27fd12aa8a98e07fdb32068a91e280cafb56`
- Hidden algorithm result: `d9c0f5b445e73a20cab953fd0f12ffec6139aff7c00b1dad9df18a96fbe462ce`
- Hidden empirical result: `571ff896acae2d5d38df3729799202399a5ac57b6711822d51ad97c7516f52a6`

## Disposition and future boundary

Operator disposition:

`OPERATOR_INVALIDATED_ACTIVE_THEORY_AND_CORRELATED_REVIEW_FALSE_POSITIVE`

Trusted full-task capability remains `4/69`.

No product-runtime correction is justified from this consumed output. The current
Theory and referee prompts already require exact workspace reads, independent
reconstruction, small cases, dimensional checks, complete-proposition scratch, and
rejection of false intermediate steps. Adding a Neyman-Scott rule, formula parser,
another reviewer, repeated sampling, retry, repair worker, scheduler, or model
escalation would overfit this draw and obscure the measured exact-Haiku limit.

Before the next unrelated task is activated, its sealed semantic evaluator authority
should run the exact integrated candidate-adjudication path on both its full reference
document and at least one realistic long-form near-miss candidate that preserves the
headline conclusion but contains a material active contradiction. This is an
evaluator-authority negative control, not product feedback, and must be frozen before
the first product call. It cannot alter Task69's immutable `0/1` result.
