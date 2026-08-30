# Task107 Operator Audit: Stein Identity, SURE, and James-Stein Shrinkage

## Disposition

**FAILED, consumed, immutable.** The sole exact-Haiku product draw ended
`BLOCKED` after three independently rejected Theory checkpoints and one final
source-owner no-progress failure. Runtime research evaluation and the sole hidden
assessment are both `0/1`. No theory packet was independently accepted, so the
hidden candidate harness correctly did not run. Trustworthy aggregate capability
remains `7/107`.

## Frozen Boundary

- Public authority: Charles M. Stein, *Estimation of the Mean of a Multivariate
  Normal Distribution*, Annals of Statistics 9(6), 1981, DOI
  `10.1214/aos/1176345632`.
- Visible question commit: `a0354b2aedc66a1ddf24f51cc07d957ee838aeda`.
- Preactivation ledger commit and product source head:
  `86e9e38c12db768e0f85c0c09a37ab228a08f509`.
- Product model: `claude-haiku-4-5-20251001` only; Sonnet, Opus, and automatic
  escalation were disabled.
- Run: `runs/main_worker_research_l3_stein_sure_theory_20260829_v1_codex_workspace_exact_haiku`.
- Formalization, scientific code, simulation, source replication, and novelty
  were not applicable and did not run.

Hidden reference mathematics, rubric, calibration cases, near miss, labels,
responses, and judgments remained evaluator-only. The one post-runtime assessment
made zero model calls, generated no runtime feedback, and evaluated no candidate
because runtime had no independently accepted Theory artifact.

## Harness Evidence

The retained workspace mechanism operated without a second scheduler or repair
worker:

- TheoryDeveloper authored one 302-line Markdown/LaTeX document, used sixteen
  scratch runs across author and referee workspaces, and committed three immutable
  checkpoints.
- Three independent reports were persisted and hash-bound. A fourth preflight
  invocation resumed the same referee checkpoint after its ordinary turn budget;
  it was not an Architect replan or a new candidate draw.
- The eight runtime steps consumed seven outer iterations plus one same-owner
  referee continuation.
- All 134 product calls were exact-Haiku client-tool turns: 55 TheoryDeveloper and
  79 independent-referee turns. The same 134 tool executions returned fourteen
  raw errors to their current owners.
- No direct model call, retry, fallback, runtime-authored mathematical edit,
  Formalizer, AlgorithmEngineer, SimulationEngineer, Critic, Sonnet, or Opus ran.

This is valid evidence for file-backed long-horizon authoring, isolated review,
same-owner feedback, exact persistence, and fail-closed authority. It is not
evidence that either author or referee reasoned correctly.

## Mathematical Failure

The final document contains several active defects.

1. The coordinate integration-by-parts display drops and then misplaces the
   factor `sigma^2`. The stated Stein identity is correct, but the written proof
   does not derive it.
2. The sufficient boundary condition names a standard Gaussian density instead
   of the actual shifted, scaled law. The proof must use the derivative of that
   exact density.
3. The radial-field argument studies an unweighted Lebesgue surface flux on an
   outer sphere. That is not the Gaussian-weighted boundary quantity in Stein's
   identity. With the density retained, the outer boundary vanishes by Gaussian
   decay; at the puncture the boundary is of order `epsilon^(d-2)` and vanishes
   for `d>=3`.
4. The document says `R^(d-2)` vanishes as `R` grows when `d>3`; it instead
   diverges. It then incorrectly narrows the classical risk and dominance result
   to `d>3`, contradicting the frozen `d>=3` target and its own scope section.
5. The inverse-square integrability paragraph writes a central radial density for
   a noncentral Gaussian without supplying the local boundedness and tail bounds
   needed to justify the reduction.

The exact risk coefficient, dominance interval, optimal radial coefficient,
linear-shrinkage check, and SURE interpretation are otherwise written correctly.
That partial correctness cannot close a derivation with false active steps.

## Referee Failure

The first report correctly rejected abandoned false linear-risk text. Later reports
recognized the polynomial order error but kept auditing the wrong unweighted
quantity. The final report therefore concluded that the outer boundary invalidates
the result for every `d>=3`; that conclusion is itself false because it omits the
Gaussian density. The reports also missed the earlier integration-by-parts factor
error. A rejected artifact and a mathematically correct review are separate claims.

## Future-Task Correction

Commit `a27af9794f4dbccb089a8063c3a42edb0d509084` changes only shared future
behavior. TheoryDeveloper and referee prompts now require reductions and
counterexamples to preserve the exact domains, measures or densities,
conditioning, normalization, dimensions, and limit order of the object under
review. Exact-edit failures now name missing, unexpected, required, and optional
fields, allowing the same source owner to regenerate its call from the raw error.

This selectively follows official Codex's stable-tool, raw-observation, retained
owner, and checkpoint principles. Codex's GPT-specific freeform `apply_patch`
grammar, Codex Core, App Server, thread manager, scheduler, and provider transport
were not imported. No Stein formula, boundary rule, mathematical parser, patch
parser, RepairAgent, extra model call, retry, fallback, Sonnet, or Opus was added.

## Evidence Hashes

- Theory document: `d67c664a7f9f29bd0e2ed5ec9ccb4257bca8728c5212eec5e05449388a34d5ee`.
- Referee reports: `b8b03ecd4eec74579dbf1d6993ae8e000216c1b149d8be27ac67ab1476177ce5`,
  `f6ee2ab045fcbc34d3b4763ca9d5be1ef660092fa7c341740bacf501fd2ad69d`,
  and `bc47c5ce2c7e587a306ab353c916ca632a7aef7c639285f3d72cd3b7dd9a966a`.
- Runtime manifest: `a5bef637e8c12fd27089f8310bec1e8fc42599ddc337a6fefa1203001677bbf0`.
- Runtime result: `567aa7e7eb4fb43c8a0ae336dec43e6e5a984cc4c60adc6d6d1c1a41ccd2da0f`.
- Hidden assessment: `38593e9d86cfbd30bf59306fc4607fa09443dd6c2f3e8b6398ef8398ea60b2a4`.
- Runtime topology: `7dd15bc2f8f1b136d4d5d59ca40285d6244213b7d2d4d689a2512c0e69b553cd`.

The draw, artifacts, reports, and assessment are consumed. Never rerun, resume,
repair, reevaluate, rescore, resample, manually patch, expose hidden authority, or
model-escalate Task107.
