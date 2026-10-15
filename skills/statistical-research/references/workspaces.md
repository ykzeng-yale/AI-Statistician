# Research Workspace

An example layout, adjustable to the project:

```text
research/
  question.md
  sources.bib
  theory/
    definitions.md
    claims.md
    derivations.tex
    gaps.md
  code/
  experiments/
    exploratory/
    confirmatory_protocol.md
    confirmatory/
  reviews/
  report.md
```

Keep claims and dependencies durable without rewriting the entire research
record on each model turn. A claim states what is asserted, under which
assumptions, why each derivation step is valid and what remains unresolved.
Simulations can expose a wrong or unidentified claim; do not silently omit that
finding or transform a failed derivation into a weaker success claim.

## Theory Development And Revision

Define the mathematical objects, target and assumptions before pursuing a result.
Treat a supplied or published conclusion as a claim to investigate, not an endpoint
that the argument must reproduce. Established mathematics can be reused: name the
source and verify its relevant conditions in this problem instead of reproving
everything or importing a conclusion by analogy.

Make load-bearing calculations auditable in aligned equation chains. Show complete
successive expressions with one justified transformation per line; use the correct
relation for an equality, implication, bound, approximation or limit. Keep notation,
conditioning, domains and normalization consistent. A verbal or structural argument
can use justified prose steps; do not force it into false equalities or a fixed
number of derivation steps.

Advance the useful claim or lemma in the persistent workspace, inspect its
consequences, and choose the next source read, computation or proof route from the
remaining uncertainty. Revise assumptions only for explicit scientific reasons.
Keep conjectures, partial arguments and unresolved conditions distinguishable from
established results. Numerical agreement and successful compilation do not prove a
statistical claim; inspect what a proposed counterexample or probe actually tests.

Evaluate review findings against the exact current argument. Identify the first
unsupported transition and its consequence, or explain why a proposed criticism
does not apply. The source owner authors the correction and revisits affected
claims and experiments. Correcting one finding does not establish the whole paper.

For a published baseline, preserve paper version/DOI, code revision, data and
environment identities. Compare the original computational question with your
actual executed version. Distinguish exact replication, paper-based reimplementation
and an extension; running a script is not automatically reproducing a paper.

For simulation design, articulate aims, data-generating mechanisms, estimands,
methods and performance measures. Record operating conditions, comparator
settings, numerical failures and Monte Carlo uncertainty. Prefer a frozen
precision target and valid stopping rule to a nominal number of repetitions.
See [Morris, White and Crowther](https://doi.org/10.1002/sim.8086).

Reviewer findings identify the exact artifact/version, location, defect and
scientific consequence. Confirmation and external judgments apply to those
inputs only. When premises or source change, revisit dependent evidence; preserve
unaffected evidence and every consumed evaluation. Kernel proof of an encoded
statement cannot substitute for reviewing its statistical meaning.

## Manuscript And Supporting Material

Respect the requested audience, format, notation and established manuscript master.
For new methods prose, connect the consequential problem, the closest existing
method's limitation, the precise contribution and the evidence supporting it.
Attribute literature claims to verified sources. A source-assisted reconstruction,
a methodological extension and a new result have different contributions; do not
rename the first as the last or invent novelty to strengthen an introduction.

The main text should make the estimand, assumptions, procedure, principal result
and scientific interpretation intelligible. Supporting material supplies the full
arguments and invoked-result conditions, algorithmic/computational details, complete
simulation design and outcomes, and application details needed to reproduce the
claims. Adapt the organization to the question; this is not a mandatory section
template. An omitted derivation remains missing, even if its conclusion looks right.

Make the application answer a substantive question. Explain why the methodological
difficulty matters, what the recorded variables measure, what the comparison shows,
and which assumptions or data limitations change interpretation. Include useful
comparators and sensitivity analyses for consequential uncertainties, not an
indiscriminate list of extra analyses. Statistical significance is not clinical
importance or identification.

After a scientific revision, synchronize dependent definitions, claims, proofs,
algorithm descriptions, simulation settings, tables, captions and conclusions.
Retain unaffected content and the author's voice. Report actual results and all
material failures; distinguish proposed, executed, reproduced, reviewed and formally
verified work. Do not fabricate citations, values, analyses or review. Never
silently replace original records. Ordinary exploratory analyses may be revised
and rerun with changes disclosed. Do not retry, resume or rescore a consumed
benchmark. A revised confirmatory analysis needs an explicit new condition; it
cannot replace the original outcome.
