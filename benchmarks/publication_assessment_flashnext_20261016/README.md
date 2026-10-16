# Fixed Flash-Next Assessment Preparation

This is a new model-condition preparation, not a retry of the consumed 4B
assessor or either current 27B research arm. No assessor or official publication
draw is activated by downloading weights. The consumed 27B statistical arm keeps
its original model, code, inputs and resource envelope.

The selected candidate is `Qwen/Qwen3.8-Flash-Next`, revision
`de4b8e4d43b917e7706784d8bb445c9af86a3540`, in BF16. Its 131 weight files total
360,000,192,888 bytes. Active parameters do not determine resident memory.
The [actual license](https://huggingface.co/Qwen/Qwen3.8-Flash-Next/blob/de4b8e4d43b917e7706784d8bb445c9af86a3540/LICENSE)
is Qwen Community License 1.0, not Apache-2.0 or an unrestricted open-source
claim. Keep its notices and restrictions separate from our harness license;
this preparation does not redistribute weights or resolve release rights.

`stage_weights.sh` reuses the existing serial Hugging Face 1.31.0 downloader
and full size/LFS-hash verification from `prepare_qwen27b.sh`, using the existing
client environment rather than installing another copy. It selects the new
repository/revision and creates a new owned directory and receipt,
uses no GPU, runs no model, and cannot overwrite a completed receipt. There is
no download manager, model fallback or new agent controller.

The declared CPU allocation and source hashes are in
[weight_staging_plan.json](weight_staging_plan.json). Submission and actual
verification remain separate evidence. The proposed later four-B200 BF16 shape
is a feasibility estimate, not allocated capacity or measured serving fit.
Any inference condition still needs pinned runtime/configuration and an actual
assessment design before model calls. Reuse the native retained file/review
components, not the legacy research scheduler or a new referee framework.

The scientific requirement is assessment of complete source-bound arguments,
including valid alternatives, false assertions and honest unresolved steps,
against separately prepared source-grounded reference reasoning. Agreement of
labels, execution, numerical checks and model confidence are not proof. The
current native product reviewer and the common external publication endpoint
are distinct authorities; qualifying one does not silently qualify the other.

The prospective [native-review protocol](assessment_protocol.md) now fixes five
source-grounded argument controls, isolated contexts, complete-panel execution
and a separate examination of decisive reasons. `qualify.py` directly reuses the
current read-only Markdown reviewer; `run_assessment.sh` uses the existing pinned
runtime and deployment probe. These files are preparation, not inference or a
qualified assessor. The old consumed 4B condition is unchanged. No repeated
candidate-mode positive is added because this native workspace has no such mode.

[Weight staging completed](weight_staging_observation.json) with all 144 file
identities verified. The frozen [assessment job 29735341](submission.json) is
submitted under `pi_fl426`, with four B200s, 32 CPUs, 1 TiB host memory and
48 hours, after successful staging. It is pending allocation; there is no
observed serving fit, completed panel or scientific qualification yet.
