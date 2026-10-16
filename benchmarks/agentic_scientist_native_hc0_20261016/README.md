# Native API HC0 Workflow Development

Prepared October 16, 2026. Frozen and submitted once as job **29722963**; its
first observed state was `PENDING`, with no scientific calls at submission.
See [prospective configuration](precall.json), [deployment](deployment_receipt.json)
and [submission receipt](submission.json). Submission does not establish a start
time, completed research or an official comparison.
The subsequent [live observation](runtime_observation.json) records allocation,
successful startup and the first nine completed API/tool turns, with ideation
still in flight. It is not a terminal outcome or a completed scientific study.
This reuses the exposed HC0 family and unchanged full-study evaluator from the
October 15 Bouchet observation. Earlier candidates, reviews, results and scores
remain consumed and unchanged.

The question is whether one pinned open-weight API can carry the existing
upstream controller through candidate authoring, host execution, source review,
revision and interpretation of the actual outputs. The scientific setting is
the same twelve-cell, 5,000-dataset-per-cell comparison. The host owns simulation
generation and aggregation; this condition does not test autonomous study design
or simulation-program generation. The separate application and full manuscript
workflow remain outside this development check.

Both arms use the same pinned Qwen3.8-27B BF16 deployment, API/file tools, fixed
criteria, environment and scientific inputs. `stock` uses the pinned upstream
investigation instruction; `statistical` uses the statistical instruction and
portable guidance. Both receive the same fresh-context AI source review and
artifact-only reporting. This is a guidance-bundle development contrast through
the native API adaptation, not an unmodified-v3 run, the portable-host H study,
the full four-arm S study or a causal model-size comparison.

One draw per arm, ordered stock then statistical, cannot establish a population
effect. Each arm permits at most three candidate cycles, one idea-generation
attempt per cycle, four hours per source-authoring session, thirty minutes each
for host evaluation and review, and up to three one-hour report attempts.
The Slurm envelope is 48 hours for both arms, not a shorter hidden total deadline.
This permits findings-driven revision; three cycles are a ceiling, not mandatory
extra passes. The original paper is identified bibliographically; its full text is not
supplied. This is known-method rederivation using available model knowledge and
permitted local material, not a controlled historical rediscovery experiment.
AI reviewers have not been scientifically calibrated. Their dispositions are
internal feedback; numerical agreement and report file checks do not establish
mathematical correctness or publication quality.

## Run Through The Existing Controller

`prepare.py` creates strictly new arm directories, retaining the exact old
evaluator and an unimplemented seed. It freezes task requirements, public result
declarations and the report question before calls. The prepared hashes include
the statistical guidance only in its declared arm. Never update these inputs
after an arm starts.

Apply the three integration patches, in their documented order, to a separate
checkout of upstream `2b8aa39285c35aaca3b0e06dd121061ef8a2d854`.
Invoke that checkout's `src.pipeline.cli` with
`execution.phases=investigation,posthoc`, `agent.name=local-api`, an explicit model,
`container.enabled=false`, `versioning.enabled=false` and
`investigation.execution.harness_evaluated_attempts=true`. The fixed requirements
allow a genuine reconstruction cold start. All routine source/tool/reviewer
feedback remains in the existing candidate workflow.

The outer controller selects posthoc stages `0,1,4,5,6` and consumes the analysis
plan from `task/posthoc/`. It does not pass a nonexistent ablation bundle. The
actual attempt receives the public-output declaration before its evaluation.
Reporting verifies the originating native receipt even when upstream selected a
frozen non-winning study snapshot. Public review findings may inform the report;
private reviewer sessions are not granted. Missing or inconclusive science remains
visible, including when the controller regards reporting as a best-effort phase.

The API author can read/write ordinary mathematical and program files but cannot
call the official evaluator. Native candidate execution is not OS-isolated by
these file grants. Full API request bodies, tool observations, source identities,
returned usage, execution logs and reviewer/report artifacts must be preserved.

## Before Scientific Calls

The model deployment probe must finish first. Preserve its startup failures;
do not silently substitute the managed shared model, a different precision or a
smaller context. `prepare_remote.sh` resolves a separate worker environment from
the exact upstream lock plus the existing scientific versions and JSON-schema
dependency, records hashes and packages it for node-local use. It makes no model
call. It does not modify the environments used by earlier observations.

Freeze the final product/patch commit and archives, both prepared task trees,
resolved worker requirements, model/runtime/template/sampling, actual resources,
arm order and source/review/report budgets before activation. The prepared task
and passing process fixtures alone do not activate a scientific condition.
All failed and absent artifacts stay in the record; no consumed candidate or
review is executed again for another score.
