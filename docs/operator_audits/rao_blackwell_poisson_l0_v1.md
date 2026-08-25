# Rao-Blackwell/Poisson Theory L0 v1 Operator Audit

## Frozen identity

- Task: `rao_blackwell_poisson_variance_reduction_known_result`
- Product code: `5c6f77569df0caa37069b756d76448b95e28021f`
- Model: `claude-haiku-4-5-20251001` for every enabled role
- Visible question SHA-256: `5bb8bc4648daa15df3d6b5c25834cada52c4f9d364f97757201402cd38af1532`
- Gold manifest SHA-256: `92b0e4f3edc66351dea4ce459ec371111720e6dfb0e2742bad16e5afde5f05e0`
- Gold descriptor hash: `ff98c895c2f8971093808e8feae0d098c4e64f3d618bf2640bb866388aaa4574`
- Activation commit: `c776b8f0ec8fbd9c6ed2bf3d76ffe4611e735fe1`

Exactly one fresh product run and one post-termination hidden evaluation were
authorized. They are consumed at `0/1`. This task must not be rerun, resumed,
repaired, rescored, or resampled.

## Observed execution

AgentRuntime ended `BLOCKED` after five outer traces and four handoffs. One
Architect planning call and 50 client-tool model turns used exact Haiku:

1. Architect routed the theory-only intent to TheoryDeveloper.
2. TheoryDeveloper used nine turns to write and checkpoint one 251-line,
   12,319-byte Markdown/LaTeX derivation.
3. The isolated referee used 28 turns over two content-addressed segments. It
   read the exact document, maintained a versioned Markdown report, ran two
   exploratory scratch calculations, and tried to submit `ACCEPT` twice.
4. Both `ACCEPT` submissions were deterministically rejected because the
   source packet had no estimator specification.
5. The referee therefore emitted a high-severity finding requesting estimator
   specifications and routed the exact observation to the same TheoryDeveloper
   workspace.
6. TheoryDeveloper used thirteen turns to populate estimator and theorem
   handoffs, but the packet remained structurally invalid at terminal budget.

Scientific code, confirmatory simulation, source replication, formalization,
and novelty were correctly absent. Formalizer and Lean did not run.

## Mathematical artifacts

The authoritative model-authored theory document is `rao_blackwell_theory.md`,
SHA-256 `5c64facd63a6b2ae98c4a6ce4b43cff019500f465ce8a7650783a69c0734ebfc`.
Its initial packet is
`theory_derivation:6482ec2c8a1dbf8d8a3f34f4`, with content hash
`37d2c6026f027c89987e6eb83b4804f884fde8c313fd7e4eb767d37e9dcb6baa`.

The independent model-authored report is 232 lines and 12,025 bytes, SHA-256
`a47321893186eaddbf04a36752c929073e48656c9868f908d7c663254bcde888`.
It ends with `Overall Verdict: ACCEPT` and describes the risk decomposition,
vanishing cross term, Poisson factorization, conditional binomial law, risk
improvement, boundary cases, and UMVU limitation as coherent. This report is
diagnostic model evidence only: the typed independent-review acceptance gate
did not accept it, so it is not a passed theory dimension or proof evidence.

## Hidden result

Evaluator-only gold reported `0/1`. It observed no independently accepted
serious theory packet, so neither the grammar-free structural harness nor the
calibrated semantic judge executed on the candidate. It generated no runtime
feedback and disclosed no expected values.

## Shared mechanism diagnosis

The initial packet was valid under task intent and correctly contained empty
`estimator_specs` and `theorem_cards`: scientific code, empirical evidence,
formalization, source replication, and novelty were all `not_applicable`.

The independent preflight still used an execution-readiness acceptance rule:
`theory execution preflight cannot accept without an estimator`. This
contradicted the runtime-owned task intent and forced the model to invent a
downstream ABI handoff solely to make a mathematical review submit-able. The
subsequent blocker was therefore structural noise: executable estimator
interface shape and exact claim-index ID alignment, not a referee-identified
mathematical defect.

The future-task correction is to make one existing preflight submission
contract task-intent-aware. Mathematical review may accept an exact theory
artifact without estimator or simulation handoffs when those dimensions are
not applicable. Estimator ABI validation remains strict only when a downstream
executable lane is requested. This needs no new agent, scheduler, task formula,
mathematical parser, retry, turn increase, or model escalation.

## Future-task correction

Commit `3a6af4086eb229d6ff4f0fee393cb56e37da9d60` implements that shared
boundary. The compact upstream contract preserves runtime-owned dimension
requirements, and the existing preflight validator derives whether an
executable handoff is required. It accepts a theory-only compact disposition
without an estimator and still rejects the same omission for an executable
task. The fixed six-row review-considerations transport was removed, leaving
the isolated model to choose the load-bearing derivation in its Markdown
workspace.

Focused adjacent panels passed `162/162`; the complete repository passed
`892/892` in 69.42 seconds. Production Python shrank to 149,984 lines. This is
future-task regression evidence only: no model call, rerun, resume, repair,
hidden evaluation, rescore, extra turn, task formula, checklist, scheduler, or
model escalation occurred.

## Immutable artifact hashes

- Runtime manifest: `9a3e86d9ee11c7ecc081c3b676d8cc59515206d7d9ed87fd01f9c7e746995ac3`
- Hidden report: `6dc32211c0f769536a44e98e940a8791586402ba168c479eaf1a0c90480f2e68`
- Progress: `b6a8fb0f6d056d94863b3e84ff7cd40d3205f8c90abb3cbe689456f2afd63d56`
- Failure summary: `a3c6ef8064cea4248030d56896889270abf9d009122be473f3e490156b727313`
- Completion summary: `3d0f8b7d0083d8b7a47f489f510e7eb0478a9e4bc02e08e329099d54fb197f41`
- LLM topology: `9846cc299d7d4154bc6e0193deb17cb4fd24cd73ede7c95d9af5b667e423f225`
- Runtime traces: `0a74e6c269e1eacf962fc742c735e67b6eef5dc01015fafc07ee31846076c9ce`
- Task handoffs: `cb97814974573e7a37138a01ec52b9360c5dbe999e171f6790d855666e6acbd5`
- Runtime result: `84b3a63fb9c6de8feff18019c5cbdc68a92ecaf29aa9ec66980c9f917ece69c9`

Any post-run code correction is future-task regression evidence only. It cannot
change this candidate's score or authorize hidden evaluation of its unaccepted
artifact.
