# Lean Foundation Integration Check

AI integration: `c480917f7427c2ebbe2ddff1bb0c1c0c02d3b7e9`.
Lean main/submodule: `db6c7718349f3c14a7e37905f3529675f1ebaa52`.
This is release/mechanism evidence, not a new agent experiment or mathematical result.

The [foundation audit](../external/EmpericalProcessLEAN-main/docs/publication_foundation_audit_20261001.md#correction-baseline-inventory-mismatch)
corrects the earlier eight-name diagnosis. The separate baseline walker missed
inline attributes, unlike the current-file reader. It is deleted; both inventories
reuse the existing reader. No source theorem, proof body, name exception, new Lean
grammar or relaxed check is introduced. New attributed source-qualified names
remain rejected; explicit all-declaration audits still expose legacy debt.

Verification records are local under `runs/publication_lean_api_inventory_20261002/`:

- Primary suite: 1961 passed, 18 skipped, one existing xfail, 711.59 seconds.
  `primary_suite.junit.xml`: 1980 cases, zero failures/errors, SHA-256
  `a19fe2b524f3c59515d018bc0a17f39731f8a5c843bf8e161f1e31653eb822f3`.
- Lean/RAG tool suite: 86 passed, one opt-in skip. `tool_tests.junit.xml`:
  87 cases, zero failures/errors, SHA-256
  `ba118c575b789b511fb06fc9d68892732df66e5886b93c44e2d99e0f2800f139`.
- Default guarded InteriorPoint file/module and three existing ledger declarations:
  exit 0, complete native axiom-dependency records, zero unexpected axioms. No policy bypass.
  `guarded_check.log` SHA-256
  `9ee67527184179815bbcc48c120e5cacad4d94bfb571b14831ff26bbac2c237d`.
- Entire unchanged library incremental gate: zero new names/violations. This is
  not whole-API conformance: InteriorPoint's explicit all-declaration audit has
  746 violations among 1466 source declarations, including 328 oversized names.

Current main RAG was refreshed without changing historical indexes/evaluations
or tracked CSV exports. Its schema 6 SQLite metadata and shared manifest bind the
clean Lean commit above, Lean 4.30.0 and Mathlib
`81343555dae873c8de2de2b27bbabf7bc4d8d97a`. It has 52485 declarations;
canonical lookup of `negLogBarrier_selfConcordantBarrierOn_Ioi` returns the
same active source. Index counts and graph neighbors are not native proof evidence.
The source ledger is unchanged at SHA-256
`99f2a42a4813a896591a9296cc824d6131982bfd52a482056173a4f330c54e80`.

Partial branch review confirms the truncated-power-moments and affine-power-moments
files are byte-identical to their non-ancestor branch versions. Main retains the
compact-power-concave-family branch content and adds a constrained-family definition
and three lemmas. This checks those files, not all branch mathematics or proof fidelity;
unmerged ancestry alone does not justify a wholesale merge.

Release rights remain unresolved: the Lean tree tracks 50 textbook assets
(23 PDF, 20 Markdown and seven PNG files across five source groups). Presence in
Git does not establish redistribution rights. Neither repository has a root code
license. No book asset was deleted, redistributed anew or licensed by this check.
An exact-pattern scan of current tracked text found no Anthropic/GitHub token-prefix
matches; it is not a comprehensive security audit or a check of Git history.

No model calls, new theory acceptance, source-fidelity/coverage qualification,
clean-machine release or comparative scientific benefit is established. Both
official publication studies remain prospective. Historical Haiku and consumed
Qwen records remain unchanged; the full two-publication goal remains active.
