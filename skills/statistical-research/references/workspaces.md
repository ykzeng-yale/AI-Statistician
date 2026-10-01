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
