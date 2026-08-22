# Pearson Multinomial GOF L0 v1 Operator Audit

## Disposition

The single frozen exact-Haiku product draw is **failed, consumed, and closed**.
AgentRuntime reached a source-grounded Markdown/LaTeX theory checkpoint, independent
theory acceptance, generated estimator execution and source review, independent metric
protocol acceptance, and a generated confirmatory simulation that passed all eight
runtime metric gates. The post-simulation source review then failed before its model
call because runtime incorrectly treated a deliberately withheld upstream smoke result
as an included empty result. The research loop and hidden full-task result remain
`0/1`. The task must not be rerun, resumed, repaired, or rescored.

Run directory:
`runs/main_worker_research_l0_pearson_multinomial_gof_20260821_v1_codex_harness_exact_haiku`

Immutable evidence hashes:

- Runtime manifest SHA-256: `9f1059372d85a188b52c1bee44f7ea347ac923fa3708bc6c8ec97f0e2ae9f33e`
- Hidden-gold report SHA-256: `fec2988703dbcce5d2abccae91b155a27259e9ce43255a2ac1e53428716aefc3`
- Runtime result SHA-256: `d507cdc629afcd59bb1bc961cb315ecf6bdd2bf8dac8c43b4d7a8fcc570c589d`
- Runtime failure summary SHA-256: `be42de2a18b0329dd931afd65ef9e203008565e98be529ee2774c9bbb5c49ec9`
- Runtime completion summary SHA-256: `4003f9a7200d91370d1bfada2e11866aa2790cd490ad610629ecde0b72ff58b3`
- Runtime traces SHA-256: `c30932c7e7635e8668f60c09376826ba1faa363e40868e554d1d86ef7ee7822a`
- Runtime handoffs SHA-256: `967b2c8080cd48756e9bc291c868f42570063e9d6a247e940b83b7cb2a0afef6`
- Theory document SHA-256: `7e4c88040ff1cd931c9fc5fb0c1ba0f966ad0e5c607c3c932cfb52bde2b9434b`
- Estimator source SHA-256: `1050f68574123c222561d85930480477da14f3d5e75cf624d2bf9b6bd89ca47c`
- Simulation source SHA-256: `1d0afc33d9c50c3830ef7c5d6c2b6eb4094127761dcbc9d2ac815734a5a87921`

Every enabled LLM role used `claude-haiku-4-5-20251001`; no enabled role used
Sonnet or Opus. Formalization was `not_applicable`, no Formalizer ran, and Lean was
not a blocker.

## Live Trajectory

TheoryDeveloper read both frozen public sources, authored one persistent mathematical
document, used an isolated scratchpad, recovered from one exact document-edit error,
and explicitly committed its checkpoint. The independent referee read the complete
document, ran its own scratch computation, wrote a Markdown report, and accepted all
indexed claims.

AlgorithmEngineer generated and executed one estimator on its first source submission.
The independent source reviewer accepted the exact executed bytes. The fresh metric
author and isolated reviewer then accepted one pre-outcome protocol. SimulationEngineer
generated source that executed 5,000 replicates for each of three DGPs, invoked the
accepted estimator 75,006 times, and passed all eight typed runtime gates. The observed
aggregate rejection rate was `0.0514667`; the maximum statistic mean and variance
deviations were `0.0544160` and `0.2736703`.

The ninth outer trace never called the post-simulation reviewer model. It blocked on
`upstream generated dependency result hash mismatch: est_multinomial_pearson_gof`.
The runtime therefore correctly withheld research completion and Critic acceptance.

## Model Defects

The accepted theory was not mathematically reliable. It first defines standardized
coordinates using `sqrt(n p_j)` but later reuses the same symbol for division only by
`sqrt(n)`. It states the unweighted sum constraint for the standardized vector, whereas
the relevant constraint is weighted by `sqrt(p_j)`. It also moves between the
unweighted projection orthogonal to the all-ones vector and the standardized projection
orthogonal to `sqrt(p)` without a valid transformation. The runtime referee partially
reconstructed the correct weighted argument in its own report, then silently classified
the candidate discrepancy as a minor presentation issue and accepted it. The calibrated
hidden semantic judge returned `INCONCLUSIVE`, so theory was not gold-validated.

The estimator computed valid requests correctly and the hidden empirical harness passed
all eight checks across 15,000 invocations. Its own submitted smoke output nevertheless
contained `passed=false`: the proposed exact-fit case used probabilities summing to
`1.2`. The source also coerced boolean and noninteger counts to integers and ignored an
extra request field instead of enforcing the frozen invalid-input contract. The hidden
algorithm harness therefore executed but did not pass all acceptance checks.

These are model and review failures, not outputs to patch. They remain immutable negative
evidence for future tasks.

## Shared Harness Defects

The accepted algorithm handoff intentionally excluded the exact smoke outcome while
retaining its hash. The dependency projection marked `exact_result_included=false`, but
the post-simulation validator read the absent payload as `{}` and compared the stored
nonempty hash against `stable_hash({})`. Any nonempty withheld outcome therefore failed
before semantic review even when source and lineage were unchanged.

The scientific workspace also treated a process-level accepted source submission as a
terminal action. The same coding model never received a subsequent turn to inspect the
successful execution envelope, notice its own failed diagnostic, and choose whether to
revise or finish. Parsing arbitrary nested `passed` fields in runtime would be a new
hardcoded scientific rule; terminating before model inspection was the actual harness
mistake.

## Shared Correction

Future-task code commit `f4fe83ed` makes three general corrections:

- hash-only upstream outcomes are validated as nonempty references and remain withheld;
  included outcomes still require exact content-hash agreement;
- `submit_scientific_source` executes and returns the raw observation but is nonterminal;
  the same model must later call `commit_scientific_source` on the unchanged accepted
  hash, and a same-turn submit-plus-commit is rejected;
- the independent theory referee is explicitly told that changing a candidate's defined
  variable, normalization, constraint subspace, covariance operator, or quadratic form
  is a substantive finding, not a silent correction compatible with acceptance.

The runtime does not inspect task formulas or arbitrary diagnostic keys. A regression
shows the same model revising after a technically successful execution whose own output
contains `passed=false`. Hash-only result, leak-rejection, source-workspace lifecycle,
and theory-referee regressions pass. The full local suite passed `819/819` in 67.19
seconds, and `research_agent_runtime.py` remains at 24,950 lines.

No agent, scheduler, Architect round trip, RepairAgent, task-family rule, statistical
formula, Lean grammar rule, model-tier escalation, frozen-run mutation, rerun, resume,
or rescore was added. The correction applies only to future tasks; Pearson remains
immutable at `0/1`, and the scored ladder remains `0/20`.
