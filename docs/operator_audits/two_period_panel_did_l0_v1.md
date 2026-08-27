# Operator audit: two-period panel DID L0 v1

## Immutable draw boundary

Task `two_period_panel_did_known_result` consumed exactly one fresh product draw
and exactly one post-runtime hidden evaluation from the sealed code and authority
binding at `d388a0ce6d9e27ce7fbf2075d4b3657b9cabce1c`. The product run used exact
`claude-haiku-4-5-20251001` for all seven enabled roles. No Sonnet or Opus call
occurred.

The immutable run is:

`runs/main_worker_research_l0_two_period_panel_did_20260827_v1_codex_workspace_exact_haiku`

Its product status was `BLOCKED`, its research completion result was `0/1`, and
its hidden-gold result was `0/1`. Formalization was correctly not applicable and
the Formalizer did not execute. This task must never be rerun, resumed, repaired,
hidden-evaluated again, rescored, or resampled.

## What executed

The single outer graph used eight steps:

1. Architect selected TheoryDeveloper.
2. TheoryDeveloper used a persistent Markdown/LaTeX workspace, Python scratch,
   raw tool feedback, and an explicit checkpoint.
3. An isolated theory preflight reviewer accepted the two theory documents.
4. AlgorithmEngineer wrote, executed, and committed one exact Python estimator.
5. An isolated generated-source reviewer accepted the estimator.
6. SimulationEngineer wrote, iterated, executed, and committed one exploratory
   Python source bound to the accepted estimator.
7. An isolated generated-source reviewer accepted the simulation source.
8. Critic correctly blocked final acceptance because confirmatory empirical
   evidence had not been produced.

This is useful harness evidence: source-owning models operated persistent
workspaces and received raw execution observations, ordinary transitions did not
require Architect routing, and the runtime preserved task intent and evidence
authority. It is not full-task capability evidence.

## Operator findings

### 1. Active theory is not semantically valid

The main theory document defines no anticipation as

`E[Y_i0(0) | G_i=1] = E[Y_i0(0) | G_i=0]`

and the independent preflight reviewer explicitly says that no anticipation
ensures equal pre-period means across groups. That is false. No anticipation says
future treatment does not alter the pre-treatment potential outcome; it does not
require treated and control populations to have equal baseline levels. The
elementary two-period DID identification permits different group baseline means
and restricts untreated mean changes through parallel trends.

The final DID identity can be derived without equating the two baseline means.
The candidate's stronger restriction does not make the displayed identity false,
but its assumption interpretation and claimed role in the proof are wrong and
contradict the frozen reference. The candidate also does not clearly state that
equal baseline levels do not establish parallel trends.

The exact-Haiku hidden semantic judge nevertheless marked all eight claims
satisfied, and the preflight reviewer called the false statement standard. The
operator therefore overrides the automated theory pass. This task receives no
trusted theory or full-task credit. Passing a finite calibration set did not make
the judge authoritative for an unseen semantic confounder.

### 2. Estimator is numerically right but violates the public closed contract

The hidden algorithm harness passed 17 of 19 checks. The only substantive failed
check was `invalid_requests_rejected`; `all_contract_checks_passed` failed as its
aggregate consequence. The implementation used Python's
`isinstance(value, (int, float))` without excluding `bool`, so Boolean outcomes
were accepted even though the public contract explicitly rejects them.

All numerical formulas, counts, sample variances, standard error, zero-variance
boundary, and declared equivariances passed. The hidden empirical harness also
passed every frozen check over 16,000 accepted-estimator invocations. Those are
component observations only; they do not repair the closed-contract violation or
complete the product research loop.

### 3. Reviewer tool ergonomics allowed a false ACCEPT

The independent algorithm reviewer attempted three diagnostic probes. None
invoked the target estimator:

- the first probe omitted the required `run_sandbox` wrapper;
- the next two defined a wrapper that did not accept the runtime's `estimators`
  argument.

Raw failures were correctly returned to the same reviewer session, but the
reviewer then accepted by inspection and asserted that all input validation was
enforced. This is not evidence that the target passed the public contract. The
generic review tool currently makes the model author a wrapper ABI merely to call
one accepted function, obscuring the scientific review objective.

### 4. Required empirical work was scheduled only as exploratory work

