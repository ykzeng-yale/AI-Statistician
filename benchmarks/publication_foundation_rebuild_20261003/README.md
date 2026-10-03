# Pinned Foundation Reconstruction

This release check rebuilds the active Lean 4.30.0 `StatInference` source in a
fresh checkout of its exact repository commit. It addresses the difference between
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

## Preparation Outcome

The [original preparation](preparation_result.json) exited 1 before invoking Lake.
Copying dependency Git metadata retained `core.filemode=true`, whereas the native
fresh clone on this ExFAT volume sets it to false. Statlib's 22 reported changes
were executable bits only; its content diff with permission bits ignored was empty.
All 11 copied dependency revisions subsequently matched the manifest, with no
content/type/symlink diff under the same check. No root build directory existed.
This is not a successful reconstruction or a failed Lean proof.

The separate [first-build protocol](build_protocol.json), fixed before compilation,
permits only matching the copied repositories' Git file-mode setting to the native
clone. It does not change tracked files, toolchain, Lake configuration or dependency
pins, and makes no permission-preservation claim. The original failed preparation
is retained; no scientific evaluation is retried or rescored. The first root-build
terminal result is reported separately below.

## Root Build Outcome

The [first root build](observed_results.json) timed out after 3600.372 seconds;
Lake was terminated with SIGTERM (return code -15; runner shell exit 241).
Its [original output](root_build_output.txt), [initial state](build_initial_state.json)
and [terminal record](terminal.json) are preserved byte-for-byte. The last reported
completion was Lake job 9526/9843. No native `error:` diagnostic line was observed
before termination; this does not establish success of the unfinished modules.
The fixed source and manifest were unchanged, and no local-library build directory
existed at startup. Copied third-party caches were used.

This is an incomplete source reconstruction under the recorded host, storage and
timeout, not a new proof rejection or a passing release test. It does not negate
the earlier incremental build, establish public installability or confer agent
credit. There was no retry, mathematical/source patch, dependency migration or
model call. Do not make this optional release check a gate on non-formal studies
or continue an infrastructure campaign in place of matched scientific experiments.

## Repository Access

The operator's configured Git access can fetch the pinned Lean source. On
2026-10-03, anonymous requests to its GitHub repository page and repository API
both returned 404. Public availability is therefore not established; this check
does not prove that an unauthenticated researcher can install the foundation.
No repository visibility or rights setting was changed.
