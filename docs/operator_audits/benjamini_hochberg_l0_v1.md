# Benjamini-Hochberg L0 v1 Operator Audit

## Disposition

The single frozen exact-Haiku run is **failed and closed**. AgentRuntime stopped in
TheoryDeveloper after a substantive Markdown derivation was written, but before
independent theory review, algorithm authoring, simulation, the terminal Critic, or
hidden evaluation. The task remains `0/1` and must not be rerun, manually repaired,
or rescored.

Run directory:
`runs/main_worker_research_l0_benjamini_hochberg_20260814_v1_document_theory_exact_haiku`

Immutable evidence hashes:

- Runtime manifest SHA-256: `a3cb9b729dbc1b4c4dd3c1deaf77ab8ef9d80f9645f644fac2fbe3b851c554e7`
- Hidden-gold report SHA-256: `153430fffbc00c2ea91a2dca4f972d4309f1c4ea7250ed23120685e71064d9cb`
- Theory document SHA-256: `c10e1057153d46a67891aedfe4ed00376bf7302f4eabb5b8cec0df110ef67da9`

Formalization was optional and nonblocking by frozen task intent. No Lean work ran,
so Lean was not the cause of this failure.

## Transport Failure

The run completed three outer iterations: Architect planning, source retrieval, and
TheoryDeveloper. In one source-owning session, exact Haiku used ten model turns and
ten tools to inspect the workspace, search and read the frozen paper snapshot, write
and inspect `theory_derivation.md`, revise it, and report a gap.

The terminal blocker was a compact-index grammar requirement. Eleven of thirteen
claim rows and all five sanity-check rows referred to anchor strings that did not
occur literally in the Markdown. Runtime rejected five otherwise structured handoff
submissions for absent anchors. With the existing write budget exhausted, the model
honestly reported this as unresolved instead of fabricating acceptance.

This was misclassified as a mathematical gap. A document path, content hash, stable
claim ID, direct dependency edge, and status are sufficient compact provenance;
requiring a particular Markdown anchor spelling adds no scientific authority.

## Theory Audit

The intended representation did work: the substantive mathematics is a 192-line,
10,051-byte Markdown document, while JSON is only a compact handoff. That made the
candidate directly auditable. It did not make the derivation correct.

The unaccepted document has at least these substantive weaknesses:

1. Lines 58-62 characterize `R = r` using only ranks `r` and `r+1`. A step-up maximum
   requires ruling out every qualifying rank above `r`; the stated stability lemma may
   be usable, but its submitted proof is incomplete.
2. Line 69's converse rejection argument does not establish the needed order-statistic
   count, especially under the document's own ambiguous tie convention.
3. Line 129 asserts all-null equality from tightness without completing the step that
   replacing one p-value by zero makes the leave-one-out rejection count positive.
4. Line 168 assigns a tied group its minimum rank. That is not the executable BH
   adjusted-value convention and can change the rejection set relative to ordinal
   sorted positions plus the reverse cumulative minimum.

These are model-authored scientific defects. Product code must not add a BH formula,
tie rule, leave-one-out proof, or task-specific correction for them.

## Shared Mechanism Response

Commit `7fa52b2571b419d21bc55320d6fb5c15e3971b12` makes one generic simplification:

1. Claim and sanity-check indexes use stable IDs, exact document paths, statuses, and
   direct dependencies, but no longer require model-authored Markdown anchor syntax.
2. Independent preflight must inspect every line of each hash-bound authoritative
   Markdown/LaTeX document. Long documents can be read through adjacent ranges in
   parallel within the existing tool loop.
3. Read coverage is inspection provenance only. The reviewing model still owns the
   derivations, counterexamples, uncertainty, and verdict; kernel proof remains a
   separate authority when formalization is requested.

The change is a net code reduction and adds no agent, fallback, retry, tool turn,
budget, content patch, statistical formula, Lean rule, tactic rule, or model-tier
escalation. The full suite passed `761/761`. This is regression evidence only; the
frozen BH task was not rerun and the transport fix supplies no mathematical credit.
