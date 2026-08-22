# Basu Independence L0 v1 Operator Audit

## Frozen identity

- Task: `basu_complete_sufficient_ancillary_independence_known_result`
- Product code: `5d31059500ab291389b5aac1d6c97b5c712848f1`
- Model: `claude-haiku-4-5-20251001` for every enabled role
- Visible question SHA-256: `81d80ac8a01f1f0ffe0e1f75c0bd4062611711de902292267378cbf9c9868bab`
- Gold manifest SHA-256: `f86ba4be31ecd34b1b855160ada36fa933502450ae07905f0ed9b7cb652f8895`
- Runtime manifest SHA-256: `d6a31fd4a535b89d358067ecfbbbccd5e31620822c7b92ec8c65e4c815cedf15`
- Hidden report SHA-256: `3c1e28627a5b13b7454a49aeabc0c0545f4bea57a060ed273e74e3c571415769`

Exactly one fresh product run and one post-termination hidden evaluation were
authorized. They are consumed. This task must not be rerun, resumed, repaired,
or rescored.

## Observed execution

AgentRuntime ended `BLOCKED` after four outer traces and three handoffs:

1. ArchitectCoordinator selected TheoryDeveloper.
2. TheoryDeveloper used eleven same-session model/tool turns and committed one
   304-line, 20,551-byte Markdown/LaTeX derivation.
3. TheoryDeveloper returned to ArchitectCoordinator instead of the existing
   isolated theory preflight.
4. ArchitectCoordinator incorrectly described terminal CriticEvaluator as the
   independent theory reviewer and routed there.
5. CriticEvaluator's deterministic backstop blocked before its model call with
   `required_independent_theory_review_missing`.

Visible `research_eval` reported 0/1 complete, while remaining mode-conformant.
Scientific code, empirical simulation, formalization, source replication, and
novelty were correctly absent under task intent.

The authoritative theory document is
`basu_theorem_derivation.md`, SHA-256
`126b82e46aa0a33c4bd57e87aaf6d4430d542de86c679a75ee17a537bad3c6ac`.
Its packet identity is `theory_derivation:1ed21d1e993608431c59facb`, with
content hash
`586529c64ffad478fe881c6d5f576778639b558bc9244ccf2e75c138715a9209`.
This is model-authored theory evidence, not an accepted derivation or proof.

## Hidden result

Evaluator-only gold reported 0/1. It observed no independently accepted serious
theory packet, so neither the grammar-free structural harness nor the calibrated
semantic judge executed on the candidate. Required theory, unresolved-gap, and
overall runtime-loop dimensions failed. No hidden feedback was generated.

The result is an orchestration failure rather than a hidden mathematical score.
The candidate's own checkpoint disclosed unresolved concerns, but no operator or
hidden-evaluator judgment may be fed back into this consumed artifact.

## Shared mechanism diagnosis

Runtime task intent correctly required independent theory review, and the
runtime-requested evidence contract carried that requirement. The nonempty
Architect plan contract omitted the runtime-owned field. TheoryDeveloper gave
the nonempty plan contract precedence, concluded that no preflight was needed,
and returned to ArchitectCoordinator.

The terminal Critic backstop prevented false acceptance, but a backstop is not
the intended workflow. Runtime-owned task intent must survive Architect contract
projection and must be checked again at TheoryDeveloper's exit. The existing
isolated referee, exact artifact lineage, and same-owner revision return are the
correct mechanisms; no additional reviewer or scheduler is needed.

## Immutable artifact hashes

- Progress: `14d858af1bedabcd73a1fd55e77bb5384ab5adcdb0b9f7caae4b44c94c4ff81f`
- Failure summary: `26869271f880edfbae70c11d557409a544d7cfae5c784f4fafc63d1d4631e936`
- Completion summary: `6f025f0abc0361bd09780a4d9c5b290eefc4f715e093614a0898bb31dad8db84`
- LLM topology: `92816dda8837a0df4febee9d91f72ae1c72bd2982178b5fccd54fec2b0e2df65`
- Runtime traces: `db4768cd7d4cc3d369ead410e8da8091efeaf55d4a3de42eb7040d6b7f1c854d`
- Task handoffs: `35c98be1092756c8aa935a16ba8ab75baaa73f1d77bfc98dd0894e29bda9d9c2`
- Runtime result: `5aec291ecfb3dd127385df6f62bed1c7876fd8dbfeab4d5f4a4c06a3ab6eb156`

## Shared correction boundary

Future theory-required tasks must preserve the runtime-owned independent-review
requirement in the canonical Architect plan and must route the exact Theory
artifact directly to the existing isolated referee. This correction may use
task-intent identity and artifact hashes only. It must not add Basu formulas,
mathematical checklists, retries, votes, repair agents, another scheduler, or
hidden evaluator feedback.

The consumed candidate remains 0/1 regardless of later regression results.
