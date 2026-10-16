# Local Qwen Testing

The operator's 2026-10-01 decision replaces Anthropic for future model tests.
The application defaults to `local`: standard loopback Chat Completions/native
function calling, with the existing retained loop executing tools. No Claude Code
dependency, Qwen grammar parser, content repair or cloud fallback is introduced.

On 2026-10-15 the operator also authorized larger open-weight Qwen deployments
and long complete-system runs on Bouchet. The 4B records below remain historical
development conditions, not a limit on future model capacity. Freeze and verify
each new deployment before scientific calls; do not silently change an active run.

## Bouchet Availability, 2026-10-15

Verified through BatchMode SSH, installed module metadata, and an actual compute
allocation, not inferred from a model name. Standard `day` job **29681055** ran
the official `local-coding-agents/1.1` launcher under `pi_fl426`: two CPUs, 4 GiB,
12 seconds, `COMPLETED`, exit `0:0`, no GPUs and no inference. Pi **0.85.1** lists
`bouchet/ycrc-local` and `bouchet/ycrc-local-think`; both declare 262000 context
tokens and 16384 output tokens. The second invocation confirms the extended-mode
alias selected by `YCRC_THINKING=1`. The raw record is
`runs/bouchet_model_inventory_20261015/inspection-29681055.log`.

