# Native Kimi ACP And Local Qwen Conformance

One fresh installation/activation probe, frozen at `42f16f64`, before inference.
The cached `@moonshot-ai/kimi-code@2.1.1` was installed offline into an exclusive
test directory. Its executable, the existing Qwen weights/runtime/template and
all three skill files matched their recorded hashes. The newer documented
`auto_session_title` key was ignored by this pinned v2 engine and removed before
the first call; no live configuration was repaired or restarted.

The native ACP surface discovered the project skill, loaded its exact 2,994-character
body into model context, and completed one `Read` of `probe.txt`. The final reply
contained the exact receipt and correctly said no independent scientific review
or Lean proof was requested. Two local-Qwen loop requests reported 22,172 input
tokens (11,043 cached) and 71 output tokens in 27.60 seconds. No auxiliary request
was observed. There is no bare-host comparison or scientific outcome here.

The operator started the pinned loopback server using the declared settings and
verified `/props`, `/v1/models`, weights, executable and active template before
calling the frozen runner. The runner uses native ACP, not a copied host agent,
inference proxy or product scheduler. It refuses an existing output directory,
retains all notifications and terminates its owned host process group. The
operator separately stopped the owned model server and verified both PIDs and
port 8081 absent. Protocol and source are retained alongside the
[first outcome](observed_results.json); raw native records remain locally under
`runs/publication_host_activation_20261002` with their public hashes.

For a separately authorized future compatibility check, verify the exact pins
and start the declared server before invoking:

```sh
.venv/bin/python benchmarks/publication_host_conformance/kimi_acp_qwen_20261002/run_native_activation.py \
  --host "$KIMI_BIN" --skill skills/statistical-research --out "$FRESH_OUTPUT"
```

Never resume or overwrite `probe_1`. This probe establishes native body uptake
and a local file read, not reference-tool breadth, scientific capability,
researcher usability, adversarial isolation or either publication's efficacy.
The old failed R pilot remains unchanged. Both official studies remain unactivated.
