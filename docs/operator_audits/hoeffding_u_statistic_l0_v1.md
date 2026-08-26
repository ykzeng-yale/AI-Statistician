# Hoeffding U-statistic L0 v1 operator audit

Date: 2026-08-25

## Frozen identity

- Task: `hoeffding_degree_two_u_statistic_known_result`
- Family: `u_statistic_projection_asymptotics`
- Visible question SHA-256: `06727dd37d8c4fd3d3f3384f87246a9f4dc5c9e29b80af1f22d58e34a816bc5c`
- Visible question hash: `fed313901dc5e5674f17bea5238801ea0e46af4bb659435a508bb6ab0c75f063`
- Gold bundle: `research-l0-hoeffding-u-statistic-20260825-v1`
- Gold manifest SHA-256: `0b03e9695a7c4d4fe5c59df963aaf94248ff38c643d29cf8a886dde3edbcfe4c`
- Activation commits: `e35c3d65fee7cf1d869dd5f5bde2de706a1584ff`, then binding commit `bf0fb93eade11d5d195fe9aaafdc015f388c677a`
- Runtime head: `bf0fb93eade11d5d195fe9aaafdc015f388c677a`
- Runtime model: `claude-haiku-4-5-20251001`
- Run: `runs/main_worker_research_l0_hoeffding_u_statistic_20260825_v1_codex_harness_exact_haiku`

Evaluator authority was frozen, calibrated, and pushed before the first product
model call. The task received exactly one product draw and exactly one hidden
evaluation after AgentRuntime terminated. It must not be rerun, resumed,
repaired, hidden-evaluated again, rescored, or resampled.

## Immutable result

The canonical runtime returned `ACCEPTED`. Visible research evaluation and the
pre-frozen hidden theory authority each returned `1/1`; hidden mechanics passed
`7/7`, and the calibrated semantic judge marked `8/8` claims satisfied.
Formalization, generated code, simulation, and source replication were not
applicable and did not execute.

The two source-owner sessions used 22 exact-Haiku model/tool turns. The first
isolated referee used 13 turns, found one high-severity boundary-limit error, and
returned `REVISE`. The same TheoryDeveloper then revised the existing Markdown
workspace. A fresh isolated referee used 10 turns and returned `ACCEPT`; the
terminal Critic also returned `ACCEPTED`. The run used 47 product calls: one
Architect plan, 22 Theory turns, 23 referee turns, and one terminal Critic call.

Authoritative artifact hashes:

- Runtime manifest: `bc06c9a119c612f58932716e72190d12fc36174db437e7642c5879c01e0da725`
- Runtime result: `c334fb7cbcab24bf9426a8f468163735fb01b0c71081875ef03660d503526ed1`
- Gold report: `df57e04aa39730ee5177ef9772ef3777b00a2c68c7decc1d3934da5ce6768892`
- Evidence ledger: `c31f8bc1553a129cb8af40cda84f3ab816f868c56fc735cfe686c8468e6670a1`
- Final theory document: `338790b9ecc3b0bc63406e2097ef62dbe743e0310364d0fb555c6aa761c535fb`
- First referee report: `dffb0ce0c2b5b1998a848f3f2abc3bb5484108af54361be7194f20d54d5e3a63`
- Accepted referee report: `d921c150656df869cf03f442a7fea554d82757a3ad8ebfaafa07facd6f6adf4d`

## What worked

The final active document correctly defines the two Hoeffding projections,
derives mean zero and conditional degeneracy, obtains the exact factor `2/n`,
and derives the exact variance
`4 zeta_1/n + 2 zeta_2/[n(n-1)]`. It distinguishes independent disjoint pairs
from uncorrelated overlapping pairs and correctly states the nondegenerate CLT
and the degenerate root-n boundary conclusion.

The first referee caught a real arithmetic error: the initial document claimed
`2 zeta_2/(n-1)` converged to `2 zeta_2`. Its exact report returned to the same
source owner, which changed the document and committed a new content-addressed
checkpoint. No RepairAgent, runtime-authored mathematical patch, task formula,
or second scheduler was involved.

## Operator caveats

The frozen automated pass is not a clean mathematical-quality pass.

1. Lines 150 and 159-165 of the final document multiply the degenerate
   U-statistic remainder by `1/sqrt(n)` after multiplying the full decomposition
   by `sqrt(n)`. The actual term is `sqrt(n)` times that remainder. The stated
   CLT is true, but this displayed proof establishes negligibility for the wrong
   scaled quantity. The correct variance is `2 zeta_2/(n-1) -> 0`.
2. In the overlapping-pair covariance calculation, line 111 pulls
   `h_2(X_j,X_l)` outside a conditional expectation given only `X_j`, although
   it also depends on `X_l`. The zero covariance follows after conditioning on
   `(X_j,X_l)` or factoring both conditional expectations using conditional
   independence, not by the displayed equality.
3. Lines 194-197 speculate that suitable Lindeberg conditions should give a
   Gaussian `n`-scale limit. For a fixed canonical square-integrable kernel, the
   generic limit is a weighted centered chi-square series, not a normal law.
   The candidate labels the result unresolved, but the visible task explicitly
   prohibited an unsupported `n`-scale law.
4. The accepted referee repeats the wrong CLT scaling and treats the speculative
   Gaussian boundary claim as nonblocking. The terminal Critic receives the
   exact document and accepted report but says there are no false equations or
   unsupported claims. The hidden Haiku semantic judge also misses both issues.
5. The final structured handoff contradicts the authoritative Markdown. Its
   inherited `derivation_summary` and `self_critique` still say the root-n
   boundary variance tends to `2 zeta_2`, even though the revised document says
   it tends to zero. This is a duplicate-authority harness defect, not a
   statistical task-specific defect.

The immutable protocol score remains `1/1`, but the capability record is
therefore **pass with operator mathematical, evaluator, and duplicate-handoff
caveats**. It is evidence that direct review-driven source iteration works; it
is not evidence that Haiku referee agreement guarantees correct mathematics.

## Harness conclusion

The OpenAI Codex mechanism comparison points to one clear correction: keep the
substantive source in one model-owned workspace and make structured transport a
small reference/index envelope. Future document-backed TheoryDeveloper packets
should not duplicate derivation prose, self-critique, or rejected mathematical
alternatives in JSON. Claim IDs, document paths and hashes, dependencies,
statuses, and optional formalization ABI are sufficient.

This future-task correction cannot alter this candidate, either referee report,
the terminal Critic, the hidden judgment, or the frozen score.
