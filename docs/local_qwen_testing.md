# Local Qwen Testing

The operator's 2026-10-01 decision replaces Anthropic for future model tests.
The application defaults to `local`: standard loopback Chat Completions/native
function calling, with the existing retained loop executing tools. No Claude Code
dependency, Qwen grammar parser, content repair or cloud fallback is introduced.

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

## Forward Evaluation Binding

New `--research-eval` and capability profiles use explicit `evaluation_provider`,
`evaluation_model` and `evaluation_model_tier` bindings. All live roles, including
Theory, Python/R, Simulation, Lean and independent reviewers, use local Qwen;
cloud selections fail before inference. The local server must report the requested
model identity. A local error never falls back to Anthropic or another model.

Hidden-gold schema 5 binds its reviewer to the same frozen provider/model policy.
Semantic protocols 26/27 hash the actual requested model and native tool contract,
and validate retained turn identity. Prior Haiku authority is readable for archival
inspection and offline fixtures, not reusable qualification. Fresh scientific
authority still needs prospective deployment/task/rubric pins and independent
calibration. This change does not activate or qualify a scientific benchmark.

After this migration the same weights, binary and active chat-template hashes
were rechecked. The opt-in local suite passed 24 tests in 2.09 seconds, including
one schema call and two native tool turns. Tool-session usage was 515 input and
52 output tokens; the in-memory transcript fingerprint was
`350f9dca1d8cf924478ba201af413810af239f5d934b0281b318ac704173511e`.
The owned server was stopped after testing. No Anthropic inference was performed.

Official publication studies start fresh with open-weight models. Historical
Haiku development outcomes are not comparison arms or main results. Local Claude
Code compatibility/user-workflow testing is a separately authorized host check;
the installed version was observed as 2.1.168, but no new Claude model turn or
skill-discovery conformance was run in this migration.
