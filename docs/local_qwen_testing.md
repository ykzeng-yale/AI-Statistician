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

## Remaining Migration

Role factories can construct the local backend, including the independent
Architect preflight reviewer, now selected by native-tool capability rather than
an Anthropic-name condition. Legacy `--research-eval`, strict capability profiles
and hidden authority still contain exact-Haiku contracts. Do not use them as Qwen
benchmarks, call Anthropic as a workaround or relabel historical judgments.

New provider-neutral authority must prospectively bind the exact Qwen deployment,
task/rubric identity, retained observations and independent calibration. This is
not permission to bypass review or introduce another scheduler. Qualification and
comparative scientific experiments remain unfinished.
