# Task 97 operator audit: JSS beta-regression R replication

Date: 2026-08-29

Task: `betareg_jss_2010_r_public_replication`

Immutable run:
`runs/main_worker_research_l1_betareg_jss_r_replication_20260829_v1_codex_same_owner_exact_haiku`

## Disposition

`FAILED` for full-task capability credit.

The official R source execution is valid component evidence. The exact staged
source returned zero, preserved its pinned identity, reproduced the expected raw
stdout and stderr, and created the declared 59,037-byte `Rplots.pdf`. The runtime
also respected the frozen task intent: one TheoryDeveloper-owned source session
used exact Haiku, while Architect, generated-code, Simulation, Formalizer, Lean,
Sonnet, Opus, fallback, and repair lanes did not execute.

The model-authored report is not scientifically reliable enough for full-task
credit. The post-runtime hidden evaluator reported `1/1`, but its single
integrated Haiku candidate judgment false-accepted material active errors.
Operator review therefore overrides the automated pass without modifying,
rerunning, or rescoring the consumed candidate.

## Material findings

1. **Wrong link-likelihood ordering.** The report reproduces the five
   FoodExpenditure log likelihoods as logit 49.18495, probit 49.08044, cloglog
   49.35888, cauchit 50.01105, and loglog 48.86718, then says loglog is highest
   and gives another incorrect ordering. Cauchit is highest only among these
   displayed fitted candidates. This is a direct contradiction between the
   copied table and the adjacent interpretation.

2. **Wrong Breusch-Pagan threshold semantics.** The report calls `p=0.05144`
   marginal evidence or marginal significance at the 5% level. The 5% decision
   is non-rejection; the p value is below 0.10. Non-rejection does not establish
   homoskedasticity.

3. **Information criterion mislabeled.** The source calls
   `AIC(fe_beta, fe_beta2, k = log(nrow(FoodExpenditure)))`. The displayed values
   are therefore BIC-like penalized criteria despite the generic printed `AIC`
   column label. The report repeatedly interprets them as ordinary AIC.

4. **Coverage and scope remain incomplete.** The report does not explicitly
   account for the eight source-derived PDF pages, and its unresolved-gap section
   does not clearly separate this one compatibility rerun from theory validation,
   package-wide validation, simulation evidence, causal inference, novelty, or
   formal proof. Several conclusions also use stronger fit language than the
   reproduced diagnostics alone warrant.

## Harness diagnosis

The inner source workspace is structurally sound: one outer graph step, one
source owner, seventeen same-session model turns, twenty-one generic tool calls,
one immutable source execution, one Markdown write, and one explicit terminal
checkpoint. The failure is not evidence for another scheduler, a RepairAgent, a
beta-regression parser, or a report patcher.

Two shared future-task corrections follow from the failure:

- the existing source-owner prompt now asks the same model to inspect the exact
  saved report and adversarially cross-check numerical comparisons, threshold
  decisions, labels, scope, and gaps before it chooses commit;
- optional semantic protocol v11 keeps the full integrated judgment and adds one
  separately prompted adversarial Haiku pass over the same complete reference,
  rubric, and candidate. Conservative combination lets either pass block a
  false-positive acceptance. Qualification uses the same two-pass path for
  calibration cases, long-form negatives, the reference, and the candidate.

These changes improve model attention and evaluator falsification. They do not
encode the beta-regression answer, add runtime content rules, or repair Task 97.

## Immutable evidence

- runtime manifest SHA-256:
  `48ec46c17c30f2cc5a2af2c1c5cafc01561174945067550e8fc72bc363a1b0b7`
- runtime result SHA-256:
  `f0528f5a6579762f720dd354786d415753cf770666d46c141254ef0ebc21341d`
- automated gold evaluation SHA-256:
  `dabeab3ba1de7ce8e9507610da1ceaa6a2ce232589d1762079f5f9e47edb8600`
- runtime topology SHA-256:
  `1348e6f8d0a609dad94a0bee3e3653318fd506242b733d14a7712196d35c8243`
- model-authored report SHA-256:
  `09444d67efc602960153c90d2e9793b761bfb8cdb1e892d88f5e855a5e0fe10f`

The sole product draw and sole post-runtime candidate judgment are consumed.
Never rerun, resume, repair, reevaluate, rescore, resample, manually patch, or
feed hidden or operator findings back into this task.
