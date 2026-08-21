# Exact Paired Sign Test L0 v1 Operator Audit

## Frozen identity

- Activation commit: `5a25adbeb6b90d3ddbfe7f026d48c9677bf81865`
- Task: `exact_paired_sign_test_known_result`
- Run: `runs/main_worker_research_l0_exact_sign_test_20260821_v1_referee_scratch_exact_haiku`
- Runtime manifest SHA-256: `b22e492713b490823819c7e4c40e360df9f9aa95839bc9fa1a2c6bda2d955eb9`
- Hidden-gold report SHA-256: `807ba3eec84520591e71ebe2963d23aabf2b237a3488d076953bfe80f53640dc`
- Model policy: exact `claude-haiku-4-5-20251001` for every enabled role; no tier escalation

The source snapshot, visible task, intent, hidden evaluators, and expected values
were frozen and pushed before the first runtime model call. This draw is closed
from rerun, candidate repair, and retrospective rescoring.

## Outcome

The run terminated `BLOCKED` after four outer traces. It scored research
evaluation `0/1`; hidden gold remained `0/1` and correctly did not execute
without independently accepted runtime artifacts. TheoryDeveloper completed a
checkpoint, but independent theory preflight produced no accepted review.
AlgorithmEngineer, SimulationEvaluator, Critic, and hidden execution did not
run. Formalization was correctly `not_applicable` and was not the blocker.

The model created one 237-line, 11,103-byte authoritative Markdown/LaTeX
document with SHA-256
`5596005e3edae4115579ad1dc2aeb63f70c27dc3348247341295660db82d733a`.
It is an unaccepted recovery artifact, not accepted theory evidence.

## Trajectory

1. TheoryDeveloper issued two source searches, read the complete Dixon-Mood and
   SciPy snapshot documents, and wrote the mathematical document plus compact
   consumer indexes.
2. The same model ran two exploratory Python calculations successfully and
   interpreted the raw results before committing its checkpoint. Neither
   calculation was promoted to confirmatory or proof evidence.
3. The independent referee read the complete theory document, made two
   model-chosen source searches in one turn, and used its optional scratch tool
   twice.
4. The referee made three terminal review submissions. All three were rejected
   by the identical runtime validation error: the first scratch execution ref
   lacked a request hash. The bounded review loop then exhausted without an
   accepted payload.

## Findings

### Failed scratch calls lacked stable request identity

The scientific sandbox intentionally returns an execution with a blank
`request_hash` when contract validation fails before request-file
materialization. The shared theory scratch adapter persisted that blank value,
while independent-preflight validation unconditionally required every scratch
ref to carry a request hash. Runtime itself injects these refs into the review
packet, so the referee could not repair or omit the poisoned field. Every later
submission was therefore impossible to accept.

Commit `75921c0d` preserves a stable hash of the exact model tool request and
operator-pinned execution parameters when the lower sandbox has not yet
materialized its request. Failure status, `execution_attempted=false`, errors,
and empty result evidence remain unchanged. This is provenance, not execution
success or scientific-content repair.

### Scratch ABI was not visible enough at the tool boundary

The second referee program defined `run_sandbox()` with no parameters and
called it itself. The isolated runner then returned the raw generated-source
error that `run_sandbox()` did not accept the injected `seed` argument. The
generic tool description now states the existing ABI directly: define, but do
not call, `run_sandbox(seed, replicates)` and return a named JSON-finite metric
object. The model still owns all source and receives raw execution feedback.

### The median derivation is circular or imprecise

The document first makes equal sign probabilities an explicit assumption, then
claims to derive them from continuity and median zero. Its proof says
`P(D <= 0) = 1/2` "by definition of median." A general median definition gives
two one-sided inequalities; continuity and the partition of probability are
needed to derive equality. The theorem is not invalid when equal signs are
assumed directly, but the requested implication is not derived as written.

### Zero handling overstates what continuity proves

Under the stated continuous model, an exact observed zero has probability zero
and `n_effective = n` almost surely. Once actual zeros are observed because of
rounding, measurement, or a different data-generating law, simply discarding
them does not by itself prove that the remaining signs are independent fair
coins. The document's statement that the retained differences are still i.i.d.
from the original continuous law is unsupported without a tie mechanism or a
scope restriction to the probability-one theorem event.

### The executable ABI does not match the frozen task

The visible task requires `run_estimator(request)`. The authoritative document
instead specifies `run_estimator(differences, alpha)`. Its returned field
semantics are otherwise aligned with inclusive binomial tails, but this
signature mismatch would block the required downstream consumer even if the
review transport had succeeded.

### Secondary precision issues

The document refers to nonexistent "Theorem 3.1" when its validity result is
Theorem 4.1. The superuniformity argument has the right tail-set structure, but
its key claim that each discrete tail set has probability at most `alpha/2` is
asserted rather than explicitly closed by choosing the extremal included
integer. These do not justify task credit and should have remained reviewable
model-owned mathematics.

## Disposition

The task remains `0/1`. The request-identity contradiction and scratch-tool ABI
visibility receive a shared regression fix; the mathematical, scope, and
estimator-ABI defects remain immutable capability evidence. The candidate is
not promoted, repaired, rerun, or sent through hidden gold after the fact.
