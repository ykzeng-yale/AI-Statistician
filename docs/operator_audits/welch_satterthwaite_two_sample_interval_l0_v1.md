# Operator audit: Welch-Satterthwaite two-sample interval L0 v1

## Immutable draw boundary

Task `welch_satterthwaite_two_sample_interval_known_result` consumed exactly one
fresh product draw and exactly one post-runtime hidden evaluation from sealed code
head `c62e01b7e0a38c3ae874687c387401c6bd4e8560`. All seven enabled roles used exact
`claude-haiku-4-5-20251001`; no Sonnet or Opus call occurred.

The immutable run is:

`runs/main_worker_research_l0_welch_satterthwaite_20260827_v1_codex_workspace_exact_haiku`

Product status was `BLOCKED`, research completion was `0/1`, and hidden gold was
`0/1`. Formalization was correctly not applicable and Formalizer did not execute.
This task must never be rerun, resumed, repaired, hidden-evaluated again, rescored,
or resampled.

## What executed

The one outer graph consumed twelve steps:

1. Architect selected TheoryDeveloper.
2. TheoryDeveloper used one persistent Markdown/LaTeX workspace with direct reads,
   writes, scratch execution, raw observations, and an explicit checkpoint.
3. An isolated theory preflight reviewer accepted the two theory documents.
4. Architect selected AlgorithmEngineer.
5. AlgorithmEngineer authored and executed one exact Python estimator.
6. An isolated generated-source reviewer accepted that estimator.
7. SimulationEngineer authored and executed an exploratory simulation bound to the
   accepted estimator; its independent review accepted.
8. The same Simulation owner progressed to confirmatory source authoring.
9. Independent review correctly requested revision of the first confirmatory source
   for runtime-argument validation and a hardcoded acceptance result.
10. The same source owner observed syntax feedback, revised, and executed a final
    source whose twelve DGP checks all passed at 128 replicates.
11. The second independent review returned `REVISE` by describing lines from the
    superseded source even though its work order named the final executed source.
12. The exhausted source lineage reached Architect, which blocked.

This run demonstrates real model-owned Theory, Algorithm, and Simulation workspaces,
direct environment feedback, exact estimator binding, and optional-formalization
conformance. It does not establish full-task capability.

## Operator findings

### 1. Active theory contains mathematical errors

The theory's general formula for the variance of the unbiased sample variance is
dimensionally invalid. It writes a factor of `sigma_x^4/(n_x-1)` multiplying a
difference whose terms already have fourth-moment units. The general identity is

`Var(S^2) = (1/n) * (mu_4 - ((n-3)/(n-1)) * sigma^4)`.

Under normality this reduces to `2*sigma^4/(n-1)`. The candidate immediately states
that normal result, but it does not follow from its displayed general formula.

The same theory also claims that adding a common constant to both samples shifts the
confidence-interval endpoints by that constant. For an interval for
`mean_x - mean_y`, the common shift cancels; the mean difference and both endpoints
are unchanged. The preflight report reproduces the contradiction: it says the mean
difference is unchanged and then says the endpoints shift, yet concludes that all
equivariances are correct and accepts the theory.

The reported 90%, 95%, and 99% critical values `1.638`, `2.132`, and `3.055` for the
displayed equal-size five-observation example are also inconsistent with its eight
degrees of freedom. The corresponding two-sided values are approximately `1.860`,
`2.306`, and `3.355`.

Finally, the section labeling fiducial, Bayesian, and numerical-integration methods
as generic "exact solutions" to Behrens-Fisher is too broad without specifying the
inferential authority and coverage criterion. This is secondary to the explicit
formula and equivariance errors.

The frozen mechanical theory harness passed `7/7` and the calibrated exact-Haiku
semantic judge marked all `8/8` claims satisfied. Operator inspection overrides that
automated pass. The task receives no trusted theory or full-task credit.

### 2. Estimator formulas pass, but the public closed request contract fails

The hidden algorithm harness passed `15/17` checks. The estimator's numerical
formulas, sample-variance behavior, degrees of freedom, critical value, interval,
joint zero-variance boundary, and declared equivariances passed. The substantive
failure is closed request validation; the aggregate all-checks row fails as its
consequence.

The source converts sample entries with `float(...)`, which accepts Boolean and
numeric-string values that the public JSON contract explicitly rejects. Its
`confidence_level` check uses `isinstance(value, (int, float))`, so Python Boolean
values are also accepted. It reads the three expected fields but does not reject an
extra request field. These are source-owned ABI defects, not reasons for runtime to
add Python-type patches or task-specific repair rules.

### 3. Final confirmatory source was falsely rejected from stale context

