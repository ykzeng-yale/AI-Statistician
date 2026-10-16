# Complete DR-DID Methods Investigation

This is exposed, source-assisted known-method development, not blind rediscovery,
a novel estimator claim, a qualified publication comparison or literal historical
replication. Investigate doubly robust difference-in-differences for panel and
repeated-cross-section data using the supplied Sant'Anna--Zhao paper, proof
supplement, original replication sources/data and pinned DRDID package.

## Scientific Deliverable

Develop one coherent research project connecting the motivating policy estimand,
identification, estimation, inference, comparative simulation and NSW application.
Maintain reviewable Markdown/LaTeX files under `src/`, with definitions,
assumptions, justified vertical equation chains and the conditions of every
invoked result. Explain the panel and repeated-cross-section constructions,
double robustness, nuisance-estimation effects, improved inference and efficiency
claims at the scope actually established. Do not substitute numerical agreement,
source quotation or a theorem number for a mathematical argument. Preserve gaps,
conditional claims and counterexamples honestly.

Read and attribute the primary paper and separate proof supplement. Native main
TeX and bibliography are available; their incomplete LaTeX build assets do not
invalidate the PDF or supply missing proof steps. The extracted PDF text has
layout/formula limitations; check the native source and original references.
This family has already been exposed in assessor development. Do not read prior
assessor reports or unpublished key files, claim untouched holdout performance,
or use operator-prepared population arguments as your own result.

Reuse original code and pinned packages where appropriate rather than rebuilding
established infrastructure. Document exactly what is reused and what you author.
The original scripts contain site-specific paths, installation commands and
historical environment assumptions. You own every adaptation in your candidate;
the host does not patch statistical source. Preserve the original source tree.
The fixed environment is R 4.4.2 and DRDID 1.3.0, commit
`85807cfbddbd64cc6f3f8ba37f52d07c6c3acc65`, not the historical R 3.6.2/package.
Do not install a moving GitHub head or claim exact paper-era reproduction.

## Complete Computational Scope

Run the original ordinary Monte Carlo design for BOTH data structures:

- Four original DGPs, sample sizes 500 and 1000, 10,000 datasets per cell,
  original seed 1234 and propensity-index setting 0.75.
- For repeated cross sections use the original sampling share 0.5.
- Use the original DGP definitions and method/inference specifications. Document
  scheduling/RNG changes rather than silently claiming identical random streams.
- Panel methods: improved DR, traditional DR, unnormalized IPW, normalized IPW,
  regression and two-way fixed effects.
- Repeated-cross-section methods: improved DR1/DR2, traditional DR1/DR2,
  unnormalized IPW, normalized IPW, regression and two-way fixed effects.
- Retain every dataset/method attempt, warnings, failures and denominators. Never
  silently replace failed draws, filter unfavorable results or change the design
  after seeing it. Report the original measures with clearly justified Monte
  Carlo uncertainty. Numeric simulation is not a proof.
- Retain the original DGP's infeasible ATT benchmark and efficiency-bound value
  with each draw. Include their original benchmark comparisons in the summaries
  or executed-study notes; do not silently omit the oracle rows from interpretation.

This is 160,000 datasets and 1,120,000 method-attempt records, not independent
research-agent draws. The n=500 archive cells are additional to the main paper's
n=1000 study. The separate efficiency-bound integration entries (1,000 draws of
size 10,000,000) are NOT executed in this condition. Describe their role and this
omission; do not claim whole-paper computational replication or infer a bound's
mathematical correctness from a finite integration. Analyze the efficiency claims
from their stated assumptions and mathematical expressions instead.

Complete the original NSW/CPS application: LaLonde, Dehejia--Wahba and early-RA
samples, three original covariate specifications and all six panel methods.
Retain its 54 estimator/inference records and evaluation-bias contrasts against
the original experimental benchmarks. Explain the substantive population,
comparison, assumptions and sensitivity/limitations; do not call it an EHR study.
Preserve and explain observed source/version/result discrepancies rather than
adjusting numbers to the published tables. Inspect the original code critically;
its authorship is not a guarantee that every summary expression is correct.

## Existing Native Interface