The frozen task required a separately frozen confirmatory assessment across
multiple effects, group sizes, variances, heterogeneous effects, and sample-size
regimes. The Simulation workspace was instantiated with
`empirical_evaluation_phase=exploratory_diagnostic`. It eventually executed one
bound-estimator smoke invocation and several deterministic boundary checks, then
committed and advanced to review. The reviewer accepted that exploratory source,
but no exact confirmatory evaluator source was authored or replayed.

The runtime then routed directly to Critic. Critic correctly reported the
empirical dimension as inconclusive. Hidden empirical success cannot be promoted
back into runtime evidence because the authority was evaluator-only and executed
after termination.

### 5. Research completion still contains a contract inconsistency

The frozen evidence contract records typed metric contracts as not required and
the metric-protocol phase as not required. The research summary nevertheless
lists `metric_protocol_independently_accepted` among the required checks. This did
not change the correct final failure because confirmatory empirical evidence was
also absent, but the completion contract should derive requirements from task
intent and the selected executable-evaluator path rather than retain an obsolete
typed-metric requirement.

## Evidence hashes

- Runtime manifest: `a990b80871166265c7af04d514530fa2f9d871a2b5e867eba949230b8ec5203c`
- Runtime result: `ad3925dbb8964a4eb2e92ba6a037634687cecdbbdd78aa14e1e843ade930eaee`
- Hidden evaluation: `b820f353e865594feb3430505ca302c4f16ba4e421e2c6802ba44541ab8411e2`
- Accepted theory packet: `3ccd83bdc0da2f709323204811b979daea00eb380ca890ef0d74f7be1407a037`
- Accepted theory document set: `e7acb5d7068b8b3879e4cff673f91158bed6f58442117b064d14503d78058769`
- Theory document bytes: `d9834c1d04b6db3d431e822bf1c2cef73e255c88dbbafc014d308704b0ac4b3e`
- Estimator document bytes: `62e4c8845512360dede930f6212388c6eda2c1e42347ecd2feaad182b9d69d10`
- Theory review bytes: `460150493c45b30337445d5d956c38e214e7577855e134eb9504c834efd89850`
- Evaluated estimator source identity: `5b3126b21bee3b2ddadb49cf20d1aebd32766c15346253f670cf557ca6cb3f47`
- Evaluated estimator file bytes: `66816135baa18d32ffeca73c91a55db9620fef1588c8f349478751e76990160d`
- Exploratory simulation file bytes: `7270f46605119b58c04943e3e28b3665681c7382225ffeacee886f3cb2a099ac`
- Hidden theory mechanical result: `2448162397b7703a7f48b7085f566f96c6179c7bac3eeaf4f72af86fd45a11b6`
- Hidden theory semantic result: `5a383fb49507b0ecd0322198889aaebdad9ca9fa94c29f189e028a4edaf1922c`
- Hidden algorithm result: `bed224e71b9ef5826f890d104c15bc0c76ae78ec0e1e050b654b0eb6b980f1e7`
- Hidden empirical result: `9f18850328cb9ce22a212ed114c1be084336205c38ac8631c844ba5bc2f64484`

## Disposition and future-only correction boundary

Operator disposition:

`OPERATOR_INVALIDATED_THEORY_CODE_CONTRACT_FAILED_CONFIRMATORY_EMPIRICAL_NOT_RUN`

Trusted full-task credit remains `4/67`.

Future shared work should improve the harness, not this DID answer:

- give reviewers a simple generic exact-call probe in addition to arbitrary test
  source, so wrapper mechanics do not hide target behavior;
- prevent `ACCEPT` from treating failed reviewer scaffolds as target evidence and
  make the reviewer explicitly account for unexecuted public contract clauses;
- let an empirical-required task progress from exploratory diagnostics to one
  exact source-owned confirmatory evaluator checkpoint before Critic;
- align research completion with the selected executable-evaluator contract;
- strengthen future hidden semantic calibration with claim-specific contradiction
  and assumption-conflation cases, while retaining operator review as the final
  capability-credit authority.

No future mechanism change may alter this consumed result or introduce a DID
formula, no-anticipation rule, Boolean patch, hidden threshold, content repair,
retry, extra scheduler, or model escalation.
