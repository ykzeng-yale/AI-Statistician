# Pinned Foundation Reconstruction

This release check rebuilds the active Lean 4.30.0 `StatInference` source in a
fresh checkout of its exact public commit. It addresses the difference between
the existing incremental build and reconstruction without local-library build
artifacts. The prospective [protocol](protocol.json) permits copied, revision-checked
third-party dependency caches. It is not a cold dependency or clean-machine test.

The checkout is on the operator's mounted T7 volume because the main disk lacks
comfortable space for another complete library build. Source, toolchain, Lake
configuration and manifest must remain unchanged. Use the existing active-project
verifier guard rather than introduce another build scheduler. Store the raw build
log and first terminal record under `runs/publication_foundation_rebuild_20261003/`.

A passing root build establishes only this source reconstruction in the recorded
environment. It does not establish all declarations' axiom hygiene, source-book
fidelity, coverage, mathematical novelty, model performance or release rights.
The active project and RAG are unchanged. No model calls or consumed scientific
evaluations are involved.
