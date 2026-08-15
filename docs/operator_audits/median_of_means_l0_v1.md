# Median-of-Means L0 v1 Operator Audit

## Disposition

The single frozen exact-Haiku run is **failed and closed**. AgentRuntime stopped at
the independent theory preflight with a nonretryable Anthropic schema-compilation
error. The run did not reach algorithm authoring, simulation, the terminal Critic,
or hidden evaluation. Independently, the unaccepted model-authored theory document
contains active mathematical errors, so removal of the transport failure would not
make this frozen candidate a pass.

Run directory:
`runs/main_worker_research_l0_median_of_means_20260814_v1_document_theory_exact_haiku`

Immutable evidence hashes:

- Runtime manifest SHA-256: `689f37286995c3d02faaa3177602817f2c0c24802d984b4a513ec1eaa5e5f5c9`
- Runtime failure summary SHA-256: `447d117321a4720141c4fa8c5708a613f98db4cf9d4d63e6405d5aa5ed188cfd`
- Hidden-gold report SHA-256: `6f6b15de25b3737fd3e140bf2bead74957998eb7a8b039c1565e8f158c2007b8`
- Theory document SHA-256: `005a97b742777e3cc5097175633816ff7449e8626997370e26045857531cf691`

This task remains `0/1`. It must not be rerun, manually repaired, or rescored.

## Transport Failure

The run completed four outer iterations: Architect planning, source retrieval,
TheoryDeveloper authoring, and Architect preflight. On the first preflight model
turn, Anthropic rejected the request before the reviewer produced any response:

`Schema is too complex for compilation. Try reducing the number of tools or simplifying tool schemas.`

The failed request exposed six tools. Its terminal submission tool used a strict
schema whose claim, dimension, and estimator rows were expanded into generated
`slot_0`, `slot_1`, and similar object properties. Runtime already validates every
submitted row and returns typed validation observations to the same reviewer, so
provider-side strict compilation duplicated an existing boundary without adding
scientific authority.

The failure was classified as `subsystem_exception`, nonretryable, with zero retry
attempts. No preflight verdict exists. Hidden algorithm, theory, and empirical
harnesses were correctly not executed because no independently accepted runtime
handoff existed.

## Theory Audit

The candidate did use the intended representation: its substantive mathematics is
in `median_of_means_theory.md`, while the structured handoff contains no JSON
derivation steps or equation-chain body. Markdown authority therefore worked as a
storage and audit mechanism. It did not make the model's reasoning correct.

The active document has at least these defects:

1. At lines 71 and 75 it infers `|Z_j - mu| > r` from a non-strict boundary
   `Z_j >= mu + r` or `Z_j <= mu - r`. Equality gives only `>= r`. A valid proof
   can use the preceding strict median inequality, but the submitted implication as
   written is false.
2. At line 123 it states `(k+1)/2 - k/4 = k/4` and calls the two events equivalent.
   The difference is `k/4 + 1/2`. Replacing it by the weaker `k/4` threshold can
   yield an upper bound, but it is not equality or event equivalence.
3. Lines 125-131 place the false Hoeffding formula `exp(-2 t^2 k)` and the resulting
   `exp(-k^3/8)` inside the active proof, then correct it in prose rather than marking
   the rejected calculation as non-authoritative. The later formula at lines 133-137
   is the relevant one.
4. Lines 172-175 prescribe `ceil(8 log(1/delta))` blocks without enforcing the
   task's odd-`k` requirement. Line 206 then claims `k=11` for `delta=0.05`; the
   displayed rule gives 24, whose next admissible odd value is 25.

These are model-authored content failures. Product code must not add a median rule,
Hoeffding formula, odd-rounding recipe, or task-specific correction for them.

## Shared Mechanism Response

Commit `44e12fff3e2f5163d071944b973416cf70f14fc4` makes only a generic harness
simplification:

1. The existing terminal review tool is non-strict; runtime remains the sole typed
   submission validator and returns raw validation errors to the same model.
2. Claim, dimension, and estimator reviews use compact fixed-length arrays in the
   client-tool schema. Runtime still binds each ordered row to immutable identity.
3. When a non-formal task already supplies authoritative theory documents and an
   exact research-source snapshot, the duplicate compact-source search tool is not
   exposed. Formal tasks and source-sparse tasks retain it.

This adds no agent, fallback, retry, tool turn, budget, content patch, statistical
formula, Lean rule, or model-tier escalation. The focused preflight suite passed
`47/47`; the full suite passed `757/757`. A separate infrastructure-only exact-Haiku
probe with five tools, sixteen claim rows, and a 5,201-character submit schema was
accepted by Anthropic and returned `tool_use` with no strict tools. That probe carried
no median-of-means content and is not a benchmark rerun or scientific capability
result.

