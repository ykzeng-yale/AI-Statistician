# Statistical Research On Agentic Scientist

The user-selected new backbone is [Sakana AI's Agentic Scientist](https://github.com/SakanaAI/AI-Scientist-v3),
pinned as a Git submodule at `2b8aa39285c35aaca3b0e06dd121061ef8a2d854`.
It supplies the phase controller and coding-host execution. This integration
adds statistical research guidance through its existing task, preset and prompt
interfaces. It does not invoke our old `AgentRuntime` inside that controller.

**Current scope:** source installation, task preparation, actual upstream config
composition, six-phase command construction, statistical prompt rendering and
the real CLI's dry-run are verified. A separate native stock-v3/local-Qwen
[development observation](../../benchmarks/agentic_scientist_hc0_20261015/analysis.md)
now reaches actual host/model use; a prompt-delivery contrast reaches tool use
and source editing, but neither produces an evaluated candidate or complete
research. The custom statistical profile has not completed a clean efficacy comparison.
This is not a standalone single-API implementation or publication evidence. The
paper/code audit and its reading exclusions are in
[the source review](../../docs/ai_scientist_v3_evidence_review_20261015.md).

The pinned upstream native evaluator now also executes real multi-file Python
and R fixtures, retaining outputs and raw errors and refusing a second evaluation
of the consumed attempt. This verifies project handoff without a new executor;
the opaque fixtures are not statistical experiments or model-generated research.
Stock upstream metric/source rubrics do not assess mathematical arguments.
The native extension now attaches a separate source-bound AI review for declared
review criteria. Missing, interrupted or uncertain review is `not_assessed`, not
a finding that the mathematics is false. Its scientific reliability is not yet
qualified. The native drafting/final gap below remains.

The subsequent Bouchet conditions and their frozen configuration changes are in
[the module record](../../benchmarks/agentic_scientist_hc0_bouchet_20261015/README.md).
Fresh stock job 29684591 now reaches Qwen/Pi source authoring and the complete
fixed numerical study, but all candidate reference checks fail; theory remains
unassessed. Statistical job 29684597 passed all numerical checks but read the
exposed evaluator and ran prohibited extra diagnostics. Both host rubrics failed
because our preparer used unsupported nested metric fields; only future inputs
are fixed, with a real-upstream conformance test. See the
[terminal analysis](../../benchmarks/agentic_scientist_hc0_bouchet_20261015/short_tmp_analysis.md).
These module observations do not establish a full campaign, independent
mathematical acceptance, statistical efficacy or Paper S.

An explicit [native API extension](local_api_backend.patch) connects upstream
ideation and source authoring to our existing local API transport and retained
tool loop. A separate [fixed-requirement extension](native_campaign_semantics.patch)
uses upstream campaign/state/evaluator interfaces for unsolved reconstruction.
The complete native CLI tests start without a scored baseline, evaluate a failed
candidate, return its raw execution or independent review feedback to the next
author and evaluate a new candidate.
The author cannot weaken the fixed task criteria. These deterministic HTTP
fixtures are mechanism evidence, not live model research or a completed S system.

The stock optimization path still uses its original incumbent semantics.
Qualified runtime activation can admit a finite-scored **incorrect** baseline,
so "validated incumbent" does not universally mean a solved task. The explicit
fixed-requirement path instead permits an unscored starter and stops at the
operator's requirements plus evaluator correctness, never an invented score.
Native receipts and resume checks bind source, task, criteria and prior consumed
evidence. Pre-evaluation inputs and the program-spec source tree stay immutable;
new evaluator-produced CSVs, plots and other results receive separate hashes,
without filename-specific exemptions. Computational compliance is not mathematical
task completion.

## Prepare And Preview

From this repository root:

```sh
git submodule update --init --depth 1 third_party/ai-scientist-v3
uv sync --project third_party/ai-scientist-v3 --frozen --no-dev
export AI_STATISTICIAN_ROOT="$(pwd -P)"
export AGENTIC_TEMP_ROOT="$AI_STATISTICIAN_ROOT/runs/agentic-temp"
mkdir -p "$AGENTIC_TEMP_ROOT"
export AI_STATISTICIAN_AUTH_ROOT="$(mktemp -d "$AI_STATISTICIAN_ROOT/runs/agentic-auth.XXXXXX")"
mkdir -p "$AI_STATISTICIAN_AUTH_ROOT/.config/opencode"
cp integrations/agentic-scientist/opencode.local.json \
  "$AI_STATISTICIAN_AUTH_ROOT/.config/opencode/opencode.json"
.venv/bin/python scripts/prepare_agentic_task.py \
  --brief /absolute/path/to/research-brief.md \
  --destination "$AI_STATISTICIAN_ROOT/runs/new-research-task"
uv run --project third_party/ai-scientist-v3 --frozen --no-dev \
  agsci run "$AI_STATISTICIAN_ROOT/runs/new-research-task" \
  "hydra.searchpath=[file://$AI_STATISTICIAN_ROOT/integrations/agentic-scientist/configs]" \
  preset=statistician \
  "paths.results_root=$AI_STATISTICIAN_ROOT/runs/agentic-scientist" --dry-run
```

The preparer refuses an existing destination, retains the exact brief bytes and
copies the existing portable skill with its relative references. It launches no
process, agent or model. No paper, statistical formula or reference answer is
embedded in this generic task interface. The upstream `task.md` parser reads the
entire quoted brief, including its original headings. The original brief and
guidance live under `resources/search/`, the upstream candidate-visible resource
tree; the prompt reads them through upstream's `TASK_SOURCE_DIR`, not a guessed
host path or the writable attempt's current directory.

The preview uses upstream's six phases: drafting, investigation, ablations,
final evaluation, post-hoc analysis and paper. It creates no research outcome.
The conformance test blocks subprocess launches and network sockets inside that
dry-run. No new cloud model, Docker image or coding CLI was installed or run by
the preview. The Python environment was installed from upstream's own lock file.

## Native API Research Attempt

The canonical submodule stays unmodified for the stock comparator. Apply
`local_api_backend.patch` and then `native_campaign_semantics.patch` only to a
separate checkout of the exact pinned commit. The first supports native
`run.sh --agent local-api --harness-evaluated-attempt` and ideation through the
investigation CLI. The second supports pre-authored fixed-requirement tasks.
Drafting, paper generation, parallel workers and the full six-phase pipeline are not yet
integrated with this API participant. It never routes through Headless,
OpenCode, a cloud provider or the legacy `AgentRuntime` graph.

Set these absolute operator-owned paths before launching the patched runner:

```sh
export AI_STATISTICIAN_API_PYTHON=/absolute/path/to/product-python
export AI_STATISTICIAN_API_ENTRYPOINT=/absolute/path/to/AI-Statistician/scripts/run_agentic_api.py
export AI_STATISTICIAN_API_CONFIG=/absolute/path/to/frozen-api-config.json
```

The JSON configuration requires `model`, loopback `base_url`, `max_tokens`,
`temperature`, `timeout_seconds`, `max_turns` and `deployment_ref` with `path`
and `sha256`. The optional `public_source_horizon` is described below; omission
keeps the original source permissions. Freeze actual values and the deployment receipt before scientific
calls. The command's `--agent-model` must equal `model`. Runtime/template/sampling
not represented by these client fields belong in the pinned deployment receipt;
an operator declaration is not automatic verification of server internals.
No API key, model fallback or per-role model substitution is supported here.

### Model-Selected Public Sources

For a new source-permitted condition, set `public_source_horizon` to an ISO date
in the frozen API configuration. This reuses the existing Crossref/arXiv/GitHub
discovery tools in the same file-authoring session, not another agent or graph.
The model selects queries, follows opaque handles, reads bounded source text and
can acquire a previously resolved complete Git repository at an exact commit.
Acquisition does not install dependencies, execute code or establish replication.
Crossref reads are metadata/abstracts, not a journal's full paper; arXiv supports
versioned HTML and original source. Arbitrary PDFs and binary-data import are not
added by this connection.

Ideation and research share durable public observations under the campaign's
`.public-sources` store. Each source reviewer starts a separate model context and
source store under `.public-review-sources`, outside candidate source trees; no
author conversation, outcome or search history is inherited. Post-hoc analysis
remains limited to supplied artifacts and has no live discovery tools. Source
content, hashes and tool observations remain in the existing source store and
session transcript; neither retrieval nor reviewer agreement is proof.

This is live source access bounded by publication dates, not a historical web
snapshot or protection against benchmark-answer leakage. Use frozen source
snapshots for blinded rediscovery. Enabling this field changes the experimental
information condition: never add it to an active or consumed comparison, and
give compared arms the same declared access. Deterministic retained-loop and
actual upstream CLI/pipeline fixtures verify the connection, not research ability.

For a fixed-requirement investigation, the operator supplies a nonempty
`task_dir/target_rubrics.json` in upstream's rubric-list format, preserving explicit
metric/operator/threshold fields. It is not a model-authored evaluation contract.
Use the patched checkout's existing `python -m src.investigation.cli` with
`agent.name=local-api`, the exact `agent.model`, task/results paths,
`execution.harness_evaluated_attempts=true`, `container.enabled=false` and
`paper.enabled=false`. Select cycle and wall-time budgets for the workload.
Absence of the task rubric file selects stock optimization semantics, not an
implicit reconstruction fallback. Review criteria require the separate AI review
below; a source string match cannot establish a mathematical argument or proof.

The author uses generic list/read/search/write/exact-edit/remove/history/finish
tools. Substantive mathematics remains in Markdown/LaTeX and programs in source
files. No fixed equation count, statistical family, grammar repair or proof tactic
is encoded. The source-only execution policy comes from the upstream
harness-evaluated stage, not a claim that all future research must lack execution
tools. Host execution and independent review remain separate authorities.

The runner reuses upstream `program_clone` to copy the seed into the candidate,
preserving binary assets and upstream copy/exclusion rules. It does not copy
prior evaluator results as candidate evidence. The file view grants read-only
access to the staged seed, public task/idea/rubric,
selected skills and `resources/search`. Only `program_1/src`, its
`program_spec.toml`, and attempt-local `memory.md` are writable. `src` is the
pinned upstream version-1 program ABI. The current evaluator, its outputs,
unrelated directories and environment variables are not author tools. Linked
paths are rejected; this is an application file boundary, not an OS sandbox for
arbitrary shell execution. There is no shell tool in this source-only participant.
For a task with fixed criteria, the idea stage authors only `idea_bundle.json`
(identity, hypothesis, plan and author notes). The host attaches the unchanged
operator requirements to the existing downstream artifacts; the model neither
copies criteria nor authors source-marker checks. The native prompt and staged
skill render the same task contract. Unfixed optimization retains upstream
rubric authoring. The host owns global memory bookkeeping. The ownership
contract lives in system instructions; no file grant is widened and the research
prompt is unchanged. Both stages can read selected
prior source, public status and raw execution logs through `history/` file
references. Prior evaluator source is not granted. A new stage has a new model
conversation; file-backed history is not a claim of uninterrupted context.
Native generated-code execution itself is not OS-isolated by these file grants.

The file session states its configured turn/tool and output-token envelope in
the system context. This does not extend its budget, compact context or certify
completion. If an investigation child returns nonzero, the upstream pipeline
writes a failed completion marker and does not run posthoc. A hard-killed parent
can still leave a running marker; this artifact is not a process-liveness probe.

File changes require the current hash; exact edits reuse the existing helper.
Tool errors return to the same source-owning model, without a repair agent.
`finish(candidate)` hands source to the existing evaluator and does **not**
accept the science. `finish(gap)` exits incomplete without running the evaluator.
Completed responses and tool rounds atomically update an incomplete transcript,
returned usage and current file hashes. SIGTERM records interruption; SIGKILL
leaves only the last persisted prefix, not the in-flight response or a resumable
checkpoint. Exhausted/error sessions retain their current-source identity,
separately from initial authorization. An existing session directory is refused
rather than silently resumed or replaced. Explicit author-session resume remains
migration work. At a completed cycle boundary, the fixed campaign can validate
existing state and start a new cycle without rerunning a consumed evaluation;
this is not permission to resume a terminated scientific study. Partial or stale
evidence is rejected, not repaired. Native evaluation timeout recovery remains
unfinished. The existing local
transport now retains received stop/usage metadata when tool JSON decoding
fails, and stores the rejected parsed-provider response separately by hash.
No call from that response is executed or repaired; an unobserved response keeps
truncation unknown. This prospective fix does not alter the frozen a799e03f
development job or backfill any consumed record.

Per-attempt API evidence is under `.local-api/session`: deployment/input
references, exact source hashes, transcript, observations and actual returned
usage. These records are not parsed as Headless cost or reported as zero usage.
Native assistant `reasoning`/`reasoning_content` fields are now preserved as opaque
continuation state and passed back under their original field names. This uses
the existing thinking-block/session representation, not a new reasoning agent or
markup parser. That private state is not a source proof and is not granted to
independent reviewers or reporters. The consumed a799e03f condition predates this
fix and remains unchanged. A separately frozen long-workflow prefix now persists
fourteen native state blocks in actual ideation turns; complete-workflow and
long-context quality qualification remain pending.
The current participant connects native public discovery/read/acquisition as
described above, but not Python/R exploratory tools or Lean/RAG specialist tools.
Official evaluator-owned Python/R project execution is a separate boundary,
not arbitrary exploratory command access. Those validated specialist assets
remain intact. This extension
removes one CLI dependency; it is not a substitute for their integration or the
full independently assessed research workflow. The tested source-owner revision
cycle supplies a necessary handoff, not mathematical acceptance.

### Retained Official-Evaluation Iteration

For a **fresh native condition**, apply `native_iteration.patch` after the three
patches above, including `native_posthoc.patch`. Set the existing
`execution.harness_evaluated_attempts=false` (or its `investigation.` pipeline
prefix). This selects the upstream iterative investigation prompt instead of
the earlier source-only handoff. It does not modify frozen running conditions.
The ordinary upstream evaluation-count and stage-time budgets still apply.

The same retained model session now has `evaluate_program` and `clone_program`
alongside the existing file tools. Evaluation invokes upstream
`run_harness_evaluation` with its selected task interpreter, fixed criteria and
fresh source-bound reviewer. Observations are paged read-only files, not copied
entirely into the tool response. A model can inspect the raw failure, clone a
new version through upstream's guarded command, edit it and evaluate it without
re-ideation. Even a completed nonzero evaluator exit can remain unscored: no
finite score or accepted baseline is invented to permit a source revision.

Consumed source is read-only, old evaluator results are excluded from clones,
each new receipt binds its parent's receipt, and accepted candidates stop
cloning. Source/receipt tampering, repeat evaluation, budget exhaustion and
private result access fail explicitly. The model owns every edit and decides
whether to continue or report a gap; there is no repair agent, source patcher,
new scheduler or problem-family rule. Independent review remains an assessment,
not mathematical proof. Native execution is still not an OS sandbox; sealed
multi-candidate evaluation and session restart are not claimed.

Actual upstream HTTP-fixture tests cover process failure without metrics,
structured public error with empty stderr, independent-review rejection,
same-session revision, posthoc handoff and immutable receipt-chain resume.
These are mechanism tests, not model research or official H/S efficacy.

### Independent Source Review

For frozen `type=review` criteria, the native host invokes the same pinned API
in a fresh reviewer context after successful computational execution and before
finalizing the evaluation receipt. It uses the existing file/session loop, not
the legacy reviewer controller or a new scheduler. No review criteria means no
review call. The sealed evaluator path is unchanged.

The reviewer reads the exact pre-evaluation candidate files, task, criteria and
permitted sources. Only its Markdown report is writable. Author conversations,
prior reviewer opinions and numerical evaluator outputs are not granted.
Candidate-authored text can still assert outcomes; this is tool-level context
separation, not a guarantee of no anchoring or shared-model error.
The [review prompt](prompts/scientific-review.md) asks for source-located findings
and decisive reasoning, without fixed equation counts or task-specific rules.

`submit_review` returns PASS, FAIL or UNCERTAIN for every fixed review criterion.
The host checks source/task/criteria/model/report/session identities; it does not
infer mathematical correctness from their hashes. It preserves reviewer logs,
the report, dispositions and private session under the evaluated program. A
missing or invalid receipt remains unassessed. It never retries a consumed review.
The next source owner can read the report and public logs through existing history;
the reviewer cannot revise the candidate or choose the next research action.
History also exposes the evaluator's explicitly declared public output files,
read-only and checked against their receipt hashes. It does not expose all receipt
evidence or private evaluator data. Evaluators that capture source exceptions
inside structured results must declare a public observation artifact if authors
are to receive that feedback; empty process stderr does not establish successful
source execution. The new process fixture covers this route without interpreting
or repairing an error. This prospective correction does not alter the running
frozen HC0 condition or make its undeclared replicate stream public.

The combined HTTP test verifies that numeric success plus review failure does
not complete the campaign. This is deterministic mechanism evidence only.
Source review cannot certify observed simulation outcomes, a theorem, human
endorsement or publication quality. Same-model author/reviewer errors may agree;
scientific qualification and independent empirical assessment remain required.

### Reporting Existing Results

Apply `native_posthoc.patch` after the two patches above, only to the same exact
disposable upstream checkout. It extends the existing posthoc pipeline; it does
not add a controller or rerun the scientific evaluator. Sakana AI's Apache-2.0
license and pinned source attribution remain unchanged.

Before a new evaluation, the operator can supply task-root `public_outputs.json`:

```json
[{"path": "tables/study_summary.csv", "kind": "table", "media_type": "text/csv"}]
```

Entries use upstream scientific-evidence artifact descriptors with explicit
candidate-relative paths, not globs. They must be new evaluator result files,
not preexisting author source. The native receipt binds the declaration and task
before execution, then the result bytes. Missing declared files cannot silently
disappear. Do not add this declaration to a consumed study to obtain a new report.

For this artifact-only API path, prospectively supply upstream-format
`task/posthoc/posthoc_bundle.json` and `task/posthoc/posthoc_selection.json`.
The report question is a task input, frozen with the scientific brief before calls.
The posthoc controller stages it into its fresh generation directory without
replacing existing plans. Use the existing `src.posthoc_pipeline.cli` stages
`0,1,4,5,6`, `agent.name=local-api`, the same frozen API configuration,
`container.enabled=false`, `execution.checkpoint_mode=optional` and
`execution.retrain_if_checkpoint_missing=false`. The supplied analysis specifies
the report question and required outputs, not an expected scientific answer.
Native generation/selection, checkpoint analysis and full manuscript production
are not implemented by this path. The same outer `src.pipeline.cli` can now run
`execution.phases=investigation,posthoc` with native harness-owned evaluation.
It forwards the consumed candidate's public results rather than an ablation
directory. Other native phases remain unsupported; their existing verification
requirements are unchanged. A complete HTTP process test covers a failed review,
a new source candidate, completed evaluation and a report within this controller.

Extraction verifies the consumed candidate receipt and stages only its declared
public outputs under `evidence/`, using upstream's size/hash manifest with role
`completed_native_evaluation`. Private review sessions are excluded. Existing
upstream evidence limits still apply; declare summary tables appropriate for the
report instead of assuming arbitrary large replicate files are supported.
The actual API process runs in the upstream attempt directory. Task, candidate
source, permitted `resources/search` (including retained statistical skills) and
result tables are read-only; declared report files are writable.
Public `scientific_review.md` findings and the compact verdict receipt, when
present, are also read-only report inputs. The private reviewer conversation is
not granted. For a frozen non-winning study, extraction verifies the originating
evaluation receipt through upstream's verified selection, preserving its identity
instead of treating the copied snapshot as a newly evaluated program.
There is no execution tool: this stage interprets existing results and must not
claim it generated new calculations, figures or proof. An honest gap is not
published as a completed analysis, even if output files exist.

The upstream publisher's `valid` means its artifact checks passed, not that a
statistical claim, self-rubric or manuscript is scientifically accepted. Report
accuracy needs separate assessment. Deterministic HTTP fixtures exercise the
real extraction/bootstrap/materialization/API/publication path and verify that
consumed source/results remain unchanged and the evaluator executes only once.

This migration adds a small participant alongside the retained legacy code. The
package source ceiling increases explicitly from 150000 to 150500 lines; the
legacy runtime/CLI limits remain unchanged. This is temporary migration overlap,
not a reason to expand the old controller or hide code outside its measured tree.

## What Changes

| Upstream owner | Statistical integration and remaining boundary |
| --- | --- |
| `src/pipeline/cli.py`, `phases.py` | Sole outer phase controller; the preset never invokes the legacy research graph |
| `src/investigation/main_entry.py`, `src/scripts/idea.sh`, `run.sh` | Retain candidate/attempt execution; substantive theory and code stay in files, not idea JSON |
| `src/investigation/state.py`, `src/pipeline/downstream_selection.py` | Retain lineage, memory and selection; exact claim/reviewer evidence joins still need integration |
| Task drafting and final evaluation | Preserve task/verifier authority; native Python/R/Lean execution boundaries remain unfinished |
| `src/scripts/lib/container_agent.sh` and Headless | Reuse coding hosts for H; S still needs an actual single-API specialist backend |
| `src/scripts/paper.sh`, `src/orchestrator/paper_*` | Reuse grounded writing; add statistical main/appendix guidance now, journal venue/render QA later |

- `prompts/investigate.md` replaces the upstream execution prompt through
  `investigation.paths.instruct`. The revised default follows evaluator-owned
  execution: the author prepares a complete theory, method and simulation
  candidate; additional diagnostic execution requires explicit permission in
  the public task contract. Small simulations are not a mandatory extra stage.
  The preset uses upstream harness-owned evaluation: the author can
  revise `program_1/src/` before handoff, but cannot invoke the
  official evaluator or write its result artifacts. The existing host performs
  that evaluation after author exit. No additional research scheduler is added.
- Substantive mathematics stays in candidate-owned Markdown/LaTeX files under
  `src/`, alongside code. Idea/rubric JSON remains a small coordination format,
  not the mathematical artifact or a certificate of correctness.
- `prompts/manuscript.md` supplies statistical methods, ADEMP, application and
  complete proof/experiment supplement guidance through `paper.venue_file`.
  `prompts/contributions.md` supplies attribution and claim boundaries. The
  inherited ICLR layout/page checks are provisional, not journal-template support.
  Our H/S comparison requirements apply only to those study briefs, not to every
  future statistical or biostatistical methods paper.
- No-winner and verified non-qualifying results may support an explicitly negative
  report under upstream policy. Missing required evidence still blocks completion;
  a written manuscript is never relabelled scientific success.
- Lean is intent-selected. The portable tooling reference points to the existing
  Statlib/Mathlib/StatInference project, retrieval and axiom tools. Their actual
  use through this backbone, native R and exact claim/evidence joins remain to
  be integrated and evaluated, not inferred from tool availability.

## Preserve The Statistical Subsystems

Only the outer coordinator is being replaced. The existing scientific components
remain the implementation assets, not deprecated experiments to re-create in v3.
Their previous evidence keeps its original scope. This migration reuses the
retained loop and adds a file participant; it does not change existing scientific
workspaces or any EmpericalProcessLEAN proof.

| Retained asset | Reuse at the new boundary |
| --- | --- |
| `skills/statistical-research/` | Already staged byte-for-byte into the full-package task, including derivation, methods, simulation and writing guidance |
| `theory_workspace.py`, `client_tool_loop.py` | Keep file-backed arguments, exact model-authored edits, retained observations and checkpoints; reuse session/tool primitives for API specialists, not a second controller |
| `research_source_discovery.py`, `research_source_project.py`, `research_source_library.py` | Keep permitted-source acquisition, pinned code/data/documents and baseline provenance; v3 task/candidate memory does not replace source qualification |
| `scientific_code_workspace.py`, `scientific_sandbox.py` | Keep multi-file Python/R authoring, native/scientific runtimes, integration feedback and source ownership; execute/review the exact selected files |
| `metric_protocol_stage.py`, `generated_metric_contract.py` | Keep theory-bound, outcome-blind confirmation and evaluator authority; simplify transport where compatible, not the scientific boundary |
| `generated_code_semantic_reviewer_llm.py`, `formal_target_semantic_reviewer_llm.py` | Keep isolated exact-artifact review and return findings to the source owner; upstream rubric scores cannot replace statement/procedure review |
| `formal_source_index.py`, `formal_source_hybrid.py`, `lean_candidate_revision_tool_loop.py`, `lean_project.py` | Keep task/proof-state retrieval, multi-file Lean iteration, diagnostics and project identity; no new grammar/tactic repair rules |
| Pinned EmpericalProcessLEAN/StatInference, Statlib/Mathlib and axiom tools | Keep the actual foundation, declaration provenance and exact proof authority; discovery corpora are not automatically active-project dependencies |
| Local model backend, artifact fingerprints and publication evaluators | Keep pinned Qwen requests, lineage, external assessment and all immutable outcomes; do not relabel old draws as new-backbone evidence |

Except for skill/prompt/config staging, these boundary integrations remain to be
verified under v3. The code is retained; capability parity is not yet demonstrated.
The optional OCI `native_project.py` tool is not a prerequisite for this migration
and does not justify rebuilding the earlier VM/network workstream.

Use upstream's existing `scientific-evidence` references and sidecars for report
provenance rather than a second ledger. Its `resolved`/`anchored` links establish
only their documented provenance scope, not mathematical truth or independent
acceptance. Bind our reviewer/verifier findings to the exact scientific files.
The six-phase preset is a full-report default, not a mandatory scientific order.
Select phases according to task intent without bypassing required final evidence.
Complete deliverables do not imply one-shot generation; execution/review findings
return to the source owner through upstream's existing attempt workflow. Full
simulation requires an evaluator that actually runs that study, not only unit
agreement or self-authored rubric checks. Mathematical assessment stays separate.

## Local Model And Execution Boundaries

The preset selects OpenCode with the existing local Qwen model. The checked-in
OpenCode example enables only `local-qwen`, points at loopback and includes no
credential. This follows the official [custom provider](https://opencode.ai/docs/providers/#custom-provider)
and [configuration](https://opencode.ai/docs/config/) interfaces. It is not an
isolation boundary. Config
precedence, effective requests and exact weights/runtime/template/decoding must
be observed before a live scientific condition. Do not infer a working backend
from a model name. The latest observation's owned Qwen server is closed.

The 4B preset is a recorded development configuration, not a model-size limit.
The user authorizes larger open-weight Qwen models and long runs on Bouchet.
Use explicit upstream model/config overrides for a prospectively fixed condition;
do not change consumed results or silently substitute a shared service's latest
alias. Prefer existing cluster runtimes, and qualify the actual scientific workload
before committing a long allocation. Cluster availability is not a completed
full-system deployment. The authorized resource policy is in the execution goal.

Upstream pins Headless at `93cd9b06b85f848af1308c41e018991b33907c5e`
and documents OpenCode `1.18.29`. Both executed in the separate native observation,
with fresh HOME, pinned local model and recorded logs. Headless's build summaries
omit host title calls; the observation records both. Exact request bodies and
effective per-call sampling were not captured, so this is not yet a publication
reproducibility condition. Stock OpenCode prompt delivery and the separate one-line
transport contrast are documented; the canonical upstream submodule is unchanged.
Its default cloud reviewer is not selected. Its concept-figure skill is excluded
from the paper skill set and the manuscript brief requests local data-driven
plots, not Autoillustrate or image APIs. No credentials or whole `.env` are
named by this preset. Upstream seeds OpenCode's configuration from the explicit
fresh auth root; do not point it at the operator's credential-bearing HOME or
enable subscription bridging for a local scientific condition. A real run must
still verify its full effective access;
prompts/configuration alone do not establish absence of unauthorized calls.

**Important native gap:** the upstream validator requires `container.enabled=true`
for task drafting and final evaluation, and its final command explicitly uses a
container image. Consequently the full preset retains that existing upstream
backend. Turning the flag off does not provide native E2E execution; our test
records the exact rejection. No VM, proxy, Docker installation or image build is
added here. Reusing our local execution/verifier tools at those boundaries is
remaining migration work, not a reason to bypass final validation. Local-model
endpoint reachability inside a container is also unqualified on this Mac.

## Migration And Publication Work

1. Replace the outer workflow with this backbone; keep the legacy implementation
   only for its existing tests, reusable scientific tools and historical records.
   Do not run both schedulers. The checked-in profile is the first integration,
   not completion of that replacement.
2. Complete local execution/evaluator boundaries, file-backed theory/reviewer
   provenance, Python/R and optional Lean tooling without task-answer rules.
   A task/model/evaluator proposal generated by an agent is not external gold.
3. Implement the actual single-API specialist path at the stage boundary. Reuse
   suitable retained-session/tool components without calling the old outer graph.
   A CLI-backed v3 run is labelled as such and cannot pass for Paper S evidence.
4. Add a proper arXiv/statistical-journal venue/template and supporting-material
   workflow, then verify actual generated artifacts. Do not hardcode manuscript
   success from the upstream page/compile checks.
5. Requalify published-method tasks and common external AI/executable assessment;
   the consumed failed Qwen qualification remains failed. For H add an unmodified
   v3 comparator as well as the bare host. Reassemble S's same-model controls on
   the common backbone before official calls. No old result is rerun or relabelled.
   Use genuinely supported hosts for matched v3 comparisons. Kimi portable-skill
   compatibility is retained separately; upstream's current backend list has no
   Kimi entry, so its compatibility cannot be relabelled a v3/Kimi efficacy arm.

The existing [40-item programme](../../docs/publication_programme.md) remains the
completion record. No checklist credit or research-readiness percentage follows
from this integration. The two papers must establish their statistical additions
and incremental effects rather than rename upstream orchestration.

## Tests And Attribution

```sh
.venv/bin/pytest -q tests/test_agentic_task_preparation.py \
  tests/test_agentic_scientist_backbone.py tests/test_portable_skill.py
```

With the pinned upstream environment and native Rscript available: 26 passed,
5 existing opt-in host checks skipped. Without the upstream environment the real
conformance checks explicitly skip; R checks also require Rscript. The preparer
remains dependency-free. Four tests invoke the actual upstream evaluator on opaque
Python/R success/failure fixtures; the remaining preparation/config/preview checks
do not execute it. No check calls a model or establishes scientific capability.
The separate live native observation remains unchanged. Full regression scope is
recorded in the project status after completion.

Native API campaign checks additionally run `test_agentic_api_campaign.py`,
`test_agentic_api_backend_patch.py`, `test_agentic_api_workspace.py` and
`test_agentic_native_campaign_semantics.py`. They require the pinned upstream
Python environment; shell process checks require Bash 4+ (`AI_STATISTICIAN_V3_BASH`).
On macOS use a canonical temporary path such as `/private/tmp`, not its `/tmp`
symlink. The broader upstream comparison currently has two identical failures
in stock and patched checkouts: the coding-host timeout fixture and native
publication-recovery descriptor path. These are not claimed as passing checks
or addressed by disabling upstream safeguards. The exact records live under
`runs/agentic_api_campaign_20261015/` and in the measured status.

Upstream code remains unmodified under its own Apache-2.0 LICENSE in the submodule.
Cite Lange et al., [The Agentic Scientist](https://arxiv.org/abs/2610.18933v1), and
the exact revision. Downstream prompts and guidance are this project's additions;
no textbook/source PDF or data rights are inferred from the code license. The
original project and third-party release-rights work remain open.
