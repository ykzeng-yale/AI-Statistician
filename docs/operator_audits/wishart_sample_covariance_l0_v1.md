# Task111 Operator Audit: Wishart Sample Covariance

Date: 2026-08-30

## Immutable Evaluation Boundary

Task111 is the sole consumed exact-Haiku draw for
`multivariate_normal_sample_covariance_wishart_known_result`. The visible question
was frozen at commit `c0b926ab`; hidden authority was qualified and the public
preactivation ledger was pushed at `d0721678` before the first product-model call.

The product run, its five committed theory packets, five independent review reports,
terminal recovery snapshot, one post-runtime hidden assessment, and every output are
immutable. They must never be rerun, resumed, repaired, reevaluated, rescored,
resampled, manually patched, exposed to a source owner, or model-escalated. This audit
does not feed observations back into the consumed runtime.

## Result

- Runtime status: `BLOCKED` after 12 outer iterations. The terminal subsystem was
  TheoryDeveloper with classification `theory_developer_packet_validation_failed`.
- Full hidden task: failed, 0/1. No candidate qualified for hidden execution.
- Trusted capability credit: 0/1; aggregate becomes 7/111.
- Formalization: not applicable; Formalizer correctly did not run.
- Product model: `claude-haiku-4-5-20251001` only. No Sonnet or Opus call ran.
- Product calls: 164 total, comprising one Architect proposal call and 163 retained
  client-tool turns. TheoryDeveloper used 81 turns and the isolated referee used 82.
- Tools: 173 executions with 20 raw errors. Fourteen of nineteen exact document-edit
  calls returned errors to TheoryDeveloper.
- Hidden assessment: one invocation, zero candidate evaluations, zero model calls,
  no expected value disclosure, and no runtime feedback.

## What Worked

The canonical harness exercised real persistent mathematical work rather than a JSON
answer or a task-specific repair path:

- TheoryDeveloper used one durable Markdown/LaTeX workspace across six visits, wrote
  substantive derivations and a separate estimator handoff, ran model-authored
  scratch calculations, inspected exact ranges, and committed five hash-bound packets.
- Five independent referee sessions inspected exact checkpoint files in clean
  contexts and wrote persisted Markdown reports.
- Runtime preserved every finding, report, source hash, task handoff, and failed tool
  observation without editing mathematics or generating a replacement proof.
- The latest reviewed packet had a 359-line, 15,694-byte theory document and a
  209-line, 10,420-byte estimator document.
- The final recovery snapshot expanded the theory document to 381 lines and 18,598
  bytes. It is preserved for diagnosis but was not committed as a new Theory packet,
  independently reviewed, or accepted, so it receives no capability credit.
- Research-eval mode remained conformant, formalization remained not applicable, and
  the hidden gate correctly declined to execute without accepted theory and code.

These are genuine harness observations. They do not establish a correct or complete
research result.

## Scientific Findings

The latest independent report judged all seven finite response formulas coherent and
the estimator handoff deterministic and implementable. It also said no additional
theory or code was needed for that finite execution handoff.

The same report retained material proof-completeness findings for the orthogonal
decomposition, projection identity, joint-Gaussian independence step, and Wishart
entry-covariance formula. The overall preflight therefore remained `REVISE`, and no
serious theory packet received independent acceptance.

The report's formula assessment is useful diagnostic evidence but not hidden theory
credit. No accepted packet existed, so the evaluator correctly did not run its hidden
mechanical or semantic theory checks. Likewise, AlgorithmEngineer, SimulationEngineer,
GeneratedCodeSemanticReviewer, CriticEvaluator, and all hidden algorithm and empirical
harnesses did not run.

## Harness Findings

Two shared control-plane defects made this run much less efficient than its scientific
state warranted.

First, the prior runtime counted a changed theory source hash as revision progress.
After the first review, four subsequent reports each recorded
`progress_made=false` and `stalled=true`, with no prior finding closed. Nevertheless,
the changed source hash repeatedly released another TheoryDeveloper visit. Source
identity is provenance, not evidence that a reviewed defect was resolved.

Second, one binary preflight disposition represented both full theory quality and the
readiness of a finite execution handoff. The latest referee explicitly said the
execution handoff was complete while proof-completeness findings remained. The old
gate therefore blocked all Python/R exploration even though the exact finite interface
was ready to implement and falsify. This contradicted the project's progressive
commitment design.

