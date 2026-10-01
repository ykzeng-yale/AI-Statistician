# Native Open-Weight Development Pilot

This is one paper family's attempted function-level source-replication integration test,
not an official publication study, full research-E2E result, blind rediscovery,
or original CORE-Bench benchmark score. Six simulation settings are repeated
measurements within the same family. One draw per arm cannot estimate general
harness efficacy or reliability. Mathematical review is not automated here.

The source is the MIT-licensed code from Bertoldo, Zandonella Callegher and
Altoe's *Designing Studies and Evaluating Research Results: Type M and Type S
Errors for Pearson Correlation Coefficient*, distributed through public
CORE-Bench `core_train` capsule `7935517`,
[Code Ocean DOI](https://doi.org/10.24433/CO.8165442.v1).
The model sees the unchanged author function but not old numerical outputs.
Use of existing code is intentional replication, not an autonomous invention.

## Frozen Comparison

`protocol.json`, `TASK.md`, `scenarios.csv` and `reference.R` were committed
before either native-host model call. Final pre-call commit: `50b91d62`.
Earlier pre-call revisions corrected an unused host UI preference; no model
draw had been started. Each final scheduled draw is consumed once, without
resume, operator output edits or result-dependent replacement.

Both conditions run Kimi Code 2.1.1 with the same local Qwen3-4B Q4_K_M,
native tools, 600-second wall envelope and prepared R environment. The treatment
offers only the statistical-research skill. Each gets a separate project and host
data root. The pinned server is resident across the ordered draws; cache/warmup
effects mean this small pilot is not a latency-effect comparison. No cloud
model or independent model referee participates.

This is a native open-weight host check, not the separately authorized local
Claude Code compatibility check, and not the standalone multi-agent system.

## Reproduction Setup

1. Verify every model/runtime/template/skill hash in `protocol.json`.
2. Retrieve the pinned capsule archive and verify its SHA-256 before extracting.
   Stage only `code/R/Design_analysis_r.R`, `code/README.md` and `code/LICENSE`
   as `source/`. Preserve original bytes and attribution. Do not stage `Data`,
   knitr caches, `.Rhistory`, paper TeX/PDF or `results/`.
3. Prepare the recorded R/MASS/docstring versions. The original capsule uses
   R4.1.0/MASS7.3-51.6; this is an explicit R4.4.2/MASS7.3.61 portability
   adaptation, not a claim of reproducing its historical environment.
4. Independently run `reference.R` against the unchanged source and scenarios
   before the agent calls. Keep its outputs outside both author workspaces.
5. Configure Kimi's only model/provider as local Qwen at the loopback endpoint.
   Disable telemetry; apply the common tool list, context and native retry
   settings in the protocol. Validate with native `kimi doctor config`.
6. Place task/scenarios/source in separate projects. Use isolated `HOME` and
   `KIMI_CODE_HOME`, with no inherited model credentials. Invoke `kimi --prompt`
   using the exact arm prompt, `--output-format stream-json` and `--skills-dir`
   pointing to an empty directory or the exact frozen skill package.
7. Retain stdout, stderr, native sessions, process status, server provenance,
   source and final artifact hashes. Apply the declared timeout to the complete
   native process group. Do not start a second draw in response to its outcome.

Prepared native R must actually inherit the designated libraries. This machine's
existing user `Rscript` wrapper overwrites `R_LIBS_USER`; the pilot instead uses
the actual R-framework executable with its existing `R_HOME` and `RHOME` and
puts that bin directory first on PATH. No author statistical code was patched.

## Independent Check

Compare the final CSV and one fresh execution of the exact generated
`reproduce.R` against the preregistered reference at absolute tolerance `1e-12`.
Require the six exact IDs, declared columns, finite values and an unchanged
reference-source hash. Inspect retained native execution observations as well:
reading or copying an old file is not fresh computation. Missing artifacts,
failed executions and timeouts remain outcomes.

Numerical agreement only establishes replication of the supplied code in this
environment. Archive the Markdown report for later mathematical review; do not
award theory correctness, novelty, independent review or Lean closure through
self-report. File/source restrictions in this local native-host pilot are
declared, not an OS-enforced adversarial blinding boundary.

Run artifacts are retained in `runs/open_weight_host_pilot_20261001/` locally.
They are not an activated main-study dataset. This development family is excluded
from the prospective publication test split.

## Observed Outcome

The sole frozen assessment is preserved byte-for-byte in `observed_results.json`
(SHA-256 `8acd2ad542154e0fc8ab17c107fe8e73d0758e7b43630a18a0b025529c807e2b`).
Both draws ended before the wall limit, but neither wrote `results.csv` and both
exact final scripts failed their one fresh execution with an undefined author
function. The operator did not edit or resume either output.

| Condition | Native model calls | Source unchanged | Fresh script exit | Numeric replication |
| --- | ---: | --- | ---: | --- |
| Bare | 21 | No | 1 | Failed |
| Skill offered | 38, including one compaction | Yes | 1 | Failed |

The bare agent rewrote part of the author's function despite the unchanged-source
requirement. The skill-offered agent also created a second script in `source/`;
its required root script remained broken. Both generated reports are unreviewed.
Host exit code zero and assertions of completion are not scientific acceptance.

Crucially, the skill appeared in the treatment's native listing but the headless
`--prompt` preserved `/skill:statistical-research` as literal text. Its trace has
neither a `Skill` invocation nor a read of `SKILL.md`; no body-consumption evidence
exists. This is an intervention-uptake failure, not a valid efficacy comparison.
Do not discard it, call it a successful treatment or start another draw here.

After consumption, an independent transport-only test verified that the installed
host's ACP `session/prompt` activation does expand the entire skill into the
model request. Its response came from a fixed mock endpoint, with no live model
or scientific task. This corrects future invocation knowledge; it does not alter
this frozen protocol or either failed result. No topic-specific instruction,
statistical source patch, extra repair agent or fallback was added.

The retained native usage includes all loop and compaction calls: bare 402,070
input tokens including 377,600 cache-read tokens, 4,331 output; skill-offered
720,638 input including 667,267 cache-read, 4,341 output. Native caching is reported
separately, not hidden by counting only uncached input. Ordered resident-server
draws do not support a speedup claim. Raw native records and exact artifact hashes
remain at the local run path; the assessment alone is not a public trajectory
release or main-study dataset. The owned model server was stopped afterward.
