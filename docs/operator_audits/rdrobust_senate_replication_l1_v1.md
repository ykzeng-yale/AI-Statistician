# rdrobust Senate source replication L1 v1 operator audit

Date: 2026-08-26

## Immutable identity

- Task: `rdrobust_senate_python_illustration_public_replication`
- Family: `regression_discontinuity_source_replication`
- Activation commits: `3e844a12fa25a77830aa81b1784b18e64a2f139d` and
  `fba535c8462205c19ed783c57f4b47c9e1006181`
- Public source commit: `7dd25671b8f28fc8618b1b7aa4a981564ee53f75`
- Source snapshot hash:
  `9afb817e88f385b6cdda4048ff0f1903c0e7d88f6799ca9128ec113b2613a954`
- Run:
  `runs/main_worker_research_l1_rdrobust_senate_replication_20260826_v1_codex_harness_exact_haiku`
- Runtime model: exact `claude-haiku-4-5-20251001` for all seven enabled
  roles; no Sonnet, Opus, or automatic escalation
- Runtime result: `ACCEPTED` after three outer traces
- Frozen automated full-task result: `1/1`
- Trustworthy capability result: `0/1`
- Operator disposition:
  `OPERATOR_INVALIDATED_SOURCE_REPORT_FALSE_ACCEPTANCE`
- Future-task shared mechanism commit:
  `0134c4cb5361956ed328dfd0de3db77210695a88`

The task received exactly one product draw and one post-runtime hidden
evaluation. Both are closed and immutable. It must not be resumed, rerun,
repaired, hidden-evaluated again, rescored, or resampled.

Immutable SHA-256 values:

- Runtime manifest:
  `e21657808a9a8fe433b7b0bab0b1559051cc3ba83ab90dbf6deafa9113274921`
- Runtime result:
  `70492f12fda8dff9556c6a7fae157a4255f1dfdf47671faf2cb8ec61fc4f3242`
- Runtime model topology:
  `1617548d20c98e062f722f60e0b7af13d1d7f4862cb6a9d6456aeb0c33705493`
- Hidden gold evaluation:
  `7dcbccc705baefef5a1a62a6316e19bb001f61de2c7dd7c0b3c7e6bbc32ece22`
- Runtime traces:
  `97c0df768fb44c08923a017d0ee85203529245befef00e7f675549b315e0f4b8`
- Runtime handoffs:
  `95bef3bc61bfe0f5ca857cc4493716ae8f523b6ffda2ad9f3670872adc3d0b5a`
- Runtime observations:
  `e21bac44a912f2d668e4f5f4e4b361fee5f96123fef6eccd5c8be6dcbb42086c`
- Model-authored report:
  `be13a4ed05f98d7234d9e9ec54664e60d4f08ee04abb4119fffa58ad9b000ec9`
- Hidden semantic result:
  `b0cf414529862b4cfa98c1b5317c7b44425ae6643706678acebd2998c2e3627f`

## Runtime result

One Architect call selected the source-replication workspace. The persistent
source owner then used 16 exact-Haiku model turns and 20 model-selected tools:
seven source searches, nine exact source reads, one unchanged source execution,
one report write, one workspace read, and one checkpoint commit. All 20 tools
executed. One final Critic call completed the 18-call product run. The outer
runtime recorded three traces, two handoffs, five observations, and zero outer
tool calls.

The source workspace committed one 749-line, 34,796-byte Markdown report and
the following durable identities:

- source manifest: `source_replication:326fdeabeca29ca2e0d5`, manifest hash
  `c540704fe37ff0ed3f48a8886146f35270b9ed2155b807fbc46eb5157a62d2ff`;
- workspace evidence: `source_replication_workspace:2eb49a9b4b9eaa419066`,
  content hash
  `58052308f8b36b5c0b16bf3672ff233a88d5c9c5d129d5c2358dafe24215d200`;
- checkpoint: `source_replication_checkpoint:f84c80310cc822982b0f`;
- immutable report path:
  `theory_workspaces/theory_workspace-1ec7fff62c3c69d8c95e/.immutable_checkpoints/16a1db48cb0c0cdbcb8f0a6e6c8b0c7497b3ec78428cb64bee06b592b3042b8c/rdrobust_senate_python_replication_report.md`.

Formalization was correctly not applicable. No generated estimator, simulation,
Formalizer proposal, Lean proof, or kernel evidence was produced.

