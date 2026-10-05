# Installed Local-Tool Qualification

This is a prospectively recorded installation/mechanism check, supporting R02 of
the [publication checklist](../../docs/publication_programme.md). It is not an
official comparative study, a scientific reproduction or a proof. R02 remains
open. No model calls or consumed-evaluation changes occurred.

## Fixed Scope and Changes

The [plan](plan.json) and [synthetic probe](probe_installed_tools.py) were committed
at `71205913607a8621b6d4c71c76587a5b799baeed` before the first wheel build. The
default local provider was incorrectly classified as unknown, and installed
diagnosis incorrectly required the caller's directory to contain package source
and example questions. Diagnosis now uses the installed module location, treats
examples as optional, and reuses the existing local-backend URL validation.
No endpoint request, statistical answer, repair action or new executor was added.
Explicitly empty URLs are rejected rather than inheriting another configuration.

The first complete regression attempt detected the unchanged product-size limit
at 150001 lines. It was interrupted after diagnosis, not reported as passing.
Deduplicating the existing optional cloud checks reduced the product to 149991
lines without changing the limit. Four mock contract tests preserve prior cloud
behavior; they make no API calls. The corrected source was committed at
`53839f1d640f45ec9b11fe2a35ecd18f1decee6f` before a new wheel/environment check.

## Observed Installation and Tool Scope

- Selected tracked inputs were archived; no old `.env`, Python environment,
  `node_modules`, study output or Lean artifacts were copied. Both wheels and
  preparation attempts are retained locally.
- The final wheel was installed without extras into a new CPython 3.12.13 venv.
  CLI help/list/doctor ran from a separate empty researcher workspace, with a new
  HOME and explicit minimal environment. Required installation checks passed;
  absent examples, external proof services and repository docs remained optional.
  Doctor's readiness fields are configuration checks, not live-model authority.
- `npm ci --omit=dev` and the unchanged preparation command ran using the committed
  lock in the first source capsule. That newly prepared runtime was explicitly
  reused for the corrected wheel; its lock and adapter bytes were unchanged.
  This is not a second independent npm reconstruction.
- The installed Python tool imported NumPy, SciPy, pandas, scikit-learn,
  statsmodels and SymPy, and imported a second local file. The R tool sourced a
  second local file using base/stats. Both returned the fixed synthetic marker.
  Deliberate helper failures in both languages returned raw errors and nonzero
  status while preserving the exact main/helper source. These are ABI fixtures,
  not estimators, simulations, proofs or demonstrated same-model revisions.
- The source capsule contains exactly the skill's three files; both relative
  references resolve. No host activation was attempted in this check. Existing
  native-host observations retain their separate scope.

The [results record](results.json) binds source, wheel, runtime, raw observations
and regression. Raw artifacts remain under
`runs/publication_release_qualification_20261003/`; rights must be resolved before
distributing them. Installed file inventories exclude generated Python bytecode;
runtime inventories include the newly downloaded WASM wheels. Version lists and
inventory hashes are observations, not a guarantee of future byte-identical builds.

The default full suite on corrected source completed with 2139 passed, 30 skipped
and one existing xfail in 1443.32 seconds, exit zero. Twelve explicit native-R
integration checks were among the skips; other opt-in model/host/container checks
were not activated. The installed WASM fixtures above did execute. Focused
diagnosis/backend/environment tests passed 67 checks with one opt-in skip;
compileall passed. Earlier native-R verification retains its own distinct record.

## Reconstruction Instructions

Use the exact source pin in `results.json`, CPython 3.12, and the recorded Node/npm
condition. In a newly extracted tracked source capsule, build the application
wheel, install it into a fresh venv without extras, run `npm ci --omit=dev` and
`npm run prepare:scientific-sandbox`. Do not copy a previous runtime or environment.
These are reconstruction instructions, not a request to overwrite this record.
Before calling the installed CLI or probe from another working directory, set:

```sh
export AI_STATISTICIAN_SCIENTIFIC_SANDBOX_NODE_MODULES="/absolute/path/to/new/source/node_modules"
/absolute/path/to/new/venv/bin/ai-statistician --help
/absolute/path/to/new/venv/bin/ai-statistician list
/absolute/path/to/new/venv/bin/ai-statistician doctor --out /new/doctor/output --json
/absolute/path/to/new/venv/bin/python \
  /absolute/path/to/new/source/benchmarks/publication_release_qualification_20261003/probe_installed_tools.py \
  /new/probe/output
```

The probe refuses an existing output directory. Initialization downloads required
dependencies; generated fixture execution itself remains local. Use a new HOME
and no inherited credentials. A first preparation invocation selected a nonexistent
versioned Python path and failed; the observed managed interpreter path was then
used successfully. The failure logs and interrupted regression remain distinct
from later successful commands.

## Limits

This fresh venv is on the operator's existing macOS 26.5.2 arm64 machine and reuses
its Python/Node binaries and `sandbox-exec`. The scientific runtime currently
requires that macOS isolation provider. No new-machine, Linux/Windows, native R,
Lean, actual Qwen server, long-session, researcher usability or scientific efficacy
claim is supported here. The two publications still require qualified official
comparisons, independent mathematical assessment, substantive case results and
resolved release rights.

## Second-Machine Reconstruction: 2026-10-05

The separate [plan](cross_machine_plan.json) and
[reconstruction driver](cross_machine_reconstruct.py) were committed at
`23b36c42f954e8d22a8ac03eca79cb8fde2f0078` before transfer/installation. This is a
new condition, not a rerun or reinterpretation of the earlier record. Source is
pinned at `50dcec2550d35d5b5032225e77c91308676c9dfe`; the existing probe is unchanged.

On another owned Apple M4 Mac with macOS 15.3.1, existing Python 3.12.12 and
Node 22.22.0, all ten recorded stages passed: build, fresh venv, declared base
dependencies, new npm cache/runtime preparation, installed CLI checks, Python/R
probe and dependency reporting. Stages took 31.83 seconds, excluding admission,
transfer/capture/retrieval. Positive two-file fixtures and raw helper failures
passed; all 154 archived source files remain exact. The [results](cross_machine_results.json)
bind source, wheel, inventories and every stage channel. Raw material remains at
`runs/publication_release_cross_machine_20261005/`; no model/scientific task ran.

The driver accepts the plan, extracted source, nonexistent output directory and
existing observed uv/Python/Node-bin paths:

```sh
/existing/python3.12 cross_machine_reconstruct.py \
  cross_machine_plan.json /new/task/source /new/task/execution \
  /existing/uv /existing/python3.12 /existing/node/bin
```

Use the exact archive members in the plan, not an old environment/runtime. New
HOME and caches prevent implicit reuse; required public downloads occur during
preparation. The driver stops on the first failed stage and bounds owned process
groups. Post-stage disk checks and Node old-space are not hard disk/RSS quotas.
Build dependencies were not prospectively locked; the wheel reports setuptools
84.0.0 and cache metadata is retained. Preparation/capture errors remain disclosed.

This supports installation/tool execution on another existing Mac/version
condition. Neither machine was factory-reset. It establishes no Linux/Windows,
native-R, Lean, model deployment, host activation, model-owned revision, researcher
usability or statistical correctness. Doctor readiness is configuration only.
After verified retrieval, only the owned remote tree was removed; peer work and
global configuration were untouched. R02 and scientific comparisons remain open.
