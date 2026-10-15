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
research. The custom statistical profile has not yet completed a live comparison.
This is not a standalone single-API implementation or publication evidence. The
paper/code audit and its reading exclusions are in
[the source review](../../docs/ai_scientist_v3_evidence_review_20261015.md).

The pinned upstream native evaluator now also executes real multi-file Python
and R fixtures, retaining outputs and raw errors and refusing a second evaluation
of the consumed attempt. This verifies project handoff without a new executor;
the opaque fixtures are not statistical experiments or model-generated research.
Upstream metric/source rubrics do not assess mathematical arguments. An unsupported
review rubric receives `assessment=failed` with evidence saying it cannot be
verified; this is not a finding that the mathematics is false. A separate exact-file
scientific assessment is still needed. The native drafting/final gap below remains.

The subsequent Bouchet conditions and their frozen configuration changes are in
[the module record](../../benchmarks/agentic_scientist_hc0_bouchet_20261015/README.md).
Fresh stock job 29684591 now reaches Qwen/Pi source authoring and the complete
fixed numerical study, but all candidate reference checks fail; theory remains
unassessed. Statistical job 29684597 is still running. These module observations
do not establish a full campaign, independent mathematical acceptance or Paper S.
The full campaign's cold-start issue is distinct: qualified runtime activation can
admit a finite-scored **incorrect** baseline, so "validated incumbent" does not
universally mean a solved task. Native pre-authored reconstruction skips that
activation and cannot currently reconcile its unscored starter. Upstream already
has null bootstrap state and first-correct-candidate promotion, but startup,
resume provenance and score-improvement stopping must agree before using them.
Do not remove only the startup check, invent a baseline score, or treat binary
computational compliance as mathematical task completion. This belongs in the
existing campaign interfaces, separately from native drafting/final verification.

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
Their previous evidence keeps its original scope. This migration has not changed
any `ai_statistician/` source or any EmpericalProcessLEAN proof.

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

Upstream code remains unmodified under its own Apache-2.0 LICENSE in the submodule.
Cite Lange et al., [The Agentic Scientist](https://arxiv.org/abs/2610.18933v1), and
the exact revision. Downstream prompts and guidance are this project's additions;
no textbook/source PDF or data rights are inferred from the code license. The
original project and third-party release-rights work remain open.
