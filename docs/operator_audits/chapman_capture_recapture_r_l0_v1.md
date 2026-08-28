# Task 86 Operator Audit: Chapman Capture-Recapture in R

## Immutable disposition

- Task: `chapman_capture_recapture_bias_r_known_result`
- Frozen product code HEAD: `8da93daa665d5918c642da2fe7e3b23c7117b019`
- Run: `runs/main_worker_research_l0_chapman_capture_recapture_r_20260828_v1_codex_direct_exact_haiku`
- Product runtime status: `BLOCKED`
- Frozen automated full-task result: `0/1`
- Operator trustworthy full-task result: `0/1`
- Trusted aggregate after consumption: `5/86`
- Runtime model for every enabled role: `claude-haiku-4-5-20251001`
- Formalization: not applicable and not executed

The sole product invocation and sole post-runtime gold assessment are consumed and
immutable. They must not be rerun, resumed, repaired, reevaluated, rescored,
resampled, or exposed to the Task 86 source owners as hidden feedback.

## Frozen authority

The visible task fixed one finite-population result, one closed base-R estimator ABI,
three public hypergeometric designs, at least 12,000 confirmatory replicates per
design, and four-MCSE comparison rules. The hidden authority was qualified before the
first product call with one reference estimator, three executable source negatives,
an exact finite-support theory evaluator, a hidden empirical evaluator, six exact-Haiku
semantic calibration cases, and one full-document semantic near miss.

The visible question SHA-256 was
`070ecba80334e6966c9be9255105c63d791cbc405755c3c77ad495ee51414475`.
The hidden manifest stable hash was
`c58242c5e0f18761a0e7124844ad7d90a9b7617f1ab3a8f18ee5e5345c84a595`.
Hidden formulas, reference source, checks, and outcomes remained outside the
repository, runtime RAG, and model workspaces.

## Product execution

The task used one `AgentRuntime` and the existing workspaces:

1. Architect selected the mixed Theory, R code, and empirical path.
2. One persistent TheoryDeveloper session used 19 exact-Haiku turns, wrote two
   authoritative Markdown documents, ran R scratch calculations, and explicitly
   committed a theory checkpoint.
3. An isolated theory referee read the exact documents, used independent scratch
   calculations, and accepted the checkpoint.
4. AlgorithmEngineer read the theory, authored a real base-R `run_estimator`, executed
   it, received direct observations, and committed exact source. Its isolated source
   reviewer accepted it.
5. SimulationEngineer authored exploratory and confirmatory R sources. Failed R
   executions returned raw stderr to the same retained session; the model edited and
   reran its own source successfully without Architect repair or a RepairAgent.
6. The confirmatory-source reviewer authored an ACCEPT report with no findings, but
   its compact submission omitted a runtime-owned exhaustive clause-ID list twice.
   Packet validation ended the runtime at outer iteration 10.

The run contains 10 traces, 9 sparse handoffs, 13 runtime tools, 23 observations, and
81 product model turns. All seven enabled roles used exact Haiku. Formalizer and
formal-target review were disabled; there were zero Sonnet and Opus product calls,
no provider fallback, and no model escalation. One evaluator-only exact-Haiku call ran
after runtime termination; it did not generate runtime feedback.

## Hidden result by dimension

The full task failed, but the dimensions are not interchangeable:

- **Scientific code passed.** The hidden R harness accepted the exact estimator hash
  `4e6632d1258006a6b57077f4970e63aceebf9e4838723c31575f5f8f0a874aad`
  on all nine checks.
- **Empirical execution passed.** The hidden evaluator accepted all eleven checks for
  the model-authored R simulation source, including all three public designs and
  confirmatory finite-support comparisons.
- **Theory mechanics passed.** Both Markdown documents were present, hash-bound, and
  mechanically inspectable; all seven deterministic document checks passed.
- **Theory semantics failed.** The calibrated hidden judge marked the integrated
  document FAIL. It found one violated claim and two inconclusive claims among the
  seven load-bearing criteria.
- **Runtime completion failed.** The source-review envelope blocker prevented final
  simulation acceptance and Critic disclosure, so empirical gold success cannot make
  the runtime research loop complete.

## Theory failure

The authoritative derivation correctly states the overlap law and the final qualitative
bias result, but its central algebra is not a derivation of that result. It incorrectly
turns the shifted sum into

`E[1/(M+1)] = (1/(n1+1)) (1 - C(N-n1,n2)/C(N,n2))`

and therefore obtains an impossible expectation bounded near `n2`. The document itself
notices the contradiction, restarts, and still leaves the same invalid closed form
active. It later replaces the missing algebra with a proof sketch and numerical checks,
then declares the exact theorem established. The correct omitted-term argument requires
the shifted `n2 + 1` convolution and yields

