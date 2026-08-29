# Non-adaptive FLAME matching: public method record

## Primary source

Neha Gupta, Tianyu Zang, Awa Dieng, Skyler Speakman, and Alexander Volfovsky,
"dame-flame: A Python Package Providing Fast Interpretable Matching for Causal
Inference," *Journal of Statistical Software* 113(2), 2025.
DOI: `10.18637/jss.v113.i02`.

Article and replication materials:
<https://www.jstatsoft.org/article/view/v113i02>

The authors' MIT-licensed implementation is published at
<https://github.com/almost-matching-exactly/DAME-FLAME-Python-Package>.
For this paper-to-code task its identity and pinned commit are recorded, but its
source and outputs are withheld from the model workspace.

This operator-authored record indexes one closed algorithmic slice from the
paper. It is not a copy of the article, implementation source, or hidden test
data. The task deliberately does not ask for adaptive prediction-error scoring,
DAME active-set search, matching with replacement, missing-data handling, or a
causal-identification theorem.

## Statistical object

There are `n` observational units and `p` discrete covariates. Unit `i` has
covariate vector `x_i`, binary treatment `t_i`, and observed outcome `y_i`.
For an active covariate index set `J`, define the exact-match cell

```math
G_i(J)=\{j : x_{j,k}=x_{i,k}\text{ for every }k\in J\}.
```

A cell is admissible only when it contains at least one treated and at least one
control unit. All units in an admissible cell receive a main matched group at the
first iteration where their cell is admissible. In the frozen task, matching is
without replacement, so a unit leaves the unmatched pool after receiving that
main group.

For an admissible group `G`, report the within-group outcome contrast

```math
\widehat\tau_G
=\frac{1}{|G_1|}\sum_{i\in G_1}y_i
-\frac{1}{|G_0|}\sum_{i\in G_0}y_i,
\qquad G_a=\{i\in G:t_i=a\}.
```

This contrast is a descriptive matched-group quantity. The executable task does
not establish unconfoundedness, overlap in a population, consistency, or an
average causal effect theorem.

## Frozen non-adaptive procedure

The task supplies one nonnegative weight for each covariate. The weights sum to
one. Smaller weight means the covariate is less important for matching.

1. Begin with all covariates active and all units unmatched. At iteration zero,
   partition the unmatched units by equality on every active covariate. Accept
   every cell containing both treatment arms and remove its units from the
   unmatched pool.
2. If the unmatched pool no longer contains both treatment arms, stop: no later
   covariate drop can create a mixed-treatment group. Otherwise, while unmatched
   units remain and at least two covariates are active, remove the active
   covariate with smallest weight. If weights tie, remove the smaller original
   covariate index. Record that index in `drop_order`.
3. Repartition only the currently unmatched units using the remaining active
   covariates. Accept all cells containing both treatment arms, record their
   main matched groups, and remove their units.
4. Stop when every unit is matched, the unmatched pool lacks either treatment
   arm, or only one covariate remains. The final active covariate is never
   dropped.

Groups are mathematical partitions, not display rows. The output contract uses
sorted unit and covariate indices only to provide a canonical JSON
representation. It does not make row ordering part of the statistical method.

## Properties to audit

- Every unit appears in at most one main matched group; matched and unmatched
  indices partition the input rows.
- Every reported group contains treated and control units and is exactly equal
  on every covariate recorded as active for that group.
- Once a unit receives a main group, later covariate drops cannot move it to a
  different main group.
- Permuting input rows merely relabels group members. Permuting covariates and
  their weights together relabels active sets and the drop order.
- Translating every outcome by a common finite constant leaves all group
  contrasts unchanged. Multiplying every outcome by a finite scalar multiplies
  every contrast by the same scalar while leaving the matching partition fixed.
- Repeated calls are deterministic and do not mutate the request.

These are finite algorithmic identities. They do not validate the adaptive
FLAME match-quality criterion, estimate uncertainty, or prove causal validity.

## Hidden implementation authority

After the product run, evaluator-only code may compare the submitted function
with an independent implementation and with behavior from the MIT-licensed
author package pinned at commit
`6dcbc3c3945f1eb4f89f8386ef6418e72755ba73`. Hidden source, cases, outputs,
seeds, and acceptance thresholds never enter AgentRuntime, RAG, or model
feedback.
