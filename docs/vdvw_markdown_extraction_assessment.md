# VdV&W Markdown Extraction Assessment

This document records the first audit of the markdown conversion of van der
Vaart and Wellner, *Weak Convergence and Empirical Processes*.  The assessment
is about using the converted markdown as an ingest source for theorem cards,
benchmark holes, and later Lean formalization work.

## Input Files

The converted text is split into five markdown files under:

`/Users/yukang/Desktop/AI for Math/Codex/Math Textbook Foundation/Vaart 1996 Weak Convergence and Emperical Process(1)/Markdown/`

Line counts from the current conversion:

| File segment | Lines |
| --- | ---: |
| `Vaart 1996 Weak Convergence and Emperical Process_1-100.md` | 1,999 |
| `Vaart 1996 Weak Convergence and Emperical Process_101-200.md` | 2,840 |
| `Vaart 1996 Weak Convergence and Emperical Process_201-300.md` | 3,057 |
| `Vaart 1996 Weak Convergence and Emperical Process_301-400.md` | 3,110 |
| `Vaart 1996 Weak Convergence and Emperical Process_400-523.md` | 3,568 |
| Total | 14,574 |

## Structural Extraction Result

A simple numbered-statement regex over the five files found 324 labelled items:

| Kind | Count |
| --- | ---: |
| Theorem | 101 |
| Lemma | 91 |
| Definition | 9 |
| Corollary | 18 |
| Proposition | 3 |
| Example | 102 |

By chapter:

| Chapter | Count |
| --- | ---: |
| Chapter 1 | 65 |
| Chapter 2 | 155 |
| Chapter 3 | 104 |

This is high enough quality for an automated first-pass theorem atlas.  It is
not clean enough for direct Lean autoformalization without semantic review.

## Quality Assessment

Strengths:

- Numbered theorem, lemma, corollary, definition, and example labels are mostly
  preserved in machine-readable form.
- The table of contents and chapter headings are usable for dependency grouping.
- Key empirical-process results in Chapters 2.4-2.6 and statistical applications
  in Chapters 3.2, 3.3, and 3.9 are visible and extractable.
- Display math is mostly preserved as LaTeX-style markdown.

Known issues:

- Some file splits begin or end in the middle of a logical section; extraction
  must deduplicate boundary overlap.  For example, item `3.9.22` appears at a
  split boundary.
- Theorem statements can span many lines and blend into proof text; `Proof.`
  is useful but not a perfect delimiter.
- OCR/formatting artifacts occur in mathematical prose, such as joined words
  like `Hadamarddifferentiable`, `one-toone`, and `permutationsymmetric`.
- Some formulas are line-wrapped or split in ways that require manual checking
  against the original PDF before formalization.
- Some important mathematical definitions are implicit in prose rather than
  labelled as `Definition`, for example bracketing numbers, VC classes,
  envelopes, and empirical-process notation.
- Book-specific outer probability and nonmeasurable-map conventions are
  pervasive.  These cannot be ignored in a self-contained formalization plan.

## Can We Accurately Extract All Definitions And Theorems?

We can accurately build a high-recall theorem atlas from the markdown:

1. Extract numbered statements with source file, line span, label, kind, title,
   local section, and raw text span.
2. Deduplicate repeated items at chunk boundaries.
3. Classify each item by formalization readiness.
4. Attach dependency hints from theorem references and surrounding section.
5. Generate Lean theorem-hole benchmark tasks, not promoted declarations.

We should not directly promote every extracted statement to Lean.  The markdown
is an ingest source, not an authority sufficient to bypass mathematical review.
Every theorem card needs a second pass for:

- exact assumptions and conclusion;
- hidden measurability, separability, tightness, integrability, and envelope
  conditions;
- match to existing mathlib definitions;
- dependency graph;
- formalization tier;
- non-vacuity examples or concrete instances where relevant.

## Formalization Readiness Tiers

### Tier A: immediate or near-term targets

These are the best candidates for expanding the current library beyond bridge
interfaces.

| Source item family | Why it is suitable |
| --- | --- |
| Ch. 2.4 finite-bracketing Glivenko-Cantelli theorem | Clean proof architecture: finite brackets plus SLLN.  This is the most direct path from the current `BracketingDeviationCertificate` interface to a primitive theorem. |
| Ch. 2.4 empirical CDF example via brackets | Good concrete non-vacuous instance after finite-bracketing GC exists. |
| Ch. 3.2 consistency / argmax-style deterministic reductions | Matches current M-estimator route and can be staged first as deterministic well-separated argmax lemmas. |
| Ch. 3.3 Z-estimator linearization theorem | Matches current Z-estimator bridge; should be introduced as theorem cards before attempting full Banach-space proof. |
| Ch. 3.9 delta method and chain rule | Matches current delta-method bridge; first formalize finite-dimensional/normed-space restricted versions before the full topological-vector-space theorem. |

### Tier B: important but dependency-heavy

These should become theorem cards and benchmark holes now, but primitive proofs
come later.

