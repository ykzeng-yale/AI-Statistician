# Native FDA Reimplementation Development Study

Prospective one-family, one-draw-per-arm comparison, not an official efficacy
experiment or full theoretical research task. The entire paper family is excluded
from the future official test pool after these draws. Existing Haiku and Qwen
outcomes remain unchanged. This uses the original native Kimi ACP activation
surface rather than the earlier ineffective headless slash-text surface.

The [protocol](protocol.json) fixes local Qwen/native-host/skill pins, public
inputs, both arms, their order/resources and two source-derived reference variants
before inference. The [task](TASK.md) supplies the published paper and original
dataset, but not the replication script or reference predictions. The paper's
rounded result is visible, so this is not blind rediscovery. Both arms use the
same operator-prepared adapted Python environment; no autonomous installation
claim is possible.

`prepare_reference.py` executes only the author's Section 3.5 AST, replacing its
split random state with each declared seed, without modifying the original file
or scientific algorithm. Seed zero matches the displayed paper result; seed 17
has a different chosen grid configuration. The read-only numeric checker accepts
both actual reference fixtures, rejects copying split-zero results to split 17,
and rejects missing outputs. These are evaluator checks, not agent successes or
independent mathematical validation. The old full-script reference is not rerun
or reassessed; these are separately declared numerical variants.

`run_draw.py` is an operator client to the upstream ACP lifecycle. The host owns
all research, editing, execution and native context management. No agent/tool loop
or host controller is imported into the product. Final files are copied only by
the existing trusted native snapshot collector after termination. Missing files,
negative host exits, ACP completion and background termination stay separate.
Run each selected final source once for each reference seed in a fresh evaluator
directory. Hidden checks never return to its author. `research.md` stays unreviewed.

Native local access restrictions are declared, not OS-enforced; inspect actual
observations and retain this limitation. No model judge, copied reference output,
manual candidate repair, new inference proxy or task-specific product rule is
introduced. One paired draw estimates neither efficacy nor a population success
rate. A numerical-component pass is not independent theory or research-E2E credit.

## First Observed Outcomes

Both scheduled draws are terminal and unsuccessful. [Results](observed_results.json)
bind their native records and the first external executions, not a repaired rerun.
Skill body uptake was verified, but reading the full paper led the native host to
send a 45,809-token compaction request to the frozen 32,768-token server. Compaction
itself failed; no final artifact exists. Bare wrote source/report without reading
the paper or running code, observed missing outputs, and still reported completion.
Its unchanged final source exited 1 for an invalid SVC parameter in both declared
split checks. No predictions/metrics were produced. Both reports and mathematical
claims remain unaccepted; no efficacy inference follows from one pair.

`evaluate_final.py` resolves the exact final snapshots through the existing trusted
reader, then executes available source once per declared seed in fresh directories.
Its logs never return to the author. Supplied inputs stayed unchanged. The frozen
native runner incorrectly supplied a normalized mixed ACP transcript as process
stdout to the collector; the results contain an explicit metadata correction.
Original records and source are retained, not silently rewritten. Future native
capture must distinguish raw stdout bytes from normalized messages.
