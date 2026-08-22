# Huber Location L0 v1 Operator Audit

## Frozen identity

- Task: `huber_location_m_estimator_known_result`
- Product code and authority binding: `03558bacee39ea28d00fa962383f1d1aaaabc31d`
- Model: `claude-haiku-4-5-20251001` for every enabled role
- Visible question SHA-256: `1ceb1a07955b4b4043e934c541f1b4ba353cfd37d92e60de5442b81be989dd23`
- Gold manifest SHA-256: `89dba52ede66123bf142d1aa80d78173816dd185cf4ccdb0e605337a4f3ab2fd`
- Runtime manifest SHA-256: `cfff777302fdfdebc2ae65311c18aaa0571b48ae0785533b033944d64fd12231`
- Hidden report SHA-256: `b4e39ede472bfc0d76504ea121e642f01b76f6337bc946f7ff1a9f8275cb530c`

Exactly one fresh product run and one post-termination hidden evaluation were
authorized. They are consumed. This task must not be rerun, resumed, repaired,
or rescored.

## Observed execution

AgentRuntime ended `BLOCKED` after six outer traces and five handoffs. Every one
of the seven enabled model roles was pinned to exact Haiku; Formalizer was
disabled because formal evidence was not applicable.

1. Architect made one initial research decision, then RetrievalMemory supplied
   local source context without a model call.
2. TheoryDeveloper used 13 same-session model/tool turns. It wrote and locally
   edited two authoritative Markdown documents, ran two Python scratch checks,
   reread its work, and explicitly committed a checkpoint.
3. The isolated theory preflight used 10 model/tool turns, read the frozen
   documents, ran three independent scratch checks, wrote a 311-line referee
   report, and accepted the theory.
4. AlgorithmEngineer used three model/tool turns. Its first executed source
   reported a translation-tolerance failure; the same source owner revised the
   code from that raw observation, executed it again, and explicitly committed.
5. GeneratedCodeSemanticReviewer made three model calls but failed to produce a
   contract-valid review packet. Runtime failed closed before metric authoring,
   simulation, terminal Critic, or algorithm promotion.

The mathematics lives in 262-line `theory_derivation.md` and 262-line
`estimator_implementation.md`, not a large derivation JSON value. Their hashes
are `74df8ae7...` and `4e7b463b...`. The final generated Python source hash is
`31071e76...`. These are model-authored artifacts, not hidden-gold acceptance or
proof.

## Hidden result

Evaluator-only gold reported 0/1:

- Theory mechanical checks passed 7/7.
- The exact-Haiku semantic judge calibrated on 12/12 cases.
- Eight of nine semantic claims were `SATISFIED`; `empirical_targets` was
  `INCONCLUSIVE`, so combined theory did not pass.
- The runtime never produced an independently accepted algorithm handoff.
  Hidden algorithm and empirical harnesses therefore did not execute.
- Formalization and novelty remained not applicable.

The theory documents discuss the estimator, sandwich formula, normal closed
form, and robustness, but do not state the frozen coverage, contamination,
RMSE, and protocol-identity targets with enough specificity. The runtime
preflight's blanket acceptance missed that omission.

## Harness diagnosis

The immediate blocker was not a Python exception or a need for task-specific
repair. The reviewer response schema was too large for Anthropic's compiled
grammar, so provider-native structured output fell back to unconstrained text.
All three responses were complete, roughly 8.5k characters, but none covered
the required `dimension_reviews` in the exact prescribed order. Runtime then
regenerated the entire packet twice. Those three calls consumed 151,472 input
tokens and 6,708 output tokens before failing on the same structural error.

This is the wrong harness shape. Independent scientific judgment should remain
model-owned, but its control envelope should be small: artifact reference,
verdict, review-document reference, finding references, and evidence-boundary
acknowledgment. Review prose and dimension analysis belong in a durable artifact.
The runtime should verify identity, source hash, reviewer independence, and
promotion authority; it should not require a long ordered list or regenerate a
full scientific packet to repair presentation.

## Shared correction boundary

The correction may simplify the existing reviewer interface and use recorded
packets for deterministic regression. It must not add Huber formulas, special
dimensions, deterministic content patches, a RepairAgent, a second scheduler,
hidden feedback, another model draw, or post-hoc capability credit. Huber remains
0/1 regardless of later shared-mechanism improvements.

## Post-consumption shared correction

Commits `82083807`, `f5822f58`, and `a73be809` implement the permitted shared
correction. The live reviewer now makes one model call, returns a compact
`ACCEPT|REVISE` envelope, and authors the scientific analysis as a separately
hashed Markdown artifact. The provider schema contains no fixed ordered
dimensions or dynamic evidence-pointer enum, and invalid output is not sent
back to the model for full-packet regeneration. Runtime still validates exact
source lineage, reviewer independence, evidence references, document identity,
and promotion authority, and still fails closed.

One unrelated generic exact-Haiku calibration then confirmed that Anthropic
applied native structured output with zero provider fallback and zero transport
retry. The one response used bracket notation for array references, so it was
correctly rejected; the shared transport now canonicalizes only unambiguous
numeric brackets such as `[0]` to RFC 6901 `/0` before ordinary target-existence
validation. A deterministic regression covers that observed representation. No
second model draw occurred.

The final focused panel passed 105 tests and the complete repository passed
867 tests. Compile-all, diff, model-policy, provider-schema-size, legacy replay,
artifact-hash, and control-plane size checks passed. This is future-task harness
evidence only: no Huber artifact was changed or fed back, and its score remains
0/1 within the unchanged 0/28 ladder.

## Immutable artifact hashes

- Progress: `357cc7582112e4cfbf37b1c3bf0a761db5fc8a56c8600fcec7f1ee2795f45e9b`
- Failure summary: `b185a2a3a02697166ee050e51dcc7120e70b773fc638c0884440a05c4668bd00`
- Completion summary: `eaa86651f45b3b7a5b31cca8446fb2cca398554d1297649c546fd65cc4b66022`
- LLM topology: `22b4ebbd829f4d0fffc58b103ad1e8965d6f3ac29bc7dd0c135a635ab691e0b1`
- Traces: `5580ca692a5eb9a93737b55b9a94323206f68e907c175baebe914fefd0333603`
- Handoffs: `9b9e2551886582ddd31cae94c91aca7703ebd8288c0cc218147b93568285ef80`
- Observations: `710fc2c128418fd4977c4d8b156798461bc88fb8b6f7e6974688a95ac8524175`
- Runtime result: `fa26b9cfeddfba7e2fb8c453184a9de8be752249e537ac1b0661bcca4f35c657`