[YCRC documents](https://docs.ycrc.yale.edu/ai/local-coding-agents/) these as modes
of its hosted Qwen3.8-Flash-Next, shared by Pi, Codex, Copilot and Claude interfaces.
Four interfaces are not four models, and Claude here is not Anthropic inference.
The CLI lists `thinking=no` for both aliases; alias selection alone does not prove
effective backend reasoning settings. Weight revision, quantization, server
runtime, request sampling, throughput and inference health are not verified by
this inventory. Noninteractive launches warn about `/dev/tty` and unavailable
GitHub SSH identity but complete; no credentials or launcher controls were changed.

No second managed model was found in the inspected configuration. Ollama 0.22.0,
PyTorch 2.9.1 and Transformers 4.55.2 modules exist, but are not model deployments
or proof of compatibility with current architectures. Bouchet has no `llms`
module or `/apps/large_language_models` at the checked paths; that offline cache
is documented for [Hopper](https://docs.ycrc.yale.edu/clusters/hopper/#llm-models),
not established for this account on Bouchet. That inventory downloaded no weights;
the subsequent task-owned staging is recorded below.

The source-verified shortlist below is a deployment recommendation, not a model
ranking, scientific performance result or claim that Yale already hosts every row:

| Candidate | Actual availability and intended use |
| --- | --- |
| [Qwen3.8-Flash-Next](https://huggingface.co/Qwen/Qwen3.8-Flash-Next) | Actual returned model in the new Pi authoring condition, not only a launcher alias. Shared weights/configuration remain unpinned. |
| [Qwen3.8-27B](https://huggingface.co/Qwen/Qwen3.8-27B) | Task-owned, exact BF16 deployment passed native schema and retained tool/error feedback in job 29722100. One B200, native configured context 262144; long-context quality and statistical capability are not yet established. |
| [Qwen3-Coder-Next](https://huggingface.co/Qwen/Qwen3-Coder-Next) | Public 80B-total/3B-active coding model; useful coding-agent comparator. Non-thinking-only, so not presumed superior for mathematical theory. Not installed or called here. |
| [Qwen3.5-122B-A10B](https://huggingface.co/Qwen/Qwen3.5-122B-A10B) | Larger open-weight reasoning/tool-use candidate, not an observed Yale service or a demonstrated improvement over the newer 27B. BF16 weights alone are approximately 244 GB; two B200s are a feasibility estimate, not measured context/runtime fit. Not staged or called. |
| [Qwen3.5-397B-A17B](https://huggingface.co/Qwen/Qwen3.5-397B-A17B) | Larger comparison candidate. The official card supplies eight-GPU serving/tool-use commands; BF16 weights alone are approximately 794 GB. An eight-H200/B200 allocation is a deployment candidate, not an allocated service or statistical result. Not staged or called. |
| [DeepSeek-V4-Flash](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash) | Public 284B-total/13B-active model; possible later cross-family comparison, not an observed Yale service or selected Qwen-only study condition. No deployment or calls. |

The October 16 recheck also confirms official open weights for
[Qwen3.8-2.4T-A95B](https://huggingface.co/Qwen/Qwen3.8-2.4T-A95B), with a
model-specific license, not Apache-2.0. BF16 weights alone would require about
4.8 TB, exceeding one Bouchet eight-GPU node before cache/runtime overhead.
It is not the immediate deployment choice. Flash-Next's official card instead
lists 125B parameters/6B active plus 51B n-gram embeddings and 4B MTP; active
parameter count is not resident-weight memory. A pinned self-hosted Flash-Next is
also a possible larger-model condition, but cannot be assumed identical to Yale's
managed revision. No additional model is downloaded or substituted during the
current paired condition. Model capacity comparisons require complete matched
tasks, not parameter-count rankings or a succession of toy tests.

The [current Bouchet inventory](https://docs.ycrc.yale.edu/clusters/bouchet/)
includes B200 nodes with eight 193-GB GPUs as well as H200 nodes with eight
141-GB GPUs. This is schedulable inventory, not free/allocated capacity; actual
permissions, queue estimates and fit must be checked for the selected condition.

For Paper H, use the same actual managed host/model condition for bare and
statistical-skill arms, recording effective access and any service changes.
Sakana's pinned host now reaches real Pi model/file tools through Yale's wrapper;
that alone does not verify scientific skill benefit. For Paper S, a CLI launch is not the required single-API system:
verify a supported direct API and exact deployment or use a task-owned pinned
Qwen service. Do not extract credentials or bypass managed-client restrictions.
Match the model across each harness contrast rather than confound model upgrades
with architectural effects. Preserve the old 4B outcomes separately.

[Clarity/Portkey](https://docs.ycrc.yale.edu/ai/clarity/) provide a separate route
to commercial models, not local Bouchet weights; they are not selected for the
open-weight scientific studies. Model-card scores do not establish performance
on statistical derivations, simulations or Lean. Freeze a complete research task
and assess those outputs directly, without a new succession of toy-task gates.

## Larger Consistent Deployment

The October 15 follow-up makes a capable, consistent Bouchet deployment the
preferred route when the research workload needs it, not an exceptional fallback
after a 4B failure. Select the model before a new comparison and keep it fixed
across arms. There is no need for repeated operator approval of ordinary bounded
standard-tier work. A larger model does not fix a broken launch or certify theory.

The prospective first task-owned model is `Qwen/Qwen3.8-27B`, revision
`1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0`. The public Hugging Face metadata lists
18 BF16 weight shards totaling 55,563,006,776 bytes (about 51.75 GiB), Apache-2.0
licensing and no access gate. Its native context is 262144 tokens. These are
source-verified properties. Metadata is retained at
`runs/bouchet_model_inventory_20261015/qwen38_27b_metadata.json`.
This is larger than our historical 4B baseline, not a claim that it outperforms
Yale's managed Flash-Next model. Task results, not parameter count, decide that.

Use the [upstream vLLM recipe](https://recipes.vllm.ai/Qwen/Qwen3.8-27B), including
its supported reasoning and tool-call parsers, rather than adding model syntax
handling to AI-Statistician. The installed Yale Transformers 4.55.2 module is not
the recipe's Transformers 5.8+ environment. Pin a compatible runtime and its full
resolved dependencies before serving; do not blindly install `latest` or assume
PyPI availability implies driver compatibility. The qualified startup and API
transport, and their narrower evidence scope, are recorded below.

The initial resource shape is one H200 with BF16 weights, native context and
single-request concurrency. This is a feasibility estimate, not measured fit:
weights, attention cache, recurrent state, activations and runtime all consume
memory. Measure actual startup/context capacity, tool round trips and throughput
before a complete research run. Scale GPU count or choose another documented
precision as a new fixed condition when measured needs require it; do not shrink
the scientific task. Reasoning effort and output/time limits belong to that
condition, not an automatic per-failure escalation policy.

Fresh SSH checks found both authorized account associations, H200 and B200
partitions, no user GPU job, and substantial `pi_fl426` project/scratch quota
headroom. The quota tool's report is dated midnight, not live byte accounting.
Cluster inventory is not idle capacity; request through Slurm. Use task-owned
storage, a bounded compute-node loopback API and the existing authenticated SSH
route. No GPU job, large weight download or inference was started by that inventory.

Subsequent staging used the exact revision and upstream Hugging Face downloader,
not a new model-management framework. Job **29684890** exhausted its 12-GiB host
memory allocation during concurrent downloads. Job **29685132** used the same
revision/client with the upstream `--max-workers 1` option and 40 GiB host memory;
it completed in 591 seconds. All 32 files have recorded sizes and SHA-256 hashes,
and every LFS object matches the source metadata. The receipt is
`runs/bouchet_model_inventory_20261015/verified-model-files.json`, SHA-256
`3b138394437dc1c4959330965db95b40c7c1400d0b9479c5105cd96f03d50dfd`.
The task storage occupies 65 GiB. Both attempts used zero GPUs and made no model
requests; retain the failed attempt as well as the successful staging.

Upstream vLLM **0.31.0** has a resolved, hash-locked 199-package Linux/Python 3.12
environment (lock SHA-256
`77df8a4c761d31626671a829ed344985eeeb3935ad1a75e3bc7fcd0e16dff2f1`).
Runtime-install job **29685758** completed in 1,009 seconds with exit `0:0`,
two CPUs, 24 GiB and no GPU. All 199 installed packages pass `uv pip check`;
the complete runtime freeze is retained. Task storage occupies 73 GiB.
The freeze SHA-256 is `7601c963977f3d69b05dbbe64cc21344afd5f2dd024aa46df8f60a8f48fb8d1f`;
the terminal log SHA-256 is `8d9bc33b5dbdd2eef2eb6b5f222d67a762cf5b9e60303c1da95dac5d12685d48`.
The preparation scripts are under
`integrations/agentic-scientist/bouchet/`; exact locks, logs and job receipts remain
in task storage and `runs/bouchet_model_inventory_20261015/`.
CUDA initialization subsequently succeeded on B200. Actual model memory/context
fit, tool round trips and throughput remain unverified. Installed software is not
a deployed service.

The [frozen deployment probe](../integrations/agentic-scientist/bouchet/qwen27b_probe_precall.json)
was submitted once as job **29687651**, account `pi_fl426`, standard `gpu_b200`,
one B200, eight CPUs, 128 GiB and one hour. Before allocation, the same job moved
to standard `gpu_devel` with unchanged resources/model under the recorded
[scheduler amendment](../integrations/agentic-scientist/bouchet/qwen27b_probe_partition_amendment_20261015.json).
Before submission both authorized accounts gave earlier B200 estimates than
H200; this is a prospective hardware choice, not a model or precision fallback.
It preserves BF16, native 262144 context, one-request concurrency and upstream
reasoning/tool parsers. The pinned chat template defaults to thinking with
`xhigh` effort; actual runtime behavior still requires observation. Temperature
1.0, top-p 0.95 and top-k 20 come from the pinned generation configuration.

The probe reuses `LocalChatGeneratorBackend` and the retained tool loop from
product commit `3301dff9`, with no old outer graph or coding CLI. It checks one
native schema response and exact raw failed-tool feedback, allowing 8192 output
tokens per request. This is transport conformance, not scientific evaluation or
long-context capacity/quality evidence. The loopback service stops at completion
or failure; there is no automatic retry, cloud call or context/precision change.

**Terminal first deployment, October 15:** job 29687651 ran on `a1117u29n01`
for 44m26s and failed with exit `1:0`. B200 driver 580.178.04 and PyTorch
2.13.0+cu130/CUDA 13.0 initialized successfully. Repeated process observations
showed filesystem waits and little CPU time during imports. vLLM's first banner
appeared about 24 minutes after allocation, followed by front-end/engine handshake
timeouts. No API request ran. This supports addressing shared-file import latency;
it does not establish GPU-memory insufficiency or a model-capacity failure.
The preserved `probe-29687651/server.log` SHA-256 is
`161abe4977c7325988cc0b0988ee72a38aa672c04f0151c632bcea920f8f9379`
under `runs/bouchet_model_inventory_20261015/`.

The October 16 correction archived the unchanged 7.8-GiB installed environment
once in CPU job **29719771**, completed in 522 seconds with exit `0:0`. The
[new frozen condition](../integrations/agentic-scientist/bouchet/qwen27b_node_local_precall_20261016.json)
extracts that verified archive to task-owned
node-local temporary storage for a fresh GPU probe. Weights, precision, context,
sampling, parsers, product commit and probe questions stay fixed. The previous
script and failed run remain preserved remotely; future script invocation requires
the exact archive hash. No startup timeout was relaxed and no commercial model
or managed-service credential was substituted. The new condition's allocation and
outcome must be recorded before calling it available. Job **29720252** was submitted
once at `2026-10-16T01:49:33-04:00`, account `pi_fl426`, normal `gpu_devel`,
one B200/eight CPUs/128 GiB/one hour. It failed after 92 seconds. The vLLM
banner appeared within 19 seconds of allocation; weights loaded in 18.56 seconds,
using 50.22 GiB. Compilation then failed because `nvcc` was unavailable. This
resolves the earlier import-latency diagnosis but does not establish API readiness.
The preserved server log SHA-256 is
`3a068f9607d984cefd85a86afbb2d6101eacdacfa05e7d6f4e21895f550086e2`.

The [compiler condition](../integrations/agentic-scientist/bouchet/qwen27b_nvcc_precall_20261016.json)
loaded Yale's existing `CUDA/12.9.1` module. Job **29721459** failed after 72
seconds because `ninja`, already installed in the unchanged environment, was not
on `PATH`. No request reached the model. Its server log SHA-256 is
`ab76846827115caa66d687444f60550d68e3c3dac1239697b24bca2c64ff4d6a`.
This is a launcher omission, not a numerical or model-capacity result.

The [activation correction](../integrations/agentic-scientist/bouchet/qwen27b_path_precall_20261016.json)
prepends the extracted environment's bin directory to `PATH` and records compiler,
`nvcc` and `ninja` versions before serving. Actual no-inference checks found ninja
1.13.2 and GCC 13.3.0 and loaded the frozen product probe's CLI successfully.
Job **29722100**, the same one-B200/128-GiB/one-hour standard allocation shape,
completed in 3m08s with exit `0:0`. The actual API returned
`Qwen3.8-27B-pinned`, passed the native structured response and two retained tool
turns, and returned the exact opaque failed-tool observation. This establishes
startup/compiler interoperability and transport, not statistical correctness or
long-context quality. Weights, BF16, configured 262144 context, runtime archive,
parsers and sampling remained fixed. Raw records are in
`runs/bouchet_model_inventory_20261015/probe-29722100/`. The owned service stopped
when the job completed; this is not an always-running endpoint.

The separate native workflow preparation now includes a fresh hash-locked worker
environment in CPU job **29722329**, outside the earlier Pi environments. It
completed in 9m48s with exit `0:0`; all 83 installed packages pass `uv pip check`.
Its archive SHA-256 is
`5752b5f1e842bd89d5370a42cd4b4df123fb276c348dbdd72553c85d6342eaa6`.
It supports the [continuous investigation/report condition](../benchmarks/agentic_scientist_native_hc0_20261016/README.md)
after a prospective code/input/configuration freeze. Environment installation
does not activate a scientific draw or official publication model comparison.

## Native State And Complete-Workflow Observation, October 16

The [native 27B condition](../benchmarks/agentic_scientist_native_hc0_20261016/analysis.md)
is terminal. Both arms stopped at the 32768-output limit in ideation, without
scientific source, evaluation or simulation. No HTTP timeout or tool-permission
failure caused those recorded stops. This does not measure theorem correctness
or establish a model-capacity ceiling.

Installed [vLLM 0.31.0](https://github.com/vllm-project/vllm/blob/v0.31.0/vllm/entrypoints/openai/chat_completion/protocol.py)
returns native `reasoning`, with `reasoning_content` as an older alias. The
frozen adapter discarded both before subsequent requests. The prospective fix
preserves each returned field as opaque assistant state, including through
session storage; it introduces no reasoning-text parser or statistical rule.
Private state is not a mathematical deliverable or an external review input.
The earlier short transport probe did not test this preservation path.

The [pinned model card](https://huggingface.co/Qwen/Qwen3.8-27B/blob/1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0/README.md)
also distinguishes its coding-benchmark output allowance from larger long-agent
budgets under extended context. Future complete-workflow conditions must qualify
state continuity and coherent context/output/stage timing before calls. Do not
change the consumed 262144-context condition or silently claim that an extended
context is already deployed. No new service remained after job 29722963.

The [fresh long-workflow condition](../benchmarks/agentic_scientist_native_hc0_long_20261016/README.md)
reuses these exact BF16 weights and locked runtimes, not another model download
or manager. It prospectively declares static YaRN factor 4/1M context, 393216
combined output, four-hour requests and a separate 48-hour B200 allocation for
each arm. The card's reasoning/final recommendations are not separate enforced
caps in this API. Static scaling can affect shorter contexts; startup is not
quality qualification. Both arms and all roles must keep the same settings.
The existing full study and scientific requirements are unchanged; no automatic
fallback, reduced task or retroactive rerun is permitted.
The [first live prefix](../benchmarks/agentic_scientist_native_hc0_long_20261016/runtime_observation.json)
now confirms the configured 1M endpoint started on B200 and preserves fourteen
native assistant-state blocks across returned ideation turns. No completed idea
or scientific study exists in that prefix; startup is not long-context quality.
The [subsequent stage observation](../benchmarks/agentic_scientist_native_hc0_long_20261016/authoring_observation.json)
records stock ideation completing in 6m07s and the same fixed model entering
source authoring. The authoring prefix is still in flight; no evaluation,
mathematical acceptance or completed study is established. Both original prefix
snapshots and the pending statistical arm remain unchanged.

## Latest Managed-Host Observation

The [full-study module condition](../benchmarks/agentic_scientist_hc0_bouchet_20261015/README.md)
prepared two matched instructions and a 12-cell, 5000-dataset-per-cell evaluator.
Both launches failed before the managed Pi client because the operator chose a
long NFS temporary path; the SSH socket path and upstream private log spool could
not be created. There is no model-capacity or scientific result. Original scripts
and records remain immutable. A separate zero-inference job **29683607** completed
with short node-local `/tmp`, exercising the actual launcher, logger and CLI.
The future runner uses that configuration; no consumed candidate was rerun.

The separately frozen short-temp condition has now returned
`responseModel=Qwen3.8-Flash-Next` and actual file/tool activity. Stock job
**29684591** authored a candidate and completed the 60,000-replicate evaluator,
but passed zero implementation-reference checks. Its source contains an extra
sample-size division in the covariance; it was not manually fixed or reexecuted.
Theory remains unassessed. See the
[terminal stock record](../benchmarks/agentic_scientist_hc0_bouchet_20261015/short_tmp_stock_observation.json).
Statistical job **29684597** completed all 60,000 numerical checks successfully,
but the author read the exposed evaluator and ran prohibited extra diagnostics.
Its host rubric remained false because our preparer emitted unsupported nested
metric fields. The future format is fixed; consumed outcomes are not rescored.
See the [terminal analysis](../benchmarks/agentic_scientist_hc0_bouchet_20261015/short_tmp_analysis.md).
Theory is unassessed, and the final report was not produced from the actual
post-evaluation outputs. The separate weight transfer overlapped that arm,
another reason not to interpret wall-time differences causally. Neither these
managed-host draws nor the 27B preparation establish Paper S's single-API system
or an official publication result.

## Transport Conformance

Use existing compatible llama.cpp/model files at operator-selected paths; do not
modify another project's frozen deployment. The verified server configuration was:

```sh
"$LLAMA_SERVER" --model "$QWEN_GGUF" --alias Qwen3-4B-Instruct-2507 \
  --host 127.0.0.1 --port 8081 --ctx-size 32768 --parallel 1 --jinja \
  --threads 4 --n-gpu-layers 99 --flash-attn on \
  --cache-type-k q8_0 --cache-type-v q8_0 --no-warmup --no-context-shift
```

The observed macOS binary needed its existing library directory in
`DYLD_LIBRARY_PATH`; other builds may not. Stop the owned test server after use.
This temporary loopback test is not a production-service hardening claim.

```sh
export AI_STATISTICIAN_LOCAL_BASE_URL=http://127.0.0.1:8081/v1
export AI_STATISTICIAN_LOCAL_MODEL=Qwen3-4B-Instruct-2507
AI_STATISTICIAN_LOCAL_MODEL_CONFORMANCE=1 .venv/bin/pytest -q -s \
  tests/test_local_model_backend.py::test_live_local_schema_and_retained_raw_observation
```

The fixture checks native JSON schema, tool identity and exact failed-tool feedback
in the same session. It is not a scientific evaluation; normal unit tests do not
call a model. It never interprets text as tool syntax or corrects model content.

## Observed Deployment

Verified after the interrupted process ended on 2026-10-01:

| Item | Exact observed value |
| --- | --- |
| Model | `Qwen3-4B-Instruct-2507`, `Q4_K_M` |
| GGUF revision | `unsloth/Qwen3-4B-Instruct-2507-GGUF`, `a06e946bb6b655725eafa393f4a9745d460374c9` |
| Weights SHA-256 | `3605803b982cb64aead44f6c1b2ae36e3acdb41d8e46c8a94c6533bc4c67e597` |
| Runtime | llama.cpp `4fea119`, `0.4.1-dev`, Darwin arm64 |
| Server binary SHA-256 | `f124807ba31de5a65ea22fd624f33fd4dfe3c837d1c014dcf4a516b66812ffd7` |
| Active `/props` chat-template SHA-256 | `c979e0e71a3e21b8f208e6ab120d5cb29327885f29d2a8b18fda67a723798e18` |
| Request sampling | temperature 0; schema max tokens 64, tool max tokens 256; parallel tool use disabled |
| Other server defaults | seed `4294967295` (random sentinel), top-k 40, top-p 0.95, min-p 0.05, typical-p 1, repeat penalty 1; no speculative decoding |
| Sampler order | penalties, dry, top-n-sigma, top-k, typical-p, top-p, min-p, XTC, temperature |
| Result | 1 schema call plus 2 tool turns / 2 tool calls; all 11 local-backend tests passed in 1.77 seconds |
| Retained tool usage | 515 input / 52 output tokens, total 567; excludes the schema call |
| Transcript fingerprint | `1b5c3665625c2424556b68d1f9913e3923195551fc4fd32e1eddd69aac5e2e5c` |

The final run follows a transport correction that preserves `is_error` alongside
the unchanged observation. Both conformance invocations were synthetic mechanism
tests, not statistical task draws or a selected publication score.
This fixture returns the retained messages in memory; passing `session_dir` does
not itself invoke the caller-owned session persister. Its printed workspace path
is not a saved transcript or publication dataset. Record complete prospective
provenance and immutable histories in actual scientific workspaces/runs.
Transport success is not theory, simulation, Lean or research-E2E capability.

## Prospective Publication Conditions

The deployed small quantized checkpoint is a development condition, not the
whole system's scientific capacity ceiling. The [official Qwen model card](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507#best-practices)
describes a non-thinking model with a native 262,144-token context and recommends
temperature 0.7, top-p 0.8, top-k 20, min-p 0 and 16,384 output tokens. The
consumed development pilot instead used a 32k server context, temperature zero
and 4,096 output tokens. These differences are not repaired retrospectively.
Any future decoding/context/model condition must be frozen before its fresh
draws, verified against the actual local runtime and reported separately. Upstream
recommendations alone neither validate a deployment nor establish a fair comparison.
Do not add Qwen-Agent's controller over the retained product loop or automatically
increase resources, change models or retry after a consumed failure.

## Forward Evaluation Binding

New `--research-eval` and capability profiles use explicit `evaluation_provider`,
`evaluation_model` and `evaluation_model_tier` bindings. All live roles, including
Theory, Python/R, Simulation, Lean and independent reviewers, use local Qwen;
cloud selections fail before inference. The local server must report the requested
model identity. A local error never falls back to Anthropic or another model.

The development default remains `Qwen3-4B-Instruct-2507`, not a capacity ceiling.
`--llm-model` selects an explicit local pin for the normal runtime CLI;
publication draw configurations declare it in the deployment, role and runtime
fields. Unspecified role models inherit the chosen CLI pin, while conflicting
explicit role models fail instead of being silently overwritten. The four draw
modes preserve the declared model in their frozen configuration and native
requests. Alternate model IDs are covered by mocked transport tests only: no new
weights were deployed or called. An ID match does not attest weights, template,
sampling, resource parity or scientific capacity; those still require the
prospective deployment checks. Do not select a stronger model after an outcome
or automatically expand a run's resources.

Hidden-gold schema 5 retains its original exact 4B evaluator policy.
Semantic protocols 26/27 hash the actual requested model and native tool contract,
and validate retained turn identity. Prior Haiku authority is readable for archival
inspection and offline fixtures, not reusable qualification. Fresh scientific
authority still needs prospective deployment/task/rubric pins and independent
calibration. Allowing an explicit researcher-model pin does not widen a frozen
evaluator's qualification or alter any consumed result. This change does not
activate or qualify a scientific benchmark.

After this migration the same weights, binary and active chat-template hashes
were rechecked. The opt-in local suite passed 24 tests in 2.09 seconds, including
one schema call and two native tool turns. Tool-session usage was 515 input and
52 output tokens; the in-memory transcript fingerprint was
`350f9dca1d8cf924478ba201af413810af239f5d934b0281b318ac704173511e`.
The owned server was stopped after testing. No Anthropic inference was performed.

## Whole-Task Resource Accounting

The existing `AgentRuntime` records local transport requests across its planner,
source owners, reviewers and workspace continuations in `local_model_usage`.
Each question has its own scope; an explicit new runtime invocation starts a new
scope. Calls outside that graph, such as independent gold evaluation or a native
coding host's private transport, are not included. The current graph is serial;
this is not a concurrent resource allocator.

`research-agent-runtime --local-model-call-limit N` optionally stops before an
additional local request after N attempts. The default is no additional limit.
HTTP failures consume attempts, and Architect routing cannot reset the counter.
Exhaustion preserves source, retained observations and the exact pending task;
it does not restart or repair a consumed evaluation. Completion on the last
allowed call remains valid. This is a request cap, not a token or wall-time cap.

Usage records retain reported input/output/total tokens and cached-input tokens,
numeric server timings and transport elapsed time. Missing usage remains unknown,
not zero. Cache reads are a subset of input, not extra tokens to add to the total.
See the pinned [llama.cpp server API](https://github.com/ggml-org/llama.cpp/blob/4fea119/tools/server/README.md)
for the response fields. Equal request counts alone do not establish equal cost.
Mocked mechanism tests verify scope, failures and retained state; they are not
model inference or scientific capability evidence.

Official publication studies start fresh with open-weight models. Historical
Haiku development outcomes are not comparison arms or main results. Local Claude
Code compatibility/user-workflow testing is a separately authorized host check;
the installed version was observed as 2.1.168, but no new Claude model turn or
skill-discovery conformance was run in this migration.

## Single-Context Control Probe

The research-control submission path at `0b83e790`, before its later
resource-selective join refinement, was checked with the same deployed
weights, binary and active template hashes above. The temporary server used seed
`20261001`; native requests used temperature 0, max tokens 1024, no thinking budget
and disabled parallel tool use. The synthetic fixture had an eight-turn/eight-action
envelope and no statistical question or hidden gold.

```sh
AI_STATISTICIAN_LOCAL_MODEL_CONFORMANCE=1 .venv/bin/pytest -q -s \
  tests/test_research_control.py::test_live_local_control_selects_its_actual_checkpoint_and_writes_a_report
```

One probe passed in 17.90 seconds: two model turns, four tool calls, 9315 input
and 392 output tokens, including 4350 cached-input tokens (not additional tokens).
The in-memory transcript fingerprint was
`6dc7e46c1a2f6caa6acd9e242f9fcf70f5377a742a12ea5aff46d2993f2aef04`.
Unlike the earlier bare-loop fixture, this control persisted its joint session,
exact observations/checkpoint payloads and unchanged model-authored Markdown
report. Local records are in `runs/publication_research_control_20261001`, including
a source/deployment protocol frozen before inference and native test JUnit.
This is transport/submission conformance, not a scientific draw or publication
dataset. The owned server was terminated afterwards and port 8081 was closed.
No Anthropic or Claude Code inference occurred.
The subsequent join refinement is covered by deterministic tests with real
Python/R execution, not by reinterpreting or rerunning this consumed probe.