The second review work order correctly binds
`simulation_manifest:4835e60f5bdc8ef93a84`, stable hash
`db08a742b3f3820ebbc11f609060373374ddd03b72f95fcd240a6a1e5664f043`, and the
final executed source with stable script hash
`66060f8ca313239c930eab2729d9918655c3f3d54a0249c12c057aa45f4a2821`.
That source implements per-DGP mean-bias, variance-bias, and coverage checks at
lines 204-244, aggregates them, and returns the resulting variable at line 248.
The exact execution output records `acceptance_passed=true` with all twelve DGPs
passing.

Nevertheless, review `generated_code_semantic_review:82a8774da66a1202cec6eec9`
claims that lines 158-159 return `acceptance_passed=True` unconditionally. Those
lines belong to the prior source. The current lineage and work-order identities are
correct; the isolated reviewer anchored on historical finding text without a fresh
current-source observation. Runtime then exhausted the source revision lineage and
Architect blocked.

This is a generic review-session lifecycle defect. It is not evidence that the final
confirmatory source was wrong, and it must not be fixed by manually accepting this
consumed run.

### 4. Hidden empirical behavior passes but runtime did not accept it

The evaluator-only empirical component passed `11/11` checks over 16,000 estimator
invocations. The final runtime confirmatory diagnostic also executed successfully,
but its false semantic rejection prevented accepted confirmatory evidence and the
terminal Critic never ran. Therefore runtime research completion, unresolved-gap
disclosure, and full-task acceptance all correctly remain absent.

Hidden post-runtime outcomes cannot be fed back into AgentRuntime or promoted into
runtime evidence. They remain component diagnostics only.

## Evidence hashes

- Runtime manifest bytes: `b4cd1df56bec18c84840806915ddd651fff5fcecf72b802c47301183203d01b9`
- Runtime result bytes: `cf4dbaf5dec00b6826cfefc83ad298925d21916ef9f3406e4af4a10bba334f58`
- Hidden evaluation bytes: `f9a082fb11739c2227acd5496770806a1032583f2747c13037d6db8d506491e9`
- Accepted theory packet: `803ce13e971e3579a2e4ce1bfa824e14fc512736e6640e4cef8cc37d1f20f2c2`
- Accepted theory document set: `503bc2be863e39cabbf9098cf52eee58181f5306c2b52c27abc38d944f87549a`
- Theory document bytes: `eafbf84cc90eb5c4162ceb26434594ba04378bff8a9325e0a44081dc6e0c03e3`
- Estimator document bytes: `1b546ced962be7614b6b44938ebb4c20e72faf7539117997f9e8a753601c1fde`
- Theory review bytes: `cbb2271496312a9c028081a275d8947b17c55655f4ef8f3b74972abb4696b733`
- Evaluated estimator source identity: `565c482b7c8cbe59e45b952b6d3c697018531dd225af74bc98e82a55b4f54049`
- Evaluated estimator file bytes: `bbea13119517d71e6b0a40e954434f62ac83127235022d3e709aeedd2e1033b0`
- Final confirmatory source bytes: `482844d5a2116782268f2a9d57a694d8806baed46601777868b52b5ed3982919`
- Final confirmatory metrics bytes: `a2bd9fc74f23adb13e91f00932341247051d3eb1b43c7f587fe227db0f87ca75`
- False review document bytes: `7da94e82281d296aa85946d1f44a790724caf082b909d7ba5c44f11e88029b82`
- Hidden theory mechanical result: `2448162397b7703a7f48b7085f566f96c6179c7bac3eeaf4f72af86fd45a11b6`
- Hidden theory semantic result: `2d545a7091ce9c64d558da3261bb4b7c00698a3adb32f437aa6af3311229ad4f`
- Hidden algorithm result: `39ab3f53d8b9fd68fb06d2e65f65843974ff5a071f6af78851ec1545edb9ba5f`
- Hidden empirical result: `04e9cd810f52da2e2537effe34d5e18c249ecb7711ab89c7dbbbc61073ea360d`

## Disposition and future-only correction boundary

Operator disposition:

`OPERATOR_INVALIDATED_THEORY_CODE_CONTRACT_FAILED_RUNTIME_FALSE_REJECTED_REVISED_CONFIRMATORY_SOURCE`

Trusted full-task capability remains `4/68`.

Commit `f2e39edbea3c6f0122a14827d8d996c1854966bd` applies one future-only,
Codex-shaped harness correction. When active prior findings exist, the same isolated
reviewer session must call `read_current_generated_source` for each current artifact
before submitting. Runtime returns complete immutable source bytes with line numbers,
artifact identity, and exact hash as a fresh tool observation. Historical findings
remain context, but the current observation is authoritative. First reviews add no
tool call.

The change adds no source parser, statistical formula, Python input-type rule, Welch
rule, repair agent, retry scheduler, second reviewer, provider, model escalation, or
Codex runtime embedding. Runtime still validates identity and evidence boundaries;
the model still owns scientific interpretation and source revision. Focused tests
passed `146/146`, and the complete repository passed `988/988` in 79.56 seconds with
production Python at 149,998 lines.

This future mechanism commit cannot alter Task 68's immutable `0/1` result.