| Source item family | Main missing dependencies |
| --- | --- |
| Ch. 2.4 random-entropy GC theorem | Symmetrization, maximal inequalities, outer expectations, reverse martingale convergence. |
| Ch. 2.5 uniform-entropy Donsker theorem | Empirical-process weak convergence in `ell^infty`, asymptotic equicontinuity, tight Gaussian limits. |
| Ch. 2.5 bracketing Donsker theorem | Bracketing entropy integral, Gaussian/pre-Gaussian process infrastructure. |
| Ch. 2.6 VC / VC-subgraph entropy bounds | VC combinatorics, Sauer lemma, covering-number translation, measurability conditions. |
| Ch. 2.10 permanence properties | Existing GC/Donsker theorems plus Lipschitz/closure/convex-hull machinery. |

### Tier C: late-stage research targets

These are valuable but should not block the self-contained GC/ERM route.

| Source item family | Reason to defer |
| --- | --- |
| Bootstrap empirical processes | Requires conditional weak convergence and multiplier processes. |
| Contiguity and Le Cam lemmas | Requires likelihood-ratio convergence and measure-change infrastructure. |
| Semiparametric efficiency and convolution/minimax theorems | Requires a mature statistical experiment formalization layer. |
| Infinite-dimensional Hadamard differentiability applications | Requires substantial functional-analysis and path-space APIs. |

## Recommended Extraction Pipeline

1. `vdvw_index`: parse numbered items into theorem cards with source spans.
2. `vdvw_dedup`: merge duplicate items at split boundaries.
3. `vdvw_classify`: assign each card to `definition`, `primitive_candidate`,
   `bridge_candidate`, `dependency_heavy`, `example`, or `defer`.
4. `vdvw_dependency_scan`: extract explicit theorem references such as
   `Lemma 2.3.1` or `Theorem 2.5.2`.
5. `vdvw_lean_skeleton`: generate Lean theorem-hole benchmark files only.
6. `semantic_review`: human/statistical review of statement fidelity.
7. `promotion`: move a theorem from theorem-hole to promoted `StatInference`
   only after a no-placeholder Lean proof and non-vacuity review.

## Immediate Library Expansion Recommendation

The next mathematically honest expansion should be:

1. Keep the current `BracketingDeviationCertificate` as an interface.
2. Add primitive definitions for brackets, bracket membership, L1 bracket width,
   and finite bracketing covers.
3. Prove the deterministic finite-bracket reduction:
   finite bracket control plus pointwise convergence on finitely many bracket
   endpoints implies uniform deviation convergence.
4. Use mathlib SLLN, or an explicit SLLN wrapper if needed, to prove the
   probabilistic finite-bracketing GC theorem.
5. Instantiate the theorem for a simple one-point class, then for the empirical
   CDF bracket example.

This is the cleanest route from the markdown to a self-contained theorem rather
than another bridge.

## P10 Bracketing And VC Audit Notes

The P10.M2 milestone should now focus on the finite-bracketing route before
the VC route.  This follows the textbook order: VdV&W prove the simplest
Glivenko-Cantelli theorem first by finite bracketing and LLN, then use random
entropy and later VC/VC-subgraph entropy results.

For P10.M2, acceptable progress is:

- keep `BracketingDeviationCertificate` as a high-level interface;
- add primitive deterministic bracketing inequalities for bracket endpoint
  control;
- add endpoint strong-law wrappers against mathlib's real-valued strong law for
  the finite endpoint families in the bracketing proof;
- add fixed-tolerance almost-sure eventual endpoint-control wrappers, because
  the strong law does not produce a deterministic all-`n` rate sequence by
  itself;
- add benchmark seeds for the deterministic bracketing inequality and the
  explicit finite `L1(P)` bracketing route;
- connect the endpoint LLN wrappers to explicit empirical averages and
  outer-probability/measurability bookkeeping before claiming the full
  Theorem 2.4.1 result;
- avoid calling the result self-contained until finite bracketing cover,
  endpoint convergence, measurability, and GC convergence mode are all explicit.

The VC-subgraph work should move after this finite-bracketing step.  The
markdown audit supports VC milestones only as plumbing and obligation tracking,
not as completed VC theorems.

The relevant VdV&W source families are:

| Source family | Formalization consequence |
| --- | --- |
| Theorem 2.6.4, VC classes of sets | Requires a combinatorial Sauer/shatter layer and a separate translation to covering numbers. |
| Theorem 2.6.7, VC-subgraph classes of functions | Requires measurable envelope handling and `L_r(Q)` covering-number statements before any GC handoff. |
| Theorem 2.6.8, VC-subgraph Donsker theorem | Requires pointwise separability, pre-Gaussianity, and envelope weak-second-moment/tail conditions. |
| Lemmas 2.6.15-2.6.20, examples and permanence | Useful for later class construction, but should enter as theorem cards first. |

Therefore the VC-subgraph milestone should add explicit metadata for:

- VC dimension or index bound;
- shatter coefficient or Sauer-bound statement;
- entropy or covering-number translation statement;
- measurable subgraph statement;
- measurable envelope statement;
- envelope integrability or moment/tail statement;
- separability statement where a Donsker route is involved;
- a no-placeholder non-vacuity witness that does not assert any real VC
  theorem.

This avoids the common autoformalization error of turning "VC-subgraph classes
are GC/Donsker under conditions" into a Lean declaration that silently drops
the conditions.
