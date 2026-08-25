# PyMLE CIR source replication L1 v1 operator audit

## Frozen authority

- Task: `pymle_jss_cir_example_public_replication`
- Paper: Kirkby et al. (2025), *Journal of Statistical Software* 113(4),
  DOI `10.18637/jss.v113.i04`
- Repository: `https://github.com/jkirkby3/pymle`
- Pinned commit: `a68ee7b071a9eae8264c649719052ef711b47775`
- Visible question SHA-256:
  `67d9e1e5abaae744b0f2ec30e1267b93b450fc74b0977034d0abc1e46f3b08b9`
- Source snapshot hash:
  `6aed2ddc96d822d1c253f67d69015c1de4c924955e573089939ac2f8edeaac78`
- Evaluator descriptor:
  `ea3789f34dd03433de0721533786eff876b89348f45624ebec2653cc3fa6855a`
- Activation commit: `378d00df589952ae18c3f5e149293439bd5d0fe1`
- Every enabled live role: `claude-haiku-4-5-20251001`
- Formal evidence: `not_applicable`

The visible task, immutable source snapshot, execution environment, and
evaluator-only gold were frozen and pushed before the first product-model
call. This single draw is consumed and cannot be rerun, resumed, repaired, or
rescored.

## Runtime result

The sole AgentRuntime terminated `ACCEPTED` after three outer traces:
ArchitectCoordinator, the TheoryDeveloper-hosted source workspace, and
CriticEvaluator. The source workspace used 14 model turns and 20 model-chosen
tool calls. It executed the unchanged `examples/Example_CIR_MLE.py` exactly
once in the pinned CPython 3.12.13 compatibility environment, wrote a
320-line Markdown report, disclosed unresolved gaps, and committed one
hash-bound `SourceReplicationCheckpoint`.

The execution preserved the pinned source and environment identities, denied
network and secret inheritance, returned process status zero, recorded four
`xtol` terminations, recorded the Shoji-Ozaki maximum-evaluation termination,
and retained the SciPy `delta_grad == 0.0` warning. No generated estimator,
replacement simulation, theory theorem, Lean source, RepairAgent, second
scheduler, or runtime-authored scientific edit was involved.

## Frozen evaluation

The pre-frozen evaluator returned `1/1`:

- source, environment, and execution checks: `11/11`;
- source-report judge calibration: `6/6`;
- source-report rubric claims: `6/6 SATISFIED`;
- checkpoint lineage and unresolved-gap disclosure: passed.

This is the first protocol-level source-replication pass and the second full
task pass in the 31-task ladder. It is not theorem evidence, a Monte Carlo
study, validation of PyMLE, or proof of general source interpretation.

## Operator semantic finding

Post-run read-only audit found that the frozen report judge produced a false
positive. The report correctly says one seeded path cannot establish bias,
consistency, efficiency, or estimator superiority, but elsewhere calls the
Shoji-Ozaki estimate "substantially biased downward." It also says the exact
density "should theoretically be optimal" and supplies speculative
explanations not established by this replication. Finally, it labels the
40-character Git commit as "Commit SHA-256."

The deterministic identity and output evidence remains valid. The semantic
finding narrows capability credit but does not alter the score fixed by the
pre-run protocol. Critic also returned `ACCEPT` without inspecting these
report-level contradictions, which confirms that terminal orchestration
acceptance is not independent scientific correctness authority.

## Shared correction

Commit `3c00a515040dff2e21e4ec4666fce7e70b45a8b7` changes future hidden
semantic judgments from bare per-claim labels to labels grounded by one exact
candidate-document excerpt. The same Haiku judge must scan the complete
document, prefer a violating passage over supportive caveats, and quote the
candidate verbatim; runtime verifies only that binding and hashes the excerpt.

This adds no second judge, retry, repair path, task formula, phrase detector,
or scientific-content patch. A new unrelated synthetic contradiction case
calibrated `2/2` under exact Haiku and returned `FAIL` with a bound decisive
excerpt. Focused tests passed `73/73`; the complete repository passed
`873/873` in 68.00 seconds, with compile, JSON, diff, model-policy, and
production line-budget checks passing.

After integrating the immutable ladder and status records, `80/80` focused
tests and the complete `874/874` suite passed in 67.79 seconds.

The correction applies only to future evaluations. PyMLE v1 remains immutable
at its frozen `1/1`, with the semantic false-positive caveat permanently
recorded.