The host has cloned a new candidate. Use the existing file tools to write its
complete source under `program_N/src/`; `program_spec.toml` retains a Python script
entrypoint `program.py`. That script may launch your R project with `Rscript`.
The host invokes it as:

```text
python src/program.py --source-dir ABSOLUTE_PUBLIC_DRDID_ROOT --output-dir ABSOLUTE_PROGRAM_ROOT
```

The public source root contains `paper/`, `replication/`, `package/` and
`source_inventory.json`. Its file-tool view is `sources/drdid/`. Read the staged
statistical research skill and relevant references as needed. Binary data are
read by your scientific program, not converted into text tool payloads. Paths
passed by the host are ordinary files; source inputs remain unchanged. Write
generated results under the supplied output directory, never `src/` or the
original source tree. The host has already loaded the fixed R module and set
`R_LIBS_USER` to its prepared library. At most fourteen R workers and one BLAS
thread per worker are available to your study. Do not submit additional jobs,
download models or call external LLM APIs from candidate code.

Use `evaluate_program` for complete official execution and fresh source review.
The retained same-model author reads the actual observations and chooses any
revision through `clone_program`. No additional diagnostic execution or separate
small-simulation gate is provided. A new candidate is a development revision,
not independent confirmation or a replacement for an earlier consumed result.
Do not edit frozen criteria or write host-owned metrics/receipts. The declared
turn, evaluation and time envelope is not a requirement to spend it all.

## Generated Outputs

Produce these new files at the output root:

1. `replicates.csv`: one row per dataset/method. Columns `frame,dgp,n,replicate,
   method,truth,oracle_att,efficiency_bound,estimate,se,lci,uci,status,error`.
   Frame is `panel` or `rc`, DGP
   is 1--4, n is 500 or 1000, replicate is 1--10000. Panel method IDs are
   `dr_imp,dr_tr,ipw,ipw_std,reg,twfe`; RC IDs are
   `dr_imp1,dr_imp2,dr_tr1,dr_tr2,ipw,ipw_std,reg,twfe`.
   `status` is `ok` or `failed`; failed rows retain a nonempty reason and may
   leave numerical fields empty. Successful records contain finite values,
   nonnegative SE and ordered intervals. Keep warnings in your execution logs.
2. `study_summary.csv`: one row per frame/DGP/n/method, 112 rows. Include
   scheduled/attempted/usable/failed denominators, the scientific measures and
   their Monte Carlo uncertainty; explain any undefined quantity. Do not remove
   failed methods from the summaries. Statistical formulas and summary column
   choices are yours, not host-authored mathematical answers.
3. `application.csv`: 54 rows with columns `sample_id,covariate_id,method,
   estimate,se,status,error`, plus any required substantive contrasts. Sample
   IDs 1,2,3 identify the three source samples in the order above; covariate IDs
   1,2,3 retain the original specification order. Methods use the six panel IDs.
   The same status/failure rules apply; document sample sizes and benchmark
   correspondence in a companion output or the report.
4. `study_notes.md`: the executed study's provenance, environments, sources,
   differences, failures and interpretation limits. This is generated evidence,
   not a prewritten assertion that execution passed.

The host records raw stdout/stderr, process status, source identity and table
accounting separately. It returns the public summaries, notes and execution
observation to the author and later report stage. Large raw records remain
retained but are not copied into the report prompt.

The host's `records_complete` metric checks table accounting and process delivery,
NOT correct DGPs, estimators, numerical reproduction, mathematical truth or report
quality. Source review separately assesses the argument and code correspondence;
its model is fallible and currently unqualified as a general scientific judge.
The common independent final publication assessment remains unqualified. Do not
claim independent acceptance because an internal criterion passes.

## Report And Formalization

Keep a source-authored methods/derivation appendix with the code. After a
completed selected candidate, the existing posthoc stage reads the actual public
results and writes a coherent main report and supporting empirical appendix.
The report must distinguish attempted, executed, reproduced, AI-reviewed and
unresolved claims, with citations and reproducible source-to-result links.
Posthoc cannot run new calculations or repair consumed results. No report stage
is promised after an incomplete investigation. Lean is optional and not requested
for this condition; no nonformal outcome is a kernel proof.
