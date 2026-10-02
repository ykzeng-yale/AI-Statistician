# Statlib Foundation Migration Check

The current release foundation uses Lean 4.30.0. The inspected Statlib main
adds contiguity, e-variable and potential-response APIs on Lean 4.33.1. Test
the entire existing library against those exact upstream pins, not just a
small new import, before treating the newer declarations as active premises.

The prospective protocol fixes the source commit and allows only dependency
and toolchain changes in a separate local clone. Lake generates the dependency
manifest. Mathematical statements and proof bodies remain byte-identical.
Use the existing repository verifier guard; do not bypass a live owner or
launch concurrent Lean work. Record actual terminal results and diagnostic
logs. Cache reuse is allowed and must not be called a clean-machine build.

A successful build is only compatibility evidence. It does not establish all
declarations' axiom hygiene, source fidelity, textbook coverage, new statistical
theory or autonomous proof performance. Failure leaves the active project and
its verified index on the old pin. There is no model call, candidate repair,
rerun of a consumed research evaluation or automatic migration/fallback here.

Local preparation and logs: `runs/publication_foundation_migration_20261002/`.

## Observed Outcome

The [terminal record](observed_results.json) reports successful dependency update
and cache retrieval, followed by `lake build StatInference` exit 1 after 205.41
seconds, without timeout. Lake lists 41 failed targets; 165 native error lines
are diagnostics, not independent mathematical defects or theorem counts. For
example, the existing `ENNRealSeries` proof refers to a constant no longer found
in the candidate environment. No mathematical source was edited or regenerated.

Only the separate clone's toolchain, Lake configuration and generated manifest
changed. All owned commands ended and released the existing verifier guard.
The active library and RAG remain on the verified Lean 4.30.0 foundation. This
is a failed compatibility check, not a new proof or scientific result. It does
not prevent non-formal research comparisons from proceeding when their own
task, resource and evaluation requirements are ready.
