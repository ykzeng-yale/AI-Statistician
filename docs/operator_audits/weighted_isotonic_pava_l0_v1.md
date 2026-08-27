# Weighted isotonic PAVA L0 v1 operator audit

Date: 2026-08-27

## Immutable identity

- Task: `weighted_isotonic_regression_pava_known_result`
- Family: `shape_constrained_regression`
- Visible-question commit: `ffac666ed4caf4ff73cf5a37d9809f224fba72a3`
- Authority-binding commit: `05e5b2a7d4447791419408ebaa85258d453e3bb2`
- Activation-seal and run head: `2720809ddfc1ff333b9f7c4faf1246c2c428e880`
- Run:
  `runs/main_worker_research_l0_weighted_isotonic_pava_20260827_v1_codex_workspace_exact_haiku`
- Runtime model: exact `claude-haiku-4-5-20251001` for all seven enabled
  roles; no Sonnet, Opus, or automatic escalation
- Runtime result: `BLOCKED` after three outer traces
- Frozen full-task result: `0/1`
- Trustworthy capability result: `0/1`
- Operator disposition: `OPERATOR_INVALIDATED_UNACCEPTED_THEORY`
- Future-task shared mechanism commit:
  `f56db3a789de9ed25e86ed492a52ae7f6e6062a6`

The task received exactly one product draw and one post-runtime evaluator-gate
invocation. It is closed and immutable. It must not be resumed, rerun, repaired,
hidden-evaluated, rescored, or resampled.

Immutable SHA-256 values:

- Visible question: `4bf298aa59447fbc66894a286af9cd14892d17c220c80c3c3308596a9346c109`
- Runtime manifest: `612d252affe306320827edaf85056979182d1a84c72ce56a3a567e0d346973e3`
- Runtime result: `64eb8a109b83b8e4496f3c7d0e4cb0a071bd3c27d673d0dab360c133b14f7b47`
- Runtime completion summary: `70fe9a3c7b9d9bdf6eb9699efd855509c399826da809ce43ec769271bb8e32b4`
- Runtime failure summary: `bc15832b6887ead9d2390fff313df8bac6df62ca35e0885de392007ee496f081`
- Runtime model topology: `4690423d3707a6bab502e7f25c18afcce2bd7f4cac78cf5d668bb6bee6fc16e0`
- Runtime progress: `f2f3e76ebe3ddd52383788ca1f083f29423bb70b49b89cc1782afc08550f93d7d`
- Runtime traces: `fb1772a0e4c169ea3f42017a9cd89e84653e45667a27490f531bd5cad59b27eb`
- Runtime observations: `b23e76ebe3ddd52383788ca1f083f29423bb70b49b89cc1782afc08550f93d7d`
- Runtime handoffs: `6a9a5ac58dd0c01cf0f53019137885641b6ebde2af5f5ee59259ee4cb59eba51`
- Post-runtime gold gate: `205cefe64f3d1ead3b01e00162c99b6bcc063e8940daf8eefd371010fbd0989d`
- Theory document: `e1562575892b02cd56ca70ce258443d69a6b0308d753581749fd382067418a9e`
- Theory document set: `a6d24ba84bd64b53d46dd094997724b4c857a4ba670ae89f7d1671a8e2538b90`
- Theory client-tool session: `60cee303feb6b66a8a62c0833b5ba3b6dd349e49da657cd2e5c28edcb78b43ad`

## Runtime result

One Architect call selected public source retrieval followed by Theory. The
deterministic retrieval subsystem handed the task to one persistent Theory owner.
That exact-Haiku session used 34 model turns and 38 model-selected tools:

- 9 public source searches and 7 source reads;
- 3 Theory-document reads and 1 complete Markdown write;
- 14 structured handoff writes;
- 2 successful Python scratch executions;
- 1 rejected checkpoint commit and 1 terminal honest-gap report.

The model made 15 structured submissions and authored one 308-line Markdown/LaTeX
document. The final ordinary turn attempted `commit_theory_checkpoint`; the exact
structural rejection returned to the same session. The one terminal recovery turn
then selected `report_theory_gap`. Runtime preserved that model-owned disposition
and did not route, patch, or invent a repair.

No independently accepted Theory handoff existed. AlgorithmEngineer, generated
Python/R execution, SimulationEngineer, the terminal Critic, and all scientific
promotion gates therefore did not run. Formalization was not applicable and the
Formalizer did not run.

