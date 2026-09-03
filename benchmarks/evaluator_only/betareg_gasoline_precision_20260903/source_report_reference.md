# Reference: GasolineYield precision comparison

## Source and execution identity

This is a narrow rerun of Section 4.1 in Francisco Cribari-Neto and Achim
Zeileis, “Beta Regression in R,” *Journal of Statistical Software* 34(2),
2010, DOI `10.18637/jss.v034.i02`. The operator-bound entrypoint is the
unmodified official journal companion source with SHA-256
`0725416e1d260a76acf2f27db9a028ee5cf8366a1bb766e3e8115c5b381de57d`.
It ran once in the staged copy-on-write environment with R 4.4.3, betareg
2.2.0, and Formula 1.0.0. The process exited successfully, the staged source
inputs were unchanged, and the complete standard output matched its frozen
hash.

## Focused result

The first fit is

```r
betareg(yield ~ batch + temp, data = GasolineYield)
```

It uses a logit link for the conditional mean and a constant precision model
with an identity link. The source prints the fitted precision intercept as
`440.2783`. It then refits after omitting observation 4 and prints `577.7907`.
Thus the fitted precision is larger after that observation is omitted.

In the beta-regression mean-precision parameterization,

\[
\operatorname{Var}(Y\mid x)=\frac{\mu(x)\{1-\mu(x)\}}{1+\phi},
\]

so a larger fitted \(\phi\) corresponds to smaller conditional dispersion at
a fixed fitted mean within this model. This numerical comparison is a model-fit
diagnostic. It does not establish that observation 4 caused the change, that
omitting observations is a generally valid procedure, or that this model or
package is universally superior.

## Artifact and scope boundary

The execution declared and produced a nonempty `Rplots.pdf`. Its presence and
size are execution metadata; no visual or pixel-level inspection follows from
that fact, and its raw PDF hash is not a reproducibility authority because
three otherwise identical preactivation runs produced stable numerical output
but different PDF hashes. The official source continues through other article
examples, but they are outside this task's scoring scope.

This run reconstructs neither the authors' complete 2010 operating system and
R stack nor every article result. It is one source replication under the
recorded current interpreter and historical package versions. It supplies no
new theorem, general beta-regression validation, causal claim, novelty claim,
or Lean proof.