`E[N_hat_C] = N - (n2+1) C(N-n1,n2+1) / C(N,n2)`.

This formula is recorded here only to explain the frozen evaluator finding. It must not
enter a Task 86 prompt, repair, rerun, task rule, or source revision. The independent
runtime referee false-accepted the active contradiction despite a generic prompt that
already said a correct final statement cannot cancel false intermediate steps and that
numerical agreement cannot establish an identity. This is a model mathematical-judgment
failure, not evidence for a Chapman parser, Vandermonde rule, extra reviewer vote, or
hidden-feedback loop.

## Harness correction for future tasks

Commit `9606ac34c19129ee7ec53808a8ccfb7b6b018374` removes one genuinely
unnecessary harness layer for future generated-code reviews. The model no longer has to
copy every runtime-owned public-contract clause ID into its verdict, and exact ID-set
coverage can no longer terminate an otherwise substantive source review. The complete
question, public contract, exact source, execution observations, and review material
remain bound by trusted hashes. The isolated reviewer still owns Markdown analysis,
model-selected probes, findings, and ACCEPT/REVISE judgment.

This change does not auto-fill a finding, infer that every clause was inspected, relax
source semantics, or modify this consumed task. It adds no retry, repair worker,
fallback, scheduler, task-specific branch, model call, or model escalation. It is a
direct application of the selectively adopted OpenAI Codex harness principle: the
model should reason and act through stable tools while the harness owns identity and
observations, not force the model to reproduce bookkeeping already known to runtime.

## Capability conclusion

Task 86 is the first trusted evidence that the canonical product can produce and
execute both a model-owned R estimator and model-owned R simulation in the same task,
including direct same-session recovery from raw R failures. It is not a full-task
success. Long-form mathematical derivation and independent theory review remain the
decisive failures, while an overconstrained reviewer envelope was a separate terminal
harness defect.

The correct response is to keep the persistent Markdown/LaTeX Theory workspace, raw
Python/R/Lean feedback, sparse content-addressed handoffs, isolated review, and external
gold authority. Do not add a statistical formula rule, content repair path, equation
parser, another scheduler, or mandatory formalization. The aggregate trustworthy score
remains `5/86` and strict development-panel source theorem closure remains `0/2`.

Reviewer and AgentRuntime regressions passed `127/127`; ladder closeout regressions
passed `84/84`; the complete repository passed `1030/1030` in 81.27 seconds. Compile-all,
JSON, duplicate-key, diff, and changed-file secret checks passed. Central runtime remains
24,947 lines, the generated-code reviewer shrank to 1,578 lines, and top-level production
Python shrank to 149,933 lines. These checks made no product or evaluator model call and
did not rerun or reinterpret the consumed task.

## Immutable hashes

- Runtime manifest: `433d428fd7e00940ca295bc8c7152bd14d1b2a21a11e5087b6ff73b4f13d48ff`
- Runtime result: `762046fea1c937d5a254a8271f034a2ce89ea45489d72b7965be6ce09cdc4b93`
- Gold evaluation: `e9aa0cb4d6253d6a8ac5e85d05acde26f9cb3e07760fb7ff0fd03296fc43063b`
- Failure summary: `cc66b9baaf2aa4f4fc506781f0c662fb0b1bc9937e7b6211f5ca7967b30d39b3`
- Runtime topology: `b6afad37e9e8b8b12346d1a6c1f24a039614d7e81f8302f9ecf71025ee495566`
- Evidence ledger: `f9e74319f0f8102768e24b5f0fb10e55ec0267f69726661870dc0cf43bd20735`
- Task handoffs: `e135c617592b1bef63563f63654610e2696003950c8995fab7b61d9e3222acf7`
- Runtime tools: `e9240b654bd4ce9e56d3a3fa7ac2c2a8f26f580837a88f641f820d07c523d420`
- Runtime traces: `cdab6662987bd7086f70fcb8d27bef2b59f042bb17ec92dc6c0e82e7fb156447`
- Runtime observations: `ff829255b073fcbf4d95c37e7a8126674586e2a7769ac4125c2135bc1f8f239e`
- Theory document: `b77cffad12df17d1203443a8c472cc02f8619b40e644f9779114148ee556181f`
- Estimator source file: `2b6c8de1385775432807fcc89cca3a3077eeaeddd46245d819e229ba4d991969`
- Confirmatory source file: `8b38a45f63cfa40dcdb1f2ac8916aef3bb1a858e9a49b259d43c7564f56fb45e`
