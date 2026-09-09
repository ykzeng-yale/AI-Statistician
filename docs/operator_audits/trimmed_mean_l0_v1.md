# Trimmed Mean: Consumed Independent Rejection

Date: 2026-09-09. Product commit: `db6e434bba1e0a7c126b4542b9adfb18563f0850`.
Task: `fixed_fraction_trimmed_mean_inference_known_result`.
The [preactivation ledger](../evaluation_activations/trimmed_mean_preactivation.json)
is unchanged. This closeout reads the existing result; it is not another grading
invocation, a revised candidate, or a retry of any earlier task.

## Result and Cost

The process exited 1 after 947.444 seconds. AgentRuntime completed nine steps and
returned `ACCEPTED`. The post-runtime frozen independent evaluator rejected the
full task, 0/1. The internal graph and summary acceptance are not independent
scientific correctness or a new E2E credit.

Completed product model turns, counted from the existing progress events:

| Stage | Completed model turns |
|---|---:|
| Initial Architect plan | 1 |
| TheoryDeveloper | 6 |
| Independent theory/preflight reviewer | 9 |
| AlgorithmEngineer | 8 |
| Generated source reviewers, two reviews | 43 |
| SimulationEvaluator source author | 10 |
| Final Critic | 25 |
| Total | 102 |

All calls used exactly `claude-haiku-4-5-20251001`. The 16 prequalification calls
(94.02 seconds) and two post-runtime candidate semantic-evaluator calls are
separate from those 102 product turns. These are observed completed model turns,
not an estimate of tokens, money, or transport-level retries. Reviewer and Critic
turns account for 77/102; more reviewing did not guarantee a correct result.

The run reached document-backed theory, generated scientific source, independent
source review, frozen confirmatory execution and final Critic. It did not stop at
the previous checkpoint-history defect. Formalization and source replication were
not required. It adds no formal, research-E2E or frontier-discovery credit.

## Existing Independent Findings

| Recorded check | Result |
|---|---|
| Runtime summary/result identity | Valid |
| Algorithm hidden harness execution | Executed successfully; 2/5 acceptance checks passed |
| Theory structural checks | 7/7 passed |
| Theory semantic judgments | 1 SATISFIED, 3 VIOLATED, 2 INCONCLUSIVE; document FAIL |
| Empirical hidden execution | Executed successfully; 0/7 acceptance checks passed |
| Full task | FAILED |

The semantic judge used the prequalified frozen authority; it was not recalibrated
after seeing the candidate. These counts report the existing evaluator output,
not a new expert mathematical judgment. Hidden checks are not assumed independent
error causes. Neither the mathematical defect nor its remedy can be inferred from
the check counts alone.

Accepted theory document-set hash:
`342b5e2f8b3e0473a7d6d573d31a972fa370a0b506b7916ea8194f60d7d6469c`.
Evaluated scientific source hash:
`46ebca35bcbd347a03b008e11559dca0803bd5ff02d9d2fdd2a65c070ee5c386`.

The design implication is limited but important: functioning workspaces, structural
validity, execution and independent runtime model approval did not establish the
scientific claim. Diagnose general author/reviewer/tool behavior using visible
artifacts and disjoint controls; do not add the expected trimmed-mean result to a
prompt, patch this source, introduce another reviewer by default, or weaken gold.

## Immutable Evidence

Root: `runs/main_worker_research_l0_trimmed_mean_20260909_v1_codex_workspace_exact_haiku`.

| File | SHA-256 |
|---|---|
| `research_agent_runtime_manifest.json` | `50170baa4a38771ee37781b2b85299425a4b55d00a778d34085332d9727b59ca` |
| `fixed_fraction_trimmed_mean_inference_known_result_runtime_result.json` | `83463a1d7a688a7947d461db41c81a40c67d260e583b8ae733cdfa67169bfa2a` |
| `research_capability_gold_evaluation.json` | `f612179a656d0a6b6695e2fe81d66a6b14446b247b261b7d8a45e128b8b38546` |
| `runtime_progress.jsonl` | `a730e2b723a6ae34c3fe145103b94f5296c036333b1eccab840e4289e6d0ed39` |
| `operator_single_draw_terminal.json` | `c6ca81445fc1086470d2e3e10d787c2e90dd825a957470b384ca2ea38dd1a193` |

The candidate, result, authority and all checkpoints remain consumed and immutable.
Do not resume, repair, rerun, rejudge or rescore them. No hidden source, expected
value or decisive excerpt is copied into product context by this closeout.
