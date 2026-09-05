# Prove2Me Adoption

Inspected on 2026-09-04: [paper v1](https://arxiv.org/html/2608.28433v1),
[platform](https://prove2.me/), and
[workspace commit 16e3fb51](https://github.com/prove2me/prove2me_workspace/tree/16e3fb51a061c05ea83e07617400fd642a9eac81).
The public snapshot contains client instructions, API references, and extraction
scripts, not the complete verification service or a downloadable Formalpedia
corpus. No tracked LICENSE, COPYING, or NOTICE file was found at that commit.
This change independently implements design ideas; it does not vendor their code.

## Applied to the Existing Runtime

The paper's useful contribution here is not another agent framework. It separates
stable theorem statements from proof attempts, uses independently checked
read-backs for statement fidelity, and supports reductions to separately solvable
lemmas. Our adoption keeps the single outer graph and retained inner tool loop.

### Blind Mathematical Read-Back

The previous FormalTargetSemanticReviewer saw intended mathematics alongside Lean
on its first turn. That allowed author intent to bias the reading. Following
[the auditor protocol](https://github.com/prove2me/prove2me_workspace/blob/16e3fb51a061c05ea83e07617400fd642a9eac81/references/mission_auditor.md),
the same existing reviewer now:

1. Receives only exact Lean source, declaration identity, and model-owned support
   files. Question, Theory, proposal prose, prior judgments, and their document
   handles are unavailable through read/search.
2. Authors a Markdown/LaTeX reading of the actual binders, definitions, hypotheses,
   conclusion, opaque dependencies, and possible vacuity.
3. Records that reading once, bound to source and project hashes. Only then does
   the runtime reveal the intended mathematics for comparison in the same session.

Early submission, guessed hidden paths, same-turn reveal/submission, and later
read-back replacement are rejected. Large comparison material stays available
through ordinary line-addressed document reads instead of an omitted tool result.
This adds no separate reviewer agent, scheduler, repair taxonomy, or model tier.
Source comments and names remain visible but untrusted; this is blinding against
separate author context, not a guarantee against hints embedded in source. Missing
library definitions must remain explicit uncertainty. Unlike Prove2Me missions,
our automated comparison does not claim a human audit or guaranteed faithfulness.

### Modular Diagnostic Sketches

The [proof protocol](https://github.com/prove2me/prove2me_workspace/blob/16e3fb51a061c05ea83e07617400fd642a9eac81/references/prove.md)
motivates checking a parent reduction before every child proof is complete.
Our support compiler previously promoted `hasSorry` to an error, preventing that
workflow across files. It now permits ordinary Lean diagnostic compilation of
unfinished helpers. The model chooses decomposition and revisions using existing
file, compile, inspection, and retrieval tools; no source is rewritten by runtime.

Support compilation remains `LEAN_SUPPORT_FILE_CHECK_NOT_TARGET_PROOF_EVIDENCE`.
The target identity probe traverses axioms, so an imported `sorryAx` or
custom axiom blocks closure even if the parent source compiles. Revised dependency
hashes invalidate the cached project; final promotion rebuilds from exact files.
An additional real-Lean regression exposed an existing audit bug: an earlier
`#print axioms` for an unrelated clean helper could mask the target's axiom report.
The parser now requires the final report to name the requested declaration. It
interprets the verifier's diagnostic protocol, not model-authored Lean grammar.
This fixes output attribution; it is not a new adversarial Lean-code sandbox.
This is not Prove2Me's remotely certified, immutable reduction graph or automatic
parent promotion. A local sketch is diagnostic work until local closure succeeds.

## Reuse Boundaries

Existing immutable target contracts, isolated candidate projects, dependency order,
local kernel promotion, and task-scoped RAG remain the collaboration foundation.
Keep shared definitions and milestone statements stable while the model develops
helper proofs. Ordinary compiler feedback stays with its source owner; only real
cross-workspace conflicts reach Architect. No fixed lemma count, mandatory proof
strategy, swarm scheduler, or new platform account workflow is introduced.

The [declaration extractor](https://github.com/prove2me/prove2me_workspace/blob/16e3fb51a061c05ea83e07617400fd642a9eac81/scripts/extract_decl_graph.lean)
uses elaborated Lean dependencies, separates type and value dependencies, and
handles theorem bodies through theorem metadata. The accompanying source extractor
uses Lean syntax/info spans. These are useful references for future measured
dependency-index work, not justification for a regex theorem splitter now.

Remote Formalpedia retrieval is **not connected**. An anonymous environments request
returned HTTP 401. The documented [search interface](https://github.com/prove2me/prove2me_workspace/blob/16e3fb51a061c05ea83e07617400fd642a9eac81/references/discover.md)
uses substring search and returns environment-bound theorem objects. A future
read-only integration must retain theorem/submission IDs, exact source hashes,
dependencies, status, and `mathlib_rev`; a remote `Proved` badge is never local proof.
No account was created, project uploaded, or external result added as a premise.

[Documented platform environments](https://github.com/prove2me/prove2me_workspace/blob/16e3fb51a061c05ea83e07617400fd642a9eac81/references/lean-setup.md)
use Lean 4.33.1/Mathlib `0df444a` by default, or Lean 4.30.0/Mathlib `c5ea003`.
Our active StatInference project remains `4cec7860`, Lean 4.30.0/Mathlib `81343555`,
with Statlib `6575d611`. Even the equal Lean version is not equal library identity.
Selected remote results would need porting and fresh active-project checking;
there is no silent environment upgrade or replacement of Statlib/Mathlib RAG.

## Evidence

Regression tests exercise blinded tool access, immutable read-back identity,
retained-session rejection feedback, and oversized comparison documents. Real
local Lean tests exercise a two-module child-to-parent reduction: admitted or
axiomatic child rejected at the target, proved child accepted, reopened child
rejected again under a changed project hash, even with unrelated clean axiom
diagnostics in the model's source. These are mechanism tests, not new
research-task credit. Current full-suite results are in `main_worker_status.json`.

No fresh model efficacy comparison or consumed-task rerun was performed. The
direct Anthropic SDK backend needs a securely injected `ANTHROPIC_API_KEY`, not
Claude Code. Tests/evaluations remain pinned to `claude-haiku-4-5-20251001`; no chat
credential, Opus model, or automatic escalation is used. The paper's heterogeneous
case studies do not establish a speed or success-rate gain for our Haiku system.