A smaller tool-observation defect amplified the final failure. Successful exact edits
did not return the current document SHA-256 under a stable named field, and the edit
tool lacked strict Anthropic input validation. The model then made stale-hash and
malformed-edit calls before the generic no-progress boundary stopped the workspace.

## Shared Future-Task Change

Commit `2124ee6e598a58885e11d9458e10316815b69952` changes only shared future-task
harness behavior:

1. The independent referee now reports theory quality separately from finite
   exploratory-execution readiness. `REVISE` may coexist with
   `READY_FOR_EXPLORATORY_EXECUTION`; active findings remain visible and research-eval
   theory credit remains false.
2. A rejected preflight continues only when the reviewer records actual prior-finding
   progress. A changed source hash remains telemetry and cannot authorize another
   revision by itself.
3. Successful theory-document edits return `current_document_sha256`, and the existing
   exact-edit tool uses strict schema validation.

The same source-owning model still chooses mathematics, code, searches, edits, and
terminal actions. The runtime does not parse the proof, add a Wishart formula, invent
an edit, generate a repair recipe, add a worker, start another scheduler, loosen the
final evidence gate, or authorize confirmatory credit from a provisional handoff.

This selectively applies the useful OpenAI Codex harness invariants already adopted by
the repository: one retained source-owner session, stable capability-accurate tools,
raw model-actionable observations, external hash-bound files, explicit commits, clean
reviewer contexts, and sparse typed handoffs. Codex Core, App Server, provider
transport, thread store, worktree manager, and scheduler remain outside the product.

## Artifact Identity

- Visible question SHA-256:
  `f8ba186e9457ae0a66952dbc0a0d7cba53c89ef3ab9f035d531afe1f95e91954`
- Public preactivation ledger SHA-256:
  `01da45c78fc86b434e9784263e14369db6e88cecd1409843b44d46cd0ca5e958`
- Hidden gold manifest file SHA-256:
  `ab206fa5da0dc6b81b526a74d13fab8713128388b4ea9d2a3a1d31f018a3c077`
- Hidden gold stable hash:
  `295e3abbde32e14c01608f2769107447587458c5e418f5664fa27baf14f08583`
- Runtime result SHA-256:
  `ecd080099dfdcda63364579c65314f4262dfebed4465d4996fa5e207dd8f9b23`
- Runtime manifest SHA-256:
  `ac3dfdcbad9b84c8193c07119dadc2453056918f2a21b39f005a962ea9432336`
- Completion summary SHA-256:
  `afa43c93868b2ed9ab665b98e3a07e9155daf3440824b8234e09ddcd528ceccf`
- Failure summary SHA-256:
  `837396f5e9e7bbb4a5c294279bdccd3b5b45270349255e3d991cf2a32c490dd0`
- LLM topology SHA-256:
  `60b305669e0b8d2afd10b341a58162e9869be41226c272a5f2e56da78dd1aed7`
- Runtime progress SHA-256:
  `5851f7d961bd0ac9442e23d377276fd3dc101715006148c712ad00deefa65013`
- Gold assessment SHA-256:
  `e3872572bfc2b5a29874fafbf883cf93f8299bf8bf5de82877702d199ead64e5`
- Latest committed theory document SHA-256:
  `da151a988a57985d897360c8e95994c6ed382575b43929611379f8a20c6c5aef`
- Estimator handoff document SHA-256:
  `29dcbda561abac0b722e336a2b10a123b58eeac67eee905134ca50da43e33ca7`
- Terminal recovery theory document SHA-256:
  `5754fe36fed631a983994451a0305103d078353d4af45996513350b1cc464ab1`
- Latest referee report SHA-256:
  `ff4d187f04c89e145e412daa7846bee04531d8bbd8a0a959654657241c61216e`

## Final Disposition

Task111 remains permanently consumed at 0/1. Its persistent Markdown/LaTeX work,
independent reports, tool observations, recovery snapshot, and failed hidden gate are
retained. No accepted theory packet, generated implementation, simulation evidence,
Critic decision, formal proof, or hidden candidate evaluation exists. The post-run
shared commit improves future progressive research flow but cannot repair or rescore
this draw.
