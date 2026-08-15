# DKW ECDF Band L0 v1 Operator Audit

## Frozen identity

- Activation commit: `539e8f130306cb4f5afa3a2ecfdc5b5e2ca670be`
- Task: `dkw_ecdf_simultaneous_band_known_result`
- Run: `runs/main_worker_research_l0_dkw_band_20260815_v1_document_theory_exact_haiku`
- Runtime manifest SHA-256: `c2e2b343599214856754f8132144193b45e563af234ce24caaa8367e48bba254`
- Hidden-gold report SHA-256: `b558c31978cca209bc648f72a374ebfdefa2aa5d50f3215fe86de2b6ac6af5bb`
- Model policy: exact `claude-haiku-4-5-20251001` for every enabled role; no tier escalation

The source snapshot, visible task, task intent, hidden evaluators, and expected
values were frozen and pushed before the first runtime model call. This draw is
closed from rerun, candidate repair, and retrospective rescoring.

## Outcome

The run terminated `BLOCKED` after three outer traces and twelve
TheoryDeveloper client-tool turns. It scored research evaluation `0/1` and
hidden gold `0/1`. No independent theory review, generated algorithm,
simulation, Critic, hidden semantic evaluation, or Formalizer execution ran.
Formalization was correctly `not_applicable` and was not the blocker.

The model created one 255-line, 11,017-byte Markdown/LaTeX document with SHA-256
`1af41dd80f69ea8bfc7588b64fb7559e0850407d621518ed4ad1568dbd5c036d`.
That file is an unaccepted recovery artifact, not theory evidence.

## Trajectory

1. TheoryDeveloper inspected both hash-bound research documents.
2. It wrote the Markdown derivation and the compact problem, estimator,
   simulation, claim, and sanity-check indexes.
3. It spent one turn on a stale-hash edit, then read only lines 1-50 of an
   intermediate document and successfully made a later local edit.
4. Its fourth structured write made the packet structurally valid with one
   standard turn remaining.
5. `commit_theory_checkpoint` then rejected the candidate because the model had
   not inspected lines 1-255 at the final document SHA-256. No turn remained for
   a read or a model-owned progress checkpoint.

## Findings

### Shared workspace feedback defect

`write_theory_workspace` returned `workspace_valid=true` but did not report that
the checkpoint still lacked final-SHA document inspection. The exact missing
range was exposed only by the terminal commit. Structural validity and commit
readiness are distinct states; revealing the second only at commit wastes the
remaining model-owned decision budget.

The shared correction makes every valid write return
`checkpoint_commit_ready`, generic blockers, final inspection refs, and exact
missing path/hash/line ranges. It does not add a turn, retry, agent, scheduler,
content patch, statistical rule, or task-specific branch. The model still
chooses whether to inspect and commit or preserve honest progress.

### Active probability equality is false

The document says at line 43 that it chooses the radius so that
`Pr(D_n > epsilon) = alpha`. The supplied DKW-Massart premise provides only an
upper bound. Setting the upper-bound expression equal to alpha yields
`Pr(D_n > epsilon) <= alpha`; it does not make the true tail probability equal
alpha. Later lines use the correct inequality, but the false active step was
never marked rejected.

### Empty-sample ABI is not handled

The visible task requires a nonempty sample. Lines 177 and 203, the estimator
spec, and the termination guarantee instead claim validity for any finite
sample. At `n=0`, the ECDF normalization and DKW radius divide by zero. This is
a substantive executable-domain mismatch, not a JSON transport issue.

### Boundary description ignores clipping when epsilon exceeds one

Line 222 describes limiting bands as `[0, epsilon]` and `[1-epsilon, 1]`.
For permitted small samples and high confidence, epsilon can exceed one, so the
actual clipped limits are `[0, min(1, epsilon)]` and
`[max(0, 1-epsilon), 1]`. The model's own `check_boundary_behavior=PASS` did not
catch this counterexample.

### Additional precision issues

The document calls square-root-logarithmic growth in confidence "logarithmic"
and attributes finiteness of the supremum to right continuity rather than
bounded CDF values. These are secondary, but they reinforce that document
authority improves auditability without making self-review reliable.

## Disposition

The task remains `0/1`. The tool-feedback timing defect receives a shared
regression fix; the mathematical and ABI defects remain immutable evidence of
model capability limits. The candidate is not promoted, repaired, rerun, or
sent through hidden gold after the fact.