The post-runtime gold gate observed the failed runtime once and recorded
`n_tasks_evaluated=0`. It did not invoke the hidden mechanical Theory harness,
semantic judge, algorithm harness, or empirical harness. It produced no runtime
feedback.

## Structural failure

The pre-run document-authoritative contract still sent contradictory guidance:

1. its estimator row inherited rich outer mathematical fields such as `formula`,
   `algorithm_sketch`, `outputs`, and `required_assumptions`, and the validator
   required some of them;
2. its executable interface permitted only compact request
   `{name, meaning, binding}` and response
   `{name, meaning, normalization, derivation_ref}` rows;
3. the visible frozen ABI carried richer public metadata such as `json_type`,
   `shape`, `edge_cases`, and `clause_id`;
4. the rejection said only that the estimator must contain executable ABI fields,
   without naming the unsupported nested paths.

The model consequently oscillated between removing outer fields that another
validator still required and restoring them while leaving copied rich metadata
inside the interface contract. Its terminal gap blamed the outer estimator row,
but the persistent error was the nested interface metadata. This is a shared
handoff and observation-quality defect, not a PAVA-specific coding defect.

## Mathematical audit

Removing the structural failure would not make this candidate correct. The active
document has multiple load-bearing errors.

1. Line 56 uses `+ lambda_i (theta_(i+1)-theta_i)` with `lambda_i >= 0` for a
   minimization constraint `theta_i <= theta_(i+1)`. That is the wrong multiplier
   sign. Lines 64-92 then derive cumulative residuals
   `sum_(i<=k) w_i(y_i-hat theta_i) <= 0`, while the public contract requires the
   correct nonnegative sign.
2. Lines 128-134 say multipliers vanish inside a constant block. Active equality
   constraints may have positive multipliers. Multipliers vanish at strict fitted
   jumps. Lines 191-207 explicitly reverse this complementary-slackness behavior
   again and then claim it verifies KKT.
3. The block-mean proof relies on that false interior-multiplier statement. A valid
   telescoping proof instead uses zero multipliers at the strict boundaries of a
   maximal constant block.
4. Lines 212-229 assert the wrong cumulative-residual invariant and do not prove it
   from the pooling operation. The claimed global-optimality proof therefore does
   not establish dual feasibility or KKT for the stated problem.
5. The required max-min characterization, or an equivalent independently
   checkable characterization, is absent.
6. Lines 44-47 prove only that the projection minimizes residual loss,
   `||y-hat theta||_w^2 <= ||y-theta*||_w^2`. The requested empirical/theory claim
   is the different projection-risk contraction
   `||hat theta-theta*||_w^2 <= ||y-theta*||_w^2`, which needs the projection
   variational inequality or Pythagorean inequality.
7. Line 268 calls PAVA worst-case `O(n^2)` and says weighted complexity is not
   characterized. The standard stack implementation is linear time. This is
   secondary to the failed optimality proof but still contradicts a mature PAVA
   account.

The document marks these sections `SUPPORTED` and describes the derivation as
complete. It receives no Theory component credit merely for being long,
source-grounded, or structurally inspectable.

## Shared correction

Commit `f56db3a7` changes future tasks only:

1. document-authoritative Theory handoffs keep estimator JSON to `id`, `name`, and
   the executable interface contract; substantive formulae, algorithms,
   assumptions, rates, and proofs stay in Markdown/LaTeX;
2. the legacy structured-JSON path retains its old fields for compatibility;
3. unsupported executable-interface metadata is reported with exact nested paths
   and the allowed ABI shape;
4. the same source-owning model still chooses every revision or honest stop.

This adds no statistical formula, PAVA rule, content parser, output patch, repair
agent, retry, Architect route, scheduler, model call, or model-tier escalation. The
Theory, ABI, document-consumer, AgentRuntime, gold-evaluation, and scientific-
progress mechanism panel passed `275/275` before accounting updates. The final
focused panel passed `331/331`; the complete repository passed `955/955` in 83.05
seconds. Compile-all, JSON, diff, model-policy, and secret hygiene passed.

## Capability accounting

This is the fifty-eighth consumed scored task. It is `0/1`; four of 58 tasks retain
trustworthy full-task capability credit. The run demonstrates a real persistent
Markdown Theory workspace, public source tools, scratch execution, direct
same-session validation feedback, and an honest terminal gap. It does not
demonstrate correct statistical derivation, accepted Theory, scientific code,
simulation, independent review, hidden-gold success, or formal proof.