## Frozen evaluation

The mechanical hidden source harness passed `10/10`. It verified the exact
source, data, environment, no-argument command, immutable execution, return
status, stdout, stderr, warnings, and report binding. This remains valid scoped
source-execution evidence.

The independently calibrated exact-Haiku semantic judge repeated its `8/8`
calibration result and marked all ten report claims `SATISFIED`, so the frozen
automated artifact says `1/1`. That automated record remains immutable, but its
semantic pass is a false acceptance and cannot receive trustworthy capability
credit.

## Operator findings

The authoritative report contains material errors and unsupported claims:

1. Line 130 calls `7.414` the robust point estimate. Its own complete table at
   lines 163-165 shows conventional `7.414` and bias-corrected/robust `7.507`;
   the compact default printout does not display a robust coefficient.
2. Line 76 labels the target a global average treatment effect. RD inference is
   local at the cutoff and causal interpretation requires identification
   assumptions that the execution did not validate.
3. Lines 280 and 679 treat nonsignificant balance tests as support for balance
   and RD validity. Failure to reject discontinuity is not proof of either.
4. Line 255 says one `0.28%` CI-length change confirms that uninformative
   covariates cannot improve precision artificially. One observed example does
   not establish that procedure-level claim.
5. Line 319 says the procedure correctly accounts for within-state correlation.
   Execution establishes only that the clustered option ran and reported CR1.
6. Line 395 calls every bandwidth selector reasonable without a supplied
   criterion or validation.
7. Lines 633 and 690 assert or strongly imply that plot objects were generated
   in memory, while line 708 correctly says execution of the plots cannot be
   determined from the available artifacts.
8. Lines 664-669 and 710 offer a different random seed as an explanation for
   deterministic Python-versus-R differences even though the immutable
   illustration contains no random or seed operation.
9. Line 702 calls `hc1` deprecated or incompatible. The observed warning only
   establishes that `hc1` is not a cluster option and that the package switched
   to `cr1`; deprecation was not observed.
10. Lines 5 and 639 count three stderr lines although the immutable stderr has
    two warnings, and line 13 labels a 40-character Git commit as SHA-256.

The later no-causal-claim caveat does not erase earlier unqualified ATE, positive
treatment-effect, and validity language. Likewise, the final admission that plot
execution is unverified does not erase the earlier memory-object assertion.

## Reviewer failure and shared correction

The old runtime Critic received the full report, raw execution, and nine exact
source ranges in one generation request. Its sole exact-Haiku call consumed
36,226 input tokens and 3,044 output tokens, then repeated several report errors:
it called plots generated in memory, called random seed a likely source of the
deterministic discrepancy, and returned `ACCEPT`. The hidden semantic judge also
false-accepted. This is evidence against another single-shot prompt or another
reviewer vote, not evidence for an RD phrase detector or content repair rule.

Commit `0134c4cb` changes future runtime Critic work to the existing generic
client-tool harness. Long exact evidence is represented in the opening context by
path, JSON location, hash, and size, while the same reviewer model chooses generic
document reads and searches, observes exact line results in the same transcript,
and submits one terminal judgment. Runtime validates only identity, schema,
task-intent requirements, and authority boundaries. There is no new scheduler,
agent, task formula, report patch, packet repair worker, model escalation, or
one-shot live fallback.

The same commit removes the 394-line `primitive_source_coverage_audit.py`, which
had no import, test, CLI entry, or canonical runtime consumer. This keeps the
change focused on live RAG/prover tools rather than retaining a retrieval-hit side
audit. The complete repository passed `944/944` in 78.46 seconds; the adjacent
runtime panel passed `216/216`; compile-all, diff hygiene, structure, and secret
checks passed. Top-level production Python decreased to 149,864 lines and
`research_agent_runtime.py` remains 24,986 lines.

## Capability accounting

This is the fifty-fourth consumed scored task. The immutable automated result is
recorded as `1/1`, but required report semantics are false, so the trustworthy
full-task score is `0/1`. Four of 54 tasks retain full-task capability credit.
Task 54 retains mechanical `10/10` execution evidence but receives neither a
source-replication component pass nor a full-task pass. The pre-existing
operator-invalid variance-ratio benchmark remains the only task excluded from the
valid-task denominator.

No post-run shared change can alter this disposition. Task 54 is permanently
closed from rerun, resume, report repair, hidden reevaluation, rescore, or
resampling.
