# PyOD ABOD source replication L1 v1 operator audit

Date: 2026-08-26

## Immutable identity

- Task: `pyod_abod_example_public_replication`
- Family: `anomaly_detection_source_replication`
- Activation and runtime identity: `45a2271677b7428512f996fb5497451055c13581`
- Public source commit: `690a0f25987fab0664b014bbc7121d999c92f5f6`
  (`v1.1.3`)
- Source snapshot: `pyod-jmlr-2019-abod-v1.1.3-public-replication-v1`
- Source snapshot hash:
  `aa5219ef58f5b24ae3bd8477668d7cb65163fed4e74f6e0d33bc66f324e2c82d`
- Run:
  `runs/main_worker_research_l1_pyod_abod_replication_20260826_v1_codex_external_state_exact_haiku`
- Runtime model: exact `claude-haiku-4-5-20251001` for all seven enabled
  roles; no Sonnet, Opus, or automatic escalation
- Runtime result: `ACCEPTED` after three outer traces
- Hidden full-task result: `0/1`
- Operator disposition: `OPERATOR_CONFIRMED_HIDDEN_SOURCE_REPORT_FAILURE`

The task received exactly one product draw and one post-runtime hidden
evaluation. Both are closed and immutable. It must not be resumed, rerun,
repaired, hidden-evaluated again, rescored, or resampled.

Immutable SHA-256 values:

- Runtime manifest:
  `583d5e5a0678ddd90c548264c49e7bd4e3f258a8535bbbfeee074a21b5023f10`
- Runtime result:
  `395eea0717d6e2b4a61f703f1ec2e6560db8f1050a0a99857f72ebd9e1186d1f`
- Runtime model topology:
  `5a67d55924f21396229d859b6abb4d50d7d8422557d5e8a4858d4836a1cedbf8`
- Runtime progress:
  `ffdaf7e0b16c50f2d50d78f552d77586030a9006bd3b05bcbab9372df354ee0e`
- Model-authored report:
  `2e78ef9ba61465a31616db28c5abea16d98ffd682d9ff1019449b6592e2276d3`
- Hidden gold report:
  `6679783af62bdac1b7699b4a007307149aa96ea782b10e346cfe13dd57e87658`
- Hidden semantic result:
  `5d27c1502af5244ce66fd7b96a2b54a2b0600011d1bab6c2183da2dbf541ecf2`

## Runtime result

Architect used two provider calls because its first structured packet violated
the generic non-applicable-lane contract. The second packet selected the source
replication workspace. One persistent source owner then used 26 model turns and
31 model-selected tools; every selected tool executed. It inspected hash-bound
paper and source ranges, ran the unchanged author entrypoint once, and committed
one 504-line Markdown report. Critic made one final provider call. The complete
product run therefore used 29 provider/model calls, one Architect trace, two
handoffs, five observations, and no outer runtime tool call.

The source workspace recorded these durable identities:

- Source manifest: `source_replication:4c952aaeaeb57155da60`, hash
  `996ac281eeb4eb53f20412cab1a0eb6f8b8875536033f84a751b7c1acd93d116`
- Workspace evidence: `source_replication_workspace:3f31abf81eede044b0e5`,
  hash `35e01aad1841ca55b8ef5d5d57115c52d799955e774da57f324a567f4a01dc73`
- Checkpoint: `source_replication_checkpoint:842653347b820d07a10c`
- Report:
  `theory_workspaces/theory_workspace-de34596cb70ee6f8fe98/pyod_abod_replication_report.md`

Formalization was correctly not applicable. No generated algorithm or
simulation ran, and there is no theorem or kernel-proof evidence.

## Hidden evaluation

The mechanical source harness passed `12/12`. It verified the exact source and
environment identity, unchanged no-argument entrypoint, immutable inputs, raw
stdout and stderr, display warning, and report binding. This establishes a
faithful execution record only.

The independently calibrated exact-Haiku semantic judge classified five of six
report claims `SATISFIED` and claim 5 `VIOLATED`, so the candidate status was
`FAIL`. The report's lines 406-414 said that no source issue or discrepancy had
been identified. Yet the model-visible `ABOD` docstring says
`n_neighbors` defaults to 10 while the executable constructor defaults to 5.
That material source discrepancy is visible at source lines 112 and 142 and was
not disclosed. Because source-report semantics were required, the full task is
`0/1` despite all mechanical checks passing.

## Operator findings

The hidden failure is correct, and manual review found further defects:

1. Report lines 190-201 reverse the ABOD interpretation. The implementation
   computes angular variance and negates it at source lines 178-180; lower raw
   variance is more outlying, while higher stored decision score is more
   abnormal. The report instead calls high raw variance outlying.
2. Report line 408 says no issue was identified despite the default-parameter
   contradiction and the public old/new `generate_data` return-order change.
3. Report lines 444-447 infer successful high-accuracy anomaly detection from
   one seeded synthetic run. Execution and a large observed ROC do not establish
   detector validity, accuracy across draws, or generalization.
4. Report lines 486-488 call the outputs high quality, expected, and proof that
   the source runs correctly. Those claims exceed the single observed execution.
5. Report line 472 says the paper's exact PyOD version is unspecified. The
   model-visible JMLR text explicitly names PyOD version 0.7.0.
6. Report line 474 says `matplotlibrc` was absent from the snapshot, although it
   was included and model-visible.

The calibrated judge accepted claim 6 despite some of these contradictory
success claims. That is a judge caveat, not a reason to change the frozen `0/1`.

## Critic authority defect

Runtime Critic accepted because its canonical view contained only theory,
scientific-code, empirical, and formal dimensions, all not applicable. It did
not receive the authoritative source report, immutable execution observation,
or exact source ranges that the source owner had read. It therefore treated the
local accepted checkpoint as sufficient rather than independently checking the
report. This was a generic authority omission, not a need for a phrase detector,
ABOD rule, repair worker, another reviewer, or another scheduler.

For future tasks, the existing Critic now receives transient hash-verified
content for the report and the exact author-read source ranges, plus the bounded
raw execution observation. Required source replication cannot be accepted unless
the Critic marks that dimension supported. The persisted runtime record contains
only a compact identity audit; report and source text stay in external files.
Snapshot or report mutation fails closed.

Two unused legacy side audits were removed at the same time:
`fresh_holdout_frontier_audit.py`, which used token-overlap and a legacy
benchmark runner, and `adversarial_intake_audit.py`, which encoded a deterministic
intake side path. No live call or consumed-task replay validates this future-task
mechanism.

## Capability accounting

This is the fiftieth consumed scored task and remains `0/1`. Four of 50 tasks
retain trustworthy full-task capability credit. The separate variance-ratio
task remains operator-invalid and contributes neither credit nor blame. PyOD
retains scoped `12/12` mechanical source evidence but receives neither source-
replication component credit nor full-task credit because its required report
semantics failed.

Future-task regression evidence is `927/927` for the complete repository.
Compile-all and diff hygiene pass. Top-level production Python is 149,859 lines
across 139 modules; `research_agent_runtime.py` is 24,970 lines. These facts do
not alter the consumed result.
